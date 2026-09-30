# Meeting Helper

Meeting Helper is a real-time meeting workspace built with LiveKit, Next.js, and FastAPI. It captures browser speech transcripts, produces rolling summaries during a meeting, creates a final report with action items and decisions, and answers follow-up questions from the meeting transcript.

## Features

- Create a meeting and invite participants by email.
- Join a LiveKit video room.
- Capture speech transcripts in the browser.
- Generate live timeline summaries every two minutes.
- Produce a final summary with action items and key decisions.
- Search the meeting transcript semantically and ask transcript-grounded questions after the meeting.
- Email invitations and the final meeting summary when SMTP credentials are configured.

## Architecture

| Area | Technology | Responsibility |
| --- | --- | --- |
| Frontend | Next.js, React, LiveKit Components | Meeting creation, video room, transcript capture, summaries, and Q&A |
| Backend | FastAPI, SQLModel, SQLite | Meeting APIs, transcript storage, summary scheduling, and LiveKit tokens |
| AI | Groq API with Llama 3.3 70B | Live summaries, final reports, and answers |
| Retrieval | Sentence Transformers and FAISS | Local transcript embeddings and semantic search |

## Prerequisites

- Node.js 18 or later
- pnpm 10 or later
- Python 3.10 or later
- A LiveKit project with an API key and secret
- A Groq API key for AI-generated summaries and answers (optional; basic local fallbacks are used without one)

## Setup

### 1. Configure the backend

Create a virtual environment and install the Python dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy the backend example configuration, then fill in the required LiveKit credentials:

```powershell
Copy-Item .env.example .env
```

```env
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-livekit-server
GROQ_API_KEY=your_groq_api_key
```

`GROQ_API_KEY` is optional. Without it, the backend uses simple local fallback summaries and answers. Email delivery is also optional; add these values when you want invitations and final summaries sent by email:

```env
SMTP_USER=sender@example.com
SMTP_PASS=your_smtp_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
```

Start the API from the `backend` directory:

```powershell
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`, with interactive documentation at `http://localhost:8000/docs`.

### 2. Configure the frontend

In a second terminal, install the frontend dependencies and configure the backend URL:

```powershell
cd frontend\livekit-ui
pnpm install
```

Copy the frontend example configuration. `BACKEND_API_TOKEN` must match the backend value in hosted environments; it is intentionally server-only.

```powershell
Copy-Item .env.example .env.local
```

```env
BACKEND_API_URL=http://localhost:8000
BACKEND_API_TOKEN=replace_with_the_same_backend_token
```

Start the frontend:

```powershell
pnpm dev
```

Open `http://localhost:3000` in a browser. Chrome is recommended because browser transcription relies on the Web Speech API and requires microphone permission.

## Using the App

1. Enter a meeting title and host email, then select **Create**.
2. Add comma-separated participant email addresses and select **Send Invites** if email is configured.
3. Select **Start Meeting** to enter the LiveKit room.
4. Allow microphone access so speech can be transcribed.
5. Review live summaries as the meeting progresses.
6. End the meeting to generate the final summary, action items, and decisions.
7. Use the Q&A panel to ask questions about the indexed meeting transcript.

## Available Commands

### Backend

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
pytest
```

### Frontend

```powershell
cd frontend\livekit-ui
pnpm dev
pnpm build
pnpm test
pnpm format:check
```

## Data and Privacy Notes

- The application stores SQLite data and FAISS embeddings under `backend/data/`; these files are generated locally and ignored by Git.
- Transcript embeddings use the local `all-MiniLM-L6-v2` model. The first indexing request downloads the model if it is not already cached.
- When `GROQ_API_KEY` is configured, transcript content is sent to Groq for summary and answer generation.
- Configure `FRONTEND_ORIGINS`, `FRONTEND_URL`, and `BACKEND_API_TOKEN` before deploying. The frontend uses a server-side proxy, so the API token is not exposed to browsers.

## Quality Checks

GitHub Actions runs backend API tests and frontend tests/builds on every push and pull request. Run the same checks locally with `pytest` from `backend` and `pnpm test && pnpm build` from `frontend/livekit-ui`.

## License

This project is licensed under the [MIT License](LICENSE).
