# backend/prompts/matcher.py

MATCH_PROMPT = """
You are an expert career coach and resume analyst.
Analyze how well this candidate's resume matches the job requirements.
Return ONLY valid JSON. No explanation, no markdown, no preamble.

Candidate Skills:
{candidate_skills}

Job Required Skills:
{required_skills}

Already Matched Skills:
{matched_skills}

Missing Skills:
{missing_skills}

Job Responsibilities:
{responsibilities}

Return this exact JSON structure:
{{
  "bonus_score": <integer 0-30, additional score beyond skill match>,
  "weak_sections": ["section or bullet that needs improvement"],
  "suggestions": [
    "specific actionable improvement suggestion 1",
    "specific actionable improvement suggestion 2"
  ]
}}
"""
