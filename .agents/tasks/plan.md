# Implementation Plan — Personal Task & Calendar AI Agent

## Environment

- Python 3.14 (system), Node 26, npm 11 — all available on PATH
- Workspace: `d:\Ai agent\` (empty — greenfield build)
- Backend target: http://localhost:8000
- Frontend target: http://localhost:5173
- No existing code to preserve; build everything from scratch

---

## Phase 1 — Repo Scaffold & Configuration

- [ ] 1. Create every directory and stub `__init__.py` file so imports resolve.

  Create the full directory tree:
  ```
  d:\Ai agent\
  ├── backend\app\routes\
  ├── backend\app\agent\
  ├── backend\tests\
  └── frontend\src\components\
  ```
  Files to create (empty or minimal content):
  - `backend/app/__init__.py`
  - `backend/app/routes/__init__.py`
  - `backend/app/agent/__init__.py`
  - `backend/tests/__init__.py`

  Verify: `python -c "import os; print('ok')"` — just confirms Python is accessible;
  real verification is `pytest --collect-only` in Phase 3 after models exist.

- [ ] 2. Write `backend/requirements.txt` with pinned versions and `backend/.env.example`.

  `requirements.txt`:
  ```
  fastapi==0.111.0
  uvicorn[standard]==0.29.0
  sqlalchemy==2.0.30
  pydantic==2.7.1
  pydantic-settings==2.2.1
  anthropic==0.25.0
  python-dotenv==1.0.1
  httpx==0.27.0
  pytest==8.2.0
  pytest-asyncio==0.23.7
  ```
  Note: Python 3.14 is very new; if any pinned package fails to build, relax the
  patch version to the latest compatible release (e.g. `fastapi>=0.111.0`) and
  document the change. The stack must be kept (FastAPI + SQLAlchemy + Anthropic).

  `.env.example`:
  ```
  ANTHROPIC_API_KEY=your_api_key_here
  MODEL=claude-opus-4-5
  DATABASE_URL=sqlite:///./planner.db
  MAX_AGENT_STEPS=8
  CORS_ORIGINS=http://localhost:5173
  ```

  Files: `backend/requirements.txt`, `backend/.env.example`

  Verify: `pip install -r backend/requirements.txt --dry-run` — no dependency
  resolution errors.

- [ ] 3. Create a Python venv, install backend dependencies, and create `.env`.

  Commands (PowerShell, run from `d:\Ai agent`):
  ```powershell
  python -m venv backend\.venv
  backend\.venv\Scripts\Activate.ps1
  pip install -r backend\requirements.txt
  ```
  Copy `.env.example` to `.env` and leave `ANTHROPIC_API_KEY` as placeholder —
  all tests mock the API so a real key is not required.

  File: `backend/.env` (not committed — add to `.gitignore`)

  Verify: `backend\.venv\Scripts\python.exe -c "import fastapi, sqlalchemy, anthropic; print('deps ok')"` — prints `deps ok`.

---

## Phase 2 — Database, Models, Schemas & Config

- [ ] 4. Write `backend/app/config.py` using `pydantic-settings`.

  Load `ANTHROPIC_API_KEY`, `MODEL`, `DATABASE_URL`, `MAX_AGENT_STEPS` (int),
  `CORS_ORIGINS` (comma-separated string → list) from environment / `.env`.
  Use `model_config = ConfigDict(env_file=".env")`.

  File: `backend/app/config.py`

  Verify: `backend\.venv\Scripts\python.exe -c "from app.config import settings; print(settings.model)"` (run from `backend/`) — prints model name.

- [ ] 5. Write `backend/app/database.py` — SQLAlchemy engine + session factory.

  Use `create_engine(settings.database_url, connect_args={"check_same_thread": False})`.
  Provide `get_db()` FastAPI dependency (yields session, closes on exit).
  Provide `Base` (declarative base) and `init_db()` (calls `Base.metadata.create_all`).

  File: `backend/app/database.py`

  Verify: Covered by model creation test in step 6.

- [ ] 6. Write `backend/app/models.py` — three SQLAlchemy ORM models.

  **Task**: id (PK), title (str, not null), description (str nullable), due_date
  (DateTime nullable), priority (Enum: low/medium/high, default medium), status
  (Enum: open/in_progress/completed/cancelled, default open), created_at
  (DateTime, server_default=now), updated_at (DateTime, onupdate=now).

  **Event**: id (PK), title (str), description (str nullable), start_time
  (DateTime), end_time (DateTime), task_id (FK→tasks.id nullable), created_at.

  **Reminder**: id (PK), task_id (FK nullable), event_id (FK nullable), remind_at
  (DateTime), message (str nullable), sent (Boolean default False), created_at.

  Add relationships: `Task.events`, `Task.reminders`, `Event.reminders`.

  File: `backend/app/models.py`

  Verify: `backend\.venv\Scripts\python.exe -c "from app.database import init_db; init_db(); print('tables ok')"` (run from `backend/`) — creates `planner.db` without errors.

- [ ] 7. Write `backend/app/schemas.py` — Pydantic v2 request/response schemas.

  Use `model_config = ConfigDict(from_attributes=True)` on all response models.

  Define:
  - `TaskCreate`, `TaskUpdate`, `TaskRead`
  - `EventCreate`, `EventUpdate`, `EventRead`
  - `ReminderCreate`, `ReminderRead`
  - `ChatRequest` (session_id: str, message: str, history?: list)
  - `ConfirmRequest` (session_id: str, confirmed: bool)
  - `HealthResponse`

  All datetime fields accept ISO strings; FastAPI serializes them automatically.

  File: `backend/app/schemas.py`

  Verify: `backend\.venv\Scripts\python.exe -c "from app.schemas import TaskCreate; print(TaskCreate(title='x'))"` — no import errors.

---

## Phase 3 — Backend REST Routes

- [ ] 8. Write `backend/app/routes/tasks.py` — full CRUD for tasks.

  Endpoints:
  - `GET /api/tasks` — list (optional query params: status, priority)
  - `POST /api/tasks` — create
  - `GET /api/tasks/{task_id}` — retrieve
  - `PATCH /api/tasks/{task_id}` — partial update
  - `DELETE /api/tasks/{task_id}` — delete

  All DB operations use the `get_db` dependency. Return 404 if record not found.
  Use `TaskRead` as response model.

  File: `backend/app/routes/tasks.py`

- [ ] 9. Write `backend/app/routes/events.py` — full CRUD for calendar events with conflict detection.

  Endpoints same pattern as tasks. On `POST` and `PATCH`, query existing events
  for the same time window:
  ```python
  # overlap condition
  existing.start_time < new_end AND existing.end_time > new_start
  ```
  Return HTTP 409 with `{"detail": "Scheduling conflict with event <id>"}` if
  overlap found (exclude the record being updated from the check).

  File: `backend/app/routes/events.py`

- [ ] 10. Write `backend/app/routes/reminders.py` — reminder creation and upcoming list.

  Endpoints:
  - `POST /api/reminders` — create reminder linked to task or event
  - `GET /api/reminders/upcoming` — return reminders where `remind_at > now` and `sent = False`, ordered ascending

  File: `backend/app/routes/reminders.py`

- [ ] 11. Write `backend/app/main.py` — FastAPI application factory.

  - Instantiate `FastAPI(title="Planner API")`.
  - Call `init_db()` at startup (`@app.on_event("startup")`).
  - Register `CORSMiddleware` using `settings.cors_origins`.
  - Include routers: tasks (`/api`), events (`/api`), reminders (`/api`), chat (`/api`).
  - Add `GET /health` returning `{"status": "ok"}`.

  File: `backend/app/main.py`

  Verify: Run `uvicorn app.main:app --port 8000` (from `backend/`) — server starts
  without import errors. Also verify `curl http://localhost:8000/health` returns
  `{"status":"ok"}`.

