// src/pages/Playground.jsx
import { useRef, useState, useCallback } from 'react'
import Editor from '../components/editor/Editor'
import Sidebar from '../components/layout/Sidebar'
import OutputPanel from '../components/panels/OutputPanel'
import TokenPanel from '../components/panels/TokenPanel'
import PipelineView from '../components/panels/PipelineView'
import ASTViewer from '../components/panels/ASTViewer'
import TrustPanel from '../components/panels/TrustPanel'
import { useStore } from '../store/useStore'
import { api } from '../services/api'
import s from './Playground.module.css'

const BOTTOM_TABS = [
  { id: 'terminal',  label: 'TERMINAL'  },
  { id: 'pipeline',  label: 'PIPELINE'  },
  { id: 'ast',       label: 'AST'       },
  { id: 'trust',     label: 'TRUST'     },
  { id: 'tokens',    label: 'TOKENS'    },
]

export default function Playground({ onRun }) {
  const { bottomTab, setBottomTab, result } = useStore()
  const issues = result?.issues ?? []
  const hasHigh = issues.some(i => i.severity === 'HIGH')

  // Resizable bottom panel
  const [bottomH, setBottomH] = useState(220)
  const dragRef = useRef(null)

  const startDrag = useCallback((e) => {
    e.preventDefault()
    const startY = e.clientY
    const startH = bottomH
    const onMove = (mv) => {
      setBottomH(Math.max(100, Math.min(startH + (startY - mv.clientY), 500)))
    }
    const onUp = () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.body.style.cursor = 'row-resize'
    document.body.style.userSelect = 'none'
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }, [bottomH])

  return (
    <div className={s.playground}>
      {/* Sidebar */}
      <Sidebar />

      {/* Main editing area */}
      <div className={s.main}>
        {/* Editor fills remaining height above bottom panel */}
        <div className={s.editorArea}>
          <Editor onRun={onRun} />
        </div>

        {/* Resize handle */}
        <div className={s.resizeHandle} onMouseDown={startDrag} />

        {/* Bottom panel */}
        <div className={s.bottomPanel} style={{ height: bottomH }}>
          {/* Tab bar */}
          <div className={s.tabBar}>
            {BOTTOM_TABS.map(t => (
              <button
                key={t.id}
                className={`${s.tab} ${bottomTab === t.id ? s.tabActive : ''}`}
                onClick={() => setBottomTab(t.id)}
              >
                {t.label}
                {t.id === 'pipeline' && hasHigh && <span className={s.badge}>!</span>}
              </button>
            ))}
            <div className={s.tabSpacer} />
            <button className={s.clearBtn} onClick={() => useStore.getState().clearTerminal()}>
              Clear
            </button>
          </div>

          {/* Panel content */}
          <div className={s.panelContent}>
            {bottomTab === 'terminal' && <OutputPanel />}
            {bottomTab === 'pipeline' && <PipelineView />}
            {bottomTab === 'ast'      && <ASTViewer />}
            {bottomTab === 'trust'    && <TrustPanel />}
            {bottomTab === 'tokens'   && <TokenPanel />}
          </div>
        </div>
      </div>
    </div>
  )
}
