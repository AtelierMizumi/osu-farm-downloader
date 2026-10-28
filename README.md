# 🎵 osu! Ranked Farm Maps Downloader (Linux & External Drive)

[![License: MIT](https://img.shields.io/badge/License-MIT-pink.svg)](https://opensource.org/licenses/MIT)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-blue.svg)](https://archlinux.org/)
[![GUI: PySide6](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41cd52.svg)](https://wiki.qt.io/Qt_for_Python)
[![Profile: Cao Mi Le](https://img.shields.io/badge/Profile-Cao%20Mi%20Le%20(%2312k)-ff66aa.svg)](https://osu.ppy.sh/users/10910765)
[![Release: v1.1.0](https://img.shields.io/badge/Release-v1.1.0-brightgreen.svg)](https://github.com/AtelierMizumi/osu-farm-downloader/releases)

Công cụ tìm kiếm, lọc và tải beatmap **song song đa luồng (Parallel Multi-threading)** từ nhiều nguồn Mirror siêu tốc (`osu.direct`, `Catboy/Mino`, `Sayobot`, `Beatconnect`, `Nerinyan`).

Hỗ trợ **Desktop GUI (PySide6)** phong cách osu! và **Terminal CLI**, tối ưu hóa riêng cho người dùng **Linux** và **osu! stable lưu trên ổ cứng ngoài**, đồng thời tùy chỉnh theo trình độ profile **`Cao Mi Le`** (Rank #12k Global / #155 Việt Nam, ~9,100 PP).

---

## 🌟 Tính năng vượt trội (So sánh & Chắt lọc từ các tool GitHub)

Dựa trên nghiên cứu các công cụ nổi tiếng trên GitHub như *nzbasic/batch-beatmap-downloader*, *osu-collector*, *NexDirect*, dự án đã chắt lọc và tối ưu các chức năng quan trọng nhất:

### 1. ⚡ Tải Song Song Đa Luồng (Parallel Multi-Threading 1 – 8 Threads)
- Thay vì tải tuần tự từng file mất nhiều thời gian, công cụ phân phối tải song song từ **1 đến 8 luồng đồng thời**.
- Tốc độ tải thực tế: Đạt **8 – 15 MB/s**, tải 30 mapset trong vòng **chưa đầy 20 – 30 giây**!
- Cập nhật tiến trình và trạng thái tải chi tiết theo từng dòng trong bảng.

### 2. 🎛 Bộ Lọc Tình Trạng Map (Beatmap Status Filter)
Hỗ trợ lọc chính xác theo trạng thái xếp hạng:
- **`Ranked` (Mặc định):** Map chính thức, có điểm PP, có Leaderboard.
- **`Ranked + Approved`:** Bao gồm cả các map kinh điển được phê duyệt (Approved) có tính PP.
- **`Loved`:** Các map được cộng đồng bình chọn yêu thích, có bảng xếp hạng Leaderboard riêng.
- **`Qualified`:** Các map đang trong tuần thử nghiệm cuối cùng trước khi vào Ranked.
- **`Tất cả có Leaderboard`:** Gộp toàn bộ Ranked + Approved + Loved.
- **`Tất cả trạng thái`:** Bao gồm cả Pending và Graveyard.

### 3. 🌐 Tùy Chọn Nguồn Mirror Đa Dạng & Smart Fallback
Hỗ trợ 5 nguồn Mirror hàng đầu với cơ chế tự động chuyển đổi nếu một mirror bị nghẽn:
1. **osu.direct API** *(Mặc định - Băng thông cao, ổn định nhất)*
2. **Catboy / Mino (`catboy.best`)** *(Cực kỳ phổ biến trong cộng đồng osu!)*
3. **Sayobot (`dl.sayobot.cn`)** *(Máy chủ Châu Á, hỗ trợ bản Mini cắt video siêu nhẹ)*
4. **Beatconnect (`beatconnect.io`)**
5. **Nerinyan (`api.nerinyan.moe`)**

### 4. 🎧 Nghe Thử Audio Preview Ngay Trong Ứng Dụng
- Tích hợp trực tiếp trình phát âm thanh mẫu (`QMediaPlayer` + FFmpeg).
- Chỉ cần **Double-click vào bất kỳ bài hát nào trong bảng** (hoặc nhấn nút Dừng ở góc trên) để nghe thử đoạn cao trào 10 giây trước khi quyết định tải về!

### 5. 🧠 Thuật Toán Smart Farm & Comfort Score (0 – 100)
- **Tỷ lệ Pass Rate ($\frac{\text{Pass}}{\text{Plays}}$):** Đánh giá pattern mượt mà ($\ge 18\% - 25\%$), phạt các map dễ choke ($< 8\%$).
- **Hitbox Circle Size (CS) Vàng:** Tỉ lệ vàng của jump farm là **CS 3.8 – 4.3**. Phạt map CS quá nhỏ ($CS > 4.6$).
- **Approach Rate (AR) Chuẩn:** AR 9.3 – 9.8.
- **Độ dài TV Size (65s – 150s):** Retry nhanh, đỡ tốn thể lực.
- **Phân loại Mapper:** Jump Farm (Sotarks, Reform, browiec,...), Flow Aim (Seni, SMOKELIND,...), Stream (Lasse, Awaken,...).

### 6. 💾 Tương Thích Hoàn Hảo Ổ Cứng Ngoài & Linux
- Tự động nhận diện thư mục Songs của osu! stable trên ổ cứng ngoài: `/mnt/SSDStorage/osu!/Songs`.
- **Tự động quét và bỏ qua map đã có sẵn** (hơn 1,600+ maps) để tránh trùng lặp.
- Tên file được làm sạch an toàn cho mọi định dạng phân vùng (NTFS, exFAT, ext4).

---

## 🖥 Giao diện Desktop GUI (PySide6)

Khởi chạy bằng lệnh:
```bash
osu-dl-gui
```
Giao diện bao gồm:
* **Thẻ Người chơi:** Profile `Cao Mi Le` (Rank #12k, 9.1k PP, 98.32% Acc) & Star Rating gợi ý.
* **Bộ phát Audio Preview:** Nghe thử bài hát ngay trên thanh tiêu đề.
* **Thư mục Songs:** Nhận diện sẵn ổ cứng ngoài, có nút chọn đường dẫn nhanh.
* **Bộ lọc Presets & Tình trạng:** Chuyển đổi nhanh Nomod, DT, HR, Mapper, Tình trạng map (Ranked/Loved...).
* **Cài đặt Tải song song & Mirror:** Chọn số luồng (1-8 luồng) và mirror mong muốn.
* **Bảng Map & Checkbox:** Chọn bài linh hoạt, xem Farm Score và Tags đánh giá trước khi tải.

---

## 💻 Hướng dẫn Dòng lệnh (CLI One-Liner)

```bash
# Tải song song 4 luồng 30 map farm Nomod/HD (6.5* - 7.6*):
osu-dl --count 30 --threads 4

# Tải 20 map Loved có Star Rating từ 6.8* đến 7.5*:
osu-dl --status loved --min-sr 6.8 --max-sr 7.5 --count 20

# Tải 20 map của Sotarks ưu tiên nguồn Sayobot:
osu-dl --mapper Sotarks --mirror sayobot --count 20

# Tải gói DT Farm (tải 6 luồng siêu tốc):
osu-dl --dt --count 25 --threads 6

# Mở giao diện Desktop GUI:
osu-dl --gui
```

---

## 🎮 Cách nạp map vào osu! stable trên Linux
1. Sau khi tải xong, các file `.osz` sẽ nằm sẵn trong thư mục `Songs/` trên ổ cứng ngoài.
2. Mở **osu! stable** trên Linux (qua Wine, Lutris hoặc Bottles).
3. Vào màn hình **Solo / Song Select** (chọn bài hát).
4. Nhấn phím **`F5`** trên bàn phím. osu! stable sẽ tự động quét, giải nén và nạp tất cả các map mới vào game ngay lập tức!

---

## 🛠 Tự Build Standalone Binary
```bash
./build_release.sh
```
File thực thi Linux x86_64 độc lập sẽ được tạo trong thư mục `dist/`.

---

## 📄 License
Phát hành theo giấy phép [MIT License](LICENSE).
Mã nguồn công khai: [GitHub Repository](https://github.com/AtelierMizumi/osu-farm-downloader).
