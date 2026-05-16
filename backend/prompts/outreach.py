# backend/prompts/outreach.py

OUTREACH_PROMPT = """
You are an expert at writing concise, effective recruiter outreach messages.
Write a short LinkedIn/email cold outreach message.

STRICT RULES:
- Maximum 100 words for message body
- Friendly but professional tone
- Do not beg or oversell
- Mention 1 specific relevant skill or achievement
- End with a simple ask (15-min call or application consideration)
- Subject line must be under 10 words

Candidate Name: {full_name}
Candidate Top Skills: {top_skills}
Most Relevant Experience: {top_experience}

Target Role: {role_title}
Company: {company_name}

Return ONLY valid JSON. No explanation, no markdown, no preamble:
{{
  "subject_line": "concise subject line here",
  "message_body": "full outreach message here"
}}
"""
