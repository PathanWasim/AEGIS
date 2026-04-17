// src/components/panels/PipelineView.jsx
import { useStore } from '../../store/useStore'
import s from './PipelineView.module.css'

// 7-stage pipeline matching the backend's pipeline_stages dict + execution mode
const STAGES = [
  { key: 'lexed',       label: 'LEXER',     desc: 'Tokenize source' },
  { key: 'parsed',      label: 'PARSER',    desc: 'Build AST' },
  { key: 'ast_built',   label: 'AST',       desc: 'Serialize tree' },
  { key: 'analyzed',    label: 'ANALYZER',  desc: 'Static check' },
  { key: 'interpreted', label: 'INTERP',    desc: 'Sandboxed exec' },
  { key: 'trust',       label: 'TRUST',     desc: 'Score update' },
  { key: 'optimized',   label: 'OPTIMIZED', desc: 'Cached exec' },
]

const STATE_ICON = { ok: '✓', error: '✗', blocked: '⊘', skipped: '–', idle: '○' }

export default function PipelineView() {
  const result = useStore(st => st.result)

  if (!result) {
    return <div className={s.empty}>Run a program to see the pipeline execution trace.</div>
  }

  const stages  = result.pipeline_stages ?? {}
  const mode    = result.execution_mode
  const issues  = result.issues ?? []
  const hasHigh = issues.some(i => i.severity === 'HIGH')
  const metrics = result.metrics ?? {}

  function stageState(key) {
    // Optimized stage only active when mode is optimized
    if (key === 'optimized') {
      if (mode === 'optimized' && stages.optimized) return 'ok'
      if (mode === 'interpreter') return 'skipped'
      return 'idle'
    }
    // Trust stage: always attempted, blocked if HIGH issues
    if (key === 'trust') {
      if (!stages.analyzed) return 'idle'
      return hasHigh ? 'blocked' : 'ok'
    }
    // Interpreter: ok if ran, skipped if optimized ran instead
    if (key === 'interpreted') {
      if (stages.interpreted) return 'ok'
      if (stages.optimized)   return 'skipped'
      if (result.success === false && stages.analyzed) return 'error'
      return 'idle'
    }
    if (stages[key]) return 'ok'
    // If result failed and prior stages succeeded, this is the failure point
    if (result.success === false) return 'error'
    return 'idle'
  }

  return (
    <div className={s.panel}>
      {/* Stage diagram */}
      <div className={s.pipeline}>
        {STAGES.map((stage, idx) => {
          const state = stageState(stage.key)
          return (
            <div key={stage.key} className={s.stageWrap}>
              <div className={`${s.stage} ${s[state]}`}>
                <div className={s.indicator}>{STATE_ICON[state]}</div>
                <div className={s.stageLabel}>{stage.label}</div>
                <div className={s.stageDesc}>{stage.desc}</div>
              </div>
              {idx < STAGES.length - 1 && (
                <div className={`${s.arrow} ${state === 'ok' ? s.arrowOk : ''} ${state === 'skipped' ? s.arrowSkip : ''}`}>
                  →
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Static analysis issues */}
      {issues.length > 0 && (
        <div className={s.issueList}>
          <div className={s.issueHeader}>Static Analysis Issues</div>
          {issues.map((iss, i) => (
            <div key={i} className={`${s.issue} ${s['sev_' + iss.severity]}`}>
              <span className={s.sevBadge}>{iss.severity}</span>
              <span className={s.issueLine}>L{iss.line}</span>
              <span className={s.issueType}>{iss.type}</span>
              <span className={s.issueMsg}>{iss.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Metrics + mode bar */}
      <div className={s.modeInfo}>
        <span className={s.modeLabel}>Mode</span>
        <span className={`${s.modeVal} ${s['mode_' + (result.rollback ? 'rollback' : mode)]}`}>
          {result.rollback ? 'ROLLBACK' : mode?.toUpperCase()}
        </span>

        <span className={s.sep}>|</span>
        <span className={s.modeLabel}>Trust</span>
        <span className={s.modeVal}>{result.trust_score?.toFixed(3)}</span>

        <span className={s.sep}>|</span>
        <span className={s.modeLabel}>Time</span>
        <span className={s.modeVal}>{result.execution_time_ms}ms</span>

        {metrics.instruction_count !== undefined && (
          <>
            <span className={s.sep}>|</span>
            <span className={s.modeLabel}>Instructions</span>
            <span className={s.modeVal}>{metrics.instruction_count}</span>
          </>
        )}
      </div>
    </div>
  )
}
