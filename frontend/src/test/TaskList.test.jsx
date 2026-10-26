import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import TaskList from '../components/TaskList.jsx'

// Mock the API module
vi.mock('../api.js', () => ({
  getTasks: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
}))

import { getTasks, createTask } from '../api.js'

const MOCK_TASKS = [
  { id: 1, title: 'Buy groceries', priority: 'high', status: 'open', due_date: null, description: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: 2, title: 'Write report', priority: 'medium', status: 'completed', due_date: null, description: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
]

beforeEach(() => {
  vi.clearAllMocks()
  getTasks.mockResolvedValue(MOCK_TASKS)
})

describe('TaskList', () => {
  it('renders tasks after loading', async () => {
    render(<TaskList />)
    await waitFor(() => {
      expect(screen.getByText('Buy groceries')).toBeInTheDocument()
      expect(screen.getByText('Write report')).toBeInTheDocument()
    })
  })

  it('shows filter tabs', async () => {
    render(<TaskList />)
    expect(screen.getByText('all')).toBeInTheDocument()
    expect(screen.getByText('open')).toBeInTheDocument()
    expect(screen.getByText('completed')).toBeInTheDocument()
  })

  it('opens the new task modal when "New Task" button is clicked', async () => {
    render(<TaskList />)
    const btn = screen.getByText('New Task')
    fireEvent.click(btn)
    await waitFor(() => {
      expect(screen.getByText('New Task', { selector: 'h2' }) || screen.getByPlaceholderText('Task title')).toBeInTheDocument()
    })
  })

  it('shows empty state when no tasks', async () => {
    getTasks.mockResolvedValue([])
    render(<TaskList />)
    await waitFor(() => {
      expect(screen.getByText('No tasks found')).toBeInTheDocument()
    })
  })

  it('shows priority badges', async () => {
    render(<TaskList />)
    await waitFor(() => {
      expect(screen.getByText('high')).toBeInTheDocument()
      expect(screen.getByText('medium')).toBeInTheDocument()
    })
  })
})
