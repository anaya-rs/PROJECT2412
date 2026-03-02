"""
shared exceptions for the application
"""


class LessonGenerationError(Exception):
    """raised when lesson generation fails"""
    pass


class QuestionGenerationError(Exception):
    """raised when question generation fails"""
    pass


class ValidationError(Exception):
    """raised when validation fails"""
    pass