- [ ] 12. Write backend tests for tasks, events, and reminders.

  Use pytest with an in-memory SQLite test database. In `backend/tests/conftest.py`:
  - Override `get_db` dependency to use an isolated in-memory DB.
  - Provide a `client` fixture (FastAPI `TestClient`).

  `test_tasks.py`: create, list, get, update, delete; 404 on missing id.
  `test_events.py`: create, list, update, delete; 409 conflict; no 409 when updating own time.
  `test_reminders.py`: create, list upcoming (filters past/sent correctly).

  Files: `backend/tests/conftest.py`, `backend/tests/test_tasks.py`,
  `backend/tests/test_events.py`, `backend/tests/test_reminders.py`

  Verify: `pytest backend/tests/test_tasks.py backend/tests/test_events.py backend/tests/test_reminders.py -v` — all tests pass.

---

## Phase 4 — AI Agent (Tools, Executor, Loop, Prompts)

- [ ] 13. Write `backend/app/agent/prompts.py` — system prompt template.

  The system prompt must:
  - Introduce the assistant as a personal productivity AI.
  - Instruct the model to use tools for all data operations (never guess data).
  - Require confirmation before `delete_task` (set `confirmed=False` first, wait
    for user confirm, then call again with `confirmed=True`).
  - Inject the current datetime (passed as a parameter) so the model can reason
    about "today", "tomorrow", etc.
  - Mention that `find_free_slots` uses 9 AM – 6 PM windows.

  File: `backend/app/agent/prompts.py`

