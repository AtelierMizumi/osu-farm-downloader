import os
import re
import json

CONFIG_DIR = os.path.expanduser("~/.config/osu-farm-downloader")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def find_osu_songs_directory():
    """
    Tự động tìm kiếm thư mục Songs của osu! stable trên các ổ cứng ngoài,
    phân vùng mount (/mnt, /media, /run/media), hoặc thư mục mặc định Wine.
    """
    # 1. Các đường dẫn ưu tiên đã biết
    common_candidates = [
        "/mnt/SSDStorage/osu!/Songs",
        "/mnt/Baracuda/osu!/Songs",
        "/mnt/500GBext4/osu!/Songs",
        "/mnt/Windows10/osu!/Songs",
        os.path.expanduser("~/.wine/drive_c/osu!/Songs"),
        os.path.expanduser("~/.local/share/osu/Songs"),
    ]

    for path in common_candidates:
        if os.path.isdir(path):
            return os.path.abspath(path)

    # 2. Quét nhanh các điểm mount trên Linux (/mnt, /media, /run/media)
    search_roots = ["/mnt", "/media", "/run/media"]
    for root_dir in search_roots:
        if not os.path.exists(root_dir):
            continue
        try:
            for item in os.listdir(root_dir):
                full_path = os.path.join(root_dir, item)
                if os.path.isdir(full_path):
                    # Kiểm tra osu!/Songs hoặc Songs
                    candidate = os.path.join(full_path, "osu!", "Songs")
                    if os.path.isdir(candidate):
                        return os.path.abspath(candidate)
                    candidate2 = os.path.join(full_path, "osu!/Songs")
                    if os.path.isdir(candidate2):
                        return os.path.abspath(candidate2)
                    candidate3 = os.path.join(full_path, "Songs")
                    if os.path.isdir(candidate3) and os.path.exists(os.path.join(full_path, "osu!.exe")):
                        return os.path.abspath(candidate3)
        except Exception:
            continue

    return None

def load_config():
    default_songs = find_osu_songs_directory() or ""
    default_config = {
        "songs_path": default_songs,
        "player_username": "Cao Mi Le",
        "player_id": 10910765,
        "default_min_sr": 6.6,
        "default_max_sr": 7.7,
        "min_playcount": 15000,
        "no_video": True,
        "preferred_mirror": "auto",
        "default_status": "ranked",
        "concurrent_downloads": 4,
        "timeout": 15
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_config.update(saved)
                # Nếu path đã lưu không tồn tại nhưng tìm thấy đường dẫn mới thì cập nhật
                if not os.path.isdir(default_config["songs_path"]) and default_songs:
                    default_config["songs_path"] = default_songs
        except Exception:
            pass
    return default_config

def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[Cảnh báo] Không thể lưu cấu hình: {e}")

def get_installed_beatmap_ids(songs_path):
    """
    Quét nhanh thư mục Songs để lấy danh sách BeatmapSetID đã có (cả folder lẫn file .osz)
    Giúp tránh tải trùng map, tiết kiệm thời gian và băng thông.
    """
    installed_ids = set()
    if not songs_path or not os.path.isdir(songs_path):
        return installed_ids

    id_pattern = re.compile(r"^(\d+)")

    try:
        for entry in os.scandir(songs_path):
            name = entry.name
            m = id_pattern.match(name)
            if m:
                try:
                    installed_ids.add(int(m.group(1)))
                except ValueError:
                    pass
    except Exception as e:
        print(f"[Cảnh báo] Lỗi khi quét thư mục Songs: {e}")

    return installed_ids
