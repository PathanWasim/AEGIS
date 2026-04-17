// src/components/layout/Sidebar.jsx
import { useEffect } from 'react'
import { useStore } from '../../store/useStore'
import { api } from '../../services/api'
import s from './Sidebar.module.css'

export default function Sidebar() {
  const { examples, setExamples, setCode, result, trustHistory } = useStore()

  useEffect(() => {
    api.examples().then(d => d.examples && setExamples(d.examples)).catch(() => {})
  }, [setExamples])

  const trust = result?.trust_score ?? (trustHistory.at(-1)?.score ?? 0)
  const mode  = result?.execution_mode ?? 'interpreter'
  const pct   = Math.min(100, (trust / 1.0) * 100)

  return (
    <div className={s.sidebar}>
      {/* Trust summary */}
      <div className={s.trustBox}>
        <div className={s.trustTitle}>Trust Score</div>
        <div className={s.trustBar}>
          <div className={s.trustFill} style={{ width: `${pct}%` }} />
        </div>
        <div className={s.trustMeta}>
          <span className={s.trustScore}>{trust.toFixed(3)}</span>
          <span>{mode.toUpperCase()}</span>
        </div>
      </div>

      {/* Examples */}
      <div className={s.section}>
        <div className={s.sectionHeader}>Examples</div>
        {examples.map(ex => (
          <button
            key={ex.id}
            className={s.item}
            onClick={() => setCode(ex.code)}
            title={ex.description}
          >
            <span className={`${s.dot} ${ex.id === 'security_violation' ? s.violation : s.safe}`} />
            {ex.name}
          </button>
        ))}
      </div>
    </div>
  )
}
