# -*- coding: utf-8 -*-
"""
CryptoSignal AI v6.0 - Modular Architecture
============================================

Klasör Yapısı:
├── main.py              # Bu dosya - Ana FastAPI app
├── config.py            # Konfigürasyon ve sabitler
├── database.py          # Veritabanı bağlantısı ve CRUD
├── auth.py              # JWT authentication
├── models.py            # Pydantic modelleri
├── dependencies.py      # FastAPI dependencies
│
├── routers/             # API endpoint'leri
│   ├── auth.py         # /api/login, /api/register
│   ├── portfolio.py    # /api/portfolio
│   ├── signals.py      # /api/signals
│   ├── news.py         # /api/news
│   ├── analysis.py     # /api/analyze, /api/digest, /api/prices
│   ├── admin.py        # /api/admin/*
│   ├── ai_stats.py     # /api/ai/*
│   └── ai_summary.py   # /api/ai-summary/*
│
├── services/            # İş mantığı (LLM, analiz vs.)
└── utils/               # Yardımcı fonksiyonlar
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Config
from config import APP_NAME, APP_VERSION

# Database initialization
from database import init_db

# Routers
from routers import (
    auth_router,
    portfolio_router,
    signals_router,
    news_router,
    analysis_router,
    admin_router,
    ai_stats_router,
    ai_summary_router,
    websocket_router
)

# =============================================================================
# APP INITIALIZATION
# =============================================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-Powered Cryptocurrency Analysis Platform"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# =============================================================================
# DATABASE INIT
# =============================================================================

init_db()
print(f"[{APP_NAME}] v{APP_VERSION} initialized")

# =============================================================================
# INCLUDE ROUTERS
# =============================================================================

# Auth: /api/login, /api/register
app.include_router(auth_router)

# Portfolio: /api/portfolio
app.include_router(portfolio_router)

# Signals: /api/signals
app.include_router(signals_router)

# News: /api/news-public
app.include_router(news_router)

# Analysis: /api/analyze, /api/digest, /api/prices, /api/coins, /api/fear-greed
app.include_router(analysis_router)

# Admin: /api/admin/*
app.include_router(admin_router)

# AI Stats: /api/ai/*
app.include_router(ai_stats_router)

# AI Summary: /api/ai-summary/*
app.include_router(ai_summary_router)

# WebSocket: /ws, /ws/market, /ws/realtime
app.include_router(websocket_router)

# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """API root"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    from database import redis_client
    
    health = {
        "status": "ok",
        "version": APP_VERSION,
        "services": {
            "api": "ok",
            "database": "ok",
            "redis": "ok"
        }
    }
    
    # Redis check
    try:
        redis_client.ping()
    except:
        health["services"]["redis"] = "error"
        health["status"] = "degraded"
    
    return health


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
