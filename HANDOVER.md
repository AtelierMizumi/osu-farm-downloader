# 🤝 PROJECT HANDOVER: osu-farm-downloader

Tài liệu bàn giao toàn diện dành cho lập trình viên hoặc AI Agent tiếp quản dự án.

---

## 📌 1. Tổng quan Dự án (Project Overview)
- **Tên dự án:** `osu-farm-downloader`
- **Mục đích:** Công cụ tìm kiếm, lọc và tải beatmap osu! thông minh, đa luồng song song từ các Mirror siêu tốc, tối ưu hóa cho **Linux** và **osu! stable lưu trên ổ cứng ngoài**.
- **Người dùng chính (Target User Profile):**
  - Username: **`Cao Mi Le`** (User ID: `10910765`)
  - Rank hiện tại: **#12,936 Global** | **#155 Việt Nam**
  - Performance: **9,096.2 PP** | Accuracy: **98.32%**
  - Khoảng Star Rating lý tưởng:
    - **Nomod / Hidden Farm:** `6.48* – 7.62*` (Trọng tâm: `~7.03*` cho vùng farm 420 - 540pp)
    - **DoubleTime (DT) Farm:** `4.80* – 5.50*` base SR (-> 6.8* - 7.8* DT)
    - **HardRock (HR) Farm:** `6.10* – 6.75*` base SR (-> 6.5* - 7.3* HR)

---

## 📍 2. Vị trí Lưu trữ & Môi trường Hệ thống (Locations & Environment)
- **Thư mục làm việc (Workspace):**
  `/home/thuanc177/Projects/Tools/osu-farm-downloader`
- **Kho lưu trữ GitHub (Public):**
  - Repository: `https://github.com/AtelierMizumi/osu-farm-downloader`
  - Releases: `https://github.com/AtelierMizumi/osu-farm-downloader/releases` (Bản hiện tại: `v1.2.0`)
- **Đường dẫn thư mục Songs (Ổ cứng ngoài):**
  `/mnt/SSDStorage/osu!/Songs` (Đã có hơn 1,630+ beatmapsets)
- **File cấu hình người dùng:**
  `~/.config/osu-farm-downloader/config.json`
- **Lệnh thực thi toàn hệ thống (Symlinks trong `$PATH`):**
  - `osu-dl-gui` $\to$ `/home/thuanc177/Projects/Tools/osu-farm-downloader/gui.py`
  - `osu-dl` $\to$ `/home/thuanc177/Projects/Tools/osu-farm-downloader/osu_dl.py`
- **Môi trường kỹ thuật:**
  - OS: Arch Linux (x86_64, Wayland/X11)
  - Python: 3.12+ (hỗ trợ `PySide6`, `requests`, `urllib`)
  - Build Tool: `uv tool run --with PySide6 pyinstaller`

---

## 🏗 3. Kiến trúc Mã nguồn (Codebase Architecture)
```
/home/thuanc177/Projects/Tools/osu-farm-downloader/
├── gui.py                   # Giao diện Desktop GUI (PySide6 / Qt6, dark mode osu!)
├── osu_dl.py                # Giao diện tương tác & dòng lệnh Terminal CLI
├── map_finder.py            # Thuật toán quét mở danh mục osu! & chấm điểm Farm Score
├── mirror_downloader.py     # Bộ máy tải song song đa luồng (1-8 threads) qua 5 mirrors
├── profile_service.py       # Phân tích chỉ số profile & top plays của Cao Mi Le
├── config.py                # Quản lý đường dẫn Songs, tự nhận diện ổ cứng, chống trùng map
├── build_release.sh         # Script tự động build standalone Linux binary (PyInstaller)
├── pyproject.toml           # Cấu hình package Python chuẩn
├── requirements.txt         # Dependencies (PySide6)
├── dist/                    # Thư mục chứa file binary đã build độc lập
└── README.md                # Tài liệu hướng dẫn sử dụng chi tiết
```

---

