/* ================================================================
   AEGIS IDE — app.js
   Professional IDE frontend: view routing, code execution,
   trust analytics, violation log, runtime monitor
   ================================================================ */

// ── State ─────────────────────────────────────────────────────────
const state = {
  runs: 0,
  errors: 0,
  violations: [],
  execHistory: [],
  execMode: 'sandboxed',
  serverOnline: false,
  currentView: 'editor',
  currentFile: 'fibonacci.aegis',
  timings: [],
  totalTokens: 0,
  optRuns: 0,
  sandRuns: 0,
};

const SERVER = 'http://localhost:5000';

// ── Examples ──────────────────────────────────────────────────────
const EXAMPLES = {
  fibonacci: {
    name: 'Fibonacci',
    desc: 'Print first 10 numbers',
    code: `a = 0\nb = 1\ncount = 0\nwhile count < 10\n  print a\n  temp = a + b\n  a = b\n  b = temp\n  count = count + 1\nend`,
  },
  hello: {
    name: 'Hello World',
    desc: 'Basic print statement',
    code: `x = 42\nprint x`,
  },
  security_demo: {
    name: 'Security Demo',
    desc: 'Division by zero — blocked',
    code: `x = 10\ny = 0\nresult = x / y\nprint result`,
  },
  sum: {
    name: 'Sum 1 to N',
    desc: 'Accumulate sum in loop',
    code: `total = 0\ni = 1\nwhile i <= 100\n  total = total + i\n  i = i + 1\nend\nprint total`,
  },
  trust_builder: {
    name: 'Trust Builder',
    desc: 'Run repeatedly to build trust',
    code: `x = 5\ny = 10\nresult = x + y\nprint result`,
  },
  counter: {
    name: 'Counter',
    desc: 'Count with while loop',
    code: `i = 1\nwhile i <= 5\n  print i\n  i = i + 1\nend`,
  },
};

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadExample('fibonacci');
  renderNavExamples();
  renderRpExamples();
  checkServer();
  setInterval(checkServer, 10000);

  document.getElementById('code-editor').addEventListener('input', updateLineNums);
  document.getElementById('code-editor').addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); runCode(); }
    if (e.key === 'Tab') { e.preventDefault(); insertTab(); }
  });
  updateLineNums();
});

// ── View switching ─────────────────────────────────────────────────
function switchView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.rail-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.nav-section').forEach(s => s.style.display = 'none');

  const view = document.getElementById('view-' + name);
  if (view) view.classList.add('active');

  const rail = document.getElementById('rail-' + name);
  if (rail) rail.classList.add('active');

  const nav = document.getElementById('nav-' + name);
  if (nav) nav.style.display = '';

  // Update panel title
  const titles = {
    editor:     ['AEGIS', 'Workspace'],
    trust:      ['TRUST SYSTEM', 'Analytics'],
    monitor:    ['MONITOR', 'Runtime Metrics'],
    violations: ['TRUST SYSTEM', 'Violation Log'],
    settings:   ['SETTINGS', 'Configuration'],
    docs:       ['DOCUMENTATION', 'Reference'],
  };
  const t = titles[name] || ['AEGIS', ''];
  document.getElementById('nav-panel-title').textContent = t[0];
  document.getElementById('nav-panel-sub').textContent = t[1];

  state.currentView = name;

  // Refresh data for specific views
  if (name === 'trust') refreshTrustView();
  if (name === 'monitor') refreshMonitorView();
  if (name === 'violations') refreshViolationsView();
}

// ── Bottom tabs ────────────────────────────────────────────────────
function switchBottomTab(name, el) {
  document.querySelectorAll('.bottom-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.bottom-panel-content').forEach(c => c.classList.remove('active'));
  if (el) el.classList.add('active');
  const content = document.getElementById('bpc-' + name);
  if (content) content.classList.add('active');
}

// ── Settings section switching ─────────────────────────────────────
function switchSettingsSection(name, el) {
  document.querySelectorAll('.settings-nav-item').forEach(i => i.classList.remove('active'));
  document.querySelectorAll('.settings-section').forEach(s => s.style.display = 'none');
  if (el) el.classList.add('active');
  const sec = document.getElementById('sc-' + name);
  if (sec) sec.style.display = '';
}

