import s from './Sidebar.module.css'
import { FileCode2 } from 'lucide-react'

export default function Sidebar({
  view, examples, onLoadExample, activeFile,
  trustScore, trustHistory, runCount, violations,
  execMode, onModeChange, onDemo, demoRunning,
}) {
  if (!view) return null
  return (
    <div className={s.sidebar}>
      {view === 'explorer' && (
        <ExplorerView
          examples={examples} onLoadExample={onLoadExample} activeFile={activeFile}
          onDemo={onDemo} demoRunning={demoRunning}
        />
      )}
      {view === 'trust' && (
        <TrustView trustScore={trustScore} trustHistory={trustHistory} runCount={runCount} violations={violations} />
      )}
      {view === 'settings' && (
        <SettingsView execMode={execMode} onModeChange={onModeChange} />
      )}
    </div>
  )
}

/* ── Explorer ──────────────────────────────────────────────── */
function ExplorerView({ examples, onLoadExample, activeFile, onDemo, demoRunning }) {
  return (
    <>
      <div className={s.title}>EXPLORER</div>
      <div className={s.section}>AEGIS PROJECT</div>
      {Object.entries(examples).map(([key, ex]) => (
        <div
          key={key}
          className={`${s.item} ${activeFile === ex.name ? s.itemActive : ''}`}
          onClick={() => onLoadExample(key)}
        >
          <FileCode2 size={14} className={s.fileIcon} />
          {ex.name}
        </div>
      ))}
      <div className={s.section} style={{ marginTop: 12 }}>DEMO</div>
      <div className={s.demoBox}>
        <div className={s.demoDesc}>
          Runs the current file 8× to show the trust score building from <strong>SANDBOXED</strong> → <strong>OPTIMIZED</strong> mode.
        </div>
        <button
          className={`${s.demoBtn} ${demoRunning ? s.demoBtnRunning : ''}`}
          onClick={onDemo}
          disabled={demoRunning}
        >
          {demoRunning ? '⏳ Running demo…' : '▶ Trust Build-Up Demo'}
        </button>
      </div>
    </>
  )
}

/* ── Trust ──────────────────────────────────────────────────── */
function TrustView({ trustScore, trustHistory, runCount, violations }) {
  const score  = trustScore ?? null
  const pct    = score != null ? Math.min(score * 100, 100) : 0
  const level  = trustLevel(score)
  const lvlCol = {
    TRUSTED: '#89d185', HIGH: '#89d185',
    MEDIUM: '#cca700', LOW: '#f48771',
    NONE: '#858585', 'NOT RUN': '#858585',
  }
  const color = lvlCol[level]

  return (
    <>
      <div className={s.title}>TRUST ANALYTICS</div>
      {/* Score block */}
      <div className={s.trustBlock}>
        <div className={s.trustScore} style={{ color }}>{score != null ? score.toFixed(3) : '—'}</div>
        <div className={s.trustLevel} style={{ color }}>{level}</div>
        <div className={s.barTrack}>
          <div className={s.barFill} style={{ width: `${pct}%`, background: color }} />
        </div>
      </div>
      {/* Stats */}
      <div className={s.statGrid}>
        <Row label="Total Runs"  value={runCount} />
        <Row label="Violations"  value={violations.length} valueColor={violations.length > 0 ? '#f48771' : undefined} />
        <Row label="Threshold"   value="0.800" />
        <Row label="Session"     value="Active" valueColor="#89d185" />
      </div>
      {/* Trust history sparkline */}
      {trustHistory.length > 1 && (
        <>
          <div className={s.section}>TRUST HISTORY</div>
          <TrustChart history={trustHistory} />
        </>
      )}
      {/* Thresholds */}
      <div className={s.section}>THRESHOLDS</div>
      {[['NONE','≥ 0.000'],['LOW','≥ 0.100'],['MEDIUM','≥ 0.300'],['HIGH','≥ 0.600'],['TRUSTED','≥ 0.800']].map(([lvl, min]) => (
        <div key={lvl} className={`${s.threshRow} ${level === lvl ? s.threshActive : ''}`}>
          <span>{lvl}</span><span className={s.threshVal}>{min}</span>
        </div>
      ))}
    </>
  )
}