## ⚡ 4. Các tính năng cốt lõi đã hoàn thành
1. **Quét mở toàn bộ kho beatmap (Open Catalog Traversal):**
   - Không gò bó vào bất kỳ mapper hay artist nào (loại bỏ hoàn toàn hardcoded mappers).
   - Quét sâu đồng thời nhiều trang danh mục (`10 - 50 trang = 1,000 – 5,000 maps`) bằng `ThreadPoolExecutor`.
   - Lọc bỏ tuyệt đối các map đã có sẵn trong ổ cứng ngoài (`/mnt/SSDStorage/osu!/Songs`).
2. **Chấm điểm "Dễ Farm" thuần túy theo chỉ số kỹ thuật (0 - 100):**
   - **Pass Rate:** $\ge 20\% - 30\%$ (+20đ), phạt map $< 8\%$ (-15đ).
   - **CS:** 3.8 – 4.3 là tỉ lệ vàng (+15đ), CS $> 4.6$ (-15đ).
   - **AR:** 9.3 – 9.8 tối ưu (+12đ).
   - **Hit Length:** TV Size 60s - 135s (+18đ).
   - **Lượt chơi & Yêu thích:** Plays $> 300\text{k}$ hoặc Favs $> 800$ (+15đ).
3. **Bộ lọc trạng thái xếp hạng (Status Filter):**
   - `Ranked`, `Ranked + Approved`, `Loved`, `Qualified`, `Tất cả có Leaderboard`, `Tất cả trạng thái`.
4. **Tải Song Song Đa Luồng (1 – 8 Threads):**
   - Đạt tốc độ **8 – 15 MB/s**, tải 30 mapset trong 20s.
   - Bảng hiển thị tiến trình tải chi tiết từng hàng theo thời gian thực.
5. **Hỗ trợ 5 Mirror Fallback:**
   - `osu.direct` $\to$ `Catboy/Mino` $\to$ `Sayobot` $\to$ `Beatconnect` $\to$ `Nerinyan`.
   - Kiểm tra magic bytes zip archive `PK\x03\x04` trước khi ghi file, chống file rác/hỏng.
6. **Audio Preview Player:**
   - Double-click vào hàng bất kỳ trên GUI để nghe thử đoạn cao trào 10s trước khi tải.
7. **Tương thích osu! stable trên Linux:**
   - Tải file `.osz` trực tiếp vào thư mục Songs trên ổ cứng ngoài.
   - Nhấn **F5** trong màn hình Song Select của osu! để game tự động giải nén và nạp map.

---

## 🔮 5. Lộ trình phát triển tiếp theo (Next Steps / Roadmap)
1. **Trình tạo Collection tự động (`collection.db`):**
   - Tự động ghi vào file `collection.db` của osu! để gom các bài mới tải vào một Collection riêng (ví dụ: *"Farm 7* - Cao Mi Le"*).
2. **Bộ nhớ đệm Offline Cache (SQLite):**
   - Lưu trữ metadata beatmaps cục bộ để tìm kiếm và lọc tức thì (dưới 0.1s) không phụ thuộc API.
3. **Biểu đồ độ khó trực quan (Strain Graph):**
   - Hiển thị biểu đồ phân bổ nốt bấm (Aim spike, Speed spike) của từng difficulty ngay trong GUI.
4. **Tự động reload osu! (IPC / Wine):**
   - Tự động gửi tín hiệu phím F5 tới cửa sổ `osu!.exe` đang chạy trong Wine/Proton sau khi tải xong.

---

## 📋 6. Lệnh kiểm tra nhanh (Verification Commands)
```bash
# 1. Chạy GUI:
osu-dl-gui
# hoặc: python3 /home/thuanc177/Projects/Tools/osu-farm-downloader/gui.py

# 2. Chạy CLI:
osu-dl --help
osu-dl --count 20 --threads 4

# 3. Build lại binary release:
cd /home/thuanc177/Projects/Tools/osu-farm-downloader && ./build_release.sh
```
