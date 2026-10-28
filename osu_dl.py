#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
osu! Mirror Beatmap Downloader & Farm Filter
Dành riêng cho Linux & osu! stable trên ổ cứng ngoài
Tối ưu cho người chơi: Cao Mi Le (Rank #12k, 9.1k PP, SR 6.5* - 7.7*)
"""

import os
import sys
import argparse
import time

# Thêm thư mục hiện tại vào sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import config
import profile_service
import map_finder
import mirror_downloader

# Màu sắc ANSI cho terminal
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"

def print_banner():
    banner = f"""{C_CYAN}{C_BOLD}
  ___  ____  _   _   __  __ ___ ____  ____   ___  ____  
 / _ \\/ ___|| | | | |  \\/  |_ _|  _ \\|  _ \\ / _ \\|  _ \\ 
| | | \\___ \\| | | | | |\\/| || || |_) | |_) | | | | |_) |
| |_| |___) | |_| | | |  | || ||  _ <|  _ <| |_| |  _ < 
 \\___/|____/ \\___/  |_|  |_|___|_| \\_\\_| \\_\\\\___/|_| \\_\\
    {C_YELLOW}osu! Ranked Farm Maps Downloader for Linux & External Drive{C_RESET}
"""
    print(banner)

def print_profile_card(prof, songs_path, installed_count):
    border = f"{C_BLUE}=" * 66 + C_RESET
    print(border)
    print(f" {C_BOLD}👤 Profile:{C_RESET} {C_GREEN}{prof['username']}{C_RESET} (ID: {prof['id']})")
    print(f" {C_BOLD}🏆 Thứ hạng:{C_RESET} #{prof['global_rank']:,} Global | #{prof['country_rank']} {prof['country_code']}")
    print(f" {C_BOLD}⚡ Performance:{C_RESET} {C_YELLOW}{prof['pp']:,} PP{C_RESET} | Accuracy: {prof['hit_accuracy']}% | Plays: {prof['play_count']:,}")
    
    nm = prof["recommended"]["nomod_hd"]
    hr = prof["recommended"]["hr_hdhr"]
    dt = prof["recommended"]["dt"]
    print(f" {C_BOLD}🎯 Trình độ đề xuất:{C_RESET}")
    print(f"    • {C_CYAN}Nomod / HD Farm:{C_RESET}  {C_BOLD}{nm['min_sr']}* – {nm['max_sr']}*{C_RESET} (Trọng tâm: ~{nm['target_sr']}* | {nm['pp_range']})")
    print(f"    • {C_CYAN}HR / HDHR Farm:{C_RESET}   {C_BOLD}{hr['min_sr']}* – {hr['max_sr']}*{C_RESET} (Trọng tâm: ~{hr['target_sr']}* | {hr['pp_range']})")
    print(f"    • {C_CYAN}DT / NC Farm:{C_RESET}     {C_BOLD}{dt['min_sr']}* – {dt['max_sr']}*{C_RESET} base SR ({dt['pp_range']})")
    
    print(f" {C_BOLD}💾 Ổ cứng ngoài / Thư mục Songs:{C_RESET} {C_WHITE}{songs_path}{C_RESET}")
    print(f" {C_BOLD}📦 Số map đã có sẵn:{C_RESET} {C_GREEN}{installed_count:,} sets{C_RESET} (sẽ tự động bỏ qua khi tải)")
    print(border)

def draw_progress(set_id, downloaded, total_bytes, speed_kb, mirror_name):
    pct = (downloaded / total_bytes * 100) if total_bytes > 0 else 0
    bar_len = 25
    filled_len = int(bar_len * pct / 100)
    bar = "█" * filled_len + "░" * (bar_len - filled_len)
    
    dl_mb = downloaded / (1024 * 1024)
    total_mb = total_bytes / (1024 * 1024) if total_bytes > 0 else 0
    
    sys.stdout.write(
        f"\r  {C_CYAN}[{mirror_name}]{C_RESET} [{bar}] {pct:5.1f}% | {dl_mb:.1f}/{total_mb:.1f}MB | {C_YELLOW}{speed_kb:6.1f} KB/s{C_RESET}  "
    )
    sys.stdout.flush()

def download_selected_maps(maps, songs_path, no_video=True):
    if not maps:
        print(f"{C_YELLOW}Không có map nào cần tải.{C_RESET}")
        return

    print(f"\n{C_BOLD}Danh sách {len(maps)} beatmapsets sẽ được tải về:{C_RESET}")
    print("-" * 75)
    for i, m in enumerate(maps, 1):
        diffs_preview = ", ".join([f"{d['name']} ({d['sr']}*)" for d in m['valid_diffs'][:3]])
        if len(m['valid_diffs']) > 3:
            diffs_preview += f" (+{len(m['valid_diffs']) - 3} diffs)"
        print(f" {C_CYAN}{i:2d}.{C_RESET} [{m['id']}] {C_BOLD}{m['artist']} - {m['title']}{C_RESET} by {m['creator']}")
        print(f"     Plays: {m['plays']:,} | Favs: {m['favs']:,} | Diffs: {C_GREEN}{diffs_preview}{C_RESET}")
    print("-" * 75)

    ans = input(f"\n{C_BOLD}Xác nhận tải {len(maps)} mapsets vào {songs_path}? (Y/n): {C_RESET}").strip().lower()
    if ans and ans != 'y':
        print(f"{C_YELLOW}Đã hủy quá trình tải.{C_RESET}")
        return

    print(f"\n{C_GREEN}{C_BOLD}Bắt đầu tải qua các Mirror (osu.direct, Catboy/Mino, Sayobot)...{C_RESET}\n")

    success_count = 0
    fail_count = 0
    total_bytes_downloaded = 0

    start_total_time = time.time()

    for idx, m in enumerate(maps, 1):
        print(f"{C_BOLD}[{idx}/{len(maps)}]{C_RESET} Tải: {m['artist']} - {m['title']} ({m['id']})")
        ok, msg, path = mirror_downloader.download_beatmapset(
            m,
            songs_path,
            no_video=no_video,
            progress_callback=draw_progress
        )
        print() # newline after progress bar
        if ok:
            success_count += 1
            if path and os.path.exists(path):
                total_bytes_downloaded += os.path.getsize(path)
            print(f"  {C_GREEN}✔ {msg}{C_RESET}")
        else:
            fail_count += 1
            print(f"  {C_RED}✘ {msg}{C_RESET}")
        time.sleep(0.3)

    elapsed_total = max(time.time() - start_total_time, 1)
    total_mb = total_bytes_downloaded / (1024 * 1024)

    print("\n" + "=" * 66)
    print(f"{C_BOLD}{C_GREEN}HOÀN TẤT TẢI BEATMAPS!{C_RESET}")
    print(f" • Thành công: {C_GREEN}{success_count} maps{C_RESET} ({total_mb:.1f} MB trong {elapsed_total:.1f}s)")
    if fail_count > 0:
        print(f" • Thất bại: {C_RED}{fail_count} maps{C_RESET}")
    print(f" • Thư mục: {C_WHITE}{songs_path}{C_RESET}")
    print(f"\n{C_BOLD}{C_YELLOW}💡 HƯỚNG DẪN DÀNH CHO OSU! STABLE TRÊN LINUX:{C_RESET}")
    print(f" 1. Mở osu! stable trên Linux.")
    print(f" 2. Vào màn hình chọn bài hát (Solo / Song Select).")
    print(f" 3. Nhấn {C_BOLD}{C_CYAN}F5{C_RESET} trên bàn phím. osu! sẽ tự động giải nén và nạp các map mới vào game ngay lập tức!")
    print("=" * 66 + "\n")

def interactive_menu():
    print_banner()
    cfg = config.load_config()
    songs_path = cfg.get("songs_path")

    # Kiểm tra đường dẫn Songs
    if not songs_path or not os.path.isdir(songs_path):
        print(f"{C_RED}[Cảnh báo] Chưa tìm thấy thư mục osu! Songs trên ổ cứng ngoài!{C_RESET}")
        entered = input("Vui lòng nhập đường dẫn thư mục Songs của osu! (ví dụ /mnt/SSDStorage/osu!/Songs): ").strip()
        if os.path.isdir(entered):
            songs_path = os.path.abspath(entered)
            cfg["songs_path"] = songs_path
            config.save_config(cfg)
        else:
            print(f"{C_RED}Đường dẫn không tồn tại. Thoát chương trình.{C_RESET}")
            sys.exit(1)

    # Quét map đã có sẵn
    installed_ids = config.get_installed_beatmap_ids(songs_path)

    # Lấy thông tin profile
    player_name = cfg.get("player_username", "Cao Mi Le")
    print(f"{C_CYAN}Đang kết nối lấy chỉ số người chơi {player_name}...{C_RESET}")
    prof = profile_service.fetch_player_profile(player_name)

    nm_rec = prof["recommended"]["nomod_hd"]
    dt_rec = prof["recommended"]["dt"]
    hr_rec = prof["recommended"]["hr_hdhr"]

    while True:
        print_profile_card(prof, songs_path, len(installed_ids))
        print(f"{C_BOLD}CHỌN CHỨC NĂNG TẢI MAP:{C_RESET}")
        print(f" {C_GREEN}[1]{C_RESET} {C_BOLD}Tải Farm Maps nhiều người chơi nhất ({nm_rec['min_sr']}* – {nm_rec['max_sr']}* Nomod/HD) [KHUYÊN DÙNG]{C_RESET}")
        print(f" {C_CYAN}[2]{C_RESET} Tải Gói DT Farm ({dt_rec['min_sr']}* – {dt_rec['max_sr']}* base -> Jump/Speed)")
        print(f" {C_MAGENTA}[3]{C_RESET} Tải Gói HR Farm ({hr_rec['min_sr']}* – {hr_rec['max_sr']}* base -> Precision/Flow)")
        print(f" {C_YELLOW}[4]{C_RESET} Tải theo Mapper tủ (Sotarks, Reform, Seni, Kowari, Nevo, browiec...)")
        print(f" {C_WHITE}[5]{C_RESET} Tự nhập khoảng Star Rating & Bộ lọc tùy ý")
        print(f" {C_BLUE}[6]{C_RESET} Thay đổi thư mục Songs / Cấu hình ổ cứng ngoài")
        print(f" {C_RED}[0]{C_RESET} Thoát")

        choice = input(f"\n{C_BOLD}Nhập lựa chọn của bạn (0-6): {C_RESET}").strip()

        if choice == "0":
            print("Tạm biệt! Chúc bạn farm PP vui vẻ!")
            break

        elif choice == "1":
            amount_str = input(f"Nhập số lượng map muốn tải (mặc định 20): ").strip()
            amount = int(amount_str) if amount_str.isdigit() else 20
            print(f"\n{C_CYAN}Đang tìm kiếm các map Ranked phổ biến nhất trong khoảng {nm_rec['min_sr']}* – {nm_rec['max_sr']}*...{C_RESET}")
            maps = map_finder.find_ranked_farm_maps(
                min_sr=nm_rec["min_sr"],
                max_sr=nm_rec["max_sr"],
                limit=amount,
                already_installed_ids=installed_ids,
                progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
            )
            print()
            download_selected_maps(maps, songs_path, no_video=cfg.get("no_video", True))
            installed_ids = config.get_installed_beatmap_ids(songs_path)

        elif choice == "2":
            amount_str = input(f"Nhập số lượng map muốn tải (mặc định 20): ").strip()
            amount = int(amount_str) if amount_str.isdigit() else 20
            print(f"\n{C_CYAN}Đang tìm kiếm các map DT Farm trong khoảng {dt_rec['min_sr']}* – {dt_rec['max_sr']}*...{C_RESET}")
            maps = map_finder.find_ranked_farm_maps(
                min_sr=dt_rec["min_sr"],
                max_sr=dt_rec["max_sr"],
                limit=amount,
                already_installed_ids=installed_ids,
                progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
            )
            print()
            download_selected_maps(maps, songs_path, no_video=cfg.get("no_video", True))
            installed_ids = config.get_installed_beatmap_ids(songs_path)

        elif choice == "3":
            amount_str = input(f"Nhập số lượng map muốn tải (mặc định 20): ").strip()
            amount = int(amount_str) if amount_str.isdigit() else 20
            print(f"\n{C_CYAN}Đang tìm kiếm các map HR Farm trong khoảng {hr_rec['min_sr']}* – {hr_rec['max_sr']}*...{C_RESET}")
            maps = map_finder.find_ranked_farm_maps(
                min_sr=hr_rec["min_sr"],
                max_sr=hr_rec["max_sr"],
                limit=amount,
                already_installed_ids=installed_ids,
                progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
            )
            print()
            download_selected_maps(maps, songs_path, no_video=cfg.get("no_video", True))
            installed_ids = config.get_installed_beatmap_ids(songs_path)

        elif choice == "4":
            print(f"\nCác mappers nổi tiếng: {', '.join(map_finder.FARM_MAPPERS[:12])}")
            mapper = input("Nhập tên Mapper bạn muốn tải (ví dụ: Sotarks): ").strip()
            if not mapper:
                continue
            amount_str = input("Số lượng map muốn tải (mặc định 15): ").strip()
            amount = int(amount_str) if amount_str.isdigit() else 15
            print(f"\n{C_CYAN}Đang tìm kiếm map ranked của {mapper}...{C_RESET}")
            maps = map_finder.find_ranked_farm_maps(
                min_sr=nm_rec["min_sr"] - 0.2,
                max_sr=nm_rec["max_sr"] + 0.3,
                limit=amount,
                already_installed_ids=installed_ids,
                mapper_filter=mapper,
                progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
            )
            print()
            download_selected_maps(maps, songs_path, no_video=cfg.get("no_video", True))
            installed_ids = config.get_installed_beatmap_ids(songs_path)

        elif choice == "5":
            try:
                min_sr = float(input(f"Nhập Min Star Rating (ví dụ 6.5): ").strip())
                max_sr = float(input(f"Nhập Max Star Rating (ví dụ 7.8): ").strip())
                amount_str = input("Số lượng map muốn tải (mặc định 20): ").strip()
                amount = int(amount_str) if amount_str.isdigit() else 20
            except ValueError:
                print(f"{C_RED}Giá trị nhập không hợp lệ.{C_RESET}")
                continue

            print(f"\n{C_CYAN}Đang tìm kiếm các map trong khoảng {min_sr}* – {max_sr}*...{C_RESET}")
            maps = map_finder.find_ranked_farm_maps(
                min_sr=min_sr,
                max_sr=max_sr,
                limit=amount,
                already_installed_ids=installed_ids,
                progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
            )
            print()
            download_selected_maps(maps, songs_path, no_video=cfg.get("no_video", True))
            installed_ids = config.get_installed_beatmap_ids(songs_path)

        elif choice == "6":
            print(f"Đường dẫn hiện tại: {songs_path}")
            new_path = input("Nhập đường dẫn mới tới thư mục Songs: ").strip()
            if os.path.isdir(new_path):
                songs_path = os.path.abspath(new_path)
                cfg["songs_path"] = songs_path
                config.save_config(cfg)
                installed_ids = config.get_installed_beatmap_ids(songs_path)
                print(f"{C_GREEN}Đã cập nhật thư mục Songs thành công!{C_RESET}")
            else:
                print(f"{C_RED}Đường dẫn không hợp lệ hoặc thư mục không tồn tại.{C_RESET}")

def main():
    parser = argparse.ArgumentParser(description="osu! Ranked Farm Maps Downloader for Linux & External Drive")
    parser.add_argument("--gui", action="store_true", help="Mở giao diện đồ họa GUI")
    parser.add_argument("--profile", type=str, default="Cao Mi Le", help="Tên profile osu! (mặc định: Cao Mi Le)")
    parser.add_argument("--min-sr", type=float, default=None, help="Star Rating tối thiểu")
    parser.add_argument("--max-sr", type=float, default=None, help="Star Rating tối đa")
    parser.add_argument("--count", "-n", type=int, default=20, help="Số lượng mapset cần tải")
    parser.add_argument("--mapper", type=str, default=None, help="Lọc theo mapper cụ thể")
    parser.add_argument("--dt", action="store_true", help="Chế độ tải gói DT Farm")
    parser.add_argument("--hr", action="store_true", help="Chế độ tải gói HR Farm")
    parser.add_argument("--songs-path", type=str, default=None, help="Đường dẫn thư mục Songs của osu!")
    parser.add_argument("--video", action="store_true", help="Tải kèm video (mặc định: no-video)")
    parser.add_argument("--non-interactive", action="store_true", help="Chạy tự động không qua menu tương tác")

    args = parser.parse_args()

    if args.gui:
        import gui
        gui.main()
        return

    # Nếu không truyền argument nào ngoài mặc định -> Mở menu tương tác TUI
    if len(sys.argv) == 1:
        interactive_menu()
        return

    # Chế độ CLI arguments
    cfg = config.load_config()
    songs_path = args.songs_path or cfg.get("songs_path")

    if not songs_path or not os.path.isdir(songs_path):
        print(f"{C_RED}Lỗi: Không tìm thấy thư mục Songs của osu! ({songs_path}). Dùng flag --songs-path để chỉ định.{C_RESET}")
        sys.exit(1)

    prof = profile_service.fetch_player_profile(args.profile)
    installed = config.get_installed_beatmap_ids(songs_path)

    min_sr = args.min_sr
    max_sr = args.max_sr

    if args.dt:
        min_sr = min_sr or prof["recommended"]["dt"]["min_sr"]
        max_sr = max_sr or prof["recommended"]["dt"]["max_sr"]
    elif args.hr:
        min_sr = min_sr or prof["recommended"]["hr_hdhr"]["min_sr"]
        max_sr = max_sr or prof["recommended"]["hr_hdhr"]["max_sr"]
    else:
        min_sr = min_sr or prof["recommended"]["nomod_hd"]["min_sr"]
        max_sr = max_sr or prof["recommended"]["nomod_hd"]["max_sr"]

    print(f"{C_CYAN}Đang tìm kiếm {args.count} maps Ranked ({min_sr}* – {max_sr}*)...{C_RESET}")
    maps = map_finder.find_ranked_farm_maps(
        min_sr=min_sr,
        max_sr=max_sr,
        limit=args.count,
        already_installed_ids=installed,
        mapper_filter=args.mapper,
        progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
    )
    print()

    no_video = not args.video
    download_selected_maps(maps, songs_path, no_video=no_video)

if __name__ == "__main__":
    main()