- [ ] 14. Write `backend/app/agent/tools.py` — tool schemas + implementations.

  **Tool schemas** (Claude `tools` list format, JSON Schema input_schema):

  | Tool | Required inputs | Optional inputs |
  |---|---|---|
  | list_tasks | — | status, due_before, due_after |
  | create_task | title | description, due_date, priority |
  | update_task | task_id | title, description, due_date, priority, status |
  | delete_task | task_id, confirmed | — |
  | get_events | — | start, end |
  | schedule_task | task_id, start, end | — |
  | reschedule_task | task_id, new_start, new_end | — |
  | set_reminder | target_id, target_type, remind_at | message |
  | find_free_slots | date, duration_minutes | count (default 3) |

  **Python implementations** — each function accepts `(input_dict, db: Session) -> dict`.
  - `list_tasks`: query with optional filters, return list of task dicts.
  - `create_task`: insert Task, return created task dict.
  - `update_task`: find by id (404 → error dict), apply updates, return updated dict.
  - `delete_task`: if `confirmed=False` return `{"requires_confirmation": True, "message": "..."}`;
    if `confirmed=True` delete and return `{"deleted": true}`.
  - `get_events`: query with optional start/end filters.
  - `schedule_task`: find task, create Event with given times (check overlap → return
    conflict error dict on clash), return event dict.
  - `reschedule_task`: find event by task_id (most recent), update times (check
    overlap), return updated event dict.
  - `set_reminder`: insert Reminder; validate target_type is "task" or "event".
  - `find_free_slots`: generate 30-min slots from 9 AM to 6 PM on given date,
    filter out any that overlap existing events, return up to `count` slots as
    ISO strings.

  All datetime parsing uses `datetime.fromisoformat`.

  File: `backend/app/agent/tools.py`

- [ ] 15. Write `backend/app/agent/executor.py` — dispatch tool calls.

  `execute_tool(tool_name: str, tool_input: dict, db: Session) -> dict`

  Map tool names to functions from `tools.py`. Return `{"error": "Unknown tool"}` for
  unrecognised names. Wrap each call in try/except and return `{"error": str(e)}` on
  unexpected exceptions so the agent loop never crashes on a bad tool call.

  File: `backend/app/agent/executor.py`

- [ ] 16. Write `backend/app/agent/loop.py` — agent loop as an async generator.

  ```python
  async def run_agent_loop(
      session_id: str,
      user_message: str,
      db: Session,
  ) -> AsyncGenerator[dict, None]:
  ```

  Algorithm:
  1. Retrieve or create `conversation_history[session_id]` (module-level dict).
  2. Append `{"role": "user", "content": user_message}` to history.
  3. Yield `{"type": "message_start"}`.
  4. Loop up to `settings.max_agent_steps` times:
     a. Call `anthropic.messages.create(model, system, messages, tools, max_tokens=4096)`.
     b. Yield `{"type": "text", "content": text_block}` for each text block.
     c. For each `tool_use` block:
        - Yield `{"type": "tool_call", "name": ..., "input": ...}`.
        - Execute tool via `executor.execute_tool`.
        - Yield `{"type": "tool_result", "name": ..., "result": ...}`.
        - If result has `requires_confirmation=True`:
          yield `{"type": "confirmation_required", "tool": ..., "message": ...}`.
          Store pending state in a module-level `pending_confirmations[session_id]` dict.
          Return (pause loop).
        - Append assistant message + tool_result to history.
     d. If `stop_reason == "end_turn"` → break.
  5. Yield `{"type": "done"}`.
  6. On Anthropic API error → yield `{"type": "error", "message": str(e)}` and break.

  Expose `confirmation_store: dict` and `history_store: dict` for the confirmation
  endpoint to resume the loop.

  File: `backend/app/agent/loop.py`

