# backend/services/llm_client.py
# Single entry point for ALL LLM calls.
# Swap Ollama for OpenAI/Groq here — nothing else changes.

import hashlib
import json
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings
from utils.logger import get_logger
from utils.redis_cache import get_cache, set_cache

logger = get_logger(__name__)


def _hash_prompt(prompt: str) -> str:
    """MD5 hash of prompt text — used as cache key."""
    return hashlib.md5(prompt.encode()).hexdigest()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True
)
async def _call_ollama(prompt: str) -> str:
    """
    Raw HTTP call to Ollama API.
    Retries up to 3 times on HTTP errors with exponential backoff.
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        logger.info(f"Calling Ollama model={settings.ollama_model}")
        response = await client.post(
            f"{settings.ollama_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "format": "json",       # force JSON output from Ollama
                "options": {
                    "temperature": 0.1,  # low temp for consistent structured output
                    "num_predict": 2048
                }
            }
        )
        response.raise_for_status()
        return response.json()["response"]


async def call_llm(prompt: str, use_cache: bool = True) -> str:
    """
    Call LLM with optional Redis caching.
    Returns raw string response.

    Args:
        prompt: Full prompt string
        use_cache: Whether to check/store Redis cache (default True)

    Returns:
        Raw LLM response string
    """
    cache_key = f"llm:{_hash_prompt(prompt)}"

    # Check cache first
    if use_cache:
        cached = await get_cache(cache_key)
        if cached and "response" in cached:
            logger.info("LLM response served from cache")
            return cached["response"]

    # Call Ollama
    raw_response = await _call_ollama(prompt)
    logger.info(f"LLM response received: {len(raw_response)} chars")

    # Cache the result
    if use_cache:
        await set_cache(cache_key, {"response": raw_response}, ttl=3600)

    return raw_response


async def call_llm_structured(prompt: str, use_cache: bool = True) -> dict:
    """
    Call LLM and parse response as JSON dict.
    Always validates that response is parseable JSON.

    Args:
        prompt: Full prompt string
        use_cache: Whether to use Redis cache

    Returns:
        Parsed dict from LLM JSON response

    Raises:
        ValueError: If LLM returns non-JSON or malformed JSON
    """
    raw = await call_llm(prompt, use_cache=use_cache)

    # Strip common LLM artifacts before parsing
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"LLM non-JSON response (first 300 chars): {cleaned[:300]}")
        raise ValueError(f"LLM returned invalid JSON: {e}")
