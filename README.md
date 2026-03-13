# Clinic Summarizer

Clinic Summarizer is a small agent workflow that turns raw symptom descriptions into a short clinical summary, reviews the draft for quality, and shows the approved result in a simple web UI.

## What It Does

- Accepts symptom text in plain language
- Generates a concise clinical summary with an LLM
- Reviews the draft before approval
- Retries when the review step rejects the draft
- Preserves the input language in the final summary
- Streams status updates to the frontend

## Project Structure

- `main.py`: CLI entry point
- `server.py`: FastAPI backend with streaming endpoint
- `graph.py`: LangGraph workflow wiring
- `state.py`: shared graph state
- `nodes/generator.py`: summary generation step
- `nodes/critic.py`: quality review step
- `language_utils.py`: lightweight language detection helpers
- `frontend/`: React + Vite user interface

## Workflow

1. User enters symptoms
2. `Summary Writer` creates a short clinical draft
3. `Quality Checker` reviews language, tone, hallucination risk, and structure
4. If rejected, the draft is revised and checked again
5. If approved, the result is shown in the UI

## Tech Stack

- Python
- FastAPI
- LangGraph
- LiteLLM
- Groq
- React
- Vite
- Tailwind CSS
- Framer Motion

## Setup

### 1. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 2. Add environment variables

Create or update `.env`:

```env
GROQ_API_KEY=your_groq_api_key
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

## Run

### Backend

```bash
python server.py
```

The API runs on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm run dev
```

The UI runs on `http://localhost:5173` by default.

## CLI Mode

You can also test the workflow in the terminal:

```bash
python main.py
```

## Notes

- The final summary should stay in the same language as the input.
- The system is designed to summarize symptoms, not provide a definitive diagnosis.
- `.env` should not be committed with a real API key.

## Status

Current version includes:

- FastAPI streaming backend
- React frontend
- summary generation + review loop
- language consistency checks
- classic single-screen dashboard UI
