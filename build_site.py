"""Build the static site for vintagephotoprompt.com into public/.

Pages:
  /                      homepage gallery (target keyword "1980s photo prompt")
  /<category>/           category pages (portrait, fashion, polaroid-film, ...)
  /prompt/<slug>/        one detail page per prompt
  /sitemap.xml, /robots.txt, /404.html, /assets/site.css, /assets/site.js

Inputs: data/prompts.json (scraped prompts) and data/content/*.json (per-prompt copy:
name, slug, title, description, categories, intro, creates, works, tips, suits, personalize).
Images stay in images/ and are served at /images/ by server.js.
"""
import datetime
import hashlib
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "public"
SITE = "vintagephotoprompt.com"
BASE = f"https://{SITE}/"
TODAY = datetime.date.today().isoformat()
YEAR = datetime.date.today().year

esc = lambda s: html.escape(str(s or ""), quote=True)
# cache-busting version for /assets files (they are served with a 1-day max-age)
ASSET_V = hashlib.md5((ROOT / "assets" / "site.css").read_bytes() + (ROOT / "assets" / "site.js").read_bytes()).hexdigest()[:8]
ld_json = lambda obj: json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

# ---------------------------------------------------------------- data
rows = {r["id"]: r for r in json.loads((ROOT / "data" / "prompts.json").read_text())}
copy = {}
for f in sorted((ROOT / "data" / "content").glob("batch_*.json")):
    for c in json.loads(f.read_text()):
        copy[c["id"]] = c
# Per-page target keyword, title and description (overrides the drafted ones).
kw_file = ROOT / "data" / "content" / "keywords.json"
for k in json.loads(kw_file.read_text()) if kw_file.exists() else []:
    if k["id"] in copy:
        copy[k["id"]].update(keyword=k["keyword"], title=k["title"], description=k["description"],
                             slug=re.sub(r"[^a-z0-9]+", "-", k["keyword"].lower()).strip("-"))

