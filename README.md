# Canada Benefits AI Assistant

An AI-powered conversational agent that helps users discover which Canadian federal benefits they may qualify for. It guides users through a dynamic, multiple-choice survey, evaluates eligibility using a rules-based engine, and generates detailed, context-aware explanations using a Retrieval-Augmented Generation (RAG) pipeline powered by the Groq API.

## Features

- **Dynamic eligibility survey** — multiple-choice questions with an "Other" option resolved dynamically via LLM extraction, covering employment, marital status, province, residency status, income, disability, and more.
- **Rules-based eligibility engine** — deterministic, explainable eligibility checks against real federal programs (Employment Insurance, Canada Child Benefit, GST/HST Credit, Disability Tax Credit, and others).
- **Retrieval-Augmented Generation (RAG)** — benefit information scraped from Canada.ca, embedded with sentence-transformers, and retrieved via ChromaDB to ground the AI's answers in real government data.
- **Context-aware conversation** — the assistant remembers prior turns in the conversation and avoids repeating the same summary, distinguishing a first eligibility summary from natural follow-up questions.
- **Automatic multilingual replies** — responds in whichever language the user writes in (English, Arabic, French, etc.), without any language switch required.
- **Re-evaluation on life changes** — detects reported changes in circumstances (e.g. "I lost my job") and automatically re-runs eligibility, highlighting what changed.
- **Suggested follow-up questions** — after each answer, the assistant proposes relevant next questions the user can tap instead of typing.
- **Secure authentication** — JWT-based sessions with bcrypt password hashing; a user's identity is always derived from their token, never from client-supplied input.
- **Conversation history & profile editing** — users can review past conversations and update any previously answered survey field at any time.
- **PDF export** — users can download a cleaned, formatted PDF of their eligibility summary.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Frontend | Streamlit |
| Database | SQLite + SQLAlchemy |
| LLM | Groq API |
| Vector search (RAG) | ChromaDB + sentence-transformers |
| Authentication | JWT (python-jose) + bcrypt |
| Data collection | requests + BeautifulSoup |
| PDF generation | fpdf2 |

## Project Structure

```
canada-benefits-v2/
├── scraper.py                  # Scrapes benefit data from canada.ca
├── requirements.txt
├── .env.example                 # Template for required environment variables
├── backend/
│   ├── config.py                 # Centralized settings (Groq + JWT secrets)
│   ├── api.py                    # FastAPI routes
│   ├── agent.py                  # Core conversational agent orchestration
│   ├── pdf_export.py             # PDF summary generation
│   ├── database/                 # SQLAlchemy models and session setup
│   ├── vector_db/                # ChromaDB ingestion and semantic search
│   ├── eligibility/               # Rules engine and user profile schema
│   ├── memory/                   # Conversation memory, questions, change detection
│   ├── llm/                      # Groq client and LLM-based extraction
│   └── auth/                     # JWT security, schemas, dependencies
├── frontend/
│   └── app.py                    # Streamlit UI
└── data/
    └── benefits.json             # Output of scraper.py
```

## Setup & Running Locally

### 1. Clone and install dependencies
```bash
git clone https://github.com/yazanali2001/Canada-Benefits-AI-Agent
.git
cd YOUR_REPO_NAME
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure environment variables
Copy `.env.example` to `.env` and fill in your own values:
```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
SECRET_KEY=a_long_random_string
```
Get a free Groq API key at [console.groq.com](https://console.groq.com).

### 3. Collect benefits data
```bash
python scraper.py
```

### 4. Initialize the database
```bash
python -m backend.database.init_db
```

### 5. Build the RAG vector index
```bash
python -m backend.vector_db.ingest
```

### 6. Run the backend
```bash
uvicorn backend.api:app --reload
```

### 7. Run the frontend (in a separate terminal)
```bash
streamlit run frontend/app.py
```

The app will open at `http://localhost:8501`.

## Disclaimer

This tool provides AI-generated, informational guidance only. It is **not** an official eligibility determination and is not affiliated with the Government of Canada. Always verify eligibility and program details on the official [Canada.ca](https://www.canada.ca) website before applying for any benefit.

## Known Limitations

- The scraper currently collects data from a limited set of general benefit category pages rather than deep, program-specific pages.
- No automated test suite yet.
- No API rate limiting yet — intended for personal/demo use.
