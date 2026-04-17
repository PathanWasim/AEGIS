// src/services/api.js — all backend API calls

const BASE = '/api'

async function post(endpoint, body) {
  const res = await fetch(`${BASE}/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return res.json()
}

async function get(endpoint) {
  const res = await fetch(`${BASE}/${endpoint}`)
  return res.json()
}

export const api = {
  execute:    (code)  => post('execute',  { code }),
  tokenize:   (code)  => post('tokenize', { code }),
  analyze:    (code)  => post('analyze',  { code }),
  health:     ()      => get('health'),
  examples:   ()      => get('examples'),
  resetTrust: ()      => fetch(`${BASE}/trust/reset`, { method: 'POST' }).then(r => r.json()),
}
