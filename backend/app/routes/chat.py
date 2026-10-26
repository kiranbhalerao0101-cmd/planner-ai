import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ChatRequest, ConfirmRequest
from ..agent.loop import run_agent_loop, resume_after_confirmation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


async def _sse_generator(gen):
    """Wrap an async generator of dicts into SSE-formatted bytes."""
    async for event in gen:
        try:
            data = json.dumps(event, default=str)
            yield f"data: {data}\n\n"
        except Exception as exc:
            logger.error(f"SSE serialisation error: {exc}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"


@router.post("")
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Stream agent events as Server-Sent Events."""
    gen = run_agent_loop(payload.session_id, payload.message, db)
    return StreamingResponse(
        _sse_generator(gen),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/confirm")
async def confirm(payload: ConfirmRequest, db: Session = Depends(get_db)):
    """
    Resume a paused agent loop after a confirmation_required event.
    If streaming is needed, return SSE; for simplicity return JSON summary.
    """
    gen = resume_after_confirmation(payload.session_id, payload.confirmed, db)
    return StreamingResponse(
        _sse_generator(gen),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
