"""
Services Layer Tests - Orchestration and side effects
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from uuid import uuid4

from services.lesson_generation import LessonGenerator, LessonGenerationError
from services.lesson_runtime import LessonRuntimeService
from services.analytics_service import AnalyticsService
from domain.lesson import Lesson
from domain.state import ContentState, QuestionState
from domain.fsm import UserAction


class TestLessonGeneration:
    """Test lesson generation service"""
    
    def setup_method(self):
        """Setup test data"""
        self.mock_db = Mock()
        self.generator = LessonGenerator(
            ollama_url="http://test-ollama:11434",
            model="test-model",
            db_session=self.mock_db
        )
    
    @patch('services.lesson_generation.requests.post')
    def test_successful_generation(self, mock_post):
        """Test successful lesson generation"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": """{
                "schema_version": "1.0",
                "title": "Test Lesson",
                "estimated_duration_minutes": 30,
                "states": [
                    {
                        "id": "c1",
                        "type": "content",
                        "text": "Test content"
                    },
                    {
                        "id": "q1",
                        "type": "question",
                        "question_format": "mcq",
                        "prompt": "What is the test question that meets minimum length?",
                        "options": ["A", "B"],
                        "correct_answer": 0,
                        "explanation": "Test explanation"
                    },
                    {
                        "id": "c2",
                        "type": "content",
                        "text": "More test content"
                    },
                    {
                        "id": "q2",
                        "type": "question",
                        "question_format": "mcq",
                        "prompt": "What is another test question that meets minimum length?",
                        "options": ["C", "D"],
                        "correct_answer": 0,
                        "explanation": "Another test explanation"
                    },
                    {
                        "id": "c3",
                        "type": "content",
                        "text": "Final test content"
                    },
                    {
                        "id": "q3",
                        "type": "question",
                        "question_format": "mcq",
                        "prompt": "What is the final test question that meets minimum length?",
                        "options": ["E", "F"],
                        "correct_answer": 0,
                        "explanation": "Final test explanation"
                    }
                ]
            }"""
        }
        mock_post.return_value = mock_response
        
        # Mock database save
        mock_lesson_db = Mock()
        mock_lesson_db.id = 1
        self.mock_db.add.return_value = None
        self.mock_db.commit.return_value = None
        
        with patch('services.lesson_generation.LessonDB.from_domain', return_value=mock_lesson_db):
            lesson_id = self.generator.generate_lesson(
                content="Test content for generation that is definitely long enough to meet the minimum requirement of 100 characters for validation purposes",
                title="Test Lesson",
                duration_minutes=30
            )
        
        assert lesson_id == 1
        mock_post.assert_called_once()
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    @patch('services.lesson_generation.requests.post')
    def test_generation_with_invalid_json(self, mock_post):
        """Test generation with invalid JSON response"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": "invalid json content"
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(LessonGenerationError, match="Invalid JSON output"):
            self.generator.generate_lesson(
                content="Test content that is definitely long enough to meet the minimum requirement of 100 characters for validation purposes",
                duration_minutes=30
            )
    
    def test_generation_with_short_content(self):
        """Test generation fails with short content"""
        with pytest.raises(ValueError, match="Text content is too short"):
            self.generator.generate_lesson(
                content="Short",  # Less than 100 characters
                duration_minutes=30
            )
    
    def test_generation_with_invalid_duration(self):
        """Test generation fails with invalid duration"""
        with pytest.raises(ValueError, match="Duration must be 5, 30, or 60"):
            self.generator.generate_lesson(
                content="A" * 100,  # Valid length
                duration_minutes=15  # Invalid duration
            )


class TestLessonRuntime:
    """Test lesson runtime service"""
    
    def setup_method(self):
        """Setup test data"""
        self.mock_db = Mock()
        self.runtime = LessonRuntimeService(self.mock_db)
        
        # Create test lesson
        self.lesson = Lesson(
            schema_version="1.0",
            title="Test Lesson",
            estimated_duration_minutes=5,  # Changed to 5 minutes to reduce requirements
            states=[
                ContentState(id="c1", type="content", text="First content"),
                QuestionState(
                    id="q1",
                    type="question",
                    question_format="mcq",
                    prompt="What is the test question?",
                    options=["A", "B"],
                    correct_answer=0,
                    explanation="Test explanation"
                )
            ]
        )
        
        # Mock database responses
        self.mock_lesson_db = Mock()
        self.mock_lesson_db.to_domain.return_value = self.lesson
        
        self.mock_session_db = Mock()
        session_domain = Mock(
            id="test-session",
            lesson_id=1,
            user_id=1,
            current_index=0,
            attempts=0,
            started_at=datetime.utcnow(),
            last_active_at=datetime.utcnow()
        )
        # Ensure completed_at is None (not set)
        session_domain.completed_at = None
        self.mock_session_db.to_domain.return_value = session_domain
        # Add user_id property to the mock DB object
        self.mock_session_db.user_id = 1
    
    def test_start_session(self):
        """Test starting a new session"""
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_lesson_db
        self.mock_db.add.return_value = None
        self.mock_db.commit.return_value = None
        
        session_id = self.runtime.start_session(lesson_id=1, user_id=1)
        
        assert session_id is not None
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()
    
    def test_start_nonexistent_lesson(self):
        """Test starting session with non-existent lesson"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Lesson 1 not found"):
            self.runtime.start_session(lesson_id=1, user_id=1)
    
    def test_submit_action_next(self):
        """Test submitting next action"""
        # Setup mocks
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            self.mock_session_db,  # Session query
            self.mock_lesson_db    # Lesson query
        ]
        self.mock_db.commit.return_value = None
        
        action = UserAction(type="next")
        
        result = self.runtime.submit_action(
            session_id="test-session",
            user_id=1,
            action=action
        )
        
        assert result["progress"] == 0.5  # Advanced from 0 to 1 in 2-state lesson
        assert result["completed"] == False
        self.mock_db.commit.assert_called()
    
    def test_submit_action_correct_answer(self):
        """Test submitting correct answer"""
        # Setup session at question
        session_domain = Mock(
            id="test-session",
            lesson_id=1,
            user_id=1,
            current_index=1,  # At question
            attempts=0,
            started_at=datetime.utcnow(),
            last_active_at=datetime.utcnow()
        )
        # Ensure completed_at is None (not set)
        session_domain.completed_at = None
        self.mock_session_db.to_domain.return_value = session_domain
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            self.mock_session_db,  # Session query
            self.mock_lesson_db    # Lesson query
        ]
        self.mock_db.commit.return_value = None
        
        action = UserAction(type="answer", payload={"answer": 0})
        
        result = self.runtime.submit_action(
            session_id="test-session",
            user_id=1,
            action=action
        )
        
        assert result["progress"] > 0  # Advanced
        assert result["completed"] == True  # Lesson completed after correct answer
        self.mock_db.commit.assert_called()
    
    def test_submit_action_wrong_answer(self):
        """Test submitting wrong answer"""
        # Setup session at question
        session_domain = Mock(
            id="test-session",
            lesson_id=1,
            user_id=1,
            current_index=1,  # At question
            attempts=0,
            started_at=datetime.utcnow(),
            last_active_at=datetime.utcnow()
        )
        # Ensure completed_at is None (not set)
        session_domain.completed_at = None
        self.mock_session_db.to_domain.return_value = session_domain
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            self.mock_session_db,  # Session query
            self.mock_lesson_db    # Lesson query
        ]
        self.mock_db.commit.return_value = None
        
        action = UserAction(type="answer", payload={"answer": 1})  # Wrong answer
        
        result = self.runtime.submit_action(
            session_id="test-session",
            user_id=1,
            action=action
        )
        
        assert result["progress"] > 0  # Still on question
        assert result["attempts_left"] == 1  # One attempt used
        assert result["completed"] == False
        self.mock_db.commit.assert_called()


