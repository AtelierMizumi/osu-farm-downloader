import urllib.request
import urllib.parse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

STATUS_PRESETS = {
    "ranked": {"name": "Ranked (Chính thức, có PP)", "values": [1], "api_status": 1},
    "leaderboard": {"name": "Tất cả có Leaderboard (Ranked + Loved + Approved)", "values": [1, 2, 4], "api_status": None},
    "ranked_approved": {"name": "Ranked + Approved (Có PP)", "values": [1, 2], "api_status": 1},
    "loved": {"name": "Loved (Cộng đồng yêu thích, có Leaderboard)", "values": [4], "api_status": 4},
    "qualified": {"name": "Qualified (Đang thử nghiệm tuần cuối)", "values": [3], "api_status": 3},
    "all": {"name": "Tất cả trạng thái (Bao gồm Pending/Graveyard)", "values": None, "api_status": None}
}

SORT_OPTIONS = {
    "farm_score": "🏆 Dễ farm & Thoải mái nhất (Smart Farm Score)",
    "plays": "🔥 Nhiều người chơi nhất (Playcount)",
    "favs": "❤️ Được yêu thích nhất (Favourites)",
    "newest": "🆕 Mới nhất (Newest Ranked)",
    "sr_asc": "⭐ Star Rating tăng dần",
    "sr_desc": "⭐ Star Rating giảm dần"
}

def calculate_dt_ar(ar):
    """Tính AR chính xác sau khi bật mod DoubleTime (DT/NC) theo chuẩn osu!"""
    if ar <= 5:
        ms = 1800 - 120 * ar
    else:
        ms = 1200 - 150 * (ar - 5)
    ms_dt = ms * (2 / 3)
    if ms_dt >= 1200:
        return round((1800 - ms_dt) / 120, 2)
    else:
        return round(5 + (1200 - ms_dt) / 150, 2)

def calculate_objective_farm_score(diff, set_info):
    """
    Thuật toán chấm điểm Farm & Độ thoải mái (Comfort Score: 0 - 100)
    hoàn toàn dựa trên CHỈ SỐ KỸ THUẬT VÀ DỮ LIỆU THỰC TẾ của map (không phụ thuộc vào tên Mapper hay Artist):

    1. Tỷ lệ Pass Rate (Passcount / Playcount): Phản ánh độ mượt của pattern, không có diff spike/choke cuối.
    2. Circle Size (CS): CS 3.8 - 4.3 là tỉ lệ vàng của jump/farm. CS quá nhỏ (> 4.6) sẽ bị trừ điểm nặng.
    3. Approach Rate (AR): AR 9.3 - 9.8 tối ưu cho phản xạ đọc note.
    4. Độ dài bài (Hit Length): Ưu tiên TV Size / Cut Ver (60s - 140s) giúp retry nhanh, ít tốn thể lực.
    5. Mức độ phổ biến: Lượt plays & favourites từ hàng ngàn người chơi kiểm chứng.
    """
    cs = diff.get("CS", 4.0)
    ar = diff.get("AR", 9.0)
    hit_length = diff.get("HitLength", 90)
    playcount = diff.get("Playcount", 0)
    passcount = diff.get("Passcount", 0)
    favs = set_info.get("Favourites", 0)
    sr = diff.get("DifficultyRating", 0)
    ranked_status = set_info.get("RankedStatus", 1)

    score = 50.0
    tags = []

    # Tag trạng thái
    if ranked_status == 1:
        tags.append("Ranked")
    elif ranked_status == 4:
        tags.append("Loved")
    elif ranked_status == 2:
        tags.append("Approved")
    elif ranked_status == 3:
        tags.append("Qualified")

    # 1. Tỷ lệ Pass Rate
    if playcount > 500:
        pass_rate = (passcount / playcount) * 100
        if pass_rate >= 22.0:
            score += 20
            tags.append(f"Pass Rate cao ({pass_rate:.1f}%)")
        elif pass_rate >= 14.0:
            score += 10
            tags.append(f"Pass Rate ổn ({pass_rate:.1f}%)")
        elif pass_rate < 8.0:
            score -= 15
            tags.append(f"Dễ choke ({pass_rate:.1f}%)")

    # 2. Circle Size (CS)
    if 3.8 <= cs <= 4.2:
        score += 15
        tags.append(f"CS đẹp ({cs})")
    elif 4.2 < cs <= 4.4:
        score += 8
    elif cs > 4.6:
        score -= (cs - 4.5) * 25
        tags.append(f"CS nhỏ ({cs})")
    elif cs < 3.5:
        score -= 10

    # 3. Approach Rate (AR)
    if 9.3 <= ar <= 9.7:
        score += 12
        tags.append(f"AR chuẩn ({ar})")
    elif 9.0 <= ar < 9.3:
        score += 5
    elif ar < 9.0 and sr >= 6.5:
        score -= 15
        tags.append(f"AR thấp ({ar})")

    # 4. Độ dài bài (Hit Length)
    if 60 <= hit_length <= 135:
        score += 18
        tags.append("TV Size (Cày nhanh)")
    elif 135 < hit_length <= 220:
        score += 8
        tags.append("Độ dài chuẩn")
    elif hit_length > 300:
        score -= 15
        tags.append("Marathon dài")

    # 5. Phổ biến & Yêu thích
    if playcount > 300000 or favs > 800:
        score += 15
        tags.append("Rất phổ biến")
    elif playcount > 80000 or favs > 200:
        score += 8

    final_score = max(min(round(score, 1), 100.0), 10.0)
    return final_score, tags

