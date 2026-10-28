# 🎵 osu! Ranked Farm Maps Downloader (Linux & External Drive)

[![License: MIT](https://img.shields.io/badge/License-MIT-pink.svg)](https://opensource.org/licenses/MIT)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-blue.svg)](https://archlinux.org/)
[![GUI: PySide6](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41cd52.svg)](https://wiki.qt.io/Qt_for_Python)
[![Profile: Cao Mi Le](https://img.shields.io/badge/Profile-Cao%20Mi%20Le%20(%2312k)-ff66aa.svg)](https://osu.ppy.sh/users/10910765)
[![Release: v1.2.0](https://img.shields.io/badge/Release-v1.2.0-brightgreen.svg)](https://github.com/AtelierMizumi/osu-farm-downloader/releases)

Công cụ tìm kiếm, lọc và tải beatmap **mở rộng toàn diện (Open Catalog Discovery)** từ nhiều nguồn Mirror siêu tốc (`osu.direct`, `Catboy/Mino`, `Sayobot`, `Beatconnect`, `Nerinyan`).

Hỗ trợ **Desktop GUI (PySide6)** hiện đại lẫn **Terminal CLI**, tối ưu hóa riêng cho người dùng **Linux** và **osu! stable lưu trên ổ cứng ngoài**, đồng thời tùy chỉnh chính xác theo trình độ profile **`Cao Mi Le`** (Rank #12k Global / #155 Việt Nam, ~9,100 PP).

---

## 🌟 Cải tiến đột phá trong v1.2.0: Quét Mở Toàn Bộ Kho Map (Open Traversal)

Thay vì giới hạn gò bó vào một vài mapper/artist cũ kỹ (khiến việc tìm kiếm bị cạn kiệt map nếu máy đã tải nhiều), phiên bản 1.2.0 mang đến cuộc cách mạng về logic tìm kiếm:

### 1. 🌍 Loại bỏ hoàn toàn giới hạn theo Mapper / Artist
- **Khám phá toàn diện:** Kho map osu! có hàng trăm ngàn bài hát từ hàng ngàn mapper tài năng khác nhau. Công cụ quét mở trên toàn bộ danh mục của osu! mà không thiên vị bất kỳ tác giả nào.
- **Quét sâu nhiều trang đồng thời (Parallel Offset Traversal):** Tự động duyệt qua hàng ngàn mapset (`10 - 50 trang = 1,000 – 5,000 maps`) chỉ trong vài giây.
- **Đảm bảo luôn có map mới:** Dù trong máy bạn đã có hàng ngàn map, công cụ vẫn luôn đào sâu vào kho lưu trữ để tìm ra hàng chục, hàng trăm map phù hợp chưa từng tải!

### 2. 🧠 Thuật toán Chấm điểm Farm Dựa trên Chỉ số Kỹ thuật Thực tế
Độ "dễ farm" được tính toán khách quan 100% dựa trên dữ liệu thật của từng difficulty:
- **Tỷ lệ Pass Rate ($\frac{\text{Passcount}}{\text{Playcount}}$):** Map có tỷ lệ pass cao ($\ge 20\% - 30\%$) chứng minh pattern mượt, công bằng và không có chốt spike bất ngờ ở cuối bài.
- **Circle Size (CS) Vàng:** Tỉ lệ vàng của jump farm là **CS 3.8 – 4.3** (hitbox thoải mái). CS $> 4.6$ bị trừ điểm vì đòi hỏi độ chính xác ngón tay quá cao.
- **Approach Rate (AR) Chuẩn:** AR 9.3 – 9.8 phù hợp phản xạ của rank 12k.
- **Độ dài TV Size (60s – 135s):** Retry nhanh, đỡ tốn thể lực, ít choke.
- **Phổ biến:** Lượt chơi & yêu thích từ cộng đồng.

### 3. 🎛 Tiêu chí Sắp xếp Linh hoạt (Sort By)
- `🏆 Dễ farm & Thoải mái nhất (Smart Farm Score)`: Xếp các map có tỷ lệ pass cao, CS/AR đẹp lên đầu.
- `🔥 Nhiều người chơi nhất (Playcount)`: Các map quốc dân được nhiều người chơi nhất.
- `❤️ Được yêu thích nhất (Favourites)`: Các map được cộng đồng thả tim nhiều nhất.
- `🆕 Mới nhất (Newest Ranked)`: Các map vừa mới được xếp hạng gần đây.
- `⭐ Star Rating tăng / giảm dần`.

### 4. ⚡ Tải Song Song Đa Luồng (Parallel 1 – 8 Threads)
- Tải đồng thời nhiều bài hát cùng lúc với tốc độ cực nhanh **8 – 15 MB/s**.
- Hiển thị tiến trình từng hàng trong bảng thời gian thực.

### 5. 🎧 Nghe Thử Audio Preview Ngay Trong Ứng Dụng
- Tích hợp trình phát âm thanh mẫu (`QMediaPlayer` + FFmpeg).
- Chỉ cần **Double-click vào bất kỳ bài hát nào trong bảng** để nghe thử đoạn cao trào 10 giây trước khi quyết định tải!

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
* **Bộ lọc Mở Toàn Diện:** Chuyển đổi nhanh Nomod, DT, HR, Tình trạng map (Ranked/Loved...), Tiêu chí sắp xếp và Độ sâu quét.
* **Từ khóa tự do:** Tìm theo anime, tên bài, thể loại (hoặc để trống để quét tất cả).
* **Bảng Map & Checkbox:** Chọn bài linh hoạt, xem Farm Score và Tags đánh giá trước khi tải.
* **Tải song song:** Điều chỉnh số luồng tải từ 1 đến 8 luồng.

---

## 💻 Hướng dẫn Dòng lệnh (CLI One-Liner)

```bash
# Quét mở toàn bộ kho map đề xuất theo trình độ (6.5* - 7.6* Nomod/HD), tải song song 4 luồng:
osu-dl --count 30 --threads 4

# Quét sâu 30 trang (3,000 maps) tìm các bài có lượt chơi cao nhất:
osu-dl --depth 30 --sort plays --count 40

# Tìm kiếm map theo từ khóa tự do (ví dụ: anime, camellia, hololive):
osu-dl -q "hololive" --min-sr 6.5 --max-sr 7.5 --count 20

# Tải gói DT Farm (tải 6 luồng siêu tốc):
osu-dl --dt --count 25 --threads 6

# Lọc map Loved có Star Rating từ 6.8* đến 7.6*:
osu-dl --status loved --min-sr 6.8 --max-sr 7.6 --count 20

# Mở giao diện Desktop GUI:
osu-dl --gui
```

---

## 🎮 Cách nạp map vào osu! stable trên Linux
1. Sau khi tải xong, các map `.osz` sẽ nằm sẵn trong thư mục `Songs/` trên ổ cứng ngoài.
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
