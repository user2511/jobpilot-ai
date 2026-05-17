# backend/services/jd_extractor.py
# Extracts structured information from a raw JD text using LLM.
# Caches by MD5 hash of JD content — same JD never re-processed.

import hashlib

from backend.utils.redis_cache import get_cache, set_cache
from backend.utils.scraper import scrape_jd_from_url
from backend.utils.logger import get_logger
from backend.services.llm_client import call_llm_structured
from backend.prompts.jd_extract import JD_EXTRACT_PROMPT
from backend.schemas.job import JDInput, JDExtracted

logger = get_logger(__name__)


async def extract_jd(payload: JDInput) -> tuple[str, JDExtracted]:
    """
    Full pipeline: JD URL or text → structured JDExtracted.

    Steps:
    1. If URL provided, scrape text first
    2. Hash JD text → check Redis cache
    3. Call LLM to extract structure
    4. Validate with Pydantic and cache

    Returns:
        Tuple of (raw_jd_text, JDExtracted)
    """
    # Step 1: Get raw JD text
    if payload.jd_url:
        logger.info(f"Scraping JD from URL: {payload.jd_url}")
        jd_text = scrape_jd_from_url(payload.jd_url)
    else:
        jd_text = payload.jd_text

    if not jd_text or len(jd_text.strip()) < 50:
        raise ValueError("Job description text is too short to analyze")

    # Step 2: Cache check
    jd_hash = hashlib.md5(jd_text.encode()).hexdigest()
    cache_key = f"jd:{jd_hash}"

    cached = await get_cache(cache_key)
    if cached:
        logger.info(f"JD extraction cache hit for hash {jd_hash[:8]}")
        return jd_text, JDExtracted(**cached)

    # Step 3: LLM extraction
    logger.info("Calling LLM to extract JD structure")
    prompt = JD_EXTRACT_PROMPT.format(jd_text=jd_text[:5000])  # cap at 5K chars
    extracted_dict = await call_llm_structured(prompt)

    # Step 4: Validate and cache
    extracted = JDExtracted(**extracted_dict)
    await set_cache(cache_key, extracted.model_dump(), ttl=86400)  # 24h cache

    logger.info(f"JD extracted: role={extracted.role_title}, "
                f"required_skills={len(extracted.required_skills)}")
    return jd_text, extracted