CATEGORIES = {
    "portrait": {
        "name": "Portrait", "h1": "1980s Portrait Photo Prompts",
        "title": "1980s Portrait Photo Prompts – Free to Copy",
        "description": "Browse 1980s portrait photo prompts with studio backdrops, on-camera flash, "
                       "big hair and warm film color. Open any example and copy the prompt.",
        "intro": [
            "These 1980s portrait photo prompts rebuild the whole picture, not just the hairstyle: "
            "the mottled studio backdrop, the soft-box or bare flash, the slightly warm film stock "
            "and the posed, direct look people gave the camera back then.",
            "Use them for profile pictures, character sheets, album art or period-film mood boards. "
            "Open any example to see the full prompt, which model made it, and how to swap in your "
            "own subject while keeping the look.",
        ],
        "guide_h2": "How to write a convincing 1980s portrait prompt",
        "guide": [
            "Start with the backdrop. School-picture blues, marbled grey canvas and laser-beam "
            "backgrounds place a portrait in the decade before the viewer even looks at the face.",
            "Then decide on the light. A single on-camera flash gives hard shadows and bright skin; "
            "a big soft box gives the glossy glamour-shot finish of mall photo studios.",
            "Finally, keep the pose simple. Chin slightly down, shoulders angled, eyes straight to "
            "the lens: stiff, friendly and a little formal is exactly how most 80s portraits looked.",
        ],
        "source": ("portrait photography", "https://en.wikipedia.org/wiki/Portrait_photography"),
    },
    "fashion": {
        "name": "Fashion & Hair", "h1": "1980s Fashion Photo Prompts",
        "title": "1980s Fashion Photo Prompts – Hair, Glam & Street Style",
        "description": "1980s fashion photo prompts for AI: teased hair, shoulder pads, neon "
                       "workout wear, denim and glam rock styling. Copy the prompt behind each look.",
        "intro": [
            "Clothes and hair date a picture faster than anything else, so these 1980s fashion "
            "photo prompts lean on the details that scream the decade: teased volume, power "
            "shoulders, acid-wash denim, leg warmers, chunky jewelry and glossy makeup.",
            "Each example lists the exact wording that produced the outfit, so you can keep the "
            "styling language and swap the model, setting or color palette to fit your own shoot.",
        ],
        "guide_h2": "Fashion details that make a 1980s photo prompt work",
        "guide": [
            "Name the silhouette, not just the garment. “Oversized blazer with sharp shoulder pads” "
            "or “high-waisted acid-wash jeans” gives the model far more to work with than “80s outfit”.",
            "Hair needs volume words: teased, crimped, permed, feathered, side ponytail. Pair them "
            "with hairspray shine and a little frizz so it does not look like a modern wig.",
            "Makeup finishes the look. Bright blush placed high, frosted or electric eyeshadow and "
            "glossy lips read instantly as the decade under a hard flash.",
        ],
        "source": ("1980s in fashion", "https://en.wikipedia.org/wiki/1980s_in_fashion"),
    },
    "polaroid-film": {
        "name": "Polaroid & Film", "h1": "1980s Polaroid Photo Prompts",
        "title": "1980s Polaroid Photo Prompts – Film, Flash & Grain",
        "description": "1980s Polaroid photo prompts that fake real 80s film: instant borders, "
                       "disposable-camera flash, 35mm grain and faded color. Copy any prompt free.",
        "intro": [
            "The fastest way to make an AI image feel old is to describe how it was captured, and "
            "these 1980s Polaroid photo prompts do exactly that: instant film, 35mm stock, direct "
            "flash, light leaks, soft focus and color shifts.",
            "Pick an example close to the texture you want, copy the prompt, and keep the camera "
            "and film phrases intact when you change the subject.",
        ],
        "guide_h2": "How to make a Polaroid photo prompt look like real film",
        "guide": [
            "Say which camera took the shot. Polaroid 600, a disposable point-and-shoot or a "
            "cheap 35mm compact each produce a different mix of flash, sharpness and color.",
            "Ask for the flaws: slight overexposure, dust, a warm or green color cast, uneven "
            "borders and a little motion blur. Perfect images are the giveaway of AI.",
            "Avoid modern quality words. Terms like 8K, ultra detailed or HDR fight directly "
            "against the soft, grainy texture you are trying to recreate.",
        ],
        "source": ("instant film", "https://en.wikipedia.org/wiki/Instant_film"),
    },
    "neon-city": {
        "name": "Neon & City", "h1": "1980s Neon Photo Prompts",
        "title": "1980s Neon Photo Prompts – City Nights & Synthwave",
        "description": "1980s neon photo prompts for city-night images: neon signs, wet streets, "
                       "arcades and pink-and-cyan light. Browse examples and copy any prompt free.",
        "intro": [
            "Pink and cyan light, reflections on wet asphalt, diner signs and arcade glow: these "
            "1980s neon photo prompts capture one of the most recognisable looks in AI imagery, "
            "and one of the easiest to overdo.",
            "Each example shows how much light, haze and color to ask for so the scene reads as a "
            "night out in the decade rather than a generic cyberpunk render.",
        ],
        "guide_h2": "Keeping neon photo prompts believable",
        "guide": [
            "Anchor the glow to real places: a motel sign, a diner, an arcade entrance or a car "
            "wash. Neon with a source feels photographed; neon everywhere feels like a render.",
            "Wet ground doubles the light for free. Ask for rain-soaked pavement or a puddle in the "
            "foreground and the reflections do most of the atmosphere work.",
            "Keep technology period-correct. Boxy cars, payphones and CRT screens stop the model "
            "drifting into futuristic cyberpunk territory.",
        ],
        "source": ("neon lighting", "https://en.wikipedia.org/wiki/Neon_lighting"),
    },
    "cinematic": {
        "name": "Cinematic", "h1": "1980s Cinematic Photo Prompts",
        "title": "1980s Cinematic Photo Prompts – Movie Still Looks",
        "description": "1980s cinematic photo prompts for movie-still images: dramatic lighting, "
                       "period sets and story-driven scenes. Browse examples and copy the prompt.",
        "intro": [
            "These 1980s cinematic photo prompts treat the image as a frame from a film shot in the "
            "decade: a clear scene, motivated light, period set dressing and the soft, grainy "
            "finish of a 35mm print.",
            "They work well for storyboards, pitch decks, book covers and any project that needs a "
            "moment frozen mid-story rather than a posed portrait.",
        ],
        "guide_h2": "Writing a cinematic photo prompt like a film still",
        "guide": [
            "Describe a moment, not a pose. Something should be about to happen, or have just "
            "happened, so the frame carries tension the way a real movie still does.",
            "Give the light a source: a desk lamp, a TV screen, headlights through blinds. "
            "Motivated light is what separates cinematic images from studio portraits.",
            "Mention the lens and format. Anamorphic widescreen, shallow depth of field and a "
            "subtle halation around highlights all point toward 80s cinema.",
        ],
        "source": ("cinematography", "https://en.wikipedia.org/wiki/Cinematography"),
    },
    "illustration": {
        "name": "Illustration & 3D", "h1": "1980s Illustration Prompts",
        "title": "1980s Illustration Prompts – Comic, Airbrush & 3D Art",
        "description": "1980s illustration prompts for AI art that is not a photo: comic panels, "
                       "airbrush posters, toy box art and 3D renders. Browse and copy any prompt.",
        "intro": [
            "Not every retro image needs to look like a photograph. These 1980s illustration "
            "prompts cover the drawn and rendered side of the decade: airbrushed posters, comic "
            "panels, toy-line box art and 3D scenes that borrow 80s color and nostalgia.",
            "Use them as a starting point for covers, merch and fan art, or mix their color "
            "language into the photographic prompts elsewhere on the site.",
        ],
        "guide_h2": "Getting the 1980s illustration style right in a prompt",
        "guide": [
            "Name the medium. Airbrush, gouache, cel animation, halftone comic print and early "
            "CGI each have a distinct texture that the model can reproduce.",
            "Borrow the palette: hot pink, teal, purple gradients and chrome lettering signal the "
            "decade even when the subject is modern.",
            "Reference the format rather than an artist, such as a VHS cover, arcade flyer or "
            "Saturday-morning cartoon title card, to keep results original.",
        ],
        "source": ("airbrush art", "https://en.wikipedia.org/wiki/Airbrush"),
    },
}

