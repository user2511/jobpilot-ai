# backend/tests/test_matcher.py
import pytest
from unittest.mock import patch, AsyncMock
from schemas.job import JDExtracted


@pytest.mark.asyncio
async def test_compute_match_perfect_score():
    """All required skills present should give high base score."""
    from services.matcher import compute_match

    resume_skills = ["Python", "FastAPI", "Docker"]
    jd = JDExtracted(
        role_title="Backend Engineer",
        required_skills=["Python", "FastAPI", "Docker"],
        keywords=["python", "api"]
    )

    llm_response = {"bonus_score": 10, "weak_sections": [], "suggestions": []}
    with patch("services.matcher.call_llm_structured", new_callable=AsyncMock, return_value=llm_response):
        result = await compute_match(resume_skills, jd)
        assert result.fit_score >= 70
        assert len(result.missing_skills) == 0


@pytest.mark.asyncio
async def test_compute_match_missing_skills():
    """Missing skills should appear in result."""
    from services.matcher import compute_match

    resume_skills = ["Python"]
    jd = JDExtracted(
        role_title="ML Engineer",
        required_skills=["Python", "TensorFlow", "Kubernetes"],
        keywords=[]
    )

    llm_response = {"bonus_score": 5, "weak_sections": [], "suggestions": ["Add Kubernetes"]}
    with patch("services.matcher.call_llm_structured", new_callable=AsyncMock, return_value=llm_response):
        result = await compute_match(resume_skills, jd)
        assert "TensorFlow" in result.missing_skills
        assert "Kubernetes" in result.missing_skills
