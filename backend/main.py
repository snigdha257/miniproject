import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

dotenv_path = os.path.join(BACKEND_DIR, ".env")
load_dotenv(dotenv_path)

from routes.auth import router as auth_router
from routes.documents import router as documents_router

app = FastAPI(
    title="Context-Aware Sensitive Data Masking API",
    description="AI-Powered Enterprise Document Privacy Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)


@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "miniproject-api",
        "version": "0.1.0",
    }