# "Upload your photo" (image-edit) collections, listed before the text-to-image ones.
HUB = "chatgpt-1980s-photo-prompts"
EDIT_CATEGORIES = {
    HUB: {
        "name": "Upload Your Photo", "h1": "ChatGPT 1980s Photo Prompts",
        "title": "ChatGPT 1980s Photo Prompts – Turn Your Photo Into the 80s",
        "description": "ChatGPT 1980s photo prompts that turn your own picture into a real-looking 80s "
                       "photo. Your face stays, the hair, outfit and setting change. Works in Gemini too.",
        "intro": [
            "These ChatGPT 1980s photo prompts are made for the viral trend: upload a clear photo of "
            "yourself, paste a prompt, and see what you would have looked like in 1985. Every prompt "
            "locks your face and identity, then changes only the hair, clothes, setting and film look.",
            "They work the same way in Gemini. Pick a style below, from Bollywood studio portraits and "
            "wedding albums to mall laser backdrops, arcades and VHS home videos.",
        ],
        "guide_h2": "How to keep your face in a ChatGPT photo prompt",
        "guide": [
            "Upload the right photo. A sharp, front-facing picture in daylight with your whole face "
            "visible gives the model the most to hold on to. Skip sunglasses, heavy filters and group "
            "shots unless the prompt is written for groups.",
            "If the face drifts, do not start over. Reply in the same chat with a short correction such "
            "as “keep my face exactly as in the uploaded photo, change only the clothes and background” "
            "and regenerate.",
            "Push the era with capture details rather than more clothing words. Direct flash, film "
            "grain, a slight color cast and a date stamp make the result look found, not filtered.",
        ],
        "source": ("the 1980s", "https://en.wikipedia.org/wiki/1980s"),
    },
    "bollywood": {
        "name": "Bollywood & India", "h1": "1980s Bollywood Photo Prompts",
        "title": "1980s Bollywood Photo Prompts for ChatGPT & Gemini",
        "description": "1980s Bollywood photo prompts for your own photo: heroine and hero portraits, "
                       "wedding albums, Doordarshan-era and street looks. For ChatGPT and Gemini.",
        "intro": [
            "These 1980s Bollywood photo prompts turn your uploaded picture into the kind of image that "
            "filled film magazines, studio walls and family albums in 80s India: voluminous curls, silk "
            "sarees, moustaches, painted backdrops and warm tungsten light.",
            "Each one keeps your face and skin tone recognisable and changes the styling around you, "
            "from a heroine publicity still to a 1987 bazaar street or a wedding album page.",
        ],
        "guide_h2": "What makes a Bollywood photo prompt look authentic",
        "guide": [
            "Studio portraits of the time used painted or mottled backdrops and a single warm key "
            "light. Ask for those instead of a plain modern background.",
            "Jewellery and hair carry the look: gold jhumkas, bangles, a bindi, bouffant or soft curls "
            "for women; thick side-parted hair and a moustache for men.",
            "Keep colors rich but slightly aged. Saturated reds and golds with a faded print finish "
            "read as 80s India, while heavy sepia makes the picture look decades older.",
        ],
        "source": ("Hindi cinema", "https://en.wikipedia.org/wiki/Hindi_cinema"),
    },
    "men": {
        "name": "Men", "h1": "1980s Photo Prompts for Men",
        "title": "1980s Photo Prompts for Men – ChatGPT & Gemini",
        "description": "1980s photo prompts for men: moustache studio portraits, denim and classic "
                       "cars, office suits, gym shots and motorcycle heroes. Upload your photo and copy.",
        "intro": [
            "These 1980s photo prompts for men start from your own uploaded picture and rebuild it with "
            "the decade's staples: thick feathered hair, a neat moustache, denim jackets, wide ties, "
            "tank tops and the classic cars and motorcycles people posed beside.",
            "Every prompt keeps your face, age and build recognisable, so the result looks like an old "
            "photo of you rather than a stranger in costume.",
        ],
        "guide_h2": "Details that make a men's photo prompt convincing",
        "guide": [
            "Hair first: thick, side-parted or feathered with visible volume. If you have a beard "
            "today, decide whether the prompt should trim it to a moustache or keep it.",
            "Choose one strong prop that dates the picture, such as a boxy car, a chrome motorcycle, a "
            "wall of dumbbells or a wood-panelled office, rather than many small ones.",
            "Direct flash and warm film color are more convincing than piling on more era clothing. "
            "Ask for grain and a slightly soft focus.",
        ],
        "source": ("1980s in fashion", "https://en.wikipedia.org/wiki/1980s_in_fashion"),
    },
    "women": {
        "name": "Women", "h1": "1980s Photo Prompts for Women",
        "title": "1980s Photo Prompts for Women – ChatGPT & Gemini",
        "description": "1980s photo prompts for women: big-hair studio glamour, denim street style, "
                       "power suits, leather and motorcycles. Upload your photo to ChatGPT or Gemini.",
        "intro": [
            "These 1980s photo prompts for women turn your uploaded picture into a studio glamour shot, "
            "a street-style snapshot or a power-suit portrait, with the volume, shoulder pads, bold "
            "makeup and warm film color of the decade.",
            "Your face, skin tone and proportions stay the same; only the hair, wardrobe, setting and "
            "photo finish change.",
        ],
        "guide_h2": "How to style a women's photo prompt",
        "guide": [
            "Pick one hair signature: big teased curls, a side ponytail, crimped waves or a feathered "
            "bob. Naming it precisely avoids a generic modern blowout.",
            "Balance the outfit with the setting. A silk blouse and pearls belong in a soft-box studio; "
            "an oversized denim jacket belongs on a sunny street.",
            "Ask for period makeup placed the way it was then: blush high on the cheekbones, bright or "
            "frosted eyeshadow and glossy lips.",
        ],
        "source": ("1980s in fashion", "https://en.wikipedia.org/wiki/1980s_in_fashion"),
    },
    "couple-family": {
        "name": "Couple & Family", "h1": "1980s Couple and Family Photo Prompts",
        "title": "1980s Couple and Family Photo Prompts for ChatGPT",
        "description": "1980s couple and family photo prompts: upload a photo of two or more people "
                       "and get a prom night, wedding album, TV night or holiday snapshot from the 80s.",
        "intro": [
            "These 1980s couple and family photo prompts are written for pictures with more than one "
            "person. Upload a photo of you and your partner, parents or kids, and the prompt keeps every "
            "face while turning the scene into an 80s prom night, wedding album or living-room snapshot.",
            "They are the version of the trend people share most in family groups, because everyone "
            "gets to see themselves in the same old photo.",
        ],
        "guide_h2": "Getting every face right in a group photo prompt",
        "guide": [
            "Use one photo where everyone faces the camera and is clearly lit. Separate photos can "
            "work, but the model keeps faces better when they arrive together.",
            "Name how many people should appear. A line such as “keep all four people from the "
            "uploaded photo” stops the model dropping or adding someone.",
            "If one face drifts, ask the model to fix only that person and keep the rest of the image "
            "unchanged.",
        ],
        "source": ("snapshot photography", "https://en.wikipedia.org/wiki/Snapshot_(photography)"),
    },
    "studio": {
        "name": "Studio Portraits", "h1": "1980s Studio Portrait Prompts",
        "title": "1980s Studio Portrait Prompts – Yearbook, ID & Glamour",
        "description": "1980s studio portrait prompts for your own photo: yearbook, passport, black and "
                       "white headshots, laser backdrops and the classic 1985 look. ChatGPT and Gemini.",
        "intro": [
            "These 1980s studio portrait prompts recreate the pictures most people actually have from "
            "the decade: school yearbooks, ID photos, mall glamour shots and formal headshots, all built "
            "from your own uploaded photo.",
            "They start with the 1985 prompt that kicked off the trend and move through flat yearbook "
            "light, laser-beam backdrops and silver-gelatin black and white.",
        ],
        "guide_h2": "Lighting a studio portrait prompt the 80s way",
        "guide": [
            "Yearbook and ID photos used flat, even light from the front. Ask for it explicitly or the "
            "model will add dramatic modern shadows.",
            "Glamour studios used a big soft box, a hair light and heavy diffusion. Words like soft "
            "focus and airbrushed glow push the result in that direction.",
            "Backdrops matter as much as clothes: mottled grey or blue canvas, laser beams or a pastel "
            "gradient each date the image at a glance.",
        ],
        "source": ("portrait photography", "https://en.wikipedia.org/wiki/Portrait_photography"),
    },
    "retro-scenes": {
        "name": "Retro Scenes", "h1": "1980s Retro Scene Photo Prompts",
        "title": "1980s Retro Scene Photo Prompts – Arcade, VHS & Disco",
        "description": "1980s retro scene photo prompts that put you in an arcade, a diner, a roller "
                       "disco, a VHS home video or a Miami sunset. Upload your photo and copy a prompt.",
        "intro": [
            "These 1980s retro scene photo prompts drop you into the places that define the decade: a "
            "glowing arcade, a chrome diner, a roller rink, a wood-panelled living room on camcorder "
            "tape and a pastel Miami sunset.",
            "Each prompt keeps your face and builds the whole scene around you, including the light, "
            "the camera and the small imperfections that make an old photo believable.",
        ],
        "guide_h2": "Choosing the right scene for your photo prompt",
        "guide": [
            "Match the scene to your uploaded photo. A close-up selfie suits portrait-style scenes like "
            "the arcade; a full-body shot works better for roller disco or car scenes.",
            "Let the light come from the scene: cabinet screens, mirror balls, diner fluorescents or "
            "sunset. That keeps your face lit the same way as the background.",
            "Add the capture format last. VHS scan lines, disposable-camera flash or a date stamp "
            "finish the scene without touching your face.",
        ],
        "source": ("VHS", "https://en.wikipedia.org/wiki/VHS"),
    },
}
PALETTES = {  # placeholder gradients per primary category
    "bollywood": ("#7a1f3d", "#e8a24a"), "men": ("#1d3557", "#457b9d"), "women": ("#6a1b4d", "#e76f8a"),
    "couple-family": ("#3d2c5e", "#d4a373"), "studio": ("#23395b", "#8ea8c3"),
    "retro-scenes": ("#2b1055", "#ff2e88"), HUB: ("#2b1055", "#e8a24a"),
}
for v in CATEGORIES.values():
    v["group"] = "t2i"
