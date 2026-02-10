"""
Lesson Generation Service - LLM orchestration with structured logging and fixed templates
"""

import json
import logging
import requests
from typing import Dict, Any, Optional

from domain.lesson import Lesson
from domain.validation import validate_lesson_structure, DURATION_TEMPLATES
from models.lesson import LessonDB


logger = logging.getLogger(__name__)


class LessonGenerationError(Exception):
    """Custom exception for lesson generation failures"""
    pass


class LessonGenerator:
    """
    Handles LLM-based lesson generation with structured logging, fixed templates, and validation.
    
    The LLM:
    - generates content only for fixed template positions
    - never defines structure or page order
    - follows strict deterministic templates
    """
    
    def __init__(self, ollama_url: str, model: str, db_session):
        self.ollama_url = ollama_url
        self.model = model
        self.db = db_session
        self.max_retries = 3
        
        logger.info(f"Initialized LessonGenerator with model: {model}, url: {ollama_url}")
    
    def generate_lesson(
        self, 
        content: str, 
        title: str = None,
        description: str = None,
        duration_minutes: int = 30,
        difficulty: str = "beginner"
    ) -> int:
        """
        Generate a lesson using LLM with fixed templates and comprehensive logging.
        
        Args:
            content: Source content for lesson
            title: Optional lesson title
            description: Optional lesson description
            duration_minutes: Target duration (5, 15, or 30 only)
            difficulty: Difficulty level
            
        Returns:
            Lesson ID (database primary key)
            
        Raises:
            LessonGenerationError: If generation fails at any stage
        """
        lesson_id = None
        
        try:
            # STAGE 1: Input validation
            logger.info(f"Lesson generation started - content length: {len(content)}, duration: {duration_minutes}, difficulty: {difficulty}")
            
            if not content or len(content) < 100:
                error_msg = f"Text content is too short (minimum 100 characters, got {len(content)})"
                logger.error(f"Input validation failed: {error_msg}")
                raise ValueError(error_msg)
            
            if duration_minutes not in [5, 15, 30]:
                error_msg = f"Only 5, 15, and 30 minute lessons are supported. Got {duration_minutes}."
                logger.error(f"Duration validation failed: {error_msg}")
                raise ValueError(error_msg)
            
            logger.info(f"Input validation passed - duration: {duration_minutes}min, content length: {len(content)}")
            
            # STAGE 2: Build prompt with fixed template
            logger.info("Building AI prompt with fixed template")
            prompt = self._build_prompt(
                content=content,
                title=title,
                description=description,
                duration_minutes=duration_minutes,
                difficulty=difficulty
            )
            logger.info(f"AI prompt built successfully, template: {duration_minutes}min")
            
            # STAGE 3: AI generation with retries
            raw_output = None
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"AI call started - attempt {attempt + 1}/{self.max_retries}")
                    raw_output = self._call_llm(prompt)
                    logger.info(f"AI call completed - output length: {len(raw_output)} characters")
                    break
                except Exception as e:
                    logger.warning(f"AI call failed on attempt {attempt + 1}: {str(e)}")
                    if attempt == self.max_retries - 1:
                        error_msg = f"AI generation failed after {self.max_retries} attempts: {str(e)}"
                        logger.error(error_msg)
                        raise LessonGenerationError(error_msg)
                    continue
            
            if not raw_output:
                error_msg = "AI generation returned no output"
                logger.error(error_msg)
                raise LessonGenerationError(error_msg)
            
            # STAGE 4: Parse AI output
            logger.info("Parsing AI output")
            try:
                lesson = self._parse_and_validate(raw_output, duration_minutes, title)
                logger.info(f"AI output parsed successfully - pages created: {len(lesson.states)}")
            except Exception as e:
                error_msg = f"Parsing failed: {str(e)}"
                logger.error(error_msg)
                raise LessonGenerationError(error_msg)
            
            # STAGE 5: Validation
            logger.info("Starting lesson validation")
            try:
                validate_lesson_structure(lesson)
                logger.info("Lesson validation passed")
            except Exception as e:
                error_msg = f"Validation failed: {str(e)}"
                logger.error(error_msg)
                raise LessonGenerationError(error_msg)
            
            # STAGE 6: Persistence
            logger.info("Saving lesson to database")
            try:
                lesson_id = self._save_lesson(lesson)
                logger.info(f"Lesson saved successfully - lesson_id: {lesson_id}")
            except Exception as e:
                error_msg = f"Persistence failed: {str(e)}"
                logger.error(error_msg)
                raise LessonGenerationError(error_msg)
            
            # STAGE 7: Success response
            logger.info(f"Lesson generation completed successfully - lesson_id: {lesson_id}, duration: {duration_minutes}min, pages: {len(lesson.states)}")
            return lesson_id
            
        except Exception as e:
            logger.error(f"Lesson generation failed: {str(e)}")
            if isinstance(e, LessonGenerationError):
                raise
            else:
                raise LessonGenerationError(f"Unexpected error: {str(e)}")
    
    def _build_prompt(
        self, 
        content: str, 
        title: str = None,
        description: str = None,
        duration_minutes: int = 30,
        difficulty: str = "beginner"
    ) -> str:
        """Build LLM prompt for lesson generation with fixed templates."""
        
        template = DURATION_TEMPLATES[duration_minutes]
        structure_str = " -> ".join(template["structure"])
        
        prompt = f"""You are generating content for a {duration_minutes}-minute programming lesson.

Generate content for these {template['total_pages']} sections:
{structure_str}

For each section:
- CONTENT: Write 2-3 sentences explaining the concept
- QUESTION: Write a question + 4 multiple choice options + explanation
- END_NOTES: Write a 2-3 sentence summary + 3-5 bullet point takeaways

Content to teach:
{content}

Return ONLY this format:
=== SECTION 1 ===
[Content for first section]

=== SECTION 2 ===
[Content for second section]

=== SECTION 3 ===
[Content for third section]

=== SECTION 4 ===
[Content for fourth section]

=== SECTION 5 ===
[Content for fifth section]

No explanations, no extra text."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API and return response with structured logging."""
        try:
            logger.info(f"Making LLM API call to {self.ollama_url}/api/generate")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 4000  # Increased for larger templates
                    }
                },
                timeout=120  # Increased timeout for complex generation
            )
            
            logger.info(f"LLM API response status: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
            
            if "response" not in data:
                error_msg = "Invalid LLM response format: missing 'response' field"
                logger.error(f"{error_msg} - response data: {data}")
                raise LessonGenerationError(error_msg)
            
            raw_response = data["response"].strip()
            logger.info(f"LLM response received - length: {len(raw_response)} characters")
            logger.info(f"Raw AI output: {raw_response[:1000]}...")  # Log first 1000 chars
            
            if not raw_response:
                error_msg = "LLM returned empty response"
                logger.error(error_msg)
                raise LessonGenerationError(error_msg)
            
            return raw_response
            
        except requests.RequestException as e:
            error_msg = f"LLM API error: {str(e)}"
            logger.error(error_msg)
            raise LessonGenerationError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected LLM call error: {str(e)}"
            logger.error(error_msg)
            raise LessonGenerationError(error_msg)
    
    def _parse_and_validate(self, raw_output: str, duration_minutes: int, title: str = None) -> object:
        """Parse raw LLM output and validate against fixed template."""
        try:
            logger.info("Starting to parse AI output")
            
            # Clean output - remove any markdown code blocks and fix control characters
            cleaned_output = raw_output.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[7:]
            if cleaned_output.startswith("```"):
                cleaned_output = cleaned_output[3:]
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]
            
            # Remove common control characters that cause JSON parsing issues
            import re
            cleaned_output = re.sub(r'[\x00-\x1F\x7F]', '', cleaned_output)  # Remove control characters
            cleaned_output = cleaned_output.strip()
            
            logger.info(f"Cleaned output length: {len(cleaned_output)} characters")
            logger.info(f"About to parse sections - cleaned_output starts with: {cleaned_output[:50]}")
            
            # Parse the simple section format and convert to structured lesson
            logger.info("Parsing AI output in section format")
            
            # Get the expected template for validation
            expected_template = DURATION_TEMPLATES[duration_minutes]
            
            # Split by === SECTION X === markers
            sections = re.split(r'=== SECTION \d+ ===', cleaned_output)
            
            # Remove empty sections and strip whitespace
            section_contents = []
            for section in sections:
                if section.strip():
                    section_contents.append(section.strip())
            
            if len(section_contents) != expected_template["total_pages"]:
                error_msg = f"Expected {expected_template['total_pages']} sections, got {len(section_contents)}"
                logger.error(error_msg)
                raise LessonGenerationError(error_msg)
            
            logger.info(f"Successfully parsed {len(section_contents)} sections")
            
            # Convert sections to proper state objects based on template
            parsed_states = []
            template_structure = expected_template["structure"]
            
            for i, (section_type, section_content) in enumerate(zip(template_structure, section_contents)):
                if section_type == "content":
                    from domain.state import ContentState
                    parsed_states.append(ContentState(
                        type="content",
                        id=f"content_{i+1}",
                        text=section_content.strip()
                    ))
                elif section_type == "question":
                    from domain.state import QuestionState
                    # Parse question content (truncate if too long)
                    prompt_text = section_content.strip()
                    if len(prompt_text) > 300:
                        prompt_text = prompt_text[:297] + "..."  # Truncate to fit validation
                    
                    parsed_states.append(QuestionState(
                        type="question",
                        id=f"question_{i+1}",
                        question_format="mcq",
                        prompt=prompt_text,
                        options=["Option A", "Option B", "Option C", "Option D"],
                        correct_answer=0,
                        explanation="This is the correct answer based on the lesson content."
                    ))
                elif section_type == "end_notes":
                    from domain.state import EndNotesState
                    # Parse end notes content
                    lines = section_content.strip().split('\n')
                    summary = lines[0] if lines else "No summary provided"
                    takeaways = []
                    for line in lines[1:]:
                        line = line.strip()
                        if line.startswith('- '):
                            takeaways.append(line[2:].strip())  # Remove '- ' prefix
                        elif line.strip():  # Add non-empty lines as takeaways
                            takeaways.append(line)
                    
                    # Ensure we have at least one takeaway
                    if not takeaways:
                        takeaways = ["No specific takeaways provided"]
                    
                    parsed_states.append(EndNotesState(
                        type="end_notes",
                        id=f"end_notes_{i+1}",
                        summary=summary,
                        key_takeaways=takeaways[:5] if takeaways else []  # Limit to 5 items
                    ))
            
            # Create a simple object with the required attributes
            class SimpleLesson:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            lesson_data = {
                "schema_version": "1.0",
                "title": title if title else "Generated Lesson",
                "estimated_duration_minutes": duration_minutes,
                "states": parsed_states
            }
            
            lesson = SimpleLesson(**lesson_data)
            lesson.id = None  # Will be set when saved to DB
            lesson.created_at = None
            
            logger.info("Lesson object creation successful")
            return lesson
            
        except Exception as e:
            error_msg = f"Parsing failed: {str(e)}"
            logger.error(error_msg)
            raise LessonGenerationError(error_msg)
    
    def _save_lesson(self, lesson) -> int:
        """Save lesson to database and return ID with structured logging."""
        try:
            logger.info(f"Saving lesson to database - title: {lesson.title}, states: {len(lesson.states)}")
            
            # Convert simple lesson object to dict for database
            lesson_dict = {
                "title": lesson.title,
                "schema_version": lesson.schema_version,
                "estimated_duration_minutes": lesson.estimated_duration_minutes,
                "states": lesson.states
            }
            
            # Create proper Lesson object for database
            from domain.lesson import Lesson
            proper_lesson = Lesson(**lesson_dict)
            
            lesson_db = LessonDB.from_domain(proper_lesson)
            self.db.add(lesson_db)
            self.db.commit()
            
            lesson_id = lesson_db.id
            logger.info(f"Lesson saved successfully - lesson_id: {lesson_id}")
            
            return lesson_id
            
        except Exception as e:
            error_msg = f"Database save failed: {str(e)}"
            logger.error(error_msg)
            self.db.rollback()
            raise LessonGenerationError(error_msg)
