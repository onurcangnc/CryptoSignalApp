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
from .signal_stats import router as signal_stats_router
from .payment import router as payment_router
from .ads import router as ads_router
from .watchlist import router as watchlist_router
from .price_alerts import router as price_alerts_router

__all__ = [
    'auth_router',
    'portfolio_router',
    'signals_router',
    'news_router',
    'analysis_router',
    'admin_router',
    'ai_stats_router',
    'ai_summary_router',
    'websocket_router',
    'signal_stats_router',
    'payment_router',
    'ads_router',
    'watchlist_router',
    'price_alerts_router'
]
