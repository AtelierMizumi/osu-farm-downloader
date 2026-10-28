#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
osu! Farm Map Downloader - Modern Linux GUI (PySide6)
Tối ưu hóa cho Linux & osu! stable trên ổ cứng ngoài
Dành cho người chơi: Cao Mi Le (Rank #12k, 9.1k PP)
"""

import os
import sys
import time

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QThread, Signal

# Import core modules
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import config
import profile_service
import map_finder
import mirror_downloader

# ----------------- Stylesheet (Dark Modern osu! Theme) -----------------
DARK_STYLE = """
QMainWindow {
    background-color: #17141f;
}
QWidget {
    color: #e5e1ee;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #332d42;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    background-color: #1e1a29;
    font-weight: bold;
    color: #b3a6d4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #ff66aa;
}
QLabel {
    color: #e5e1ee;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #272235;
    border: 1px solid #433b59;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    selection-background-color: #ff66aa;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #ff66aa;
}
QPushButton {
    background-color: #38304c;
    border: 1px solid #544973;
    border-radius: 6px;
    padding: 7px 15px;
    color: #ffffff;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #493f63;
    border-color: #ff66aa;
}
QPushButton:pressed {
    background-color: #2b253b;
}
QPushButton#PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff66aa, stop:1 #b366ff);
    border: none;
    color: #ffffff;
    font-size: 14px;
    padding: 10px 20px;
    border-radius: 6px;
}
QPushButton#PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff7ab5, stop:1 #be7aff);
}
QPushButton#PrimaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e65595, stop:1 #9f52e6);
}
QPushButton#SecondaryBtn {
    background-color: #245749;
    border: 1px solid #2ecc71;
    color: #ffffff;
    font-size: 14px;
    padding: 10px 20px;
    border-radius: 6px;
}
QPushButton#SecondaryBtn:hover {
    background-color: #2c6d5b;
}
QTableWidget {
    background-color: #1b1725;
    border: 1px solid #332d42;
    border-radius: 6px;
    gridline-color: #2b2539;
    selection-background-color: #3b324f;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #231e30;
    color: #b3a6d4;
    padding: 6px;
    border: none;
    border-bottom: 2px solid #ff66aa;
    font-weight: bold;
}
QProgressBar {
    border: 1px solid #332d42;
    border-radius: 6px;
    text-align: center;
    background-color: #231e30;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff66aa, stop:1 #2ecc71);
    border-radius: 5px;
}
QCheckBox {
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #544973;
    background-color: #272235;
}
QCheckBox::indicator:checked {
    background-color: #ff66aa;
    border-color: #ff66aa;
}
"""

# ----------------- Worker Threads -----------------
class SearchWorker(QThread):
    progress_signal = Signal(int, int, str)
    finished_signal = Signal(list)
    error_signal = Signal(str)

    def __init__(self, min_sr, max_sr, limit, mod, mapper_filter, installed_ids):
        super().__init__()
        self.min_sr = min_sr
        self.max_sr = max_sr
        self.limit = limit
        self.mod = mod
        self.mapper_filter = mapper_filter
        self.installed_ids = installed_ids

    def run(self):
        try:
            maps = map_finder.find_ranked_farm_maps(
                min_sr=self.min_sr,
                max_sr=self.max_sr,
                limit=self.limit,
                mod=self.mod,
                already_installed_ids=self.installed_ids,
                mapper_filter=self.mapper_filter if self.mapper_filter != "Tất cả Mappers" else None,
                progress_callback=lambda c, t, msg: self.progress_signal.emit(c, t, msg)
            )
            self.finished_signal.emit(maps)
        except Exception as e:
            self.error_signal.emit(str(e))

class DownloadWorker(QThread):
    file_progress_signal = Signal(int, int, int, float, str)  # sid, dl, total, speed, mirror
    item_completed_signal = Signal(int, bool, str)            # index, ok, msg
    all_finished_signal = Signal(int, int, float)             # success, fail, total_mb

    def __init__(self, maps_to_download, songs_path, no_video=True):
        super().__init__()
        self.maps = maps_to_download
        self.songs_path = songs_path
        self.no_video = no_video
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        success_count = 0
        fail_count = 0
        total_bytes = 0

        for idx, m in enumerate(self.maps):
            if self.is_cancelled:
                break

            def cb(sid, dl, total, speed, mirror):
                self.file_progress_signal.emit(sid, dl, total, speed, mirror)

            ok, msg, path = mirror_downloader.download_beatmapset(
                m,
                self.songs_path,
                no_video=self.no_video,
                progress_callback=cb
            )

            if ok:
                success_count += 1
                if path and os.path.exists(path):
                    total_bytes += os.path.getsize(path)
            else:
                fail_count += 1

            self.item_completed_signal.emit(idx, ok, msg)
            time.sleep(0.2)

        total_mb = total_bytes / (1024 * 1024)
        self.all_finished_signal.emit(success_count, fail_count, total_mb)

# ----------------- Main GUI Window -----------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("osu! Ranked Farm Maps Downloader (Linux & External Drive)")
        self.resize(1100, 750)
        self.setStyleSheet(DARK_STYLE)

        self.cfg = config.load_config()
        self.songs_path = self.cfg.get("songs_path", "")
        self.installed_ids = config.get_installed_beatmap_ids(self.songs_path)
        self.profile = profile_service.fetch_player_profile(self.cfg.get("player_username", "Cao Mi Le"))
        self.current_maps = []
        self.download_worker = None
        self.search_worker = None

        self.init_ui()

    def init_ui(self):
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Header & Profile Banner
        header_card = QtWidgets.QFrame()
        header_card.setStyleSheet("background-color: #211d2e; border-radius: 8px; padding: 10px;")
        header_layout = QtWidgets.QHBoxLayout(header_card)

        # User profile text
        prof_info = QtWidgets.QVBoxLayout()
        p_name = QtWidgets.QLabel(f"👤 <b>{self.profile['username']}</b> (ID: {self.profile['id']})")
        p_name.setStyleSheet("font-size: 16px; color: #ff66aa;")
        p_stats = QtWidgets.QLabel(
            f"🏆 Rank: <b>#{self.profile['global_rank']:,} Global</b> (#{self.profile['country_rank']} VN) | "
            f"⚡ Performance: <b>{self.profile['pp']:,} PP</b> | Acc: <b>{self.profile['hit_accuracy']}%</b> | Plays: {self.profile['play_count']:,}"
        )
        p_stats.setStyleSheet("color: #d1c7e6;")
        
        nm = self.profile["recommended"]["nomod_hd"]
        p_rec = QtWidgets.QLabel(
            f"🎯 <b>Star Rating đề xuất:</b> Nomod: <font color='#2ecc71'><b>{nm['min_sr']}* – {nm['max_sr']}*</b></font> (Target: ~{nm['target_sr']}*) | "
            f"DT: <font color='#f1c40f'><b>{self.profile['recommended']['dt']['min_sr']}* – {self.profile['recommended']['dt']['max_sr']}*</b></font> | "
            f"HR: <font color='#3498db'><b>{self.profile['recommended']['hr_hdhr']['min_sr']}* – {self.profile['recommended']['hr_hdhr']['max_sr']}*</b></font>"
        )
        prof_info.addWidget(p_name)
        prof_info.addWidget(p_stats)
        prof_info.addWidget(p_rec)
        header_layout.addLayout(prof_info)

        header_layout.addStretch()

        main_layout.addWidget(header_card)

        # 2. External Drive / Songs Directory Panel
        drive_box = QtWidgets.QGroupBox("💾 Ổ cứng ngoài & Thư mục Songs của osu! stable")
        drive_layout = QtWidgets.QHBoxLayout(drive_box)
        
        self.path_edit = QtWidgets.QLineEdit(self.songs_path)
        self.path_edit.setPlaceholderText("Đường dẫn tới thư mục Songs của osu! (ví dụ /mnt/SSDStorage/osu!/Songs)")
        browse_btn = QtWidgets.QPushButton("📁 Chọn Thư mục")
        browse_btn.clicked.connect(self.browse_songs_folder)

        self.lbl_installed = QtWidgets.QLabel(f"📦 Đã có: <b>{len(self.installed_ids):,} maps</b> (Tự động bỏ qua)")
        self.lbl_installed.setStyleSheet("color: #2ecc71; padding-left: 10px;")

        drive_layout.addWidget(self.path_edit, 5)
        drive_layout.addWidget(browse_btn, 1)
        drive_layout.addWidget(self.lbl_installed, 2)
        main_layout.addWidget(drive_box)

        # 3. Filter Controls Panel
        filter_box = QtWidgets.QGroupBox("🔍 Bộ lọc Beatmaps Thông Minh (Smart Farm Filter)")
        filter_layout = QtWidgets.QGridLayout(filter_box)
        filter_layout.setContentsMargins(12, 16, 12, 12)
        filter_layout.setHorizontalSpacing(15)
        filter_layout.setVerticalSpacing(10)

        # Mode Preset Selector
        filter_layout.addWidget(QtWidgets.QLabel("Chế độ chơi:"), 0, 0)
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["⚡ Nomod / Hidden Farm", "⏩ DoubleTime (DT) Farm", "🎯 HardRock (HR) Farm"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        filter_layout.addWidget(self.mode_combo, 0, 1)

        # Star Rating Spinners
        filter_layout.addWidget(QtWidgets.QLabel("Min Star:"), 0, 2)
        self.spin_min_sr = QtWidgets.QDoubleSpinBox()
        self.spin_min_sr.setRange(1.0, 11.0)
        self.spin_min_sr.setSingleStep(0.05)
        self.spin_min_sr.setValue(nm["min_sr"])
        filter_layout.addWidget(self.spin_min_sr, 0, 3)

        filter_layout.addWidget(QtWidgets.QLabel("Max Star:"), 0, 4)
        self.spin_max_sr = QtWidgets.QDoubleSpinBox()
        self.spin_max_sr.setRange(1.0, 11.0)
        self.spin_max_sr.setSingleStep(0.05)
        self.spin_max_sr.setValue(nm["max_sr"])
        filter_layout.addWidget(self.spin_max_sr, 0, 5)

        # Mapper filter
        filter_layout.addWidget(QtWidgets.QLabel("Mapper tủ:"), 1, 0)
        self.mapper_combo = QtWidgets.QComboBox()
        self.mapper_combo.addItem("Tất cả Mappers")
        self.mapper_combo.addItems(map_finder.FARM_MAPPERS)
        filter_layout.addWidget(self.mapper_combo, 1, 1)

        # Limit
        filter_layout.addWidget(QtWidgets.QLabel("Số lượng map:"), 1, 2)
        self.spin_limit = QtWidgets.QSpinBox()
        self.spin_limit.setRange(5, 100)
        self.spin_limit.setValue(25)
        filter_layout.addWidget(self.spin_limit, 1, 3)

        # No video checkbox
        self.chk_no_video = QtWidgets.QCheckBox("No-Video (Tải siêu nhanh & tiết kiệm ổ cứng)")
        self.chk_no_video.setChecked(self.cfg.get("no_video", True))
        filter_layout.addWidget(self.chk_no_video, 1, 4, 1, 2)

        # Search Button
        self.btn_search = QtWidgets.QPushButton("🔍 Tìm Kiếm Map Farm Phù Hợp")
        self.btn_search.setObjectName("PrimaryBtn")
        self.btn_search.clicked.connect(self.start_search)
        filter_layout.addWidget(self.btn_search, 0, 6, 2, 1)

        main_layout.addWidget(filter_box)

        # 4. Beatmap Candidates Table
        table_header_layout = QtWidgets.QHBoxLayout()
        self.lbl_table_count = QtWidgets.QLabel("<b>Danh sách Beatmap tìm thấy:</b> 0 maps")
        btn_select_all = QtWidgets.QPushButton("Chọn tất cả")
        btn_select_all.clicked.connect(self.select_all_maps)
        btn_deselect_all = QtWidgets.QPushButton("Bỏ chọn tất cả")
        btn_deselect_all.clicked.connect(self.deselect_all_maps)

        table_header_layout.addWidget(self.lbl_table_count)
        table_header_layout.addStretch()
        table_header_layout.addWidget(btn_select_all)
        table_header_layout.addWidget(btn_deselect_all)
        main_layout.addLayout(table_header_layout)

        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Tải", "Set ID", "Tên Bài Hát & Nghệ Sĩ", "Mapper", "Star Rating (Diffs)", "Farm Score", "Đặc điểm / Tags"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QtWidgets.QHeaderView.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table)

        # 5. Download & Progress Bar Panel
        bottom_box = QtWidgets.QFrame()
        bottom_box.setStyleSheet("background-color: #211d2e; border-radius: 8px; padding: 10px;")
        bottom_layout = QtWidgets.QVBoxLayout(bottom_box)

        pbar_layout = QtWidgets.QHBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        self.lbl_speed = QtWidgets.QLabel("Sẵn sàng tải")
        self.lbl_speed.setStyleSheet("color: #ff66aa; font-weight: bold; min-width: 180px;")

        pbar_layout.addWidget(self.progress_bar, 4)
        pbar_layout.addWidget(self.lbl_speed, 1)

        action_layout = QtWidgets.QHBoxLayout()
        self.btn_download = QtWidgets.QPushButton("⬇ Bắt Đầu Tải Các Map Đã Chọn Về Ổ Cứng")
        self.btn_download.setObjectName("SecondaryBtn")
        self.btn_download.clicked.connect(self.start_download)
        self.btn_download.setEnabled(False)

        self.lbl_status = QtWidgets.QLabel("Chưa có map nào được tải.")
        self.lbl_status.setStyleSheet("color: #b3a6d4;")

        action_layout.addWidget(self.btn_download, 2)
        action_layout.addWidget(self.lbl_status, 4)

        bottom_layout.addLayout(pbar_layout)
        bottom_layout.addLayout(action_layout)
        main_layout.addWidget(bottom_box)

    # ----------------- UI Event Handlers -----------------
    def on_mode_changed(self, idx):
        if idx == 0:  # Nomod
            nm = self.profile["recommended"]["nomod_hd"]
            self.spin_min_sr.setValue(nm["min_sr"])
            self.spin_max_sr.setValue(nm["max_sr"])
        elif idx == 1:  # DT
            dt = self.profile["recommended"]["dt"]
            self.spin_min_sr.setValue(dt["min_sr"])
            self.spin_max_sr.setValue(dt["max_sr"])
        elif idx == 2:  # HR
            hr = self.profile["recommended"]["hr_hdhr"]
            self.spin_min_sr.setValue(hr["min_sr"])
            self.spin_max_sr.setValue(hr["max_sr"])

    def browse_songs_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Chọn thư mục Songs của osu! stable trên ổ cứng ngoài", self.songs_path
        )
        if folder:
            self.songs_path = os.path.abspath(folder)
            self.path_edit.setText(self.songs_path)
            self.cfg["songs_path"] = self.songs_path
            config.save_config(self.cfg)
            self.installed_ids = config.get_installed_beatmap_ids(self.songs_path)
            self.lbl_installed.setText(f"📦 Đã có: <b>{len(self.installed_ids):,} maps</b> (Tự động bỏ qua)")

    def start_search(self):
        songs_dir = self.path_edit.text().strip()
        if not os.path.isdir(songs_dir):
            QtWidgets.QMessageBox.warning(
                self, "Lỗi đường dẫn", "Thư mục Songs không hợp lệ hoặc không tồn tại trên máy tính/ổ cứng!"
            )
            return

        self.btn_search.setEnabled(False)
        self.btn_download.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_speed.setText("Đang tìm kiếm map...")
        self.lbl_status.setText("Đang kết nối mirror và tính toán farm score...")

        min_sr = self.spin_min_sr.value()
        max_sr = self.spin_max_sr.value()
        limit = self.spin_limit.value()
        mapper = self.mapper_combo.currentText()

        mod = "NM"
        if self.mode_combo.currentIndex() == 1:
            mod = "DT"
        elif self.mode_combo.currentIndex() == 2:
            mod = "HR"

        # Cập nhật danh sách map đã cài đặt
        self.installed_ids = config.get_installed_beatmap_ids(songs_dir)
        self.lbl_installed.setText(f"📦 Đã có: <b>{len(self.installed_ids):,} maps</b> (Tự động bỏ qua)")

        self.search_worker = SearchWorker(min_sr, max_sr, limit, mod, mapper, self.installed_ids)
        self.search_worker.progress_signal.connect(self.on_search_progress)
        self.search_worker.finished_signal.connect(self.on_search_finished)
        self.search_worker.error_signal.connect(self.on_search_error)
        self.search_worker.start()

    def on_search_progress(self, current, total, msg):
        pct = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(msg)

    def on_search_finished(self, maps):
        self.btn_search.setEnabled(True)
        self.current_maps = maps
        self.progress_bar.setValue(100)
        self.lbl_speed.setText(f"Tìm thấy {len(maps)} maps!")
        self.lbl_status.setText(f"Đã hoàn thành tìm kiếm. Hãy chọn các map bạn muốn tải.")
        self.populate_table(maps)

        if maps:
            self.btn_download.setEnabled(True)
        else:
            QtWidgets.QMessageBox.information(
                self, "Thông báo", "Không tìm thấy map mới nào thỏa mãn khoảng SR hoặc các map đều đã có sẵn trong ổ cứng!"
            )

    def on_search_error(self, err_msg):
        self.btn_search.setEnabled(True)
        self.lbl_speed.setText("Lỗi tìm kiếm")
        QtWidgets.QMessageBox.critical(self, "Lỗi tìm kiếm", f"Không thể lấy dữ liệu: {err_msg}")

    def populate_table(self, maps):
        self.table.setRowCount(len(maps))
        self.lbl_table_count.setText(f"<b>Danh sách Beatmap tìm thấy:</b> {len(maps)} maps")

        for row, m in enumerate(maps):
            # Checkbox
            chk_item = QtWidgets.QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Checked)
            self.table.setItem(row, 0, chk_item)

            # Set ID
            id_item = QtWidgets.QTableWidgetItem(str(m["id"]))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, id_item)

            # Title & Artist
            title_text = f"{m['artist']} - {m['title']}"
            title_item = QtWidgets.QTableWidgetItem(title_text)
            self.table.setItem(row, 2, title_item)

            # Creator / Mapper
            creator_item = QtWidgets.QTableWidgetItem(m["creator"])
            creator_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, creator_item)

            # Diffs & Star Rating
            diffs_str = ", ".join([f"{d['name']} ({d['sr']}*)" for d in m["valid_diffs"][:3]])
            if len(m["valid_diffs"]) > 3:
                diffs_str += f" (+{len(m['valid_diffs'])-3})"
            diffs_item = QtWidgets.QTableWidgetItem(diffs_str)
            diffs_item.setForeground(QtGui.QColor("#2ecc71"))
            self.table.setItem(row, 4, diffs_item)

            # Farm Score
            score_item = QtWidgets.QTableWidgetItem(f"{m['farm_score']}/100")
            score_item.setTextAlignment(Qt.AlignCenter)
            if m['farm_score'] >= 90:
                score_item.setForeground(QtGui.QColor("#2ecc71"))
            elif m['farm_score'] >= 75:
                score_item.setForeground(QtGui.QColor("#f1c40f"))
            else:
                score_item.setForeground(QtGui.QColor("#e67e22"))
            self.table.setItem(row, 5, score_item)

            # Tags
            tags_str = " | ".join(m.get("best_tags", []))
            tags_item = QtWidgets.QTableWidgetItem(tags_str)
            tags_item.setForeground(QtGui.QColor("#ff66aa"))
            self.table.setItem(row, 6, tags_item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QtWidgets.QHeaderView.Stretch)

    def select_all_maps(self):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.Checked)

    def deselect_all_maps(self):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.Unchecked)

    def start_download(self):
        selected_maps = []
        for r in range(self.table.rowCount()):
            chk = self.table.item(r, 0)
            if chk and chk.checkState() == Qt.Checked:
                selected_maps.append(self.current_maps[r])

        if not selected_maps:
            QtWidgets.QMessageBox.warning(self, "Chưa chọn map", "Vui lòng tick chọn ít nhất 1 beatmap để tải!")
            return

        songs_dir = self.path_edit.text().strip()
        if not os.path.isdir(songs_dir):
            QtWidgets.QMessageBox.critical(self, "Lỗi", "Thư mục Songs trên ổ cứng không tồn tại!")
            return

        self.btn_search.setEnabled(False)
        self.btn_download.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_speed.setText("Bắt đầu tải...")

        no_video = self.chk_no_video.isChecked()
        self.download_worker = DownloadWorker(selected_maps, songs_dir, no_video=no_video)
        self.download_worker.file_progress_signal.connect(self.on_file_progress)
        self.download_worker.item_completed_signal.connect(self.on_item_completed)
        self.download_worker.all_finished_signal.connect(self.on_download_all_finished)
        self.download_worker.start()

    def on_file_progress(self, sid, dl, total, speed_kb, mirror):
        pct = int(dl / total * 100) if total > 0 else 0
        dl_mb = dl / (1024 * 1024)
        total_mb = total / (1024 * 1024) if total > 0 else 0
        speed_mb = speed_kb / 1024

        self.progress_bar.setValue(pct)
        self.lbl_speed.setText(f"{mirror}: {speed_mb:.1f} MB/s ({dl_mb:.1f}/{total_mb:.1f}MB)")

    def on_item_completed(self, index, ok, msg):
        status_text = f"[{index + 1}/{len(self.current_maps)}] {msg}"
        self.lbl_status.setText(status_text)

    def on_download_all_finished(self, success, fail, total_mb):
        self.btn_search.setEnabled(True)
        self.btn_download.setEnabled(True)
        self.progress_bar.setValue(100)
        self.lbl_speed.setText("Hoàn tất!")

        # Cập nhật lại số map đã có
        self.installed_ids = config.get_installed_beatmap_ids(self.path_edit.text().strip())
        self.lbl_installed.setText(f"📦 Đã có: <b>{len(self.installed_ids):,} maps</b> (Tự động bỏ qua)")

        msg = (
            f"<b>Đã tải thành công {success} beatmapsets!</b> ({total_mb:.1f} MB)<br>"
            f"{f'Thất bại: {fail} maps<br>' if fail > 0 else ''}"
            f"Vị trí lưu: <code>{self.path_edit.text().strip()}</code><br><br>"
            f"<b>🎮 HƯỚNG DẪN OSU! STABLE TRÊN LINUX:</b><br>"
            f"1. Mở osu! stable trên Linux.<br>"
            f"2. Vào màn hình chọn bài hát (Song Select).<br>"
            f"3. Nhấn <b>F5</b> để game tự động nạp tất cả bài hát mới ngay lập tức!"
        )
        QtWidgets.QMessageBox.information(self, "Tải Beatmaps Hoàn Tất", msg)

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("osu-farm-downloader")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
