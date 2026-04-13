import s from './ActivityBar.module.css'
import { Code2, Shield, Settings } from 'lucide-react'

const items = [
  { id: 'explorer', Icon: Code2,   title: 'Explorer'  },
  { id: 'trust',    Icon: Shield,  title: 'Trust'     },
  { id: 'settings', Icon: Settings, title: 'Settings' },
]

export default function ActivityBar({ active, onSwitch }) {
  return (
    <div className={s.bar}>
      {items.map(({ id, Icon, title }) => (
        <button
          key={id}
          className={`${s.btn} ${active === id ? s.active : ''}`}
          onClick={() => onSwitch(active === id ? null : id)}
          title={title}
        >
          <Icon size={22} strokeWidth={1.5} />
          {active === id && <span className={s.indicator} />}
        </button>
      ))}
    </div>
  )
}