for v in EDIT_CATEGORIES.values():
    v["group"] = "edit"
CATEGORIES = {**EDIT_CATEGORIES, **CATEGORIES}

TOOL = [  # model id pattern -> tool shown in "Best with"
    (r"nano-banana", "Gemini (Nano Banana)"),
    (r"gpt_image", "ChatGPT (GPT Image)"),
    (r"seedream", "Seedream"),
    (r"kling", "Kling"),
    (r"imagen", "Gemini (Imagen)"),
    (r"flux", "Flux"),
]


def tool_for(model):
    for pat, name in TOOL:
        if re.search(pat, model or "", re.I):
            return name
    return "Any image model"


items = []
for r in sorted(rows.values(), key=lambda r: (-r["heat"], r["rank"])):
    c = copy.get(r["id"])
    if not c:
        print("no copy for", r["id"], "- skipped")
        continue
    cats = [k for k in c["categories"] if k in CATEGORIES]
    primary = c["primary_category"] if c["primary_category"] in CATEGORIES else (cats or ["cinematic"])[0]
    if primary not in cats:
        cats.insert(0, primary)
    items.append({**c, "row": r, "img": "/" + r["local_image"], "w": r["width"], "h": r["height"],
                  "prompt": r["prompt"].strip(), "neg": (r.get("negative_prompt") or "").strip(),
                  "tool": tool_for(r.get("model")), "author": r.get("author") or "",
                  "post_url": r["post_url"], "primary": primary, "cats": cats,
                  "url": f"/prompt/{c['slug']}/"})
slugs = [it["slug"] for it in items]
assert len(slugs) == len(set(slugs)), "duplicate slugs"
for i, it in enumerate(items):
    it["pinned"] = i < 10
    it["alt"] = f"{it['name']}: example image made with this AI prompt"
    it.setdefault("keyword", it["name"].lower() + " prompt")
    it["kw_title"] = " ".join(w if w[0].isdigit() else w.capitalize() for w in it["keyword"].split())
items[0]["alt"] = f"1980s photo prompt example: {items[0]['name']}"
for it in items:
    it["group"] = "t2i"


def placeholder_svg(it):
    """Stand-in artwork for edit prompts until a real before/after example exists."""
    c1, c2 = PALETTES.get(it["primary"], PALETTES[HUB])
    words, lines = it["name"].split(), [""]
    for w in words:
        if len(lines[-1]) + len(w) > 16:
            lines.append("")
        lines[-1] = (lines[-1] + " " + w).strip()
    text = "".join(f'<tspan x="90" dy="{0 if i == 0 else 104}">{esc(l)}</tspan>' for i, l in enumerate(lines))
    stripes = "".join(f'<rect x="0" y="{800 + i * 34}" width="1080" height="{6 + i * 3}" fill="{c1}"/>' for i in range(6))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350">
