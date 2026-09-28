"""Batch-generate example images for the "upload your photo" prompts.

For every prompt in data/content/edit_*.json, send a reference portrait plus the prompt to an
image-editing API and save the result to images/examples/<slug>.webp. build_site.py picks the
results up from data/examples.json and shows them (with the reference as a "before" inset)
instead of the placeholder artwork.

Reference portraits live in images/refs/<name>.webp. Missing ones are generated first with the
same API as fictional, non-famous people, so no real person's likeness is used. Drop your own
(authorised) photos in images/refs/ with the same names to use them instead.

Usage (run with the project venv: .venv/bin/python gen_examples.py ...):
  export GEMINI_API_KEY=...            # or OPENAI_API_KEY=... with --provider openai
  gen_examples.py --dry-run            # show which reference each prompt uses, and cost
  gen_examples.py                      # generate everything that is missing (resumable)
  gen_examples.py --only e01 e05       # just these ids (or slugs); add --force to redo
  gen_examples.py --use-image e01=path/to/result.webp   # import an image you made by hand
  gen_examples.py --prompt-text "Using my uploaded photo, ..." --ref woman_in --name test1
                                       # one-off: any prompt on one reference -> images/custom/test1.webp
"""
import argparse
import base64
import concurrent.futures as cf
import io
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).parent
REF_DIR = ROOT / "images" / "refs"
OUT_DIR = ROOT / "images" / "examples"
INDEX = ROOT / "data" / "examples.json"

# Fictional reference people. The text is only used when the file is missing.
REFS = {
    "woman_in": "a South Asian woman in her mid-20s with long dark hair",
    "man_in": "a South Asian man in his late 20s with short dark hair and light stubble",
    "woman": "a Brazilian woman in her late 20s with shoulder-length wavy brown hair",
    "man": "a man in his early 30s of mixed Black and white heritage with short curly hair",
    "woman_ea": "an East Asian woman in her mid-20s with straight black hair",
    "couple": "a South Asian couple in their late 20s, a woman and a man, standing side by side",
    "family": "a South Asian family of four: mother, father, a girl of about 10 and a boy of about 6",
}
REF_PROMPT = ("A plain, modern, everyday smartphone photo of {who}, facing the camera with a relaxed "
              "natural expression, {framing}, casual present-day clothes, soft daylight, "
              "simple indoor background. A fictional person, not a real or famous person. "
              "Realistic, unedited, no filters, no text.")
OVERRIDES = {"e33": "woman_ea"}  # prompt id -> reference name

PROVIDERS = {
    "gemini": {"env": "GEMINI_API_KEY", "model": os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"),
               "usd": 0.04},
    "openai": {"env": "OPENAI_API_KEY", "model": os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1"),
               "usd": 0.06},
}


def load_prompts():
    items = []
    for f in sorted((ROOT / "data" / "content").glob("edit_*.json")):
        for c in json.loads(f.read_text()):
            c["slug"] = re.sub(r"[^a-z0-9]+", "-", c["keyword"].lower()).strip("-")
            items.append(c)
    return items


def pick_ref(item, index):
    if item["id"] in OVERRIDES:
        return OVERRIDES[item["id"]]
    cats, kw = item["categories"], item["keyword"]
    india = "bollywood" in cats
    if "couple-family" in cats:
        return "family" if re.search(r"family|album|tv", kw) else "couple"
    if "women" in cats:
        return "woman_in" if india else "woman"
    if "men" in cats:
        return "man_in" if india else "man"
    options = ["woman_in", "man_in"] if india else ["woman", "man", "woman_in", "man_in"]
    return options[index % len(options)]


