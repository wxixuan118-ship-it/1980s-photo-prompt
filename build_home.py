"""Build index.html — the vintagephotoprompt.com homepage — from data/prompts.json.

Target keyword: "1980s photo prompt". The gallery is rendered into the HTML so crawlers
see every image; JavaScript only re-flows it into columns, filters it and opens the modal.
"""
import datetime
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "vintagephotoprompt.com"
BASE = f"https://{SITE}/"
rows = json.loads((ROOT / "data" / "prompts.json").read_text())

# Keyword-based categories shown as filter chips.
CATEGORIES = {
    "Portrait": r"portrait|woman|man\b|girl|boy|face|close-up",
    "Fashion": r"fashion|outfit|hair|dress|jacket|makeup|style",
    "Film & Polaroid": r"polaroid|film|kodak|35mm|grain|analog|vhs|flash",
    "Neon & City": r"neon|city|street|night|arcade|synth",
    "Cinematic": r"cinematic|movie|scene|dramatic",
    "Illustration": r"illustration|comic|cartoon|drawing|3d|lego|anime|mural|poster",
}

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


def alt_text(prompt, limit=110):
    """Short, human alt text from the start of a prompt."""
    t = re.sub(r"@\w+", "", prompt)
    t = re.sub(r"^\s*prompt\s*[‘'\"“][^’'\"”]*[’'\"”]\s*:\s*", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" .,:;")
    t = re.split(r"(?<=[a-z0-9)])[.!?](?:\s|$)", t)[0]
    if len(t) > limit:
        t = t[:limit].rsplit(" ", 1)[0]
    return t


items = []
for r in sorted(rows, key=lambda r: (-r["heat"], r["rank"])):
    text = r["prompt"].lower()
    items.append({
        "id": r["id"], "img": r["local_image"], "w": r["width"], "h": r["height"],
        "prompt": r["prompt"].strip(), "neg": r.get("negative_prompt") or "",
        "model": r.get("model") or "", "author": r.get("author") or "",
        "url": r["post_url"], "cats": [c for c, pat in CATEGORIES.items() if re.search(pat, text)],
        "alt": alt_text(r["prompt"]),
    })
items[0]["alt"] = "1980s photo prompt example: " + items[0]["alt"]

esc = lambda s: html.escape(s, quote=True)
cards = "\n".join(
    f'<button class="pin" data-i="{i}" type="button">'
    f'<img src="{esc(d["img"])}" width="{d["w"]}" height="{d["h"]}" loading="{"eager" if i < 6 else "lazy"}"'
    f' decoding="async" alt="{esc(d["alt"])}">'
    f'<span class="badge{"" if i < 10 else " p"}"><i></i>{"Pinned" if i < 10 else "Prompt"}</span></button>'
    for i, d in enumerate(items))
chips = "".join(f'<button class="chip" type="button" data-cat="{c}">{esc(c)}</button>' for c in CATEGORIES)
faq_html = "\n".join(f'<h3>{esc(q)}</h3>\n<p>{esc(a)}</p>' for q, a in FAQ)

TITLE = "1980s Photo Prompt Gallery – Copy Retro AI Prompts"
DESC = ("Browse 67 AI images and copy the exact 1980s photo prompt behind each one: film grain, "
        "Polaroid flash, neon nights, big hair and retro portraits.")

