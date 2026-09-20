async function request(path, options) {
  const r = await fetch(path, options)
  if (!r.ok) {
    const text = await r.text()
    let msg = text
    try { msg = JSON.parse(text).detail || text } catch { /* 保留原文 */ }
    throw new Error(msg)
  }
  return r.json()
}
export function getJSON(path) {
  return request(path)
}
export function postJSON(path, body) {
  return request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
}
export function patchJSON(path, body) {
  return request(path, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
}