// ── Server health ──────────────────────────────────────────────────
async function checkServer() {
  try {
    const r = await fetch(SERVER + '/api/health', { signal: AbortSignal.timeout(2000) });
    const ok = r.ok;
    setServerStatus(ok);
  } catch {
    setServerStatus(false);
  }
}

function setServerStatus(online) {
  state.serverOnline = online;
  const dot = document.getElementById('nav-srv-dot');
  const txt = document.getElementById('nav-srv-txt');
  const sbTxt = document.getElementById('sb-server');
  if (dot)  dot.className = 'srv-dot' + (online ? ' online' : '');
  if (txt)  txt.textContent = online ? 'localhost:5000 ● Connected' : 'Server offline';
  if (sbTxt) sbTxt.textContent = online ? 'Server: localhost:5000' : 'Server: offline';
}

// ── Examples ──────────────────────────────────────────────────────
function renderNavExamples() {
  const container = document.getElementById('examples-nav');
  if (!container) return;
  container.innerHTML = '';
  Object.entries(EXAMPLES).forEach(([key, ex]) => {
    const div = document.createElement('div');
    div.className = 'nav-item';
    div.innerHTML = `<span class="ni-icon">📄</span>${ex.name}`;
    div.onclick = () => loadExample(key);
    container.appendChild(div);
  });
}

function renderRpExamples() {
  const container = document.getElementById('rp-examples');
  if (!container) return;
  container.innerHTML = '';
  Object.entries(EXAMPLES).forEach(([key, ex]) => {
    const btn = document.createElement('div');
    btn.className = 'ex-btn';
    btn.innerHTML = `<span class="ex-name">${ex.name}</span><span class="ex-desc">${ex.desc}</span>`;
    btn.onclick = () => loadExample(key);
    container.appendChild(btn);
  });
}

function loadExample(key) {
  const ex = EXAMPLES[key];
  if (!ex) return;
  const editor = document.getElementById('code-editor');
  editor.value = ex.code;
  state.currentFile = key + '.aegis';
  const fn = document.getElementById('active-filename');
  if (fn) fn.textContent = state.currentFile;
  updateLineNums();
  clearProblems();
}

function tryExample(code) {
  document.getElementById('code-editor').value = code;
  updateLineNums();
  switchView('editor');
  clearProblems();
}

// ── Editor ────────────────────────────────────────────────────────
function updateLineNums() {
  const el = document.getElementById('code-editor');
  const lns = document.getElementById('line-nums');
  if (!el || !lns) return;
  const lines = el.value.split('\n').length;
  lns.textContent = Array.from({ length: lines }, (_, i) => i + 1).join('\n');
  el.style.height = 'auto';
}

function clearEditor() {
  const e = document.getElementById('code-editor');
  if (e) { e.value = ''; updateLineNums(); clearProblems(); }
}

function copyCode() {
  const e = document.getElementById('code-editor');
  if (e) navigator.clipboard.writeText(e.value).catch(() => {});
}

function insertTab() {
  const e = document.getElementById('code-editor');
  const start = e.selectionStart, end = e.selectionEnd;
  e.value = e.value.slice(0, start) + '  ' + e.value.slice(end);
  e.selectionStart = e.selectionEnd = start + 2;
  updateLineNums();
}

function setMode(mode) {
  state.execMode = mode;
  document.getElementById('btn-sandboxed').classList.toggle('active', mode === 'sandboxed');
  document.getElementById('btn-optimized').classList.toggle('active', mode === 'optimized');
  document.getElementById('mode-hint').textContent = 'Mode: ' + (mode === 'sandboxed' ? 'Sandboxed' : 'Optimized');
  document.getElementById('sb-mode').textContent = mode === 'sandboxed' ? 'Sandboxed' : 'Optimized';
}

// ── Run code ──────────────────────────────────────────────────────
async function runCode() {
  const code = document.getElementById('code-editor').value.trim();
  if (!code) return;

  const btn = document.getElementById('run-btn');
  btn.textContent = '⏳ Running…';
  btn.disabled = true;

  // Reset pipeline stages
  resetPipeline();
  clearProblems();

  // Show output tab
  switchBottomTab('output', document.querySelector('.bottom-tab'));

  const startTime = performance.now();

  try {
    const res = await fetch(SERVER + '/api/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, mode: state.execMode }),
    });
    const data = await res.json();
    const elapsed = performance.now() - startTime;

    state.runs++;
    handleResult(data, elapsed, code);
  } catch (err) {
    state.errors++;
    appendOutput('error', `Connection error: ${err.message}`);
    setPipelineError('lexer');
    updateStatusBar();
  } finally {
    btn.textContent = '▶ Run';
    btn.disabled = false;
  }
}