<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
<linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd27a"/><stop offset="1" stop-color="#ff5e8a"/></linearGradient></defs>
<rect width="1080" height="1350" fill="url(#g)"/>
<circle cx="760" cy="880" r="230" fill="url(#s)" opacity=".9"/>{stripes}
<text x="90" y="170" font-family="Georgia, serif" font-size="40" fill="#fff" opacity=".8" letter-spacing="4">UPLOAD YOUR PHOTO · 1980s</text>
<text y="330" font-family="Georgia, serif" font-size="92" font-weight="700" fill="#fff">{text}</text>
<text x="90" y="1270" font-family="Helvetica, Arial, sans-serif" font-size="34" fill="#fff" opacity=".85">Example image coming soon · vintagephotoprompt.com</text>
</svg>
"""


edits = []
for f in sorted((ROOT / "data" / "content").glob("edit_*.json")):
    for c in json.loads(f.read_text()):
        slug = re.sub(r"[^a-z0-9]+", "-", c["keyword"].lower()).strip("-")
        cats = [k for k in c["categories"] if k in CATEGORIES]
        edits.append({**c, "slug": slug, "img": f"/placeholders/{slug}.svg", "w": 1080, "h": 1350,
                      "placeholder": True, "prompt": c["prompt"].strip(), "neg": "",
                      "tool": c.get("best_with") or "ChatGPT or Gemini", "author": "", "post_url": "",
                      "primary": cats[0], "cats": cats, "url": f"/prompt/{slug}/", "group": "edit",
                      "pinned": False, "alt": f"{c['name']} – example image coming soon"})
        edits[-1]["kw_title"] = " ".join(w if w[0].isdigit() else w.capitalize() for w in c["keyword"].split())
        edits[-1]["kw_title"] = edits[-1]["kw_title"].replace("Chatgpt", "ChatGPT")
all_items = items + edits
slugs = [it["slug"] for it in all_items]
assert len(slugs) == len(set(slugs)), "duplicate slugs"
by_cat = {k: [it for it in all_items if k in it["cats"]] for k in CATEGORIES}


# ---------------------------------------------------------------- shared chrome
def head(title, desc, path, og_img, ld=None, extra="", noindex=False):
    url = BASE + path.lstrip("/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{'<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="{url}">'}
<meta property="og:site_name" content="Vintage Photo Prompt">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="{extra or 'website'}">
<meta property="og:image" content="{BASE}{og_img.lstrip('/')}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css?v={ASSET_V}">
{f'<script type="application/ld+json">{ld_json(ld)}</script>' if ld else ''}
</head>
<body>
<header class="top"><div class="top-in">
  <a class="logo" href="/" aria-label="Vintage Photo Prompt home">
    <span class="mark"><svg viewBox="0 0 24 24" fill="none" stroke="#1b1408" stroke-width="2" aria-hidden="true"><rect x="3" y="6" width="18" height="14" rx="2"/><circle cx="12" cy="13" r="3.5"/><path d="M8 6l1.5-2h5L16 6"/></svg></span>
    <span class="word">vintage<span>photoprompt</span></span>
  </a>
  <form class="search" action="/" method="get" role="search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
    <input id="q" name="q" type="search" placeholder="Search prompts: polaroid, neon, portrait…" aria-label="Search prompts"></form>
  <nav aria-label="Main"><a href="/">Home</a><a href="/{HUB}/">Upload Your Photo</a><a href="/portrait/">Portrait</a><a href="/fashion/">Fashion</a><a href="/polaroid-film/">Polaroid &amp; Film</a><a href="/neon-city/">Neon &amp; City</a></nav>
</div></header>
"""


