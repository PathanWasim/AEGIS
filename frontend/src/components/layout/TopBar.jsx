// src/components/layout/TopBar.jsx
import { useNavigate, useLocation } from 'react-router-dom'
import { useStore } from '../../store/useStore'
import { api } from '../../services/api'
import s from './TopBar.module.css'

export default function TopBar({ onRun }) {
  const navigate   = useNavigate()
  const location   = useLocation()
  const { running, serverOnline, result, trustHistory } = useStore()

  const mode  = result?.execution_mode ?? 'interpreter'
  const trust = result?.trust_score ?? (trustHistory.at(-1)?.score ?? 0)

  const handleReset = async () => {
    await api.resetTrust()
    useStore.getState().setResult(null)
  }

  const nav = [
    { label: 'Playground', path: '/' },
    { label: 'Docs',       path: '/docs' },
    { label: 'About',      path: '/about' },
  ]

  return (
    <div className={s.bar}>
      <span className={s.title}>AEGIS</span>

      <div className={s.divider} />

      <button className={s.runBtn} onClick={onRun} disabled={running}>
        {running ? '⏳' : '▶'} {running ? 'Running' : 'Run'}
      </button>

      <div className={s.divider} />

      {/* Mode badge — interpreter=yellow, optimized=green, rollback/failed=red */}
      {result?.rollback
        ? <span className={`${s.modeBadge} ${s.rollback}`}>rollback</span>
        : <span className={`${s.modeBadge} ${s[mode]}`}>{mode}</span>
      }

      <span className={s.trustLabel}>trust</span>
      <span className={s.trustVal}>{trust.toFixed(3)}</span>
      <span className={s.trustLabel}>/1.000</span>

      <span className={s.spacer} />

      <span className={s.hint}>Ctrl+Enter to run</span>

      {nav.map(n => (
        <button
          key={n.path}
          className={`${s.navLink} ${location.pathname === n.path ? s.active : ''}`}
          onClick={() => navigate(n.path)}
        >
          {n.label}
        </button>
      ))}

      <div className={s.divider} />

      <button className={s.resetBtn} onClick={handleReset} title="Reset all trust scores to 0">
        Reset Trust
      </button>

      <div className={s.divider} />
      <div className={`${s.serverDot} ${serverOnline ? s.online : ''}`} />
      <span className={s.serverLabel}>{serverOnline ? 'Server' : 'Offline'}</span>
    </div>
  )
}
