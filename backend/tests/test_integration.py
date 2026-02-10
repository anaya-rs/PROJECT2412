"""
Integration Tests - End-to-end workflow testing
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
import time

from main import create_app
from core.db import get_db_session
from models.lesson import LessonDB
from models.session import LessonSessionDB
from models.analytics import AnalyticsEventDB


class TestEndToEndWorkflow:
    """Test complete lesson generation and session workflow"""
    
    def setup_method(self):
        """Setup test client and database"""
        self.app = create_app()
        self.client = TestClient(self.app)
        self.auth_headers = {"Authorization": "Bearer mock-token"}
        
        # Setup test database
        self.db = get_db_session()
    
    def teardown_method(self):
        """Cleanup test database"""
        # Clean up test data
        self.db.query(AnalyticsEventDB).delete()
        self.db.query(LessonSessionDB).delete()
        self.db.query(LessonDB).delete()
        self.db.commit()
        self.db.close()
    
    @patch('services.lesson_generation.requests.post')
    def test_complete_lesson_flow(self, mock_post):
        """Test complete flow: generate lesson -> start session -> complete lesson"""
        # Step 1: Generate lesson
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": """{
                "schema_version": "1.0",
                "title": "Integration Test Lesson",
                "estimated_duration_minutes": 5,
                "states": [
                    {
                        "id": "c1",
                        "type": "content",
                        "text": "Python is a high-level programming language known for its simplicity and readability."
                    },
                    {
                        "id": "q1",
                        "type": "question",
                        "question_format": "mcq",
                        "prompt": "What type of programming language is Python?",
                        "options": ["High-level", "Low-level", "Machine code", "Assembly"],
                        "correct_answer": 0,
                        "explanation": "Python is considered a high-level programming language because it abstracts away complex computer details."
                    },
                    {
                        "id": "c2",
                        "type": "content",
                        "text": "Python was created by Guido van Rossum and first released in 1991."
                    }
                ]
            }"""
        }
        mock_post.return_value = mock_response
        
        # Generate lesson
        gen_response = self.client.post(
            "/api/lessons/generate",
            json={
                "text": "Python is a high-level programming language. It was created by Guido van Rossum and first released in 1991. Python supports multiple programming paradigms and is known for its simple syntax.",
                "title": "Python Basics",
                "duration": 5
            },
            headers=self.auth_headers
        )
        
        assert gen_response.status_code == 200
        lesson_data = gen_response.json()
        lesson_id = lesson_data["lesson_id"]
        assert lesson_id is not None
        
        # Step 2: Get lesson details
        lesson_response = self.client.get(
            f"/api/lessons/{lesson_id}",
            headers=self.auth_headers
        )
        
        assert lesson_response.status_code == 200
        lesson_detail = lesson_response.json()
        assert lesson_detail["title"] == "Integration Test Lesson"
        assert len(lesson_detail["states"]) == 3
        
        # Step 3: Start session
        session_response = self.client.post(
            f"/api/sessions/?lesson_id={lesson_id}",
            headers=self.auth_headers
        )
        
        assert session_response.status_code == 200
        session_data = session_response.json()
        session_id = session_data["session_id"]
        session_state = session_data["session_state"]
        
        assert session_id is not None
        assert session_state["state"]["id"] == "c1"  # First content state
        assert session_state["progress"] == 0.0
        assert session_state["completed"] == False
        
        # Step 4: Advance from first content
        next_response = self.client.post(
            f"/api/sessions/{session_id}/next",
            headers=self.auth_headers
        )
        
        assert next_response.status_code == 200
        next_state = next_response.json()["result"]
        assert next_state["state"]["id"] == "q1"  # Should be at question now
        assert next_state["progress"] == 1/3  # 1 out of 3 states
        
        # Step 5: Submit correct answer
        answer_response = self.client.post(
            f"/api/sessions/{session_id}/answer",
            json={"answer": 0},  # Correct answer
            headers=self.auth_headers
        )
        
        assert answer_response.status_code == 200
        answer_state = answer_response.json()["result"]
        assert answer_state["state"]["id"] == "c2"  # Should advance to final content
        assert answer_state["progress"] == 2/3
        assert answer_state["completed"] == False
        
        # Step 6: Complete lesson
        complete_response = self.client.post(
            f"/api/sessions/{session_id}/next",
            headers=self.auth_headers
        )
        
        assert complete_response.status_code == 200
        final_state = complete_response.json()["result"]
        assert final_state["completed"] == True
        
        # Step 7: Verify analytics
        analytics_response = self.client.get(
            f"/api/analytics/sessions/{session_id}",
            headers=self.auth_headers
        )
        
        assert analytics_response.status_code == 200
        analytics_data = analytics_response.json()
        events = analytics_data["events"]
        
        # Should have events for: enter c1, advance c1->q1, enter q1, answer q1, advance q1->c2, enter c2, advance c2->complete, complete
        assert len(events) >= 8
        
        event_types = [event["event_type"] for event in events]
        assert "enter" in event_types
        assert "answer" in event_types
        assert "advance" in event_types
        assert "complete" in event_types
        
        # Step 8: Verify lesson analytics
        lesson_analytics_response = self.client.get(
            f"/api/analytics/lessons/{lesson_id}",
            headers=self.auth_headers
        )
        
        assert lesson_analytics_response.status_code == 200
        lesson_analytics = lesson_analytics_response.json()
        assert lesson_analytics["lesson_id"] == lesson_id
        assert lesson_analytics["completed_sessions"] == 1
        assert lesson_analytics["completion_rate"] == 100.0
    
    @patch('services.lesson_generation.requests.post')
    def test_lesson_with_wrong_answers(self, mock_post):
        """Test lesson flow with wrong answers and retries"""
        # Mock lesson with question
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": """{
                "schema_version": "1.0",
                "title": "Retry Test Lesson",
                "estimated_duration_minutes": 5,
                "states": [
                    {
                        "id": "c1",
                        "type": "content",
                        "text": "Test content about retries"
                    },
                    {
                        "id": "q1",
                        "type": "question",
                        "question_format": "mcq",
                        "prompt": "What is 2 + 2?",
                        "options": ["3", "4", "5", "6"],
                        "correct_answer": 1,
                        "explanation": "2 + 2 = 4"
                    }
                ]
            }"""
        }
        mock_post.return_value = mock_response
        
        # Generate and start lesson
        gen_response = self.client.post(
            "/api/lessons/generate",
            json={
                "text": "Math test for retry logic. " * 20,
                "title": "Math Test",
                "duration": 5
            },
            headers=self.auth_headers
        )
        
        lesson_id = gen_response.json()["lesson_id"]
        
        session_response = self.client.post(
            f"/api/sessions/?lesson_id={lesson_id}",
            headers=self.auth_headers
        )
        
        session_id = session_response.json()["session_id"]
        
        # Advance to question
        self.client.post(f"/api/sessions/{session_id}/next", headers=self.auth_headers)
        
        # Submit wrong answer (first attempt)
        wrong_response = self.client.post(
            f"/api/sessions/{session_id}/answer",
            json={"answer": 0},  # Wrong answer
            headers=self.auth_headers
        )
        
        wrong_state = wrong_response.json()["result"]
        assert wrong_state["state"]["id"] == "q1"  # Stay on question
        assert wrong_state["attempts_left"] == 1  # One attempt left
        
        # Submit wrong answer again (second attempt - should force advance)
        wrong_response2 = self.client.post(
            f"/api/sessions/{session_id}/answer",
            json={"answer": 2},  # Another wrong answer
            headers=self.auth_headers
        )
        
        wrong_state2 = wrong_response2.json()["result"]
        assert wrong_state2["completed"] == True  # Should be completed after final wrong answer
        
        # Verify retry events in analytics
        analytics_response = self.client.get(
            f"/api/analytics/sessions/{session_id}",
            headers=self.auth_headers
        )
        
        events = analytics_response.json()["events"]
        retry_events = [e for e in events if e["event_type"] == "retry"]
        assert len(retry_events) == 1  # Should have one retry event


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        """Setup test client"""
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to all endpoints"""
        endpoints = [
            ("/api/lessons/", "GET"),
            ("/api/lessons/1", "GET"),
            ("/api/lessons/generate", "POST"),
            ("/api/sessions/?lesson_id=1", "POST"),
            ("/api/sessions/test/answer", "POST"),
            ("/api/analytics/sessions/test", "GET")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = self.client.get(endpoint)
            else:
                response = self.client.post(endpoint, json={})
            
            assert response.status_code == 401
            assert "Access token required" in response.json()["detail"]
    
    def test_invalid_session_actions(self):
        """Test invalid actions on sessions"""
        # Start with a valid session (mocked)
        with patch('routers.sessions.LessonRuntimeService') as mock_runtime:
            mock_runtime_instance = Mock()
            mock_runtime_instance.submit_action.side_effect = ValueError("Session not found")
            mock_runtime.return_value = mock_runtime_instance
            
            response = self.client.post(
                "/api/sessions/invalid-session/answer",
                json={"answer": 0},
                headers={"Authorization": "Bearer mock-token"}
            )
            
            assert response.status_code == 500
            assert "Session not found" in response.json()["detail"]
    
    def test_lesson_generation_failure(self):
        """Test lesson generation failure handling"""
        with patch('services.lesson_generation.requests.post') as mock_post:
            # Mock LLM failure
            mock_post.side_effect = Exception("LLM API error")
            
            response = self.client.post(
                "/api/lessons/generate",
                json={
                    "text": "Test content" * 20,
                    "duration": 30
                },
                headers={"Authorization": "Bearer mock-token"}
            )
            
            assert response.status_code == 500
            assert "Failed after" in response.json()["detail"]


class TestPerformance:
    """Test performance and load handling"""
    
    def setup_method(self):
        """Setup test client"""
        self.app = create_app()
        self.client = TestClient(self.app)
        self.auth_headers = {"Authorization": "Bearer mock-token"}
    
    def test_concurrent_session_creation(self):
        """Test creating multiple sessions concurrently"""
        # This would require async testing framework, but we can simulate
        session_ids = []
        
        for i in range(5):
            with patch('routers.sessions.LessonRuntimeService') as mock_runtime:
                mock_runtime_instance = Mock()
                mock_runtime_instance.start_session.return_value = f"session-{i}"
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
                session_ids.append(response.json()["session_id"])
        
        # Verify all sessions are unique
        assert len(set(session_ids)) == 5
    
    def test_large_lesson_generation(self):
        """Test generating large lesson (60 minutes)"""
        with patch('services.lesson_generation.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            # Generate proper 60-minute lesson structure
            states = []
            for i in range(7):  # 7 content blocks
                states.append({
                    "id": f"c{i+1}",
                    "type": "content",
                    "text": f"Content block {i+1} for large lesson"
                })
                if i < 6:  # 6 questions
                    states.append({
                        "id": f"q{i+1}",
                        "type": "question",
                        "question_format": "mcq",
                        "prompt": f"Question {i+1} that meets minimum length requirement?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 0,
                        "explanation": f"Explanation for question {i+1}"
                    })
            
            mock_response.json.return_value = {
                "response": json.dumps({
                    "schema_version": "1.0",
                    "title": "Large Test Lesson",
                    "estimated_duration_minutes": 60,
                    "states": states
                })
            }
            mock_post.return_value = mock_response
            
            start_time = time.time()
            response = self.client.post(
                "/api/lessons/generate",
                json={
                    "text": "Large content for testing performance. " * 50,
                    "duration": 60
                },
                headers=self.auth_headers
            )
            end_time = time.time()
            
            assert response.status_code == 200
            # Should complete within reasonable time (adjust threshold as needed)
            assert (end_time - start_time) < 30  # 30 seconds max


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
