"""
Analytics Events - State-Level Event Logging
Analytics should observe behavior, not infer it.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlite3 import Connection


class AnalyticsEvent:
    """Represents a single analytics event."""
    
    def __init__(
        self,
        lesson_id: int,
        user_id: int,
        event_type: str,
        state_id: str = None,
        payload: Dict[str, Any] = None
    ):
        self.id = str(uuid.uuid4())
        self.lesson_id = lesson_id
        self.user_id = user_id
        self.event_type = event_type
        self.state_id = state_id
        self.payload = payload or {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage."""
        return {
            "id": self.id,
            "lesson_id": self.lesson_id,
            "user_id": self.user_id,
            "state_id": self.state_id,
            "event_type": self.event_type,
            "payload": json.dumps(self.payload),
            "created_at": self.created_at
        }


class AnalyticsCollector:
    """
    Collects and stores lesson events for analytics.
    
    Event types:
    - enter: User enters a state
    - answer: User answers a question
    - retry: User retries a question
    - advance: User advances to next state
    - complete: User completes lesson
    """
    
    def __init__(self, db_connection: Connection):
        self.db = db_connection
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create analytics tables if they don't exist."""
        cursor = self.db.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_events (
                id TEXT PRIMARY KEY,
                lesson_id INTEGER,
                user_id INTEGER,
                state_id TEXT,
                event_type TEXT,
                payload TEXT,
                created_at TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lesson_events_lesson_id 
            ON lesson_events(lesson_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lesson_events_user_id 
            ON lesson_events(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lesson_events_created_at 
            ON lesson_events(created_at)
        """)
        
        self.db.commit()
    
    def track_event(
        self,
        lesson_id: int,
        user_id: int,
        event_type: str,
        state_id: str = None,
        payload: Dict[str, Any] = None
    ) -> str:
        """
        Track a single analytics event.
        
        Args:
            lesson_id: ID of the lesson
            user_id: ID of the user
            event_type: Type of event
            state_id: ID of the state (if applicable)
            payload: Additional event data
            
        Returns:
            Event ID
        """
        event = AnalyticsEvent(
            lesson_id=lesson_id,
            user_id=user_id,
            event_type=event_type,
            state_id=state_id,
            payload=payload
        )
        
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO lesson_events (
                id, lesson_id, user_id, state_id, event_type, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event.id,
            event.lesson_id,
            event.user_id,
            event.state_id,
            event.event_type,
            json.dumps(event.payload),
            event.created_at
        ))
        
        self.db.commit()
        return event.id
    
    def track_lesson_events(
        self,
        lesson_id: int,
        user_id: int,
        events: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Track multiple events from a lesson session.
        
        Args:
            lesson_id: ID of the lesson
            user_id: ID of the user
            events: List of event dictionaries from FSM
            
        Returns:
            List of event IDs
        """
        event_ids = []
        
        for event_data in events:
            event_id = self.track_event(
                lesson_id=lesson_id,
                user_id=user_id,
                event_type=event_data.get("event_type"),
                state_id=event_data.get("payload", {}).get("state_id"),
                payload=event_data.get("payload", {})
            )
            event_ids.append(event_id)
        
        return event_ids
    
    def get_lesson_events(
        self,
        lesson_id: int,
        user_id: int = None,
        event_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get events for a specific lesson.
        
        Args:
            lesson_id: ID of the lesson
            user_id: Optional user ID filter
            event_types: Optional event type filter
            
        Returns:
            List of event dictionaries
        """
        cursor = self.db.cursor()
        
        query = "SELECT * FROM lesson_events WHERE lesson_id = ?"
        params = [lesson_id]
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if event_types:
            placeholders = ",".join(["?" for _ in event_types])
            query += f" AND event_type IN ({placeholders})"
            params.extend(event_types)
        
        query += " ORDER BY created_at ASC"
        
        cursor.execute(query, params)
        
        events = []
        for row in cursor.fetchall():
            events.append({
                "id": row[0],
                "lesson_id": row[1],
                "user_id": row[2],
                "state_id": row[3],
                "event_type": row[4],
                "payload": json.loads(row[5]) if row[5] else {},
                "created_at": row[6]
            })
        
        return events
    
    def get_user_analytics(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get analytics for a specific user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT * FROM lesson_events 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        
        events = []
        for row in cursor.fetchall():
            events.append({
                "id": row[0],
                "lesson_id": row[1],
                "user_id": row[2],
                "state_id": row[3],
                "event_type": row[4],
                "payload": json.loads(row[5]) if row[5] else {},
                "created_at": row[6]
            })
        
        return events
    
    def get_lesson_statistics(self, lesson_id: int) -> Dict[str, Any]:
        """
        Get aggregated statistics for a lesson.
        
        Args:
            lesson_id: ID of the lesson
            
        Returns:
            Dictionary with lesson statistics
        """
        cursor = self.db.cursor()
        
        # Basic counts
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_events,
                COUNT(DISTINCT event_type) as unique_event_types
            FROM lesson_events 
            WHERE lesson_id = ?
        """, (lesson_id,))
        
        basic_stats = cursor.fetchone()
        
        # Completion rate
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as completed_users
            FROM lesson_events 
            WHERE lesson_id = ? AND event_type = 'complete'
        """, (lesson_id,))
        
        completion_stats = cursor.fetchone()
        
        # Question accuracy
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN payload LIKE '%"correct":true%' THEN 1.0 ELSE 0.0 END) as avg_accuracy,
                COUNT(*) as total_answers
            FROM lesson_events 
            WHERE lesson_id = ? AND event_type = 'answer'
        """, (lesson_id,))
        
        accuracy_stats = cursor.fetchone()
        
        return {
            "lesson_id": lesson_id,
            "unique_users": basic_stats[0] or 0,
            "total_events": basic_stats[1] or 0,
            "unique_event_types": basic_stats[2] or 0,
            "completed_users": completion_stats[0] or 0,
            "completion_rate": (
                (completion_stats[0] or 0) / (basic_stats[0] or 1) * 100
            ) if basic_stats[0] else 0,
            "average_accuracy": accuracy_stats[0] or 0,
            "total_answers": accuracy_stats[1] or 0
        }
    
    def get_dropoff_analysis(self, lesson_id: int) -> List[Dict[str, Any]]:
        """
        Analyze where users drop off in a lesson.
        
        Args:
            lesson_id: ID of the lesson
            
        Returns:
            List of drop-off points with user counts
        """
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT 
                state_id,
                COUNT(DISTINCT user_id) as user_count,
                event_type
            FROM lesson_events 
            WHERE lesson_id = ? AND event_type IN ('enter', 'answer', 'advance')
            GROUP BY state_id, event_type
            ORDER BY 
                CASE 
                    WHEN event_type = 'enter' THEN 1
                    WHEN event_type = 'answer' THEN 2
                    WHEN event_type = 'advance' THEN 3
                END,
                state_id
        """, (lesson_id,))
        
        dropoff_data = []
        for row in cursor.fetchall():
            dropoff_data.append({
                "state_id": row[0],
                "user_count": row[1],
                "event_type": row[2]
            })
        
        return dropoff_data


# ---------- Utility Functions ----------

def create_session_analytics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create session-level analytics from FSM events.
    
    Args:
        events: List of FSM events
        
    Returns:
        Session analytics dictionary
    """
    if not events:
        return {}
    
    # Calculate session metrics
    start_time = events[0].get("created_at")
    end_time = events[-1].get("created_at")
    
    answers = [e for e in events if e.get("event_type") == "answer"]
    correct_answers = [
        e for e in answers 
        if e.get("payload", {}).get("correct") is True
    ]
    
    retries = [e for e in events if e.get("event_type") == "retry"]
    
    return {
        "session_start": start_time,
        "session_end": end_time,
        "total_events": len(events),
        "questions_answered": len(answers),
        "correct_answers": len(correct_answers),
        "accuracy": (
            len(correct_answers) / len(answers) * 100
        ) if answers else 0,
        "total_retries": len(retries),
        "completed": any(e.get("event_type") == "complete" for e in events)
    }
