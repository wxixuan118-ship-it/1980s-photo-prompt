"""Build index.html (self-contained gallery) from data/prompts.json."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
rows = json.loads((ROOT / "data" / "prompts.json").read_text())
keep = ["rank", "source", "heat", "likes", "bookmarks", "prompt", "negative_prompt", "model",
        "author", "post_url", "local_image", "thumb_url", "width", "height"]
data = json.dumps([{k: r.get(k) for k in keep} for r in rows], ensure_ascii=False)
data = data.replace("</", "<\\/")

HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>1980s Photo Prompts</title>
<style>
:root{--bg:#f6f3ee;--card:#fff;--ink:#1d1b18;--muted:#6f6a62;--line:#e4ded4;--accent:#b4462b;--chip:#efe9df}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15130f;--card:#1f1c17;--ink:#eee8dd;--muted:#a39b8e;--line:#353027;--accent:#e0714f;--chip:#2a261f}}
:root[data-theme=dark]{--bg:#15130f;--card:#1f1c17;--ink:#eee8dd;--muted:#a39b8e;--line:#353027;--accent:#e0714f;--chip:#2a261f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",sans-serif}
header{max-width:1280px;margin:0 auto;padding:28px 16px 8px}
h1{margin:0 0 4px;font-size:26px;letter-spacing:-.01em}
.sub{color:var(--muted);margin:0 0 16px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.bar input,.bar select{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
.bar input{flex:1;min-width:200px}
.count{color:var(--muted);font-size:13px}
main{max-width:1280px;margin:0 auto;padding:12px 16px 48px;columns:300px;column-gap:16px}
.card{break-inside:avoid;margin:0 0 16px;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.card img{display:block;width:100%;height:auto;background:var(--chip);cursor:zoom-in}
.body{padding:10px 12px 12px}
.meta{display:flex;gap:6px;flex-wrap:wrap;align-items:center;font-size:12px;color:var(--muted);margin-bottom:6px}
.chip{background:var(--chip);border-radius:999px;padding:1px 8px}
.heat{color:var(--accent);font-weight:600}
.prompt{font-size:13.5px;white-space:pre-wrap;word-break:break-word;max-height:7.5em;overflow:hidden;position:relative}
.card.open .prompt{max-height:none}
.actions{display:flex;gap:8px;margin-top:8px;font-size:13px}
.actions button,.actions a{font:inherit;background:none;border:1px solid var(--line);border-radius:6px;padding:3px 9px;color:var(--ink);cursor:pointer;text-decoration:none}
.actions button:hover,.actions a:hover{border-color:var(--accent)}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:9;cursor:zoom-out}
#lb img{max-width:94vw;max-height:94vh}
</style>
</head>
<body>
<header>
  <h1>1980s Photo Prompts</h1>
  <p class="sub">Prompts + result images from OpenArt / Civitai, ranked by engagement (likes + 2×bookmarks + shares + comments).</p>
  <div class="bar">
    <input id="q" type="search" placeholder="Filter prompts (e.g. polaroid, flash, tokyo)">
    <select id="sort"><option value="heat">Sort: heat</option><option value="likes">Sort: likes</option><option value="rank">Sort: rank</option></select>
    <select id="src"><option value="">All sources</option><option>openart</option><option>civitai</option></select>
    <span class="count" id="count"></span>
  </div>
</header>
<main id="grid"></main>
<div id="lb"><img alt=""></div>
<script>
const DATA = __DATA__;
const grid = document.getElementById('grid'), q = document.getElementById('q'),
      sortSel = document.getElementById('sort'), src = document.getElementById('src'),
      count = document.getElementById('count'), lb = document.getElementById('lb');
const esc = s => (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function render(){
  const term = q.value.trim().toLowerCase(), s = sortSel.value;
  let rows = DATA.filter(r => (!src.value || r.source===src.value) && (!term || r.prompt.toLowerCase().includes(term)));
  rows.sort((a,b) => s==='rank' ? a.rank-b.rank : (b[s]-a[s]) || a.rank-b.rank);
  count.textContent = rows.length + ' / ' + DATA.length;
  grid.innerHTML = rows.map(r => `
    <article class="card">
      <img loading="lazy" src="${esc(r.local_image||r.thumb_url)}" data-full="${esc(r.local_image||r.thumb_url)}"
           ${r.width&&r.height?`width="${r.width}" height="${r.height}"`:''} alt="">
      <div class="body">
        <div class="meta"><span class="heat">🔥 ${r.heat}</span><span>♥ ${r.likes}</span>${r.bookmarks?`<span>★ ${r.bookmarks}</span>`:''}
          <span class="chip">${esc(r.source)}</span>${r.model?`<span class="chip">${esc(r.model)}</span>`:''}<span>#${r.rank}</span></div>
        <div class="prompt">${esc(r.prompt)}</div>
        <div class="actions"><button data-copy>Copy prompt</button><button data-more>Expand</button>
          <a href="${esc(r.post_url)}" target="_blank" rel="noopener">Source ↗</a></div>
      </div>
    </article>`).join('');
  grid.querySelectorAll('.card').forEach((el,i) => el._row = rows[i]);
}
grid.addEventListener('click', e => {
  const card = e.target.closest('.card'); if(!card) return;
  if(e.target.matches('[data-copy]')){ navigator.clipboard.writeText(card._row.prompt); e.target.textContent='Copied'; setTimeout(()=>e.target.textContent='Copy prompt',1200); }
  else if(e.target.matches('[data-more]')){ card.classList.toggle('open'); e.target.textContent = card.classList.contains('open')?'Collapse':'Expand'; }
  else if(e.target.tagName==='IMG'){ lb.firstElementChild.src = e.target.dataset.full; lb.style.display='flex'; }
});
lb.onclick = () => lb.style.display='none';
[q,sortSel,src].forEach(el => el.addEventListener('input', render));
render();
</script>
</body>
</html>
"""
(ROOT / "public" / "prompts.html").write_text(HTML.replace("__DATA__", data), encoding="utf-8")
print(f"wrote public/prompts.html with {len(rows)} entries")