- [ ] 17. Write `backend/app/routes/chat.py` — SSE streaming endpoint + confirmation.

  `POST /api/chat` — accepts `ChatRequest` (session_id, message), streams
  `run_agent_loop` as SSE. Each yielded dict becomes `data: {json}\n\n`.
  Use `StreamingResponse(media_type="text/event-stream")`.

  `POST /api/chat/confirm` — accepts `ConfirmRequest` (session_id, confirmed).
  Look up pending state in `confirmation_store`.
  If `confirmed=True`, re-call the tool with `confirmed=True`, continue the loop,
  and return the streamed response.
  If `confirmed=False`, clear pending state and return `{"status": "cancelled"}`.

  File: `backend/app/routes/chat.py`

  Verify: Start server, POST to `/api/chat` with `{"session_id":"s1","message":"list my tasks"}`;
  response should be `text/event-stream` with at least one `data:` line.

- [ ] 18. Write `backend/tests/test_agent.py` — agent and SSE tests with mocked Anthropic.

  Patch `anthropic.Anthropic` (or the module-level client) using `unittest.mock.patch`.

  Tests:
  - Tool execution: each of the 9 tools called directly with a test DB session —
    correct return shape, 404 path, conflict path.
  - Agent loop (mocked Anthropic returning one text block then `end_turn`) yields
    correct event sequence: `message_start`, `text`, `done`.
  - Agent loop with one tool call: mock returns `tool_use` then after tool result
    returns `end_turn`; verify `tool_call` and `tool_result` events are yielded.
  - `delete_task` with `confirmed=False`: verify `confirmation_required` event.
  - MAX_AGENT_STEPS guard: mock always returns `tool_use`; after N steps the loop
    terminates with `done` not an infinite loop.
  - SSE endpoint: `POST /api/chat` with mocked loop returns `200` and
    `content-type: text/event-stream`.
  - Confirmation endpoint: confirm=True resumes, confirm=False cancels.

  File: `backend/tests/test_agent.py`

  Verify: `pytest backend/tests/test_agent.py -v` — all tests pass.

---

## Phase 5 — Frontend Scaffold

- [ ] 19. Initialise the frontend with Vite + React.

  From `d:\Ai agent\`:
  ```powershell
  npm create vite@latest frontend -- --template react
  cd frontend
  npm install
  npm install -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  npm install @fullcalendar/react @fullcalendar/daygrid @fullcalendar/timegrid @fullcalendar/interaction
  npm install react-hot-toast lucide-react
  ```

  Configure `tailwind.config.js`:
  ```js
  content: ["./index.html", "./src/**/*.{js,jsx}"]
  ```

  Configure `vite.config.js` to proxy `/api` → `http://localhost:8000`:
  ```js
  server: { proxy: { '/api': 'http://localhost:8000' } }
  ```

  Add Tailwind directives to `frontend/src/index.css`.

  Files: `frontend/vite.config.js`, `frontend/tailwind.config.js`,
  `frontend/postcss.config.js`, `frontend/src/index.css`

  Verify: `npm run build` inside `frontend/` — exits 0, `dist/` created.