function handleResult(data, elapsed, code) {
  const isError = !data.success;
  if (isError) state.errors++;

  // Detect security/semantic error by message
  const isSecurityError = isError && data.error && /security|divis.*zero|overflow|undefined var/i.test(data.error);

  // Determine timing
  const execTime = data.execution_time_ms != null ? data.execution_time_ms : elapsed.toFixed(1);

  // Mode: server gives 'optimized' bool
  const mode = data.optimized ? 'optimized' : state.execMode;

  // Update pipeline stages
  updatePipelineFromData(data, isSecurityError);

  // Output
  const outputArea = document.getElementById('output-area');
  outputArea.innerHTML = '';

  if (data.output && data.output.length) {
    data.output.forEach(line => appendOutput('ok', line));
  }
  if (data.error) {
    if (isSecurityError) {
      appendOutput('error', 'SecurityError: ' + data.error);
      addProblem('error', 'SecurityError: ' + data.error, 'Analyzer');
      registerViolation(data.error, code, null);
    } else {
      appendOutput('error', data.error);
      addProblem('error', data.error, '—');
    }
  }
  if (!data.output?.length && !data.error) {
    appendOutput('sys', '(no output)');
  }

  // Trust & stats
  const trust = data.trust_score ?? null;
  const tokens = data.tokens?.length ?? data.token_count ?? 0;

  // Update code hash in right panel
  const rpHash = document.getElementById('rp-hash');
  if (rpHash && data.code_hash) rpHash.textContent = '#' + data.code_hash;

  updateTrustDisplay(trust, mode, isSecurityError);
  updatePipelineStats(execTime, tokens, trust);
  updateStatusBar();

  // Store history
  state.timings.push(parseFloat(execTime));
  state.totalTokens += tokens;
  if (mode === 'optimized') state.optRuns++;
  else state.sandRuns++;

  const runEntry = {
    run: state.runs,
    file: state.currentFile,
    time: parseFloat(execTime).toFixed(1) + 'ms',
    mode,
    trust,
    isError,
    tokens,
    ts: new Date().toLocaleTimeString(),
  };
  state.execHistory.unshift(runEntry);
  if (state.execHistory.length > 20) state.execHistory.pop();

  updateMonitorTab(execTime, tokens, trust, mode);

  // Tokenise
  if (data.tokens) renderTokens(data.tokens);
  else fetchTokens(document.getElementById('code-editor').value);
}

// ── Pipeline ──────────────────────────────────────────────────────
function resetPipeline() {
  ['lexer','parser','analyzer','trust','executor'].forEach(s => {
    const el = document.getElementById('ps-' + s);
    if (el) el.className = 'pipe-stage';
    const ic = document.getElementById('pi-' + s);
    if (ic) ic.textContent = '·';
  });
}

function setPipelineDone(stage) {
  const el = document.getElementById('ps-' + stage);
  const ic = document.getElementById('pi-' + stage);
  if (el) el.className = 'pipe-stage done';
  if (ic) ic.textContent = '✓';
}

function setPipelineError(stage) {
  const el = document.getElementById('ps-' + stage);
  const ic = document.getElementById('pi-' + stage);
  if (el) el.className = 'pipe-stage error';
  if (ic) ic.textContent = '✗';
}

function updatePipelineFromData(data, isSecurityError) {
  const stages = data.pipeline_stages || {};
  if (data.success) {
    ['lexer','parser','analyzer','trust','executor'].forEach(s => setPipelineDone(s));
  } else if (isSecurityError) {
    setPipelineDone('lexer');
    setPipelineDone('parser');
    setPipelineError('analyzer');
  } else if (data.error) {
    setPipelineDone('lexer');
    // If parsed flag available use it
    if (stages.parsed === false) { setPipelineError('parser'); }
    else { setPipelineDone('parser'); setPipelineError('analyzer'); }
  } else {
    ['lexer','parser','analyzer','trust','executor'].forEach(s => setPipelineDone(s));
  }
}