/* ── Trust Chart (SVG sparkline) ───────────────────────────── */
function TrustChart({ history }) {
  const W = 210, H = 60, PAD = 6
  const vals = history.map(h => h.trust)
  const max  = Math.max(...vals, 1)
  const min  = 0
  const xs   = vals.map((_, i) => PAD + (i / Math.max(vals.length - 1, 1)) * (W - PAD * 2))
  const ys   = vals.map(v => H - PAD - ((v - min) / (max - min)) * (H - PAD * 2))

  const polyline = xs.map((x, i) => `${x},${ys[i]}`).join(' ')
  const threshold = H - PAD - (0.8 / max) * (H - PAD * 2)

  return (
    <div className={s.chartWrap}>
      <svg width={W} height={H} style={{ display: 'block' }}>
        {/* Threshold line */}
        <line x1={PAD} y1={threshold} x2={W - PAD} y2={threshold}
          stroke="#cca700" strokeWidth={1} strokeDasharray="3,3" />
        <text x={W - PAD + 1} y={threshold + 3} fill="#cca700" fontSize={8}>0.8</text>
        {/* Score line */}
        <polyline points={polyline} fill="none" stroke="#007acc" strokeWidth={1.5} />
        {/* Dots */}
        {xs.map((x, i) => (
          <circle key={i} cx={x} cy={ys[i]} r={2.5}
            fill={history[i].mode === 'optimized' ? '#89d185' : '#007acc'} />
        ))}
      </svg>
      <div className={s.chartLegend}>
        <span style={{ color: '#007acc' }}>● Sandboxed</span>
        <span style={{ color: '#89d185' }}>● Optimized</span>
      </div>
    </div>
  )
}

function Row({ label, value, valueColor }) {
  return (
    <div className={s.statRow}>
      <span className={s.statLabel}>{label}</span>
      <span className={s.statValue} style={valueColor ? { color: valueColor } : undefined}>{value}</span>
    </div>
  )
}

/* ── Settings ───────────────────────────────────────────────── */
function SettingsView({ execMode, onModeChange }) {
  return (
    <>
      <div className={s.title}>SETTINGS</div>
      <div className={s.section}>EXECUTION</div>
      <div className={s.settingRow}>
        <label className={s.settingLabel}>Execution Mode</label>
        <select className={s.select} value={execMode} onChange={e => onModeChange(e.target.value)}>
          <option value="sandboxed">Sandboxed — Safe</option>
          <option value="optimized">Optimized — Fast</option>
        </select>
      </div>
      <div className={s.section}>SECURITY</div>
      <div className={s.settingRow}>
        <label className={s.settingLabel}>Block Division by Zero</label>
        <select className={s.select} defaultValue="yes"><option value="yes">Enabled</option></select>
      </div>
      <div className={s.settingRow}>
        <label className={s.settingLabel}>Block Undefined Vars</label>
        <select className={s.select} defaultValue="yes"><option value="yes">Enabled</option></select>
      </div>
      <div className={s.section}>TRUST POLICY</div>
      <div className={s.settingRow}>
        <label className={s.settingLabel}>Trust Threshold</label>
        <input type="number" className={s.input} defaultValue="0.8" step="0.1" min="0" max="1" />
      </div>
    </>
  )
}

function trustLevel(score) {
  if (score == null) return 'NOT RUN'
  if (score >= 0.8)  return 'TRUSTED'
  if (score >= 0.6)  return 'HIGH'
  if (score >= 0.3)  return 'MEDIUM'
  if (score >= 0.1)  return 'LOW'
  return 'NONE'
}
