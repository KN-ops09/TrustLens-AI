TrustLens AI

AI-powered scam and fraud message detector built for Indian users.
TrustLens AI allows users to paste suspicious SMS, WhatsApp forwards, emails, job offers, or investment messages and receive a live, explainable risk analysis.

Built as a Vibe Coding project: a full-stack AI application, containerized with Docker, deployed on Render.

---

🔗 Project Links

GitHub Repository:
https://github.com/KN-ops09/TrustLens-AI

Live Demo:
https://trustlens-ai-2bbu.onrender.com

---

🚀 What it does

1. User enters a suspicious message through the web interface.

2. The backend extracts lightweight scam indicators such as:
   
   - Urgency words
   - OTP/KYC mentions
   - Suspicious links
   - Phone numbers
   - Scam-related keywords

3. These signals are checked against a lightweight community pattern store containing anonymized scam patterns. No original user messages are stored.

4. The message context is analyzed using the Groq API with Llama models through a structured AI prompt.

5. The AI generates:
   
   - Scam probability score
   - Scam category
   - Red flags
   - Simple explanation
   - Recommended safety action

6. The frontend displays the analysis with live reasoning updates, risk visualization, and warning indicators.

---

🛠️ Tech Stack

Frontend

- HTML
- CSS
- JavaScript
- Server-Sent Events (SSE) for live streaming responses

Backend

- Python
- FastAPI
- Groq API (Llama model)
- Groq Python SDK

Storage

- Local JSON-based community pattern store
- Stores only anonymized keywords, categories, and probability information

Containerization

- Docker
- Single container serving backend and frontend

Deployment

- Render (Free Tier)

---

📁 Project Structure

trustlens-ai/
│
├── backend/
│   ├── main.py                 # FastAPI backend and AI analysis logic
│   ├── requirements.txt
│   └── data/
│       └── patterns.json       # Anonymized scam pattern store
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── Dockerfile
├── .env.example
├── .dockerignore
├── .gitignore
└── README.md

---

💻 Run Locally

1. Clone the repository

git clone https://github.com/KN-ops09/TrustLens-AI.git

2. Configure environment variables

Create a ".env" file:

GROQ_API_KEY=your_groq_api_key

3. Install dependencies

cd backend
pip install -r requirements.txt

4. Start FastAPI server

uvicorn main:app --reload --port 8000

Open:

http://localhost:8000

---

🐳 Run Using Docker

Build the Docker image:

docker build -t trustlens-ai .

Run the container:

docker run -p 8000:8000 --env-file .env trustlens-ai

Open:

http://localhost:8000

---

☁️ Deployment

TrustLens AI is deployed using Render.

Deployment process:

1. Repository connected with GitHub.
2. Docker-based deployment configured.
3. Environment variable "GROQ_API_KEY" added securely.
4. Application deployed as a public web service.

Live application:

https://trustlens-ai-2bbu.onrender.com

---

🔒 Security Notes

- API keys are stored only as environment variables.
- No API key is exposed in frontend files.
- ".env" files are ignored using ".gitignore".
- User messages are not permanently stored.
- Community pattern storage contains only anonymized scam indicators.

---

🔮 Future Enhancements

- Replace keyword-based pattern matching with vector embeddings and advanced RAG.
- Add database storage for scalable community pattern management.
- Add multilingual scam detection for Indian regional languages.
- Add browser extension support for real-time scam detection.
- Add advanced fraud intelligence using larger AI models.

---

👩‍💻 Author

Karishma Narkhede
,Deepak Patil
,Prerana Patil

TrustLens AI — AI-powered Scam Detection System
