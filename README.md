# 🗓️ Personal Task & Calendar AI Agent

A full-stack AI agent that plans your week. Type **"plan my week"** and the agent creates tasks, schedules them on a calendar, sets reminders, and reschedules when plans change. Every tool call the AI makes is shown live in the UI.

> Built with **FastAPI**, **React**, **SQLite**, and the **Claude API** (tool use).

---

## 🚀 Quick Start (Windows PowerShell)

### Prerequisites
- Python 3.11+ — verify: `python --version`
- Node.js 18+ — verify: `node --version`
- An Anthropic API key from https://console.anthropic.com

### 1. Backend Setup

```powershell
# From the workspace root: d:\Ai agent
cd backend

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Open .env and set your ANTHROPIC_API_KEY
notepad .env

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

Backend runs at **http://localhost:8000**  
Interactive API docs at **http://localhost:8000/docs**

### 2. Frontend Setup

Open a second PowerShell terminal:

```powershell
cd "d:\Ai agent\frontend"
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**

### 3. Open the App

Navigate to **http://localhost:5173** and try:
- "Plan my week"
- "Add a task to submit the lab report by Friday 5 PM"
- "What's on my plate tomorrow?"
- "Find free time on Wednesday morning"

---

## 🔐 Environment Variables

Create `backend/.env` (copy from `backend/.env.example`):

```env
ANTHROPIC_API_KEY=your_api_key_here
MODEL=claude-opus-4-5
DATABASE_URL=sqlite:///./planner.db
MAX_AGENT_STEPS=8
CORS_ORIGINS=http://localhost:5173
```

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Claude API key — **never commit this** |
| `MODEL` | Claude model for the agent |
| `DATABASE_URL` | SQLAlchemy connection string (SQLite by default) |
| `MAX_AGENT_STEPS` | Safety cap on tool-use iterations per message |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) |

> **Note:** The app starts without an API key, but AI chat will show a configuration error. All task/event/reminder APIs work normally.

---

## 🧪 Running Tests

### Backend tests (49 tests)

```powershell
cd "d:\Ai agent\backend"
.\.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

### Frontend tests (19 tests)

```powershell
cd "d:\Ai agent\frontend"
npm test
```

All tests use isolated in-memory databases and mocked API calls. No real Anthropic API key is required.

---

## 📁 Project Structure

```
d:\Ai agent\
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── config.py          # Settings (pydantic-settings)
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── models.py          # Task, Event, Reminder ORM models
│   │   ├── schemas.py         # Pydantic v2 schemas
│   │   ├── routes/
│   │   │   ├── tasks.py       # GET/POST/PATCH/DELETE /api/tasks
│   │   │   ├── events.py      # GET/POST/PATCH/DELETE /api/events
│   │   │   ├── reminders.py   # POST /api/reminders, GET /api/reminders/upcoming
│   │   │   └── chat.py        # POST /api/chat (SSE), POST /api/chat/confirm
│   │   └── agent/
│   │       ├── loop.py        # Claude agent loop (async generator)
│   │       ├── tools.py       # Tool schemas + Python implementations
│   │       ├── executor.py    # Tool dispatch
│   │       └── prompts.py     # System prompt
│   ├── tests/
│   │   ├── conftest.py        # Test fixtures (in-memory DB)
│   │   ├── test_tasks.py
│   │   ├── test_events.py
│   │   ├── test_reminders.py
│   │   └── test_agent.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── App.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── TaskList.jsx
│   │   │   ├── CalendarView.jsx
│   │   │   ├── ChatPanel.jsx
│   │   │   ├── ToolCallLog.jsx
│   │   │   ├── RemindersPanel.jsx
│   │   │   └── ConfirmDialog.jsx
│   │   ├── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 🛠️ AI Agent Tools

| Tool | Purpose |
|---|---|
| `list_tasks` | Fetch tasks with optional status/date filters |
| `create_task` | Create a new task |
| `update_task` | Edit title, priority, status, etc. |
| `delete_task` | Remove a task (requires user confirmation) |
| `get_events` | Read calendar events in a range |
| `schedule_task` | Place a task into a calendar slot |
| `reschedule_task` | Move a scheduled task |
| `set_reminder` | Attach a reminder to a task or event |
| `find_free_slots` | Find open time windows (9 AM–6 PM) |

---

## 📡 API Reference

### Tasks
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/tasks` | List tasks (`?status=`, `?priority=`, `?due_before=`, `?due_after=`) |
| POST | `/api/tasks` | Create task |
| GET | `/api/tasks/{id}` | Get task |
| PATCH | `/api/tasks/{id}` | Update task |
| DELETE | `/api/tasks/{id}` | Delete task |

### Events
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/events` | List events (`?start=`, `?end=`) |
| POST | `/api/events` | Create event (409 on conflict) |
| GET | `/api/events/{id}` | Get event |
| PATCH | `/api/events/{id}` | Update event |
| DELETE | `/api/events/{id}` | Delete event |

### Reminders
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/reminders` | Create reminder |
| GET | `/api/reminders/upcoming` | List upcoming reminders |

### Agent
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Send message; streams SSE events |
| POST | `/api/chat/confirm` | Approve/reject a pending destructive action |

---

## 🏗️ Architecture

```
React UI (port 5173)
    │  HTTP / SSE
    ▼
FastAPI Backend (port 8000)
    │
    ├── /api/tasks, /api/events, /api/reminders  ──► SQLite DB
    │
    └── /api/chat ──► Agent Loop
                          │
                          ├── Claude API (tool use)
                          │       │ tool_use blocks
                          │       ▼
                          └── Tool Executor ──► SQLite DB
                                    │
                                    └── SSE stream back to UI
```

---

## 🔒 Security Notes

- API key lives in `backend/.env` only — never the frontend
- All inputs validated with Pydantic before touching the database
- CORS restricted to configured origins
- Destructive tool calls require explicit user confirmation
- Task text is treated as untrusted data (never injected into system prompt)

---

## 🗺️ Roadmap

- [ ] Google Calendar sync
- [ ] Email / push notification delivery
- [ ] Recurring tasks
- [ ] Multi-user accounts with auth
- [ ] Docker Compose setup
- [ ] Dark mode
