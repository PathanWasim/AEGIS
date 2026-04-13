// ─────────────────────────────────────────────────────────────────────────────
// AEGIS IDE — App.jsx  (full rewrite with bytecode / IR / AST / debug / demo)
// ─────────────────────────────────────────────────────────────────────────────
import { useState, useCallback, useEffect } from 'react'
import ActivityBar  from './components/ActivityBar'
import Sidebar      from './components/Sidebar'
import EditorPane   from './components/EditorPane'
import BottomPanel  from './components/BottomPanel'
import StatusBar    from './components/StatusBar'
import './App.css'

const SERVER = ''  // Vite proxy → Flask :5000

const EXAMPLES = {
  fibonacci: {
    name: 'fibonacci.aegis',
    code: `a = 0\nb = 1\ncount = 0\nwhile count < 10\n  print a\n  temp = a + b\n  a = b\n  b = temp\n  count = count + 1\nend`,
  },
  hello: {
    name: 'hello_world.aegis',
    code: `x = 42\nprint x`,
  },
  security_demo: {
    name: 'security_demo.aegis',
    code: `x = 10\ny = 0\nresult = x / y\nprint result`,
  },
  sum: {
    name: 'sum_1_to_100.aegis',
    code: `total = 0\ni = 1\nwhile i <= 100\n  total = total + i\n  i = i + 1\nend\nprint total`,
  },
  counter: {
    name: 'counter.aegis',
    code: `i = 1\nwhile i <= 5\n  print i\n  i = i + 1\nend`,
  },
  trust_demo: {
    name: 'trust_demo.aegis',
    code: `# Run this repeatedly to watch trust score build!\n# First runs: SANDBOXED  →  later: OPTIMIZED\ntotal = 0\ni = 1\nwhile i <= 10\n  total = total + i\n  i = i + 1\nend\nprint total`,
  },
}

