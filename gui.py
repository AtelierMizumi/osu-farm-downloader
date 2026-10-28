#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
osu! Farm Map Downloader - Modern Linux GUI (PySide6)
Phiên bản 1.1.0: Tải song song đa luồng, Bộ lọc trạng thái map, Tùy chọn nguồn Mirror, Nghe thử Audio Preview
Dành riêng cho Linux & osu! stable trên ổ cứng ngoài
Người chơi: Cao Mi Le (Rank #12k, 9.1k PP)
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

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
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
    border: none;
    color: #ffffff;
    font-size: 14px;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: bold;
}
QPushButton#SecondaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3be382, stop:1 #2ecc71);
}
QPushButton#AudioBtn {
    background-color: #2a243a;
    border: 1px solid #ff66aa;
    color: #ff66aa;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 12px;
}
QPushButton#AudioBtn:hover {
    background-color: #ff66aa;
    color: #ffffff;
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

    def __init__(self, min_sr, max_sr, limit, mod, status_filter, mapper_filter, installed_ids):
        super().__init__()
        self.min_sr = min_sr
        self.max_sr = max_sr
        self.limit = limit
        self.mod = mod
        self.status_filter = status_filter
        self.mapper_filter = mapper_filter
        self.installed_ids = installed_ids

    def run(self):
        try:
            maps = map_finder.find_ranked_farm_maps(
                min_sr=self.min_sr,
                max_sr=self.max_sr,
                limit=self.limit,
                mod=self.mod,
                status_filter=self.status_filter,
                already_installed_ids=self.installed_ids,
                mapper_filter=self.mapper_filter if self.mapper_filter != "Tất cả Mappers" else None,
                progress_callback=lambda c, t, msg: self.progress_signal.emit(c, t, msg)
            )
            self.finished_signal.emit(maps)
        except Exception as e:
            self.error_signal.emit(str(e))

class ParallelDownloadWorker(QThread):
    row_progress_signal = Signal(int, str, int)  # row_index, status_text, percent
    overall_progress_signal = Signal(int, int, float, float)  # completed, total, total_mb, speed_mb
    all_finished_signal = Signal(int, int, float, float)      # success, fail, total_mb, elapsed

    def __init__(self, selected_items, songs_path, max_workers=4, preferred_mirror="auto", no_video=True):
        super().__init__()
        # selected_items là danh sách tuple (row_index, map_dict)
        self.selected_items = selected_items
        self.songs_path = songs_path
        self.max_workers = max_workers
        self.preferred_mirror = preferred_mirror
        self.no_video = no_video
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        total = len(self.selected_items)
        completed = 0
        success = 0
        fail = 0
        total_bytes = 0

        start_time = time.time()
        active_speeds = {}

        def single_task(item):
            row_idx, m = item
            if self.is_cancelled:
                return row_idx, False, "Đã hủy", 0

            self.row_progress_signal.emit(row_idx, "Đang kết nối...", 5)

            def progress_cb(sid, dl, tot, spd_kb, mir):
                pct = int(dl / tot * 100) if tot > 0 else 50
                active_speeds[row_idx] = spd_kb
                current_total_speed = sum(active_speeds.values()) / 1024.0
                dl_mb = total_bytes / (1024 * 1024)
                self.overall_progress_signal.emit(completed, total, dl_mb, current_total_speed)
                self.row_progress_signal.emit(row_idx, f"Tải {pct}% ({mir})", pct)

            ok, msg, path = mirror_downloader.download_beatmapset(
                m,
                self.songs_path,
                preferred_mirror=self.preferred_mirror,
                no_video=self.no_video,
                progress_callback=progress_cb
            )

            if row_idx in active_speeds:
                del active_speeds[row_idx]

            size = os.path.getsize(path) if ok and path and os.path.exists(path) else 0
            return row_idx, ok, msg, size

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(single_task, it) for it in self.selected_items]
            for fut in futures:
                if self.is_cancelled:
                    break
                row_idx, ok, msg, size = fut.result()
                completed += 1
                if ok:
                    success += 1
                    total_bytes += size
                    self.row_progress_signal.emit(row_idx, f"✔ {msg}", 100)
                else:
                    fail += 1
                    self.row_progress_signal.emit(row_idx, f"✘ {msg}", 0)

                dl_mb = total_bytes / (1024 * 1024)
                current_total_speed = sum(active_speeds.values()) / 1024.0
                self.overall_progress_signal.emit(completed, total, dl_mb, current_total_speed)

        elapsed = max(time.time() - start_time, 0.1)
        total_mb = total_bytes / (1024 * 1024)
        self.all_finished_signal.emit(success, fail, total_mb, elapsed)

