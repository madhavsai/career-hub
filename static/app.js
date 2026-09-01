/* Career Hub - nav, search, and the tracker overlay.
 *
 * Section bodies arrive as pre-built HTML from content.json. The playbook's
 * sections are shells whose grids are filled by renderPlaybook() (lifted
 * verbatim from the source doc), so all sections are put in the DOM once at
 * load and then shown or hidden - never re-rendered. */

const STATUSES = [
  { id: 'interested',  label: 'Interested' },
  { id: 'applied',     label: 'Applied' },
  { id: 'in-progress', label: 'In progress' },
  { id: 'rejected',    label: 'Rejected' },
  { id: 'closed',      label: 'Closed' },
];
const STATUS_LABEL = Object.fromEntries(STATUSES.map(s => [s.id, s.label]));

const el = id => document.getElementById(id);
const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const deent = s => { const d = document.createElement('textarea'); d.innerHTML = s; return d.value; };

const store = {
  content: null,
  sections: [],          // flat list, in nav order
  byId: {},
  text: {},              // section id -> lowercased plain text, for search
  names: {},             // section id -> lowercased headings/entity names only
  items: {},             // tracker state, keyed "sectionId::label"
  current: null,
};

/* ------------------------------------------------------------------ boot */

async function boot() {
  const saved = localStorage.getItem('careerhub-theme');
  if (saved) document.documentElement.dataset.theme = saved;
  else if (matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.dataset.theme = 'dark';

  const [content, state] = await Promise.all([
    fetch('/content.json').then(r => r.json()),
    fetch('/api/state').then(r => r.json()).catch(() => ({ items: {} })),
  ]);
  store.content = content;
  store.items = state.items || {};

  buildSectionList();
  renderNav();
  renderAllSections();

  // The playbook's own renderers need their target divs in the DOM already.
  try { renderPlaybook(); }
  catch (e) { console.error('playbook render failed', e); }

  indexText();
  decorateTrackables();
  renderFooter();
  wireEvents();

  const first = location.hash.slice(1);
  show(store.byId[first] ? first : store.sections[0].id, { push: false });
}

function buildSectionList() {
  store.content.groups.forEach(g => {
    g.sections.forEach(s => {
      s.group = g.title;
      store.sections.push(s);
      store.byId[s.id] = s;
    });
  });
  // A synthetic section: everything the user has marked, in one place.
  const tracker = { id: 'tracker', title: 'My tracker', group: 'Tracker',
                    source: 'Saved locally in career-hub/state.json', html: '', track: null };
  store.sections.push(tracker);
  store.byId.tracker = tracker;
}

/* ------------------------------------------------------------------- nav */

function renderNav() {
  const parts = [];
  let n = 0;
  store.content.groups.forEach(g => {
    parts.push(`<div class="grp">${g.title}</div>`);
    g.sections.forEach(s => {
      n++;
      parts.push(
        `<button data-goto="${s.id}"><span class="n">${String(n).padStart(2, '0')}</span>` +
        `<span class="t">${s.title}</span><span class="tally" data-tally="${s.id}" hidden></span></button>`);
    });
  });
  parts.push('<div class="grp">Tracker</div>');
  parts.push('<button data-goto="tracker"><span class="n">&#9733;</span>' +
             '<span class="t">My tracker</span><span class="tally" data-tally="tracker" hidden></span></button>');
  el('toc').innerHTML = parts.join('');
}

function renderAllSections() {
  el('secBody').innerHTML = store.sections
    .map(s => `<div class="sec" data-sec="${s.id}" hidden>${s.html}</div>`)
    .join('');
}

function renderFooter() {
  const c = store.content;
  el('pageFoot').innerHTML =
    `Built from ${c.sources.map(s => `<code>${esc(s.path)}</code>`).join(', ')}. ` +
    `Compiled ${esc(c.generated)}. ` +
    `Content is copied verbatim &mdash; edit the originals, then re-run <code>build_content.py</code>. ` +
    `${c.exclusions.length} personalised sections were deliberately left out; they are listed in ` +
    `<code>build_content.py</code>.`;
}

function show(id, opts = {}) {
  const sec = store.byId[id];
  if (!sec) return;
  store.current = id;

  document.querySelectorAll('[data-goto]').forEach(b =>
    b.classList.toggle('active', b.dataset.goto === id));

  el('secGroup').textContent = deent(sec.group);
  el('secTitle').innerHTML = sec.title;
  el('secSource').textContent = sec.source;

  if (id === 'tracker') renderTracker();
  document.querySelectorAll('.sec').forEach(d => { d.hidden = d.dataset.sec !== id; });

  renderMiniToc(id);
  updateTally();
  el('secCount').innerHTML = countLine(id);

  if (opts.push !== false) history.replaceState(null, '', '#' + id);
  window.scrollTo({ top: 0, behavior: opts.instant === false ? 'smooth' : 'auto' });
}

function countLine(id) {
  const sec = document.querySelector(`.sec[data-sec="${id}"]`);
  if (!sec || id === 'tracker') return '';
  const rows = [...sec.querySelectorAll('tr')].filter(tr => !tr.querySelector('th')).length;
  const cards = sec.querySelectorAll('.dcard').length;
  const bits = [];
  if (cards) bits.push(cards + ' entries');
  if (rows > 0) bits.push(rows + ' rows');
  const tracked = Object.values(store.items).filter(i => i.section === id).length;
  if (tracked) bits.push(tracked + ' tracked');
  return bits.join(' &middot; ');
}

function renderMiniToc(id) {
  const box = el('minitoc');
  const sec = document.querySelector(`.sec[data-sec="${id}"]`);
  if (!sec) { box.hidden = true; return; }
  // Structural headings only. Cards, tables and job descriptions carry their
  // own <h4>s - hundreds of them - which would drown the jump list.
  const heads = [...sec.querySelectorAll('h3, h4')]
    .filter(h => h.textContent.trim()
                 && !h.closest('.dcard, .card, details, .jd-body, table, .fnote, .method'));
  if (heads.length < 3) { box.hidden = true; return; }
  box.innerHTML = heads.map((h, i) => {
    h.id = h.id || `${id}-h-${i}`;
    return `<a href="#${h.id}" data-jump="${h.id}">${esc(h.textContent.trim())}</a>`;
  }).join('');
  box.hidden = false;
}

/* --------------------------------------------------------------- tracking
 * Two shapes get a status control: dossier cards (.dcard, one platform each)
 * and table rows (one company each). The key is the section id plus the
 * entity's own name, so it survives a content rebuild. */

function keyFor(sectionId, label) { return sectionId + '::' + label; }

function decorateTrackables() {
  store.sections.forEach(s => {
    if (!s.track) return;
    const root = document.querySelector(`.sec[data-sec="${s.id}"]`);
    if (!root) return;

    if (s.track === 'card') {
      root.querySelectorAll('.dcard').forEach(card => {
        const h = card.querySelector('h4');
        if (!h) return;
        card.appendChild(makeChip(s.id, h.textContent.trim(), card));
        card.style.paddingBottom = '38px';
      });
    }

    if (s.track === 'row') {
      root.querySelectorAll('table').forEach(table => {
        table.querySelectorAll('tr').forEach(tr => {
          if (tr.querySelector('th')) {                    // header row
            const th = document.createElement('th');
            th.textContent = '';
            tr.insertBefore(th, tr.firstElementChild);
            return;
          }
          const first = tr.querySelector('td');
          if (!first) return;
          const label = first.textContent.trim();
          if (!label) return;
          const td = document.createElement('td');
          td.className = 'track-cell';
          td.appendChild(makeChip(s.id, label, tr));
          tr.insertBefore(td, tr.firstElementChild);
        });
      });
    }
  });
}

function makeChip(sectionId, label, host) {
  const btn = document.createElement('button');
  btn.className = 'track';
  btn.dataset.key = keyFor(sectionId, label);
  btn.dataset.label = label;
  btn.dataset.section = sectionId;
  btn.title = 'Set status / add a note';
  host.classList.add('trackable');
  paintChip(btn, host);
  return btn;
}

function paintChip(btn, host) {
  const item = store.items[btn.dataset.key];
  host = host || btn.closest('tr, .dcard');
  if (item && (item.status || item.note)) {
    btn.dataset.status = item.status || '';
    btn.classList.add('has');
    btn.classList.toggle('noted', !!(item.note || '').trim());
    btn.innerHTML = item.status
      ? `<span class="dot"></span>${STATUS_LABEL[item.status]}`
      : '<span class="dot"></span>Note';
    if (host) host.classList.add('tracked');
  } else {
    delete btn.dataset.status;
    btn.classList.remove('has', 'noted');
    btn.textContent = '+ track';
    if (host) host.classList.remove('tracked');
  }
}

function repaintAllChips() {
  document.querySelectorAll('.track').forEach(b => paintChip(b));
  updateTally();
  el('secCount').innerHTML = countLine(store.current);
}

function updateTally() {
  const counts = {};
  Object.values(store.items).forEach(i => {
    counts[i.section] = (counts[i.section] || 0) + 1;
  });
  document.querySelectorAll('[data-tally]').forEach(t => {
    const id = t.dataset.tally;
    const n = id === 'tracker' ? Object.keys(store.items).length : counts[id] || 0;
    t.textContent = n;
    t.hidden = !n;
  });
}

/* --------------------------------------------------------------- popover */

let popTarget = null;   // {key, label, section} - not a DOM node, so the tracker
                        // view can reopen an entry whose chip is on another page

function openPopover(anchor, target) {
  popTarget = target;
  const item = store.items[target.key] || { status: '', note: '' };
  el('popLabel').textContent = target.label;
  el('popNote').value = item.note || '';
  el('popStatuses').innerHTML = STATUSES.map(s =>
    `<button data-status="${s.id}"${item.status === s.id ? ' class="on"' : ''}>${s.label}</button>`
  ).join('');

  const btn = anchor;
  const pop = el('popover');
  pop.hidden = false;
  const r = btn.getBoundingClientRect();
  const top = r.bottom + window.scrollY + 6;
  const left = Math.min(r.left + window.scrollX,
                        document.documentElement.clientWidth - pop.offsetWidth - 16);
  pop.style.top = top + 'px';
  pop.style.left = Math.max(8, left) + 'px';
  el('popNote').focus();
}

function closePopover() { el('popover').hidden = true; popTarget = null; }

async function savePopover(clear) {
  if (!popTarget) return;
  const status = clear ? '' : (el('popStatuses').querySelector('.on')?.dataset.status || '');
  const note = clear ? '' : el('popNote').value;
  const body = { ...popTarget, status, note };
  const res = await fetch('/api/state', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) { alert('Could not save - is the server still running?'); return; }
  store.items = (await res.json()).items || {};
  repaintAllChips();
  if (store.current === 'tracker') renderTracker();
  closePopover();
}

/* ---------------------------------------------------------------- tracker */

function renderTracker() {
  const host = document.querySelector('.sec[data-sec="tracker"]');
  const entries = Object.entries(store.items);
  if (!entries.length) {
    host.innerHTML =
      '<p class="tracker-empty">Nothing tracked yet. On the company tables and platform ' +
      'cards, click <span class="track">+ track</span> to set a status and keep a note ' +
      '&mdash; everything you mark shows up here, and is saved to ' +
      '<code>career-hub/state.json</code>.</p>';
    return;
  }
  const order = ['in-progress', 'applied', 'interested', 'rejected', 'closed', ''];
  const groups = {};
  entries.forEach(([key, it]) => (groups[it.status || ''] ||= []).push([key, it]));

  host.innerHTML = order.filter(s => groups[s]).map(status => {
    const rows = groups[status].sort((a, b) => a[1].label.localeCompare(b[1].label)).map(([key, it]) => {
      const sec = store.byId[it.section];
      return `<tr>
        <td><strong>${esc(it.label)}</strong>
            ${it.note ? `<p class="tracker-note">${esc(it.note)}</p>` : ''}</td>
        <td class="tracker-link">${sec ? esc(deent(sec.title)) : esc(it.section)}</td>
        <td><button class="ghost-btn" data-open-key="${esc(key)}">Edit</button></td>
      </tr>`;
    }).join('');
    return `<div class="tracker-group">
      <h3 class="section-h">${status ? STATUS_LABEL[status] : 'Note only'}
        <span class="rank">&nbsp;${groups[status].length}</span></h3>
      <div class="table-wrap"><table><tr><th>Entry</th><th>Section</th><th></th></tr>
      ${rows}</table></div></div>`;
  }).join('');
}

/* ---------------------------------------------------------------- search */

function indexText() {
  store.sections.forEach(s => {
    const node = document.querySelector(`.sec[data-sec="${s.id}"]`);
    store.text[s.id] = node ? (node.innerText || '').toLowerCase() : '';
    // Names - headings, card titles, first table cells, JD titles - are what
    // people actually search for, so a hit there outranks a passing mention.
    store.names[s.id] = node
      ? [...node.querySelectorAll('h3, h4, h5, .dcard h4, summary, td:first-child, .pill')]
          .map(n => n.textContent).join(' \n ').toLowerCase()
      : '';
  });
}

function runSearch(q) {
  const box = el('searchResults');
  el('searchClear').hidden = !q;
  if (q.length < 2) { box.hidden = true; return; }
  const needle = q.toLowerCase();
  const count = (hay) => {
    let n = 0, i = hay.indexOf(needle);
    while (i !== -1) { n++; i = hay.indexOf(needle, i + needle.length); }
    return n;
  };
  const hits = store.sections.map(s => {
    const n = count(store.text[s.id] || '');
    const named = count(store.names[s.id] || '');
    const inTitle = deent(s.title).toLowerCase().includes(needle);
    // A name match is worth far more than a passing mention in body copy.
    return { s, n, named, score: n + named * 25 + (inTitle ? 500 : 0) };
  }).filter(h => h.n).sort((a, b) => b.score - a.score);

  box.innerHTML = hits.length
    ? hits.map(h => `<button class="sr" data-goto="${h.s.id}" data-q="${esc(q)}">
         <span class="n">${h.named ? '&#9679; ' : ''}${h.n}</span>
         <span class="g">${esc(deent(h.s.group))}</span>
         ${h.s.title}</button>`).join('')
    : `<div class="empty">No match for &ldquo;${esc(q)}&rdquo;</div>`;
  box.hidden = false;
}

function highlight(sectionId, q) {
  clearHighlights();
  if (!q || q.length < 2) return;
  const root = document.querySelector(`.sec[data-sec="${sectionId}"]`);
  if (!root) return;
  const needle = q.toLowerCase();
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: n => n.nodeValue.toLowerCase().includes(needle) && n.parentElement.offsetParent !== null
      ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT,
  });
  const targets = [];
  while (walker.nextNode()) targets.push(walker.currentNode);

  targets.forEach(node => {
    const frag = document.createDocumentFragment();
    let rest = node.nodeValue, idx;
    while ((idx = rest.toLowerCase().indexOf(needle)) !== -1) {
      frag.append(rest.slice(0, idx));
      const m = document.createElement('mark');
      m.textContent = rest.slice(idx, idx + q.length);
      frag.append(m);
      rest = rest.slice(idx + q.length);
    }
    frag.append(rest);
    node.parentNode.replaceChild(frag, node);
  });

  const first = root.querySelector('mark');
  if (first) {
    first.classList.add('on');
    // Any <details> holding the hit must be open before scrolling to it.
    let p = first.parentElement;
    while (p) { if (p.tagName === 'DETAILS') p.open = true; p = p.parentElement; }
    first.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
}

