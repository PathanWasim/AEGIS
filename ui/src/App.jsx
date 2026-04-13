// ─────────────────────────────────────────────────────────────────────────────
// AEGIS IDE — App.jsx
// Features: multi-tab editor, resizable bottom panel, full compiler views
// ─────────────────────────────────────────────────────────────────────────────
import { useState, useCallback, useEffect, useRef } from 'react'
import ActivityBar  from './components/ActivityBar'
import Sidebar      from './components/Sidebar'
import EditorPane   from './components/EditorPane'
import BottomPanel  from './components/BottomPanel'
import StatusBar    from './components/StatusBar'
import './App.css'

const SERVER = ''

const EXAMPLES = {
  fibonacci:     { name: 'fibonacci.aegis',     code: `a = 0\nb = 1\ncount = 0\nwhile count < 10\n  print a\n  temp = a + b\n  a = b\n  b = temp\n  count = count + 1\nend` },
  hello:         { name: 'hello_world.aegis',   code: `x = 42\nprint x` },
  security_demo: { name: 'security_demo.aegis', code: `x = 10\ny = 0\nresult = x / y\nprint result` },
  sum:           { name: 'sum_1_to_100.aegis',  code: `total = 0\ni = 1\nwhile i <= 100\n  total = total + i\n  i = i + 1\nend\nprint total` },
  counter:       { name: 'counter.aegis',       code: `i = 1\nwhile i <= 5\n  print i\n  i = i + 1\nend` },
  trust_demo:    { name: 'trust_demo.aegis',    code: `# Run repeatedly: SANDBOXED → OPTIMIZED\ntotal = 0\ni = 1\nwhile i <= 10\n  total = total + i\n  i = i + 1\nend\nprint total` },
  ifelse:        { name: 'if_else_demo.aegis',  code: `x = 15\nif x > 10\n  print x\nelse\n  print 0\nend` },
}

