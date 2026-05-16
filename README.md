# JobPilot 🚀

AI-powered job application optimizer. Upload your resume, paste a job description, get:
- Fit score with skill gap analysis
- AI-rewritten resume bullets
- Tailored cover letter
- Recruiter outreach message

## Stack
- **Backend**: FastAPI + SQLite + Redis
- **AI**: Ollama (Phi-3 Mini local) 
- **Frontend**: Streamlit
- **Deployment**: Docker / Render / Railway

---

## Local Setup (without Docker)

### 1. Install Ollama and pull model
```bash
# Install from https://ollama.ai
ollama pull phi3:mini
ollama serve   # runs on localhost:11434
```

### 2. Start Redis
```bash
docker run -d -p 6379:6379 redis:7-alpine
# or: brew install redis && redis-server
```

### 3. Backend
```bash
cd backend
pip install -r ../requirements.txt
cp ../.env.example .env
uvicorn main:app --reload --port 8000
```

### 4. Frontend
```bash
cd frontend
API_BASE_URL=http://localhost:8000 streamlit run app.py
```

Open http://localhost:8501

---

## Docker Setup (recommended)

```bash
# Copy env file
cp .env.example .env

# Build and run everything
docker-compose up --build

# App: http://localhost:8501
# API docs: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/resume/upload` | Upload PDF resume |
| GET | `/resume/{session_id}` | Get parsed resume |
| POST | `/jobs/analyze` | Full analysis pipeline |
| GET | `/jobs/history/{session_id}` | Past analyses |
| GET | `/outputs/{analysis_id}` | Get saved output |
| GET | `/health` | Health check |

---

## Project Structure

```
jobpilot/
├── backend/
│   ├── main.py          # FastAPI entry point
│   ├── config.py        # Settings
│   ├── database.py      # SQLite setup
│   ├── routers/         # HTTP routes (thin layer)
│   ├── services/        # Business logic + LLM calls
│   ├── models/          # ORM models
│   ├── schemas/         # Pydantic schemas
│   ├── prompts/         # LLM prompt templates
│   └── utils/           # PDF parser, scraper, cache, logger
└── frontend/
    └── app.py           # Streamlit UI
```

---

## Deployment on Render

1. Push to GitHub
2. Create new Web Service on Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add Redis instance from Render dashboard
6. Set env vars from `.env.example`
7. Note: Ollama needs separate hosting — use `ngrok` locally for demo or switch `llm_client.py` to use Groq API

---

## Swapping to Groq/OpenAI (for cloud deployment)

Change only `backend/services/llm_client.py`:

```python
# Replace _call_ollama with:
async def _call_openai(prompt: str) -> str:
    import openai
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content
```

Everything else stays identical.
