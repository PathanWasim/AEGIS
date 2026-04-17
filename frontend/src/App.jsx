// src/App.jsx — root: routing, health poll, run orchestration
import { useEffect, useCallback } from 'react'
import { Routes, Route, BrowserRouter } from 'react-router-dom'
import { useStore } from './store/useStore'
import { api } from './services/api'
import TopBar from './components/layout/TopBar'
import Playground from './pages/Playground'
import Docs from './pages/Docs'
import About from './pages/About'
import './index.css'
import s from './App.module.css'

function ts() {
  const d = new Date()
  return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`
}

function line(type, text) { return { type, text, ts: ts() } }

export default function App() {
  const {
    code, setRunning, setResult, setServerOnline,
    addLine, incRunCount, appendTrust, setBottomTab, runCount,
  } = useStore()

  // Health check — poll every 8s
  useEffect(() => {
    const check = () =>
      api.health()
        .then(d => setServerOnline(d.status === 'ok'))
        .catch(() => setServerOnline(false))
    check()
    const id = setInterval(check, 8000)
    return () => clearInterval(id)
  }, [setServerOnline])

  // ── Run handler ─────────────────────────────────────────────────────────────
  const handleRun = useCallback(async () => {
    if (!code.trim()) return
    setRunning(true)
    setBottomTab('terminal')

    const runNum = runCount + 1
    addLine({ type: 'meta', text: `─── Run #${runNum} ─────────────────────────────────`, ts: ts() })

    try {
      const result = await api.execute(code)

      // Validate response shape — all fields must be present
      if (result.error && !result.output) result.output = []
      if (!Array.isArray(result.output)) result.output = []

      setResult(result)
      incRunCount()

      // Program output lines
      if (result.output.length > 0) {
        result.output.forEach(txt => addLine(line('out', txt)))
      } else if (!result.error) {
        addLine(line('info', '(no output)'))
      }

      // Error lines
      if (result.error) {
        const errType = result.rollback ? 'secerr' : (result.execution_mode === 'failed' ? 'err' : 'secerr')
        addLine(line(errType, result.error))
      }

      // Rollback notice
      if (result.rollback) {
        addLine(line('secerr', '⚠ ROLLBACK — violation in optimized mode. Trust reset to 0.0. Reverted to interpreter.'))
      }

      // Summary line
      const modeLabel = result.execution_mode === 'optimized' ? '⚡ OPTIMIZED' : '🔒 INTERPRETER'
      addLine(line('meta',
        `Exit ${result.success ? 0 : 1} · ${result.execution_time_ms}ms · ${modeLabel} · trust ${result.trust_score?.toFixed(3)}`
      ))

      // Metrics block (if available)
      const m = result.metrics ?? {}
      if (m.instruction_count !== undefined) {
        addLine(line('metric',
          `[METRICS] Instructions: ${m.instruction_count}  Arithmetic: ${m.arithmetic_ops}  ` +
          `Assignments: ${m.assignment_ops}  Prints: ${m.print_ops}  Time: ${m.execution_time_ms}ms`
        ))
      }

      // Violations
      if (result.violations?.length) {
        result.violations.forEach(v => addLine(line('secerr', `[VIOLATION] ${v}`)))
      }

      // Trust history for chart
      appendTrust({ run: runNum, score: result.trust_score ?? 0, mode: result.execution_mode })

    } catch (err) {
      // Network / parse error — never crash the UI
      addLine(line('err', `Connection error: ${err.message}`))
    } finally {
      setRunning(false)
    }
  }, [code, runCount, setRunning, setResult, addLine, incRunCount, appendTrust, setBottomTab])

  return (
    <BrowserRouter>
      <div className={s.shell}>
        <TopBar onRun={handleRun} />
        <div className={s.body}>
          <Routes>
            <Route path="/"      element={<Playground onRun={handleRun} />} />
            <Route path="/docs"  element={<Docs />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}