- [ ] 20. Write `frontend/src/api.js` — all backend calls in one module.

  Functions (all using `fetch`, relative URLs so the Vite proxy forwards them):
  - `getTasks(filters)` — GET /api/tasks
  - `createTask(data)` — POST /api/tasks
  - `updateTask(id, data)` — PATCH /api/tasks/:id
  - `deleteTask(id)` — DELETE /api/tasks/:id
  - `getEvents(params)` — GET /api/events
  - `createEvent(data)` — POST /api/events
  - `updateEvent(id, data)` — PATCH /api/events/:id
  - `deleteEvent(id)` — DELETE /api/events/:id
  - `getUpcomingReminders()` — GET /api/reminders/upcoming
  - `createReminder(data)` — POST /api/reminders
  - `streamChat(sessionId, message, onEvent)` — POST /api/chat, reads SSE stream, calls `onEvent(parsedEvent)` for each data line
  - `confirmAction(sessionId, confirmed)` — POST /api/chat/confirm

  File: `frontend/src/api.js`

---

## Phase 6 — Frontend Components

Order: shared/atomic components first, then page-level, then App.jsx wiring.

- [ ] 21. Write `frontend/src/components/ConfirmDialog.jsx` — accessible modal.

  Props: `open`, `title`, `message`, `onConfirm`, `onCancel`.
  Uses a `<dialog>` element or a fixed overlay div with `role="dialog"` and
  `aria-modal="true"`. Trap focus while open. Tailwind-styled with a white card,
  grey overlay, and two action buttons (Confirm / Cancel).

  File: `frontend/src/components/ConfirmDialog.jsx`

- [ ] 22. Write `frontend/src/components/ToolCallLog.jsx` — tool call event display.

  Props: `events` (array of `{type, name, input, result, status}`).
  Render each tool call as a collapsible card: tool name + status icon (spinner /
  ✓ / ✗), expandable JSON viewer for input/result (`<pre>` with syntax
  highlighting via CSS classes).

  File: `frontend/src/components/ToolCallLog.jsx`

- [ ] 23. Write `frontend/src/components/Sidebar.jsx` — navigation sidebar.

  Props: `currentPage`, `onNavigate`.
  Links: Dashboard, Tasks, Calendar, Chat, Reminders.
  Highlight active link. Show "AI Powered by Claude" badge at the bottom.
  Collapsible on mobile (hamburger button).

  File: `frontend/src/components/Sidebar.jsx`

- [ ] 24. Write `frontend/src/components/TaskList.jsx` — task management page.

  State: task list, filter (all/open/in_progress/completed), modal open/close,
  editing task.

  Features:
  - Filter tabs (All / Open / In Progress / Completed).
  - Table rows with priority badge (colour-coded: red=high, yellow=medium,
    green=low), status badge, due date, action buttons (edit, delete).
  - Inline modal form for create/edit with fields: title, description, due_date,
    priority, status.
  - Delete triggers `ConfirmDialog`.
  - Loads tasks on mount via `getTasks()`.

  File: `frontend/src/components/TaskList.jsx`

- [ ] 25. Write `frontend/src/components/CalendarView.jsx` — FullCalendar wrapper.

  Use `@fullcalendar/react` with `dayGridPlugin`, `timeGridPlugin`,
  `interactionPlugin`.

  Features:
  - Display events from `/api/events` as FullCalendar events.
  - Click a day → open create-event modal (pre-filled date).
  - Click an event → open edit/delete modal.
  - Month/week/day view switcher.

  File: `frontend/src/components/CalendarView.jsx`

- [ ] 26. Write `frontend/src/components/ChatPanel.jsx` — AI chat interface.

  State: messages list, input value, streaming flag, tool events, pending confirmation.

  Features:
  - Message bubbles (user right, assistant left) with timestamps.
  - Inline `ToolCallLog` after each assistant message that triggered tools.
  - Confirmation prompt rendered inline when a `confirmation_required` SSE event
    arrives (Confirm / Cancel buttons; calls `confirmAction`).
  - Textarea input with send button; disabled while streaming.
  - Auto-scroll to bottom on new messages.
  - Loading indicator while streaming.

  File: `frontend/src/components/ChatPanel.jsx`

- [ ] 27. Write `frontend/src/components/RemindersPanel.jsx` — upcoming reminders.

  Loads from `GET /api/reminders/upcoming`. Displays a list with time, message,
  and which task/event it belongs to. Shows empty state when none.

  File: `frontend/src/components/RemindersPanel.jsx`

