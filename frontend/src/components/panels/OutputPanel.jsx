// src/components/panels/OutputPanel.jsx
// Terminal-style output with timestamps, color-coded prefixes, and auto-scroll

import { useRef, useEffect } from 'react'
import { useStore } from '../../store/useStore'
import s from './OutputPanel.module.css'

const PREFIX = {
  out:    { sym: '›', cls: s.out    },
  err:    { sym: '✗', cls: s.err    },
  secerr: { sym: '⚠', cls: s.secerr },
  meta:   { sym: '─', cls: s.meta   },
  info:   { sym: '#', cls: s.info   },
  metric: { sym: '≡', cls: s.metric },
}

function TermLine({ line }) {
  const p = PREFIX[line.type] ?? PREFIX.info
  return (
    <div className={`${s.line} ${p.cls}`}>
      {line.ts && <span className={s.ts}>{line.ts}</span>}
      <span className={s.pfx}>{p.sym}</span>
      <span className={s.text}>{line.text}</span>
    </div>
  )
}

export default function OutputPanel() {
  const { terminalLines } = useStore()
  const ref = useRef(null)

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [terminalLines])

  return (
    <div className={s.panel} ref={ref}>
      {terminalLines.map((line, i) => <TermLine key={i} line={line} />)}
    </div>
  )
}
