// src/components/editor/Editor.jsx
import MonacoEditor from '@monaco-editor/react'
import { useStore } from '../../store/useStore'
import s from './Editor.module.css'

// AEGIS language token rules for Monaco
function registerAegisLanguage(monaco) {
  if (monaco.languages.getLanguages().some(l => l.id === 'aegis')) return

  monaco.languages.register({ id: 'aegis' })
  monaco.languages.setMonarchTokensProvider('aegis', {
    keywords: ['if', 'else', 'while', 'end', 'print'],
    tokenizer: {
      root: [
        [/#.*$/,                          'comment'],
        [/\b(if|else|while|end|print)\b/, 'keyword'],
        [/\d+/,                           'number'],
        [/[a-zA-Z_]\w*/,                  'identifier'],
        [/[+\-*\/%=<>!]=?|==|!=|<=|>=/,  'operator'],
        [/[()]/,                          'delimiter'],
      ],
    },
  })

  monaco.editor.defineTheme('aegis-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword',    foreground: 'c586c0', fontStyle: 'bold' },
      { token: 'number',     foreground: 'b5cea8' },
      { token: 'identifier', foreground: '9cdcfe' },
      { token: 'operator',   foreground: 'd4d4d4' },
      { token: 'comment',    foreground: '6a9955', fontStyle: 'italic' },
    ],
    colors: {
      'editor.background': '#1e1e1e',
      'editor.lineHighlightBackground': '#2a2d2e',
      'editorLineNumber.foreground': '#858585',
      'editorLineNumber.activeForeground': '#c6c6c6',
    },
  })
}

export default function Editor({ onRun }) {
  const { code, setCode } = useStore()

  function handleMount(editor, monaco) {
    registerAegisLanguage(monaco)
    monaco.editor.setTheme('aegis-dark')

    // Ctrl+Enter to run
    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
      () => onRun?.()
    )
  }

  return (
    <div className={s.container}>
      <div className={s.header}>
        <span className={s.tab}>
          <span className={s.tabDot} />
          program.aegis
        </span>
      </div>
      <MonacoEditor
        language="aegis"
        value={code}
        onChange={v => setCode(v ?? '')}
        onMount={handleMount}
        options={{
          fontSize: 14,
          fontFamily: "'Fira Code', 'Consolas', monospace",
          fontLigatures: true,
          lineHeight: 22,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          renderWhitespace: 'none',
          wordWrap: 'off',
          tabSize: 2,
          insertSpaces: true,
          overviewRulerBorder: false,
          hideCursorInOverviewRuler: true,
          scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
          bracketPairColorization: { enabled: false },
        }}
        height="100%"
        theme="aegis-dark"
      />
    </div>
  )
}
