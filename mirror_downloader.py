import os
import re
import time
import urllib.request
import urllib.error

MIRRORS = [
    {
        "name": "osu.direct",
        "url_template": "https://osu.direct/api/d/{set_id}",
        "supports_novideo": False
    },
    {
        "name": "Catboy (Mino)",
        "url_template": "https://catboy.best/d/{set_id}{novideo_flag}",
        "supports_novideo": True
    },
    {
        "name": "Sayobot",
        "url_template": "https://dl.sayobot.cn/beatmaps/download/{variant}/{set_id}",
        "supports_novideo": True
    },
    {
        "name": "Beatconnect",
        "url_template": "https://beatconnect.io/b/{set_id}",
        "supports_novideo": False
    }
]

def sanitize_filename(filename):
    """
    Làm sạch tên file để tương thích an toàn tuyệt đối với mọi hệ thống file trên Linux
    và ổ cứng ngoài (NTFS, exFAT, ext4, FAT32).
    """
    # Loại bỏ ký tự cấm: \ / : * ? " < > |
    clean = re.sub(r'[\\/*?:"<>|]', '', filename)
    # Loại bỏ khoảng trắng thừa
    clean = clean.strip()
    return clean[:120]  # giới hạn độ dài an toàn

def build_mirror_urls(set_id, no_video=True):
    urls = []
    # 1. osu.direct
    urls.append(("osu.direct", f"https://osu.direct/api/d/{set_id}"))

    # 2. Catboy (Mino)
    nv_flag = "n" if no_video else ""
    urls.append(("Catboy (Mino)", f"https://catboy.best/d/{set_id}{nv_flag}"))

    # 3. Sayobot
    variant = "mini" if no_video else "full"
    urls.append(("Sayobot", f"https://dl.sayobot.cn/beatmaps/download/{variant}/{set_id}"))

    # 4. Beatconnect (dự phòng)
    urls.append(("Beatconnect", f"https://beatconnect.io/b/{set_id}"))

    return urls

def download_beatmapset(
    set_info,
    destination_dir,
    no_video=True,
    progress_callback=None
):
    """
    Tải một beatmapset (.osz) về thư mục Songs trên ổ cứng ngoài.
    Trả về (thành công: bool, thông điệp: str, đường_dẫn_file: str)
    """
    set_id = set_info["id"]
    artist = set_info.get("artist", "Unknown")
    title = set_info.get("title", "Unknown")

    clean_artist = sanitize_filename(artist)
    clean_title = sanitize_filename(title)
    final_filename = f"{set_id} {clean_artist} - {clean_title}.osz"
    final_path = os.path.join(destination_dir, final_filename)
    part_path = final_path + ".part"

    # Nếu file đã tồn tại và hợp lệ, bỏ qua
    if os.path.isfile(final_path) and os.path.getsize(final_path) > 10000:
        return True, "Đã có sẵn", final_path

    mirror_list = build_mirror_urls(set_id, no_video=no_video)
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

    last_error = ""

    for mirror_name, mirror_url in mirror_list:
        try:
            req = urllib.request.Request(mirror_url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                # Kiểm tra HTTP status
                if response.status != 200:
                    last_error = f"HTTP {response.status}"
                    continue

                total_size = response.headers.get("Content-Length")
                total_bytes = int(total_size) if total_size and total_size.isdigit() else 0

                downloaded = 0
                start_time = time.time()

                with open(part_path, "wb") as f_out:
                    first_chunk = True
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break

                        # Kiểm tra magic bytes zip archive (PK\x03\x04) ở chunk đầu tiên
                        if first_chunk:
                            first_chunk = False
                            if not chunk.startswith(b"PK"):
                                # Không phải file zip hợp lệ (có thể là trang HTML lỗi hoặc rate limit)
                                raise ValueError("Nội dung không phải file .osz hợp lệ (không có zip header PK)")

                        f_out.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback:
                            elapsed = max(time.time() - start_time, 0.001)
                            speed_kb = (downloaded / 1024) / elapsed
                            progress_callback(set_id, downloaded, total_bytes, speed_kb, mirror_name)

                # Kiểm tra dung lượng tối thiểu (> 50KB)
                if downloaded < 50000:
                    if os.path.exists(part_path):
                        os.remove(part_path)
                    raise ValueError(f"Dung lượng tải về quá nhỏ ({downloaded} bytes)")

                # Đổi tên file atomic từ .part thành .osz
                os.replace(part_path, final_path)
                return True, f"Thành công ({mirror_name})", final_path

        except Exception as e:
            last_error = str(e)
            if os.path.exists(part_path):
                try:
                    os.remove(part_path)
                except Exception:
                    pass
            continue

    return False, f"Thất bại tất cả mirror ({last_error})", ""
