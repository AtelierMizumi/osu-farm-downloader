import os
import re
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

MIRROR_PROVIDERS = {
    "auto": "Tự động (Smart Fallback - Khuyên dùng)",
    "osu.direct": "osu.direct (Tốc độ cao, không giới hạn)",
    "catboy": "Catboy / Mino (catboy.best)",
    "sayobot": "Sayobot (dl.sayobot.cn - Máy chủ Châu Á)",
    "beatconnect": "Beatconnect (beatconnect.io)",
    "nerinyan": "Nerinyan (api.nerinyan.moe)"
}

def sanitize_filename(filename):
    """
    Làm sạch tên file để tương thích an toàn tuyệt đối với mọi hệ thống file trên Linux
    và ổ cứng ngoài (NTFS, exFAT, ext4, FAT32).
    """
    clean = re.sub(r'[\\/*?:"<>|]', '', filename)
    clean = clean.strip()
    return clean[:120]

def build_mirror_urls(set_id, preferred_mirror="auto", no_video=True):
    """
    Xây dựng danh sách URLs mirror theo thứ tự ưu tiên.
    Nếu người dùng chọn một mirror cụ thể, mirror đó sẽ được thử đầu tiên.
    """
    nv_flag = "n" if no_video else ""
    sayo_variant = "mini" if no_video else "full"

    mirror_map = {
        "osu.direct": ("osu.direct", f"https://osu.direct/api/d/{set_id}"),
        "catboy": ("Catboy (Mino)", f"https://catboy.best/d/{set_id}{nv_flag}"),
        "sayobot": ("Sayobot", f"https://dl.sayobot.cn/beatmaps/download/{sayo_variant}/{set_id}"),
        "beatconnect": ("Beatconnect", f"https://beatconnect.io/b/{set_id}"),
        "nerinyan": ("Nerinyan", f"https://api.nerinyan.moe/d/{set_id}{'?noVideo=true' if no_video else ''}")
    }

    urls = []
    # Nếu chọn mirror cụ thể, thêm lên đầu
    if preferred_mirror in mirror_map and preferred_mirror != "auto":
        urls.append(mirror_map[preferred_mirror])

    # Thêm các mirror còn lại theo thứ tự ổn định nhất
    fallback_order = ["osu.direct", "catboy", "sayobot", "beatconnect", "nerinyan"]
    for key in fallback_order:
        item = mirror_map[key]
        if item not in urls:
            urls.append(item)

    return urls

def download_beatmapset(
    set_info,
    destination_dir,
    preferred_mirror="auto",
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
    part_path = final_path + f".{os.getpid()}_{int(time.time()*1000)%10000}.part"

    # Nếu file đã tồn tại và hợp lệ, bỏ qua
    if os.path.isfile(final_path) and os.path.getsize(final_path) > 10000:
        return True, "Đã có sẵn", final_path

    mirror_list = build_mirror_urls(set_id, preferred_mirror=preferred_mirror, no_video=no_video)
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

    last_error = ""

    for mirror_name, mirror_url in mirror_list:
        try:
            req = urllib.request.Request(mirror_url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
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
                                raise ValueError("Nội dung không phải file .osz hợp lệ (không có zip header PK)")

                        f_out.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback:
                            elapsed = max(time.time() - start_time, 0.001)
                            speed_kb = (downloaded / 1024) / elapsed
                            progress_callback(set_id, downloaded, total_bytes, speed_kb, mirror_name)

                # Kiểm tra dung lượng tối thiểu (> 30KB)
                if downloaded < 30000:
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

def download_batch_parallel(
    maps_list,
    destination_dir,
    max_workers=4,
    preferred_mirror="auto",
    no_video=True,
    item_callback=None,
    progress_callback=None
):
    """
    Tải danh sách beatmapsets song song đa luồng (Multi-threaded worker pool).
    """
    total = len(maps_list)
    completed = 0
    success = 0
    failed = 0
    total_bytes = 0

    results = []

    def task(item_tuple):
        idx, m = item_tuple
        ok, msg, path = download_beatmapset(
            m,
            destination_dir,
            preferred_mirror=preferred_mirror,
            no_video=no_video,
            progress_callback=lambda sid, dl, tot, spd, mir: (
                progress_callback(idx, sid, dl, tot, spd, mir) if progress_callback else None
            )
        )
        return idx, m, ok, msg, path

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(task, (i, m)): i for i, m in enumerate(maps_list)}
        for fut in as_completed(futures):
            idx, m, ok, msg, path = fut.result()
            completed += 1
            if ok:
                success += 1
                if path and os.path.exists(path):
                    total_bytes += os.path.getsize(path)
            else:
                failed += 1

            if item_callback:
                item_callback(idx, m, ok, msg, completed, total)

            results.append((m, ok, msg, path))

    return results, success, failed, total_bytes
