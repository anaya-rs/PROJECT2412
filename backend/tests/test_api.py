"""
API Layer Tests - HTTP endpoints integration
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from main import create_app


class TestLessonsAPI:
    """Test lessons API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.app = create_app()
        self.client = TestClient(self.app)
        self.auth_headers = {"Authorization": "Bearer mock-token"}
    
    @patch('core.dependencies.get_db_session')
    def test_get_lessons_empty(self, mock_get_db):
        """Test getting lessons when none exist"""
        # Mock empty database response
        mock_db = Mock()
        mock_db.query.return_value.order_by.return_value.all.return_value = []
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/api/lessons/", headers=self.auth_headers)
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_lessons_unauthorized(self):
        """Test getting lessons without auth"""
        response = self.client.get("/api/lessons/")
        
        assert response.status_code == 401
        assert "Access token required" in response.json()["detail"]
    
    @patch('core.dependencies.get_db_session')
    def test_get_lesson_by_id(self, mock_get_db):
        """Test getting specific lesson"""
        # Mock database response
        mock_db = Mock()
        mock_lesson = Mock()
        mock_lesson.id = 1
        mock_lesson.title = "Test Lesson"
        mock_lesson.schema_version = "1.0"
        mock_lesson.estimated_duration_minutes = 30
        mock_lesson.states = '[{"id": "c1", "type": "content", "text": "Test"}]'
        mock_lesson.created_at = "2024-01-01T00:00:00"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_lesson
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/api/lessons/1", headers=self.auth_headers)
        
        assert response.status_code == 200
        lesson_data = response.json()
        assert lesson_data["id"] == 1
        assert lesson_data["title"] == "Test Lesson"
    
    def test_get_lesson_not_found(self):
        """Test getting non-existent lesson"""
        with patch('core.dependencies.get_db_session') as mock_get_db:
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_get_db.return_value = mock_db
            
            response = self.client.get("/api/lessons/999", headers=self.auth_headers)
            
            assert response.status_code == 404
            assert "Lesson not found" in response.json()["detail"]
    
    @patch('routers.lessons.LessonGenerator')
    @patch('core.dependencies.get_db_session')
    @patch('routers.lessons.get_settings')
    def test_generate_lesson_success(self, mock_settings, mock_get_db, mock_generator):
        """Test successful lesson generation"""
        # Mock settings
        mock_settings.return_value = Mock(
            OLLAMA_URL="http://test-ollama:11434",
            OLLAMA_MODEL="test-model"
        )
        
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock generator
        mock_gen_instance = Mock()
        mock_gen_instance.generate_lesson.return_value = 1
        mock_generator.return_value = mock_gen_instance
        
        # Test request
        request_data = {
            "text": "Python is a high-level programming language. " * 10,  # Make it long enough
            "title": "Python Basics",
            "duration": 30
        }
        
        response = self.client.post(
            "/api/lessons/generate",
            json=request_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["lesson_id"] == 1
        assert "Lesson generated successfully" in result["message"]
        
        # Verify generator was called correctly
        mock_gen_instance.generate_lesson.assert_called_once_with(
            content=request_data["text"],
            title=request_data["title"],
            description="",
            duration_minutes=30,
            difficulty="beginner"
        )
    
    def test_generate_lesson_short_content(self):
        """Test generation with short content"""
        request_data = {
            "text": "Short",  # Too short
            "duration": 30
        }
        
        response = self.client.post(
            "/api/lessons/generate",
            json=request_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 400
        assert "Text content is too short" in response.json()["detail"]
    
    def test_generate_lesson_invalid_duration(self):
        """Test generation with invalid duration"""
        request_data = {
            "text": "Valid content that is long enough for testing purposes. " * 5,
            "duration": 15  # Invalid duration
        }
        
        response = self.client.post(
            "/api/lessons/generate",
            json=request_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 400
        assert "Duration must be 5, 30, or 60" in response.json()["detail"]


class TestSessionsAPI:
    """Test sessions API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.app = create_app()
        self.client = TestClient(self.app)
        self.auth_headers = {"Authorization": "Bearer mock-token"}
    
    @patch('routers.sessions.LessonRuntimeService')
    def test_create_session(self, mock_runtime):
        """Test creating a new session"""
        # Mock runtime service
        mock_runtime_instance = Mock()
        mock_runtime_instance.start_session.return_value = "test-session-id"
        mock_runtime_instance.get_session_state.return_value = {
            "state": {"id": "c1", "type": "content", "text": "Test content"},
            "progress": 0.0,
            "attempts_left": 2,
            "completed": False
        }
        mock_runtime.return_value = mock_runtime_instance
        
        response = self.client.post(
            "/api/sessions/?lesson_id=1",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["session_id"] == "test-session-id"
        assert "session_state" in result
        
        # Verify service was called
        mock_runtime_instance.start_session.assert_called_once_with(1, 1)
    
    @patch('routers.sessions.LessonRuntimeService')
    def test_get_session(self, mock_runtime):
        """Test getting session state"""
        # Mock runtime service
        mock_runtime_instance = Mock()
        mock_runtime_instance.get_session_state.return_value = {
            "state": {"id": "c1", "type": "content", "text": "Test content"},
            "progress": 0.5,
            "attempts_left": 2,
            "completed": False
        }
        mock_runtime.return_value = mock_runtime_instance
        
        response = self.client.get(
            "/api/sessions/test-session-id",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["session_id"] == "test-session-id"
        assert result["session_state"]["progress"] == 0.5
    
    @patch('routers.sessions.LessonRuntimeService')
    def test_submit_answer(self, mock_runtime):
        """Test submitting answer"""
        # Mock runtime service
        mock_runtime_instance = Mock()
        mock_runtime_instance.submit_action.return_value = {
            "next_index": 2,
            "completed": False,
            "events": []
        }
        mock_runtime.return_value = mock_runtime_instance
        
        payload = {"answer": 0}
        response = self.client.post(
            "/api/sessions/test-session-id/answer",
            json=payload,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["session_id"] == "test-session-id"
        assert result["result"]["next_index"] == 2
        
        # Verify service was called with correct action
        call_args = mock_runtime_instance.submit_action.call_args
        assert call_args[0][1] == 1  # user_id
        assert call_args[0][2].type == "answer"  # action
        assert call_args[0][2].payload["answer"] == 0
    
    @patch('routers.sessions.LessonRuntimeService')
    def test_advance_content(self, mock_runtime):
        """Test advancing from content"""
        # Mock runtime service
        mock_runtime_instance = Mock()
        mock_runtime_instance.submit_action.return_value = {
            "next_index": 1,
            "completed": False,
            "events": []
        }
        mock_runtime.return_value = mock_runtime_instance
        
        response = self.client.post(
            "/api/sessions/test-session-id/next",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["result"]["next_index"] == 1
        
        # Verify service was called with correct action
        call_args = mock_runtime_instance.submit_action.call_args
        assert call_args[0][1] == 1  # user_id
        assert call_args[0][2].type == "next"  # action


class TestAnalyticsAPI:
    """Test analytics API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.app = create_app()
        self.client = TestClient(self.app)
        self.auth_headers = {"Authorization": "Bearer mock-token"}
    
    @patch('routers.analytics.AnalyticsService')
    def test_get_session_analytics(self, mock_analytics):
        """Test getting session analytics"""
        # Mock analytics service
        mock_analytics_instance = Mock()
        mock_analytics_instance.get_session_events.return_value = [
            {
                "id": "event-1",
                "event_type": "answer",
                "payload": {"correct": True}
            }
        ]
        mock_analytics.return_value = mock_analytics_instance
        
        response = self.client.get(
            "/api/analytics/sessions/test-session",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["session_id"] == "test-session"
        assert len(result["events"]) == 1
        assert result["events"][0]["event_type"] == "answer"
    
    @patch('routers.analytics.AnalyticsService')
    def test_get_lesson_analytics(self, mock_analytics):
        """Test getting lesson analytics"""
        # Mock analytics service
        mock_analytics_instance = Mock()
        mock_analytics_instance.get_lesson_analytics.return_value = {
            "lesson_id": 1,
            "total_events": 10,
            "completion_rate": 80.0,
            "average_accuracy": 75.0
        }
        mock_analytics.return_value = mock_analytics_instance
        
        response = self.client.get(
            "/api/analytics/lessons/1",
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["lesson_id"] == 1
        assert result["completion_rate"] == 80.0
        assert result["average_accuracy"] == 75.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
