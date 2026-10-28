import urllib.request
import urllib.parse
import json
import re

FARM_MAPPERS = [
    "Sotarks", "Nevo", "Reform", "browiec", "Seni", "Kowari",
    "Akitoshi", "Log Off Now", "fieryrage", "SMOKELIND", "Monstrata",
    "Taeyang", "Armin", "Doormat", "SnowNiNo_", "Chanci", "Mirash",
    "Lami", "Awaken", "SkyFlame", "Lasse", "Djulus", "Len", "Kroytz"
]

AIM_JUMP_MAPPERS = {"Sotarks", "Reform", "browiec", "Nevo", "Kowari", "fieryrage", "Akitoshi", "Monstrata", "Taeyang", "Armin", "Doormat"}
FLOW_SPEED_MAPPERS = {"Seni", "SMOKELIND", "Log Off Now", "Chanci", "Mirash", "SkyFlame"}
STREAM_MAPPERS = {"Lasse", "Awaken", "Lami", "Djulus", "Kroytz"}

def calculate_dt_ar(ar):
    """Tính AR sau khi bật mod DoubleTime (DT/NC)"""
    if ar <= 5:
        ms = 1800 - 120 * ar
    else:
        ms = 1200 - 150 * (ar - 5)
    ms_dt = ms * (2 / 3)
    if ms_dt >= 1200:
        return round((1800 - ms_dt) / 120, 2)
    else:
        return round(5 + (1200 - ms_dt) / 150, 2)

def calculate_smart_farm_score(diff, set_info, mod="NM"):
    """
    Thuật toán chấm điểm Farm & Độ thoải mái (Comfort Score: 0 - 100):
    - Đánh giá Pass Rate: Map có tỷ lệ pass cao chứng tỏ pattern mượt, ít choke.
    - Đánh giá CS: CS 3.8 - 4.3 là tỉ lệ vàng của jump farm. CS > 4.6 bị trừ điểm.
    - Đánh giá AR: AR 9.3 - 9.8 phù hợp cao với người chơi rank 12k.
    - Đánh giá độ dài: TV Size (70s - 150s) được cộng điểm tối đa vì dễ cày và retries nhanh.
    - Đánh giá Mapper: Các mappers nổi danh về farm jump/flow aim được gắn tag và ưu tiên.
    """
    cs = diff.get("CS", 4.0)
    ar = diff.get("AR", 9.0)
    hit_length = diff.get("HitLength", 90)
    playcount = diff.get("Playcount", 0)
    passcount = diff.get("Passcount", 0)
    favs = set_info.get("Favourites", 0)
    creator = set_info.get("Creator", "")
    sr = diff.get("DifficultyRating", 0)

    score = 60.0
    tags = []

    # 1. Tỷ lệ Pass Rate (Passcount / Playcount)
    if playcount > 500:
        pass_rate = (passcount / playcount) * 100
        if pass_rate >= 22.0:
            score += 15
            tags.append(f"Pass Rate cao ({pass_rate:.1f}%)")
        elif pass_rate >= 14.0:
            score += 8
            tags.append(f"Pass Rate ổn ({pass_rate:.1f}%)")
        elif pass_rate < 8.0:
            score -= 15  # Map khó hoặc dễ choke cuối

    # 2. Circle Size (CS)
    if 3.8 <= cs <= 4.2:
        score += 10
        tags.append(f"CS đẹp ({cs})")
    elif cs > 4.5:
        score -= (cs - 4.5) * 20
        tags.append(f"CS nhỏ ({cs})")

    # 3. Approach Rate (AR)
    if 9.3 <= ar <= 9.7:
        score += 10
    elif ar < 9.0 and sr >= 6.5:
        score -= 15  # AR thấp ở map 6.5*+ dễ bị dính note

    # 4. Độ dài bài (Length Efficiency)
    if 65 <= hit_length <= 150:
        score += 15
        tags.append("TV Size (Dễ farm)")
    elif 150 < hit_length <= 240:
        score += 5
        tags.append("Độ dài chuẩn")
    elif hit_length > 300:
        score -= 15
        tags.append("Marathon dài")

    # 5. Phân loại phong cách Mapper
    if creator in AIM_JUMP_MAPPERS:
        score += 10
        tags.append("Jump Farm")
    elif creator in FLOW_SPEED_MAPPERS:
        score += 8
        tags.append("Flow Aim")
    elif creator in STREAM_MAPPERS:
        score += 5
        tags.append("Stream/Finger Control")

    # 6. Mức độ phổ biến (Playcount & Favourites)
    if playcount > 500000 or favs > 1000:
        score += 10
        tags.append("Cực kỳ phổ biến")
    elif playcount > 100000 or favs > 300:
        score += 5

    # Giới hạn điểm 0 - 100
    final_score = max(min(round(score, 1), 100.0), 10.0)
    return final_score, tags

