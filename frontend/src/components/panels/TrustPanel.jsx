// src/components/panels/TrustPanel.jsx
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ReferenceLine, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import { useStore } from '../../store/useStore'
import s from './TrustPanel.module.css'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className={s.tooltip}>
      <div>Run {label}</div>
      <div>Trust: <strong>{d.score.toFixed(3)}</strong></div>
      <div>Mode: {d.mode}</div>
    </div>
  )
}

export default function TrustPanel() {
  const { trustHistory } = useStore()

  const data = trustHistory.slice(-10).map((h, i) => ({
    run:   h.run ?? i + 1,
    score: h.score ?? 0,
    mode:  h.mode ?? 'interpreter',
  }))

  if (!data.length) {
    return <div className={s.empty}>Run code to see trust score history.</div>
  }

  return (
    <div className={s.panel}>
      <div className={s.header}>
        <span>Trust Score History</span>
        <span className={s.hint}>Last {data.length} runs</span>
      </div>
      <div className={s.chart}>
        <ResponsiveContainer width="100%" height={140}>
          <LineChart data={data} margin={{ top: 10, right: 16, bottom: 4, left: 0 }}>
            <CartesianGrid vertical={false} stroke="#3c3c3c" strokeDasharray="3 3" />
            <XAxis
              dataKey="run"
              tick={{ fontSize: 10, fill: '#858585', fontFamily: 'Consolas,monospace' }}
              tickLine={false}
              axisLine={{ stroke: '#3c3c3c' }}
              label={{ value: 'Run', position: 'insideBottom', offset: -2, fill: '#858585', fontSize: 10 }}
            />
            <YAxis
              domain={[0, 1.2]}
              tick={{ fontSize: 10, fill: '#858585', fontFamily: 'Consolas,monospace' }}
              tickLine={false}
              axisLine={false}
              width={30}
            />
            <ReferenceLine
              y={1.0}
              stroke="#4ec9b0"
              strokeDasharray="4 3"
              label={{ value: 'Optimized', position: 'right', fontSize: 9, fill: '#4ec9b0' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#007acc"
              strokeWidth={1.5}
              dot={{ fill: '#007acc', r: 3, strokeWidth: 0 }}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Table */}
      <div className={s.table}>
        <div className={s.tableHeader}>
          <span>Run</span><span>Score</span><span>Mode</span>
        </div>
        {[...data].reverse().map((d, i) => (
          <div key={i} className={s.row}>
            <span className={s.mono}>#{d.run}</span>
            <span className={`${s.mono} ${d.score >= 1.0 ? s.scoreHigh : ''}`}>
              {d.score.toFixed(3)}
            </span>
            <span className={`${s.mode} ${d.mode === 'optimized' ? s.modeOpt : ''}`}>
              {d.mode}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
