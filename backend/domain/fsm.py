"""
domain fsm - pure deterministic logic, no side effects
"""

# import typing utilities for type hints
from typing import Dict, Any, List, Literal
# import datetime for timestamp handling
from datetime import datetime
# import uuid4 for generating unique session identifiers
from uuid import uuid4
# import base model from pydantic for data validation and serialization
from pydantic import BaseModel

# import domain models from other modules
from .lesson import Lesson
from .state import AuthoredState, ContentState, QuestionState, DomainEvent


class FSMResult(BaseModel):
    """result of fsm step - pure data, no persistence"""
    # index of the next state to transition to
    next_index: int
    # number of attempts remaining or reset
    next_attempts: int
    # flag indicating if lesson is completed
    completed: bool
    # list of domain events generated during this step
    events: List[DomainEvent]


class UserAction(BaseModel):
    """user action input"""
    # type of action: either "next" for content or "answer" for questions
    type: Literal["next", "answer"]
    # optional payload containing action-specific data (e.g., answer choice)
    payload: dict | None = None


class LessonSession(BaseModel):
    """runtime session state - pure domain model"""
    # unique identifier for this session instance
    id: str  # uuid
    # foreign key reference to the lesson being taken
    lesson_id: int
    # foreign key reference to the user taking the lesson
    user_id: int
    # current position in the lesson state sequence
    current_index: int = 0
    # number of attempts made on current question
    attempts: int = 0
    # timestamp when session was created
    started_at: datetime
    # timestamp of last user activity
    last_active_at: datetime
    # timestamp when lesson was completed (null if ongoing)
    completed_at: datetime | None = None


def _create_advance_events(events: List[DomainEvent], reason: str, state_id: str = None) -> None:
    """create common advancement events"""
    events.append(DomainEvent(
        event_type="advance",
        payload={"reason": reason}
    ))
    if state_id:
        events.append(DomainEvent(
            event_type="enter",
            payload={"state_id": state_id}
        ))


def _handle_completion(next_index: int, lesson_length: int, next_attempts: int, events: List[DomainEvent]) -> FSMResult | None:
    """handle lesson completion logic"""
    if next_index >= lesson_length:
        events.append(DomainEvent(
            event_type="complete",
            payload={"total_states": lesson_length}
        ))
        return FSMResult(
            next_index=next_index,
            next_attempts=next_attempts,
            completed=True,
            events=events
        )
    return None


