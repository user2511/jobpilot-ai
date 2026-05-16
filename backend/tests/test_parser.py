# backend/tests/test_parser.py
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_parse_resume_short_text():
    """Resume with too-short text should raise ValueError."""
    from services.resume_parser import parse_resume

    # Create a minimal fake PDF bytes (won't pass fitz, so mock pdf_parser)
    with patch("services.resume_parser.extract_text_from_pdf", return_value="too short"):
        with pytest.raises(ValueError, match="too short"):
            await parse_resume(b"fake pdf bytes")


@pytest.mark.asyncio
async def test_parse_resume_cache_hit():
    """Cache hit should skip LLM call."""
    from services.resume_parser import parse_resume

    cached_data = {
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "phone": None,
        "summary": "Engineer",
        "skills": ["Python", "FastAPI"],
        "experience": [],
        "education": [],
        "certifications": []
    }

    with patch("services.resume_parser.extract_text_from_pdf", return_value="a" * 200):
        with patch("services.resume_parser.get_cache", new_callable=AsyncMock, return_value=cached_data):
            with patch("services.resume_parser.call_llm_structured") as mock_llm:
                result = await parse_resume(b"fake bytes")
                mock_llm.assert_not_called()   # LLM should be skipped
                assert result.full_name == "Jane Doe"
