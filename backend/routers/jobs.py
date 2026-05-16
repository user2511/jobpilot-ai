# backend/routers/jobs.py

import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.job import JDInput
from schemas.outputs import AnalysisResponse, FullOutput
from schemas.resume import ResumeMetadata, ExperienceItem, EducationItem
from models.db_models import ResumeSession, JobAnalysis
from services.jd_extractor import extract_jd
from services.matcher import compute_match
from services.optimizer import optimize_resume
from services.generator import generate_cover_letter, generate_recruiter_outreach
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_job(
    payload: JDInput,
    db: Session = Depends(get_db)
):
    """
    Full analysis pipeline:
    1. Load resume from session
    2. Extract JD structure
    3. Compute fit score
    4. Optimize bullets
    5. Generate cover letter + outreach
    6. Save results to DB
    7. Return FullOutput
    """
    # Step 1: Load resume session
    record = db.query(ResumeSession).filter_by(session_id=payload.session_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Session not found. Upload your resume first.")

    resume = ResumeMetadata(
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

    # Step 2: Extract JD
    try:
        jd_text, jd_extracted = await extract_jd(payload)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"JD extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze job description")

    # Step 3: Compute match
    try:
        match_result = await compute_match(resume.skills, jd_extracted)
    except Exception as e:
        logger.error(f"Match computation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute match score")

    # Step 4: Optimize bullets
    try:
        optimized_bullets = await optimize_resume(resume, jd_extracted)
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize resume bullets")

    # Step 5: Generate materials
    try:
        cover_letter = await generate_cover_letter(resume, jd_extracted)
        recruiter_outreach = await generate_recruiter_outreach(resume, jd_extracted)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate application materials")

    # Step 6: Save to DB
    import hashlib
    jd_hash = hashlib.md5(jd_text.encode()).hexdigest()

    output = FullOutput(
        session_id=payload.session_id,
        role_title=jd_extracted.role_title,
        company_name=jd_extracted.company_name or "N/A",
        match_result=match_result,
        optimized_bullets=optimized_bullets,
        cover_letter=cover_letter,
        recruiter_outreach=recruiter_outreach
    )

    try:
        analysis = JobAnalysis(
            session_id=payload.session_id,
            jd_hash=jd_hash,
            jd_source=payload.jd_url,
            jd_extracted=json.dumps(jd_extracted.model_dump()),
            match_result=json.dumps(match_result.model_dump()),
            rewritten_bullets=json.dumps(optimized_bullets.rewritten_bullets),
            cover_letter=cover_letter.content,
            recruiter_outreach=recruiter_outreach.message_body
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        logger.info(f"Analysis saved: id={analysis.id}, score={match_result.fit_score}")
    except Exception as e:
        logger.error(f"DB save failed: {e}")
        db.rollback()
        # Don't fail the request — results are generated, just not persisted
        analysis = type("obj", (object,), {"id": 0})()

    return AnalysisResponse(
        analysis_id=analysis.id,
        output=output
    )


@router.get("/history/{session_id}")
async def get_analysis_history(session_id: str, db: Session = Depends(get_db)):
    """List all previous analyses for a session."""
    analyses = db.query(JobAnalysis).filter_by(session_id=session_id).all()
    return {
        "session_id": session_id,
        "count": len(analyses),
        "analyses": [
            {
                "id": a.id,
                "jd_source": a.jd_source,
                "fit_score": json.loads(a.match_result).get("fit_score"),
                "created_at": str(a.created_at)
            }
            for a in analyses
        ]
    }
