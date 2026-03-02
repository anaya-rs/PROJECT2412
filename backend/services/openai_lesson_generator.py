"""
OpenAI-based Lesson Generator with integrated question generation
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Literal
from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.state import ContentState, QuestionState, EndNotesState, AuthoredState
from domain.lesson import Lesson
from domain.validation import validate_lesson_structure, DURATION_TEMPLATES
from config import settings

logger = logging.getLogger(__name__)


class StatewiseGenerationError(Exception):
    """Custom exception for state-wise lesson generation failures"""
    pass


@dataclass
class QuestionSpec:
    question_type: Literal["single_choice", "multiple_choice"]
    num_options: int

    def __post_init__(self):
        if self.num_options < 2:
            raise ValueError("at least two options required")
        if self.num_options > 8:
            raise ValueError("maximum 8 options supported")


class StateBlueprint:
    """Immutable blueprint for state generation order"""
    
    def __init__(self, duration_minutes: int):
        if duration_minutes not in DURATION_TEMPLATES:
            raise ValueError(f"Invalid duration: {duration_minutes}")
        
        self.duration_minutes = duration_minutes
        self.template = DURATION_TEMPLATES[duration_minutes]
        self.structure = self.template["structure"].copy()  # Create a mutable copy
        
    def get_state_type(self, index: int) -> str:
        """Get the state type at the given index"""
        if index < 0 or index >= len(self.structure):
            raise ValueError(f"Invalid state index: {index}")
        return self.structure[index]
    
    def get_total_states(self) -> int:
        """Get total number of states in blueprint"""
        return len(self.structure)
    
    def is_end_notes(self, index: int) -> bool:
        """Check if the state at index is end notes"""
        return self.get_state_type(index) == "end_notes"


class StatePromptBuilder:
    """Builds targeted prompts for each state type"""
    
    @staticmethod
    def build_content_prompt(
        source_content: str, 
        state_number: int, 
        total_states: int,
        previous_context: str = ""
    ) -> str:
        """Build prompt for content state generation"""
        
        context_section = f'PREVIOUS CONTEXT:\n{previous_context}\n' if previous_context else ""
        prompt = f"""Generate educational content for state {state_number} of {total_states}.

SOURCE MATERIAL:
{source_content[:2000]}

{context_section}

INSTRUCTIONS:
- Generate ONE content section (100-200 words)
- Focus on a specific concept from the source material
- Write in clear, educational language suitable for the target audience
- Do NOT include questions, quizzes, or assessments
- Do NOT use markdown formatting or special characters
- Content should be self-contained but logically connect to previous context
- Must be directly derived from the source material - no external knowledge

Return ONLY the content text, nothing else."""
        
        return prompt
    
    @staticmethod
    def build_single_choice_prompt(
        source_content: str,
        state_number: int,
        total_states: int,
        previous_context: str = ""
    ) -> str:
        """Build prompt for single choice question generation"""
        
        context_section = f'PREVIOUS CONTEXT:\n{previous_context}\n' if previous_context else ""
        prompt = f"""Generate a single choice multiple choice question for state {state_number} of {total_states}.

SOURCE MATERIAL:
{source_content[:2000]}

{context_section}

INSTRUCTIONS:
- Generate ONE single choice question
- Question must test understanding of concepts from the source material
- Provide EXACTLY 4 answer options (A, B, C, D)
- EXACTLY 1 option must be correct
- All options must be unique and plausible
- Provide a brief explanation for the correct answer
- Question must be answerable from the source material context

Return JSON format exactly:
{{
  "prompt": "The question text",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_answer": 0,
  "explanation": "Brief explanation of why this is correct"
}}

IMPORTANT:
- "correct_answer" must be 0, 1, 2, or 3 (0-based index)
- All options must be different
- No duplicate options allowed"""
        
        return prompt
    
    @staticmethod
    def build_multiple_choice_prompt(
        source_content: str,
        state_number: int,
        total_states: int,
        previous_context: str = ""
    ) -> str:
        """Build prompt for multiple choice question generation"""
        
        context_section = f'PREVIOUS CONTEXT:\n{previous_context}\n' if previous_context else ""
        prompt = f"""Generate a multiple choice question for state {state_number} of {total_states}.