class TestAnalyticsService:
    """Test analytics service"""
    
    def setup_method(self):
        """Setup test data"""
        self.mock_db = Mock()
        self.analytics = AnalyticsService(self.mock_db)
    
    def test_get_session_events(self):
        """Test getting events for a session"""
        # Mock database query
        mock_event = Mock()
        mock_event.id = "event-1"
        mock_event.session_id = "session-1"
        mock_event.event_type = "answer"
        mock_event.payload = '{"correct": true}'
        mock_event.created_at = datetime.utcnow()
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_event]
        
        # Mock _event_to_dict method
        with patch.object(self.analytics, '_event_to_dict', return_value={"id": "event-1"}):
            events = self.analytics.get_session_events("session-1")
        
        assert len(events) == 1
        assert events[0]["id"] == "event-1"
    
    def test_get_lesson_analytics(self):
        """Test getting lesson analytics"""
        # Mock events
        mock_events = [
            Mock(event_type="answer", payload='{"correct": true}'),
            Mock(event_type="complete", payload='{"total_states": 3}'),
            Mock(event_type="advance", payload='{"reason": "correct"}')
        ]
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_events
        
        # Mock analysis method
        with patch.object(self.analytics, '_analyze_lesson_events', return_value={
            "lesson_id": 1,
            "total_events": 3,
            "completion_rate": 100.0
        }):
            analytics = self.analytics.get_lesson_analytics(lesson_id=1)
        
        assert analytics["lesson_id"] == 1
        assert analytics["total_events"] == 3
        assert analytics["completion_rate"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
