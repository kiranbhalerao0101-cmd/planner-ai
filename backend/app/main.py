import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routes import tasks, events, reminders, chat
from .schemas import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Planner AI API",
    description="Personal Task & Calendar AI Agent backend",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(tasks.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.on_event("startup")
def startup():
    init_db()
    if not settings.groq_api_key:
        logger.warning(
            "GROQ_API_KEY is not set. "
            "Task/event/reminder APIs will work, but AI chat will return an error. "
            "Add the key to backend/.env and restart."
        )
    else:
        logger.info(f"AI model: {settings.model} via Groq")


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}
