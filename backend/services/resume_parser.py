# backend/services/resume_parser.py
# Parses PDF bytes → structured ResumeMetadata using LLM.

import uuid
import hashlib

from utils.pdf_parser import extract_text_from_pdf
from utils.redis_cache import get_cache, set_cache
from utils.logger import get_logger
from services.llm_client import call_llm_structured
from prompts.resume_structure import RESUME_STRUCTURE_PROMPT
from schemas.resume import ResumeMetadata, ExperienceItem, EducationItem

logger = get_logger(__name__)


async def parse_resume(file_bytes: bytes) -> ResumeMetadata:
    """
    Full pipeline: PDF bytes → structured ResumeMetadata.

    Steps:
    1. Extract raw text from PDF
    2. Check Redis cache (same PDF = same hash = skip LLM)
    3. Call LLM to structure the resume
    4. Validate output with Pydantic
    5. Cache result

    Args:
        file_bytes: Raw PDF content

    Returns:
        Validated ResumeMetadata object

    Raises:
        ValueError: If PDF extraction or LLM structuring fails
    """
    # Step 1: Extract text
    raw_text = extract_text_from_pdf(file_bytes)

    if len(raw_text.strip()) < 100:
        raise ValueError("Extracted text too short — PDF may be empty or image-only")

    # Step 2: Cache check by text hash
    text_hash = hashlib.md5(raw_text.encode()).hexdigest()
    cache_key = f"resume:{text_hash}"

    cached = await get_cache(cache_key)
    if cached:
        logger.info(f"Resume parse cache hit for hash {text_hash[:8]}")
        session_id = str(uuid.uuid4())   # new session even on cache hit
        cached["session_id"] = session_id
        return _build_metadata(cached, raw_text, session_id)

    # Step 3: LLM structuring
    logger.info("Calling LLM to structure resume")
    prompt = RESUME_STRUCTURE_PROMPT.format(resume_text=raw_text[:6000])  # cap at 6K chars
    structured = await call_llm_structured(prompt)

    # Step 4: Build and validate
    session_id = str(uuid.uuid4())
    metadata = _build_metadata(structured, raw_text, session_id)

    # Step 5: Cache (without session_id — that's per-request)
    cacheable = structured.copy()
    await set_cache(cache_key, cacheable, ttl=3600)

    logger.info(f"Resume parsed: {metadata.full_name}, {len(metadata.skills)} skills, session={session_id[:8]}")
    return metadata


def _build_metadata(data: dict, raw_text: str, session_id: str) -> ResumeMetadata:
    """Build and validate ResumeMetadata from LLM output dict."""
    # Safely build nested objects
    experience = [
        ExperienceItem(**exp) if isinstance(exp, dict) else ExperienceItem(
            title=str(exp), company="", bullets=[]
        )
        for exp in data.get("experience", [])
    ]
    education = [
        EducationItem(**edu) if isinstance(edu, dict) else EducationItem(
            degree=str(edu), institution=""
        )
        for edu in data.get("education", [])
    ]

    return ResumeMetadata(
        session_id=session_id,
        full_name=data.get("full_name", "Unknown"),
        email=data.get("email", ""),
        phone=data.get("phone"),
        summary=data.get("summary"),
        skills=data.get("skills", []),
        experience=experience,
        education=education,
        certifications=data.get("certifications", []),
        raw_text=raw_text
    )
