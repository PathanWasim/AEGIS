import { useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'
import s from './EditorPane.module.css'
import { Play, Loader2, FileCode2, GitBranch, Cpu, Code2, Bug } from 'lucide-react'

export default function EditorPane({
  code, onChange, activeFile, onRun, running,
  onParseAST, onBytecode, onIR, onDebug,
}) {
  const editorRef   = useRef(null)
  const monacoRef   = useRef(null)

  function handleEditorMount(editor, monaco) {
    editorRef.current  = editor
    monacoRef.current  = monaco
    editor.focus()
    registerAegisLanguage(monaco)
    // Re-set language so tokenizer applies immediately
    monaco.editor.setModelLanguage(editor.getModel(), 'aegis')
  }

  return (
    <div className={s.pane}>
      {/* Tab bar */}
      <div className={s.tabs}>
        <div className={s.tab}>
          <FileCode2 size={14} className={s.tabIcon} />
          <span>{activeFile}</span>
          <span className={s.tabClose}>×</span>
        </div>
        <div className={s.tabSpacer} />

        {/* Tool buttons */}
        <button className={s.toolBtn} onClick={onParseAST} title="Parse AST tree (visualizer)">
          <GitBranch size={13} /> AST
        </button>
        <button className={s.toolBtn} onClick={onBytecode} title="Compile to bytecode">
          <Cpu size={13} /> Bytecode
        </button>
        <button className={s.toolBtn} onClick={onIR} title="Generate IR / Three-Address Code">
          <Code2 size={13} /> IR
        </button>
        <button className={s.toolBtn} onClick={onDebug} title="Step-by-step debugger">
          <Bug size={13} /> Debug
        </button>

        <button
          className={`${s.runBtn} ${running ? s.runBtnDisabled : ''}`}
          onClick={onRun}
          disabled={running}
          title="Run (Ctrl+Enter)"
        >
          {running
            ? <Loader2 size={14} className={s.spin} />
            : <Play size={14} fill="currentColor" />
          }
          {running ? 'Running…' : 'Run'}
        </button>
      </div>

      {/* Breadcrumb */}
      <div className={s.breadcrumb}>
        <span className={s.bcItem}>AEGIS</span>
        <span className={s.bcSep}> › </span>
        <span className={s.bcItem}>{activeFile}</span>
      </div>

      {/* Monaco editor */}
      <div className={s.editorWrap}>
        <Editor
          height="100%"
          defaultLanguage="plaintext"
          value={code}
          onChange={v => onChange(v ?? '')}
          onMount={handleEditorMount}
          theme="aegis-dark"
          options={{
            fontSize: 14,
            fontFamily: 'Consolas, "Courier New", monospace',
            lineHeight: 21,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            renderLineHighlight: 'gutter',
            tabSize: 2,
            insertSpaces: true,
            padding: { top: 8, bottom: 8 },
            overviewRulerLanes: 0,
            hideCursorInOverviewRuler: true,
            scrollbar: {
              verticalScrollbarSize: 10,
              horizontalScrollbarSize: 10,
            },
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  )
}

// ── Register AEGIS language in Monaco ──────────────────────────────────────
function registerAegisLanguage(monaco) {
  monaco.languages.register({ id: 'aegis' })

  monaco.languages.setMonarchTokensProvider('aegis', {
    keywords: ['if', 'else', 'while', 'end', 'print', 'def', 'return', 'call', 'for', 'to'],
    tokenizer: {
      root: [
        // Comments
        [/#.*$/, 'comment'],
        // Keywords
        [/\b(if|else|while|end|print|def|return|call|for|to)\b/, 'keyword'],
        // Numbers
        [/\b\d+\b/, 'number'],
        // String literals
        [/"[^"]*"/, 'string'],
        // Operators
        [/[+\-*/%]/, 'operator'],
        [/==|!=|<=|>=|[<>]/, 'operator'],
        [/=/, 'delimiter'],
        // Identifiers
        [/[a-zA-Z_]\w*/, 'identifier'],
        // Whitespace
        [/\s+/, 'white'],
      ],
    },
  })

  // Define AEGIS Dark theme
  monaco.editor.defineTheme('aegis-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword',    foreground: 'c586c0', fontStyle: 'bold' },
      { token: 'number',     foreground: 'b5cea8' },
      { token: 'string',     foreground: 'ce9178' },
      { token: 'comment',    foreground: '6a9955', fontStyle: 'italic' },
      { token: 'operator',   foreground: '4ec9b0' },
      { token: 'delimiter',  foreground: 'd4d4d4' },
      { token: 'identifier', foreground: '9cdcfe' },
    ],
    colors: {
      'editor.background': '#1e1e1e',
    },
  })
}