# ---------------------------------------------------------------- API calls
def call_gemini(key, model, prompt, image_bytes=None):
    parts = []
    if image_bytes:
        parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(image_bytes).decode()}})
    parts.append({"text": prompt})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": "4:5"}}}
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                      headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                      json=body, timeout=180)
    if r.status_code == 400 and "imageConfig" in r.text:  # older models: no aspect-ratio option
        body["generationConfig"].pop("imageConfig")
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                          headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                          json=body, timeout=180)
    r.raise_for_status()
    for cand in r.json().get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                return base64.b64decode(blob["data"])
    raise RuntimeError("no image in response: " + r.text[:300])


def call_openai(key, model, prompt, image_bytes=None):
    headers = {"Authorization": f"Bearer {key}"}
    if image_bytes:
        r = requests.post("https://api.openai.com/v1/images/edits", headers=headers, timeout=300,
                          data={"model": model, "prompt": prompt, "size": "1024x1536", "quality": "medium"},
                          files={"image[]": ("ref.png", image_bytes, "image/png")})
    else:
        r = requests.post("https://api.openai.com/v1/images/generations", headers=headers, timeout=300,
                          json={"model": model, "prompt": prompt, "size": "1024x1536", "quality": "medium"})
    r.raise_for_status()
    return base64.b64decode(r.json()["data"][0]["b64_json"])


def generate(provider, key, prompt, image_bytes=None, tries=4):
    fn = call_gemini if provider == "gemini" else call_openai
    model = PROVIDERS[provider]["model"]
    for attempt in range(tries):
        try:
            return fn(key, model, prompt, image_bytes)
        except requests.HTTPError as e:
            code = e.response.status_code
            if code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {code}: {e.response.text[:300]}") from None
        except (requests.ConnectionError, requests.Timeout, RuntimeError):
            if attempt == tries - 1:
                raise
            time.sleep(10 * (attempt + 1))


# ---------------------------------------------------------------- files
def save_webp(data_or_path, dest, max_side=1200):
    im = Image.open(io.BytesIO(data_or_path) if isinstance(data_or_path, bytes) else data_or_path)
    im = im.convert("RGB")
    im.thumbnail((max_side, max_side))
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "WEBP", quality=82, method=6)
    return im.size


def png_bytes(path):
    buf = io.BytesIO()
    Image.open(path).convert("RGB").save(buf, "PNG")
    return buf.getvalue()


def load_index():
    return json.loads(INDEX.read_text()) if INDEX.exists() else {}


def save_index(index):
    INDEX.write_text(json.dumps(dict(sorted(index.items())), indent=1, ensure_ascii=False) + "\n")