function clearHighlights() {
  document.querySelectorAll('mark').forEach(m => {
    const t = document.createTextNode(m.textContent);
    m.parentNode.replaceChild(t, m);
  });
  document.querySelectorAll('.sec').forEach(s => s.normalize());
}

/* ---------------------------------------------------------------- events */

function wireEvents() {
  document.addEventListener('click', e => {
    const goto = e.target.closest('[data-goto]');
    if (goto) {
      show(goto.dataset.goto);
      if (goto.dataset.q) { highlight(goto.dataset.goto, goto.dataset.q); el('searchResults').hidden = true; }
      else clearHighlights();
      return;
    }
    const jump = e.target.closest('[data-jump]');
    if (jump) {
      e.preventDefault();
      const t = document.getElementById(jump.dataset.jump);
      if (t) t.scrollIntoView({ block: 'start', behavior: 'smooth' });
      return;
    }
    const chip = e.target.closest('.track');
    if (chip) {
      e.preventDefault(); e.stopPropagation();
      openPopover(chip, { key: chip.dataset.key, label: chip.dataset.label,
                          section: chip.dataset.section });
      return;
    }

    const edit = e.target.closest('[data-open-key]');
    if (edit) {
      const key = edit.dataset.openKey;
      const it = store.items[key];
      if (it) openPopover(edit, { key, label: it.label, section: it.section });
      return;
    }

    const st = e.target.closest('#popStatuses button');
    if (st) {
      const was = st.classList.contains('on');
      el('popStatuses').querySelectorAll('button').forEach(b => b.classList.remove('on'));
      if (!was) st.classList.add('on');
      return;
    }
    if (!e.target.closest('#popover')) closePopover();
  });

  el('popSave').addEventListener('click', () => savePopover(false));
  el('popClear').addEventListener('click', () => savePopover(true));
  el('popNote').addEventListener('keydown', e => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) savePopover(false);
  });

  let t;
  el('search').addEventListener('input', e => {
    clearTimeout(t);
    const q = e.target.value.trim();
    t = setTimeout(() => runSearch(q), 130);
  });
  el('searchClear').addEventListener('click', () => {
    el('search').value = '';
    el('searchResults').hidden = true;
    el('searchClear').hidden = true;
    clearHighlights();
  });

  el('themeToggle').addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('careerhub-theme', next);
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closePopover(); el('searchResults').hidden = true; }
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT'
        && document.activeElement.tagName !== 'TEXTAREA') {
      e.preventDefault(); el('search').focus();
    }
  });
}

boot();
