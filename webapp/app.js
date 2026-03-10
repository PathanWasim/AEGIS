/* ================================================================
   AEGIS Dashboard — App Logic
   ================================================================ */

const API = 'http://localhost:5000/api';

// ── Session stats ────────────────────────────────────────────────
const session = { runs: 0, errors: 0, timings: [] };

// ── Examples (shown in playground sidebar) ───────────────────────
let serverExamples = [];

// ── Token filter state ───────────────────────────────────────────
let activeFilters = new Set(['keyword','identifier','literal','operator','structural']);

// ── Init ─────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  showPage('home');
  checkServer();
  loadExamples();
  startTypewriter();
  updateLineNums();
  document.getElementById('code-editor').addEventListener('input', () => {
    updateLineNums();
    debouncedTokenize();
  });
});

// ── Navigation ───────────────────────────────────────────────────
function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.toggle('active', t.dataset.page === id));
  const pg = document.getElementById('page-' + id);
  if (pg) pg.classList.add('active');
}

// ── Server health ─────────────────────────────────────────────────
async function checkServer() {
  try {
    const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(2000) });
    setServerStatus(r.ok);
  } catch { setServerStatus(false); }
  setInterval(async () => {
    try { const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(2000) }); setServerStatus(r.ok); }
    catch { setServerStatus(false); }
  }, 10000);
}

function setServerStatus(ok) {
  const dot  = document.getElementById('srv-dot');
  const txt  = document.getElementById('srv-txt');
  if (!dot) return;
  dot.className = 'dot' + (ok ? '' : ' off');
  txt.textContent = ok ? 'Server online' : 'Server offline';
  document.getElementById('sb-server').textContent = ok ? '● Connected to localhost:5000' : '○ Server offline';
}

// ── Examples ─────────────────────────────────────────────────────
async function loadExamples() {
  try {
    const r    = await fetch(`${API}/examples`);
    const data = await r.json();
    serverExamples = data.examples;
    renderExamples(serverExamples);
  } catch {
    document.getElementById('examples-grid').innerHTML = '<div style="color:var(--txt3);font-size:12px;grid-column:1/-1;padding:8px;">Start server to load examples</div>';
  }
}

function renderExamples(list) {
  const grid = document.getElementById('examples-grid');
  grid.innerHTML = '';
  list.forEach(ex => {
    const btn = document.createElement('button');
    btn.className = 'ex-btn';
    btn.innerHTML = `<span class="ex-name">${ex.name}</span><span class="ex-desc">${ex.description}</span>`;
    btn.onclick = () => loadExample(ex.id);
    grid.appendChild(btn);
  });
}

async function loadExample(id) {
  try {
    const r = await fetch(`${API}/examples/${id}`);
    const d = await r.json();
    document.getElementById('code-editor').value = d.code;
    updateLineNums();
    showPage('playground');
  } catch {}
}

// ── Line numbers ─────────────────────────────────────────────────
function updateLineNums() {
  const ta    = document.getElementById('code-editor');
  const nums  = document.getElementById('line-nums');
  const lines = ta.value.split('\n').length;
  nums.textContent = Array.from({length: lines}, (_, i) => i + 1).join('\n');
}

