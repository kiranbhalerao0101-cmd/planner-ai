import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, MessageCircle, CheckCircle, XCircle } from 'lucide-react'
import { streamChat, confirmAction } from '../api.js'
import ToolCallLog from './ToolCallLog.jsx'

const SESSION_ID = `session_${Date.now()}`

const SUGGESTIONS = [
  'Plan my week',
  "What's due today?",
  'Find free time tomorrow morning',
  'Create a task to review the project',
  "What's on my calendar this week?",
]

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 p-3">
      <div className="w-7 h-7 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-primary-600" />
      </div>
      <div className="flex gap-1 bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3">
        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:0ms]" />
        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:150ms]" />
        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:300ms]" />
      </div>
    </div>
  )
}

export default function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [pendingConfirm, setPendingConfirm] = useState(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streaming])

  function addMessage(role, content, toolEvents = []) {
    setMessages(prev => [...prev, { role, content, toolEvents, id: Date.now() + Math.random() }])
  }

  function updateLastAssistantMessage(patch) {
    setMessages(prev => {
      const copy = [...prev]
      for (let i = copy.length - 1; i >= 0; i--) {
        if (copy[i].role === 'assistant') {
          copy[i] = { ...copy[i], ...patch }
          break
        }
      }
      return copy
    })
  }

  function appendToolEvent(evt) {
    setMessages(prev => {
      const copy = [...prev]
      for (let i = copy.length - 1; i >= 0; i--) {
        if (copy[i].role === 'assistant') {
          copy[i] = {
            ...copy[i],
            toolEvents: [...(copy[i].toolEvents || []), evt],
          }
          break
        }
      }
      return copy
    })
  }

  async function handleSend(text) {
    const msg = (text || input).trim()
    if (!msg || streaming) return
    setInput('')
    addMessage('user', msg)
    // Placeholder assistant message
    setMessages(prev => [...prev, { role: 'assistant', content: '', toolEvents: [], id: Date.now() }])
    setStreaming(true)

    await streamChat(SESSION_ID, msg, (evt) => {
      if (evt.type === 'text') {
        updateLastAssistantMessage(prev => ({
          content: (prev.content || '') + evt.content,
        }))
        // actually we need the functional updater differently:
        setMessages(prev => {
          const copy = [...prev]
          for (let i = copy.length - 1; i >= 0; i--) {
            if (copy[i].role === 'assistant') {
              copy[i] = { ...copy[i], content: (copy[i].content || '') + evt.content }
              break
            }
          }
          return copy
        })
      } else if (evt.type === 'tool_call' || evt.type === 'tool_result') {
        appendToolEvent(evt)
      } else if (evt.type === 'confirmation_required') {
        setPendingConfirm(evt)
        setStreaming(false)
      } else if (evt.type === 'error') {
        setMessages(prev => {
          const copy = [...prev]
          for (let i = copy.length - 1; i >= 0; i--) {
            if (copy[i].role === 'assistant') {
              copy[i] = { ...copy[i], content: `⚠️ ${evt.message}`, isError: true }
              break
            }
          }
          return copy
        })
        setStreaming(false)
      } else if (evt.type === 'done') {
        setStreaming(false)
      }
    })
  }

  async function handleConfirm(confirmed) {
    const confirm = pendingConfirm
    setPendingConfirm(null)

    // Add a note in chat
    addMessage('user', confirmed ? '✅ Confirmed' : '❌ Cancelled')
    setMessages(prev => [...prev, { role: 'assistant', content: '', toolEvents: [], id: Date.now() }])
    setStreaming(true)

    await confirmAction(SESSION_ID, confirmed, (evt) => {
      if (evt.type === 'text') {
        setMessages(prev => {
          const copy = [...prev]
          for (let i = copy.length - 1; i >= 0; i--) {
            if (copy[i].role === 'assistant') {
              copy[i] = { ...copy[i], content: (copy[i].content || '') + evt.content }
              break
            }
          }
          return copy
        })
      } else if (evt.type === 'tool_call' || evt.type === 'tool_result') {
        appendToolEvent(evt)
      } else if (evt.type === 'done') {
        setStreaming(false)
      }
    })
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full max-h-screen">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 bg-white border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-primary-600 rounded-xl flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-slate-800">AI Planner</h1>
            <p className="text-xs text-slate-400">Powered by Claude · tool use enabled</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-16">
            <div className="w-16 h-16 bg-primary-50 rounded-2xl flex items-center justify-center mb-4">
              <MessageCircle className="w-8 h-8 text-primary-500" />
            </div>
            <h2 className="text-lg font-semibold text-slate-700 mb-1">How can I help you today?</h2>
            <p className="text-sm text-slate-400 mb-6 max-w-xs">
              Ask me to plan your week, create tasks, schedule events, or set reminders.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  className="px-3 py-1.5 bg-white border border-slate-200 hover:border-primary-300 hover:bg-primary-50 text-sm text-slate-600 rounded-xl transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex items-start gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-4 h-4 text-primary-600" />
              </div>
            )}

            <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-first' : ''}`}>
              <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary-600 text-white rounded-br-sm'
                  : msg.isError
                    ? 'bg-red-50 text-red-700 border border-red-200 rounded-bl-sm'
                    : 'bg-white text-slate-700 border border-slate-200 rounded-bl-sm'
              }`}>
                {msg.content || (msg.role === 'assistant' && !msg.isError ? '…' : '')}
              </div>

              {/* Tool call log inline */}
              {msg.role === 'assistant' && msg.toolEvents?.length > 0 && (
                <div className="mt-1">
                  <ToolCallLog events={msg.toolEvents} />
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-7 h-7 bg-slate-200 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <User className="w-4 h-4 text-slate-500" />
              </div>
            )}
          </div>
        ))}

        {streaming && <TypingIndicator />}

        {/* Confirmation prompt */}
        {pendingConfirm && (
          <div className="flex justify-start items-start gap-2">
            <div className="w-7 h-7 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
              <Bot className="w-4 h-4 text-primary-600" />
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-2xl rounded-bl-sm px-4 py-3 max-w-sm">
              <p className="text-sm text-yellow-800 font-medium mb-3">{pendingConfirm.message}</p>
              <div className="flex gap-2">
                <button
                  onClick={() => handleConfirm(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded-lg transition-colors"
                >
                  <CheckCircle className="w-3.5 h-3.5" /> Confirm
                </button>
                <button
                  onClick={() => handleConfirm(false)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-lg transition-colors"
                >
                  <XCircle className="w-3.5 h-3.5" /> Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 p-4 bg-white border-t border-slate-200">
        <div className="flex items-end gap-2 bg-slate-50 border border-slate-200 rounded-2xl p-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={streaming || !!pendingConfirm}
            rows={1}
            placeholder={pendingConfirm ? 'Waiting for confirmation…' : 'Ask me to plan your week, add tasks, or schedule events…'}
            className="flex-1 bg-transparent text-sm text-slate-700 placeholder-slate-400 resize-none focus:outline-none px-2 py-1.5 max-h-32"
            style={{ overflowY: 'auto' }}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || streaming || !!pendingConfirm}
            className="p-2 bg-primary-600 hover:bg-primary-700 text-white rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
