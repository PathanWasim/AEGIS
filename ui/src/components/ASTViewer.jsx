import { useState } from 'react'
import s from './ASTViewer.module.css'

const COLOR = {
  statement:  '#569cd6',
  keyword:    '#c586c0',
  control:    '#d7993a',
  operator:   '#4ec9b0',
  identifier: '#9cdcfe',
  literal:    '#b5cea8',
  unknown:    '#858585',
}

export default function ASTViewer({ nodes }) {
  return (
    <div className={s.viewer}>
      <div className={s.root}>
        {nodes.map((n, i) => <TreeNode key={i} node={n} depth={0} />)}
      </div>
    </div>
  )
}

function TreeNode({ node, depth }) {
  const [open, setOpen] = useState(true)
  const hasChildren = node.children && node.children.length > 0
  const color = COLOR[node.color] ?? '#cccccc'

  return (
    <div className={s.node} style={{ marginLeft: depth * 20 }}>
      <div className={s.row} onClick={() => hasChildren && setOpen(o => !o)}>
        {hasChildren
          ? <span className={s.arrow}>{open ? '▾' : '▸'}</span>
          : <span className={s.dot}>·</span>
        }
        <span className={s.typeBadge} style={{ background: color + '22', color }}>
          {node.type}
        </span>
        <span className={s.label}>{node.label}</span>
      </div>
      {hasChildren && open && (
        <div className={s.children}>
          {node.children.map((c, i) => <TreeNode key={i} node={c} depth={depth + 1} />)}
        </div>
      )}
    </div>
  )
}
