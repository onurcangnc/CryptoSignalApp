# -*- coding: utf-8 -*-
"""
CryptoSignal - News Router
==========================
/api/news endpoints
"""

from fastapi import APIRouter, Query
from typing import Optional
import json

from database import redis_client

router = APIRouter(prefix="/api", tags=["News"])


@router.get("/news-public")
async def get_public_news(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    sentiment: Optional[str] = Query(default=None, pattern="^(bullish|bearish|neutral)$"),
    coin: Optional[str] = None
):
    """Herkese açık haber listesi - Pagination destekli"""
    try:
        news_raw = redis_client.get("news_db")
        if not news_raw:
            return {"news": [], "total": 0, "stats": {"bullish": 0, "bearish": 0, "neutral": 0}}
        
        news_dict = json.loads(news_raw)
        news_list = list(news_dict.values())
        
        # Sırala (en yeni önce)
        news_list.sort(
            key=lambda x: x.get('crawled_at', x.get('published_at', '')),
            reverse=True
        )
        
        # Stats hesapla (tüm haberler için)
        stats = {
            "bullish": sum(1 for n in news_list if n.get('sentiment') == 'bullish'),
            "bearish": sum(1 for n in news_list if n.get('sentiment') == 'bearish'),
            "neutral": sum(1 for n in news_list if n.get('sentiment') == 'neutral')
        }
        
        # Filtrele
        filtered = news_list
        
        if sentiment:
            filtered = [n for n in filtered if n.get('sentiment') == sentiment]
        
        if coin:
            coin_upper = coin.upper()
            filtered = [n for n in filtered if coin_upper in (n.get('coins') or [])]
        
        # Pagination uygula
        paginated = filtered[offset:offset + limit]
        
        return {
            "news": paginated,
            "total": len(news_list),
            "filtered_count": len(filtered),
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < len(filtered),
            "stats": stats
        }
    
    except Exception as e:
        return {"news": [], "total": 0, "stats": {}, "error": str(e)}


@router.get("/news/coins")
async def get_news_coins():
    """Haberlerde geçen coinleri getir"""
    try:
        news_raw = redis_client.get("news_db")
        if not news_raw:
            return {"coins": []}
        
        news_dict = json.loads(news_raw)
        
        coin_counts = {}
        for news in news_dict.values():
            for coin in news.get('coins', []):
                if coin and coin != 'GENERAL':
                    coin_counts[coin] = coin_counts.get(coin, 0) + 1
        
        # En çok geçen coinler
        sorted_coins = sorted(coin_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "coins": [{"symbol": c, "count": n} for c, n in sorted_coins[:50]]
        }
    
    except Exception as e:
        return {"coins": [], "error": str(e)}


@router.get("/news/sentiment")
async def get_news_sentiment(coin: Optional[str] = None):
    """Haber sentiment özeti"""
    try:
        news_raw = redis_client.get("news_db")
        if not news_raw:
            return {"sentiment": "neutral", "score": 0, "news_count": 0}
        
        news_dict = json.loads(news_raw)
        news_list = list(news_dict.values())
        
        if coin:
            coin_upper = coin.upper()
            news_list = [n for n in news_list if coin_upper in (n.get('coins') or [])]
        
        if not news_list:
            return {"sentiment": "neutral", "score": 0, "news_count": 0}
        
        bullish = sum(1 for n in news_list if n.get('sentiment') == 'bullish')
        bearish = sum(1 for n in news_list if n.get('sentiment') == 'bearish')
        total = len(news_list)
        
        score = (bullish - bearish) / total if total > 0 else 0
        
        if score > 0.2:
            sentiment = "bullish"
        elif score < -0.2:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": round(score, 3),
            "news_count": total,
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": total - bullish - bearish
        }
    
    except Exception as e:
        return {"sentiment": "neutral", "score": 0, "error": str(e)}