import { useState, useEffect } from 'react'
import { CheckSquare, Calendar, Bell, TrendingUp, Plus, MessageCircle } from 'lucide-react'
import { getTasks, getEvents, getUpcomingReminders } from '../api.js'
import RemindersPanel from './RemindersPanel.jsx'

function StatCard({ icon: Icon, label, value, color, loading }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 flex items-center gap-4">
      <div className={`p-3 rounded-xl ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-800">
          {loading ? <span className="inline-block w-6 h-6 bg-slate-200 rounded animate-pulse" /> : value}
        </p>
        <p className="text-sm text-slate-500">{label}</p>
      </div>
    </div>
  )
}

function today() {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
}
function tomorrow() {
  const d = today()
  d.setDate(d.getDate() + 1)
  return d
}

const PRIORITY_COLORS = {
  high: 'bg-red-100 text-red-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
}

export default function Dashboard({ onNavigate }) {
  const [tasks, setTasks] = useState([])
  const [todayEvents, setTodayEvents] = useState([])
  const [reminders, setReminders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [t, e, r] = await Promise.all([
          getTasks(),
          getEvents({ start: today().toISOString(), end: tomorrow().toISOString() }),
          getUpcomingReminders(),
        ])
        setTasks(t)
        setTodayEvents(e)
        setReminders(r)
      } catch {
        // errors handled per-component
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const openTasks = tasks.filter(t => t.status === 'open').length
  const completedTasks = tasks.filter(t => t.status === 'completed').length

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <button
          onClick={() => onNavigate('chat')}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-sm font-medium transition-colors shadow-sm"
        >
          <MessageCircle className="w-4 h-4" />
          Plan My Week
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={CheckSquare} label="Open Tasks" value={openTasks} color="bg-primary-500" loading={loading} />
        <StatCard icon={TrendingUp} label="Completed" value={completedTasks} color="bg-green-500" loading={loading} />
        <StatCard icon={Calendar} label="Today's Events" value={todayEvents.length} color="bg-blue-500" loading={loading} />
        <StatCard icon={Bell} label="Reminders" value={reminders.length} color="bg-orange-500" loading={loading} />
      </div>

      {/* Bottom grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Today's schedule */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-slate-800">Today's Schedule</h2>
            <button
              onClick={() => onNavigate('calendar')}
              className="text-xs text-primary-600 hover:underline"
            >
              View calendar →
            </button>
          </div>
          {loading && (
            <div className="space-y-2">
              {[1, 2].map(i => <div key={i} className="h-12 bg-slate-100 rounded-xl animate-pulse" />)}
            </div>
          )}
          {!loading && todayEvents.length === 0 && (
            <div className="text-center py-8">
              <Calendar className="w-10 h-10 text-slate-200 mx-auto mb-2" />
              <p className="text-sm text-slate-400">No events today</p>
              <button
                onClick={() => onNavigate('calendar')}
                className="mt-2 text-xs text-primary-600 hover:underline"
              >
                Add an event
              </button>
            </div>
          )}
          {!loading && todayEvents.map(evt => (
            <div key={evt.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl mb-2">
              <div className="w-1 h-10 bg-primary-500 rounded-full" />
              <div>
                <p className="text-sm font-medium text-slate-700">{evt.title}</p>
                <p className="text-xs text-slate-400">
                  {new Date(evt.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} –{' '}
                  {new Date(evt.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Recent tasks */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-slate-800">Recent Tasks</h2>
            <button
              onClick={() => onNavigate('tasks')}
              className="flex items-center gap-1 text-xs text-primary-600 hover:underline"
            >
              <Plus className="w-3 h-3" /> New task
            </button>
          </div>
          {loading && (
            <div className="space-y-2">
              {[1, 2, 3].map(i => <div key={i} className="h-10 bg-slate-100 rounded-xl animate-pulse" />)}
            </div>
          )}
          {!loading && tasks.length === 0 && (
            <div className="text-center py-8">
              <CheckSquare className="w-10 h-10 text-slate-200 mx-auto mb-2" />
              <p className="text-sm text-slate-400">No tasks yet</p>
              <button
                onClick={() => onNavigate('tasks')}
                className="mt-2 text-xs text-primary-600 hover:underline"
              >
                Create your first task
              </button>
            </div>
          )}
          {!loading && tasks.slice(0, 5).map(task => (
            <div key={task.id} className="flex items-center gap-3 py-2.5 border-b border-slate-100 last:border-0">
              <div className={`w-2 h-2 rounded-full ${
                task.status === 'completed' ? 'bg-green-400' :
                task.status === 'in_progress' ? 'bg-blue-400' : 'bg-slate-300'
              }`} />
              <span className={`flex-1 text-sm ${task.status === 'completed' ? 'line-through text-slate-400' : 'text-slate-700'}`}>
                {task.title}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PRIORITY_COLORS[task.priority]}`}>
                {task.priority}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Reminders panel */}
      <RemindersPanel />
    </div>
  )
}
