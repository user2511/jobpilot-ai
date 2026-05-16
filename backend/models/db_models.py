# backend/models/db_models.py
# ORM models — maps directly to SQLite tables.

import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime
from database import Base


class ResumeSession(Base):
    """
    Stores parsed resume metadata per session.
    One row per uploaded resume.
    """
    __tablename__ = "resume_sessions"

    session_id      = Column(String(36), primary_key=True)   # UUID
    full_name       = Column(String(200), nullable=False)
    email           = Column(String(200), nullable=False)
    phone           = Column(String(50), nullable=True)
    summary         = Column(Text, nullable=True)
    skills_json     = Column(Text, nullable=False)            # JSON list of strings
    experience_json = Column(Text, nullable=False)            # JSON list of dicts
    education_json  = Column(Text, nullable=False)            # JSON list of dicts
    certifications_json = Column(Text, nullable=True)         # JSON list of strings
    raw_text        = Column(Text, nullable=False)            # full extracted PDF text
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)


class JobAnalysis(Base):
    """
    Stores each job description analysis tied to a session.
    One session can have multiple analyses (multiple job applications).
    """
    __tablename__ = "job_analyses"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    session_id      = Column(String(36), nullable=False)      # FK to resume_sessions
    jd_hash         = Column(String(32), nullable=False)      # MD5 of JD text
    jd_source       = Column(String(500), nullable=True)      # URL if provided
    jd_extracted    = Column(Text, nullable=False)            # JSON: JDExtracted
    match_result    = Column(Text, nullable=False)            # JSON: MatchResult
    rewritten_bullets = Column(Text, nullable=True)           # JSON list
    cover_letter    = Column(Text, nullable=True)
    recruiter_outreach = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)
