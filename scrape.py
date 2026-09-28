"""Collect 1980s-photo-style prompts + result images, ranked by engagement.

Sources:
  - OpenArt public search (no auth). Each query only exposes ~60 results, so we
    fan out over many keyword variants and dedupe.
  - Civitai (optional): needs CIVITAI_API_KEY; the unauthenticated API no longer
    returns prompt metadata.

Usage:
  python3 scrape.py                 # scrape + download images + build CSV/JSON
  CIVITAI_API_KEY=xxx python3 scrape.py
"""
import csv
import json
import os
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).parent
DATA = ROOT / "data"
IMAGES = ROOT / "images"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/140 Safari/537.36"}
DELAY = 1.5  # seconds between requests; keep it polite
TOP_N = 150  # how many ranked entries to keep and download

OPENART_QUERIES = [
    "1980s photo", "1980s photograph", "80s photo", "1980s film photo",
    "1980s analog photo", "1980s polaroid", "1980s snapshot", "1980s kodak",
    "vintage 80s photo", "1980s disposable camera", "1980s flash photography",
    "1980s portrait", "1980s street photography", "1980s family photo",
    "1980s mall", "80s film grain", "retro 1980s photo", "1980s yearbook",
    "1980s fashion photo", "1980s japan photo", "kodachrome 1980s",
    "1980s candid photo", "1980s party photo", "1980s bedroom", "1980s tokyo",
    "1980s new york photo", "1980s arcade", "1980s aesthetic photo",
]
OPENART_CURSORS = [0, 1170]  # the two distinct result pages the API exposes

ERA_RE = re.compile(r"1980|\b80s\b|\b80's\b|'80s|eighties|\b198\ds?\b", re.I)


def heat_openart(stats):
    s = stats or {}
    return (s.get("like_count", 0) + 2 * s.get("bookmark_count", 0)
            + s.get("share_count", 0) + s.get("comment_count", 0)
            + s.get("vote_count", 0))


def scrape_openart():
    out = {}
    for q in OPENART_QUERIES:
        for cur in OPENART_CURSORS:
            try:
                r = requests.get("https://openart.ai/api/search", headers=UA, timeout=30,
                                 params=dict(query=q, cursor=cur, method="prompt",
                                             apply_filter="true"))
                items = r.json().get("items", [])
            except Exception as e:
                print(f"  openart {q!r} cursor={cur}: {e}")
                items = []
            for it in items:
                prompt = (it.get("prompt") or "").strip()
                if not prompt or it.get("is_prompt_private") or it["id"] in out:
                    continue
                img = it.get("image") or {}
                stats = it.get("stats") or {}
                out[it["id"]] = {
                    "source": "openart",
                    "id": it["id"],
                    "prompt": prompt,
                    "negative_prompt": it.get("negative_prompt") or "",
                    "model": it.get("ai_model") or it.get("sd_version") or "",
                    "image_url": img.get("raw") or img.get("url") or it.get("image_url") or "",
                    "thumb_url": img.get("512") or img.get("url") or it.get("image_url") or "",
                    "width": it.get("image_width"),
                    "height": it.get("image_height"),
                    "likes": stats.get("like_count", 0),
                    "bookmarks": stats.get("bookmark_count", 0),
                    "shares": stats.get("share_count", 0),
                    "comments": stats.get("comment_count", 0),
                    "heat": heat_openart(stats),
                    "author": (it.get("userProfile") or {}).get("name", ""),
                    "created_at": (it.get("created_at") or {}).get("_seconds"),
                    "post_url": f"https://openart.ai/discovery/{it['id']}",
                    "query": q,
                }
            time.sleep(DELAY)
        print(f"openart {q!r}: total unique {len(out)}")
    return list(out.values())