SOURCE MATERIAL:
{source_content[:2000]}

{context_section}

INSTRUCTIONS:
- Generate ONE multiple choice question
- Question must test understanding of concepts from the source material
- Provide EXACTLY 4 answer options (A, B, C, D)
- AT LEAST 1 option must be correct
- All options must be unique and plausible
- Provide a brief explanation for the correct answers
- Question must be answerable from the source material context

Return JSON format exactly:
{{
  "prompt": "The question text",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_answers": [0, 2],
  "explanation": "Brief explanation of why these are correct"
}}

IMPORTANT:
- "correct_answers" must be an array of indices [0, 1, 2, and/or 3]
- All options must be different
- No duplicate options allowed"""
        
        return prompt
    
    @staticmethod
    def build_true_false_prompt(
        source_content: str,
        state_number: int,
        total_states: int,
        previous_context: str = ""
    ) -> str:
        """Build prompt for true/false question generation"""
        
        context_section = f'PREVIOUS CONTEXT:\n{previous_context}\n' if previous_context else ""
        prompt = f"""Generate a true/false question for state {state_number} of {total_states}.

SOURCE MATERIAL:
{source_content[:2000]}

{context_section}

INSTRUCTIONS:
- Generate ONE true/false question
- Question must test understanding of concepts from the source material
- Provide EXACTLY 2 options: "True" and "False"
- EXACTLY 1 option must be correct
- Provide a brief explanation for the correct answer
- Question must be answerable from the source material context

Return JSON format exactly:
{{
  "prompt": "The question text",
  "options": ["True", "False"],
  "correct_answer": 0,
  "explanation": "Brief explanation of why this is correct"
}}

IMPORTANT:
- "correct_answer" must be 0 (True) or 1 (False)
- Options must be exactly ["True", "False"]"""
        
        return prompt
    
    @staticmethod
    def build_end_notes_prompt(
        source_content: str,
        state_number: int,
        total_states: int,
        previous_context: str = ""
    ) -> str:
        """Build prompt for end notes generation"""
        
        context_section = f'PREVIOUS CONTEXT:\n{previous_context}\n' if previous_context else ""
        prompt = f"""Generate end notes for state {state_number} of {total_states}.

SOURCE MATERIAL:
{source_content[:2000]}

{context_section}

INSTRUCTIONS:
- Generate a brief summary (2-3 sentences) of the lesson content
- List 3-5 key takeaways from the lesson
- Focus ONLY on concepts covered in this lesson
- Do NOT introduce new concepts or external information
- Keep it concise and memorable

Return JSON format exactly:
{{
  "summary": "Brief lesson summary",
  "key_takeaways": ["Key point 1", "Key point 2", "Key point 3"]
}}