schema = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "WebSite", "@id": BASE + "#website", "url": BASE, "name": "Vintage Photo Prompt"},
        {"@type": "CollectionPage", "@id": BASE + "#page", "url": BASE, "name": TITLE,
         "description": DESC, "isPartOf": {"@id": BASE + "#website"},
         "mainEntity": {"@id": BASE + "#gallery"}},
        {"@type": "ItemList", "@id": BASE + "#gallery", "name": "1980s photo prompt examples",
         "numberOfItems": len(items),
         "itemListElement": [
             {"@type": "ListItem", "position": i + 1,
              "item": {"@type": "ImageObject", "contentUrl": BASE + d["img"], "caption": d["alt"],
                       "width": d["w"], "height": d["h"],
                       **({"creator": {"@type": "Person", "name": d["author"]}} if d["author"] else {})}}
             for i, d in enumerate(items)]},
        {"@type": "FAQPage", "@id": BASE + "#faq",
         "mainEntity": [{"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ],
}

data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
ld = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<link rel="canonical" href="__BASE__">
<meta property="og:site_name" content="Vintage Photo Prompt">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:url" content="__BASE__">
<meta property="og:type" content="website">
<meta property="og:image" content="__BASE____OGIMG__">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<script type="application/ld+json">__LD__</script>
<style>
:root{--bg:#14151d;--bar:#191a24;--card:#1f2130;--ink:#f1ede4;--muted:#a19e96;--line:#2b2d3d;--accent:#e8a24a;--accent-ink:#1b1408;--badge:rgba(20,21,29,.72)}
*{box-sizing:border-box}
html{color-scheme:dark;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 Inter,-apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;-webkit-font-smoothing:antialiased}
a{color:inherit}
button{font:inherit;color:inherit;cursor:pointer}

/* header */
.top{position:sticky;top:0;z-index:5;background:var(--bar);border-bottom:1px solid var(--line)}
.top-in{max-width:1320px;margin:0 auto;height:64px;padding:0 16px;display:flex;align-items:center;gap:24px}
.logo{display:flex;align-items:center;gap:10px;flex-shrink:0;text-decoration:none}
.mark{width:36px;height:36px;border-radius:9px;background:linear-gradient(135deg,#e8a24a,#c4492f);display:grid;place-items:center}
.mark svg{width:20px;height:20px}
.word{font-family:Fraunces,Georgia,serif;font-size:20px;color:var(--accent);letter-spacing:-.01em}
.word span{color:var(--ink)}
.search{flex:1;max-width:420px;position:relative}
.search input{width:100%;height:38px;border-radius:999px;border:1px solid var(--line);background:var(--bg);color:var(--ink);padding:0 14px 0 36px;font:inherit;font-size:14px}
.search input:focus{outline:none;border-color:var(--accent)}
.search svg{position:absolute;left:12px;top:11px;width:16px;height:16px;color:var(--muted)}
.top nav{margin-left:auto;display:flex;gap:22px;font-size:15px}
.top nav a{color:#d8d4cb;text-decoration:none}
.top nav a:hover{color:var(--accent)}

/* intro + filters */
.wrap{max-width:1320px;margin:0 auto;padding:0 16px}
.intro{padding-top:28px}
.intro h1{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:clamp(26px,3.4vw,38px);line-height:1.15;margin:0 0 8px;letter-spacing:-.01em}
.intro p{margin:0;color:var(--muted);max-width:720px}
.toc{display:flex;flex-wrap:wrap;gap:6px 18px;margin:12px 0 0;padding:0;list-style:none;font-size:14px}
.toc a{color:var(--accent);text-decoration:none}
.toc a:hover{text-decoration:underline}
.gal-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:26px 0 0}
.gal-head h2{margin:0;font-size:18px;font-weight:600}
.gal-head span{color:var(--muted);font-size:13px}
.chips{padding:12px 0 16px;display:flex;gap:8px;overflow-x:auto;scrollbar-width:none}
.chip{flex-shrink:0;border:1px solid var(--line);background:var(--card);border-radius:999px;padding:6px 14px;font-size:13.5px;color:#d8d4cb}
.chip:hover{border-color:var(--accent)}
.chip.on{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600}

/* masonry grid: CSS columns without JS, row-ordered columns with JS */
.grid{columns:5 230px;column-gap:16px}
.grid.js{columns:auto;display:flex;gap:16px;align-items:flex-start}
.col{flex:1;min-width:0}
.pin{break-inside:avoid;margin:0 0 16px;position:relative;border-radius:14px;overflow:hidden;background:var(--card);cursor:zoom-in;display:block;width:100%;border:0;padding:0;text-align:left}
.pin[hidden]{display:none}
.pin img{display:block;width:100%;height:auto;transition:transform .35s ease}
.pin:hover img{transform:scale(1.03)}
.badge{position:absolute;top:10px;left:10px;display:flex;align-items:center;gap:5px;background:var(--badge);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);color:#fff;font-size:12.5px;font-weight:500;padding:3px 10px;border-radius:999px}
.badge i{width:7px;height:7px;border-radius:50%;background:#ef5b4c}
.badge.p i{background:var(--accent)}
.over{position:absolute;inset:auto 0 0 0;padding:40px 12px 12px;background:linear-gradient(transparent,rgba(10,10,14,.9));opacity:0;transition:opacity .2s}
.pin:hover .over,.pin:focus-visible .over{opacity:1}
.over span{display:-webkit-box;margin:0 0 8px;font-size:12.5px;line-height:1.4;color:#eee;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.copy{display:inline-flex;align-items:center;background:var(--accent);color:var(--accent-ink);border-radius:999px;padding:5px 12px;font-size:12.5px;font-weight:600}
.empty{text-align:center;color:var(--muted);padding:60px 16px}

/* guide copy */
.guide{max-width:760px;margin:40px auto 0;padding:0 16px 56px}
.guide section{border-top:1px solid var(--line);padding-top:28px;margin-top:28px}
.guide h2{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:26px;line-height:1.2;margin:0 0 12px}
.guide h3{font-size:17px;margin:22px 0 6px}
.guide p{margin:0 0 12px;color:#d6d2c9;line-height:1.65}
.guide strong{color:var(--ink)}
.guide a{color:var(--accent)}
.credit{font-size:13.5px}

/* modal */
.modal{position:fixed;inset:0;background:rgba(6,6,10,.8);z-index:10;display:none;align-items:center;justify-content:center;padding:16px}
.modal.open{display:flex}
.sheet{background:var(--card);border:1px solid var(--line);border-radius:18px;max-width:1000px;width:100%;max-height:92vh;display:grid;grid-template-columns:1.1fr 1fr;overflow:hidden}
.sheet .ph{background:#0d0d12;display:grid;place-items:center;min-height:0}
.sheet .ph img{max-width:100%;max-height:92vh;display:block}
.info{padding:22px;overflow:auto;display:flex;flex-direction:column;gap:14px}
.lbl{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:600}
.ptext{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px 14px;font-size:14px;line-height:1.55;white-space:pre-wrap;word-break:break-word}
.meta{display:flex;flex-wrap:wrap;gap:8px;font-size:13px;color:var(--muted)}
.meta span{background:var(--bg);border:1px solid var(--line);border-radius:999px;padding:2px 10px}
.row{display:flex;gap:10px;flex-wrap:wrap}
.btn{border:1px solid var(--line);background:transparent;border-radius:999px;padding:8px 16px;font-size:14px;text-decoration:none}
.btn.main{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600}
.x{position:absolute;top:14px;right:16px;width:38px;height:38px;border-radius:50%;background:var(--card);border:1px solid var(--line);font-size:20px;line-height:1}

footer{border-top:1px solid var(--line);color:var(--muted);font-size:13px;text-align:center;padding:24px 16px}
.toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(20px);background:var(--ink);color:var(--bg);padding:8px 16px;border-radius:999px;font-size:14px;opacity:0;transition:.2s;pointer-events:none;z-index:20}
.toast.show{opacity:1;transform:translateX(-50%)}

@media (max-width:860px){.top nav{display:none}.sheet{grid-template-columns:1fr;overflow:auto}.sheet .ph img{max-height:50vh}}
@media (max-width:560px){.word{font-size:17px}.word span{display:none}.grid{columns:2;column-gap:10px}.grid.js{gap:10px}.pin{margin-bottom:10px}.top-in{gap:12px}.guide h2{font-size:22px}}
</style>
</head>
<body>
<header class="top"><div class="top-in">
  <a class="logo" href="/" aria-label="Vintage Photo Prompt home">
    <span class="mark"><svg viewBox="0 0 24 24" fill="none" stroke="#1b1408" stroke-width="2" aria-hidden="true"><rect x="3" y="6" width="18" height="14" rx="2"/><circle cx="12" cy="13" r="3.5"/><path d="M8 6l1.5-2h5L16 6"/></svg></span>
    <span class="word">vintage<span>photoprompt</span></span>
  </a>
  <label class="search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
    <input id="q" type="search" placeholder="Search prompts: polaroid, neon, portrait…" aria-label="Search prompts"></label>
  <nav aria-label="Main"><a href="/">Home</a><a href="/#gallery">Gallery</a><a href="/#how-to">How to use</a><a href="/#faq">FAQ</a><a href="/prompts.html">All prompts</a></nav>
</div></header>

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
  <div class="gal-head"><h2>Browse 1980s photo prompts</h2><span id="count">__N__ prompts</span></div>
  <div class="chips" id="chips"><button class="chip on" type="button" data-cat="">All</button>__CHIPS__</div>
  <div class="grid" id="grid">
__CARDS__
  </div>
</div>

<article class="guide">
  <section id="how-to">
    <h2>How to use a 1980s photo prompt</h2>
    <p><strong>Start from the closest picture.</strong> Scroll the gallery until you find an image with the mood you want, whether that is a flash-lit house party, a neon car park or a soft studio portrait. Tap it to see the full prompt, the model that made it and a link to the original post.</p>
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
__FAQ__
    <p class="credit">Example images and prompts were collected from public posts on <a href="https://openart.ai/discovery" rel="nofollow noopener" target="_blank">OpenArt</a>, and credit belongs to the original creators. Want to read every prompt as plain text, sorted by popularity? Open the <a href="/prompts.html">full prompt list</a>.</p>
  </section>
</article>
</main>

<div class="modal" id="modal" role="dialog" aria-modal="true" aria-label="Prompt details">
  <button class="x" id="x" type="button" aria-label="Close">×</button>
  <div class="sheet">
    <div class="ph"><img id="m-img" alt=""></div>
    <div class="info">
      <div class="lbl">Prompt</div>
      <div class="ptext" id="m-prompt"></div>
      <div id="m-neg-wrap"><div class="lbl" style="margin-bottom:8px">Negative prompt</div><div class="ptext" id="m-neg"></div></div>
      <div class="meta" id="m-meta"></div>
      <div class="row"><button class="btn main" id="m-copy" type="button">Copy prompt</button><a class="btn" id="m-src" target="_blank" rel="nofollow noopener">View source ↗</a></div>
    </div>
  </div>
</div>

<footer id="about">© __YEAR__ __SITE__ · A free library of vintage and 1980s AI photo prompts.</footer>
<div class="toast" id="toast" role="status">Prompt copied</div>

<script>
const DATA = __DATA__;
const $ = id => document.getElementById(id);
const grid = $('grid'), q = $('q'), modal = $('modal');
const cards = [...grid.querySelectorAll('.pin')];
let cat = '', ncols = 0;

// hover overlay with a prompt preview
cards.forEach(el => {
  const over = document.createElement('span');
  over.className = 'over';
  over.innerHTML = '<span></span><span class="copy" data-copy>Copy prompt</span>';
  over.firstChild.textContent = DATA[el.dataset.i].prompt;
  el.appendChild(over);
});

const colCount = () => Math.max(2, Math.min(5, Math.floor((grid.clientWidth + 16) / 246)));
function render(){
  const term = q.value.trim().toLowerCase();
  const shown = cards.filter(el => {
    const d = DATA[el.dataset.i];
    const ok = (!cat || d.cats.includes(cat)) && (!term || d.prompt.toLowerCase().includes(term));
    el.hidden = !ok; return ok;
  });
  $('count').textContent = shown.length + ' prompts';
  ncols = colCount();
  const cols = Array.from({length:ncols}, () => { const c = document.createElement('div'); c.className = 'col'; c._h = 0; return c; });
  shown.forEach(el => {
    const d = DATA[el.dataset.i], c = cols.reduce((a,b) => b._h < a._h ? b : a);
    c._h += d.h / d.w; c.appendChild(el);
  });
  grid.classList.add('js');
  grid.replaceChildren(...cols);
  if(!shown.length) grid.innerHTML = '<p class="empty">No prompts match. Try another keyword.</p>';
}

function toast(msg){ const t=$('toast'); t.textContent=msg; t.classList.add('show'); clearTimeout(t._h); t._h=setTimeout(()=>t.classList.remove('show'),1400); }
function copy(text){
  (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject())
    .then(()=>toast('Prompt copied'), ()=>toast('Copy failed — select the text manually'));
}
const esc = s => (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function open(d){
  $('m-img').src = d.img; $('m-img').alt = d.alt;
  $('m-prompt').textContent = d.prompt;
  $('m-neg').textContent = d.neg; $('m-neg-wrap').hidden = !d.neg;
  $('m-meta').innerHTML = [d.model && 'Model: '+esc(d.model), d.author && 'By '+esc(d.author), ...d.cats.map(esc)].filter(Boolean).map(s=>`<span>${s}</span>`).join('');
  $('m-src').href = d.url;
  $('m-copy').onclick = () => copy(d.prompt);
  modal.classList.add('open'); document.body.style.overflow='hidden';
}
function close(){ modal.classList.remove('open'); document.body.style.overflow=''; }

cards.forEach(el => el.addEventListener('click', e => {
  const d = DATA[el.dataset.i];
  if(e.target.closest('[data-copy]')) copy(d.prompt); else open(d);
}));
$('chips').addEventListener('click', e => {
  const b = e.target.closest('.chip'); if(!b) return;
  document.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c===b));
  cat = b.dataset.cat; render();
});
$('x').onclick = close;
modal.addEventListener('click', e => { if(e.target===modal) close(); });
addEventListener('keydown', e => { if(e.key==='Escape') close(); });
addEventListener('resize', () => { if(colCount() !== ncols) render(); });
q.addEventListener('input', () => { render(); if(q.value) $('gallery').scrollIntoView({block:'start'}); });
render();
</script>
</body>
</html>
"""

out = HTML
for k, v in {"__TITLE__": esc(TITLE), "__DESC__": esc(DESC), "__BASE__": BASE, "__OGIMG__": items[0]["img"],
             "__LD__": ld, "__N__": str(len(items)), "__CHIPS__": chips, "__CARDS__": cards,
             "__FAQ__": faq_html, "__YEAR__": str(datetime.date.today().year), "__SITE__": SITE,
             "__DATA__": data}.items():
    out = out.replace(k, v)
(ROOT / "index.html").write_text(out, encoding="utf-8")
print(f"wrote index.html with {len(items)} entries")