# ----------------- Main GUI Window -----------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("osu! Ranked Farm Maps Downloader (Linux & External Drive) v1.1.0")
        self.resize(1180, 800)
        self.setStyleSheet(DARK_STYLE)

        self.cfg = config.load_config()
        self.songs_path = self.cfg.get("songs_path", "")
        self.installed_ids = config.get_installed_beatmap_ids(self.songs_path)
        self.profile = profile_service.fetch_player_profile(self.cfg.get("player_username", "Cao Mi Le"))
        self.current_maps = []
        self.download_worker = None
        self.search_worker = None

        # Audio Preview Player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)
        self.playing_set_id = None

        self.init_ui()

    def init_ui(self):
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # 1. Header & Profile Banner
        header_card = QtWidgets.QFrame()
        header_card.setStyleSheet("background-color: #211d2e; border-radius: 8px; padding: 10px;")
        header_layout = QtWidgets.QHBoxLayout(header_card)

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

        # Audio Player Controls in Header
        audio_box = QtWidgets.QHBoxLayout()
        self.lbl_now_playing = QtWidgets.QLabel("🎵 Chưa phát audio")
        self.lbl_now_playing.setStyleSheet("color: #b3a6d4; font-size: 12px; margin-right: 8px;")
        self.btn_stop_audio = QtWidgets.QPushButton("⏹ Dừng")
        self.btn_stop_audio.setObjectName("AudioBtn")
        self.btn_stop_audio.clicked.connect(self.stop_audio)
        self.btn_stop_audio.setEnabled(False)
        audio_box.addWidget(self.lbl_now_playing)
        audio_box.addWidget(self.btn_stop_audio)
        header_layout.addLayout(audio_box)

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

        # 3. Enhanced Filter Controls Panel
        filter_box = QtWidgets.QGroupBox("🔍 Bộ lọc Beatmaps Thông Minh (Smart Farm Filter & Status)")
        filter_layout = QtWidgets.QGridLayout(filter_box)
        filter_layout.setContentsMargins(12, 14, 12, 12)
        filter_layout.setHorizontalSpacing(14)
        filter_layout.setVerticalSpacing(8)

        # Row 0: Chế độ & Star Rating
        filter_layout.addWidget(QtWidgets.QLabel("Chế độ chơi:"), 0, 0)
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["⚡ Nomod / Hidden Farm", "⏩ DoubleTime (DT) Farm", "🎯 HardRock (HR) Farm"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        filter_layout.addWidget(self.mode_combo, 0, 1)

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

        # Search Button (Spans 2 rows)
        self.btn_search = QtWidgets.QPushButton("🔍 Tìm Kiếm Map Farm Phù Hợp")
        self.btn_search.setObjectName("PrimaryBtn")
        self.btn_search.clicked.connect(self.start_search)
        filter_layout.addWidget(self.btn_search, 0, 6, 2, 1)

        # Row 1: Tình trạng map, Mapper, Số lượng
        filter_layout.addWidget(QtWidgets.QLabel("Tình trạng map:"), 1, 0)
        self.status_combo = QtWidgets.QComboBox()
        self.status_keys = list(map_finder.STATUS_PRESETS.keys())
        for k in self.status_keys:
            self.status_combo.addItem(map_finder.STATUS_PRESETS[k]["name"])
        filter_layout.addWidget(self.status_combo, 1, 1)

        filter_layout.addWidget(QtWidgets.QLabel("Mapper tủ:"), 1, 2)
        self.mapper_combo = QtWidgets.QComboBox()
        self.mapper_combo.addItem("Tất cả Mappers")
        self.mapper_combo.addItems(map_finder.FARM_MAPPERS)
        filter_layout.addWidget(self.mapper_combo, 1, 3)

        filter_layout.addWidget(QtWidgets.QLabel("Số lượng map:"), 1, 4)
        self.spin_limit = QtWidgets.QSpinBox()
        self.spin_limit.setRange(5, 100)
        self.spin_limit.setValue(30)
        filter_layout.addWidget(self.spin_limit, 1, 5)

        # Row 2: Nguồn Mirror & Tải song song (Đa luồng)
        filter_layout.addWidget(QtWidgets.QLabel("Nguồn Mirror:"), 2, 0)
        self.mirror_combo = QtWidgets.QComboBox()
        self.mirror_keys = list(mirror_downloader.MIRROR_PROVIDERS.keys())
        for k in self.mirror_keys:
            self.mirror_combo.addItem(mirror_downloader.MIRROR_PROVIDERS[k])
        filter_layout.addWidget(self.mirror_combo, 2, 1)

        filter_layout.addWidget(QtWidgets.QLabel("Tải song song (Luồng):"), 2, 2)
        self.spin_threads = QtWidgets.QSpinBox()
        self.spin_threads.setRange(1, 8)
        self.spin_threads.setValue(self.cfg.get("concurrent_downloads", 4))
        filter_layout.addWidget(self.spin_threads, 2, 3)

        self.chk_no_video = QtWidgets.QCheckBox("No-Video (Tải siêu nhanh & tiết kiệm ổ cứng)")
        self.chk_no_video.setChecked(self.cfg.get("no_video", True))
        filter_layout.addWidget(self.chk_no_video, 2, 4, 1, 2)

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

        # Table with 8 columns: [Chọn, Set ID, Tên bài, Mapper, Diffs, Farm Score, Trạng thái tải, Tags]
        self.table = QtWidgets.QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Chọn", "ID", "Tên Bài Hát & Nghệ Sĩ", "Mapper", "Star Rating (Diffs)", "Farm Score", "Trạng thái", "Đặc điểm / Tags"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QtWidgets.QHeaderView.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.itemDoubleClicked.connect(self.on_table_double_clicked)
        main_layout.addWidget(self.table)

        # 5. Download & Parallel Progress Bar Panel
        bottom_box = QtWidgets.QFrame()
        bottom_box.setStyleSheet("background-color: #211d2e; border-radius: 8px; padding: 10px;")
        bottom_layout = QtWidgets.QVBoxLayout(bottom_box)

        pbar_layout = QtWidgets.QHBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        self.lbl_speed = QtWidgets.QLabel("Sẵn sàng tải")
        self.lbl_speed.setStyleSheet("color: #ff66aa; font-weight: bold; min-width: 220px;")

        pbar_layout.addWidget(self.progress_bar, 4)
        pbar_layout.addWidget(self.lbl_speed, 1)

        action_layout = QtWidgets.QHBoxLayout()
        self.btn_download = QtWidgets.QPushButton("⚡ BẮT ĐẦU TẢI SONG SONG VỀ Ổ CỨNG")
        self.btn_download.setObjectName("SecondaryBtn")
        self.btn_download.clicked.connect(self.start_parallel_download)
        self.btn_download.setEnabled(False)

        self.lbl_status = QtWidgets.QLabel("Chưa có tác vụ nào đang chạy.")
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
        status_key = self.status_keys[self.status_combo.currentIndex()]

        mod = "NM"
        if self.mode_combo.currentIndex() == 1:
            mod = "DT"
        elif self.mode_combo.currentIndex() == 2:
            mod = "HR"

        self.installed_ids = config.get_installed_beatmap_ids(songs_dir)
        self.lbl_installed.setText(f"📦 Đã có: <b>{len(self.installed_ids):,} maps</b> (Tự động bỏ qua)")

        self.search_worker = SearchWorker(min_sr, max_sr, limit, mod, status_key, mapper, self.installed_ids)
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
        self.lbl_table_count.setText(f"<b>Danh sách Beatmap tìm thấy:</b> {len(maps)} maps (Double click để nghe thử preview)")

        for row, m in enumerate(maps):
            # 0. Checkbox
            chk_item = QtWidgets.QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Checked)
            self.table.setItem(row, 0, chk_item)

            # 1. Set ID
            id_item = QtWidgets.QTableWidgetItem(str(m["id"]))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, id_item)

            # 2. Title & Artist
            title_text = f"{m['artist']} - {m['title']}"
            title_item = QtWidgets.QTableWidgetItem(title_text)
            self.table.setItem(row, 2, title_item)

            # 3. Creator / Mapper
            creator_item = QtWidgets.QTableWidgetItem(m["creator"])
            creator_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, creator_item)

            # 4. Diffs & Star Rating
            diffs_str = ", ".join([f"{d['name']} ({d['sr']}*)" for d in m["valid_diffs"][:3]])
            if len(m["valid_diffs"]) > 3:
                diffs_str += f" (+{len(m['valid_diffs'])-3})"
            diffs_item = QtWidgets.QTableWidgetItem(diffs_str)
            diffs_item.setForeground(QtGui.QColor("#2ecc71"))
            self.table.setItem(row, 4, diffs_item)

            # 5. Farm Score
            score_item = QtWidgets.QTableWidgetItem(f"{m['farm_score']}/100")
            score_item.setTextAlignment(Qt.AlignCenter)
            if m['farm_score'] >= 90:
                score_item.setForeground(QtGui.QColor("#2ecc71"))
            elif m['farm_score'] >= 75:
                score_item.setForeground(QtGui.QColor("#f1c40f"))
            else:
                score_item.setForeground(QtGui.QColor("#e67e22"))
            self.table.setItem(row, 5, score_item)

            # 6. Status Column
            status_item = QtWidgets.QTableWidgetItem("Sẵn sàng tải")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QtGui.QColor("#b3a6d4"))
            self.table.setItem(row, 6, status_item)

            # 7. Tags
            tags_str = " | ".join(m.get("best_tags", []))
            tags_item = QtWidgets.QTableWidgetItem(tags_str)
            tags_item.setForeground(QtGui.QColor("#ff66aa"))
            self.table.setItem(row, 7, tags_item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QtWidgets.QHeaderView.Stretch)

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

    def on_table_double_clicked(self, item):
        row = item.row()
        if 0 <= row < len(self.current_maps):
            m = self.current_maps[row]
            audio_url = m.get("preview_audio")
            if audio_url:
                self.play_audio_preview(m["id"], f"{m['artist']} - {m['title']}", audio_url)

    def play_audio_preview(self, set_id, title, audio_url):
        self.playing_set_id = set_id
        self.media_player.setSource(QUrl(audio_url))
        self.media_player.play()
        self.lbl_now_playing.setText(f"▶ Đang phát: <b>{title[:30]}...</b>")
        self.lbl_now_playing.setStyleSheet("color: #2ecc71; font-size: 12px; margin-right: 8px;")
        self.btn_stop_audio.setEnabled(True)

    def stop_audio(self):
        self.media_player.stop()
        self.lbl_now_playing.setText("🎵 Chưa phát audio")
        self.lbl_now_playing.setStyleSheet("color: #b3a6d4; font-size: 12px; margin-right: 8px;")
        self.btn_stop_audio.setEnabled(False)

    def start_parallel_download(self):
        selected_items = []
        for r in range(self.table.rowCount()):
            chk = self.table.item(r, 0)
            if chk and chk.checkState() == Qt.Checked:
                selected_items.append((r, self.current_maps[r]))
                self.table.item(r, 6).setText("Chờ luồng tải...")
                self.table.item(r, 6).setForeground(QtGui.QColor("#f1c40f"))

        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "Chưa chọn map", "Vui lòng tick chọn ít nhất 1 beatmap để tải!")
            return

        songs_dir = self.path_edit.text().strip()
        if not os.path.isdir(songs_dir):
            QtWidgets.QMessageBox.critical(self, "Lỗi", "Thư mục Songs trên ổ cứng không tồn tại!")
            return

        self.btn_search.setEnabled(False)
        self.btn_download.setEnabled(False)
        self.progress_bar.setValue(0)

        max_workers = self.spin_threads.value()
        pref_mirror = self.mirror_keys[self.mirror_combo.currentIndex()]
        no_video = self.chk_no_video.isChecked()

        self.lbl_speed.setText(f"Khởi động {max_workers} luồng...")

        self.download_worker = ParallelDownloadWorker(
            selected_items,
            songs_dir,
            max_workers=max_workers,
            preferred_mirror=pref_mirror,
            no_video=no_video
        )
        self.download_worker.row_progress_signal.connect(self.on_row_progress)
        self.download_worker.overall_progress_signal.connect(self.on_overall_progress)
        self.download_worker.all_finished_signal.connect(self.on_download_all_finished)
        self.download_worker.start()

    def on_row_progress(self, row_idx, status_text, percent):
        item = self.table.item(row_idx, 6)
        if item:
            item.setText(status_text)
            if percent == 100:
                item.setForeground(QtGui.QColor("#2ecc71"))
            elif percent > 0:
                item.setForeground(QtGui.QColor("#3498db"))
            else:
                item.setForeground(QtGui.QColor("#e74c3c"))

    def on_overall_progress(self, completed, total, total_mb, speed_mb):
        pct = int(completed / total * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.lbl_speed.setText(f"Tải {completed}/{total} maps ({speed_mb:.1f} MB/s)")
        self.lbl_status.setText(f"Đang tải song song đa luồng... Đã tải {total_mb:.1f} MB")

    def on_download_all_finished(self, success, fail, total_mb, elapsed):
        self.btn_search.setEnabled(True)
        self.btn_download.setEnabled(True)
        self.progress_bar.setValue(100)
        self.lbl_speed.setText(f"Hoàn thành ({total_mb:.1f} MB trong {elapsed:.1f}s)")
        self.lbl_status.setText(f"Đã tải thành công {success} maps! (Thất bại: {fail})")

        self.installed_ids = config.get_installed_beatmap_ids(self.path_edit.text().strip())
        self.lbl_installed.setText(f"📦 Đã có: <b>{len(self.installed_ids):,} maps</b> (Tự động bỏ qua)")

        msg = (
            f"<b>Đã tải thành công {success} beatmapsets!</b> ({total_mb:.1f} MB trong {elapsed:.1f}s)<br>"
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
