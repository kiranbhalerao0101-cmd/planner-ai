import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ChatPanel from '../components/ChatPanel.jsx'

vi.mock('../api.js', () => ({
  streamChat: vi.fn(),
  confirmAction: vi.fn(),
}))

import { streamChat, confirmAction } from '../api.js'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ChatPanel', () => {
  it('renders the input area', () => {
    streamChat.mockImplementation(async () => {})
    render(<ChatPanel />)
    expect(screen.getByPlaceholderText(/Ask me to plan/i)).toBeInTheDocument()
  })

  it('shows suggestion prompts when empty', () => {
    render(<ChatPanel />)
    expect(screen.getByText('Plan my week')).toBeInTheDocument()
  })

  it('displays user message and assistant response', async () => {
    streamChat.mockImplementation(async (sessionId, message, onEvent) => {
      onEvent({ type: 'text', content: 'You have 2 tasks.' })
      onEvent({ type: 'done' })
    })

    render(<ChatPanel />)
    const input = screen.getByPlaceholderText(/Ask me to plan/i)
    fireEvent.change(input, { target: { value: 'List tasks' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

    await waitFor(() => {
      expect(screen.getByText('List tasks')).toBeInTheDocument()
      expect(screen.getByText('You have 2 tasks.')).toBeInTheDocument()
    })
  })

  it('shows confirmation buttons on confirmation_required event', async () => {
    streamChat.mockImplementation(async (sessionId, message, onEvent) => {
      onEvent({
        type: 'confirmation_required',
        message: 'Are you sure you want to delete this task?',
        tool: 'delete_task',
        task_id: 1,
      })
      onEvent({ type: 'done' })
    })

    render(<ChatPanel />)
    const input = screen.getByPlaceholderText(/Ask me to plan/i)
    fireEvent.change(input, { target: { value: 'Delete my task' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

    await waitFor(() => {
      expect(screen.getByText(/Are you sure you want to delete/i)).toBeInTheDocument()
      expect(screen.getByText('Confirm')).toBeInTheDocument()
      expect(screen.getByText('Cancel')).toBeInTheDocument()
    })
  })

  it('shows error message on error event', async () => {
    streamChat.mockImplementation(async (sessionId, message, onEvent) => {
      onEvent({ type: 'error', message: 'API key not configured' })
      onEvent({ type: 'done' })
    })

    render(<ChatPanel />)
    const input = screen.getByPlaceholderText(/Ask me to plan/i)
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

    await waitFor(() => {
      expect(screen.getByText(/API key not configured/i)).toBeInTheDocument()
    })
  })
})
