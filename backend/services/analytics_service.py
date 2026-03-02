"""
v 1.2 analytics service - event persistence and aggregation
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from models.analytics import AnalyticsEventDB
from models.session import LessonSessionDB
from models.lesson import LessonDB


class AnalyticsService:
    """
    analytics service - passive event logging and aggregation.
    
    analytics never drive behavior, they only observe.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """
        get all events for a session.
        
        args:
            session_id: session id
            
        returns:
            List of event dictionaries
        """
        events = self.db.query(AnalyticsEventDB).filter(
            AnalyticsEventDB.session_id == session_id
        ).order_by(AnalyticsEventDB.created_at.asc()).all()
        
        return [self._event_to_dict(event) for event in events]
    
    def get_lesson_analytics(self, lesson_id: int) -> Dict[str, Any]:
        """
        get comprehensive analytics for a lesson.
        
        args:
            lesson_id: lesson id
            
        returns:
            Analytics summary dictionary
        """
        events = self.db.query(AnalyticsEventDB).filter(
            AnalyticsEventDB.lesson_id == lesson_id
        ).order_by(AnalyticsEventDB.created_at.desc()).all()
        
        return self._analyze_lesson_events(events)
    
    def get_user_analytics(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        get analytics for a user.
        
        args:
            user_id: user id
            limit: maximum number of events
            
        returns:
            list of event dictionaries
        """
        events = self.db.query(AnalyticsEventDB).filter(
            AnalyticsEventDB.user_id == user_id
        ).order_by(AnalyticsEventDB.created_at.desc()).limit(limit).all()
        
        return [self._event_to_dict(event) for event in events]
    
    def _event_to_dict(self, event: AnalyticsEventDB) -> Dict[str, Any]:
        """convert event to dictionary"""
        import json
        
        return {
            "id": event.id,
            "session_id": event.session_id,
            "lesson_id": event.lesson_id,
            "user_id": event.user_id,
            "state_index": event.state_index,
            "event_type": event.event_type,
            "payload": json.loads(event.payload) if event.payload else {},
            "created_at": event.created_at.isoformat() if event.created_at else None
        }
    
    def _analyze_lesson_events(self, events: List[AnalyticsEventDB]) -> Dict[str, Any]:
        """analyze events for lesson-level insights"""
        if not events:
            return {}
        
        # basic stats
        unique_users = len(set(e.user_id for e in events))
        unique_sessions = len(set(e.session_id for e in events))
        
        # event type counts
        event_counts = {}
        for event in events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # completion analysis
        completed_sessions = set()
        for event in events:
            if event.event_type == "complete":
                completed_sessions.add(event.session_id)
        
        completion_rate = (len(completed_sessions) / unique_sessions * 100) if unique_sessions > 0 else 0
        
        # answer analysis across all sessions
        answer_events = [e for e in events if e.event_type == "answer"]
        correct_answers = 0
        total_answers = len(answer_events)
        
        for event in answer_events:
            import json
            try:
                payload = json.loads(event.payload) if event.payload else {}
                if payload.get('correct') is True:
                    correct_answers += 1
            except (json.JSONDecodeError, TypeError):
                continue
        
        avg_accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0
        
        # drop-off analysis by state
        state_dropoffs = self._calculate_state_dropoffs(events)
        
        # time analysis
        session_durations = self._calculate_session_durations(events)
        avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
        
        return {
            "lesson_id": events[0].lesson_id if events else None,
            "unique_users": unique_users,
            "unique_sessions": unique_sessions,
            "total_events": len(events),
            "event_counts": event_counts,
            "completed_sessions": len(completed_sessions),
            "completion_rate": completion_rate,
            "total_answers": total_answers,
            "correct_answers": correct_answers,
            "average_accuracy": avg_accuracy,
            "state_dropoffs": state_dropoffs,
            "average_session_duration_seconds": avg_session_duration,
            "session_durations": session_durations
        }
    
    def _calculate_state_dropoffs(self, events: List[AnalyticsEventDB]) -> List[Dict[str, Any]]:
        """calculate drop-off rates by state"""
        # group events by session and state
        session_states = {}
        
        for event in events:
            session_id = event.session_id
            state_index = event.state_index
            
            if session_id not in session_states:
                session_states[session_id] = set()
            session_states[session_id].add(state_index)
        
        # calculate drop-offs
        state_stats = {}
        
        for session_id, states in session_states.items():
            max_state = max(states) if states else 0
            
            for state_idx in range(max_state + 1):
                if state_idx not in state_stats:
                    state_stats[state_idx] = {
                        "state_index": state_idx,
                        "sessions_entered": 0,
                        "sessions_completed": 0,
                        "dropoff_rate": 0.0
                    }
                
                state_stats[state_idx]["sessions_entered"] += 1
                
                if state_idx < max_state:
                    state_stats[state_idx]["sessions_completed"] += 1
        
        # calculate drop-off rates
        dropoffs = []
        for state_idx, stats in state_stats.items():
            entered = stats["sessions_entered"]
            completed = stats["sessions_completed"]
            dropoff_rate = ((entered - completed) / entered * 100) if entered > 0 else 0
            
            dropoffs.append({
                "state_index": state_idx,
                "sessions_entered": entered,
                "sessions_completed": completed,
                "dropoff_rate": dropoff_rate
            })
        
        return sorted(dropoffs, key=lambda x: x["state_index"])
    
    def _calculate_session_durations(self, events: List[AnalyticsEventDB]) -> List[float]:
        """calculate duration for each session"""
        session_events = {}
        
        for event in events:
            session_id = event.session_id
            if session_id not in session_events:
                session_events[session_id] = []
            session_events[session_id].append(event)
        
        durations = []
        
        for session_id, sess_events in session_events.items():
            sess_events.sort(key=lambda x: x.created_at)
            
            if len(sess_events) >= 2:
                start_time = sess_events[0].created_at
                end_time = sess_events[-1].created_at
                
                if start_time and end_time:
                    duration = (end_time - start_time).total_seconds()
                    durations.append(duration)
        
        return durations
