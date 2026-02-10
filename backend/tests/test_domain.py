"""
Domain Layer Tests - Pure business logic
"""

import pytest
from datetime import datetime
from uuid import uuid4

from domain.lesson import Lesson
from domain.state import ContentState, QuestionState, DomainEvent
from domain.fsm import UserAction, step, LessonSession
from domain.validation import validate_duration_constraints, validate_lesson_structure


class TestLessonModel:
    """Test domain Lesson model"""
    
    def test_valid_lesson_creation(self):
        """Test creating a valid lesson"""
        states = [
            ContentState(id="c1", type="content", text="Introduction to Python"),
            QuestionState(
                id="q1", 
                type="question",
                question_format="mcq",
                prompt="What is Python programming language?",
                options=["A language", "A framework", "A database"],
                correct_answer=0,
                explanation="Python is a programming language"
            ),
            ContentState(id="c2", type="content", text="Python Features"),
            QuestionState(
                id="q2",
                type="question", 
                question_format="short_answer",
                prompt="Name one Python feature",
                correct_answer="dynamic typing",
                explanation="Python has dynamic typing"
            ),
            ContentState(id="c3", type="content", text="Advanced Python"),
            QuestionState(
                id="q3",
                type="question",
                question_format="mcq",
                prompt="What is Python used for commonly?",
                options=["Web development", "Only gaming", "Only cooking"],
                correct_answer=0,
                explanation="Python is commonly used for web development"
            )
        ]
        
        lesson = Lesson(
            schema_version="1.0",
            title="Python Basics",
            estimated_duration_minutes=30,
            states=states
        )
        
        assert lesson.title == "Python Basics"
        assert len(lesson.states) == 6
        assert lesson.estimated_duration_minutes == 30
    
    def test_invalid_consecutive_questions(self):
        """Test validation rejects consecutive questions"""
        states = [
            ContentState(id="c1", type="content", text="Intro"),
            QuestionState(id="q1", type="question", question_format="mcq", 
                       prompt="What is test question?", options=["A", "B"], correct_answer=0, explanation="Test"),
            QuestionState(id="q2", type="question", question_format="mcq",
                       prompt="What is second test question?", options=["C", "D"], correct_answer=0, explanation="Test2")
        ]
        
        with pytest.raises(ValueError, match="Two questions cannot appear consecutively"):
            Lesson(
                schema_version="1.0",
                title="Invalid Lesson",
                estimated_duration_minutes=30,
                states=states
            )


class TestFSM:
    """Test deterministic FSM logic"""
    
    def setup_method(self):
        """Setup test data"""
        self.lesson = Lesson(
            schema_version="1.0",
            title="Test Lesson",
            estimated_duration_minutes=30,
            states=[
                ContentState(id="c1", type="content", text="First content"),
                QuestionState(
                    id="q1",
                    type="question",
                    question_format="mcq",
                    prompt="Test question 1",
                    options=["A", "B"],
                    correct_answer=0,
                    explanation="Test explanation 1"
                ),
                ContentState(id="c2", type="content", text="Second content"),
                QuestionState(
                    id="q2",
                    type="question",
                    question_format="mcq",
                    prompt="Test question 2",
                    options=["C", "D"],
                    correct_answer=0,
                    explanation="Test explanation 2"
                ),
                ContentState(id="c3", type="content", text="Third content"),
                QuestionState(
                    id="q3",
                    type="question",
                    question_format="mcq",
                    prompt="Test question 3",
                    options=["E", "F"],
                    correct_answer=0,
                    explanation="Test explanation 3"
                ),
                ContentState(id="c4", type="content", text="Fourth content")
            ]
        )
        
        self.session = LessonSession(
            id=str(uuid4()),
            lesson_id=1,
            user_id=1,
            current_index=0,
            attempts=0,
            started_at=datetime.utcnow(),
            last_active_at=datetime.utcnow()
        )
    
    def test_content_next_action(self):
        """Test next action from content state"""
        action = UserAction(type="next")
        
        result = step(self.lesson, self.session, action)
        
        assert result.next_index == 1
        assert result.next_attempts == 0
        assert result.completed == False
        assert len(result.events) == 2  # advance + enter
        assert result.events[0].event_type == "advance"
        assert result.events[1].event_type == "enter"
    
    def test_question_correct_answer(self):
        """Test correct answer advances immediately"""
        self.session.current_index = 1  # Move to question
        action = UserAction(type="answer", payload={"answer": 0})
        
        result = step(self.lesson, self.session, action)
        
        assert result.next_index == 2
        assert result.next_attempts == 0
        assert result.completed == False
        assert len(result.events) == 3  # answer + advance + enter
        assert result.events[0].event_type == "answer"
        assert result.events[0].payload["correct"] == True
    
    def test_question_wrong_answer_retry(self):
        """Test wrong answer allows retry"""
        self.session.current_index = 1  # Move to question
        action = UserAction(type="answer", payload={"answer": 1})
        
        result = step(self.lesson, self.session, action)
        
        assert result.next_index == 1  # Stay on same question
        assert result.next_attempts == 1  # Increment attempts
        assert result.completed == False
        assert len(result.events) == 2  # answer + retry
        assert result.events[0].event_type == "answer"
        assert result.events[0].payload["correct"] == False
        assert result.events[1].event_type == "retry"
    
    def test_question_wrong_answer_final(self):
        """Test second wrong answer forces advance"""
        self.session.current_index = 1  # Move to question
        self.session.attempts = 1  # Already attempted once
        
        action = UserAction(type="answer", payload={"answer": 1})
        
        result = step(self.lesson, self.session, action)
        
        assert result.next_index == 2  # Force advance
        assert result.next_attempts == 0  # Reset attempts
        assert result.completed == False
        assert len(result.events) == 3  # answer + advance + enter
        assert result.events[0].event_type == "answer"
        assert result.events[0].payload["correct"] == False
        assert result.events[1].event_type == "advance"
        assert result.events[1].payload["reason"] == "wrong_final"
    
    def test_lesson_completion(self):
        """Test lesson completion"""
        self.session.current_index = 6  # Move to last content (index 6)
        action = UserAction(type="next")
        
        result = step(self.lesson, self.session, action)
        
        assert result.next_index == 7  # Beyond last state
        assert result.next_attempts == 0
        assert result.completed == True
        assert len(result.events) == 2  # advance + complete
        assert result.events[0].event_type == "advance"
        assert result.events[1].event_type == "complete"


