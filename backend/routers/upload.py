"""
Upload Router - File upload functionality
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Mock file upload endpoint
    In production, this would save the file and return file metadata
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Mock file processing - just return file info
    content_bytes = await file.read()
    content_text = content_bytes.decode('utf-8', errors='ignore')
    
    return {
        "filename": file.filename,
        "size": len(content_bytes),
        "content_type": file.content_type,
        "text": content_text,  # Add text field for frontend compatibility
        "fileName": file.filename,  # Add fileName field for frontend compatibility
        "message": "File uploaded successfully (mock)",
        "file_id": f"mock-file-{file.filename}"
    }
