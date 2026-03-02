"""
sessions router with proper error handling
"""

from fastapi import Depends, APIRouter, Header, HTTPException
from typing import Dict, Any
from sqlalchemy.orm import Session

from services.lesson_runtime import LessonRuntimeService
from core.dependencies import get_db, verify_authorization
from schemas.errors import CommonErrors


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/")
async def create_session(
    lesson_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """start a new lesson session with proper error handling"""
    try:
        runtime = LessonRuntimeService(db)
        session_id = runtime.start_session(lesson_id, user_id)
        
        # Get initial session state
        session_state = runtime.get_session_state(session_id, user_id)
        
        return {
            "session_id": session_id,
            "session_state": session_state
        }
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=CommonErrors.not_found("Lesson", str(lesson_id)).model_dump())
        else:
            raise HTTPException(status_code=400, detail=CommonErrors.validation_failed(str(e)).model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=CommonErrors.internal_error(str(e)).model_dump())


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """resume an existing lesson session with proper error handling"""
    try:
        runtime = LessonRuntimeService(db)
        session_state = runtime.get_session_state(session_id, user_id)
        
        return {
            "session_id": session_id,
            "session_state": session_state
        }
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=CommonErrors.session_not_found(session_id).model_dump())
        elif "unauthorized" in str(e).lower():
            raise HTTPException(status_code=403, detail=CommonErrors.forbidden(str(e)).model_dump())
        else:
            raise HTTPException(status_code=400, detail=CommonErrors.validation_failed(str(e)).model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=CommonErrors.internal_error(str(e)).model_dump())


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: str,
    action: Dict[str, Any],
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """submit an answer to a question with proper error handling"""
    try:
        runtime = LessonRuntimeService(db)
        result = runtime.submit_action(session_id, user_id, action)
        return {
            "session_id": session_id,
            "result": result
        }
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=CommonErrors.session_not_found(session_id).model_dump())
        elif "unauthorized" in str(e).lower():
            raise HTTPException(status_code=403, detail=CommonErrors.forbidden(str(e)).model_dump())
        else:
            raise HTTPException(status_code=400, detail=CommonErrors.validation_failed(str(e)).model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=CommonErrors.internal_error(str(e)).model_dump())


@router.post("/{session_id}/next")
async def next_state(
    session_id: str,
    payload: Dict[str, Any] = {},
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """advance to next state from content with proper error handling"""
    try:
        runtime = LessonRuntimeService(db)
        
        # Create action manually to avoid domain model validation
        action = {
            "type": "next",
            "payload": payload
        }
        
        print(f"🔍 [DEBUG] Processing next action for session {session_id}")
        result = runtime.submit_action(session_id, user_id, action)
        print(f"🔍 [DEBUG] Runtime result: {result}")
        
        response = {
            "session_id": session_id,
            "result": result
        }
        print(f"🔍 [DEBUG] Final response: {response}")
        return response
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=CommonErrors.session_not_found(session_id).model_dump())
        elif "unauthorized" in str(e).lower():
            raise HTTPException(status_code=403, detail=CommonErrors.forbidden(str(e)).model_dump())
        else:
            raise HTTPException(status_code=400, detail=CommonErrors.validation_failed(str(e)).model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=CommonErrors.internal_error(str(e)).model_dump())