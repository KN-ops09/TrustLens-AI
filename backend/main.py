"""
TrustLens AI — backend
FastAPI server that:
  1. Serves the static frontend
  2. Accepts a suspicious message, streams a reasoning trace + verdict from Claude
  3. Keeps a lightweight "community" JSON store of anonymized scam patterns and
     feeds similar past patterns back into the prompt as context (Option A: RAG-lite)
"""

import os
import re
import json
import uuid
import time
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

APP_DIR = Path(__file__).parent

# Load environment variables from .env file
load_dotenv(APP_DIR / ".env")
DATA_FILE = APP_DIR / "data" / "patterns.json"
FRONTEND_DIR = APP_DIR.parent / "frontend"

# Configure Google API
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found")

MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

client = Groq(api_key=api_key)

app = FastAPI(title="TrustLens AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if not DATA_FILE.exists():
    DATA_FILE.write_text("[]", encoding="utf-8")

# ---------------------------------------------------------------------------
# Community pattern store (Option A — lightweight, no vector DB required)
# ---------------------------------------------------------------------------

TRIGGER_WORDS = [
    "urgent", "otp", "kyc", "prize", "lottery", "winner", "loan", "investment",
    "guaranteed", "double your money", "click the link", "verify now", "blocked",
    "account suspended", "limited time", "act now", "refund", "cashback",
    "job offer", "work from home", "crypto", "bitcoin", "part time job",
    "aadhar", "pan card", "bank account", "upi pin", "share otp",
]

URL_RE = re.compile(r"https?://\S+|www\.\S+")
PHONE_RE = re.compile(r"\b\d{10}\b")


def extract_keywords(text: str) -> List[str]:
    lower = text.lower()
    found = [w for w in TRIGGER_WORDS if w in lower]
    if URL_RE.search(text):
        found.append("contains_url")
    if PHONE_RE.search(text):
        found.append("contains_phone_number")
    return sorted(set(found))


def load_patterns() -> List[Dict]:
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_pattern(entry: Dict):
    patterns = load_patterns()
    patterns.append(entry)
    # keep the store bounded
    patterns = patterns[-500:]
    DATA_FILE.write_text(json.dumps(patterns, indent=2), encoding="utf-8")


def find_similar(keywords: List[str], top_k: int = 3) -> List[Dict]:
    if not keywords:
        return []
    scored = []
    for p in load_patterns():
        overlap = len(set(keywords) & set(p.get("keywords", [])))
        if overlap > 0:
            scored.append((overlap, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_k]]


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are TrustLens AI, a fraud-and-scam detection assistant built for \
Indian users (SMS, WhatsApp, email, job offers, investment schemes).

For every message you receive, respond in Hinglish-friendly plain language and follow this \
exact two-part structure:

PART 1 — Stream a short reasoning trace as plain lines (no markdown headers), each on its own \
line, e.g.:
Checking sender pattern...
Scanning for urgency cues...
Cross-referencing known scam patterns...
Evaluating links and payment requests...

Keep this to 4-6 short lines, written like live progress narration.

PART 2 — After the reasoning trace, output ONE fenced json block and nothing else after it, \
with exactly this shape:
```json
{
  "scam_probability": <integer 0-100>,
  "category": "<short category e.g. 'Loan Scam', 'Job Scam', 'Phishing', 'Not a Scam'>",
  "red_flags": ["<flag 1>", "<flag 2>", "..."],
  "explanation": "<2-3 sentence plain-language explanation, Hinglish-friendly>",
  "recommended_action": "<one short actionable recommendation>"
}
```
Be calibrated: if a message is genuinely benign, return a low scam_probability and say so \
clearly. Never invent evidence that is not in the message."""


def build_user_prompt(message: str, similar: List[Dict]) -> str:
    context = ""
    if similar:
        lines = [
            f"- Category: {p['category']}, similarity keywords overlap, seen {p.get('count', 1)} time(s) before"
            for p in similar
        ]
        context = (
            "Community pattern context (anonymized, from previously analyzed messages):\n"
            + "\n".join(lines)
            + "\n\n"
        )
    return f"{context}Analyze this message:\n\n{message}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    message: str


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    message = req.message.strip()
    keywords = extract_keywords(message)
    similar = find_similar(keywords)
    user_prompt = build_user_prompt(message, similar)

    def event_stream():
        full_text = ""
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            stream=True,
        )

        for chunk in response:
            text = chunk.choices[0].delta.content or ""
            if text:
                full_text += text
                yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"

        # Persist an anonymized pattern entry (best-effort; never blocks the response)
        try:
            match = re.search(r"```json\s*(\{.*?\})\s*```", full_text, re.DOTALL)
            if match and keywords:
                parsed = json.loads(match.group(1))
                save_pattern({
                    "id": str(uuid.uuid4()),
                    "timestamp": time.time(),
                    "category": parsed.get("category", "Unknown"),
                    "keywords": keywords,
                    "scam_probability": parsed.get("scam_probability"),
                })
        except Exception:
            pass

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/health")
async def health():
    return {"status": "ok", "patterns_stored": len(load_patterns())}


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))
