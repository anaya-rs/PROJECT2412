"""
Lesson Migration - Legacy to v1 Conversion
Handles manual, auditable migration of legacy lessons to new format.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from .models import Lesson, AuthoredState, ContentState, QuestionState, LegacyLesson


class LessonMigrationError(Exception):
    """Custom exception for migration failures"""
    pass


class LegacyMigrator:
    """
    Handles migration from legacy lesson format to v1 FSM format.
    
    Rules:
    - Legacy lessons = playable only
    - v1 lessons = editable + playable
    - Migration is manual and auditable
    - Original lesson is never modified
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def migrate_legacy_to_v1(self, legacy_lesson_id: int, target_duration: int = 30) -> Dict[str, Any]:
        """
        Migrate a legacy lesson to v1 format.
        
        Args:
            legacy_lesson_id: ID of legacy lesson to migrate
            target_duration: Target duration for new lesson (5, 30, or 60)
            
        Returns:
            Dictionary with migration result
            
        Raises:
            LessonMigrationError: If migration fails
        """
        # Get legacy lesson
        legacy_lesson = self._get_legacy_lesson(legacy_lesson_id)
        
        # Convert to v1 format
        v1_lesson = self._convert_to_v1(legacy_lesson, target_duration)
        
        # Save new lesson
        new_lesson_id = self._save_v1_lesson(v1_lesson)
        
        # Log migration
        self._log_migration(legacy_lesson_id, new_lesson_id)
        
        return {
            "original_lesson_id": legacy_lesson_id,
            "new_lesson_id": new_lesson_id,
            "migrated_at": datetime.now().isoformat(),
            "schema_version": "1.0",
            "title": v1_lesson["title"],
            "states_count": len(v1_lesson["states"])
        }
    
    def _get_legacy_lesson(self, lesson_id: int) -> LegacyLesson:
        """Retrieve legacy lesson from database."""
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT id, title, description, start_node_id, nodes, transitions, metadata, created_at
            FROM lessons 
            WHERE id = ? AND (schema_version IS NULL OR schema_version = 'legacy')
        """, (lesson_id,))
        
        row = cursor.fetchone()
        if not row:
            raise LessonMigrationError(f"Legacy lesson {lesson_id} not found")
        
        return LegacyLesson(
            id=row[0],
            title=row[1],
            description=row[2],
            start_node_id=row[3],
            nodes=json.loads(row[4]) if row[4] else {},
            transitions=json.loads(row[5]) if row[5] else {},
            metadata=json.loads(row[6]) if row[6] else {}
        )
    
    def _convert_to_v1(self, legacy: LegacyLesson, target_duration: int) -> Dict[str, Any]:
        """Convert legacy lesson to v1 format."""
        states = []
        state_index = 0
        
        # Extract nodes from legacy format
        nodes = legacy.nodes
        if isinstance(nodes, dict):
            node_list = list(nodes.values())
        elif isinstance(nodes, list):
            node_list = nodes
        else:
            raise LessonMigrationError("Invalid nodes format in legacy lesson")
        
        # Convert each node to v1 state
        for node in node_list:
            if not isinstance(node, dict):
                continue
                
            node_type = node.get("type", "content")
            
            if node_type == "content":
                states.append({
                    "id": f"c_{state_index}",
                    "type": "content",
                    "text": self._truncate_text(node.get("content", ""), 900)
                })
                state_index += 1
                
            elif node_type == "question":
                # Handle MCQ questions
                options = node.get("options", [])
                if isinstance(options, list) and len(options) >= 2:
                    states.append({
                        "id": f"q_{state_index}",
                        "type": "question",
                        "question_format": "mcq",
                        "prompt": node.get("question", ""),
                        "options": options[:5],  # Limit to 5 options
                        "correct_answer": node.get("correct_index", 0),
                        "explanation": node.get("explanation", "Explanation unavailable.")
                    })
                    state_index += 1
        
        # Ensure we have at least 2 states
        if len(states) < 2:
            raise LessonMigrationError("Lesson must have at least 2 states after migration")
        
        # Create v1 lesson structure
        v1_lesson = {
            "schema_version": "1.0",
            "title": legacy.title[:120],  # Ensure title length constraint
            "estimated_duration_minutes": target_duration,
            "states": states
        }
        
        # Validate the converted lesson
        try:
            Lesson.parse_obj(v1_lesson)
        except Exception as e:
            raise LessonMigrationError(f"Migrated lesson failed validation: {str(e)}")
        
        return v1_lesson
    
    def _save_v1_lesson(self, v1_lesson: Dict[str, Any]) -> int:
        """Save the new v1 lesson to database."""
        cursor = self.db.cursor()
        
        cursor.execute("""
            INSERT INTO lessons (
                title, description, start_node_id, nodes, transitions, 
                metadata, schema_version, user_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            v1_lesson["title"],
            f"Migrated from legacy lesson",
            "start",
            json.dumps({"states": v1_lesson["states"]}),
            json.dumps({}),  # Empty transitions for v1
            json.dumps({
                "schema_version": "1.0",
                "engine_version": "fsm-v1",
                "generated_by": "migration_v1",
                "estimated_duration_minutes": v1_lesson["estimated_duration_minutes"]
            }),
            1,  # Default user ID - should be parameterized
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        self.db.commit()
        return cursor.lastrowid
    
    def _log_migration(self, from_lesson_id: int, to_lesson_id: int):
        """Log the migration for audit purposes."""
        cursor = self.db.cursor()
        
        # Create migration log table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_lesson_id INTEGER,
                to_lesson_id INTEGER,
                migrated_at TIMESTAMP,
                user_id INTEGER,
                notes TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO lesson_migrations (from_lesson_id, to_lesson_id, migrated_at, user_id, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (
            from_lesson_id,
            to_lesson_id,
            datetime.now().isoformat(),
            1,  # Default user ID - should be parameterized
            "Legacy to v1 migration"
        ))
        
        self.db.commit()
    
    def get_migration_history(self, lesson_id: int = None) -> List[Dict[str, Any]]:
        """Get migration history for a lesson or all migrations."""
        cursor = self.db.cursor()
        
        if lesson_id:
            cursor.execute("""
                SELECT * FROM lesson_migrations 
                WHERE from_lesson_id = ? OR to_lesson_id = ?
                ORDER BY migrated_at DESC
            """, (lesson_id, lesson_id))
        else:
            cursor.execute("""
                SELECT * FROM lesson_migrations 
                ORDER BY migrated_at DESC
            """)
        
        migrations = []
        for row in cursor.fetchall():
            migrations.append({
                "id": row[0],
                "from_lesson_id": row[1],
                "to_lesson_id": row[2],
                "migrated_at": row[3],
                "user_id": row[4],
                "notes": row[5]
            })
        
        return migrations


# ---------- Utility Functions ----------

def classify_lesson_schema(row_data: Dict[str, Any]) -> str:
    """
    Classify lesson schema version.
    
    Args:
        row_data: Database row data
        
    Returns:
        "legacy", "fsm_v1", or raises ValueError
    """
    schema_version = row_data.get("schema_version")
    
    if not schema_version or schema_version == "legacy":
        return "legacy"
    
    if schema_version == "1.0":
        return "fsm_v1"
    
    raise ValueError(f"Unknown schema version: {schema_version}")


def is_legacy_lesson(lesson_data: Dict[str, Any]) -> bool:
    """Check if lesson is in legacy format."""
    return classify_lesson_schema(lesson_data) == "legacy"


def can_migrate_lesson(lesson_data: Dict[str, Any]) -> bool:
    """Check if lesson can be migrated."""
    return is_legacy_lesson(lesson_data)
