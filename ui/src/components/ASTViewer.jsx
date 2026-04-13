/**
 * ASTViewer — renders an abstract syntax tree as a proper horizontal node tree.
 *
 * Layout: nodes are arranged horizontally into columns per depth.
 * Each node shows its type and label in a coloured card.
 * Lines connect parents to children via SVG.
 * Click any node to expand/collapse its subtree.
 */
import { useState, useRef, useCallback, useLayoutEffect } from 'react'
import s from './ASTViewer.module.css'

// ── Colour palette per node type ─────────────────────────────────────────────
const COLORS = {
  Assignment: { bg: '#1b3a5c', border: '#569cd6', text: '#9cdcfe', icon: '=' },
  Print:      { bg: '#1b3a2e', border: '#4ec9b0', text: '#4ec9b0', icon: '▶' },
  If:         { bg: '#3a2d1b', border: '#cca700', text: '#ddb828', icon: '?' },
  While:      { bg: '#3a1b3a', border: '#c586c0', text: '#e6a9e6', icon: '↻' },
  Condition:  { bg: '#2d2d1b', border: '#cca700', text: '#cca700', icon: '⟨⟩' },
  Then:       { bg: '#1b2d1b', border: '#89d185', text: '#89d185', icon: '✓' },
  Else:       { bg: '#2d1b1b', border: '#f48771', text: '#f48771', icon: '✗' },
  Body:       { bg: '#1b2438', border: '#569cd6', text: '#569cd6', icon: '{ }' },
  BinaryOp:   { bg: '#1f2d2d', border: '#4ec9b0', text: '#4ec9b0', icon: '⊕' },
  Identifier: { bg: '#1a2a3a', border: '#9cdcfe', text: '#9cdcfe', icon: '$' },
  Integer:    { bg: '#1e2b1e', border: '#b5cea8', text: '#b5cea8', icon: '#' },
  Unknown:    { bg: '#2d2d2d', border: '#858585', text: '#858585', icon: '?' },
}

function getColor(type) {
  return COLORS[type] ?? COLORS.Unknown
}

export default function ASTViewer({ nodes }) {
  const [collapsed, setCollapsed] = useState(new Set())

  const toggle = useCallback((id) => {
    setCollapsed(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }, [])

  // Wrap all top-level nodes under a synthetic Program root
  const root = {
    type: 'Program',
    label: 'program',
    color: 'control',
    children: nodes,
    _id: 'root',
  }

  return (
    <div className={s.viewer}>
      <div className={s.scroll}>
        <TreeNode node={root} collapsed={collapsed} onToggle={toggle} depth={0} nodeId="root" />
      </div>
      <div className={s.legend}>
        {Object.entries(COLORS)
          .filter(([k]) => !['Unknown'].includes(k))
          .map(([type, c]) => (
            <span key={type} className={s.legendItem} style={{ color: c.text, borderColor: c.border }}>
              {c.icon} {type}
            </span>
          ))
        }
      </div>
    </div>
  )
}

let _nodeCounter = 0
function uid() { return String(++_nodeCounter) }

function TreeNode({ node, collapsed, onToggle, depth, nodeId }) {
  const hasChildren = node.children && node.children.length > 0
  const isCollapsed = collapsed.has(nodeId)
  const c = getColor(node.type)

  return (
    <div className={s.nodeWrap}>
      {/* ── The node card ── */}
      <div
        className={`${s.nodeCard} ${hasChildren ? s.nodeCardClickable : ''}`}
        style={{ borderColor: c.border, background: c.bg }}
        onClick={() => hasChildren && onToggle(nodeId)}
        title={hasChildren ? (isCollapsed ? 'Expand' : 'Collapse') : undefined}
      >
        <span className={s.nodeIcon} style={{ color: c.border }}>{c.icon}</span>
        <div className={s.nodeInfo}>
          <span className={s.nodeType} style={{ color: c.text }}>{node.type}</span>
          {node.label && node.label !== node.type && (
            <span className={s.nodeLabel}>{node.label}</span>
          )}
        </div>
        {hasChildren && (
          <span className={s.collapseBtn} style={{ color: c.border }}>
            {isCollapsed ? `+${node.children.length}` : '▾'}
          </span>
        )}
      </div>

      {/* ── Children ── */}
      {hasChildren && !isCollapsed && (
        <div className={s.children}>
          <div className={s.vline} style={{ borderColor: c.border + '60' }} />
          <div className={s.childList}>
            {node.children.map((child, i) => {
              const childId = `${nodeId}-${i}`
              return (
                <div key={i} className={s.childBranch}>
                  <div className={s.hline} style={{ borderColor: (getColor(child.type || 'Unknown').border) + '60' }} />
                  <TreeNode
                    node={child}
                    collapsed={collapsed}
                    onToggle={onToggle}
                    depth={depth + 1}
                    nodeId={childId}
                  />
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
