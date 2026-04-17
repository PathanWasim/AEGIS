// src/components/panels/ASTViewer.jsx
// Displays a proper tree view using ├── / └── connectors, not raw JSON

import { useState } from 'react'
import { useStore } from '../../store/useStore'
import s from './ASTViewer.module.css'

// ── Helpers ───────────────────────────────────────────────────────────────────

function getNodeLabel(node) {
  const t = node.type ?? node.node_type ?? 'Node'
  // Attach inline scalar attrs for quick reading
  const scalars = Object.entries(node)
    .filter(([k]) => !['type', 'node_type', 'children', 'body', 'statements',
                        'then_body', 'else_body', 'condition', 'expression',
                        'left', 'right'].includes(k))
    .filter(([, v]) => v !== null && v !== undefined && typeof v !== 'object')
    .slice(0, 3)
    .map(([k, v]) => `${k}: ${v}`)
    .join('  ')
  return scalars ? `${t}  ${scalars}` : t
}

function getChildren(node) {
  const kids = []
  const push = (label, child) => {
    if (child == null) return
    if (Array.isArray(child)) {
      child.forEach((c, i) => c && kids.push({ label: `${label}[${i}]`, node: c }))
    } else if (typeof child === 'object') {
      kids.push({ label, node: child })
    }
  }
  push('condition',  node.condition)
  push('expression', node.expression)
  push('left',       node.left)
  push('right',      node.right)
  ;['children', 'body', 'statements', 'then_body', 'else_body'].forEach(k => push(k, node[k]))
  return kids
}

// ── Tree node component ────────────────────────────────────────────────────────

function TreeNode({ node, prefix = '', isLast = true, depth = 0 }) {
  const [open, setOpen] = useState(depth < 3)
  if (!node || typeof node !== 'object') return null

  const kids    = getChildren(node)
  const label   = getNodeLabel(node)
  const hasKids = kids.length > 0

  const connector = prefix === '' ? '' : (isLast ? '└── ' : '├── ')
  const childPfx  = prefix === '' ? '' : (isLast ? '    ' : '│   ')

  return (
    <div className={s.treeBlock}>
      <div
        className={`${s.treeRow} ${hasKids ? s.clickable : ''}`}
        onClick={() => hasKids && setOpen(o => !o)}
      >
        <span className={s.prefix}>{prefix}{connector}</span>
        {hasKids && <span className={s.toggle}>{open ? '▾' : '▸'}</span>}
        <span className={s.nodeType}>{label}</span>
      </div>
      {open && hasKids && kids.map((kid, i) => (
        <TreeNode
          key={i}
          node={kid.node}
          prefix={`${prefix}${childPfx}`}
          isLast={i === kids.length - 1}
          depth={depth + 1}
        />
      ))}
    </div>
  )
}

// ── exported component ────────────────────────────────────────────────────────

export default function ASTViewer() {
  const ast = useStore(st => st.result?.ast)

  if (!ast) return (
    <div className={s.empty}>Run a program to see the Abstract Syntax Tree.</div>
  )

  const nodes = Array.isArray(ast) ? ast : [ast]

  return (
    <div className={s.panel}>
      <div className={s.header}>
        AST · {nodes.length} top-level node{nodes.length !== 1 ? 's' : ''}
      </div>
      <div className={s.tree}>
        {nodes.map((n, i) => (
          <TreeNode key={i} node={n} isLast={i === nodes.length - 1} />
        ))}
      </div>
    </div>
  )
}
