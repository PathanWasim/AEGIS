import { useRef } from 'react'
import Editor from '@monaco-editor/react'
import s from './EditorPane.module.css'
import { Play, Loader2, GitBranch, Cpu, Code2, Bug, X } from 'lucide-react'

const FILE_ICONS = {
  '.aegis': '#519aba',
  '.py':    '#4ec9b0',
  '.js':    '#cca700',
}

function fileColor(name) {
  const ext = name.slice(name.lastIndexOf('.'))
  return FILE_ICONS[ext] ?? '#cccccc'
}

export default function EditorPane({
  tabs, activeTabKey, onTabClick, onTabClose,
  code, onChange, onRun, running,
  onParseAST, onBytecode, onIR, onDebug,
}) {
  const monacoRef = useRef(null)

  function handleMount(editor, monaco) {
    monacoRef.current = monaco
    editor.focus()
    registerAegisLanguage(monaco)
    monaco.editor.setModelLanguage(editor.getModel(), 'aegis')
    // Ctrl+Enter shortcut
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, onRun)
  }

  const activeTab = tabs.find(t => t.key === activeTabKey) ?? tabs[0]

  return (
    <div className={s.pane}>
      {/* ── Tab bar ── */}
      <div className={s.tabBar}>
        <div className={s.tabs}>
          {tabs.map(tab => {
            const isActive = tab.key === activeTabKey
            return (
              <div
                key={tab.key}
                className={`${s.tab} ${isActive ? s.tabActive : ''}`}
                onClick={() => onTabClick(tab.key)}
                title={tab.name}
              >
                <span className={s.tabDot} style={{ background: fileColor(tab.name) }} />
                <span className={s.tabName}>{tab.name}</span>
                <button
                  className={s.tabClose}
                  onClick={(e) => onTabClose(tab.key, e)}
                  title="Close tab"
                >
                  <X size={12} />
                </button>
              </div>
            )
          })}
        </div>

        {/* ── Toolbar ── */}
        <div className={s.toolbar}>
          <button className={s.toolBtn} onClick={onParseAST}    title="Parse & visualize AST"><GitBranch size={12} /> AST</button>
          <button className={s.toolBtn} onClick={onBytecode}    title="Compile to VM bytecode"><Cpu size={12} /> Bytecode</button>
          <button className={s.toolBtn} onClick={onIR}          title="Generate IR / Three-Address Code"><Code2 size={12} /> IR</button>
          <button className={s.toolBtn} onClick={onDebug}       title="Step-by-step debugger"><Bug size={12} /> Debug</button>
          <div className={s.sep} />
          <button
            className={`${s.runBtn} ${running ? s.runBtnBusy : ''}`}
            onClick={onRun}
            disabled={running}
            title="Run (Ctrl+Enter)"
          >
            {running ? <Loader2 size={13} className={s.spin} /> : <Play size={13} fill="currentColor" />}
            {running ? 'Running…' : 'Run'}
          </button>
        </div>
      </div>

      {/* ── Breadcrumb ── */}
      <div className={s.breadcrumb}>
        <span className={s.bcSection}>AEGIS</span>
        <span className={s.bcSep}> › </span>
        <span className={s.bcFile}>{activeTab?.name}</span>
      </div>

      {/* ── Monaco Editor ── */}
      <div className={s.editorWrap}>
        <Editor
          key={activeTabKey}        /* re-mount per tab so model is fresh */
          height="100%"
          defaultLanguage="plaintext"
          value={code}
          onChange={v => onChange(v ?? '')}
          onMount={handleMount}
          theme="aegis-dark"
          options={{
            fontSize: 14,
            fontFamily: 'Consolas, "Courier New", monospace',
            lineHeight: 22,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            renderLineHighlight: 'gutter',
            tabSize: 2,
            insertSpaces: true,
            padding: { top: 10, bottom: 10 },
            overviewRulerLanes: 0,
            hideCursorInOverviewRuler: true,
            scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
            automaticLayout: true,
            glyphMargin: false,
            folding: true,
            lineNumbersMinChars: 3,
          }}
        />
      </div>
    </div>
  )
}

// ── AEGIS language + theme registration ──────────────────────────────────────
function registerAegisLanguage(monaco) {
  if (monaco.languages.getLanguages().find(l => l.id === 'aegis')) return

  monaco.languages.register({ id: 'aegis' })
  monaco.languages.setMonarchTokensProvider('aegis', {
    keywords: ['if', 'else', 'while', 'end', 'print', 'def', 'return', 'call', 'for', 'to'],
    operators: ['+', '-', '*', '/', '%', '==', '!=', '<=', '>=', '<', '>'],
    tokenizer: {
      root: [
        [/#.*$/,                              'comment'],
        [/"[^"]*"/,                           'string'],
        [/\b(if|else|while|end|print|def|return|call|for|to)\b/, 'keyword'],
        [/\b\d+\b/,                           'number'],
        [/==|!=|<=|>=|[<>]/,                  'operator.cmp'],
        [/[+\-*\/%]/,                         'operator.arith'],
        [/=/,                                 'delimiter'],
        [/[a-zA-Z_]\w*/,                      'identifier'],
      ],
    },
  })

  monaco.editor.defineTheme('aegis-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword',        foreground: 'c586c0', fontStyle: 'bold' },
      { token: 'number',         foreground: 'b5cea8' },
      { token: 'string',         foreground: 'ce9178' },
      { token: 'comment',        foreground: '6a9955', fontStyle: 'italic' },
      { token: 'operator.cmp',   foreground: '9cdcfe' },
      { token: 'operator.arith', foreground: '4ec9b0' },
      { token: 'delimiter',      foreground: 'd4d4d4' },
      { token: 'identifier',     foreground: '9cdcfe' },
    ],
    colors: { 'editor.background': '#1e1e1e' },
  })
}