// ── Run ──────────────────────────────────────────────────────────
async function runCode() {
  const code = document.getElementById('code-editor').value.trim();
  if (!code) return;

  const btn = document.getElementById('run-btn');
  btn.classList.add('loading');
  btn.innerHTML = '<span>⏳</span><span>RUNNING…</span>';
  setAllStages('running');

  const t0 = performance.now();
  try {
    const r    = await fetch(`${API}/execute`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
    const data = await r.json();
    const elapsed = performance.now() - t0;
    session.runs++;
    if (!data.success) session.errors++;
    session.timings.push(round(elapsed, 1));
    updateSessionBar();
    displayResult(data);
  } catch {
    displayError('Cannot reach AEGIS server. Is webapp/server.py running?');
    setServerStatus(false);
    setAllStages('');
  } finally {
    btn.classList.remove('loading');
    btn.innerHTML = '<span>▶</span><span>RUN PROGRAM</span><span class="shortcut">Ctrl+Enter</span>';
  }
}

// ── Display result ────────────────────────────────────────────────
function displayResult(data) {
  // Output
  const oa = document.getElementById('output-area');
  oa.innerHTML = '';
  const now = new Date().toLocaleTimeString();

  if (data.success && data.output && data.output.length > 0) {
    data.output.forEach((line, i) => {
      const d = document.createElement('div');
      d.className = 'out-line fade-in';
      d.style.animationDelay = `${i * 35}ms`;
      d.innerHTML = `<span class="pfx">out</span><span class="val">${esc(line)}</span><span class="ts">${now}</span>`;
      oa.appendChild(d);
    });
  } else if (!data.success && data.error) {
    const d = document.createElement('div');
    d.className = 'out-line err fade-in';
    d.innerHTML = `<span class="pfx">err</span><span class="val">${esc(data.error)}</span><span class="ts">${now}</span>`;
    oa.appendChild(d);
  } else {
    oa.innerHTML = `<div class="empty"><div class="empty-icon">✓</div><span style="color:var(--green)">Ran with no output</span></div>`;
  }

  // Tokens
  renderTokens(data.tokens || []);

  // Stats
  const trust   = data.trust_score || 0;
  const trustPc = Math.min(trust * 100, 100);
  setVal('trust-val',  trust.toFixed(3));
  setVal('time-val',   data.execution_time_ms ?? '—');
  setVal('tokens-val', (data.tokens || []).filter(t => t.type !== 'NEWLINE' && t.type !== 'EOF').length);
  setVal('mode-val',   data.optimized ? '⚡ OPT' : '🛡 SAFE');
  document.getElementById('mode-sub').textContent   = data.optimized ? 'Optimized (trusted)' : 'Sandboxed interpreter';
  document.getElementById('trust-fill').style.width = `${trustPc}%`;
  document.getElementById('trust-sub').textContent  = trustLabel(trust);
  document.getElementById('sb-hash').textContent    = data.code_hash ? `hash:${data.code_hash}` : '';

  ['stat-trust','stat-time','stat-tokens','stat-mode'].forEach(id => flash(id));

  // Pipeline
  const s = data.pipeline_stages || {};
  setStage('sl', data.tokens?.length > 0 ? 'done' : 'error');
  setStage('sp', s.parsed   ? 'done' : 'error');
  setStage('sa', s.analyzed ? 'done' : 'error');
  setStage('st', 'done');
  setStage('se', data.success ? 'done' : 'error');
}

function displayError(msg) {
  document.getElementById('output-area').innerHTML =
    `<div class="out-line err fade-in"><span class="pfx">err</span><span class="val">${esc(msg)}</span></div>`;
  ['sl','sp','sa','st','se'].forEach(id => setStage(id, 'error'));
}

// ── Tokens ────────────────────────────────────────────────────────
function renderTokens(tokens) {
  const filtered = tokens.filter(t => t.type !== 'NEWLINE' && t.type !== 'EOF');
  const ta = document.getElementById('token-area');
  ta.innerHTML = '';
  const visible = filtered.filter(t => activeFilters.has(t.category));
  if (visible.length === 0) {
    ta.innerHTML = '<div class="empty"><div class="empty-icon">✦</div><span>No tokens</span></div>';
    document.getElementById('tok-count').textContent = '—';
    return;
  }
  visible.forEach((t, i) => {
    const pill = document.createElement('div');
    pill.className = `token-pill tp-${t.category} fade-in`;
    pill.style.animationDelay = `${i * 12}ms`;
    pill.title = `${t.type} · line ${t.line}, col ${t.column}`;
    pill.textContent = t.value || t.type;
    ta.appendChild(pill);
  });
  document.getElementById('tok-count').textContent = `${visible.length} / ${filtered.length}`;
}

function toggleFilter(cat, btn) {
  if (activeFilters.has(cat)) { activeFilters.delete(cat); btn.classList.remove('on'); }
  else { activeFilters.add(cat); btn.classList.add('on'); }
  // Re-render tokens from current run (stored in last data)
  const ta = document.getElementById('token-area');
  const pills = document.querySelectorAll('#token-area .token-pill');
  pills.forEach(p => {
    const cat2 = [...p.classList].find(c => c.startsWith('tp-'))?.replace('tp-','');
    p.style.display = cat2 && activeFilters.has(cat2) ? '' : 'none';
  });
}

// ── Debounced tokenize ────────────────────────────────────────────
const debouncedTokenize = debounce(async () => {
  const code = document.getElementById('code-editor').value.trim();
  if (!code) return;
  try {
    const r    = await fetch(`${API}/tokenize`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({code}) });
    const data = await r.json();
    if (data.success) renderTokens(data.tokens);
  } catch {}
}, 600);

// ── Pipeline helpers ─────────────────────────────────────────────
function setStage(id, state) {
  const el = document.getElementById('stage-' + id);
  if (!el) return;
  el.classList.remove('done','error','running');
  if (state) el.classList.add(state);
}
function setAllStages(state) {
  ['sl','sp','sa','st','se'].forEach(id => setStage(id, state));
}