export default function App() {
  // ── UI state ───────────────────────────────────────────────────
  const [activePanel, setActivePanel] = useState('explorer')
  const [bottomTab,   setBottomTab]   = useState('terminal')

  // ── Editor / execution state ───────────────────────────────────
  const [code,          setCode]         = useState(EXAMPLES.fibonacci.code)
  const [activeFile,    setActiveFile]   = useState('fibonacci.aegis')
  const [execMode,      setExecMode]     = useState('sandboxed')
  const [serverOnline,  setServerOnline] = useState(false)
  const [running,       setRunning]      = useState(false)

  // ── Output state ───────────────────────────────────────────────
  const [terminalLines, setTerminalLines] = useState([
    { type: 'info', text: 'AEGIS Execution Host ready. Press ▶ Run to execute.' },
    { type: 'info', text: 'Use AST / Bytecode / IR / Debug buttons for compiler views.' },
  ])
  const [problems,    setProblems]   = useState([])
  const [violations,  setViolations] = useState([])
  const [metrics,     setMetrics]    = useState(null)

  // ── Compiler view state ────────────────────────────────────────
  const [astData,      setAstData]     = useState([])
  const [bytecodeData, setBytecodeData] = useState([])
  const [irData,       setIrData]      = useState([])
  const [debugSteps,   setDebugSteps]  = useState([])

  // ── Trust / stats ──────────────────────────────────────────────
  const [trustScore,   setTrustScore]  = useState(null)
  const [trustHistory, setTrustHistory] = useState([])  // [{run, trust, mode}]
  const [runCount,     setRunCount]    = useState(0)
  const [errorCount,   setErrorCount]  = useState(0)
  const [tokens,       setTokens]      = useState([])

  // ── Demo mode state ────────────────────────────────────────────
  const [demoRunning,  setDemoRunning] = useState(false)

  // ── Server health poll ─────────────────────────────────────────
  const checkServer = useCallback(async () => {
    try {
      const r = await fetch(`${SERVER}/api/health`, { signal: AbortSignal.timeout(2000) })
      setServerOnline(r.ok)
    } catch { setServerOnline(false) }
  }, [])

  useEffect(() => {
    checkServer()
    const id = setInterval(checkServer, 10_000)
    return () => clearInterval(id)
  }, [checkServer])

  // ── Load example ───────────────────────────────────────────────
  const loadExample = useCallback((key) => {
    const ex = EXAMPLES[key]
    if (!ex) return
    setCode(ex.code)
    setActiveFile(ex.name)
    setProblems([])
    setAstData([])
    setBytecodeData([])
    setIrData([])
    setDebugSteps([])
  }, [])

  // ── Run code ───────────────────────────────────────────────────
  const runCode = useCallback(async () => {
    if (!code.trim() || running) return
    setRunning(true)
    setProblems([])
    setBottomTab('terminal')

    const t0 = performance.now()
    setTerminalLines(prev => [
      ...prev,
      { type: 'info', text: `\n─── Running ${activeFile} (${execMode}) ─────────────────` },
    ])

    try {
      const res  = await fetch(`${SERVER}/api/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, verbose: false }),
      })
      const data = await res.json()
      const ms   = data.execution_time_ms ?? (performance.now() - t0).toFixed(1)
      const isOk = data.success
      const isSecErr = !isOk && data.error && /division by zero|undefined|overflow|security/i.test(data.error)

      const newLines = []
      if (data.output?.length) data.output.forEach(l => newLines.push({ type: 'out', text: l }))
      if (data.error) newLines.push({ type: isSecErr ? 'secerr' : 'err', text: data.error })
      if (!data.output?.length && !data.error) newLines.push({ type: 'info', text: '(no output)' })

      const trustVal = data.trust_score ?? null
      const modeLine = data.optimized ? '⚡ OPTIMIZED' : '🔒 SANDBOXED'
      newLines.push({ type: 'meta', text: `Exit ${isOk ? 0 : 1} · ${ms}ms · ${modeLine} · trust ${trustVal?.toFixed(3) ?? '—'}` })

      setTerminalLines(prev => [...prev, ...newLines])
      const newCount = runCount + 1
      setRunCount(newCount)
      if (!isOk) setErrorCount(c => c + 1)

      if (data.error) {
        setProblems([{ id: Date.now(), severity: 'error', msg: data.error, file: activeFile, loc: '—' }])
        if (isSecErr) setBottomTab('violations')
      }

      if (isSecErr) {
        setViolations(prev => [
          { id: prev.length + 1, ts: new Date().toLocaleTimeString(), file: activeFile, type: classifyViolation(data.error), msg: data.error },
          ...prev,
        ])
      }

      setMetrics({
        time: `${ms}ms`, tokens: data.tokens?.length ?? '—',
        optimized: data.optimized ? 'Yes' : 'No',
        mode: data.optimized ? 'optimized' : execMode,
        hash: data.code_hash ?? '—',
        pipeline: data.pipeline_stages ?? null,
      })

      if (data.tokens?.length) setTokens(data.tokens)
      if (trustVal != null) {
        setTrustScore(trustVal)
        setTrustHistory(prev => [...prev, { run: newCount, trust: trustVal, mode: data.optimized ? 'optimized' : 'sandboxed' }])
      }
    } catch (err) {
      setTerminalLines(prev => [...prev, { type: 'err', text: `Connection error: ${err.message}` }])
      setErrorCount(c => c + 1)
    } finally {
      setRunning(false)
    }
  }, [code, running, activeFile, execMode, runCount])

  // ── Keyboard shortcut ──────────────────────────────────────────
  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); runCode() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [runCode])

  // ── AST parse ─────────────────────────────────────────────────
  const parseAST = useCallback(async () => {
    try {
      const res  = await fetch(`${SERVER}/api/parse`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const data = await res.json()
      if (data.success) {
        setAstData(data.ast)
        setBottomTab('ast')
        setTerminalLines(prev => [...prev, { type: 'info', text: `[AST] Parsed ${data.node_count} top-level nodes.` }])
      } else {
        setTerminalLines(prev => [...prev, { type: 'err', text: `[AST] ${data.error}` }])
      }
    } catch (e) {
      setTerminalLines(prev => [...prev, { type: 'err', text: `[AST] Connection error: ${e.message}` }])
    }
  }, [code])

  // ── Bytecode compile ───────────────────────────────────────────
  const compileBytecode = useCallback(async () => {
    try {
      const res  = await fetch(`${SERVER}/api/bytecode`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const data = await res.json()
      if (data.success) {
        setBytecodeData(data.instructions)
        setBottomTab('bytecode')
        setTerminalLines(prev => [...prev, { type: 'info', text: `[BC] Compiled ${data.count} instructions.` }])
      } else {
        setTerminalLines(prev => [...prev, { type: 'err', text: `[BC] ${data.error}` }])
      }
    } catch (e) {
      setTerminalLines(prev => [...prev, { type: 'err', text: `[BC] Connection error: ${e.message}` }])
    }
  }, [code])

  // ── IR / TAC ──────────────────────────────────────────────────
  const generateIR = useCallback(async () => {
    try {
      const res  = await fetch(`${SERVER}/api/ir`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const data = await res.json()
      if (data.success) {
        setIrData(data.ir)
        setBottomTab('ir')
        setTerminalLines(prev => [...prev, { type: 'info', text: `[IR] Generated ${data.count} TAC instructions.` }])
      } else {
        setTerminalLines(prev => [...prev, { type: 'err', text: `[IR] ${data.error}` }])
      }
    } catch (e) {
      setTerminalLines(prev => [...prev, { type: 'err', text: `[IR] Connection error: ${e.message}` }])
    }
  }, [code])

  // ── Debug trace ───────────────────────────────────────────────
  const runDebug = useCallback(async () => {
    try {
      const res  = await fetch(`${SERVER}/api/debug`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const data = await res.json()
      if (data.success) {
        setDebugSteps(data.steps)
        setBottomTab('debug')
        setTerminalLines(prev => [...prev, { type: 'info', text: `[DBG] Trace recorded — ${data.total} steps.` }])
      } else {
        setTerminalLines(prev => [...prev, { type: 'err', text: `[DBG] ${data.error}` }])
      }
    } catch (e) {
      setTerminalLines(prev => [...prev, { type: 'err', text: `[DBG] Connection error: ${e.message}` }])
    }
  }, [code])

  // ── Demo mode: run multiple times to show trust build-up ──────
  const runDemo = useCallback(async () => {
    if (demoRunning) return
    setDemoRunning(true)
    setBottomTab('terminal')
    setTerminalLines(prev => [
      ...prev,
      { type: 'info', text: '\n════ DEMO MODE: Trust Build-Up ════════════════════════' },
      { type: 'info', text: 'Running the same code 8× to show SANDBOXED → OPTIMIZED transition...' },
    ])

    try {
      const res  = await fetch(`${SERVER}/api/demo`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, runs: 8 }),
      })
      const data = await res.json()
      if (data.success) {
        const newHistory = []
        for (const r of data.runs) {
          const icon = r.optimized ? '⚡' : '🔒'
          const lvl  = r.trust_level ?? '—'
          setTerminalLines(prev => [...prev, {
            type: r.optimized ? 'out' : 'info',
            text: `  Run ${r.run}: ${icon} ${r.mode?.toUpperCase()} | trust=${r.trust} (${lvl}) | ${r.time_ms}ms`,
          }])
          newHistory.push({ run: runCount + r.run, trust: r.trust, mode: r.mode })
          if (r.trust != null) setTrustScore(r.trust)
        }
        setTrustHistory(prev => [...prev, ...newHistory])
        setRunCount(c => c + data.runs.length)
        const lastMode = data.runs[data.runs.length - 1]?.mode
        setTerminalLines(prev => [...prev,
          { type: 'info', text: `════ Demo complete. Final mode: ${lastMode?.toUpperCase()} ═══════════════` },
        ])
      }
    } catch (e) {
      setTerminalLines(prev => [...prev, { type: 'err', text: `Demo error: ${e.message}` }])
    } finally {
      setDemoRunning(false)
    }
  }, [code, demoRunning, runCount])

  return (
    <div className="shell">
      <div className="workbench">
        <ActivityBar active={activePanel} onSwitch={setActivePanel} />
        <Sidebar
          view={activePanel}
          examples={EXAMPLES}
          onLoadExample={loadExample}
          activeFile={activeFile}
          trustScore={trustScore}
          trustHistory={trustHistory}
          runCount={runCount}
          violations={violations}
          execMode={execMode}
          onModeChange={setExecMode}
          onDemo={runDemo}
          demoRunning={demoRunning}
        />
        <div className="editor-area">
          <EditorPane
            code={code}
            onChange={setCode}
            activeFile={activeFile}
            onRun={runCode}
            running={running}
            onParseAST={parseAST}
            onBytecode={compileBytecode}
            onIR={generateIR}
            onDebug={runDebug}
          />
          <BottomPanel
            activeTab={bottomTab}
            onTabChange={setBottomTab}
            terminalLines={terminalLines}
            problems={problems}
            violations={violations}
            metrics={metrics}
            astData={astData}
            bytecodeData={bytecodeData}
            irData={irData}
            debugSteps={debugSteps}
            code={code}
          />
        </div>
      </div>
      <StatusBar
        serverOnline={serverOnline}
        trustScore={trustScore}
        execMode={execMode}
        runCount={runCount}
        errorCount={errorCount}
        activeFile={activeFile}
      />
    </div>
  )
}

function classifyViolation(msg) {
  if (/division by zero/i.test(msg)) return 'Division by Zero'
  if (/undefined/i.test(msg))       return 'Undefined Variable'
  if (/overflow/i.test(msg))        return 'Integer Overflow'
  return 'Security Error'
}
