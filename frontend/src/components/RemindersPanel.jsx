import { useState, useEffect } from 'react'
import { Bell, RefreshCw } from 'lucide-react'
import { getUpcomingReminders } from '../api.js'

function relativeTime(isoStr) {
  const target = new Date(isoStr)
  const now = new Date()
  const diffMs = target - now
  const diffMin = Math.round(diffMs / 60000)
  if (diffMin < 0) return 'overdue'
  if (diffMin < 60) return `in ${diffMin} min`
  const diffHr = Math.round(diffMin / 60)
  if (diffHr < 24) return `in ${diffHr}h`
  const diffDays = Math.round(diffHr / 24)
  return `in ${diffDays} day${diffDays !== 1 ? 's' : ''}`
}

export default function RemindersPanel() {
  const [reminders, setReminders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await getUpcomingReminders()
      setReminders(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-orange-500" />
          <h2 className="text-base font-semibold text-slate-800">Upcoming Reminders</h2>
        </div>
        <button
          onClick={load}
          className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          aria-label="Refresh reminders"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {loading && (
        <div className="flex justify-center py-8">
          <div className="w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <p className="text-sm text-red-500 py-4 text-center">{error}</p>
      )}

      {!loading && !error && reminders.length === 0 && (
        <div className="text-center py-8">
          <Bell className="w-10 h-10 text-slate-200 mx-auto mb-2" />
          <p className="text-sm text-slate-400">No upcoming reminders</p>
        </div>
      )}

      {!loading && !error && reminders.length > 0 && (
        <ul className="space-y-3">
          {reminders.map((r) => (
            <li key={r.id} className="flex items-start gap-3 p-3 bg-orange-50 rounded-xl border border-orange-100">
              <div className="p-1.5 bg-orange-100 rounded-full mt-0.5">
                <Bell className="w-3.5 h-3.5 text-orange-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-700 font-medium">
                  {r.message || (r.task_id ? `Task reminder` : `Event reminder`)}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {new Date(r.remind_at).toLocaleString()} &middot; {relativeTime(r.remind_at)}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