FOOT = f"""<footer class="foot">
  <nav aria-label="Categories">{''.join(f'<a href="/{k}/">{esc(v["h1"])}</a>' for k, v in CATEGORIES.items())}<a href="/prompts.html">All prompts as text</a></nav>
  <p>© {YEAR} {SITE} · A free library of vintage and 1980s AI photo prompts. Example images belong to their creators.</p>
</footer>
<div class="toast" id="toast" role="status"></div>
<script src="/assets/site.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


def card(it, i, eager=False, alt=None):
    return (f'<a class="pin" href="{it["url"]}" data-slug="{it["slug"]}">'
            f'<img src="{it["img"]}" width="{it["w"]}" height="{it["h"]}" loading="{"eager" if eager else "lazy"}"'
            f' decoding="async" alt="{esc(alt or it["alt"])}">'
            f'<span class="badge{"" if it["pinned"] else " p"}"><i></i>{"Pinned" if it["pinned"] else "Prompt"}</span>'
            f'<span class="over"><span class="nm">{esc(it["name"])}</span></span></a>')


def grid(cards_items, max_cols=5, search=False, first_alt=None):
    body = "\n".join(card(it, i, eager=i < 6, alt=first_alt if i == 0 else None) for i, it in enumerate(cards_items))
    # prompt text for the hover "Copy prompt" button (and search on the homepage)
    data = f'<script>window.PROMPTS = Object.assign(window.PROMPTS || {{}}, {ld_json({it["slug"]: {"p": it["prompt"], "n": it["name"]} for it in cards_items})});</script>'
    return f'<div class="grid" data-max="{max_cols}"{" data-search" if search else ""}>\n{body}\n</div>\n{data}'


def chips(active="", group="t2i"):
    if group == "edit":
        out = [f'<a class="chip{" on" if k == active else ""}" href="/{k}/">{esc("All photo edits" if k == HUB else v["name"])}</a>'
               for k, v in CATEGORIES.items() if v["group"] == "edit"]
        out.append('<a class="chip" href="/">Text-to-image gallery</a>')
    else:
        out = [f'<a class="chip{" on" if not active else ""}" href="/">All</a>']
        out += [f'<a class="chip{" on" if k == active else ""}" href="/{k}/">{esc(v["name"])}</a>'
                for k, v in CATEGORIES.items() if v["group"] == "t2i"]
        out.append(f'<a class="chip" href="/{HUB}/">Upload your photo</a>')
    return f'<nav class="chips" aria-label="Categories">{"".join(out)}</nav>'


def crumbs(trail):
    """trail: [(name, path)], last one is the current page."""
    links = []
    for n, (name, path) in enumerate(trail):
        links.append(f'<span aria-current="page">{esc(name)}</span>' if n == len(trail) - 1
                     else f'<a href="{path}">{esc(name)}</a>')
    ld = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": n + 1, "name": name, "item": BASE + path.lstrip("/")}
        for n, (name, path) in enumerate(trail)]}
    return f'<nav class="crumbs" aria-label="Breadcrumb">{" <span>›</span> ".join(links)}</nav>', ld


COPY_ICON = ('<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" '
             'aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>')


def low(text):
    """Lowercase a heading for use mid-sentence, keeping brand names cased."""
    return text.lower().replace("chatgpt", "ChatGPT")


def first_sentences(text, max_words=40):
    out = ""
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if out and len((out + " " + sent).split()) > max_words:
            break
        out = (out + " " + sent).strip()
    return out


def write(path, text):
    f = OUT / path.lstrip("/")
    if path.endswith("/"):
        f = f / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- homepage
FAQ = [
    ("Which AI image tools work with these retro prompts?",
     "Any text-to-image model. The examples here were made with Nano Banana, Seedream, Kling, "
     "Imagen and GPT Image, and the same prompt text also works in Midjourney, Flux or Stable "
     "Diffusion. Expect small differences in grain and color from one model to the next."),
    ("Can I turn my own photo into a 1980s photo with these prompts?",
     "Yes. Upload your picture to a model that supports image editing, paste the prompt, and "
     "replace the subject description with a short line such as “the person in the uploaded "
     "photo”. Keep the lighting, film and color details so the retro look carries over."),
    ("Are the prompts free to copy?",
     "Yes, every prompt on this page can be copied and adapted for your own images. The example "
     "pictures belong to the creators who posted them, so link to the original post if you "
     "republish one of their images."),
]
HOME_TITLE = "1980s Photo Prompt Gallery – Copy Retro AI Prompts"
HOME_DESC = (f"Browse {len(items)} AI images and copy the exact 1980s photo prompt behind each one: "
             "film grain, Polaroid flash, neon nights, big hair and retro portraits.")
home_ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "WebSite", "@id": BASE + "#website", "url": BASE, "name": "Vintage Photo Prompt",
     "potentialAction": {"@type": "SearchAction", "target": BASE + "?q={search_term_string}",
                         "query-input": "required name=search_term_string"}},
    {"@type": "CollectionPage", "@id": BASE + "#page", "url": BASE, "name": HOME_TITLE,
     "description": HOME_DESC, "isPartOf": {"@id": BASE + "#website"}, "mainEntity": {"@id": BASE + "#gallery"}},
    {"@type": "ItemList", "@id": BASE + "#gallery", "name": "1980s photo prompt examples",
     "numberOfItems": len(items),
     "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": BASE + it["url"].lstrip("/"),
                          "name": it["name"]} for i, it in enumerate(items)]},
    {"@type": "FAQPage", "@id": BASE + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
]}
faq_html = "\n".join(f"<h3>{esc(q)}</h3>\n<p>{esc(a)}</p>" for q, a in FAQ)

write("/", head(HOME_TITLE, HOME_DESC, "/", items[0]["img"], home_ld) + f"""
<main>
<div class="wrap intro">
  <h1>1980s Photo Prompt Gallery</h1>
  <p>Every image on this page was made with AI, and each one comes with the exact 1980s photo prompt that produced it. Browse film grain, Polaroid flash, neon streets and big-hair portraits, then copy a prompt in one click and paste it into your favorite image generator.</p>
  <ul class="toc">
    <li><a href="/#gallery">Prompt gallery</a></li>
    <li><a href="/#how-to">How to use a prompt</a></li>
    <li><a href="/#era-look">What makes it look 1980s</a></li>
    <li><a href="/#faq">FAQ</a></li>
    <li><a href="/prompts.html">All prompts as text</a></li>
    <li><a href="/{HUB}/">Prompts for your own photo</a></li>
  </ul>
</div>

<div class="wrap" id="gallery">
  <div class="gal-head"><h2>Browse 1980s photo prompts</h2><span class="count">{len(items)} prompts</span></div>
  {chips()}
  {grid(items, search=True)}
</div>

