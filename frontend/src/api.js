async function parse(r) {
  if (r.ok) return r.json()
  let msg = await r.text()
  try { const j = JSON.parse(msg); if (j.detail) msg = j.detail } catch { /* keep raw text */ }
  throw new Error(msg)
}
export async function getJSON(path) {
  return parse(await fetch(path))
}
export async function postJSON(path, body) {
  return parse(await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body ?? {}) }))
}
export async function putJSON(path, body) {
  return parse(await fetch(path, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body ?? {}) }))
}
