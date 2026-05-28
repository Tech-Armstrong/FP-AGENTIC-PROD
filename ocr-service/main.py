"""
Local OCR policy microservice — POST /extract returns ExtractedPolicy JSON.

Run:  cd ocr-service && pip install -r requirements.txt && python main.py
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env BEFORE any module reads os.environ (processor imports must come after).
_OCR_DIR = Path(__file__).resolve().parent
load_dotenv(_OCR_DIR / ".env")
load_dotenv(_OCR_DIR.parent / ".env")  # repo root fallback

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from processor import log_config_status, process_pdf

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ocr-service")

MAX_BYTES = int(os.getenv("OCR_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
PORT = int(os.getenv("OCR_SERVICE_PORT", "8010"))

app = FastAPI(title="Policy OCR Service", version="1.0.0")


@app.on_event("startup")
def _startup_log_config():
    log_config_status()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds {MAX_BYTES // (1024 * 1024)} MB limit",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        policy = process_pdf(data, file.filename)
        return policy.compact_dump()
    except RuntimeError as exc:
        log.exception("OCR processing failed")
        return JSONResponse(status_code=503, content={"detail": str(exc)})
    except Exception as exc:
        log.exception("Unexpected OCR error")
        return JSONResponse(status_code=500, content={"detail": str(exc)})


if __name__ == "__main__":
    log_config_status()
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
