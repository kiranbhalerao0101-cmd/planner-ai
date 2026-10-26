import { useState, useRef } from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { X, AlertCircle } from 'lucide-react'
import { getEvents, createEvent, updateEvent, deleteEvent } from '../api.js'

const EMPTY_FORM = { title: '', description: '', start_time: '', end_time: '' }

export default function CalendarView({ showNotification }) {
  const calRef = useRef(null)
  const [showModal, setShowModal] = useState(false)
  const [editingEvent, setEditingEvent] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  function toLocalDatetimeInput(isoStr) {
    if (!isoStr) return ''
    const d = new Date(isoStr)
    const offset = d.getTimezoneOffset()
    const local = new Date(d.getTime() - offset * 60000)
    return local.toISOString().slice(0, 16)
  }

  async function loadEvents(fetchInfo, successCb, failureCb) {
    try {
      const events = await getEvents({
        start: fetchInfo.startStr,
        end: fetchInfo.endStr,
      })
      successCb(events.map(e => ({
        id: String(e.id),
        title: e.title,
        start: e.start_time,
        end: e.end_time,
        extendedProps: { description: e.description, task_id: e.task_id },
        backgroundColor: e.task_id ? '#6366f1' : '#0d9488',
        borderColor: e.task_id ? '#4f46e5' : '#0f766e',
      })))
    } catch (e) {
      failureCb(e)
    }
  }

  function openCreate(dateStr) {
    setEditingEvent(null)
    const start = dateStr ? new Date(dateStr) : new Date()
    const end = new Date(start.getTime() + 60 * 60000)
    setForm({
      title: '',
      description: '',
      start_time: toLocalDatetimeInput(start.toISOString()),
      end_time: toLocalDatetimeInput(end.toISOString()),
    })
    setError(null)
    setShowModal(true)
  }

  function openEdit(info) {
    const evt = info.event
    setEditingEvent({ id: evt.id, ...evt.extendedProps })
    setForm({
      title: evt.title,
      description: evt.extendedProps.description || '',
      start_time: toLocalDatetimeInput(evt.start?.toISOString()),
      end_time: toLocalDatetimeInput(evt.end?.toISOString()),
    })
    setError(null)
    setShowModal(true)
  }

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload = {
        title: form.title,
        description: form.description || null,
        start_time: new Date(form.start_time).toISOString(),
        end_time: new Date(form.end_time).toISOString(),
      }
      if (editingEvent) {
        await updateEvent(editingEvent.id, payload)
        showNotification?.('Event updated', 'success')
      } else {
        await createEvent(payload)
        showNotification?.('Event created', 'success')
      }
      setShowModal(false)
      calRef.current?.getApi().refetchEvents()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!editingEvent) return
    setSaving(true)
    try {
      await deleteEvent(editingEvent.id)
      showNotification?.('Event deleted', 'success')
      setShowModal(false)
      calRef.current?.getApi().refetchEvents()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Calendar</h1>
        <p className="text-sm text-slate-500 mt-0.5">Click a day or time slot to add an event</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-4">
        <FullCalendar
          ref={calRef}
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay',
          }}
          events={loadEvents}
          selectable={true}
          selectMirror={true}
          dayMaxEvents={3}
          weekends={true}
          select={(selectInfo) => openCreate(selectInfo.startStr)}
          eventClick={openEdit}
          height="auto"
        />
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowModal(false)} />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 z-10">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-slate-800">
                {editingEvent ? 'Edit Event' : 'New Event'}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl mb-4">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Title *</label>
                <input
                  type="text"
                  required
                  value={form.title}
                  onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Event title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <textarea
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Start *</label>
                  <input
                    type="datetime-local"
                    required
                    value={form.start_time}
                    onChange={e => setForm(f => ({ ...f, start_time: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">End *</label>
                  <input
                    type="datetime-local"
                    required
                    value={form.end_time}
                    onChange={e => setForm(f => ({ ...f, end_time: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
              <div className="flex gap-3 justify-end pt-2">
                {editingEvent && (
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={saving}
                    className="px-4 py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-xl transition-colors disabled:opacity-50 mr-auto"
                  >
                    Delete
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-xl transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving…' : (editingEvent ? 'Save' : 'Create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
