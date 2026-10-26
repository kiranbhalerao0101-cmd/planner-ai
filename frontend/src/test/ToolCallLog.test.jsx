import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ToolCallLog from '../components/ToolCallLog.jsx'

describe('ToolCallLog', () => {
  it('renders nothing when events array is empty', () => {
    const { container } = render(<ToolCallLog events={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders tool name for a tool_call event', () => {
    const events = [
      { type: 'tool_call', name: 'list_tasks', input: { status: 'open' } },
    ]
    render(<ToolCallLog events={events} />)
    expect(screen.getByText('list_tasks')).toBeInTheDocument()
  })

  it('shows success icon when tool result is present', () => {
    const events = [
      { type: 'tool_call', name: 'create_task', input: { title: 'Test' } },
      { type: 'tool_result', name: 'create_task', result: { success: true, task: { id: 1, title: 'Test' } } },
    ]
    render(<ToolCallLog events={events} />)
    expect(screen.getByText('create_task')).toBeInTheDocument()
  })

  it('shows error indicator when result has error', () => {
    const events = [
      { type: 'tool_call', name: 'delete_task', input: { task_id: 999, confirmed: true } },
      { type: 'tool_result', name: 'delete_task', result: { error: 'Task 999 not found' } },
    ]
    render(<ToolCallLog events={events} />)
    expect(screen.getByText(/Task 999 not found/)).toBeInTheDocument()
  })
})