// ── Stats helpers ─────────────────────────────────────────────────
function setVal(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function flash(id) { const el = document.getElementById(id); el?.classList.add('flash'); setTimeout(() => el?.classList.remove('flash'), 1800); }
function trustLabel(t) {
  if (t < 0.1) return 'NONE — sandboxed';
  if (t < 0.3) return 'LOW — building trust';
  if (t < 0.6) return 'MEDIUM — gaining trust';
  if (t < 0.8) return 'HIGH — near-optimized';
  return 'TRUSTED — ⚡ optimized';
}

// ── Session stats bar ────────────────────────────────────────────
function updateSessionBar() {
  setVal('sb-runs', `${session.runs} runs`);
  setVal('sb-errors', `${session.errors} errors`);
  const avg = session.timings.length ? round(session.timings.reduce((a,b)=>a+b,0)/session.timings.length,1) : '—';
  setVal('sb-avg', `avg ${avg}ms`);
}

// ── Clear ────────────────────────────────────────────────────────
function clearEditor() {
  document.getElementById('code-editor').value = '';
  updateLineNums();
}
function clearOutput() {
  document.getElementById('output-area').innerHTML = `<div class="empty"><div class="empty-icon">💻</div><span>Run a program to see output</span></div>`;
  document.getElementById('token-area').innerHTML  = `<div class="empty"><div class="empty-icon">✦</div><span>Tokens appear here</span></div>`;
  document.getElementById('tok-count').textContent = '—';
  resetStats(); setAllStages('');
}
function resetStats() {
  ['trust-val','time-val','tokens-val'].forEach(id => setVal(id,'—'));
  setVal('mode-val','—');
  document.getElementById('trust-fill').style.width = '0%';
  document.getElementById('trust-sub').textContent  = 'Not executed yet';
  document.getElementById('mode-sub').textContent   = 'awaiting execution';
}

// ── Docs navigation ──────────────────────────────────────────────
function showDoc(id, el) {
  document.querySelectorAll('.docs-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.docs-link').forEach(l => l.classList.remove('active'));
  const sec = document.getElementById('doc-' + id); if (sec) sec.classList.add('active');
  if (el) el.classList.add('active');
}

function tryExample(code) {
  document.getElementById('code-editor').value = code;
  updateLineNums();
  showPage('playground');
}

// ── Typewriter hero demo ─────────────────────────────────────────
const DEMOS = [
`# Fibonacci sequence
a = 0
b = 1
count = 0
while count < 8
  print a
  temp = a + b
  a = b
  b = temp
  count = count + 1
end`,

`# Trust-gated optimisation
x = 100
y = 200
total = x + y
print total`,

`# Conditional branching
score = 85
if score > 90
  print 100
else
  print score
end`,
];

let demoIdx = 0, charIdx = 0, deleting = false;

function startTypewriter() {
  const el = document.getElementById('hero-code');
  if (!el) return;
  function tick() {
    const target = DEMOS[demoIdx];
    if (!deleting) {
      charIdx++;
      el.innerHTML = highlight(target.slice(0, charIdx)) + '<span style="opacity:0.7;animation:pulse 1s infinite">▋</span>';
      if (charIdx >= target.length) { deleting = true; setTimeout(tick, 2400); return; }
      setTimeout(tick, 26);
    } else {
      charIdx = Math.max(0, charIdx - 3);
      el.innerHTML = highlight(target.slice(0, charIdx)) + '<span style="opacity:0.7;animation:pulse 1s infinite">▋</span>';
      if (charIdx === 0) { deleting = false; demoIdx = (demoIdx + 1) % DEMOS.length; setTimeout(tick, 400); return; }
      setTimeout(tick, 14);
    }
  }
  tick();
}

// ── Syntax highlight — single-pass to avoid corrupting injected span tags ────
function highlight(code) {
  // esc() converts < > & " in source to HTML entities (&lt; &gt; etc.)
  // A single regex then processes all token types left-to-right so no pass
  // ever sees the <span> tags written by a previous pass.
  return esc(code).replace(
    /(#[^\n]*)|\b(if|else|while|end|print)\b|\b(\d+)\b|([+\-*\/%]|==|!=|&lt;=?|&gt;=?|(?<![=!])=(?!=))/g,
    (_, cmt, kw, num, op) => {
      if (cmt) return `<span class="sh-cmt">${cmt}</span>`;
      if (kw)  return `<span class="sh-kw">${kw}</span>`;
      if (num) return `<span class="sh-num">${num}</span>`;
      if (op)  return `<span class="sh-op">${op}</span>`;
      return _;
    }
  );
}

// ── Utilities ────────────────────────────────────────────────────
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function debounce(fn, ms) {
  let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}
function round(n, d) { return +n.toFixed(d); }

// ── Keyboard shortcuts ───────────────────────────────────────────
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); runCode(); }
});
