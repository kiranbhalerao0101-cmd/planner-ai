import { useState } from 'react'
import { ChevronDown, ChevronRight, CheckCircle, XCircle, Loader } from 'lucide-react'

const TOOL_COLORS = {
  list_tasks: 'bg-blue-50 border-blue-200 text-blue-700',
  create_task: 'bg-blue-50 border-blue-200 text-blue-700',
  update_task: 'bg-blue-50 border-blue-200 text-blue-700',
  delete_task: 'bg-red-50 border-red-200 text-red-700',
  get_events: 'bg-green-50 border-green-200 text-green-700',
  schedule_task: 'bg-green-50 border-green-200 text-green-700',
  reschedule_task: 'bg-green-50 border-green-200 text-green-700',
  set_reminder: 'bg-orange-50 border-orange-200 text-orange-700',
  find_free_slots: 'bg-purple-50 border-purple-200 text-purple-700',
}

function JsonViewer({ data, label }) {
  const [open, setOpen] = useState(false)
  const str = JSON.stringify(data, null, 2)
  if (!str || str === '{}' || str === 'null') return null
  return (
    <div className="mt-1">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 transition-colors"
      >
        {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        {label}
      </button>
      {open && (
        <pre className="mt-1 p-2 bg-slate-900 text-green-400 rounded text-xs overflow-x-auto max-h-48">
          {str}
        </pre>
      )}
    </div>
  )
}

export default function ToolCallLog({ events = [] }) {
  if (events.length === 0) return null

  // Pair tool_call with its tool_result
  const pairs = []
  const calls = {}
  for (const evt of events) {
    if (evt.type === 'tool_call') {
      calls[evt.name] = { call: evt, result: null }
      pairs.push(calls[evt.name])
    } else if (evt.type === 'tool_result' && calls[evt.name]) {
      calls[evt.name].result = evt
    }
  }

  return (
    <div className="mt-2 space-y-2">
      {pairs.map((pair, i) => {
        const { call, result } = pair
        const colorClass = TOOL_COLORS[call.name] || 'bg-slate-50 border-slate-200 text-slate-700'
        const isError = result?.result?.error
        const isPending = !result

        return (
          <div key={i} className={`border rounded-lg p-3 text-xs ${colorClass}`}>
            <div className="flex items-center gap-2">
              {isPending ? (
                <Loader className="w-3.5 h-3.5 animate-spin" />
              ) : isError ? (
                <XCircle className="w-3.5 h-3.5 text-red-500" />
              ) : (
                <CheckCircle className="w-3.5 h-3.5 text-green-500" />
              )}
              <span className="font-mono font-semibold">{call.name}</span>
              {isPending && <span className="text-slate-400 italic">running…</span>}
              {isError && <span className="text-red-500">error: {result.result.error}</span>}
            </div>
            <JsonViewer data={call.input} label="inputs" />
            {result && !isError && <JsonViewer data={result.result} label="result" />}
          </div>
        )
      })}
    </div>
  )
}
