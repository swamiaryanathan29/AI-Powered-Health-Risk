"""
FastAPI application entry point.
"""
import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import (
    factor_router,
    parse_router,
    pipeline_router,
    recommendation_router,
    risk_router,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Health Risk Profiler API starting up …")
    yield
    logger.info("🛑 Health Risk Profiler API shutting down …")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI-Powered Health Risk Profiler",
    description=(
        "Analyzes lifestyle survey responses (text or scanned images) and generates "
        "a structured health risk profile.\n\n"
        "**Disclaimer**: This service is for informational / lifestyle-risk purposes only "
        "and does **not** constitute medical advice or diagnosis."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(parse_router.router)
app.include_router(factor_router.router)
app.include_router(risk_router.router)
app.include_router(recommendation_router.router)
app.include_router(pipeline_router.router)


# ── Root health check ─────────────────────────────────────────────────────────
@app.get("/", tags=["Health"], summary="Service health check")
async def root():
    return {
        "service": "AI-Powered Health Risk Profiler",
        "status": "ok",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health():
    return {"status": "ok"}


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
