# backend/services/optimizer.py
# Rewrites resume bullets to better match the target JD.
# Never invents experience — only improves existing content.

from utils.logger import get_logger
from services.llm_client import call_llm_structured
from prompts.optimizer import BULLET_REWRITE_PROMPT
from schemas.resume import ResumeMetadata
from schemas.job import JDExtracted
from schemas.outputs import OptimizedBullets

logger = get_logger(__name__)


def _collect_all_bullets(resume: ResumeMetadata) -> list[str]:
    """Extract all bullet points from all experience entries."""
    bullets = []
    for exp in resume.experience:
        bullets.extend(exp.bullets)
    return bullets


async def optimize_resume(
    resume: ResumeMetadata,
    jd_extracted: JDExtracted
) -> OptimizedBullets:
    """
    Rewrite resume bullets to better match JD keywords and tone.

    Args:
        resume: Parsed resume metadata
        jd_extracted: Structured JD data

    Returns:
        OptimizedBullets with original and rewritten versions
    """
    original_bullets = _collect_all_bullets(resume)

    if not original_bullets:
        logger.warning("No bullets found in resume experience — skipping optimization")
        return OptimizedBullets(
            original_bullets=[],
            rewritten_bullets=[]
        )

    # Cap at 10 bullets to keep prompt manageable
    bullets_to_optimize = original_bullets[:10]

    logger.info(f"Optimizing {len(bullets_to_optimize)} bullets for role: {jd_extracted.role_title}")

    prompt = BULLET_REWRITE_PROMPT.format(
        bullets="\n".join(f"- {b}" for b in bullets_to_optimize),
        keywords=", ".join(jd_extracted.keywords[:15]),
        role_title=jd_extracted.role_title
    )

    try:
        result = await call_llm_structured(prompt)
        rewritten = result.get("rewritten_bullets", bullets_to_optimize)
        logger.info(f"Bullets rewritten: {len(rewritten)} outputs")
    except Exception as e:
        logger.warning(f"Bullet optimization failed, returning originals: {e}")
        rewritten = bullets_to_optimize

    return OptimizedBullets(
        original_bullets=bullets_to_optimize,
        rewritten_bullets=rewritten
    )