class TestValidation:
    """Test domain validation rules"""
    
    def test_duration_constraints_valid(self):
        """Test valid duration constraints"""
        states = [
            ContentState(id="c1", type="content", text="Content 1"),
            QuestionState(id="q1", type="question", question_format="mcq",
                       prompt="Test question 1", options=["A", "B"], correct_answer=0, explanation="E1"),
            ContentState(id="c2", type="content", text="Content 2"),
            QuestionState(id="q2", type="question", question_format="mcq",
                       prompt="Test question 2", options=["C", "D"], correct_answer=0, explanation="E2"),
            ContentState(id="c3", type="content", text="Content 3"),
            QuestionState(id="q3", type="question", question_format="mcq",
                       prompt="Test question 3", options=["E", "F"], correct_answer=0, explanation="E3")
        ]
        
        # Should pass for 30-minute lesson
        assert validate_duration_constraints(states, 30) == True
    
    def test_duration_constraints_too_few_questions(self):
        """Test too few questions for duration"""
        states = [
            ContentState(id="c1", type="content", text="Content 1"),
            QuestionState(id="q1", type="question", question_format="mcq",
                       prompt="Test question 1", options=["A", "B"], correct_answer=0, explanation="E1")
        ]
        
        # Should fail for 30-minute lesson (only 1 question)
        with pytest.raises(ValueError, match="Duration 30min requires at least 3 questions"):
            validate_duration_constraints(states, 30)
    
    def test_duration_constraints_5_minute_lesson(self):
        """Test 5-minute lesson constraints"""
        states = [
            ContentState(id="c1", type="content", text="Content 1"),
            QuestionState(id="q1", type="question", question_format="mcq",
                       prompt="Test question 1", options=["A", "B"], correct_answer=0, explanation="E1"),
            ContentState(id="c2", type="content", text="Content 2"),
            QuestionState(id="q2", type="question", question_format="mcq",
                       prompt="Test question 2", options=["C", "D"], correct_answer=0, explanation="E2")
        ]
        
        # Should pass for 5-minute lesson
        assert validate_duration_constraints(states, 5) == True
    
    def test_lesson_structure_validation(self):
        """Test lesson structure validation"""
        states = [
            ContentState(id="c1", type="content", text="Content"),
            QuestionState(id="q1", type="question", question_format="mcq",
                       prompt="What is the test question?", options=["A", "B"], correct_answer=0, explanation="Explanation")
        ]
        
        lesson = Lesson(
            schema_version="1.0",
            title="Valid Lesson",
            estimated_duration_minutes=5,
            states=states
        )
        
        assert validate_lesson_structure(lesson) == True
    
    def test_lesson_structure_first_must_be_content(self):
        """Test first state must be content"""
        states = [
            QuestionState(id="q1", type="question", question_format="mcq",
                       prompt="What is the test question?", options=["A", "B"], correct_answer=0, explanation="Explanation"),
            ContentState(id="c1", type="content", text="Content")
        ]
        
        lesson = Lesson(
            schema_version="1.0",
            title="Invalid Lesson",
            estimated_duration_minutes=5,
            states=states
        )
        
        with pytest.raises(ValueError, match="First state must be content"):
            validate_lesson_structure(lesson)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