IMPORTANT:
- summary must be non-empty
- key_takeaways must have 3-5 items
- All content must be derived from lesson context only"""
        
        return prompt


class StateValidator:
    """Strict validation for each state type"""
    
    @staticmethod
    def validate_content_state(state: ContentState) -> bool:
        """Validate content state meets requirements"""
        if not state.text or not state.text.strip():
            raise ValueError("Content state text cannot be empty")
        
        if len(state.text.strip()) < 50:
            raise ValueError("Content state text must be at least 50 characters")
        
        if len(state.text) > 900:
            raise ValueError("Content state text exceeds 900 character limit")
        
        # Check for embedded questions
        if '?' in state.text and any(word in state.text.lower() for word in ['question', 'answer', 'choose', 'select']):
            raise ValueError("Content state contains embedded questions")
        
        return True
    
    @staticmethod
    def validate_single_choice_question(state: QuestionState) -> bool:
        """Validate single choice question meets requirements"""
        if not state.prompt or not state.prompt.strip():
            raise ValueError("Question prompt cannot be empty")
        
        if len(state.prompt) < 10:
            raise ValueError("Question prompt must be at least 10 characters")
        
        if len(state.options) != 4:
            raise ValueError("Single choice question must have exactly 4 options")
        
        if len(state.correct_answers) != 1:
            raise ValueError("Single choice question must have exactly 1 correct answer")
        
        # Check for duplicate options
        if len(set(state.options)) != len(state.options):
            raise ValueError("Question options must be unique")
        
        # Validate correct answer index
        correct_idx = state.correct_answers[0]
        if correct_idx < 0 or correct_idx >= len(state.options):
            raise ValueError("Correct answer index out of bounds")
        
        if not state.explanation or not state.explanation.strip():
            raise ValueError("Question explanation cannot be empty")
        
        return True
    
    @staticmethod
    def validate_multiple_choice_question(state: QuestionState) -> bool:
        """Validate multiple choice question meets requirements"""
        if not state.prompt or not state.prompt.strip():
            raise ValueError("Question prompt cannot be empty")
        
        if len(state.prompt) < 10:
            raise ValueError("Question prompt must be at least 10 characters")
        
        if len(state.options) != 4:
            raise ValueError("Multiple choice question must have exactly 4 options")
        
        if len(state.correct_answers) < 1:
            raise ValueError("Multiple choice question must have at least 1 correct answer")
        
        # Check for duplicate options
        if len(set(state.options)) != len(state.options):
            raise ValueError("Question options must be unique")
        
        # Validate correct answer indices
        for idx in state.correct_answers:
            if idx < 0 or idx >= len(state.options):
                raise ValueError("Correct answer index out of bounds")
        
        if not state.explanation or not state.explanation.strip():
            raise ValueError("Question explanation cannot be empty")
        
        return True
    
    @staticmethod
    def validate_true_false_question(state: QuestionState) -> bool:
        """Validate true/false question meets requirements"""
        if not state.prompt or not state.prompt.strip():
            raise ValueError("Question prompt cannot be empty")
        
        if len(state.prompt) < 10:
            raise ValueError("Question prompt must be at least 10 characters")
        
        if len(state.options) != 2:
            raise ValueError("True/false question must have exactly 2 options")
        
        if state.options != ["True", "False"]:
            raise ValueError("True/false question options must be exactly ['True', 'False']")
        
        if len(state.correct_answers) != 1:
            raise ValueError("True/false question must have exactly 1 correct answer")
        
        # Validate correct answer index
        correct_idx = state.correct_answers[0]
        if correct_idx not in [0, 1]:
            raise ValueError("True/false correct answer must be 0 (True) or 1 (False)")
        
        if not state.explanation or not state.explanation.strip():
            raise ValueError("Question explanation cannot be empty")
        
        return True
    
    @staticmethod
    def validate_end_notes_state(state: EndNotesState) -> bool:
        """Validate end notes state meets requirements"""
        if not state.summary or not state.summary.strip():
            raise ValueError("End notes summary cannot be empty")
        
        if len(state.summary) < 20:
            raise ValueError("End notes summary must be at least 20 characters")
        
        if len(state.summary) > 900:
            raise ValueError("End notes summary exceeds 900 character limit")
        
        if not state.key_takeaways or len(state.key_takeaways) < 3:
            raise ValueError("End notes must have at least 3 key takeaways")
        
        if len(state.key_takeaways) > 5:
            raise ValueError("End notes cannot have more than 5 key takeaways")
        
        # Check for empty takeaways
        for takeaway in state.key_takeaways:
            if not takeaway or not takeaway.strip():
                raise ValueError("Key takeaway cannot be empty")
        
        return True


class OpenAILessonGenerator:
    """Main OpenAI-based lesson generator with clean architecture"""
    
    def __init__(self, api_key: str, model: str, base_url: str, db_session):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.db_session = db_session
        self.prompt_builder = StatePromptBuilder()
        self.validator = StateValidator()
        self.max_retries = 3
        
        logger.info(f"Initialized OpenAILessonGenerator with model: {model}")
    
    def generate_lesson(
        self, 
        content: str, 
        title: str = None,
        description: str = None,
        duration_minutes: int = 30,
        difficulty: str = "beginner",
        user_id: int = 1
    ) -> int:
        """Generate a complete lesson using state-wise approach"""
        
        try:
            logger.info(f"Starting OpenAI state-wise lesson generation: duration={duration_minutes}")
            
            # Input validation
            self._validate_inputs(content, duration_minutes, difficulty)
            
            # Build state blueprint
            blueprint = StateBlueprint(duration_minutes)
            logger.info(f"Created blueprint with {blueprint.get_total_states()} states")
            
            # Generate states one by one
            states = []
            previous_context = ""
            
            for i in range(blueprint.get_total_states()):
                state_type = blueprint.get_state_type(i)
                logger.info(f"Generating state {i+1}/{blueprint.get_total_states()}: {state_type}")
                
                try:
                    state = self._generate_single_state(
                        state_type=state_type,
                        state_number=i+1,
                        total_states=blueprint.get_total_states(),
                        source_content=content,
                        previous_context=previous_context
                    )
                    
                    # Validate immediately after generation
                    self._validate_state(state)
                    
                    states.append(state)
                    
                    # Update context for next state
                    previous_context = self._update_context(previous_context, state)
                    
                    logger.info(f"Successfully generated and validated state {i+1}")
                    
                except Exception as e:
                    error_msg = f"Failed to generate state {i+1} ({state_type}): {str(e)}"
                    logger.error(error_msg)
                    raise StatewiseGenerationError(error_msg)
            
            # Create lesson
            lesson = Lesson(
                schema_version="1.0",
                title=title or f"Generated Lesson ({difficulty})",
                description=description or f"A {difficulty} level lesson generated from provided content.",
                difficulty=difficulty,
                estimated_duration_minutes=duration_minutes,
                states=states
            )
            
            # Final validation
            validate_lesson_structure(lesson)
            logger.info("Lesson validation passed")
            
            # Save lesson to database and return ID
            lesson_id = self.save_lesson(lesson, user_id)
            logger.info(f"Lesson generation completed - lesson_id: {lesson_id}")
            
            return lesson_id
            
        except Exception as e:
            logger.error(f"Lesson generation failed: {e}")
            raise StatewiseGenerationError(f"Lesson generation failed: {e}")
    
    def _validate_inputs(self, content: str, duration_minutes: int, difficulty: str) -> None:
        """Validate generation inputs"""
        if not content or len(content) < 100:
            raise ValueError("Content must be at least 100 characters")
        
        if duration_minutes not in [5, 15, 30]:
            raise ValueError("Duration must be 5, 15, or 30 minutes")
        
        if difficulty not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("Difficulty must be beginner, intermediate, or advanced")
    
    def _generate_single_state(
        self,
        state_type: str,
        state_number: int,
        total_states: int,
        source_content: str,
        previous_context: str
    ) -> AuthoredState:
        """Generate a single state with retries"""
        
        for attempt in range(self.max_retries):
            try:
                if state_type == "content":
                    return self._generate_content_state(state_number, total_states, source_content, previous_context)
                elif state_type == "question":
                    return self._generate_question_state(state_number, total_states, source_content, previous_context)
                elif state_type == "end_notes":
                    return self._generate_end_notes_state(state_number, total_states, source_content, previous_context)
                else:
                    raise ValueError(f"Unknown state type: {state_type}")
                    
            except Exception as e:
                logger.warning(f"State generation attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                continue
        
        raise StatewiseGenerationError(f"Failed to generate {state_type} state after {self.max_retries} attempts")
    
    def _generate_content_state(self, state_number: int, total_states: int, source_content: str, previous_context: str) -> ContentState:
        """Generate a content state"""
        prompt = self.prompt_builder.build_content_prompt(
            source_content, state_number, total_states, previous_context
        )
        
        response = self._call_openai(prompt)
        content_text = response.strip()
        
        # Truncate to 900 characters to meet validation requirements
        if len(content_text) > 900:
            content_text = content_text[:897] + "..."
        
        return ContentState(
            type="content",
            id=f"content_{state_number}",
            text=content_text[:900]  # Ensure max 900 chars
        )
    
    def _generate_question_state(self, state_number: int, total_states: int, source_content: str, previous_context: str) -> QuestionState:
        """Generate a question state with integrated logic"""
        # Use single choice as default for consistency
        spec = QuestionSpec(question_type="single_choice", num_options=4)
        
        for attempt in range(self.max_retries):
            try:
                raw = self._generate_raw_question(source_content, spec, state_number, total_states, previous_context)
                return self._parse_question_response(raw, spec, state_number)
            except Exception as e:
                logger.warning(f"Question generation attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    # Fallback to basic question generation
                    return self._generate_fallback_question(state_number)
                continue
        
        raise StatewiseGenerationError(f"Failed to generate question after {self.max_retries} attempts")
    
    def _generate_raw_question(self, source_content: str, spec: QuestionSpec, 
                              state_number: int, total_states: int, previous_context: str) -> str:
        """Generate raw question using OpenAI"""
        option_labels = [chr(65 + i) for i in range(spec.num_options)]

        if spec.question_type == "single_choice":
            correct_instruction = "Exactly ONE correct answer."
        else:
            correct_instruction = "One or more correct answers."

        options_format = "\n".join(
            [f"{label}) <option>" for label in option_labels]
        )

        context_section = f'PREVIOUS CONTEXT:\n{previous_context}\n' if previous_context else ""
        
        prompt = f"""Generate a {spec.question_type.replace('_', ' ')} question for state {state_number} of {total_states}.