def scrape_civitai(key):
    """Search 1980s-style models, then pull their most-reacted images with prompts."""
    hdr = dict(UA, Authorization=f"Bearer {key}")
    models = {}
    for q in ["1980s", "80s photo", "1980s photo", "vintage photo 80s"]:
        r = requests.get("https://civitai.com/api/v1/models", headers=hdr, timeout=30,
                         params=dict(query=q, limit=20, sort="Most Downloaded", nsfw="false"))
        for m in r.json().get("items", []):
            models[m["id"]] = m["name"]
        time.sleep(DELAY)
    out = {}
    for mid, mname in models.items():
        r = requests.get("https://civitai.com/api/v1/images", headers=hdr, timeout=30,
                         params=dict(modelId=mid, limit=100, nsfw="None",
                                     sort="Most Reactions", period="AllTime"))
        for it in r.json().get("items", []):
            meta = it.get("meta") or {}
            prompt = (meta.get("prompt") or "").strip()
            if not prompt:
                continue
            st = it.get("stats") or {}
            heat = (st.get("likeCount", 0) + st.get("heartCount", 0) + st.get("laughCount", 0)
                    + st.get("cryCount", 0) + st.get("commentCount", 0))
            out[it["id"]] = {
                "source": "civitai", "id": str(it["id"]), "prompt": prompt,
                "negative_prompt": meta.get("negativePrompt") or "",
                "model": f"{it.get('baseModel') or ''} / {mname}",
                "image_url": it["url"], "thumb_url": it["url"].replace("original=true", "width=512"),
                "width": it.get("width"), "height": it.get("height"),
                "likes": st.get("likeCount", 0) + st.get("heartCount", 0),
                "bookmarks": 0, "shares": 0, "comments": st.get("commentCount", 0),
                "heat": heat, "author": it.get("username") or "",
                "created_at": it.get("createdAt"),
                "post_url": f"https://civitai.com/images/{it['id']}", "query": mname,
            }
        print(f"civitai model {mid} {mname!r}: total unique {len(out)}")
        time.sleep(DELAY)
    return list(out.values())


def download(rows):
    IMAGES.mkdir(exist_ok=True)
    for r in rows:
        url = r["thumb_url"] or r["image_url"]
        ext = os.path.splitext(url.split("?")[0])[1] or ".jpg"
        path = IMAGES / f"{r['source']}_{r['id']}{ext}"
        r["local_image"] = f"images/{path.name}"
        if path.exists():
            continue
        try:
            resp = requests.get(url, headers=UA, timeout=60)
            resp.raise_for_status()
            path.write_bytes(resp.content)
        except Exception as e:
            print(f"  image failed {r['id']}: {e}")
            r["local_image"] = ""
        time.sleep(0.3)


def main():
    DATA.mkdir(exist_ok=True)
    rows = scrape_openart()
    key = os.environ.get("CIVITAI_API_KEY")
    if key:
        rows += scrape_civitai(key)
    else:
        print("CIVITAI_API_KEY not set; skipping Civitai")

    raw = len(rows)
    rows = [r for r in rows if ERA_RE.search(r["prompt"])]
    # Near-duplicate prompts (same text re-posted) -> keep the hottest one.
    best = {}
    for r in rows:
        k = re.sub(r"\W+", " ", r["prompt"].lower()).strip()[:200]
        if k not in best or r["heat"] > best[k]["heat"]:
            best[k] = r
    rows = sorted(best.values(), key=lambda r: (r["heat"], r["likes"]), reverse=True)[:TOP_N]
    print(f"{raw} scraped -> {len(best)} era-relevant unique -> keeping top {len(rows)}")

    download(rows)
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    (DATA / "prompts.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    cols = ["rank", "source", "heat", "likes", "bookmarks", "shares", "comments", "prompt",
            "negative_prompt", "model", "author", "post_url", "image_url", "local_image",
            "width", "height", "created_at", "query", "id"]
    with open(DATA / "prompts.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {DATA/'prompts.csv'} and {DATA/'prompts.json'}")


if __name__ == "__main__":
    main()
