# -*- coding: utf-8 -*-
"""
CryptoSignal - Signals Router
=============================
/api/signals endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import json

from database import redis_client
from config import TIMEFRAME_LABELS

router = APIRouter(prefix="/api", tags=["Signals"])


@router.get("/signals")
async def get_signals(
    timeframe: str = Query(default="1d", pattern="^(1d|1w|1m|3m|6m|1y)$"),
    limit: int = Query(default=500, ge=1, le=500),
    signal_filter: Optional[str] = Query(default=None, pattern="^(BUY|SELL|HOLD|ALL)$"),
    sort_by: str = Query(default="market_cap", pattern="^(market_cap|change_24h|confidence|score)$"),
    search: Optional[str] = None
):
    """
    Sinyalleri getir
    
    Parameters:
    - timeframe: 1d, 1w, 1m, 3m, 6m, 1y
    - limit: Maksimum sonuç (1-500)
    - signal_filter: BUY, SELL, HOLD veya ALL
    - sort_by: Sıralama kriteri
    - search: Coin arama
    """
    try:
        # Tüm timeframe'leri kontrol et
        all_tf_data = redis_client.get("signals_all_timeframes")
        
        if all_tf_data:
            all_timeframes = json.loads(all_tf_data)
            
            if timeframe in all_timeframes:
                tf_data = all_timeframes[timeframe]
                signals = tf_data.get('signals', {})
                stats = tf_data.get('stats', {})
                risk_stats = tf_data.get('risk_stats', {})
            else:
                signals = json.loads(redis_client.get("signals_data") or "{}")
                stats = json.loads(redis_client.get("signals_stats") or "{}")
                risk_stats = json.loads(redis_client.get("signals_risk_stats") or "{}")
        else:
            signals = json.loads(redis_client.get("signals_data") or "{}")
            stats = json.loads(redis_client.get("signals_stats") or "{}")
            risk_stats = json.loads(redis_client.get("signals_risk_stats") or "{}")
        
        # List'e çevir
        signals_list = list(signals.values())
        
        # Filtrele
        if signal_filter and signal_filter != "ALL":
            if signal_filter == "BUY":
                signals_list = [s for s in signals_list if s.get('signal') in ['BUY', 'STRONG_BUY']]
            elif signal_filter == "SELL":
                signals_list = [s for s in signals_list if s.get('signal') in ['SELL', 'STRONG_SELL']]
            elif signal_filter == "HOLD":
                signals_list = [s for s in signals_list if s.get('signal') == 'HOLD']
        
        # Ara
        if search:
            search_lower = search.lower()
            signals_list = [s for s in signals_list if search_lower in s.get('symbol', '').lower()]
        
        # Sırala
        if sort_by == "market_cap":
            signals_list.sort(key=lambda x: x.get('market_cap', 0) or 0, reverse=True)
        elif sort_by == "change_24h":
            signals_list.sort(key=lambda x: x.get('change_24h', 0) or 0, reverse=True)
        elif sort_by == "confidence":
            signals_list.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        elif sort_by == "score":
            signals_list.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Limit
        signals_list = signals_list[:limit]
        
        return {
            "success": True,
            "timeframe": timeframe,
            "timeframe_label": TIMEFRAME_LABELS.get(timeframe, timeframe),
            "count": len(signals_list),
            "total": len(signals),
            "stats": stats,
            "risk_stats": risk_stats,
            "signals": signals_list,
            "updated_at": redis_client.get("signals_updated")
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "signals": [],
            "stats": {},
            "count": 0
        }


@router.get("/signals/stats")
async def get_signals_stats():
    """Tüm timeframe'ler için sinyal istatistikleri"""
    try:
        all_tf_data = redis_client.get("signals_all_timeframes")
        
        if all_tf_data:
            all_timeframes = json.loads(all_tf_data)
            
            result = {}
            for tf, tf_data in all_timeframes.items():
                stats = tf_data.get('stats', {})
                result[tf] = {
                    'label': TIMEFRAME_LABELS.get(tf, tf),
                    'total': tf_data.get('count', 0),
                    'buy': stats.get('STRONG_BUY', 0) + stats.get('BUY', 0),
                    'hold': stats.get('HOLD', 0),
                    'sell': stats.get('STRONG_SELL', 0) + stats.get('SELL', 0),
                    'stats': stats
                }
            
            return {
                "success": True,
                "timeframes": result,
                "updated_at": redis_client.get("signals_updated")
            }
        
        # Legacy fallback
        stats = json.loads(redis_client.get("signals_stats") or "{}")
        return {
            "success": True,
            "timeframes": {
                "1d": {
                    'label': '1 Gün',
                    'total': sum(stats.values()) if stats else 0,
                    'buy': stats.get('STRONG_BUY', 0) + stats.get('BUY', 0),
                    'hold': stats.get('HOLD', 0),
                    'sell': stats.get('STRONG_SELL', 0) + stats.get('SELL', 0),
                    'stats': stats
                }
            },
            "updated_at": redis_client.get("signals_updated")
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/signals/{symbol}")
async def get_signal_detail(
    symbol: str,
    timeframe: str = Query(default="1d", pattern="^(1d|1w|1m|3m|6m|1y)$")
):
    """Tek bir coin için detaylı sinyal"""
    symbol = symbol.upper()
    
    try:
        all_tf_data = redis_client.get("signals_all_timeframes")
        
        if all_tf_data:
            all_timeframes = json.loads(all_tf_data)
            
            coin_signals = {}
            for tf, tf_data in all_timeframes.items():
                signals = tf_data.get('signals', {})
                if symbol in signals:
                    coin_signals[tf] = signals[symbol]
            
            if not coin_signals:
                raise HTTPException(status_code=404, detail=f"Signal not found for {symbol}")
            
            primary = coin_signals.get(timeframe, list(coin_signals.values())[0])
            
            return {
                "success": True,
                "symbol": symbol,
                "primary_timeframe": timeframe,
                "signal": primary,
                "all_timeframes": coin_signals
            }
        else:
            signals = json.loads(redis_client.get("signals_data") or "{}")
            if symbol not in signals:
                raise HTTPException(status_code=404, detail=f"Signal not found for {symbol}")
            
            return {
                "success": True,
                "symbol": symbol,
                "signal": signals[symbol]
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
