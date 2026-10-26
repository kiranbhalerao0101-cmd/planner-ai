// In production (Vercel), VITE_API_URL points to the Render backend.
// In development, it's empty so the Vite proxy handles /api → localhost:8000.
const BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : '/api'

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(`${BASE}${path}`, opts)
  if (res.status === 204) return null
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
  return data
}

// ─── Tasks ────────────────────────────────────────────────────────────────────

export function getTasks(filters = {}) {
  const params = new URLSearchParams()
  if (filters.status) params.set('status', filters.status)
  if (filters.priority) params.set('priority', filters.priority)
  if (filters.due_before) params.set('due_before', filters.due_before)
  if (filters.due_after) params.set('due_after', filters.due_after)
  const qs = params.toString()
  return request('GET', `/tasks${qs ? '?' + qs : ''}`)
}

export function createTask(data) {
  return request('POST', '/tasks', data)
}

export function updateTask(id, data) {
  return request('PATCH', `/tasks/${id}`, data)
}

export function deleteTask(id) {
  return request('DELETE', `/tasks/${id}`)
}

// ─── Events ──────────────────────────────────────────────────────────────────

export function getEvents(params = {}) {
  const qs = new URLSearchParams()
  if (params.start) qs.set('start', params.start)
  if (params.end) qs.set('end', params.end)
  const q = qs.toString()
  return request('GET', `/events${q ? '?' + q : ''}`)
}

export function createEvent(data) {
  return request('POST', '/events', data)
}

export function updateEvent(id, data) {
  return request('PATCH', `/events/${id}`, data)
}

export function deleteEvent(id) {
  return request('DELETE', `/events/${id}`)
}

// ─── Reminders ───────────────────────────────────────────────────────────────

export function getUpcomingReminders() {
  return request('GET', '/reminders/upcoming')
}

export function createReminder(data) {
  return request('POST', '/reminders', data)
}

// ─── Chat / SSE ──────────────────────────────────────────────────────────────

/**
 * Stream SSE events from the chat endpoint.
 * @param {string} sessionId
 * @param {string} message
 * @param {function} onEvent  called with each parsed event object
 * @returns {Promise<void>}
 */
export async function streamChat(sessionId, message, onEvent) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
    onEvent({ type: 'error', message: err.detail || 'Request failed' })
    onEvent({ type: 'done' })
    return
  }

  await _readSSE(res.body, onEvent)
}

/**
 * Resume a paused agent loop after a confirmation event.
 */
export async function confirmAction(sessionId, confirmed, onEvent) {
  const res = await fetch(`${BASE}/chat/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, confirmed }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
    onEvent({ type: 'error', message: err.detail || 'Confirmation failed' })
    onEvent({ type: 'done' })
    return
  }

  await _readSSE(res.body, onEvent)
}

async function _readSSE(body, onEvent) {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop() // keep incomplete chunk

    for (const chunk of lines) {
      const line = chunk.trim()
      if (!line.startsWith('data:')) continue
      const raw = line.slice('data:'.length).trim()
      try {
        const evt = JSON.parse(raw)
        onEvent(evt)
      } catch {
        // ignore malformed lines
      }
    }
  }
}
