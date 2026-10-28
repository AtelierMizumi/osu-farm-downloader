# 🎵 osu! Ranked Farm Maps Downloader (Linux & External Drive)

[![License: MIT](https://img.shields.io/badge/License-MIT-pink.svg)](https://opensource.org/licenses/MIT)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-blue.svg)](https://archlinux.org/)
[![GUI: PySide6](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41cd52.svg)](https://wiki.qt.io/Qt_for_Python)
[![Profile: Cao Mi Le](https://img.shields.io/badge/Profile-Cao%20Mi%20Le%20(%2312k)-ff66aa.svg)](https://osu.ppy.sh/users/10910765)

Công cụ tự động tìm kiếm, lọc và tải beatmap **Ranked**, **nhiều người chơi nhất (Most Played)**, **dễ farm (Comfort / Jump / Flow aim)** từ các Mirror siêu tốc (`osu.direct`, `Catboy/Mino`, `Sayobot`, `Beatconnect`).

Được trang bị cả giao diện đồ họa **Desktop GUI (PySide6)** hiện đại lẫn giao diện **Terminal CLI**, tối ưu hóa riêng cho người dùng **Linux** và **osu! stable lưu trên ổ cứng ngoài**.

---

## 🌟 Tính năng nổi bật

### 1. 🧠 Thuật toán Lọc Map Thông Minh (Smart Farm Score 0 – 100)
Không chỉ đơn thuần tìm map theo Star Rating, công cụ tính toán điểm số Farmability dựa trên các chỉ số cốt lõi:
- **Tỷ lệ Pass Rate ($\frac{\text{Pass}}{\text{Plays}}$):** Ưu tiên các map có pass rate $\ge 18\% - 25\%$, chứng minh pattern mượt, công bằng và ít choke ở note cuối. Phạt các map có pass rate $< 8\%$.
- **Circle Size (CS) Vàng:** Tỉ lệ vàng của jump farm là CS 3.8 – 4.3 (hitbox vừa vặn). Phạt nặng các map CS quá nhỏ ($CS > 4.6$).
- **Approach Rate (AR) Chuẩn:** AR 9.3 – 9.8 phù hợp phản xạ của người chơi từ 4-digit tới 5-digit rank.
- **Độ dài tối ưu (Hit Length):** Ưu tiên độ dài TV Size / Cut Ver (65s – 150s) giúp retry nhanh, ít tốn thể lực và đỡ choke.
- **Phân loại phong cách Mapper:**
  - *Jump Farm:* Sotarks, Reform, browiec, Nevo, Kowari, fieryrage, Akitoshi, Monstrata, Taeyang, Armin, Doormat.
  - *Flow Aim / Speed:* Seni, SMOKELIND, Log Off Now, Chanci, Mirash.
  - *Stream / Finger Control:* Lasse, Awaken, Lami, Djulus, Kroytz.

### 2. 👤 Cá nhân hóa theo Profile Người chơi (`Cao Mi Le`)
- Tự động đồng bộ và phân tích dữ liệu Top Plays của profile osu! **`Cao Mi Le`** (Rank #12,936 Global | #155 Việt Nam | 9,096 PP).
- Đề xuất các preset chuẩn xác cho từng mod:
  - **Nomod / Hidden Farm:** `6.48* – 7.62*` (Trọng tâm: ~`7.03*` | 420pp - 540pp).
  - **HardRock (HR/HDHR):** `6.10* – 6.75*` (Trọng tâm: ~`6.45*` | 400pp - 450pp).
  - **DoubleTime (DT/NC):** `4.80* – 5.50*` base SR (-> 6.8* - 7.8* DT).

### 3. 💾 Hỗ trợ Ổ cứng ngoài & osu! stable trên Linux
- **Tự động nhận diện điểm mount ổ cứng ngoài:** `/mnt/SSDStorage/osu!/Songs`, `/media/...`, `/run/media/...`, hoặc thư mục Wine/Lutris/Bottles.
- **Chống tải trùng map:** Quét toàn bộ các folder và file `.osz` hiện có trên ổ cứng (hơn 1,600+ maps) trong 0.01s và tự động bỏ qua khi tải, tiết kiệm dung lượng ổ cứng tối đa.
- **Làm sạch tên file:** Đảm bảo tên file `.osz` an toàn tuyệt đối trên mọi định dạng phân vùng (NTFS, exFAT, ext4).

### 4. ⚡ Hệ thống Multi-Mirror siêu tốc & Fallback tự động
- Ưu tiên 1: **osu.direct API** (Băng thông cao, không rate-limit khó chịu).
- Ưu tiên 2: **Catboy (Mino)**.
- Ưu tiên 3: **Sayobot** (Hỗ trợ mini no-video nhẹ, nhanh).
- Dự phòng: **Beatconnect**.
- Tải file dạng `.part` an toàn, kiểm tra magic bytes `PK\x03\x04` trước khi ghi để chống file lỗi hoặc 0-byte.

---

## 🖥 Giao diện Đồ họa Desktop GUI (PySide6)

Giao diện Dark Mode lấy cảm hứng từ osu! với đầy đủ tính năng:
- **Profile Card:** Hiển thị Rank, PP, Accuracy và khoảng SR đề xuất.
- **Thư mục Songs:** Nhận diện sẵn ổ cứng ngoài, có nút chọn đường dẫn nhanh.
- **Bộ lọc linh hoạt:** Chuyển đổi giữa Nomod, DT Farm, HR Farm hoặc lọc theo Mapper tủ.
- **Bảng xem trước & Chọn bài:** Xem ID, Tên bài, Mapper, Diffs, Farm Score (0-100) và các Tags đánh giá trước khi quyết định tải.
- **Tiến trình tải thời gian thực:** Hiển thị tốc độ (MB/s), phần trăm, nguồn mirror và trạng thái từng bài.

---

## 📥 Cài đặt & Sử dụng

### Cách 1: Tải bản thực thi Standalone (Khuyên dùng - Không cần cài Python)
1. Tải bản build Linux x86_64 mới nhất từ mục [**Releases**](https://github.com/AtelierMizumi/osu-farm-downloader/releases).
2. Mở terminal tại thư mục chứa file tải về và cấp quyền thực thi:
   ```bash
   chmod +x osu-farm-downloader-linux-x86_64
   ./osu-farm-downloader-linux-x86_64
   ```

### Cách 2: Chạy trực tiếp từ mã nguồn Python

Yêu cầu: `python >= 3.9` và `PySide6`.

1. Clone repository:
   ```bash
   git clone https://github.com/AtelierMizumi/osu-farm-downloader.git
   cd osu-farm-downloader
   ```

2. Cài đặt dependencies (nếu chưa có):
   ```bash
   pip install -r requirements.txt
   # hoặc:
   pip install PySide6
   ```

3. Khởi chạy:
   - **Mở giao diện GUI:**
     ```bash
     python3 gui.py
     ```
   - **Mở giao diện Terminal tương tác:**
     ```bash
     python3 osu_dl.py
     ```

### Cách 3: Chạy nhanh qua dòng lệnh (CLI One-Liner)

Công cụ hỗ trợ các tham số dòng lệnh phong phú cho người thích dùng terminal:

```bash
# Tải 30 map farm Nomod/HD chuẩn trình độ:
python3 osu_dl.py --count 30

# Tải 20 map farm của Sotarks:
python3 osu_dl.py --mapper Sotarks --count 20

# Tải gói DT Farm:
python3 osu_dl.py --dt --count 25

# Tùy chỉnh khoảng Star Rating bất kỳ:
python3 osu_dl.py --min-sr 6.8 --max-sr 7.5 --count 15

# Mở GUI qua cờ lệnh:
python3 osu_dl.py --gui
```

---

## 🎮 Cách nạp map vào osu! stable trên Linux

Sau khi quá trình tải hoàn tất:
1. Mở **osu! stable** trên Linux (qua Wine, Lutris hoặc Bottles).
2. Vào màn hình **Solo / Song Select** (chọn bài hát).
3. Nhấn phím **`F5`** trên bàn phím.
4. osu! stable sẽ tự động quét thư mục `Songs/` trên ổ cứng ngoài, giải nén các file `.osz` vừa tải và cập nhật ngay vào danh sách bài hát!

---

## 🛠 Tự Build Standalone Binary

Nếu bạn muốn tự đóng gói ra file nhị phân Linux độc lập:
```bash
./build_release.sh
```
File thực thi độc lập sẽ được tạo trong thư mục `dist/`.

---

## 📄 License
Phát hành theo giấy phép [MIT License](LICENSE).
Tự do sử dụng, chỉnh sửa và phân phối!
