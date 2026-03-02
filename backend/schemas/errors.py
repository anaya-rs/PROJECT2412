"""
Error response schemas for consistent API error handling
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name if validation error")
    value: Optional[Any] = Field(None, description="Invalid value if validation error")


class ValidationError(BaseModel):
    """Validation error details"""
    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(None, description="Invalid value that failed validation")


class ErrorResponse(BaseModel):
    """Standard error response format"""
    success: bool = Field(False, description="Always false for error responses")
    error: ErrorDetail = Field(..., description="Primary error information")
    validation_errors: Optional[List[ValidationError]] = Field(None, description="Detailed validation errors")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


class CommonErrors:
    """Common error definitions"""
    
    @staticmethod
    def not_found(resource: str, identifier: str = None) -> ErrorResponse:
        """Resource not found error"""
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        
        return ErrorResponse(
            error=ErrorDetail(
                code="NOT_FOUND",
                message=message
            )
        )
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized access") -> ErrorResponse:
        """Unauthorized access error"""
        return ErrorResponse(
            error=ErrorDetail(
                code="UNAUTHORIZED",
                message=message
            )
        )
    
    @staticmethod
    def forbidden(message: str = "Access denied") -> ErrorResponse:
        """Forbidden access error"""
        return ErrorResponse(
            error=ErrorDetail(
                code="FORBIDDEN", 
                message=message
            )
        )
    
    @staticmethod
    def validation_failed(message: str, validation_errors: List[ValidationError] = None) -> ErrorResponse:
        """Validation failed error"""
        return ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_FAILED",
                message=message
            ),
            validation_errors=validation_errors
        )
    
    @staticmethod
    def internal_error(message: str = "Internal server error") -> ErrorResponse:
        """Internal server error"""
        return ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message=message
            )
        )
    
    @staticmethod
    def lesson_generation_failed(message: str = "Lesson generation failed") -> ErrorResponse:
        """Lesson generation specific error"""
        return ErrorResponse(
            error=ErrorDetail(
                code="LESSON_GENERATION_FAILED",
                message=message
            )
        )
    
    @staticmethod
    def session_not_found(session_id: str) -> ErrorResponse:
        """Session not found error"""
        return ErrorResponse(
            error=ErrorDetail(
                code="SESSION_NOT_FOUND",
                message=f"Session {session_id} not found or expired"
            )
        )
    
    @staticmethod
    def invalid_lesson_state(message: str = "Invalid lesson state") -> ErrorResponse:
        """Invalid lesson state error"""
        return ErrorResponse(
            error=ErrorDetail(
                code="INVALID_LESSON_STATE",
                message=message
            )
        )
