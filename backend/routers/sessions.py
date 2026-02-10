"""
Sessions Router - HTTP endpoints, dumb on purpose
"""

from fastapi import Depends, APIRouter, Header
from typing import Optional, Dict, Any

from services.lesson_runtime import LessonRuntimeService
from domain.fsm import UserAction
from core.dependencies import get_current_db, verify_authorization

# Explicit import to avoid any circular import issues
from fastapi import Depends as FastAPIDepends


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/")
async def create_session(
    lesson_id: int,
    db=FastAPIDepends(get_current_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """Start a new lesson session"""
    # Auth is handled by dependency
    
    runtime = LessonRuntimeService(db)
    
    session_id = runtime.start_session(lesson_id, user_id)
    
    # Get initial session state
    session_state = runtime.get_session_state(session_id, user_id)
    
    return {
        "session_id": session_id,
        "session_state": session_state
    }


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    db=FastAPIDepends(get_current_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """Resume an existing lesson session"""
    # Auth is handled by dependency
    
    runtime = LessonRuntimeService(db)
    
    session_state = runtime.get_session_state(session_id, user_id)
    
    return {
        "session_id": session_id,
        "session_state": session_state
    }


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: str,
    payload: Dict[str, Any],
    db=FastAPIDepends(get_current_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """Submit an answer to a question"""
    # Auth is handled by dependency
    
    runtime = LessonRuntimeService(db)
    
    action = UserAction(type="answer", payload=payload)
    
    result = runtime.submit_action(session_id, user_id, action)
    
    return {
        "session_id": session_id,
        "result": result
    }


@router.post("/{session_id}/next")
async def next_state(
    session_id: str,
    payload: Dict[str, Any] = None,
    db=FastAPIDepends(get_current_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """Advance to next state from content"""
    # Auth is handled by dependency
    
    runtime = LessonRuntimeService(db)
    
    action = UserAction(
        type="next",
        payload=payload
    )
    
    result = runtime.submit_action(session_id, user_id, action)
    
    return {
        "session_id": session_id,
        "result": result
    }
