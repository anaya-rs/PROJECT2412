#!/usr/bin/env python3
"""
Create the RAG demo lesson for showcase
"""

from core.db import get_db_session
from models.lesson import LessonDB
from domain.lesson import Lesson
from domain.state import ContentState, QuestionState, EndNotesState
from datetime import datetime
import json

def create_rag_demo_lesson():
    """Create the RAG demo lesson in the database"""
    
    # Create RAG demo states
    states = [
        ContentState(
            type="content",
            id="content_1",
            text="Retrieval-Augmented Generation (RAG) is an architecture pattern that combines information retrieval with large language models. Instead of relying only on the model's internal training data, RAG retrieves relevant documents from a knowledge base and injects them into the prompt before generation. This grounds the model's response in external, context-specific information."
        ),
        QuestionState(
            type="question",
            id="question_1",
            question_type="single_choice",
            prompt="What is the primary purpose of Retrieval-Augmented Generation (RAG)?",
            options=[
                "To fine-tune the language model on new data",
                "To replace large language models entirely", 
                "To ground model outputs using retrieved external information",
                "To reduce token usage in prompts"
            ],
            correct_answers=[2],
            explanation="RAG's primary purpose is to ground model outputs using retrieved external information, making responses more accurate and context-specific."
        ),
        ContentState(
            type="content",
            id="content_2",
            text="In a typical RAG pipeline, user-provided text is first split into smaller chunks. Each chunk is converted into a numerical representation called an embedding. These embeddings are stored in a vector database. When a user asks a question, the system embeds the query and retrieves the most semantically similar chunks to provide context for generation."
        ),
        QuestionState(
            type="question",
            id="question_2",
            question_type="single_choice",
            prompt="Why are embeddings used in a RAG system?",
            options=[
                "To compress text for faster storage",
                "To represent text in a numerical format that enables semantic similarity search",
                "To encrypt sensitive information", 
                "To summarize documents automatically"
            ],
            correct_answers=[1],
            explanation="Embeddings convert text into numerical representations that enable semantic similarity search, allowing the system to find contextually relevant documents."
        ),
        ContentState(
            type="content",
            id="content_3",
            text="RAG systems improve factual accuracy but introduce engineering challenges. Developers must handle chunking strategy, retrieval relevance, latency, and validation of model outputs. Without proper validation, even grounded systems can produce structured output errors or hallucinated connections between retrieved documents."
        ),
        QuestionState(
            type="question",
            id="question_3",
            question_type="single_choice",
            prompt="Which of the following is a common engineering challenge in RAG systems?",
            options=[
                "Rendering HTML on the frontend",
                "Managing semantic retrieval accuracy and output validation",
                "Training the model from scratch",
                "Eliminating the need for databases"
            ],
            correct_answers=[1],
            explanation="Managing semantic retrieval accuracy and output validation are key engineering challenges in RAG systems, ensuring the retrieved content is relevant and outputs are reliable."
        ),
        EndNotesState(
            type="end_notes",
            id="end_notes",
            summary="This lesson demonstrated how RAG combines retrieval and generation, how embeddings enable semantic search, and why validation remains critical in AI systems.",
            key_takeaways=[
                "RAG grounds LLM outputs using external retrieved information",
                "Embeddings enable semantic similarity search for relevant context",
                "Engineering challenges include retrieval accuracy and output validation"
            ]
        )
    ]
    
    # Create lesson
    lesson = Lesson(
        schema_version="1.0",
        title="RAG Lesson",
        description="A comprehensive introduction to how Retrieval-Augmented Generation works, covering architecture, embeddings, and engineering challenges.",
        difficulty="intermediate",
        estimated_duration_minutes=15,
        states=states
    )
    
    # Save to database
    db = get_db_session()
    try:
        lesson_db = LessonDB.from_domain(lesson, user_id=1)
        db.add(lesson_db)
        db.commit()
        
        print(f"✅ RAG Lesson created with ID: {lesson_db.id}")
        print(f"📝 Title: {lesson_db.title}")
        print(f"👤 User ID: {lesson_db.user_id}")
        print(f"📊 Duration: {lesson_db.estimated_duration_minutes} minutes")
        print(f"🔢 States: {len(states)}")
        print(f"🎯 Ready for frontend showcase!")
        
    finally:
        db.close()

if __name__ == "__main__":
    create_rag_demo_lesson()
