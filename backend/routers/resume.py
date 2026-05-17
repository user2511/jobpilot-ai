# backend/routers/resume.py

import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from services.resume_parser import parse_resume
from models.db_models import ResumeSession
from schemas.resume import ResumeUploadResponse, ResumeMetadata
from utils.logger import get_logger
from config import settings

logger = get_logger(__name__)
router = APIRouter()


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a PDF resume.
    Returns session_id used for all subsequent requests.
    """
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Read and validate size
    file_bytes = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB"
        )

    # Parse resume
    try:
        metadata = await parse_resume(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Resume parsing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process resume. Please try again.")

    # Save to DB
    try:
        db_session = ResumeSession(
            session_id=metadata.session_id,
            full_name=metadata.full_name,
            email=metadata.email,
            phone=metadata.phone,
            summary=metadata.summary,
            skills_json=json.dumps(metadata.skills),
            experience_json=json.dumps([e.model_dump() for e in metadata.experience]),
            education_json=json.dumps([e.model_dump() for e in metadata.education]),
            certifications_json=json.dumps(metadata.certifications or []),
            raw_text=metadata.raw_text
        )
        db.add(db_session)
        db.commit()
        logger.info(f"Resume saved to DB: session={metadata.session_id[:8]}")
    except Exception as e:
        logger.error(f"DB save failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save resume data")

    return ResumeUploadResponse(
        session_id=metadata.session_id,
        full_name=metadata.full_name,
        email=metadata.email,
        skills_count=len(metadata.skills),
        experience_count=len(metadata.experience)
    )


@router.get("/{session_id}", response_model=ResumeMetadata)
async def get_resume(session_id: str, db: Session = Depends(get_db)):
    """Retrieve parsed resume metadata by session ID."""
    record = db.query(ResumeSession).filter_by(session_id=session_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")

    from schemas.resume import ExperienceItem, EducationItem
    return ResumeMetadata(
        session_id=record.session_id,
        full_name=record.full_name,
        email=record.email,
        phone=record.phone,
        summary=record.summary,
        skills=json.loads(record.skills_json),
        experience=[ExperienceItem(**e) for e in json.loads(record.experience_json)],
        education=[EducationItem(**e) for e in json.loads(record.education_json)],
        certifications=json.loads(record.certifications_json or "[]"),
        raw_text=record.raw_text
    )
