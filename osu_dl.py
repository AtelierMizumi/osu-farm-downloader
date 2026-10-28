#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
osu! Mirror Beatmap Downloader & Farm Filter
Dành riêng cho Linux & osu! stable trên ổ cứng ngoài
Tối ưu cho người chơi: Cao Mi Le (Rank #12k, 9.1k PP, SR 6.5* - 7.7*)
Phiên bản 1.1.0: Tải song song đa luồng, Bộ lọc trạng thái map, Tùy chọn nguồn Mirror
"""

import os
import sys
import argparse
import time

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
    {C_YELLOW}osu! Ranked Farm Maps Downloader for Linux & External Drive v1.1.0{C_RESET}
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

def download_selected_maps_parallel(maps, songs_path, max_workers=4, preferred_mirror="auto", no_video=True):
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

    ans = input(f"\n{C_BOLD}Xác nhận tải {len(maps)} mapsets (Song song {max_workers} luồng) vào {songs_path}? (Y/n): {C_RESET}").strip().lower()
    if ans and ans != 'y':
        print(f"{C_YELLOW}Đã hủy quá trình tải.{C_RESET}")
        return

    print(f"\n{C_GREEN}{C_BOLD}Bắt đầu tải song song {max_workers} luồng (Mirror ưu tiên: {preferred_mirror})...{C_RESET}\n")

    start_total_time = time.time()

    def on_item(idx, m, ok, msg, comp, tot):
        status_icon = f"{C_GREEN}✔{C_RESET}" if ok else f"{C_RED}✘{C_RESET}"
        print(f" [{comp:2d}/{tot:2d}] {status_icon} {m['artist']} - {m['title']} ({msg})")

    results, success, fail, total_bytes = mirror_downloader.download_batch_parallel(
        maps,
        songs_path,
        max_workers=max_workers,
        preferred_mirror=preferred_mirror,
        no_video=no_video,
        item_callback=on_item
    )

    elapsed_total = max(time.time() - start_total_time, 0.1)
    total_mb = total_bytes / (1024 * 1024)

    print("\n" + "=" * 66)
    print(f"{C_BOLD}{C_GREEN}HOÀN TẤT TẢI BEATMAPS SONG SONG!{C_RESET}")
    print(f" • Thành công: {C_GREEN}{success} maps{C_RESET} ({total_mb:.1f} MB trong {elapsed_total:.1f}s - Tốc độ TB: {total_mb/elapsed_total:.2f} MB/s)")
    if fail > 0:
        print(f" • Thất bại: {C_RED}{fail} maps{C_RESET}")
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

    if not songs_path or not os.path.isdir(songs_path):
        print(f"{C_RED}[Cảnh báo] Chưa tìm thấy thư mục osu! Songs trên ổ cứng ngoài!{C_RESET}")
        entered = input("Vui lòng nhập đường dẫn thư mục Songs của osu!: ").strip()
        if os.path.isdir(entered):
            songs_path = os.path.abspath(entered)
            cfg["songs_path"] = songs_path
            config.save_config(cfg)
        else:
            print(f"{C_RED}Đường dẫn không tồn tại. Thoát chương trình.{C_RESET}")
            sys.exit(1)

    installed_ids = config.get_installed_beatmap_ids(songs_path)
    player_name = cfg.get("player_username", "Cao Mi Le")
    print(f"{C_CYAN}Đang kết nối lấy chỉ số người chơi {player_name}...{C_RESET}")
    prof = profile_service.fetch_player_profile(player_name)

    nm_rec = prof["recommended"]["nomod_hd"]
    dt_rec = prof["recommended"]["dt"]
    hr_rec = prof["recommended"]["hr_hdhr"]

    max_threads = cfg.get("concurrent_downloads", 4)
    pref_mirror = cfg.get("preferred_mirror", "auto")

    while True:
        print_profile_card(prof, songs_path, len(installed_ids))
        print(f"{C_BOLD}CHỌN CHỨC NĂNG TẢI MAP:{C_RESET}")
        print(f" {C_GREEN}[1]{C_RESET} {C_BOLD}Tải Farm Maps nhiều người chơi nhất ({nm_rec['min_sr']}* – {nm_rec['max_sr']}* Nomod/HD) [KHUYÊN DÙNG]{C_RESET}")
        print(f" {C_CYAN}[2]{C_RESET} Tải Gói DT Farm ({dt_rec['min_sr']}* – {dt_rec['max_sr']}* base -> Jump/Speed)")
        print(f" {C_MAGENTA}[3]{C_RESET} Tải Gói HR Farm ({hr_rec['min_sr']}* – {hr_rec['max_sr']}* base -> Precision/Flow)")
        print(f" {C_YELLOW}[4]{C_RESET} Tải theo Mapper tủ (Sotarks, Reform, Seni, Kowari, Nevo, browiec...)")
        print(f" {C_WHITE}[5]{C_RESET} Tự nhập khoảng Star Rating & Bộ lọc trạng thái map (Ranked/Loved/Qualified)")
        print(f" {C_BLUE}[6]{C_RESET} Cài đặt (Số luồng tải song song: {max_threads} | Mirror: {pref_mirror})")
        print(f" {C_WHITE}[7]{C_RESET} Mở giao diện đồ họa Desktop GUI")
        print(f" {C_RED}[0]{C_RESET} Thoát")

        choice = input(f"\n{C_BOLD}Nhập lựa chọn của bạn (0-7): {C_RESET}").strip()

        if choice == "0":
            print("Tạm biệt! Chúc bạn farm PP vui vẻ!")
            break

        elif choice == "7":
            import gui
            gui.main()
            break

        elif choice == "1":
            amount_str = input(f"Nhập số lượng map muốn tải (mặc định 25): ").strip()
            amount = int(amount_str) if amount_str.isdigit() else 25
            print(f"\n{C_CYAN}Đang tìm kiếm các map Ranked phổ biến nhất trong khoảng {nm_rec['min_sr']}* – {nm_rec['max_sr']}*...{C_RESET}")
            maps = map_finder.find_ranked_farm_maps(
                min_sr=nm_rec["min_sr"],
                max_sr=nm_rec["max_sr"],
                limit=amount,
                status_filter="ranked",
                already_installed_ids=installed_ids,
                progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
            )
            print()
            download_selected_maps_parallel(maps, songs_path, max_workers=max_threads, preferred_mirror=pref_mirror, no_video=cfg.get("no_video", True))
            installed_ids = config.get_installed_beatmap_ids(songs_path)

        elif choice == "2":
            amount_str = input(f"Nhập số lượng map muốn tải (mặc định 20): ").strip()
            amount = int(amount_str) if amount_str.isdigit() else 20
            print(f"\n{C_CYAN}Đang tìm kiếm các map DT Farm trong khoảng {dt_rec['min_sr']}* – {dt_rec['max_sr']}*...{C_RESET}")
            maps = map_finder.find_ranked_farm_maps(
                min_sr=dt_rec["min_sr"],
                max_sr=dt_rec["max_sr"],
                limit=amount,
                mod="DT",
                status_filter="ranked",
                already_installed_ids=installed_ids,
                progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
            )
            print()
            download_selected_maps_parallel(maps, songs_path, max_workers=max_threads, preferred_mirror=pref_mirror, no_video=cfg.get("no_video", True))
            installed_ids = config.get_installed_beatmap_ids(songs_path)

        elif choice == "3":
            amount_str = input(f"Nhập số lượng map muốn tải (mặc định 20): ").strip()
            amount = int(amount_str) if amount_str.isdigit() else 20
            print(f"\n{C_CYAN}Đang tìm kiếm các map HR Farm trong khoảng {hr_rec['min_sr']}* – {hr_rec['max_sr']}*...{C_RESET}")
            maps = map_finder.find_ranked_farm_maps(
                min_sr=hr_rec["min_sr"],
                max_sr=hr_rec["max_sr"],
                limit=amount,
                mod="HR",
                status_filter="ranked",
                already_installed_ids=installed_ids,
                progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
            )
            print()
            download_selected_maps_parallel(maps, songs_path, max_workers=max_threads, preferred_mirror=pref_mirror, no_video=cfg.get("no_video", True))
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
                status_filter="ranked",
                already_installed_ids=installed_ids,
                mapper_filter=mapper,
                progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
            )
            print()
            download_selected_maps_parallel(maps, songs_path, max_workers=max_threads, preferred_mirror=pref_mirror, no_video=cfg.get("no_video", True))
            installed_ids = config.get_installed_beatmap_ids(songs_path)

        elif choice == "5":
            try:
                min_sr = float(input(f"Nhập Min Star Rating (ví dụ 6.5): ").strip())
                max_sr = float(input(f"Nhập Max Star Rating (ví dụ 7.8): ").strip())
                print("\nChọn tình trạng map:")
                print(" 1. Ranked (Chính thức, có PP)")
                print(" 2. Tất cả có Leaderboard (Ranked + Loved + Approved)")
                print(" 3. Loved (Cộng đồng yêu thích)")
                print(" 4. Qualified (Thử nghiệm)")
                print(" 5. Tất cả trạng thái")
                st_c = input("Chọn tình trạng (1-5, mặc định 1): ").strip()
                st_map = {"1": "ranked", "2": "leaderboard", "3": "loved", "4": "qualified", "5": "all"}
                st_filter = st_map.get(st_c, "ranked")

                amount_str = input("Số lượng map muốn tải (mặc định 20): ").strip()
                amount = int(amount_str) if amount_str.isdigit() else 20
            except ValueError:
                print(f"{C_RED}Giá trị nhập không hợp lệ.{C_RESET}")
                continue

            print(f"\n{C_CYAN}Đang tìm kiếm các map trong khoảng {min_sr}* – {max_sr}* ({st_filter})...{C_RESET}")
            maps = map_finder.find_ranked_farm_maps(
                min_sr=min_sr,
                max_sr=max_sr,
                limit=amount,
                status_filter=st_filter,
                already_installed_ids=installed_ids,
                progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
            )
            print()
            download_selected_maps_parallel(maps, songs_path, max_workers=max_threads, preferred_mirror=pref_mirror, no_video=cfg.get("no_video", True))
            installed_ids = config.get_installed_beatmap_ids(songs_path)

        elif choice == "6":
            print(f"\n{C_BOLD}CÀI ĐẶT NÂNG CAO:{C_RESET}")
            new_threads = input(f"Nhập số luồng tải song song (1-8, hiện tại: {max_threads}): ").strip()
            if new_threads.isdigit() and 1 <= int(new_threads) <= 8:
                max_threads = int(new_threads)
                cfg["concurrent_downloads"] = max_threads

            print("\nChọn Mirror ưu tiên:")
            mirrors = list(mirror_downloader.MIRROR_PROVIDERS.keys())
            for i, k in enumerate(mirrors, 1):
                print(f" {i}. {mirror_downloader.MIRROR_PROVIDERS[k]}")
            m_c = input(f"Chọn mirror (1-{len(mirrors)}, hiện tại: {pref_mirror}): ").strip()
            if m_c.isdigit() and 1 <= int(m_c) <= len(mirrors):
                pref_mirror = mirrors[int(m_c) - 1]
                cfg["preferred_mirror"] = pref_mirror

            config.save_config(cfg)
            print(f"{C_GREEN}Đã lưu cài đặt!{C_RESET}")

def main():
    parser = argparse.ArgumentParser(description="osu! Ranked Farm Maps Downloader for Linux & External Drive")
    parser.add_argument("--gui", action="store_true", help="Mở giao diện đồ họa Desktop GUI")
    parser.add_argument("--profile", type=str, default="Cao Mi Le", help="Tên profile osu! (mặc định: Cao Mi Le)")
    parser.add_argument("--min-sr", type=float, default=None, help="Star Rating tối thiểu")
    parser.add_argument("--max-sr", type=float, default=None, help="Star Rating tối đa")
    parser.add_argument("--count", "-n", type=int, default=25, help="Số lượng mapset cần tải")
    parser.add_argument("--status", type=str, default="ranked", choices=["ranked", "leaderboard", "ranked_approved", "loved", "qualified", "all"], help="Lọc theo tình trạng map")
    parser.add_argument("--mirror", type=str, default="auto", choices=["auto", "osu.direct", "catboy", "sayobot", "beatconnect", "nerinyan"], help="Nguồn mirror ưu tiên")
    parser.add_argument("--threads", "-t", type=int, default=4, help="Số luồng tải song song (mặc định 4)")
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

    if len(sys.argv) == 1:
        interactive_menu()
        return

    cfg = config.load_config()
    songs_path = args.songs_path or cfg.get("songs_path")

    if not songs_path or not os.path.isdir(songs_path):
        print(f"{C_RED}Lỗi: Không tìm thấy thư mục Songs của osu! ({songs_path}). Dùng flag --songs-path để chỉ định.{C_RESET}")
        sys.exit(1)

    prof = profile_service.fetch_player_profile(args.profile)
    installed = config.get_installed_beatmap_ids(songs_path)

    min_sr = args.min_sr
    max_sr = args.max_sr
    mod = "NM"

    if args.dt:
        mod = "DT"
        min_sr = min_sr or prof["recommended"]["dt"]["min_sr"]
        max_sr = max_sr or prof["recommended"]["dt"]["max_sr"]
    elif args.hr:
        mod = "HR"
        min_sr = min_sr or prof["recommended"]["hr_hdhr"]["min_sr"]
        max_sr = max_sr or prof["recommended"]["hr_hdhr"]["max_sr"]
    else:
        min_sr = min_sr or prof["recommended"]["nomod_hd"]["min_sr"]
        max_sr = max_sr or prof["recommended"]["nomod_hd"]["max_sr"]

    print(f"{C_CYAN}Đang tìm kiếm {args.count} maps ({min_sr}* – {max_sr}* | Trạng thái: {args.status})...{C_RESET}")
    maps = map_finder.find_ranked_farm_maps(
        min_sr=min_sr,
        max_sr=max_sr,
        limit=args.count,
        mod=mod,
        status_filter=args.status,
        already_installed_ids=installed,
        mapper_filter=args.mapper,
        progress_callback=lambda c, t, msg: sys.stdout.write(f"\r{msg} ({c}/{t})")
    )
    print()

    no_video = not args.video
    download_selected_maps_parallel(
        maps,
        songs_path,
        max_workers=args.threads,
        preferred_mirror=args.mirror,
        no_video=no_video
    )

if __name__ == "__main__":
    main()
