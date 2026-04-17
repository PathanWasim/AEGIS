// src/components/panels/TokenPanel.jsx
import { useStore } from '../../store/useStore'
import s from './TokenPanel.module.css'

const CAT_COLORS = {
  keyword:    s.keyword,
  operator:   s.operator,
  identifier: s.identifier,
  literal:    s.literal,
  structural: s.structural,
}

export default function TokenPanel() {
  const tokens = useStore(st => st.result?.tokens ?? [])
  const visible = tokens.filter(t => t.type !== 'EOF' && t.type !== 'NEWLINE')

  if (!visible.length) {
    return <div className={s.empty}>Run a program to see token stream.</div>
  }

  // Group by category
  const groups = {}
  visible.forEach(t => {
    if (!groups[t.category]) groups[t.category] = []
    groups[t.category].push(t)
  })

  return (
    <div className={s.panel}>
      <div className={s.summary}>
        {visible.length} tokens · {Object.keys(groups).length} categories
      </div>
      {Object.entries(groups).map(([cat, toks]) => (
        <div key={cat} className={s.group}>
          <div className={s.groupLabel}>{cat} ({toks.length})</div>
          <div className={s.chips}>
            {toks.map((t, i) => (
              <span
                key={i}
                className={`${s.chip} ${CAT_COLORS[cat] ?? ''}`}
                title={`${t.type}  L${t.line}:${t.column}`}
              >
                {t.value}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
