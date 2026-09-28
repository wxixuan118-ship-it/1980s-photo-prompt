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
ld_json = lambda obj: json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

# ---------------------------------------------------------------- data
rows = {r["id"]: r for r in json.loads((ROOT / "data" / "prompts.json").read_text())}
copy = {}
for f in sorted((ROOT / "data" / "content").glob("*.json")):
    for c in json.loads(f.read_text()):
        if f.name != "keywords.json":
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
by_cat = {k: [it for it in items if k in it["cats"]] for k in CATEGORIES}


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
<link rel="stylesheet" href="/assets/site.css">
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
  <nav aria-label="Main"><a href="/">Home</a><a href="/portrait/">Portrait</a><a href="/fashion/">Fashion</a><a href="/polaroid-film/">Polaroid &amp; Film</a><a href="/neon-city/">Neon &amp; City</a></nav>
</div></header>
"""


FOOT = f"""<footer class="foot">
  <nav aria-label="Categories">{''.join(f'<a href="/{k}/">{esc(v["h1"])}</a>' for k, v in CATEGORIES.items())}<a href="/prompts.html">All prompts as text</a></nav>
  <p>© {YEAR} {SITE} · A free library of vintage and 1980s AI photo prompts. Example images belong to their creators.</p>
</footer>
<div class="toast" id="toast" role="status"></div>
<script src="/assets/site.js" defer></script>
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


def chips(active=""):
    out = [f'<a class="chip{" on" if not active else ""}" href="/">All</a>']
    out += [f'<a class="chip{" on" if k == active else ""}" href="/{k}/">{esc(v["name"])}</a>' for k, v in CATEGORIES.items()]
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
    bc_html, bc_ld = crumbs([("Home", "/"), (cat["name"], path)])
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
                     for k, v in CATEGORIES.items() if k != key)
    write(path, head(cat["title"], cat["description"], path, its[0]["img"], ld) + f"""
<main>
<div class="wrap intro">
  {bc_html}
  <h1>{esc(cat["h1"])}</h1>
  {''.join(f'<p>{esc(p)}</p>' for p in cat["intro"])}
</div>
<div class="wrap" id="gallery">
  <div class="gal-head"><h2>Browse {len(its)} {esc(cat["h1"].lower())}</h2></div>
  {chips(key)}
  {grid(its, first_alt=f"{cat['h1']} example: {its[0]['name']}")}
</div>
<article class="guide">
  <section>
    <h2>Featured {esc(cat["h1"].split(" ", 1)[1].lower())}</h2>
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
    pool = [o for o in items if o is not it]
    pool.sort(key=lambda o: (-score(o), items.index(o)))
    return pool[:n]


for it in items:
    cat = CATEGORIES[it["primary"]]
    bc_html, bc_ld = crumbs([("Home", "/"), (cat["name"], f"/{it['primary']}/"), (it["name"], it["url"])])
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
    <figure class="d-img"><img src="{it["img"]}" width="{it["w"]}" height="{it["h"]}" alt="{esc(it["name"])}, made with this {esc(it["keyword"])}" fetchpriority="high"></figure>
    <div class="d-main">
      <h1>{esc(h1)}</h1>
      <p class="sub">{esc(it["name"])} · the full {esc(it["keyword"])}, ready to paste into {esc(it["tool"])} or any other image generator you use.</p>
      <p class="lead">{esc(it["intro"])}</p>
      <div class="d-actions"><button class="btn main" type="button" data-copy="prompt-text">Copy prompt</button><span class="best">Best with: <strong>{esc(it["tool"])}</strong></span></div>
      <h2 class="lbl">Prompt</h2>
      <pre class="ptext" id="prompt-text">{esc(it["prompt"])}</pre>
      {f'<h2 class="lbl">Negative prompt</h2><pre class="ptext neg">{esc(it["neg"])}</pre>' if it["neg"] else ''}
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
    <p class="credit">{credit}<a href="{esc(it["post_url"])}" rel="nofollow noopener" target="_blank">OpenArt</a>. The prompt is shown as originally posted.</p>
  </section>
</article>

<section class="wrap more">
  <h2>More prompts like this</h2>
  {grid(rel, max_cols=4)}
  <p class="more-links"><a href="/{it["primary"]}/">Browse all {len(by_cat[it["primary"]])} {esc(cat["h1"].lower())}</a> · <a href="/">Back to the 1980s photo prompt gallery</a></p>
</section>
</main>
""" + FOOT)

# ---------------------------------------------------------------- 404, sitemap, robots
write("/404.html", head("Page not found – Vintage Photo Prompt", "This page does not exist.", "/404.html",
                        items[0]["img"], noindex=True) + f"""
<main class="wrap intro"><h1>Page not found</h1><p>That prompt may have moved. Try the <a href="/">1980s photo prompt gallery</a> or one of the categories below.</p>{chips()}</main>
""" + FOOT)

urls = [("/", [it["img"] for it in items])] + [(f"/{k}/", []) for k in CATEGORIES] + \
       [(it["url"], [it["img"]]) for it in items] + [("/prompts.html", [])]
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
print(f"built {len(items)} prompt pages, {len(CATEGORIES)} category pages, homepage, sitemap ({len(urls)} urls)")
