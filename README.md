# miniproject — Context-Aware Sensitive Data Masking Platform

> **AI-Powered Enterprise Document Privacy Platform**

---

## Project Pitch

miniproject is an AI-powered enterprise document privacy platform that automatically detects and masks sensitive information—such as names, email addresses, phone numbers, financial identifiers, and medical data—inside uploaded documents (PDF, DOCX, plain text) before they are stored or shared. Unlike blunt, keyword-list approaches, the platform uses spaCy NLP combined with context-aware regex rules to understand *where* and *why* data is sensitive, enabling granular, policy-driven masking that keeps documents useful while eliminating privacy risk. Masked values are symmetrically encrypted with Fernet so authorized users can reversibly unmask them, giving enterprises both compliance confidence and operational flexibility.

---

## Architecture

```
miniproject/
├── frontend/          # React + Vite + Tailwind CSS SPA
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/  # Axios API clients
│   │   └── main.jsx
│   └── vite.config.js # /api proxy → http://localhost:8000
│
├── backend/           # FastAPI (Python)
│   ├── routes/        # Route handlers (auth, documents, masking)
│   ├── services/      # Business logic (NLP, masking, encryption)
│   ├── models/        # Pydantic schemas + MongoDB document models
│   ├── utils/         # Helpers (JWT, hashing, file parsing)
│   ├── main.py        # FastAPI app entry-point
│   ├── requirements.txt
│   └── .env.example   # Config template (no real secrets)
│
├── database/
│   └── connection.py  # MongoDB client (reads MONGO_URI from env)
│
└── docs/              # Architecture diagrams, API specs
```

**Data flow:**
1. User uploads a document via the React SPA.
2. Frontend POSTs to `/api/documents/upload`.
3. FastAPI parses the file (pdfplumber / python-docx), runs spaCy NER + regex rules.
4. Detected sensitive spans are encrypted with Fernet and replaced with masked tokens.
5. Masked document + encryption metadata are stored in MongoDB.
6. Authorised users can request un-masking; the server decrypts and returns the original span.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, React Router v6, Axios, Lucide React |
| Backend | FastAPI 0.111, Uvicorn, Python 3.11+ |
| NLP / Detection | spaCy `en_core_web_sm`, Regex rule engine |
| Encryption | `cryptography` (Fernet symmetric encryption) |
| Auth | python-jose (JWT), passlib (bcrypt) |
| Database | MongoDB Atlas via pymongo |
| File parsing | pdfplumber (PDF), python-docx (DOCX) |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A MongoDB Atlas cluster (free tier works fine)

---

### 1. Clone / open the project

```powershell
# Set the project root as your working directory
cd miniproject
```

---

### 2. Backend

```powershell
cd backend

# Create and activate the virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install all dependencies (pinned versions)
pip install -r requirements.txt

# Download the spaCy English model
python -m spacy download en_core_web_sm

# Copy and fill in environment variables
copy .env.example .env
# Edit .env — add your MONGO_URI, generate a JWT_SECRET, generate a FERNET_KEY

# Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Verify backend:** `curl http://localhost:8000/` should return:
```json
{"status":"ok","service":"miniproject-api","version":"0.1.0"}
```

---

### 3. Frontend

```powershell
cd frontend

# Install dependencies
npm install

# Start the Vite dev server
npm run dev
```

**Verify frontend:** Open [http://localhost:5173](http://localhost:5173) in your browser.

All `/api/...` calls from the frontend are automatically proxied to `http://localhost:8000` via the Vite dev server config — no CORS issues, no hardcoded backend URL.

---

### 4. Database

Populate `backend/.env` with your MongoDB Atlas URI:

```env
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/miniproject?retryWrites=true&w=majority
```

The `database/connection.py` module will ping Atlas on startup and print `[DB] MongoDB connection established successfully.` — or exit with a clear error if the URI is wrong or missing.

---

## Environment Variables Reference

| Variable | Description |
|----------|-------------|
| `MONGO_URI` | Full MongoDB Atlas connection string |
| `JWT_SECRET` | Long random string for signing JWTs |
| `JWT_ALGORITHM` | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime (default 60) |
| `FERNET_KEY` | Fernet key for masking encryption (generate with Python snippet in `.env.example`) |
| `APP_ENV` | `development` or `production` |

---

## Development Commands

```powershell
# Backend (from backend/)
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload

# Frontend (from frontend/)
npm run dev

# Linting / formatting (future)
# ruff check .
# npm run lint
```

---

## Roadmap

- [ ] Document upload & text extraction (PDF, DOCX, TXT)
- [ ] NER-based entity detection (spaCy)
- [ ] Regex rule engine for PII patterns (SSN, credit cards, emails, phones)
- [ ] Fernet encryption + masked token storage
- [ ] JWT authentication (register / login)
- [ ] Document management dashboard (React)
- [ ] Role-based un-masking with audit log
- [ ] Export masked document as PDF/DOCX
