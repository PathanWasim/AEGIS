// src/store/useStore.js — single source of truth for all app state

import { create } from 'zustand'

const DEFAULT_CODE = `# AEGIS — run twice to see Interpreter → Optimized
x = 100
y = 200
total = x + y
count = 0
while count < 5
  print total
  count = count + 1
end
print count`

const WELCOME = { type: 'info', text: 'AEGIS Runtime ready. Press ▶ Run or Ctrl+Enter to execute.' }

export const useStore = create((set) => ({
  // ── Editor
  code: DEFAULT_CODE,
  setCode: (code) => set({ code }),

  // ── Server
  serverOnline: false,
  setServerOnline: (v) => set({ serverOnline: v }),

  // ── Execution state
  running:    false,
  setRunning: (v) => set({ running: v }),

  result:    null,   // last full /api/execute response
  setResult: (r) => set({ result: r }),

  // ── Trust history for Recharts
  trustHistory: [],   // [{ run, score, mode }]
  appendTrust: (entry) =>
    set(s => ({ trustHistory: [...s.trustHistory.slice(-19), entry] })),

  runCount:    0,
  incRunCount: () => set(s => ({ runCount: s.runCount + 1 })),

  // ── Bottom tab
  bottomTab:    'terminal',
  setBottomTab: (t) => set({ bottomTab: t }),

  // ── Terminal lines
  terminalLines:  [WELCOME],
  addLine:        (ln) => set(s => ({ terminalLines: [...s.terminalLines, ln] })),
  clearTerminal:  ()   => set({ terminalLines: [WELCOME] }),

  // ── Examples list (populated from /api/examples)
  examples:    [],
  setExamples: (ex) => set({ examples: ex }),
}))

