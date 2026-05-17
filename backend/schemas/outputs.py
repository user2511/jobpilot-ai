# backend/schemas/outputs.py

from pydantic import BaseModel
from typing import List
from backend.schemas.job import MatchResult


class OptimizedBullets(BaseModel):
    original_bullets: List[str]
    rewritten_bullets: List[str]


class CoverLetter(BaseModel):
    content: str
    word_count: int


class RecruiterOutreach(BaseModel):
    subject_line: str
    message_body: str


class FullOutput(BaseModel):
    """
    Complete output returned to user after full analysis pipeline.
    """
    session_id: str
    role_title: str
    company_name: str
    match_result: MatchResult
    optimized_bullets: OptimizedBullets
    cover_letter: CoverLetter
    recruiter_outreach: RecruiterOutreach


class AnalysisResponse(BaseModel):
    """API response wrapper."""
    success: bool = True
    analysis_id: int
    output: FullOutput
    message: str = "Analysis complete"
