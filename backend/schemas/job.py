# backend/schemas/job.py

from pydantic import BaseModel, model_validator
from typing import List, Optional


class JDInput(BaseModel):
    """
    Input from user — either raw JD text or a URL.
    At least one must be provided.
    """
    session_id: str
    jd_text: Optional[str] = None
    jd_url: Optional[str] = None

    @model_validator(mode="after")
    def check_jd_provided(self):
        if not self.jd_text and not self.jd_url:
            raise ValueError("Provide either jd_text or jd_url")
        return self


class JDExtracted(BaseModel):
    """
    Structured information extracted from a job description by LLM.
    """
    role_title: str
    company_name: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    responsibilities: List[str] = []
    experience_years: Optional[str] = None     # "3-5 years"
    keywords: List[str] = []                   # ATS keywords


class MatchResult(BaseModel):
    """
    Result of comparing a resume against a job description.
    """
    fit_score: int                             # 0–100
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    weak_sections: List[str] = []             # e.g. ["summary", "bullet 3"]
    improvement_suggestions: List[str] = []