- [ ] 28. Write `frontend/src/components/Dashboard.jsx` — overview page.

  Sections:
  - Stats cards: open tasks count, today's events count, upcoming reminders count.
  - Quick-action buttons: New Task, New Event, Open Chat.
  - "Today's Schedule" — events for today from `/api/events`.
  - "Recent Tasks" — last 5 tasks from `/api/tasks`.

  File: `frontend/src/components/Dashboard.jsx`

- [ ] 29. Write `frontend/src/App.jsx` — root component with routing + notifications.

  State: `currentPage` (dashboard/tasks/calendar/chat/reminders), notification queue.

  Layout: `<Sidebar>` on left, `<main>` on right (full height).
  Render the page component matching `currentPage`.
  Use `react-hot-toast` for success/error toasts.
  Pass `onNavigate` to Sidebar; pass `showNotification` down to pages that need it.

  File: `frontend/src/App.jsx`

- [ ] 30. Write `frontend/src/main.jsx` and update `frontend/index.html`.

  `main.jsx`: mount `<App />` into `#root` with `ReactDOM.createRoot`.
  `index.html`: set title to "Planner AI", include favicon if desired.

  Files: `frontend/src/main.jsx`, `frontend/index.html`

  Verify: `npm run build` inside `frontend/` — exits 0, no TS/JSX errors.

---

## Phase 7 — Frontend Tests

- [ ] 31. Configure Vitest for the frontend.

  Add to `frontend/package.json` devDependencies:
  ```json
  "vitest": "^1.6.0",
  "@testing-library/react": "^15.0.0",
  "@testing-library/user-event": "^14.5.0",
  "@testing-library/jest-dom": "^6.4.0",
  "jsdom": "^24.0.0"
  ```

  Add to `vite.config.js`:
  ```js
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js']
  }
  ```

  Create `frontend/src/test/setup.js`:
  ```js
  import '@testing-library/jest-dom';
  ```

  Add script: `"test": "vitest run"` to `package.json`.

  Files: `frontend/vite.config.js`, `frontend/package.json`,
  `frontend/src/test/setup.js`

- [ ] 32. Write frontend tests.

  `frontend/src/test/TaskList.test.jsx`:
  - Mock `api.js`; render TaskList; assert tasks render, filter tabs work, modal opens on "New Task".

  `frontend/src/test/ChatPanel.test.jsx`:
  - Mock `streamChat` to call `onEvent` with a `text` event then `done`; assert message appears.
  - Mock `confirmation_required` event; assert confirmation buttons render.

  `frontend/src/test/ToolCallLog.test.jsx`:
  - Render with sample events; assert tool name and JSON appear.

  `frontend/src/test/Dashboard.test.jsx`:
  - Mock API calls; assert stats cards render.

  Files: `frontend/src/test/TaskList.test.jsx`, `frontend/src/test/ChatPanel.test.jsx`,
  `frontend/src/test/ToolCallLog.test.jsx`, `frontend/src/test/Dashboard.test.jsx`

  Verify: `npm test` inside `frontend/` — all tests pass.

---

## Phase 8 — Integration Verification & Debugging

- [ ] 33. End-to-end smoke test (manual, documented steps).

  With both servers running:
  1. Open http://localhost:5173 — dashboard loads, stats cards show zeros (empty DB).
  2. Navigate to Tasks — create a task via the modal form; task appears in list.
  3. Navigate to Calendar — create an event; appears on calendar.
  4. Navigate to Chat — type "List my tasks"; SSE stream returns tool_call for
     `list_tasks`, tool_result with the task, and a final text answer.
  5. In Chat, type "Delete task 1" — `confirmation_required` appears in UI;
     click Confirm — task deleted.
  6. Navigate to Reminders — create a reminder via Chat ("remind me about task X at 3pm"); reminder appears.

  Document any failures and fix before proceeding.

  Verify: all 6 steps succeed without console errors.

- [ ] 34. Fix any cross-cutting issues found in step 33.

  Common expected issues to pre-empt:
  - CORS: verify `settings.cors_origins` list parsing handles both `"http://localhost:5173"` and `"http://localhost:5173,"`.
  - Date serialisation: FastAPI returns datetimes as strings; frontend `new Date(str)` must parse them correctly.
  - SSE keep-alive: if Vite proxy closes idle SSE connections, add `proxy: { '/api': { target: '...', changeOrigin: true } }` with no timeout.
  - FullCalendar event shape: `{ id, title, start, end }` — map from API `start_time`/`end_time` fields.

  Files: whichever files contain the bugs discovered.

  Verify: repeat smoke test from step 33 — all 6 steps pass.