<article class="guide">
  <section id="how-to">
    <h2>How to use a 1980s photo prompt</h2>
    <p><strong>Start from the closest picture.</strong> Scroll the gallery until you find an image with the mood you want, whether that is a flash-lit house party, a neon car park or a soft studio portrait. Open it to see the full prompt, the model that made it and tips for changing it.</p>
    <p><strong>Copy, then change only the subject.</strong> Swap the person, outfit or location for your own idea but leave the camera, film and lighting words alone. Those details are what make the result read as a real snapshot from the decade instead of a modern photo with a filter.</p>
    <p><strong>Run it a few times.</strong> Image models are random, so generate three or four versions and keep the one with the most convincing grain and color. If faces look too clean, add a phrase such as “slight motion blur” or “visible film grain” to push the image further back in time.</p>
  </section>

  <section id="era-look">
    <h2>What makes a photo prompt look like the 1980s</h2>
    <p>A convincing 1980s photo prompt usually names the capture method first: 35mm film, a disposable camera, a Polaroid instant print or a camcorder still. Adding the film stock, such as Kodak Gold or Fujicolor, gives the model a clear color reference for warm skin tones and slightly faded shadows.</p>
    <p>Light does most of the work. Direct on-camera flash, hard red-eye shadows, mall fluorescent tubes and pink or cyan neon are all instantly recognisable. Pair them with period details like big teased hair, shoulder pads, denim jackets, arcade cabinets and boxy cars, and the scene places itself without you having to write the year at all.</p>
    <p>Just as important is what you leave out. Words like “ultra sharp”, “8K” or “HDR” pull the image back toward a modern phone camera, so skip them. Ask instead for soft focus at the edges, a little color shift in the highlights and the slightly crooked framing of someone snapping a picture at a party.</p>
  </section>

  <section id="faq">
    <h2>1980s photo prompt FAQ</h2>
{faq_html}
    <p class="credit">Example images and prompts were collected from public posts on <a href="https://openart.ai/discovery" rel="nofollow noopener" target="_blank">OpenArt</a>, and credit belongs to the original creators. Want to read every prompt as plain text, sorted by popularity? Open the <a href="/prompts.html">full prompt list</a>.</p>
  </section>
</article>
</main>
""" + FOOT)

# ---------------------------------------------------------------- category pages
for key, cat in CATEGORIES.items():
    its = by_cat[key]
    path = f"/{key}/"
    trail = [("Home", "/")]
    if cat["group"] == "edit" and key != HUB:
        trail.append((CATEGORIES[HUB]["name"], f"/{HUB}/"))
    bc_html, bc_ld = crumbs(trail + [(cat["name"], path)])
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "@id": BASE + key + "/#page", "url": BASE + key + "/",
         "name": cat["title"], "description": cat["description"]},
        {"@type": "ItemList", "name": cat["h1"], "numberOfItems": len(its),
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": BASE + it["url"].lstrip("/"),
                              "name": it["name"]} for i, it in enumerate(its)]},
        bc_ld]}
    featured = "".join(f'<li><a href="{f["url"]}"><strong>{esc(f["name"])}</strong></a> – {esc(first_sentences(f["intro"]))}</li>'
                       for f in its[:8])
    others = "".join(f'<li><a href="/{k}/">{esc(v["h1"])}</a> ({len(by_cat[k])})</li>'
                     for k, v in CATEGORIES.items() if k != key and v["group"] == cat["group"])
    others += "".join(f'<li><a href="/{k}/">{esc(v["h1"])}</a> ({len(by_cat[k])})</li>'
                      for k, v in CATEGORIES.items() if k != key and v["group"] != cat["group"])
    write(path, head(cat["title"], cat["description"], path, its[0]["img"], ld) + f"""
<main>
<div class="wrap intro">
  {bc_html}
  <h1>{esc(cat["h1"])}</h1>
  {''.join(f'<p>{esc(p)}</p>' for p in cat["intro"])}
</div>
<div class="wrap" id="gallery">
  <div class="gal-head"><h2>Browse {len(its)} {esc(low(cat["h1"]))}</h2></div>
  {chips(key, cat["group"])}
  {grid(its, first_alt=f"{cat['h1']} example: {its[0]['name']}" + (" (example image coming soon)" if its[0].get("placeholder") else ""))}
</div>
<article class="guide">
  <section>
    <h2>Featured {esc(low(cat["h1"].split(" ", 1)[1]))}</h2>
    <ul class="featured">{featured}</ul>
  </section>
  <section>
    <h2>{esc(cat["guide_h2"])}</h2>
    {''.join(f'<p>{esc(p)}</p>' for p in cat["guide"])}
    <p class="credit">Background reading: <a href="{cat["source"][1]}" rel="noopener" target="_blank">{esc(cat["source"][0])} on Wikipedia</a>.</p>
  </section>
  <section>
  <h2>More 1980s prompt collections</h2>
  <ul class="links">{others}<li><a href="/">Full 1980s photo prompt gallery</a> ({len(items)})</li></ul>
  </section>
</article>
</main>
""" + FOOT)


# ---------------------------------------------------------------- detail pages
def related(it, n=7):
    def score(o):
        return (o["primary"] == it["primary"]) * 3 + len(set(o["cats"]) & set(it["cats"]))
    pool = [o for o in all_items if o is not it and o["group"] == it["group"]]
    pool.sort(key=lambda o: (-score(o), all_items.index(o)))
    return pool[:n]


for it in all_items:
    cat = CATEGORIES[it["primary"]]
    edit = it["group"] == "edit"
    trail = [("Home", "/")]
    if edit and it["primary"] != HUB:
        trail.append((CATEGORIES[HUB]["name"], f"/{HUB}/"))
    bc_html, bc_ld = crumbs(trail + [(cat["name"], f"/{it['primary']}/"), (it["name"], it["url"])])
    h1 = it["kw_title"]
    page_url = BASE + it["url"].lstrip("/")
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": page_url + "#page", "url": page_url, "name": it["title"],
         "description": it["description"], "primaryImageOfPage": {"@id": page_url + "#image"},
         "isPartOf": {"@id": BASE + "#website"}},
        {"@type": "ImageObject", "@id": page_url + "#image", "contentUrl": BASE + it["img"].lstrip("/"),
         "width": it["w"], "height": it["h"], "caption": it["name"],
         **({"creator": {"@type": "Person", "name": it["author"]}} if it["author"] else {})},
        bc_ld]}
    if edit:
        steps = [
            "Tap <strong>Copy prompt</strong> above to copy the full text.",
            f"Open {esc(it['tool'])} and start a new chat. Upload a clear, well-lit photo where your face is fully visible"
            " (no sunglasses or heavy filters); for couple or family prompts, upload a photo with everyone in it.",
            "Paste the prompt and send it. " + esc(it["personalize"]),
            "If the face changes, reply “keep my face exactly as in the uploaded photo” and regenerate. "
            "Try two or three versions and keep the one that looks most like a real old print.",
        ]
    else:
      steps = [
        "Tap <strong>Copy prompt</strong> above to copy the full text.",
        f"Open {esc(it['tool'])}, or any image generator you prefer, and paste the prompt into a new chat or prompt box.",
        esc(it["personalize"]),
        "Generate three or four versions and keep the one with the most convincing grain, color and light. "
        "Use the tips below if the result looks too modern.",
      ]
    cat_links = " ".join(f'<a class="tag" href="/{k}/">{esc(CATEGORIES[k]["name"])}</a>' for k in it["cats"])
    rel = related(it)
    credit = (f'Example image by {esc(it["author"])}, shared publicly on '
              if it["author"] else "Example image shared publicly on ")
    write(it["url"], head(it["title"], it["description"], it["url"], it["img"], ld, extra="article") + f"""
