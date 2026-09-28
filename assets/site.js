(() => {
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const PROMPTS = window.PROMPTS || {};

  function toast(msg) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg; t.classList.add('show');
    clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('show'), 1400);
  }
  function copy(text) {
    (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject())
      .then(() => toast('Prompt copied'), () => toast('Copy failed — select the text manually'));
  }

  // Copy buttons on detail pages: <button data-copy="element-id">
  $$('button[data-copy]').forEach(b => b.addEventListener('click', () => {
    const el = document.getElementById(b.dataset.copy);
    if (!el) return;
    copy(el.textContent);
    const label = b.querySelector('span');
    if (label) {
      label.textContent = 'Copied';
      b.classList.add('done');
      clearTimeout(b._t);
      b._t = setTimeout(() => { label.textContent = 'Copy'; b.classList.remove('done'); }, 1500);
    }
  }));

  // Masonry grids: distribute cards into row-ordered columns by image aspect ratio.
  $$('.grid').forEach(grid => {
    const cards = $$('.pin', grid);
    const max = +grid.dataset.max || 5;
    const colCount = () => Math.max(2, Math.min(max, Math.floor((grid.clientWidth + 16) / 246)));
    let n = 0;

    cards.forEach(el => {
      const p = PROMPTS[el.dataset.slug];
      if (!p) return;
      const b = document.createElement('span');
      b.className = 'copy'; b.setAttribute('role', 'button'); b.tabIndex = 0; b.textContent = 'Copy prompt';
      const go = e => { e.preventDefault(); e.stopPropagation(); copy(p.p); };
      b.addEventListener('click', go);
      b.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') go(e); });
      el.querySelector('.over').appendChild(b);
    });

    function layout() {
      const shown = cards.filter(c => !c.hidden);
      n = colCount();
      const cols = Array.from({ length: n }, () => {
        const c = document.createElement('div'); c.className = 'col'; c._h = 0; return c;
      });
      shown.forEach(el => {
        const img = el.querySelector('img');
        const col = cols.reduce((a, b) => (b._h < a._h ? b : a));
        col._h += (+img.getAttribute('height') || 1) / (+img.getAttribute('width') || 1);
        col.appendChild(el);
      });
      grid.classList.add('js');
      grid.replaceChildren(...cols);
      if (!shown.length) grid.innerHTML = '<p class="empty">No prompts match. Try another keyword.</p>';
    }
    grid._layout = layout;
    layout();
    addEventListener('resize', () => { if (colCount() !== n) layout(); });

    // Live search (homepage only)
    if (grid.hasAttribute('data-search')) {
      const q = document.getElementById('q');
      const count = document.querySelector('.gal-head .count');
      const run = () => {
        const term = q.value.trim().toLowerCase();
        let k = 0;
        cards.forEach(el => {
          const p = PROMPTS[el.dataset.slug] || { p: '', n: '' };
          el.hidden = !!term && !(p.p + ' ' + p.n).toLowerCase().includes(term);
          if (!el.hidden) k++;
        });
        if (count) count.textContent = k + ' prompts';
        layout();
      };
      q.form.addEventListener('submit', e => { e.preventDefault(); run(); });
      q.addEventListener('input', () => { run(); if (q.value) document.getElementById('gallery').scrollIntoView({ block: 'start' }); });
      const initial = new URLSearchParams(location.search).get('q');
      if (initial) { q.value = initial; run(); document.getElementById('gallery').scrollIntoView({ block: 'start' }); }
    }
  });
})();
