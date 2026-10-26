import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import Dashboard from '../components/Dashboard.jsx'

vi.mock('../api.js', () => ({
  getTasks: vi.fn(),
  getEvents: vi.fn(),
  getUpcomingReminders: vi.fn(),
}))

import { getTasks, getEvents, getUpcomingReminders } from '../api.js'

beforeEach(() => {
  vi.clearAllMocks()
  getTasks.mockResolvedValue([])
  getEvents.mockResolvedValue([])
  getUpcomingReminders.mockResolvedValue([])
})

describe('Dashboard', () => {
  it('renders stat cards', async () => {
    render(<Dashboard onNavigate={vi.fn()} />)
    await waitFor(() => {
      expect(screen.getByText('Open Tasks')).toBeInTheDocument()
      expect(screen.getByText("Today's Events")).toBeInTheDocument()
      expect(screen.getByText('Reminders')).toBeInTheDocument()
    })
  })

  it('renders Plan My Week button', () => {
    render(<Dashboard onNavigate={vi.fn()} />)
    expect(screen.getByText('Plan My Week')).toBeInTheDocument()
  })

  it('shows zero counts when no data', async () => {
    render(<Dashboard onNavigate={vi.fn()} />)
    await waitFor(() => {
      const zeros = screen.getAllByText('0')
      expect(zeros.length).toBeGreaterThanOrEqual(3)
    })
  })

  it('shows task count with data', async () => {
    getTasks.mockResolvedValue([
      { id: 1, title: 'Task A', status: 'open', priority: 'high', due_date: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ])
    render(<Dashboard onNavigate={vi.fn()} />)
    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument()
    })
  })

  it('shows empty state for today schedule when no events', async () => {
    render(<Dashboard onNavigate={vi.fn()} />)
    await waitFor(() => {
      expect(screen.getByText('No events today')).toBeInTheDocument()
    })
  })
})