<main class="detail">
<div class="wrap">
  {bc_html}
  <div class="d-grid">
    <figure class="d-img"><img src="{it["img"]}" width="{it["w"]}" height="{it["h"]}" alt="{esc(it["name"])}{" – preview for this " + esc(it["keyword"]) + ", example image coming soon" if edit else ", made with this " + esc(it["keyword"])}" fetchpriority="high"></figure>
    <div class="d-main">
      <h1>{esc(h1)}</h1>
      <p class="sub">{esc(it["name"])} · {("the full " + esc(it["keyword"]) + ". Upload a photo of yourself to " + esc(it["tool"]) + ", paste this prompt and get your 80s version.") if edit else ("the full " + esc(it["keyword"]) + ", ready to paste into " + esc(it["tool"]) + " or any other image generator you use.")}</p>
      <p class="lead">{esc(it["intro"])}</p>
      <div class="d-actions"><button class="btn main" type="button" data-copy="prompt-text">Copy prompt</button><span class="best">Best with: <strong>{esc(it["tool"])}</strong></span></div>
      <h2 class="lbl">Prompt</h2>
      <div class="pbox"><button class="pcopy" type="button" data-copy="prompt-text" aria-label="Copy prompt">{COPY_ICON}<span>Copy</span></button><pre class="ptext" id="prompt-text">{esc(it["prompt"])}</pre></div>
      {f'<h2 class="lbl">Negative prompt</h2><div class="pbox"><button class="pcopy" type="button" data-copy="neg-text" aria-label="Copy negative prompt">{COPY_ICON}<span>Copy</span></button><pre class="ptext neg" id="neg-text">{esc(it["neg"])}</pre></div>' if it["neg"] else ''}
      <div class="tags">{cat_links}</div>
    </div>
  </div>
</div>

<article class="guide">
  <section>
    <h2>What this prompt creates</h2>
    <p>{esc(it["creates"])}</p>
  </section>
  <section>
    <h2>How to use this {esc(it["keyword"])}</h2>
    <ol class="steps">{''.join(f'<li>{s}</li>' for s in steps)}</ol>
  </section>
  <section>
    <h2>Tips for this prompt</h2>
    <ul class="tips">{''.join(f'<li>{esc(t)}</li>' for t in it["tips"])}</ul>
  </section>
  <section>
    <h2>Who this prompt suits</h2>
    <p>{esc(it["suits"])}</p>
  </section>
  <section>
    <h2>What makes this prompt work</h2>
    <p>{esc(it["works"])}</p>
    {"" if edit else f'<p class="credit">{credit}<a href="{esc(it["post_url"])}" rel="nofollow noopener" target="_blank">OpenArt</a>. The prompt is shown as originally posted.</p>'}
  </section>
</article>

<section class="wrap more">
  <h2>More prompts like this</h2>
  {grid(rel, max_cols=4)}
  <p class="more-links"><a href="/{it["primary"]}/">Browse all {len(by_cat[it["primary"]])} {esc(low(cat["h1"]))}</a> · {f'<a href="/{HUB}/">All ChatGPT 1980s photo prompts</a>' if edit else '<a href="/">Back to the 1980s photo prompt gallery</a>'}</p>
</section>
</main>
""" + FOOT)

# ---------------------------------------------------------------- 404, sitemap, robots
write("/404.html", head("Page not found – Vintage Photo Prompt", "This page does not exist.", "/404.html",
                        items[0]["img"], noindex=True) + f"""
<main class="wrap intro"><h1>Page not found</h1><p>That prompt may have moved. Try the <a href="/">1980s photo prompt gallery</a> or one of the categories below.</p>{chips()}</main>
""" + FOOT)

urls = [("/", [it["img"] for it in items])] + [(f"/{k}/", []) for k in CATEGORIES] + \
       [(it["url"], [] if it.get("placeholder") else [it["img"]]) for it in all_items] + [("/prompts.html", [])]
for it in edits:
    write(it["img"], placeholder_svg(it))
sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
for path, imgs in urls:
    sitemap.append(f"  <url>\n    <loc>{BASE}{path.lstrip('/')}</loc>\n    <lastmod>{TODAY}</lastmod>" +
                   "".join(f"\n    <image:image><image:loc>{BASE}{i.lstrip('/')}</image:loc></image:image>" for i in imgs) +
                   "\n  </url>")
sitemap.append("</urlset>\n")
write("/sitemap.xml", "\n".join(sitemap))
write("/robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n")

# ---------------------------------------------------------------- assets
(OUT / "assets").mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / "assets" / "site.css", OUT / "assets" / "site.css")
shutil.copy(ROOT / "assets" / "site.js", OUT / "assets" / "site.js")
print(f"built {len(all_items)} prompt pages ({len(edits)} photo-edit), {len(CATEGORIES)} category pages, homepage, sitemap ({len(urls)} urls)")
