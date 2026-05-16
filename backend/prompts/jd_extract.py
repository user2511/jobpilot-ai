# backend/prompts/jd_extract.py

JD_EXTRACT_PROMPT = """
You are an expert job description analyzer.
Extract structured information from the job description below.
Return ONLY valid JSON. No explanation, no markdown, no preamble.

Job Description:
{jd_text}

Return this exact JSON structure:
{{
  "role_title": "exact job title from the JD",
  "company_name": "company name or null",
  "required_skills": ["skill1", "skill2", "skill3"],
  "preferred_skills": ["skill1", "skill2"],
  "responsibilities": ["responsibility 1", "responsibility 2"],
  "experience_years": "e.g. 3-5 years or null if not mentioned",
  "keywords": ["ats_keyword1", "ats_keyword2", "ats_keyword3"]
}}
"""
