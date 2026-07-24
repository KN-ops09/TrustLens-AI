# TrustLens AI

AI-powered scam / fraud message detector built for Indian users — paste any suspicious
SMS, WhatsApp forward, email, job offer, or investment pitch and get a live-streamed,
explainable risk analysis.

Built as a **Vibe Coding** project: full-stack app, containerized, deployed on AWS.

---

## What it does

1. User pastes a message into the UI.
2. Backend extracts lightweight signal keywords (urgency words, OTP/KYC mentions, links,
   phone numbers) and checks them against a small **community pattern store** — a
   local JSON file of anonymized keyword/category records from previously analyzed
   messages (no raw message text is ever stored).
3. That context plus the message is sent to Claude with a structured system prompt.
4. Claude streams back a short reasoning trace ("Checking urgency cues...",
   "Cross-referencing known scam patterns...") followed by a fenced JSON verdict:
   scam probability, category, red flags, plain-language explanation, and a
   recommended action.
5. The frontend renders the reasoning trace live (Server-Sent Events) and then
   animates a risk gauge + red-flag chips once the verdict JSON arrives.

## Tech stack

- **Frontend:** vanilla HTML/CSS/JS, Server-Sent Events for streaming, no build step
- **Backend:** Python, FastAPI, Google `google-generativeai` SDK (Gemini, free tier, streaming)
- **Storage:** flat JSON file for the anonymized community pattern store (Option A —
  lightweight, no external DB required; upgradeable to a vector-based RAG store later)
- **Container:** single Dockerfile, one process serves both API and static frontend
- **Deployment target:** AWS App Runner or Elastic Beanstalk (free tier)

## Project structure

```
trustlens-ai/
├── backend/
│   ├── main.py            # FastAPI app: streaming endpoint + pattern store
│   ├── requirements.txt
│   └── data/
│       └── patterns.json  # anonymized keyword/category store (auto-created)
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── Dockerfile
├── .env.example
├── .dockerignore
├── .gitignore
└── README.md
```

## Run locally

```bash
cd trustlens-ai
cp .env.example .env
# edit .env and paste your GEMINI_API_KEY (get one free at https://aistudio.google.com/apikey)

cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000

## Run with Docker

```bash
cd trustlens-ai
docker build -t trustlens-ai .
docker run -p 8000:8000 --env-file .env trustlens-ai
```

Open http://localhost:8000

## Deploying to AWS

### Option A — AWS App Runner (recommended, simplest)

1. Push this repo to GitHub (make sure `.env` is **not** committed — it's already in
   `.gitignore`).
2. In the AWS Console, open **App Runner → Create service**.
3. Source: **Source code repository** → connect your GitHub repo, or
   **Container registry** if you push the image to Amazon ECR first:
   ```bash
   aws ecr create-repository --repository-name trustlens-ai
   aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
   docker tag trustlens-ai:latest <account>.dkr.ecr.<region>.amazonaws.com/trustlens-ai:latest
   docker push <account>.dkr.ecr.<region>.amazonaws.com/trustlens-ai:latest
   ```
4. Set the port to `8000`.
5. Under **Environment variables**, add `GEMINI_API_KEY` (and optionally
   `GEMINI_MODEL`) — never hardcode the key in the image or repo.
6. Deploy. App Runner gives you a public HTTPS URL — paste that into your Concept
   Note and Project Report.
7. Set up an **AWS Budget alert** (Billing → Budgets) so free-tier usage doesn't
   surprise you.

### Option B — Elastic Beanstalk (Docker platform)

1. `eb init -p docker trustlens-ai`
2. `eb create trustlens-env`
3. In the EB console, set `GEMINI_API_KEY` under
   **Configuration → Software → Environment properties**.
4. `eb deploy`
5. EB gives you a public HTTPS URL once you attach a certificate / use the default
   EB domain.

## Security notes

- The API key lives only in the environment (`.env` locally, platform environment
  variables in AWS) — it's never referenced from `frontend/script.js` or committed
  to version control.
- The community pattern store persists only extracted keywords, a category label,
  and a probability score — never the original message text.

## Possible extensions (documented as future scope)

- Swap the keyword-overlap pattern store for real embeddings + a vector index
  (proper RAG) for semantic similarity instead of keyword overlap.
- Add a lightweight regex/rule-based pre-filter as a fast first pass before the
  LLM call, to cut latency and cost on obviously benign messages.
- Persist the community store in a managed DB (DynamoDB) instead of a flat file
  once deployed with more than one instance, since local JSON won't be shared
  across App Runner replicas.