def fetch_search_page(query="", amount=100, offset=0, status=1, mode=0, timeout=7):
    """Gửi request tìm kiếm 1 trang beatmaps qua Cheesegull (osu.direct API)"""
    params = {
        "amount": amount,
        "offset": offset,
        "mode": mode
    }
    if status is not None:
        params["status"] = status
    if query:
        params["q"] = query

    url = f"https://osu.direct/api/search?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def find_ranked_farm_maps(
    min_sr=6.5,
    max_sr=7.65,
    limit=30,
    mod="NM",
    status_filter="ranked",
    sort_by="farm_score",
    keyword=None,
    scan_depth=15,
    already_installed_ids=None,
    progress_callback=None
):
    """
    Khám phá và lọc beatmaps trên TOÀN BỘ kho beatmap osu! mà không giới hạn theo bất kỳ mapper hay artist nào.
    Sử dụng cơ chế quét sâu nhiều trang đồng thời (Parallel Offset Traversal).
    """
    if already_installed_ids is None:
        already_installed_ids = set()

    preset = STATUS_PRESETS.get(status_filter, STATUS_PRESETS["ranked"])
    allowed_statuses = preset["values"]
    api_status = preset["api_status"]

    found_sets = {}
    query_str = keyword.strip() if keyword else ""

    # Xác định các batch offsets cần quét (mỗi offset 100 maps)
    # Ví dụ scan_depth = 15 -> quét 15 trang = 1,500 maps
    max_pages = max(scan_depth, 10)
    offsets = [i * 100 for i in range(max_pages)]

    # Chia offsets thành các đợt (chunks) để quét song song, dừng sớm khi đã đủ số lượng
    chunk_size = 5
    offset_chunks = [offsets[i:i + chunk_size] for i in range(0, len(offsets), chunk_size)]

    total_scanned_sets = 0

    for chunk_idx, chunk in enumerate(offset_chunks):
        if len(found_sets) >= limit * 2:
            break

        if progress_callback:
            start_off = chunk[0]
            end_off = chunk[-1] + 100
            progress_callback(
                chunk_idx + 1,
                len(offset_chunks),
                f"Đang quét toàn diện map {start_off} – {end_off} (Đã tìm thấy: {len(found_sets)} maps)..."
            )

        # Quét song song 5 trang cùng lúc
        with ThreadPoolExecutor(max_workers=min(len(chunk), 5)) as pool:
            futures = {
                pool.submit(fetch_search_page, query_str, 100, off, api_status, 0): off
                for off in chunk
            }
            batch_results = []
            for fut in as_completed(futures):
                res = fut.result()
                if res:
                    batch_results.extend(res)

        total_scanned_sets += len(batch_results)

        for s in batch_results:
            sid = s.get("SetID")
            if not sid or sid in already_installed_ids or sid in found_sets:
                continue

            r_status = s.get("RankedStatus", 1)
            if allowed_statuses is not None and r_status not in allowed_statuses:
                continue

            valid_diffs = []
            for b in s.get("ChildrenBeatmaps", []):
                if b.get("Mode", 0) != 0:
                    continue

                raw_sr = b.get("DifficultyRating", 0)
                effective_sr = raw_sr
                calc_ar = b.get("AR", 9.0)
                calc_bpm = b.get("BPM", 180)
                calc_length = b.get("HitLength", 90)

                if mod == "DT":
                    effective_sr = raw_sr * 1.38
                    calc_ar = calculate_dt_ar(calc_ar)
                    calc_bpm = round(calc_bpm * 1.5, 1)
                    calc_length = int(calc_length / 1.5)
                elif mod == "HR":
                    effective_sr = raw_sr * 1.08
                    calc_ar = min(round(calc_ar * 1.4, 1), 10.0)

                if min_sr <= effective_sr <= max_sr:
                    diff_copy = dict(b)
                    diff_copy["DifficultyRating"] = effective_sr
                    diff_copy["AR"] = calc_ar
                    diff_copy["BPM"] = calc_bpm
                    diff_copy["HitLength"] = calc_length

                    score, tags = calculate_objective_farm_score(diff_copy, s)

                    valid_diffs.append({
                        "id": b.get("BeatmapID"),
                        "name": b.get("DiffName"),
                        "sr": round(effective_sr, 2),
                        "raw_sr": round(raw_sr, 2),
                        "cs": b.get("CS"),
                        "ar": calc_ar,
                        "bpm": calc_bpm,
                        "hit_length": calc_length,
                        "playcount": b.get("Playcount", 0),
                        "passcount": b.get("Passcount", 0),
                        "farm_score": score,
                        "tags": tags
                    })

            if valid_diffs:
                best_diff = max(valid_diffs, key=lambda d: d["farm_score"])
                total_plays = sum(d["playcount"] for d in valid_diffs)

                found_sets[sid] = {
                    "id": sid,
                    "title": s.get("Title", "Unknown"),
                    "artist": s.get("Artist", "Unknown"),
                    "creator": s.get("Creator", "Unknown"),
                    "favs": s.get("Favourites", 0),
                    "plays": total_plays,
                    "status_id": r_status,
                    "cover_url": f"https://assets.ppy.sh/beatmaps/{sid}/covers/card.jpg",
                    "preview_audio": f"https://b.ppy.sh/preview/{sid}.mp3",
                    "farm_score": best_diff["farm_score"],
                    "best_tags": best_diff["tags"],
                    "valid_diffs": sorted(valid_diffs, key=lambda x: x["sr"])
                }

    candidate_list = list(found_sets.values())

    # Sắp xếp theo tùy chọn người dùng
    if sort_by == "plays":
        candidate_list.sort(key=lambda x: x["plays"], reverse=True)
    elif sort_by == "favs":
        candidate_list.sort(key=lambda x: x["favs"], reverse=True)
    elif sort_by == "newest":
        candidate_list.sort(key=lambda x: x["id"], reverse=True)
    elif sort_by == "sr_asc":
        candidate_list.sort(key=lambda x: min(d["sr"] for d in x["valid_diffs"]))
    elif sort_by == "sr_desc":
        candidate_list.sort(key=lambda x: max(d["sr"] for d in x["valid_diffs"]), reverse=True)
    else:  # farm_score (mặc định)
        candidate_list.sort(key=lambda x: (x["farm_score"], x["plays"]), reverse=True)

    return candidate_list[:limit]
