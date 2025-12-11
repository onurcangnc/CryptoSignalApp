# -*- coding: utf-8 -*-
"""
CryptoSignal - Routers
======================
API endpoint router'ları
"""

from .auth import router as auth_router
from .portfolio import router as portfolio_router
from .signals import router as signals_router
from .news import router as news_router
from .analysis import router as analysis_router
from .admin import router as admin_router
from .ai_stats import router as ai_stats_router
from .ai_summary import router as ai_summary_router
from .websocket import router as websocket_router

__all__ = [
    'auth_router',
    'portfolio_router',
    'signals_router',
    'news_router',
    'analysis_router',
    'admin_router',
    'ai_stats_router',
    'ai_summary_router',
    'websocket_router'
]
