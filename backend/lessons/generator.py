"""
Lesson Generator - LLM Authoring Only
The LLM is a content author, not a system designer.
"""

import json
import requests
from typing import Dict, Any, Optional
from .models import Lesson, AuthoredState


class LessonGenerationError(Exception):
    """Custom exception for lesson generation failures"""
    pass


class LessonGenerator:
    """
    Handles LLM-based lesson generation with strict validation.
    
    The LLM:
    - generates only authoring states
    - never defines transitions
    - never defines branching
    """
    
    def __init__(self, ollama_url: str, model: str):
        self.ollama_url = ollama_url
        self.model = model
        self.max_retries = 3
    
    def generate_lesson(
        self, 
        content: str, 
        title: str = None,
        description: str = None,
        duration_minutes: int = 30,
        difficulty: str = "beginner"
    ) -> Lesson:
        """
        Generate a lesson using LLM with validation and retry logic.
        
        Args:
            content: Source content for lesson
            title: Optional lesson title
            description: Optional lesson description
            duration_minutes: Target duration (5, 30, or 60)
            difficulty: Difficulty level
            
        Returns:
            Validated Lesson object
            
        Raises:
            LessonGenerationError: If generation fails after retries
        """
        prompt = self._build_prompt(
            content=content,
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            difficulty=difficulty
        )
        
        for attempt in range(self.max_retries):
            try:
                # Generate raw output from LLM
                raw_output = self._call_llm(prompt)
                
                # Parse and validate
                lesson = self._parse_and_validate(raw_output)
                
                return lesson
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise LessonGenerationError(f"Failed after {self.max_retries} attempts: {str(e)}")
                
                # Continue to next attempt
                continue
        
        raise LessonGenerationError("All generation attempts failed")
    
    def _build_prompt(
        self, 
        content: str, 
        title: str = None,
        description: str = None,
        duration_minutes: int = 30,
        difficulty: str = "beginner"
    ) -> str:
        """Build the LLM prompt for lesson generation."""
        
        duration_rules = {
            5: {
                "content_blocks": "2-3 content blocks",
                "questions": "1 question"
            },
            30: {
                "content_blocks": "6-8 content blocks", 
                "questions": "3-4 questions"
            },
            60: {
                "content_blocks": "10-14 content blocks",
                "questions": "6-8 questions"
            }
        }
        
        rules = duration_rules.get(duration_minutes, duration_rules[30])
        
        prompt = f"""You are an AI lesson author.

Your task is to generate a lesson as structured JSON that STRICTLY follows the schema below.

DO NOT include explanations, markdown, comments, or extra text.
DO NOT invent new fields.
DO NOT include transitions, branching, retries, or UI logic.

You only produce AUTHORING STATES.

--------------------------------------------------
SCHEMA (must match exactly)

{{
  "schema_version": "1.0",
  "title": string,
  "estimated_duration_minutes": {duration_minutes},
  "states": [
    {{
      "id": string,
      "type": "content",
      "text": string (20–900 chars)
    }},
    {{
      "id": string,
      "type": "question",
      "question_format": "mcq",
      "prompt": string,
      "options": string[],
      "correct_answer": number,
      "explanation": string
    }}
  ]
}}

--------------------------------------------------
STRUCTURE RULES

- States must be LINEAR.
- No two question states may appear consecutively.
- Content and question states should alternate.
- Each question must test the immediately preceding content.
- IDs must be unique (use pattern: c_1, c_2, q_1, q_2, etc).
- Keep content concise and instructional.

--------------------------------------------------
DURATION RULES ({duration_minutes} minutes)

- {rules['content_blocks']}
- {rules['questions']}
- Target difficulty: {difficulty}

--------------------------------------------------
CONTENT TO TEACH

{content}

--------------------------------------------------
LESSON METADATA

Title: {title or "Generate based on content"}
Description: {description or "Generate based on content"}

--------------------------------------------------
OUTPUT

Return ONLY valid JSON.
If you are unsure, choose simpler phrasing."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API and return the response."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 2000
                    }
                },
                timeout=60
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "response" not in data:
                raise LessonGenerationError("Invalid LLM response format")
            
            return data["response"].strip()
            
        except requests.RequestException as e:
            raise LessonGenerationError(f"LLM API error: {str(e)}")
    
    def _parse_and_validate(self, raw_output: str) -> Lesson:
        """Parse raw LLM output and validate against schema."""
        try:
            # Clean the output - remove any markdown code blocks
            cleaned_output = raw_output.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[7:]
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]
            cleaned_output = cleaned_output.strip()
            
            # Parse JSON
            data = json.loads(cleaned_output)
            
            # Validate against Pydantic model
            lesson = Lesson.parse_obj(data)
            
            return lesson
            
        except json.JSONDecodeError as e:
            raise LessonGenerationError(f"Invalid JSON output: {str(e)}")
        except Exception as e:
            raise LessonGenerationError(f"Validation failed: {str(e)}")


# ---------- Duration Templates ----------

DURATION_TEMPLATES = {
    5: {
        "min_questions": 1,
        "max_questions": 2,
        "min_content": 1,
        "max_content": 3
    },
    30: {
        "min_questions": 3,
        "max_questions": 5,
        "min_content": 3,
        "max_content": 8
    },
    60: {
        "min_questions": 5,
        "max_questions": 8,
        "min_content": 5,
        "max_content": 14
    }
}


def validate_duration_constraints(states: list[AuthoredState], duration_minutes: int) -> bool:
    """
    Validate that states match duration constraints.
    
    Args:
        states: List of lesson states
        duration_minutes: Target duration
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If constraints are not met
    """
    if duration_minutes not in DURATION_TEMPLATES:
        raise ValueError(f"Invalid duration: {duration_minutes}")
    
    template = DURATION_TEMPLATES[duration_minutes]
    
    question_count = sum(1 for s in states if s.type == "question")
    content_count = sum(1 for s in states if s.type == "content")
    
    if question_count < template["min_questions"]:
        raise ValueError(f"Duration {duration_minutes}min requires at least {template['min_questions']} questions")
    
    if question_count > template["max_questions"]:
        raise ValueError(f"Duration {duration_minutes}min allows at most {template['max_questions']} questions")
    
    if content_count < template["min_content"]:
        raise ValueError(f"Duration {duration_minutes}min requires at least {template['min_content']} content blocks")
    
    return True