export default function App() {
  // ── Multi-tab state ────────────────────────────────────────────
  const [tabs,          setTabs]          = useState([
    { key: 'fibonacci', name: 'fibonacci.aegis', code: EXAMPLES.fibonacci.code }
  ])
  const [activeTabKey,  setActiveTabKey]  = useState('fibonacci')

  const activeTab = tabs.find(t => t.key === activeTabKey) ?? tabs[0]
  const code      = activeTab?.code ?? ''

  // ── UI state ───────────────────────────────────────────────────
  const [activePanel,   setActivePanel]   = useState('explorer')
  const [bottomTab,     setBottomTab]     = useState('terminal')

  // ── Resizable bottom panel ─────────────────────────────────────
  const [bottomH,  setBottomH]  = useState(240)
  const dragRef    = useRef(null)
  const editorArea = useRef(null)

  const startDrag = useCallback((e) => {
    e.preventDefault()
    const startY = e.clientY
    const startH = bottomH
    const onMove = (mv) => {
      const delta = startY - mv.clientY
      setBottomH(Math.max(120, Math.min(startH + delta, 600)))
    }
    const onUp = () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup',   onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.body.style.cursor     = 'row-resize'
    document.body.style.userSelect = 'none'
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup',   onUp)
  }, [bottomH])

  // ── Server state ───────────────────────────────────────────────
  const [serverOnline,  setServerOnline]  = useState(false)
  const [running,       setRunning]       = useState(false)

  // ── Output state ───────────────────────────────────────────────
  const [terminalLines, setTerminalLines] = useState([
    { type: 'info', text: 'AEGIS Execution Host ready. Press ▶ Run to execute.' },
    { type: 'info', text: 'Use AST / Bytecode / IR / Debug toolbar buttons for compiler views.' },
  ])
  const [problems,    setProblems]   = useState([])
  const [violations,  setViolations] = useState([])
  const [metrics,     setMetrics]    = useState(null)

  // ── Compiler view state ────────────────────────────────────────
  const [astData,       setAstData]      = useState([])
  const [bytecodeData,  setBytecodeData] = useState([])
  const [irData,        setIrData]       = useState([])
  const [debugSteps,    setDebugSteps]   = useState([])

  // ── Trust / stats ──────────────────────────────────────────────
  const [trustScore,    setTrustScore]  = useState(null)
  const [trustHistory,  setTrustHistory] = useState([])
  const [runCount,      setRunCount]    = useState(0)
  const [errorCount,    setErrorCount]  = useState(0)
  const [demoRunning,   setDemoRunning] = useState(false)

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

  // ── Tab helpers ────────────────────────────────────────────────
  const openExample = useCallback((key) => {
    const ex = EXAMPLES[key]
    if (!ex) return
    setTabs(prev => {
      if (prev.find(t => t.key === key)) return prev
      return [...prev, { key, name: ex.name, code: ex.code }]
    })
    setActiveTabKey(key)
    setAstData([])
    setBytecodeData([])
    setIrData([])
    setDebugSteps([])
  }, [])

  const closeTab = useCallback((key, e) => {
    e.stopPropagation()
    setTabs(prev => {
      const next = prev.filter(t => t.key !== key)
      if (next.length === 0) return prev          // keep at least 1
      if (activeTabKey === key) setActiveTabKey(next[next.length - 1].key)
      return next
    })
  }, [activeTabKey])

  const updateCode = useCallback((val) => {
    setTabs(prev => prev.map(t => t.key === activeTabKey ? { ...t, code: val } : t))
  }, [activeTabKey])

  // ── Run ────────────────────────────────────────────────────────
  const runCode = useCallback(async () => {
    if (!code.trim() || running) return
    setRunning(true)
    setProblems([])
    setBottomTab('terminal')
    const t0 = performance.now()
    setTerminalLines(prev => [...prev,
      { type: 'info', text: `\n─── Running ${activeTab.name} ─────────────────────────────` }
    ])
    try {
      const res  = await fetch(`${SERVER}/api/execute`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, verbose: false }),
      })
      const data = await res.json()
      const ms   = data.execution_time_ms ?? +(performance.now() - t0).toFixed(1)
      const isOk = data.success
      const isSecErr = !isOk && /division by zero|undefined|overflow|security/i.test(data.error ?? '')

      const lines = []
      data.output?.forEach(l => lines.push({ type: 'out', text: l }))
      if (data.error) lines.push({ type: isSecErr ? 'secerr' : 'err', text: data.error })
      if (!data.output?.length && !data.error) lines.push({ type: 'info', text: '(no output)' })
      const mode = data.optimized ? '⚡ OPTIMIZED' : '🔒 SANDBOXED'
      lines.push({ type: 'meta', text: `Exit ${isOk ? 0 : 1} · ${ms}ms · ${mode} · trust ${data.trust_score?.toFixed(3) ?? '—'}` })
      setTerminalLines(prev => [...prev, ...lines])

      const newRun = runCount + 1
      setRunCount(newRun)
      if (!isOk) setErrorCount(c => c + 1)
      if (data.error) {
        setProblems([{ id: Date.now(), severity: 'error', msg: data.error, file: activeTab.name, loc: '—' }])
        if (isSecErr) { setBottomTab('violations') }
      }
      if (isSecErr) setViolations(prev => [{
        id: prev.length + 1, ts: new Date().toLocaleTimeString(),
        file: activeTab.name, type: classifyViolation(data.error ?? ''), msg: data.error
      }, ...prev])

      setMetrics({ time: `${ms}ms`, tokens: data.tokens?.length ?? '—',
        optimized: data.optimized ? 'Yes' : 'No', hash: data.code_hash ?? '—',
        pipeline: data.pipeline_stages ?? null,
      })
      if (data.trust_score != null) {
        setTrustScore(data.trust_score)
        setTrustHistory(h => [...h, { run: newRun, trust: data.trust_score, mode: data.optimized ? 'optimized' : 'sandboxed' }])
      }
    } catch (err) {
      setTerminalLines(prev => [...prev, { type: 'err', text: `Connection error: ${err.message}` }])
      setErrorCount(c => c + 1)
    } finally { setRunning(false) }
  }, [code, running, activeTab, runCount])

  useEffect(() => {
    const fn = (e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); runCode() } }
    window.addEventListener('keydown', fn)
    return () => window.removeEventListener('keydown', fn)
  }, [runCode])

  // ── Compiler views ─────────────────────────────────────────────
  const parseAST = useCallback(async () => {
    try {
      const r = await fetch(`${SERVER}/api/parse`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) })
      const d = await r.json()
      if (d.success) { setAstData(d.ast); setBottomTab('ast'); log(`[AST] ${d.node_count} top-level nodes`) }
      else log(`[AST] ${d.error}`, 'err')
    } catch (e) { log(`[AST] ${e.message}`, 'err') }
  }, [code])

  const compileBytecode = useCallback(async () => {
    try {
      const r = await fetch(`${SERVER}/api/bytecode`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) })
      const d = await r.json()
      if (d.success) { setBytecodeData(d.instructions); setBottomTab('bytecode'); log(`[BC] ${d.count} instructions`) }
      else log(`[BC] ${d.error}`, 'err')
    } catch (e) { log(`[BC] ${e.message}`, 'err') }
  }, [code])

  const generateIR = useCallback(async () => {
    try {
      const r = await fetch(`${SERVER}/api/ir`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) })
      const d = await r.json()
      if (d.success) { setIrData(d.ir); setBottomTab('ir'); log(`[IR] ${d.count} TAC instructions`) }
      else log(`[IR] ${d.error}`, 'err')
    } catch (e) { log(`[IR] ${e.message}`, 'err') }
  }, [code])

  const runDebug = useCallback(async () => {
    try {
      const r = await fetch(`${SERVER}/api/debug`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) })
      const d = await r.json()
      if (d.success) { setDebugSteps(d.steps); setBottomTab('debug'); log(`[DBG] ${d.total} steps recorded`) }
      else log(`[DBG] ${d.error}`, 'err')
    } catch (e) { log(`[DBG] ${e.message}`, 'err') }
  }, [code])

  const runDemo = useCallback(async () => {
    if (demoRunning) return
    setDemoRunning(true)
    setBottomTab('terminal')
    log('\n════ DEMO: Trust Build-Up ═══════════════════════════', 'info')
    log('Running 8× same code · watch SANDBOXED → OPTIMIZED...', 'info')
    try {
      const r = await fetch(`${SERVER}/api/demo`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code, runs: 8 }) })
      const d = await r.json()
      if (d.success) {
        const hist = []
        for (const run of d.runs) {
          const icon = run.optimized ? '⚡' : '🔒'
          log(`  Run ${run.run}: ${icon} ${(run.mode ?? '').toUpperCase()} | trust=${run.trust} (${run.trust_level}) | ${run.time_ms}ms`, run.optimized ? 'out' : 'info')
          hist.push({ run: runCount + run.run, trust: run.trust, mode: run.mode })
          if (run.trust != null) setTrustScore(run.trust)
        }
        setTrustHistory(h => [...h, ...hist])
        setRunCount(c => c + d.runs.length)
        log(`════ Demo complete. Final mode: ${(d.runs.at(-1)?.mode ?? '').toUpperCase()} ═════`, 'info')
      }
    } catch (e) { log(`Demo error: ${e.message}`, 'err') }
    finally { setDemoRunning(false) }
  }, [code, demoRunning, runCount])

  const log = (text, type = 'info') => setTerminalLines(prev => [...prev, { type, text }])

  return (
    <div className="shell">
      <div className="workbench">
        <ActivityBar active={activePanel} onSwitch={setActivePanel} />
        <Sidebar
          view={activePanel}
          examples={EXAMPLES}
          onLoadExample={openExample}
          activeFile={activeTab?.name}
          trustScore={trustScore}
          trustHistory={trustHistory}
          runCount={runCount}
          violations={violations}
          execMode="sandboxed"
          onModeChange={() => {}}
          onDemo={runDemo}
          demoRunning={demoRunning}
        />
        <div className="editor-area" ref={editorArea}>
          <EditorPane
            tabs={tabs}
            activeTabKey={activeTabKey}
            onTabClick={setActiveTabKey}
            onTabClose={closeTab}
            code={code}
            onChange={updateCode}
            onRun={runCode}
            running={running}
            onParseAST={parseAST}
            onBytecode={compileBytecode}
            onIR={generateIR}
            onDebug={runDebug}
          />
          {/* ── Resize handle ── */}
          <div className="resizeHandle" onMouseDown={startDrag} title="Drag to resize panel" />
          <BottomPanel
            height={bottomH}
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
          />
        </div>
      </div>
      <StatusBar
        serverOnline={serverOnline}
        trustScore={trustScore}
        execMode="sandboxed"
        runCount={runCount}
        errorCount={errorCount}
        activeFile={activeTab?.name}
      />
    </div>
  )
}

function classifyViolation(msg) {
  if (/division by zero/i.test(msg)) return 'Division by Zero'
  if (/undefined/i.test(msg))        return 'Undefined Variable'
  if (/overflow/i.test(msg))         return 'Integer Overflow'
  return 'Security Error'
}
