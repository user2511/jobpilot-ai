# backend/services/matcher.py
# Computes fit score between resume and JD.
# Rule-based scoring first (fast, free), LLM for qualitative analysis.

from backend.utils.logger import get_logger
from backend.services.llm_client import call_llm_structured
from backend.prompts.matcher import MATCH_PROMPT
from backend.schemas.job import MatchResult, JDExtracted

logger = get_logger(__name__)


async def compute_match(
    resume_skills: list[str],
    jd_extracted: JDExtracted
) -> MatchResult:
    """
    Compare candidate resume skills against JD requirements.

    Scoring approach:
    - Base score: skill overlap % × 70 (rule-based, instant)
    - Bonus score: LLM evaluates experience quality, summary relevance (0–30)
    - Final = min(base + bonus, 100)

    Args:
        resume_skills: List of skills from parsed resume
        jd_extracted: Structured JD data

    Returns:
        MatchResult with score, gaps, and suggestions
    """
    # Normalize for comparison
    candidate_set = {s.lower().strip() for s in resume_skills}
    required_set  = {s.lower().strip() for s in jd_extracted.required_skills}

    # Rule-based skill matching (free, instant)
    matched = [s for s in jd_extracted.required_skills
               if s.lower().strip() in candidate_set]
    missing = [s for s in jd_extracted.required_skills
               if s.lower().strip() not in candidate_set]

    # Base score from skill coverage (max 70 points)
    if required_set:
        coverage = len(matched) / len(required_set)
        base_score = int(coverage * 70)
    else:
        base_score = 50  # no required skills listed — neutral score

    logger.info(f"Rule-based match: {len(matched)}/{len(required_set)} skills, base_score={base_score}")

    # LLM qualitative analysis (bonus points + suggestions)
    try:
        prompt = MATCH_PROMPT.format(
            candidate_skills=resume_skills,
            required_skills=jd_extracted.required_skills,
            matched_skills=matched,
            missing_skills=missing,
            responsibilities=jd_extracted.responsibilities
        )
        llm_result = await call_llm_structured(prompt)
        bonus_score      = int(llm_result.get("bonus_score", 0))
        weak_sections    = llm_result.get("weak_sections", [])
        suggestions      = llm_result.get("suggestions", [])
    except Exception as e:
        logger.warning(f"LLM match analysis failed, using rule-based only: {e}")
        bonus_score   = 0
        weak_sections = []
        suggestions   = [f"Add missing skills to your resume: {', '.join(missing[:3])}"] if missing else []

    final_score = min(base_score + bonus_score, 100)
    logger.info(f"Final fit score: {final_score} (base={base_score} + bonus={bonus_score})")

    return MatchResult(
        fit_score=final_score,
        matched_skills=matched,
        missing_skills=missing,
        weak_sections=weak_sections,
        improvement_suggestions=suggestions
    )
