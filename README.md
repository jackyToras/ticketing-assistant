# Support Ticket Decision Assistant

An evidence-backed support-ticket decision assistant.

## Features

- FastAPI REST API with registration, login, JWT protection, ticket creation, and ticket history.
- SQLite persistence for users, tickets, and structured decisions.
- Password hashing with bcrypt; users can access only their own tickets.
- Local RAG over the supplied Markdown policies using Gemini embeddings and cosine similarity.
- Gemini structured output validated by Pydantic before persistence.
- Streamlit login, new-decision, and history interface that communicates only through HTTP.
- Pytest authorization/persistence tests and a supplied-case evaluation runner.

## Tech Stack

**Backend:**
- FastAPI (REST API)
- SQLAlchemy + SQLite (ORM + database)
- Pydantic (schema validation)
- PyJWT + bcrypt (authentication & password hashing)

**RAG Pipeline:**
- Google Gemini API (embeddings + LLM)
- NumPy (cosine similarity search)
- JSON file caching (policy embeddings)

**Frontend:**
- Streamlit (user interface)

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` and a strong `JWT_SECRET` in `.env`. Do not commit it.

## Run

Start the API in one terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api:app --reload
```

Start the interface in a second terminal:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open `http://localhost:8501`. The backend API documentation is at `http://127.0.0.1:8000/docs`.

## Test and evaluate

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -X utf8 evaluate.py
```

The evaluation runner sends the synthetic cases and relevant supplied policy evidence to Gemini, then reports expected-versus-actual actions and accuracy.
