# backend/schemas/resume.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional


class ExperienceItem(BaseModel):
    title: str
    company: str
    duration: Optional[str] = None      # "Jan 2024 – Present"
    bullets: List[str] = []             # achievement bullets


class EducationItem(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None


class ResumeMetadata(BaseModel):
    """
    Structured resume data extracted by LLM from raw PDF text.
    This is the canonical resume object used throughout the app.
    """
    session_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    experience: List[ExperienceItem] = []
    education: List[EducationItem] = []
    certifications: Optional[List[str]] = []
    raw_text: str


class ResumeUploadResponse(BaseModel):
    """Response after successful resume upload."""
    session_id: str
    full_name: str
    email: str
    skills_count: int
    experience_count: int
    message: str = "Resume uploaded and parsed successfully"
