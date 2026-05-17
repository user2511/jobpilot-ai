# backend/routers/outputs.py

import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from models.db_models import JobAnalysis
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{analysis_id}")
async def get_output(analysis_id: int, db: Session = Depends(get_db)):
    """Retrieve a previously generated analysis by ID."""
    record = db.query(JobAnalysis).filter_by(id=analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "analysis_id": record.id,
        "session_id": record.session_id,
        "jd_source": record.jd_source,
        "jd_extracted": json.loads(record.jd_extracted),
        "match_result": json.loads(record.match_result),
        "rewritten_bullets": json.loads(record.rewritten_bullets or "[]"),
        "cover_letter": record.cover_letter,
        "recruiter_outreach": record.recruiter_outreach,
        "created_at": str(record.created_at)
    }


@router.get("/{analysis_id}/cover-letter", response_class=PlainTextResponse)
async def download_cover_letter(analysis_id: int, db: Session = Depends(get_db)):
    """Download cover letter as plain text."""
    record = db.query(JobAnalysis).filter_by(id=analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return record.cover_letter or "No cover letter generated"


@router.get("/{analysis_id}/outreach", response_class=PlainTextResponse)
async def download_outreach(analysis_id: int, db: Session = Depends(get_db)):
    """Download recruiter outreach as plain text."""
    record = db.query(JobAnalysis).filter_by(id=analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return record.recruiter_outreach or "No outreach message generated"