def search_osu_direct(query="", amount=50, offset=0, status=1, mode=0):
    """Tìm kiếm beatmaps qua osu.direct Cheesegull API"""
    params = {
        "amount": amount,
        "offset": offset,
        "status": status,
        "mode": mode
    }
    if query:
        params["q"] = query

    url = f"https://osu.direct/api/search?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def find_ranked_farm_maps(
    min_sr=6.5,
    max_sr=7.65,
    limit=50,
    mod="NM",
    already_installed_ids=None,
    mapper_filter=None,
    keyword_filter=None,
    progress_callback=None
):
    """
    Tìm kiếm và chấm điểm beatmaps thông minh theo thuật toán Farm & Comfort Score.
    Hỗ trợ chế độ NM (Nomod), DT (DoubleTime), HR (HardRock).
    """
    if already_installed_ids is None:
        already_installed_ids = set()

    found_sets = {}

    # Xác định danh sách nguồn quét
    if mapper_filter:
        mappers_to_scan = [mapper_filter]
    elif keyword_filter:
        mappers_to_scan = [keyword_filter]
    else:
        mappers_to_scan = FARM_MAPPERS[:15]

    total_steps = len(mappers_to_scan) + (2 if not mapper_filter and not keyword_filter else 0)
    step = 0

    # 1. Quét theo danh sách mappers / từ khóa
    for mapper in mappers_to_scan:
        if len(found_sets) >= limit * 2.5:
            break

        results = search_osu_direct(query=mapper, amount=50, status=1, mode=0)
        for s in results:
            sid = s.get("SetID")
            if not sid or sid in already_installed_ids or sid in found_sets:
                continue

            valid_diffs = []
            for b in s.get("ChildrenBeatmaps", []):
                if b.get("Mode", 0) != 0:
                    continue

                raw_sr = b.get("DifficultyRating", 0)

                # Xử lý theo Mod
                effective_sr = raw_sr
                calc_ar = b.get("AR", 9.0)
                calc_bpm = b.get("BPM", 180)
                calc_length = b.get("HitLength", 90)

                if mod == "DT":
                    # Ước tính SR sau khi DT (tăng ~38%)
                    effective_sr = raw_sr * 1.38
                    calc_ar = calculate_dt_ar(calc_ar)
                    calc_bpm = round(calc_bpm * 1.5, 1)
                    calc_length = int(calc_length / 1.5)
                elif mod == "HR":
                    # Ước tính SR sau khi HR (tăng ~8%)
                    effective_sr = raw_sr * 1.08
                    calc_ar = min(round(calc_ar * 1.4, 1), 10.0)

                if min_sr <= effective_sr <= max_sr:
                    diff_copy = dict(b)
                    diff_copy["DifficultyRating"] = effective_sr
                    diff_copy["AR"] = calc_ar
                    diff_copy["BPM"] = calc_bpm
                    diff_copy["HitLength"] = calc_length

                    score, tags = calculate_smart_farm_score(diff_copy, s, mod=mod)

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
                total_plays = sum(d["playcount"] for d in valid_diffs)
                best_diff = max(valid_diffs, key=lambda d: d["farm_score"])
                cover_url = f"https://assets.ppy.sh/beatmaps/{sid}/covers/card.jpg"
                preview_audio = f"https://b.ppy.sh/preview/{sid}.mp3"

                found_sets[sid] = {
                    "id": sid,
                    "title": s.get("Title"),
                    "artist": s.get("Artist"),
                    "creator": s.get("Creator"),
                    "favs": s.get("Favourites", 0),
                    "plays": total_plays,
                    "cover_url": cover_url,
                    "preview_audio": preview_audio,
                    "farm_score": best_diff["farm_score"],
                    "best_tags": best_diff["tags"],
                    "valid_diffs": sorted(valid_diffs, key=lambda x: x["sr"])
                }

        step += 1
        if progress_callback:
            progress_callback(step, total_steps, f"Đang quét mapper {mapper}...")

    # 2. Quét thêm các map Ranked phổ biến chung nếu chưa đủ
    if len(found_sets) < limit and not mapper_filter and not keyword_filter:
        for offset in [0, 50, 100]:
            if len(found_sets) >= limit * 2:
                break
            results = search_osu_direct(query="", amount=50, offset=offset, status=1, mode=0)
            for s in results:
                sid = s.get("SetID")
                if not sid or sid in already_installed_ids or sid in found_sets:
                    continue

                valid_diffs = []
                for b in s.get("ChildrenBeatmaps", []):
                    if b.get("Mode", 0) != 0:
                        continue
                    raw_sr = b.get("DifficultyRating", 0)
                    effective_sr = raw_sr * 1.38 if mod == "DT" else (raw_sr * 1.08 if mod == "HR" else raw_sr)

                    if min_sr <= effective_sr <= max_sr:
                        score, tags = calculate_smart_farm_score(b, s, mod=mod)
                        valid_diffs.append({
                            "id": b.get("BeatmapID"),
                            "name": b.get("DiffName"),
                            "sr": round(effective_sr, 2),
                            "raw_sr": round(raw_sr, 2),
                            "cs": b.get("CS"),
                            "ar": b.get("AR"),
                            "bpm": b.get("BPM"),
                            "hit_length": b.get("HitLength"),
                            "playcount": b.get("Playcount", 0),
                            "passcount": b.get("Passcount", 0),
                            "farm_score": score,
                            "tags": tags
                        })

                if valid_diffs:
                    best_diff = max(valid_diffs, key=lambda d: d["farm_score"])
                    found_sets[sid] = {
                        "id": sid,
                        "title": s.get("Title"),
                        "artist": s.get("Artist"),
                        "creator": s.get("Creator"),
                        "favs": s.get("Favourites", 0),
                        "plays": sum(d["playcount"] for d in valid_diffs),
                        "cover_url": f"https://assets.ppy.sh/beatmaps/{sid}/covers/card.jpg",
                        "preview_audio": f"https://b.ppy.sh/preview/{sid}.mp3",
                        "farm_score": best_diff["farm_score"],
                        "best_tags": best_diff["tags"],
                        "valid_diffs": sorted(valid_diffs, key=lambda x: x["sr"])
                    }
            step += 1
            if progress_callback:
                progress_callback(step, total_steps, "Đang quét danh sách Ranked phổ biến...")

    # Sắp xếp theo farm_score cao nhất
    sorted_maps = sorted(found_sets.values(), key=lambda x: (x["farm_score"], x["plays"]), reverse=True)
    return sorted_maps[:limit]
