# backend/services/generator.py
# Generates cover letter and recruiter outreach message.

from utils.logger import get_logger
from services.llm_client import call_llm_structured
from prompts.cover_letter import COVER_LETTER_PROMPT
from prompts.outreach import OUTREACH_PROMPT
from schemas.resume import ResumeMetadata
from schemas.job import JDExtracted
from schemas.outputs import CoverLetter, RecruiterOutreach

logger = get_logger(__name__)


async def generate_cover_letter(
    resume: ResumeMetadata,
    jd_extracted: JDExtracted
) -> CoverLetter:
    """
    Generate a tailored cover letter based on resume + JD.

    Args:
        resume: Parsed resume metadata
        jd_extracted: Structured JD

    Returns:
        CoverLetter with content and word count
    """
    # Pick top experience entry for context
    top_experience = ""
    if resume.experience:
        exp = resume.experience[0]
        top_experience = f"{exp.title} at {exp.company}: {'; '.join(exp.bullets[:2])}"

    logger.info(f"Generating cover letter for {jd_extracted.role_title}")

    prompt = COVER_LETTER_PROMPT.format(
        full_name=resume.full_name,
        summary=resume.summary or "Experienced professional",
        skills=", ".join(resume.skills[:10]),
        top_experience=top_experience,
        role_title=jd_extracted.role_title,
        company_name=jd_extracted.company_name or "your company",
        requirements=", ".join(jd_extracted.required_skills[:8])
    )

    try:
        result = await call_llm_structured(prompt)
        content = result.get("content", "")
        if not content:
            raise ValueError("Empty cover letter returned")
    except Exception as e:
        logger.warning(f"Cover letter generation failed: {e}")
        content = _fallback_cover_letter(resume, jd_extracted)

    word_count = len(content.split())
    logger.info(f"Cover letter generated: {word_count} words")

    return CoverLetter(content=content, word_count=word_count)


async def generate_recruiter_outreach(
    resume: ResumeMetadata,
    jd_extracted: JDExtracted
) -> RecruiterOutreach:
    """
    Generate a short recruiter cold outreach message.

    Args:
        resume: Parsed resume metadata
        jd_extracted: Structured JD

    Returns:
        RecruiterOutreach with subject line and message body
    """
    top_skills = ", ".join(resume.skills[:5])
    top_experience = ""
    if resume.experience:
        exp = resume.experience[0]
        top_experience = f"{exp.title} at {exp.company}"

    logger.info(f"Generating outreach for {jd_extracted.role_title}")

    prompt = OUTREACH_PROMPT.format(
        full_name=resume.full_name,
        top_skills=top_skills,
        top_experience=top_experience,
        role_title=jd_extracted.role_title,
        company_name=jd_extracted.company_name or "your company"
    )

    try:
        result = await call_llm_structured(prompt)
        subject = result.get("subject_line", f"Interested in {jd_extracted.role_title} Role")
        body    = result.get("message_body", "")
        if not body:
            raise ValueError("Empty outreach message returned")
    except Exception as e:
        logger.warning(f"Outreach generation failed: {e}")
        subject = f"Application for {jd_extracted.role_title}"
        body = _fallback_outreach(resume, jd_extracted)

    return RecruiterOutreach(subject_line=subject, message_body=body)


# ─── Fallback templates (used when LLM fails) ─────────────────────────────────

def _fallback_cover_letter(resume: ResumeMetadata, jd: JDExtracted) -> str:
    return (
        f"Dear Hiring Manager,\n\n"
        f"I am writing to express my interest in the {jd.role_title} position"
        f"{' at ' + jd.company_name if jd.company_name else ''}. "
        f"With expertise in {', '.join(resume.skills[:3])}, I am confident in my ability "
        f"to contribute effectively to your team.\n\n"
        f"I would welcome the opportunity to discuss how my background aligns with your needs.\n\n"
        f"Best regards,\n{resume.full_name}"
    )


def _fallback_outreach(resume: ResumeMetadata, jd: JDExtracted) -> str:
    return (
        f"Hi, I'm {resume.full_name}, a professional with experience in "
        f"{', '.join(resume.skills[:2])}. I came across the {jd.role_title} role "
        f"and believe my background is a strong match. Would you be open to a quick chat?"
    )