def record(index, item, size, ref, source):
    index[item["slug"]] = {"id": item["id"], "img": f"images/examples/{item['slug']}.webp",
                           "w": size[0], "h": size[1], "ref": f"images/refs/{ref}.webp" if ref else None,
                           "source": source}


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", choices=PROVIDERS, default="gemini")
    ap.add_argument("--only", nargs="*", help="prompt ids (e01) or slugs to process")
    ap.add_argument("--force", action="store_true", help="regenerate even if an image exists")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--use-image", action="append", default=[], metavar="ID=PATH",
                    help="import a hand-made result for a prompt instead of calling the API")
    ap.add_argument("--prompt-text", help="one-off mode: run this prompt instead of the site's prompts")
    ap.add_argument("--prompt-file", help="one-off mode: read the prompt from this text file")
    ap.add_argument("--ref", default="woman_in", choices=REFS, help="reference person for --prompt-text")
    ap.add_argument("--name", default="custom", help="output name for --prompt-text")
    args = ap.parse_args()
    if args.prompt_file:
        args.prompt_text = Path(args.prompt_file).read_text().strip()
        if args.name == "custom":
            args.name = Path(args.prompt_file).stem

    if args.prompt_text:
        key = os.environ.get(PROVIDERS[args.provider]["env"])
        if not key:
            sys.exit(f"set {PROVIDERS[args.provider]['env']} first")
        ref_path = REF_DIR / f"{args.ref}.webp"
        if not ref_path.exists():
            framing = ("waist-up, every face clearly visible and evenly lit" if args.ref in ("couple", "family")
                       else "head and shoulders")
            print(f"creating reference {args.ref} …", flush=True)
            save_webp(generate(args.provider, key, REF_PROMPT.format(who=REFS[args.ref], framing=framing)),
                      ref_path, max_side=1024)
        print(f"generating with {args.provider} ({PROVIDERS[args.provider]['model']}) – this usually takes "
              "20–60 seconds …", flush=True)
        out = ROOT / "images" / "custom" / f"{args.name}.webp"
        size = save_webp(generate(args.provider, key, args.prompt_text, png_bytes(ref_path)), out)
        print(f"before: {ref_path.relative_to(ROOT)}\nafter:  {out.relative_to(ROOT)} {size}")
        return

    items = load_prompts()
    by_key = {**{i["id"]: i for i in items}, **{i["slug"]: i for i in items}}
    index = load_index()

    if args.use_image:
        for spec in args.use_image:
            key, _, path = spec.partition("=")
            item = by_key.get(key)
            if not item or not Path(path).exists():
                sys.exit(f"bad --use-image {spec!r}: unknown id/slug or missing file")
            size = save_webp(Path(path), OUT_DIR / f"{item['slug']}.webp")
            record(index, item, size, None, "manual")
            print(f"imported {path} -> images/examples/{item['slug']}.webp {size}")
        save_index(index)
        return

    print("loading prompts …", flush=True)
    todo = [(i, pick_ref(i, n)) for n, i in enumerate(items)]
    if args.only:
        wanted = set(args.only)
        todo = [(i, r) for i, r in todo if i["id"] in wanted or i["slug"] in wanted]
    if not args.force:
        todo = [(i, r) for i, r in todo if not (OUT_DIR / f"{i['slug']}.webp").exists()]
    refs_needed = sorted({r for _, r in todo if not (REF_DIR / f"{r}.webp").exists()})
    cost = (len(todo) + len(refs_needed)) * PROVIDERS[args.provider]["usd"]

    print(f"{len(todo)} example image(s) to generate, {len(refs_needed)} reference portrait(s) to create "
          f"with {args.provider} ({PROVIDERS[args.provider]['model']}), roughly ${cost:.2f}")
    for i, r in todo:
        print(f"  {i['id']}  {r:9s}  {i['slug']}")
    if args.dry_run or not todo:
        return

    key = os.environ.get(PROVIDERS[args.provider]["env"])
    if not key:
        sys.exit(f"set {PROVIDERS[args.provider]['env']} first")

    for name in refs_needed:
        framing = ("waist-up, every face clearly visible and evenly lit" if name in ("couple", "family")
                   else "head and shoulders")
        print(f"creating reference {name} …", flush=True)
        data = generate(args.provider, key, REF_PROMPT.format(who=REFS[name], framing=framing))
        save_webp(data, REF_DIR / f"{name}.webp", max_side=1024)

    def work(pair):
        item, ref = pair
        data = generate(args.provider, key, item["prompt"], png_bytes(REF_DIR / f"{ref}.webp"))
        return item, ref, save_webp(data, OUT_DIR / f"{item['slug']}.webp")

    failed = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(work, p): p for p in todo}
        for n, fut in enumerate(cf.as_completed(futures), 1):
            item, ref = futures[fut]
            try:
                item, ref, size = fut.result()
                record(index, item, size, ref, args.provider)
                save_index(index)
                print(f"[{n}/{len(todo)}] ok    {item['id']} {item['slug']} {size}", flush=True)
            except Exception as e:  # keep going; report at the end
                failed.append(item["id"])
                print(f"[{n}/{len(todo)}] FAIL  {item['id']} {item['slug']}: {e}", flush=True)
    print(f"done: {len(todo) - len(failed)} ok, {len(failed)} failed" + (f" ({' '.join(failed)})" if failed else ""))
    if failed:
        print("rerun the same command to retry only the missing ones")


if __name__ == "__main__":
    main()
