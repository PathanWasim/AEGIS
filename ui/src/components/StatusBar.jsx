import s from './StatusBar.module.css'
import { Wifi, WifiOff, AlertCircle, ShieldCheck } from 'lucide-react'

export default function StatusBar({ serverOnline, trustScore, execMode, runCount, errorCount, activeFile }) {
  const trust = trustScore != null ? trustScore.toFixed(3) : '—'
  const level = trustLevel(trustScore)

  return (
    <div className={`${s.bar} ${errorCount > 0 ? s.hasErrors : ''}`}>
      {/* Left */}
      <div className={s.left}>
        <div className={s.item} title={serverOnline ? 'Server connected' : 'Server offline'}>
          {serverOnline
            ? <><Wifi size={12} /> localhost:5000</>
            : <><WifiOff size={12} /> Server offline</>
          }
        </div>
        <div className={s.item}>
          <AlertCircle size={12} />
          <span>{errorCount}</span>
          &nbsp;errors
        </div>
        <div className={s.item}>Runs: {runCount}</div>
      </div>

      {/* Right */}
      <div className={s.right}>
        <div className={s.item}>{activeFile}</div>
        <div className={s.item}>
          <ShieldCheck size={12} />
          &nbsp;Trust: {trust} ({level})
        </div>
        <div className={s.item}>{execMode === 'optimized' ? '⚡ Optimized' : '🔒 Sandboxed'}</div>
        <div className={s.item}>AEGIS v1.0</div>
      </div>
    </div>
  )
}

function trustLevel(score) {
  if (score == null) return '—'
  if (score >= 0.8) return 'TRUSTED'
  if (score >= 0.6) return 'HIGH'
  if (score >= 0.3) return 'MEDIUM'
  if (score >= 0.1) return 'LOW'
  return 'NONE'
}