function updatePipelineStats(time, tokens, trust) {
  const ps = document.getElementById('ps-time');
  const pt = document.getElementById('ps-tokens');
  const pv = document.getElementById('ps-trust-val');
  if (ps) ps.textContent = parseFloat(time).toFixed(1) + 'ms';
  if (pt) pt.textContent = tokens;
  if (pv) pv.textContent = trust != null ? parseFloat(trust).toFixed(3) : '—';
}

// ── Output ───────────────────────────────────────────────────────
function appendOutput(type, text) {
  const area = document.getElementById('output-area');
  const div  = document.createElement('div');
  div.className = 'out-line';
  const pfxMap = { ok: '›', error: '✗', sys: '#' };
  div.innerHTML = `<span class="out-pfx ${type}">${pfxMap[type]||'›'}</span><span class="out-val ${type}">${escHtml(String(text))}</span>`;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
}

function clearOutput() {
  const a = document.getElementById('output-area');
  if (a) a.innerHTML = '<div class="empty-state"><div class="em-icon">💻</div>Run a program to see output</div>';
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Problems panel ─────────────────────────────────────────────────
function addProblem(type, msg, loc) {
  const area = document.getElementById('problems-area');
  if (!area) return;
  // Clear empty state
  const empty = area.querySelector('.pr-empty');
  if (empty) empty.remove();

  const row = document.createElement('div');
  row.className = 'problem-row';
  row.innerHTML = `<div class="pr-icon ${type==='warn'?'warn'
:''}">${type === 'error' ? '●' : '△'}</div>
    <div class="pr-body"><div class="pr-msg">${escHtml(msg)}</div><div class="pr-loc">${loc}</div></div>`;
  area.appendChild(row);

  // Update badge
  const count = area.querySelectorAll('.problem-row').length;
  const badge = document.getElementById('problems-badge');
  if (badge) { badge.textContent = count; badge.style.display = ''; }
}

function clearProblems() {
  const area = document.getElementById('problems-area');
  if (!area) return;
  area.innerHTML = '<div class="pr-empty"><span class="ok-icon">✓</span> No problems detected</div>';
  const badge = document.getElementById('problems-badge');
  if (badge) badge.style.display = 'none';
}

// ── Tokens ────────────────────────────────────────────────────────
async function fetchTokens(code) {
  try {
    const r = await fetch(SERVER + '/api/tokenize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
    const d = await r.json();
    if (d.tokens) renderTokens(d.tokens);
  } catch {}
}

function renderTokens(tokens) {
  const area = document.getElementById('token-area');
  if (!area) return;
  area.innerHTML = '';

  const typeMap = {
    keyword: 'keyword', identifier: 'identifier', literal: 'literal',
    number: 'literal', operator: 'operator', structural: 'structural',
    newline: 'structural', eof: 'structural',
  };

  tokens.forEach(tok => {
    if (!tok.value || tok.value === '\n' || tok.value === 'EOF') return;
    const t = tok.type?.toLowerCase() || 'structural';
    const cls = 'tp-' + (typeMap[t] || 'structural');
    const pill = document.createElement('span');
    pill.className = `token-pill ${cls}`;
    pill.textContent = tok.value;
    pill.title = tok.type;
    pill.setAttribute('data-type', typeMap[t] || 'structural');
    area.appendChild(pill);
  });
}

function toggleFilter(type, btn) {
  btn.classList.toggle('on');
  const isOn = btn.classList.contains('on');
  document.querySelectorAll(`#token-area .token-pill`).forEach(p => {
    if (p.getAttribute('data-type') === type) p.style.display = isOn ? '' : 'none';
  });
}

// ── Trust display ──────────────────────────────────────────────────
function updateTrustDisplay(trust, mode, isError) {
  const score = trust != null ? parseFloat(trust) : null;

  // Right panel
  const rts = document.getElementById('rp-trust-score');
  const rtb = document.getElementById('rp-trust-badge');
  const rtbar = document.getElementById('rp-trust-bar');
  if (rts) rts.textContent = score != null ? score.toFixed(3) : '0.000';
  if (rtb) {
    const [level, cls] = trustLevel(score);
    rtb.textContent = level;
    rtb.className = 'trust-badge ' + cls;
  }
  if (rtbar) rtbar.style.width = (score != null ? Math.min(score * 100, 100) : 0) + '%';

  // Right panel stats
  const rpExecs = document.getElementById('rp-execs');
  const rpViols = document.getElementById('rp-viols');
  const rpOpt   = document.getElementById('rp-opt');
  const rpLast  = document.getElementById('rp-lastrun');
  const rpHash  = document.getElementById('rp-hash');
  if (rpExecs) rpExecs.textContent = state.runs;
  if (rpViols) rpViols.textContent = state.violations.length;
  if (rpOpt)   { rpOpt.textContent = (mode === 'optimized' || mode === 'OPTIMIZED') ? 'Yes' : 'No'; rpOpt.className = 'stat-val' + ((mode === 'optimized' || mode === 'OPTIMIZED') ? ' hi' : ''); }
  if (rpLast)  rpLast.textContent = new Date().toLocaleTimeString();

  // Security panel
  const secStatus = document.getElementById('sec-status');
  const secBlocked = document.getElementById('sec-blocked');
  if (secStatus) {
    if (isError && state.violations.length > 0) {
      secStatus.innerHTML = '<span>✗</span> ' + state.violations.length + ' violation(s)';
      secStatus.className = 'sec-status warn';
    } else {
      secStatus.innerHTML = '<span>✓</span> No violations';
      secStatus.className = 'sec-status';
    }
  }
  if (secBlocked) { secBlocked.textContent = isError ? 'Yes' : 'No'; secBlocked.className = 'stat-val' + (isError ? ' err' : ' ok'); }

  // Status bar
  document.getElementById('sb-trust-disp').textContent = 'Trust: ' + (score != null ? score.toFixed(3) : '—');
  document.getElementById('sb-runs').textContent = state.runs + ' runs';
  document.getElementById('sb-errors').textContent = state.errors + ' errors';
}

function trustLevel(score) {
  if (score == null) return ['NOT RUN', ''];
  if (score >= 0.8) return ['TRUSTED', 'trusted'];
  if (score >= 0.6) return ['HIGH', 'high'];
  if (score >= 0.3) return ['MEDIUM', 'medium'];
  if (score >= 0.1) return ['LOW', 'low'];
  return ['NONE', 'low'];
}

// ── Monitor inline tab ─────────────────────────────────────────────
function updateMonitorTab(time, tokens, trust, mode) {
  const setV = (id, val) => { const e = document.getElementById(id); if (e) e.textContent = val; };
  const t = state.timings;
  const avg = t.length ? (t.reduce((a,b)=>a+b,0)/t.length).toFixed(1)+'ms' : '—';
  setV('mon-time', parseFloat(time).toFixed(1) + 'ms');
  setV('mon-trust', trust != null ? parseFloat(trust).toFixed(3) : '—');
  setV('mon-toks', tokens);
  setV('mon-mode', mode || '—');
  setV('mon-viol', state.violations.length);
}

// ── Status bar ─────────────────────────────────────────────────────
function updateStatusBar() {
  document.getElementById('sb-runs').textContent = state.runs + ' runs';
  document.getElementById('sb-errors').textContent = state.errors + ' errors';
}

// ── Violation tracking ─────────────────────────────────────────────
function registerViolation(msg, code, line) {
  state.violations.push({
    id: state.violations.length + 1,
    ts: new Date().toLocaleTimeString(),
    file: state.currentFile,
    line: line || '?',
    type: classifyViolation(msg),
    snippet: code.split('\n')[line ? line - 1 : 0]?.trim()?.slice(0, 40) || '—',
    msg,
  });
}

function classifyViolation(msg) {
  if (/divis/i.test(msg)) return 'Division by Zero';
  if (/undef/i.test(msg)) return 'Undefined Variable';
  if (/overflow/i.test(msg)) return 'Integer Overflow';
  if (/loop|timeout/i.test(msg)) return 'Infinite Loop';
  return 'Security Error';
}

// ── Trust Monitor View ─────────────────────────────────────────────
function refreshTrustView() {
  const lastRun = state.execHistory[0];
  const trust = lastRun?.trust ?? null;
  const score = trust != null ? parseFloat(trust) : null;

  document.getElementById('tm-score').textContent = score != null ? score.toFixed(3) : '—';
  document.getElementById('tm-execs').textContent = state.runs;
  document.getElementById('tm-viols').textContent = state.violations.length;

  const optRate = state.runs > 0 ? Math.round((state.optRuns / state.runs) * 100) + '%' : '—';
  document.getElementById('tm-optrate').textContent = optRate;

  // Execution history table
  const tbody = document.getElementById('exec-history-tbody');
  if (tbody) {
    if (!state.execHistory.length) {
      tbody.innerHTML = '<tr><td colspan="4" style="padding:12px;color:var(--txt3);font-size:11px">No executions yet</td></tr>';
    } else {
      tbody.innerHTML = state.execHistory.slice(0, 10).map(r => {
        const badgeCls = r.isError ? 'fail' : (r.mode === 'optimized' || r.mode === 'OPTIMIZED' ? 'opt' : 'sand');
        const badgeTxt = r.isError ? 'Error' : (r.mode === 'optimized' || r.mode === 'OPTIMIZED' ? 'Optimized' : 'Sandboxed');
        return `<tr class="${r.isError ? 'err-row' : ''}">
          <td>#${r.run}</td><td>${r.file}</td><td>${r.time}</td>
          <td><span class="exec-badge ${badgeCls}">${badgeTxt}</span></td>
        </tr>`;
      }).join('');
    }
  }

  // Sparkline
  renderSparkline();

  // Security events
  const secEl = document.getElementById('tm-sec-events');
  if (secEl) {
    if (!state.violations.length) {
      secEl.textContent = 'No security events recorded.';
    } else {
      secEl.innerHTML = state.violations.map(v =>
        `<div style="padding:4px 0;border-bottom:1px solid var(--border);display:flex;gap:8px;align-items:center;font-size:11px">
          <span style="color:var(--red)">●</span>
          <span style="color:var(--txt2)">${v.type}</span>
          <span style="color:var(--txt3);font-family:var(--mono)">${v.file}:${v.line}</span>
          <span style="color:var(--txt3);margin-left:auto">${v.ts}</span>
        </div>`).join('');
    }
  }

  // Trust threshold table highlight
  updateThresholdTable(score);
  document.getElementById('tm-runs-label').textContent = state.runs + ' runs';
}

function updateThresholdTable(score) {
  const levels = [
    { id: null, label: 'NONE',    min: 0 },
    { id: null, label: 'LOW',     min: 0.1 },
    { id: null, label: 'MEDIUM',  min: 0.3 },
    { id: null, label: 'HIGH',    min: 0.6 },
    { id: 'thresh-trusted', label: 'TRUSTED', min: 0.8 },
  ];
  const tbody = document.getElementById('thresh-tbody');
  if (!tbody || score == null) return;
  const rows = tbody.querySelectorAll('tr');
  rows.forEach((row, i) => {
    row.className = '';
    const min = levels[i].min;
    const next = levels[i + 1]?.min ?? 1.01;
    if (score >= min && score < next) row.className = 'current-level';
  });
}

function renderSparkline() {
  const path  = document.getElementById('sparkline-path');
  const dots  = document.getElementById('sparkline-dots');
  const empty = document.getElementById('sparkline-empty');
  if (!path || !dots) return;

  const scores = state.execHistory.slice().reverse().map(r => r.trust ?? 0).filter((_, i, a) => i < 20);
  if (!scores.length) { path.setAttribute('points', ''); dots.innerHTML = ''; if (empty) empty.style.display = ''; return; }
  if (empty) empty.style.display = 'none';

  const W = 400, H = 80, pad = 10;
  const xStep = scores.length > 1 ? (W - pad * 2) / (scores.length - 1) : 0;
  const yScale = v => H - pad - v * (H - pad * 2);

  const pts = scores.map((v, i) => `${pad + i * xStep},${yScale(v)}`).join(' ');
  path.setAttribute('points', pts);

  dots.innerHTML = scores.map((v, i) => {
    const cx = pad + i * xStep, cy = yScale(v);
    const col = v >= 0.8 ? 'var(--blue)' : v > 0 ? 'var(--green)' : 'var(--red)';
    return `<circle cx="${cx}" cy="${cy}" r="2.5" fill="${col}"/>`;
  }).join('');
}

// ── Violation Log View ─────────────────────────────────────────────
function refreshViolationsView() {
  const countEl = document.getElementById('vl-count');
  if (countEl) countEl.textContent = `Showing ${state.violations.length} violation${state.violations.length !== 1 ? 's' : ''}`;

  renderViolationTable(state.violations);
}

function renderViolationTable(violations) {
  const tbody = document.getElementById('vl-tbody');
  if (!tbody) return;

  if (!violations.length) {
    tbody.innerHTML = '<tr><td colspan="8" style="padding:20px;color:var(--txt3);font-size:12px">No violations recorded this session.</td></tr>';
    return;
  }

  tbody.innerHTML = violations.map((v, idx) => `
    <tr onclick="toggleViolationExpansion(${v.id}, this)">
      <td class="vt-num">${v.id}</td>
      <td class="vt-ts">${v.ts}</td>
      <td class="vt-file">${v.file}</td>
      <td class="vt-line">${v.line}</td>
      <td><div class="vt-type"><div class="vt-red-dot"></div>${v.type}</div></td>
      <td><code class="vt-code">${escHtml(v.snippet || '—')}</code></td>
      <td class="vt-action"><span class="action-badge">Blocked</span></td>
      <td>No change</td>
    </tr>
    <tr id="vl-exp-${v.id}" style="display:none">
      <td colspan="8" style="padding:0">
        <div class="vl-expansion">
          <div class="vl-exp-header">VIOLATION DETAIL — #${v.id}</div>
          <div class="vl-exp-grid">
            <div class="vl-exp-row"><span class="vl-exp-key">File:</span><span class="vl-exp-val">${v.file}</span></div>
            <div class="vl-exp-row"><span class="vl-exp-key">Session:</span><span class="vl-exp-val">Session #1</span></div>
            <div class="vl-exp-row"><span class="vl-exp-key">Line:</span><span class="vl-exp-val">${v.line}</span></div>
            <div class="vl-exp-row"><span class="vl-exp-key">Time:</span><span class="vl-exp-val">${v.ts}</span></div>
            <div class="vl-exp-row"><span class="vl-exp-key">Type:</span><span class="vl-exp-val">${v.type}</span></div>
            <div class="vl-exp-row"><span class="vl-exp-key">Severity:</span><span class="vl-exp-val red">CRITICAL</span></div>
          </div>
          <div class="vl-exp-msg"><span class="msg-label">Analyzer Message</span>${escHtml(v.msg)}</div>
          <div class="vl-exp-impact">Trust Impact: No change (score preserved at pre-run value)</div>
        </div>
      </td>
    </tr>
  `).join('');
}

function toggleViolationExpansion(id, row) {
  const exp = document.getElementById('vl-exp-' + id);
  if (!exp) return;
  exp.style.display = exp.style.display === 'none' ? '' : 'none';
}

function filterViolations() {
  const search = (document.getElementById('vl-search')?.value || '').toLowerCase();
  const type   = document.getElementById('vl-filter')?.value || '';
  const filtered = state.violations.filter(v =>
    (!search || v.type.toLowerCase().includes(search) || v.file.includes(search) || v.msg.toLowerCase().includes(search)) &&
    (!type   || v.type.includes(type))
  );
  renderViolationTable(filtered);
  const countEl = document.getElementById('vl-count');
  if (countEl) countEl.textContent = `Showing ${filtered.length} of ${state.violations.length} violations`;
}

function exportViolations() {
  const header = 'ID,Timestamp,File,Line,Type,Snippet,Action\n';
  const rows = state.violations.map(v => `${v.id},"${v.ts}","${v.file}","${v.line}","${v.type}","${v.snippet}","Execution Blocked"`).join('\n');
  const blob = new Blob([header + rows], { type: 'text/csv' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'aegis_violations.csv'; a.click();
}

// ── Runtime Monitor View ───────────────────────────────────────────
function refreshMonitorView() {
  const t = state.timings;
  const avg = t.length ? (t.reduce((a,b)=>a+b,0)/t.length).toFixed(1) : '—';
  const fastest = t.length ? Math.min(...t).toFixed(1) + 'ms' : '—';
  const slowest = t.length ? Math.max(...t).toFixed(1) + 'ms' : '—';

  const lastRun = state.execHistory[0];
  const setV = (id, val) => { const e = document.getElementById(id); if (e) e.textContent = val; };

  setV('rm-time',   avg === '—' ? '—' : avg + 'ms');
  setV('rm-tokens', state.totalTokens > 0 && state.runs > 0 ? Math.round(state.totalTokens / state.runs) : '—');
  setV('rm-runs',   state.runs);
  setV('rm-trust',  lastRun?.trust != null ? parseFloat(lastRun.trust).toFixed(3) : '—');
  setV('rm-fastest', fastest);
  setV('rm-slowest', slowest);
  setV('rm-avg',    avg === '—' ? '—' : avg + 'ms');
  setV('rm-total-toks', state.totalTokens || '—');
  setV('rm-opt-runs',  state.optRuns + ' / ' + state.runs);
  setV('rm-sand-runs', state.sandRuns + ' / ' + state.runs);

  // Recent executions table
  const tbody = document.getElementById('rm-exec-tbody');
  if (tbody) {
    if (!state.execHistory.length) {
      tbody.innerHTML = '<tr><td colspan="4" style="padding:10px;color:var(--txt3);font-size:11px">No executions yet</td></tr>';
    } else {
      tbody.innerHTML = state.execHistory.slice(0, 8).map(r => {
        const cls = r.isError ? 'fail' : (r.mode === 'optimized' || r.mode === 'OPTIMIZED' ? 'opt' : 'sand');
        const txt = r.isError ? 'Error' : (r.mode === 'optimized' || r.mode === 'OPTIMIZED' ? 'Optimized' : 'Sandboxed');
        return `<tr><td>#${r.run}</td><td>${r.time}</td><td>${r.tokens}</td><td><span class="exec-badge ${cls}">${txt}</span></td></tr>`;
      }).join('');
    }
  }

  // Line chart SVG
  renderRmTimeChart();
}

function renderRmTimeChart() {
  const path  = document.getElementById('rm-time-path');
  const dots  = document.getElementById('rm-time-dots');
  const empty = document.getElementById('rm-chart-empty');
  const label = document.getElementById('rm-chart-label');
  if (!path) return;

  const times = state.timings.slice(-12);
  if (!times.length) { path.setAttribute('points',''); if (dots) dots.innerHTML = ''; if (empty) empty.style.display = ''; return; }
  if (empty) empty.style.display = 'none';

  const W = 360, H = 80, padX = 20, padY = 8;
  const maxT = Math.max(...times, 5);
  const xStep = times.length > 1 ? (W - padX*2) / (times.length - 1) : 0;
  const yScale = v => H - padY - (v / maxT) * (H - padY*2);

  const pts = times.map((t, i) => `${padX + i * xStep},${yScale(t)}`).join(' ');
  path.setAttribute('points', pts);

  if (dots) {
    dots.innerHTML = times.map((t, i) => `<circle cx="${padX + i * xStep}" cy="${yScale(t)}" r="2.5" fill="var(--blue)"/>`).join('');
  }

  if (label) label.textContent = `Last ${times.length} runs`;
}

// ── Settings ──────────────────────────────────────────────────────
function toggleSetting(btn) {
  btn.classList.toggle('on');
}

function saveSettings() {
  const threshold = parseFloat(document.getElementById('cfg-threshold')?.value || 0.8);
  const url = document.getElementById('cfg-server-url')?.value || SERVER;
  appendOutput('sys', `Settings saved. Threshold: ${threshold.toFixed(2)}, Server: ${url}`);
  switchBottomTab('output', document.querySelector('.bottom-tab'));
  switchView('editor');
}

function resetSettings() {
  const th = document.getElementById('cfg-threshold');
  const thv = document.getElementById('cfg-threshold-val');
  if (th)  th.value = 0.8;
  if (thv) thv.textContent = '0.80';
}

// ── Docs ──────────────────────────────────────────────────────────
function showDoc(section, el) {
  document.querySelectorAll('.docs-section').forEach(s => s.style.display = 'none');
  const sec = document.getElementById('doc-' + section);
  if (sec) sec.style.display = '';

  // Update nav highlight
  if (el) {
    document.querySelectorAll('#nav-docs .nav-item').forEach(i => i.classList.remove('active'));
    el.classList.add('active');
  }
}