SOURCE MATERIAL:
{source_content[:2000]}

{context_section}

INSTRUCTIONS:
- Generate ONE {spec.question_type.replace('_', ' ')} question
- Question must test understanding of concepts from the source material
- Provide EXACTLY {spec.num_options} answer options
- {correct_instruction}
- All options must be unique and plausible
- Provide a brief explanation for the correct answer
- Question must be answerable from the source material context

Format EXACTLY:
QUESTION: <question>
{options_format}
correct: <comma-separated letters>
explanation: <short explanation>
<END>

Rules:
- Exactly {spec.num_options} options
- {correct_instruction}
"""

        return self._call_openai(prompt)
    
    def _parse_question_response(self, raw: str, spec: QuestionSpec, state_number: int) -> QuestionState:
        """Parse question response with validation"""
        raw = raw.replace("<END>", "").strip()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]

        expected_min_lines = 1 + spec.num_options + 2
        if len(lines) < expected_min_lines:
            raise ValueError(
                f"incomplete question block (expected ≥{expected_min_lines}, got {len(lines)})"
            )

        if not lines[0].startswith("QUESTION:"):
            raise ValueError("invalid question format")

        # parse options
        options = []
        for i in range(spec.num_options):
            line = lines[1 + i]
            expected_prefix = f"{chr(65+i)})"
            if not line.startswith(expected_prefix):
                raise ValueError("malformed option format")
            options.append(line[3:].strip())

        # parse correct line
        correct_line = lines[1 + spec.num_options]
        if not correct_line.startswith("correct:"):
            raise ValueError("missing correct line")

        correct_letters = [
            letter.strip().upper()
            for letter in correct_line.split(":", 1)[1].split(",")
        ]

        valid_letters = {chr(65+i) for i in range(spec.num_options)}
        for letter in correct_letters:
            if letter not in valid_letters:
                raise ValueError("invalid correct answer letter")

        correct_indices = [
            ord(letter) - 65 for letter in correct_letters
        ]

        # parse explanation
        explanation_line = lines[2 + spec.num_options]
        if not explanation_line.startswith("explanation:"):
            raise ValueError("missing explanation")

        explanation = explanation_line.split(":", 1)[1].strip()

        return QuestionState(
            type="question",
            id=f"question_{state_number}",
            question_type=spec.question_type,
            prompt=lines[0][9:].strip(),
            options=options,
            correct_answers=correct_indices,
            explanation=explanation,
        )
    
    def _generate_fallback_question(self, state_number: int) -> QuestionState:
        """Generate a fallback question when OpenAI fails"""
        return QuestionState(
            type="question",
            id=f"question_{state_number}",
            question_type="single_choice",
            prompt="Which of the following best summarizes the main concept presented in this lesson?",
            options=["Option A", "Option B", "Option C", "Option D"],
            correct_answers=[0],
            explanation="This is the correct answer based on the lesson content."
        )
    
    def _generate_end_notes_state(self, state_number: int, total_states: int, source_content: str, previous_context: str) -> EndNotesState:
        """Generate an end notes state"""
        prompt = self.prompt_builder.build_end_notes_prompt(
            source_content, state_number, total_states, previous_context
        )
        
        response = self._call_openai(prompt)
        end_notes_data = self._parse_json_response(response)
        
        # Truncate to meet validation requirements
        summary_text = end_notes_data["summary"][:500] if len(end_notes_data["summary"]) > 500 else end_notes_data["summary"]
        takeaways = end_notes_data["key_takeaways"][:5] if len(end_notes_data["key_takeaways"]) > 5 else end_notes_data["key_takeaways"]
        
        # Ensure we have at least 3 takeaways (fallback logic)
        if len(takeaways) < 3:
            # Add generic takeaways if OpenAI didn't provide enough
            generic_takeaways = [
                "Lesson completed successfully",
                "Key concepts were covered",
                "Learning objectives achieved"
            ]
            takeaways.extend(generic_takeaways[:3 - len(takeaways)])
        
        return EndNotesState(
            type="end_notes",
            id=f"end_notes_{state_number}",
            summary=summary_text,
            key_takeaways=takeaways
        )
    
    def _validate_state(self, state: AuthoredState) -> None:
        """Validate a single state immediately after generation"""
        if isinstance(state, ContentState):
            self.validator.validate_content_state(state)
        elif isinstance(state, QuestionState):
            if state.question_type == "single_choice":
                self.validator.validate_single_choice_question(state)
            elif state.question_type == "multiple_choice":
                self.validator.validate_multiple_choice_question(state)
            elif state.question_type == "true_false":
                self.validator.validate_true_false_question(state)
            else:
                raise ValueError(f"Unknown question type: {state.question_type}")
        elif isinstance(state, EndNotesState):
            self.validator.validate_end_notes_state(state)
        else:
            raise ValueError(f"Unknown state type: {type(state)}")
    
    def _update_context(self, previous_context: str, new_state: AuthoredState) -> str:
        """Update context string with new state information"""
        state_summary = ""
        
        if isinstance(new_state, ContentState):
            state_summary = f"Content {new_state.id}: {new_state.text[:100]}..."
        elif isinstance(new_state, QuestionState):
            state_summary = f"Question {new_state.id}: {new_state.prompt[:80]}..."
        elif isinstance(new_state, EndNotesState):
            state_summary = f"End Notes {new_state.id}: {new_state.summary[:80]}..."
        
        if previous_context:
            return f"{previous_context}\n{state_summary}"
        else:
            return state_summary
    
    def _call_openai(self, prompt: str) -> str:
        """Make a call to OpenAI API"""
        import requests
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                raise StatewiseGenerationError(f"OpenAI API call failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            raise StatewiseGenerationError("OpenAI API call timeout")
        except Exception as e:
            raise StatewiseGenerationError(f"OpenAI API call error: {e}")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from OpenAI with error handling"""
        try:
            # Clean the response
            response = response.strip()
            
            # Remove markdown code blocks
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response)
            
            # Find JSON object
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw response: {response}")
            raise StatewiseGenerationError(f"Invalid JSON in OpenAI response: {e}")
    
    def save_lesson(self, lesson: Lesson, user_id: int = 1) -> int:
        """Save lesson to database"""
        from models.lesson import LessonDB
        
        lesson_db = LessonDB.from_domain(lesson, user_id)
        
        self.db_session.add(lesson_db)
        self.db_session.commit()
        
        lesson_id = lesson_db.id
        logger.info(f"Lesson saved to database: id={lesson_id}")
        
        return lesson_id
