# backend/prompts/resume_structure.py

RESUME_STRUCTURE_PROMPT = """
You are an expert resume parser.
Extract structured information from the resume text below.
Return ONLY valid JSON. No explanation, no markdown, no preamble.

Resume Text:
{resume_text}

Return this exact JSON structure:
{{
  "full_name": "candidate full name",
  "email": "email address",
  "phone": "phone number or null",
  "summary": "professional summary paragraph or null",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {{
      "title": "job title",
      "company": "company name",
      "duration": "date range e.g. Jan 2023 - Present",
      "bullets": ["achievement or responsibility 1", "achievement 2"]
    }}
  ],
  "education": [
    {{
      "degree": "degree name",
      "institution": "university or college name",
      "year": "graduation year or null"
    }}
  ],
  "certifications": ["cert1", "cert2"]
}}
"""
