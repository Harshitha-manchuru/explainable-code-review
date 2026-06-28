# Explainable RAG-Based Code Review System

An explainable, citation-backed code review tool for Python programming
education. Submitted code is statically analyzed, matched against a
curated rule knowledge base via retrieval-augmented generation, explained
by an LLM grounded strictly in the retrieved rule text, and checked for
explanation faithfulness using an NLI entailment model.

See [`docs/architecture.md`](docs/architecture.md) for the full pipeline design.

## Tech stack

**Backend:** FastAPI, Pydantic, flake8, pylint, ChromaDB, sentence-transformers
(embeddings + CrossEncoder NLI), Gemini API

**Frontend:** React, Vite, Monaco Editor

## Project structure

```
explainable-code-review/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/                  (routes_submission.py, schemas.py)
│   │   ├── analysis/              (static_analyzer.py, flag_normalizer.py)
│   │   ├── retrieval/             (embed_rules.py, retriever.py)
│   │   ├── generation/            (llm_client.py, prompt_templates.py, explainer.py)
│   │   └── faithfulness/          (faithfulness_checker.py, metrics.py)
│   ├── knowledge_base/            (pep8_rules.json, google_style_excerpts.json, anti_patterns.json)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── public/index.html
│   ├── src/
│   │   ├── main.jsx, App.jsx
│   │   ├── components/            (CodeEditor.jsx, FeedbackPanel.jsx)
│   │   ├── api/client.js
│   │   └── styles/main.css
│   ├── package.json
│   └── vite.config.js
├── docs/architecture.md
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Local setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) A Gemini API key. Without one, the system runs in offline
  stub mode automatically — the full pipeline still works end-to-end.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set GEMINI_API_KEY if you have one (optional)

# Embed the knowledge base into ChromaDB (one-time; also runs lazily on first request)
python -m app.retrieval.embed_rules

uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`. Interactive API docs at
`http://localhost:8000/docs`.

### Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` and proxies `/api` requests to
the backend at `http://localhost:8000` (configured in `vite.config.js`).

### Verify it works

Open `http://localhost:5173`, paste or edit the default Python snippet
in the editor, and click **Analyze Code**. You should see flagged
lines, each expandable to show a grounded explanation, the retrieved
rule citation(s), and a faithfulness entailment score.

## Running with Docker

```bash
cp backend/.env.example backend/.env
# Edit backend/.env if you have a Gemini API key

docker-compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## Deployment

### Backend on Render

1. Push this repository to GitHub.
2. In the Render dashboard, create a **New Web Service** and connect
   the repository.
3. Configure:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add an environment variable `GEMINI_API_KEY` (optional — leave unset
   to run in stub mode).
5. Deploy. Note the public URL Render assigns
   (e.g. `https://your-service.onrender.com`).
6. In `app/config.py`, add your deployed frontend's origin to
   `ALLOWED_ORIGINS` (or set it dynamically via an environment variable)
   before redeploying, so CORS allows requests from the live frontend.

### Frontend on Vercel

1. In the Vercel dashboard, create a **New Project** and import the
   same repository.
2. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. Add an environment variable `VITE_API_BASE_URL` set to your Render
   backend URL (e.g. `https://your-service.onrender.com`).
4. Deploy. Vercel will give you a public URL
   (e.g. `https://your-project.vercel.app`).
5. Add that Vercel URL to `ALLOWED_ORIGINS` in the backend's
   `app/config.py` and redeploy the backend so CORS permits it.

## Notes on stub mode

If `GEMINI_API_KEY` is left blank, `app/config.py` sets `USE_LLM_STUB =
True` and `app/generation/llm_client.py` returns deterministic,
rule-grounded explanations without calling any external API. This is
intentional: it keeps the entire pipeline — including retrieval and
faithfulness checking — fully runnable and demonstrable without
network access or billing, which matters for offline grading or
demoing under time pressure.
