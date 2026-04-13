import { useRef, useEffect, useState } from 'react'
import s from './BottomPanel.module.css'
import { AlertCircle } from 'lucide-react'
import ASTViewer from './ASTViewer'

const TABS = [
  { id: 'terminal',   label: 'TERMINAL'   },
  { id: 'problems',   label: 'PROBLEMS'   },
  { id: 'metrics',    label: 'METRICS'    },
  { id: 'violations', label: 'VIOLATIONS' },
  { id: 'ast',        label: 'AST'        },
  { id: 'bytecode',   label: 'BYTECODE'   },
  { id: 'ir',         label: 'IR / TAC'   },
  { id: 'debug',      label: 'DEBUGGER'   },
]

export default function BottomPanel({
  height,
  activeTab, onTabChange,
  terminalLines, problems, violations, metrics,
  astData, bytecodeData, irData, debugSteps,
}) {
  const terminalRef = useRef(null)
  const [debugStep, setDebugStep] = useState(0)

  useEffect(() => {
    if (terminalRef.current) terminalRef.current.scrollTop = terminalRef.current.scrollHeight
  }, [terminalLines])

  useEffect(() => { setDebugStep(0) }, [debugSteps])

  const curStep = debugSteps?.[debugStep]

  return (
    <div className={s.panel} style={{ height, flexShrink: 0 }}>
      {/* ── Tab header ── */}
      <div className={s.header}>
        {TABS.map(t => (
          <button
            key={t.id}
            className={`${s.tab} ${activeTab === t.id ? s.tabActive : ''}`}
            onClick={() => onTabChange(t.id)}
          >
            {t.label}
            {t.id === 'problems'   && problems.length   > 0 && <span className={s.badge}>{problems.length}</span>}
            {t.id === 'violations' && violations.length > 0 && <span className={s.badge} style={{ background: '#ca3a31' }}>{violations.length}</span>}
            {t.id === 'ast'        && astData?.length       > 0 && <span className={s.badge} style={{ background: '#007acc' }}>{astData.length}</span>}
          </button>
        ))}
      </div>

      {/* ── TERMINAL ── */}
      {activeTab === 'terminal' && (
        <div className={s.body} ref={terminalRef}>
          {terminalLines.map((line, i) => (
            <div key={i} className={`${s.termLine} ${s['term_' + line.type]}`}>
              {line.type === 'out'    && <span className={s.prompt} style={{ color: '#89d185' }}>›</span>}
              {line.type === 'err'    && <span className={s.prompt} style={{ color: '#f48771' }}>✗</span>}
              {line.type === 'secerr' && <span className={s.prompt} style={{ color: '#f48771' }}>⚠</span>}
              {(line.type === 'meta' || line.type === 'info') && <span className={s.prompt} style={{ color: '#858585' }}>#</span>}
              <span>{line.text}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── PROBLEMS ── */}
      {activeTab === 'problems' && (
        <div className={s.body}>
          {problems.length === 0
            ? <div className={s.empty}>No problems detected.</div>
            : problems.map(p => (
                <div key={p.id} className={s.probRow}>
                  <AlertCircle size={13} className={s.errIcon} />
                  <span className={s.probMsg}>{p.msg}</span>
                  <span className={s.probLoc}>{p.file}</span>
                </div>
              ))
          }
        </div>
      )}

      {/* ── METRICS ── */}
      {activeTab === 'metrics' && (
        <div className={`${s.body} ${s.metricsBody}`}>
          {metrics == null
            ? <div className={s.empty}>Run a program to see execution metrics.</div>
            : (
              <div className={s.metricGrid}>
                <MetricCard label="Execution Time"  value={metrics.time}     />
                <MetricCard label="Tokens Parsed"   value={metrics.tokens}   />
                <MetricCard label="Optimized"       value={metrics.optimized} color={metrics.optimized === 'Yes' ? '#89d185' : '#858585'} />
                <MetricCard label="Code Hash"       value={'#' + metrics.hash} mono />
                {metrics.pipeline && (
                  <div className={s.pipelineCard}>
                    <div className={s.metLabel}>Pipeline Stages</div>
                    {Object.entries(metrics.pipeline).map(([stage, passed]) => (
                      <div key={stage} className={s.stageRow}>
                        <span className={passed ? s.stageOk : s.stageFail}>{passed ? '✓' : '✗'}</span>
                        <span className={s.stageName}>{stage}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          }
        </div>
      )}

      {/* ── VIOLATIONS ── */}
      {activeTab === 'violations' && (
        <div className={`${s.body} ${s.violBody}`}>
          {violations.length === 0
            ? <div className={s.empty}>No security violations recorded.</div>
            : (
              <table className={s.violTable}>
                <thead>
                  <tr><th>#</th><th>Time</th><th>File</th><th>Type</th><th>Message</th></tr>
                </thead>
                <tbody>
                  {violations.map(v => (
                    <tr key={v.id}>
                      <td className={s.num}>{v.id}</td>
                      <td className={s.mono}>{v.ts}</td>
                      <td className={s.mono}>{v.file}</td>
                      <td><span className={s.violType}>{v.type}</span></td>
                      <td className={s.violMsg}>{v.msg}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          }
        </div>
      )}

      {/* ── AST VIEWER ── */}
      {activeTab === 'ast' && (
        <div className={`${s.body} ${s.astBody}`}>
          {!astData || astData.length === 0
            ? <div className={s.empty}>Click the <strong>AST</strong> button in the toolbar to parse and visualize the abstract syntax tree.</div>
            : <ASTViewer nodes={astData} />
          }
        </div>
      )}

      {/* ── BYTECODE ── */}
      {activeTab === 'bytecode' && (
        <div className={`${s.body} ${s.codeBody}`}>
          {!bytecodeData || bytecodeData.length === 0
            ? <div className={s.empty}>Click <strong>Bytecode</strong> to compile and see the AEGIS VM instruction listing.</div>
            : (
              <table className={s.bcTable}>
                <thead>
                  <tr><th>ADDR</th><th>OPCODE</th><th>ARG</th></tr>
                </thead>
                <tbody>
                  {bytecodeData.map((instr, i) => (
                    <tr key={i} className={instr.opcode === 'HALT' ? s.haltRow : ''}>
                      <td className={`${s.num} ${s.mono}`}>{i.toString().padStart(4, '0')}</td>
                      <td className={s.opcode}>{instr.opcode}</td>
                      <td className={`${s.mono} ${s.arg}`}>{instr.arg ?? ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          }
        </div>
      )}

      {/* ── IR / TAC ── */}
      {activeTab === 'ir' && (
        <div className={`${s.body} ${s.codeBody}`}>
          {!irData || irData.length === 0
            ? <div className={s.empty}>Click <strong>IR</strong> to generate Three-Address Code intermediate representation.</div>
            : (
              <div className={s.irBlock}>
                <div className={s.irHeader}>Three-Address Code (TAC) · {irData.length} instructions</div>
                {irData.map((line, i) => (
                  <div key={i} className={s.irLine}>
                    <span className={s.irIdx}>{i.toString().padStart(2, '0')}</span>
                    <span className={irClass(line)}>{line}</span>
                  </div>
                ))}
              </div>
            )
          }
        </div>
      )}

      {/* ── DEBUGGER ── */}
      {activeTab === 'debug' && (
        <div className={s.body} style={{ padding: 0, overflow: 'hidden' }}>
          {!debugSteps || debugSteps.length === 0
            ? <div className={s.empty} style={{ padding: '8px 14px' }}>Click <strong>Debug</strong> to run the step-by-step execution trace.</div>
            : (
              <div className={s.debugWrap}>
                <div className={s.debugControls}>
                  <button className={s.dbBtn} onClick={() => setDebugStep(0)} disabled={debugStep === 0}>⏮</button>
                  <button className={s.dbBtn} onClick={() => setDebugStep(p => Math.max(0, p-1))} disabled={debugStep === 0}>← Prev</button>
                  <span className={s.dbCounter}>Step {debugStep + 1} / {debugSteps.length}</span>
                  <button className={s.dbBtn} onClick={() => setDebugStep(p => Math.min(debugSteps.length-1, p+1))} disabled={debugStep === debugSteps.length-1}>Next →</button>
                  <button className={s.dbBtn} onClick={() => setDebugStep(debugSteps.length - 1)} disabled={debugStep === debugSteps.length-1}>⏭</button>
                  <div className={s.dbNodeBadge}>{curStep?.node}</div>
                </div>
                {curStep && (
                  <div className={s.debugPanels}>
                    <div className={s.debugVars}>
                      <div className={s.debugLabel}>Variables</div>
                      {Object.keys(curStep.env).length === 0
                        ? <div className={s.debugEmpty}>No variables yet</div>
                        : Object.entries(curStep.env).map(([k, v]) => (
                            <div key={k} className={s.varRow}>
                              <span className={s.varName}>{k}</span>
                              <span className={s.varEq}>=</span>
                              <span className={s.varVal}>{JSON.stringify(v)}</span>
                            </div>
                          ))
                      }
                    </div>
                    <div className={s.debugOut}>
                      <div className={s.debugLabel}>Output so far</div>
                      {(!curStep.output || curStep.output.length === 0)
                        ? <div className={s.debugEmpty}>—</div>
                        : curStep.output.map((l, i) => <div key={i} className={s.outLine}>{l}</div>)
                      }
                      {curStep.error && <div className={s.dbErrLine}>⚠ {curStep.error}</div>}
                    </div>
                  </div>
                )}
              </div>
            )
          }
        </div>
      )}
    </div>
  )
}

function MetricCard({ label, value, color, mono }) {
  return (
    <div className="metCard" style={{ background: '#252526', border: '1px solid #3c3c3c', padding: '10px 14px' }}>
      <div style={{ fontSize: 10, textTransform: 'uppercase', color: '#858585', marginBottom: 4, letterSpacing: '0.06em' }}>{label}</div>
      <div style={{ fontSize: 20, fontFamily: mono ? 'Consolas,monospace' : 'inherit', color: color ?? '#cccccc' }}>{value}</div>
    </div>
  )
}

function irClass(line) {
  if (/^L\d+:$/.test(line.trim())) return s.irLabel
  if (/^(GOTO|IF_FALSE|PRINT)/i.test(line.trim())) return s.irKeyword
  return s.irInstr
}