---

## Phase 9 — Documentation & Run Instructions

- [ ] 35. Write `README.md` at the workspace root with complete setup and run instructions.

  Sections:
  1. **Project Overview** — what it does, tech stack.
  2. **Prerequisites** — Python 3.11+, Node 18+, npm.
  3. **Backend Setup** (PowerShell):
     ```powershell
     python -m venv backend\.venv
     backend\.venv\Scripts\Activate.ps1
     pip install -r backend\requirements.txt
     copy backend\.env.example backend\.env
     # Edit backend\.env and set ANTHROPIC_API_KEY
     cd backend
     uvicorn app.main:app --reload --port 8000
     ```
  4. **Frontend Setup** (PowerShell):
     ```powershell
     cd frontend
     npm install
     npm run dev
     ```
  5. **Running Tests**:
     ```powershell
     # Backend (from d:\Ai agent\)
     backend\.venv\Scripts\Activate.ps1
     cd backend
     pytest tests/ -v

     # Frontend (from d:\Ai agent\frontend\)
     npm test
     ```
  6. **Environment Variables** — table of all vars with descriptions.
  7. **API Reference** — summary of endpoints.
  8. **AI Tools Reference** — table of all 9 tools.
  9. **Architecture** — brief diagram (ASCII) of request flow.

  File: `README.md`

  Verify: `README.md` exists and is readable; no placeholder text remains.

---

## Ordering Constraints Summary

```
1-3  (scaffold+deps)
  └─► 4-7  (config+db+models+schemas)
        └─► 8-11  (REST routes+main)
              ├─► 12  (route tests — can run now)
              └─► 13-17  (agent loop+chat route)
                    └─► 18  (agent tests)
19-20  (frontend scaffold+api.js — parallel to backend after step 3)
  └─► 21-30  (components, sequential within phase 6)
        └─► 31-32  (frontend tests)
33-34  (integration — needs both servers running)
35   (docs — last)
```

Steps 19-20 can begin as soon as Node is confirmed available (after step 3 for the venv;
they share no Python dependency). All backend steps must be complete before step 33.

---

## Key Design Decisions

1. **Session history in memory (not DB)**: Simple dict keyed by `session_id`. Acceptable
   for a single-process dev server; a real deployment would use Redis. Documented limitation.

2. **Confirmation flow via pause-and-resume**: When `delete_task` returns
   `requires_confirmation`, the loop stores pending state and yields
   `confirmation_required`. The `/api/chat/confirm` endpoint resumes it.
   This avoids a second full agent call and keeps the conversation coherent.

3. **Conflict detection at the route layer AND the tool layer**: The REST event
   routes return 409 directly. The `schedule_task` / `reschedule_task` tools re-check
   inside the tool function so the AI agent gets a structured error dict rather than
   an HTTP exception.

4. **Pydantic v2 `ConfigDict(from_attributes=True)`**: All ORM response models use
   this instead of the deprecated `orm_mode = True` to stay compatible with Pydantic 2.x.

5. **Python 3.14 compatibility caveat**: Python 3.14 is pre-release. If any
   dependency fails to install (C-extension wheel not yet built), downgrade only
   that package to its latest release that publishes a wheel, or use `--no-binary`
   to build from source. Document the workaround inline in `requirements.txt`.

6. **No real email/push for reminders**: The `Reminder` model records intent.
   The frontend displays upcoming reminders. No delivery integration is configured
   or claimed; a comment in `models.py` notes this.

7. **FullCalendar via npm, not CDN**: Installed as a proper npm dependency so
   Vite tree-shakes unused plugins and the build is reproducible offline.

8. **`find_free_slots` window**: 9 AM – 6 PM local time on the requested date,
   sliced into `duration_minutes`-wide slots, filtered against all events that day.
   Returns up to `count` (default 3) non-overlapping slots.
