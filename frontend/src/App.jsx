import { useState, useCallback } from 'react'
import { Toaster, toast } from 'react-hot-toast'
import Sidebar from './components/Sidebar.jsx'
import Dashboard from './components/Dashboard.jsx'
import TaskList from './components/TaskList.jsx'
import CalendarView from './components/CalendarView.jsx'
import ChatPanel from './components/ChatPanel.jsx'
import RemindersPanel from './components/RemindersPanel.jsx'

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')

  const showNotification = useCallback((message, type = 'success') => {
    if (type === 'success') toast.success(message)
    else if (type === 'error') toast.error(message)
    else toast(message)
  }, [])

  function renderPage() {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard onNavigate={setCurrentPage} showNotification={showNotification} />
      case 'tasks':
        return <TaskList showNotification={showNotification} />
      case 'calendar':
        return <CalendarView showNotification={showNotification} />
      case 'chat':
        return <div className="h-full flex flex-col"><ChatPanel /></div>
      case 'reminders':
        return (
          <div className="p-6 max-w-2xl mx-auto">
            <h1 className="text-2xl font-bold text-slate-800 mb-6">Reminders</h1>
            <RemindersPanel />
          </div>
        )
      default:
        return <Dashboard onNavigate={setCurrentPage} />
    }
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Toaster
        position="top-right"
        toastOptions={{
          success: { className: '!bg-white !text-slate-700 !shadow-lg !border !border-slate-200' },
          error: { className: '!bg-white !text-red-600 !shadow-lg !border !border-red-200' },
        }}
      />

      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />

      <main className="flex-1 overflow-y-auto min-w-0">
        {renderPage()}
      </main>
    </div>
  )
}