def step(
    lesson: Lesson,  # immutable lesson artifact containing states and structure
    session: LessonSession,  # current runtime session state
    action: UserAction  # user action to process
) -> FSMResult:
    """
    deterministic fsm step function.
    
    args:
        lesson: immutable lesson artifact
        session: current runtime state
        action: user action to process
        
    returns:
        fsmresult with next state and events
    """
    # validate inputs
    if not lesson.states:
        raise ValueError("lesson has no states")
    if session.current_index < 0 or session.current_index >= len(lesson.states):
        raise ValueError(f"invalid session index: {session.current_index}")
    
    # initialize empty list to collect domain events during this step
    events: List[DomainEvent] = []
    # get the current state object from the lesson based on session index
    current_state = lesson.states[session.current_index]
    # cache lesson length for performance
    lesson_length = len(lesson.states)
    
    # handle different action types with conditional logic
    if action.type == "next":
        # validate that we can only advance from content states
        if not isinstance(current_state, ContentState):
            raise ValueError("cannot 'next' from question state")
        
        # content always advances - create advance event
        _create_advance_events(events, "content_complete")
        
        # calculate next state index by incrementing current
        next_index = session.current_index + 1
        # reset attempts counter for new state
        next_attempts = 0
        
        # check if we've reached the end of the lesson
        completion_result = _handle_completion(next_index, lesson_length, next_attempts, events)
        if completion_result:
            return completion_result
        
        # create event for entering the next state
        events.append(DomainEvent(
            event_type="enter",
            payload={"state_id": lesson.states[next_index].id}
        ))
        
        # return result for normal advancement
        return FSMResult(
            next_index=next_index,
            next_attempts=next_attempts,
            completed=False,
            events=events
        )
    
    # handle answer actions for question states
    elif action.type == "answer":
        # validate that we can only answer question states
        if not isinstance(current_state, QuestionState):
            raise ValueError("cannot 'answer' content state")
        
        # extract user's answer from action payload with validation
        if not action.payload:
            raise ValueError("answer action requires payload")
        user_answer = action.payload.get("answer")
        if user_answer is None:
            raise ValueError("answer payload missing 'answer' field")
        # check if the answer is correct using helper function
        is_correct = _check_answer(current_state, user_answer)
        
        # log the answer attempt with details
        events.append(DomainEvent(
            event_type="answer",
            payload={
                "state_id": current_state.id,  # which question was answered
                "correct": is_correct,  # whether answer was correct
                "attempt": session.attempts + 1,  # attempt number
                "user_answer": user_answer  # what user actually answered
            }
        ))
        
        # handle correct answer case
        if is_correct:
            # create advance event for correct answer
            _create_advance_events(events, "correct")
            
            # move to next state
            next_index = session.current_index + 1
            # reset attempts for new state
            next_attempts = 0
            
            # check if lesson is completed after this advancement
            completion_result = _handle_completion(next_index, lesson_length, next_attempts, events)
            if completion_result:
                return completion_result
            
            # create event for entering next state
            events.append(DomainEvent(
                event_type="enter",
                payload={"state_id": lesson.states[next_index].id}
            ))
            
            # return result for correct answer advancement
            return FSMResult(
                next_index=next_index,
                next_attempts=next_attempts,
                completed=False,
                events=events
            )
        
        # handle wrong answer case
        else:
            # check if this is the first wrong attempt
            if session.attempts == 0:
                # create retry event for first wrong attempt
                events.append(DomainEvent(
                    event_type="retry",
                    payload={"attempt": 1}
                ))
                
                # return result keeping user in same state with incremented attempts
                return FSMResult(
                    next_index=session.current_index,  # stay in current state
                    next_attempts=session.attempts + 1,  # increment attempts
                    completed=False,
                    events=events
                )
            
            # handle second wrong attempt - force advancement
            else:
                # create advance event for final wrong attempt
                _create_advance_events(events, "wrong_final")
                
                # move to next state despite wrong answer
                next_index = session.current_index + 1
                # reset attempts for new state
                next_attempts = 0
                
                # check if lesson is completed
                completion_result = _handle_completion(next_index, lesson_length, next_attempts, events)
                if completion_result:
                    return completion_result
                
                # create event for entering next state
                events.append(DomainEvent(
                    event_type="enter",
                    payload={"state_id": lesson.states[next_index].id}
                ))
                
                # return result for forced advancement after wrong answer
                return FSMResult(
                    next_index=next_index,
                    next_attempts=next_attempts,
                    completed=False,
                    events=events
                )
    
    # handle invalid action types
    else:
        raise ValueError(f"unknown action type: {action.type}")


def _check_answer(question: QuestionState, user_answer: Any) -> bool:
    """check if user answer is correct"""
    # validate question format
    if not hasattr(question, 'question_type') or not hasattr(question, 'correct_answers'):
        raise ValueError("question missing required fields")
    
    # handle single choice question format
    if question.question_type == "single_choice":
        # check if user answer is integer and matches one of the correct answer indices
        if not isinstance(user_answer, int):
            return False
        return user_answer in question.correct_answers
    
    # handle multiple choice question format
    elif question.question_type == "multiple_choice":
        # for multiple choice, user_answer should be a list of indices
        if not isinstance(user_answer, list):
            return False
        # check if all user answers are in the correct answers
        return all(answer in question.correct_answers for answer in user_answer)
    
    # handle unknown question formats
    else:
        # default to false for unsupported formats
        return False
