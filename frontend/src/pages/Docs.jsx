// src/pages/Docs.jsx
import s from './Docs.module.css'

const SYNTAX = [
  { construct: 'x = 42',          desc: 'Variable assignment' },
  { construct: 'print x',         desc: 'Print variable' },
  { construct: 'x + y',           desc: 'Arithmetic: + - * / %' },
  { construct: 'x == y',          desc: 'Equality comparison' },
  { construct: 'x != y',          desc: 'Inequality' },
  { construct: 'x < y',           desc: 'Less than (also <=)' },
  { construct: 'x > y',           desc: 'Greater than (also >=)' },
  { construct: 'if … else … end', desc: 'Conditional branching' },
  { construct: 'while … end',     desc: 'Loop with condition' },
  { construct: '# comment',       desc: 'Line comment' },
  { construct: '(expr)',          desc: 'Grouped expression' },
]

const EBNF = `program     ::= statement* EOF
statement   ::= assignment | print_stmt | if_stmt | while_stmt
assignment  ::= IDENTIFIER "=" expression NEWLINE
print_stmt  ::= "print" expression NEWLINE
if_stmt     ::= "if" expression NEWLINE statement* ("else" NEWLINE statement*)? "end" NEWLINE
while_stmt  ::= "while" expression NEWLINE statement* "end" NEWLINE
expression  ::= comparison
comparison  ::= addition (("==" | "!=" | "<" | "<=" | ">" | ">=") addition)?
addition    ::= multiplication (("+" | "-") multiplication)*
multiplication ::= primary (("*" | "/" | "%") primary)*
primary     ::= INTEGER | IDENTIFIER | "(" expression ")"`

const SECURITY_STEPS = [
  { n: 1, title: 'Static Analysis',     body: 'AST-level checks before execution. Detects undefined variables, division by zero, infinite loops, overflow, and deep nesting. HIGH severity → optimization blocked.' },
  { n: 2, title: 'Trust Scoring',       body: 'Code hash maps to a trust score. Safe code starts at 0.6; unsafe at 0.2. Each safe run adds +0.3. Threshold 1.0 unlocks optimized mode.' },
  { n: 3, title: 'Sandboxed Exec',      body: 'Interpreter tracks instruction count, loop iterations, and integer bounds. Violations trigger immediate halt.' },
  { n: 4, title: 'Optimized Mode',      body: 'Activated when trust ≥ 1.0 and no HIGH issues. Execution path is cached; output is replayed deterministically.' },
  { n: 5, title: 'Rollback',            body: 'If a runtime violation occurs in optimized mode, trust resets to 0.0 and execution returns to the sandboxed interpreter.' },
]

export default function Docs() {
  return (
    <div className={s.page}>
      <div className={s.header}>
        <h1 className={s.title}>AEGIS Language Reference</h1>
        <p className={s.subtitle}>Adaptive Execution Guarded Interpreter System</p>
      </div>

      <div className={s.grid}>
        {/* Syntax */}
        <section className={s.section}>
          <h2 className={s.sectionTitle}>Syntax Reference</h2>
          <table className={s.table}>
            <thead>
              <tr><th>Construct</th><th>Description</th></tr>
            </thead>
            <tbody>
              {SYNTAX.map((row, i) => (
                <tr key={i}>
                  <td className={s.code}>{row.construct}</td>
                  <td>{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* EBNF Grammar */}
        <section className={s.section}>
          <h2 className={s.sectionTitle}>Formal Grammar (EBNF)</h2>
          <pre className={s.ebnf}>{EBNF}</pre>
        </section>

        {/* Security model */}
        <section className={s.section + ' ' + s.fullWidth}>
          <h2 className={s.sectionTitle}>Security Model</h2>
          <div className={s.steps}>
            {SECURITY_STEPS.map(step => (
              <div key={step.n} className={s.step}>
                <div className={s.stepNum}>{step.n}</div>
                <div>
                  <div className={s.stepTitle}>{step.title}</div>
                  <p className={s.stepBody}>{step.body}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Trust table */}
        <section className={s.section}>
          <h2 className={s.sectionTitle}>Trust Score Rules</h2>
          <table className={s.table}>
            <thead><tr><th>Event</th><th>Effect</th></tr></thead>
            <tbody>
              <tr><td className={s.code}>Static safe</td>         <td>Initial score → 0.6</td></tr>
              <tr><td className={s.code}>Static issue found</td>   <td>Initial score → 0.2</td></tr>
              <tr><td className={s.code}>HIGH severity issue</td>  <td>Optimization BLOCKED</td></tr>
              <tr><td className={s.code}>Safe execution</td>       <td>score += 0.3</td></tr>
              <tr><td className={s.code}>score ≥ 1.0</td>          <td>Optimized mode unlocked</td></tr>
              <tr><td className={s.code}>Runtime violation</td>    <td>score → 0.0, rollback</td></tr>
            </tbody>
          </table>
        </section>
      </div>
    </div>
  )
}
