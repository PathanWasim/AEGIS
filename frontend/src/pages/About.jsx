// src/pages/About.jsx
import s from './About.module.css'

const ARCH = `
  Source Code
       │
       ▼
  ┌─────────┐
  │  LEXER  │  → Token stream
  └────┬────┘
       │
       ▼
  ┌─────────┐
  │  PARSER │  → Abstract Syntax Tree
  └────┬────┘
       │
       ▼
  ┌──────────────────┐
  │  STATIC ANALYZER │  → Issues [ {type, line, severity} ]
  └────────┬─────────┘
           │
           ▼
  ┌─────────────────┐
  │  TRUST MANAGER  │  score < 1.0 → INTERPRETER
  └────────┬────────┘  score ≥ 1.0 → OPTIMIZED VM
           │
      ┌────┴─────┐
      │          │
      ▼          ▼
 SANDBOX    OPTIMIZED
 INTERP     EXEC CACHE
      │          │
      └────┬─────┘
           │
           ▼
       OUTPUT / LOGS
`

const COMPONENTS = [
  { name: 'Lexer',            desc: 'Character-level scanner. Produces tokens with line/column info. Detects illegal characters and raises LexicalError.' },
  { name: 'Parser (RD)',      desc: 'Recursive-descent parser. Builds typed AST nodes. Raises SyntaxError with suggestions on invalid structure.' },
  { name: 'Static Analyzer',  desc: 'Walks AST before execution. Detects: UNDEFINED_VAR, DIV_BY_ZERO, INFINITE_LOOP, OVERFLOW, DEEP_NESTING.' },
  { name: 'Trust Manager',    desc: 'SHA-256 code hashing. Per-hash trust score: 0.6/0.2 initial, +0.3/run, threshold 1.0. Resets on violation.' },
  { name: 'Interpreter',      desc: 'Sandboxed recursive AST walker. Tracks instruction count, loop iterations, bounds checks. Pluggable monitor.' },
  { name: 'Optimized VM',     desc: 'Caches first execution output by code hash. Deterministic replay on subsequent runs. Rollback on violation.' },
  { name: 'Runtime Monitor',  desc: 'Instruments interpreter: counts ops, measures time, detects anomalies. Triggers rollback on threshold breach.' },
  { name: 'Flask Backend',    desc: '/api/execute, /api/tokenize, /api/analyze, /api/health. Stateless routes delegating to pipeline core.' },
]

export default function About() {
  return (
    <div className={s.page}>
      <div className={s.header}>
        <h1 className={s.title}>About AEGIS</h1>
        <p className={s.subtitle}>Adaptive Execution Guarded Interpreter System · v2.0</p>
      </div>

      <div className={s.content}>
        <section className={s.section}>
          <h2 className={s.sectionTitle}>Architecture</h2>
          <pre className={s.arch}>{ARCH}</pre>
        </section>

        <section className={s.section}>
          <h2 className={s.sectionTitle}>Core Components</h2>
          <div className={s.compGrid}>
            {COMPONENTS.map(c => (
              <div key={c.name} className={s.comp}>
                <div className={s.compName}>{c.name}</div>
                <p className={s.compDesc}>{c.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className={s.section}>
          <h2 className={s.sectionTitle}>Stack</h2>
          <table className={s.table}>
            <tbody>
              <tr><td>Backend</td>  <td className={s.code}>Python 3.11 · Flask · CORS</td></tr>
              <tr><td>Compiler</td> <td className={s.code}>Custom lexer, RD parser, AST, interpreter</td></tr>
              <tr><td>Frontend</td> <td className={s.code}>React 19 · Vite · Zustand · Monaco · Recharts</td></tr>
              <tr><td>State</td>    <td className={s.code}>Zustand store · React Router v7</td></tr>
              <tr><td>Styling</td>  <td className={s.code}>CSS Modules · VS Code dark theme</td></tr>
            </tbody>
          </table>
        </section>
      </div>
    </div>
  )
}
