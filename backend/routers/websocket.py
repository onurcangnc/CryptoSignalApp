# -*- coding: utf-8 -*-
"""
CryptoSignal - WebSocket Router
===============================
Real-time fiyat güncellemeleri
"""

import json
import asyncio
from typing import Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from database import redis_client

router = APIRouter(tags=["WebSocket"])

# Connected clients
ws_clients: Set[WebSocket] = set()


async def broadcast(message: dict):
    """Tüm bağlı client'lara mesaj gönder"""
    if not ws_clients:
        return
    
    dead_clients = set()
    msg = json.dumps(message)
    
    for client in ws_clients:
        try:
            await client.send_text(msg)
        except:
            dead_clients.add(client)
    
    # Ölü client'ları temizle
    ws_clients.difference_update(dead_clients)


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Ana WebSocket endpoint'i"""
    await ws.accept()
    ws_clients.add(ws)
    print(f"[WS] +1 ({len(ws_clients)} total)")
    
    try:
        # İlk veriyi gönder
        await send_initial_data(ws)
        
        # Mesaj döngüsü
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=30)
                
                try:
                    data = json.loads(msg)
                    msg_type = data.get("type")
                    
                    if msg_type == "ping":
                        await ws.send_text(json.dumps({
                            "type": "pong",
                            "time": datetime.utcnow().isoformat()
                        }))
                    
                    elif msg_type == "subscribe":
                        # Belirli coin'lere subscribe
                        coins = data.get("coins", [])
                        await ws.send_text(json.dumps({
                            "type": "subscribed",
                            "coins": coins
                        }))
                    
                except json.JSONDecodeError:
                    pass
            
            except asyncio.TimeoutError:
                # Keepalive ping
                try:
                    await ws.send_text(json.dumps({
                        "type": "ping",
                        "time": datetime.utcnow().isoformat()
                    }))
                except:
                    break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS] Error: {e}")
    finally:
        ws_clients.discard(ws)
        print(f"[WS] -1 ({len(ws_clients)} total)")


@router.websocket("/ws/market")
async def ws_market(ws: WebSocket):
    """Market WebSocket - alias"""
    await websocket_endpoint(ws)


@router.websocket("/ws/realtime")
async def ws_realtime(ws: WebSocket):
    """Realtime WebSocket - alias"""
    await websocket_endpoint(ws)


async def send_initial_data(ws: WebSocket):
    """İlk bağlantıda verileri gönder"""
    try:
        # Redis'den verileri al
        prices_raw = redis_client.get("prices_data")
        prices = json.loads(prices_raw) if prices_raw else {}
        
        fx_raw = redis_client.get("fx_rates")
        fx = json.loads(fx_raw) if fx_raw else {"USD": 1, "TRY": 34.5, "EUR": 0.92}
        
        fear_greed_raw = redis_client.get("fear_greed")
        fear_greed = json.loads(fear_greed_raw) if fear_greed_raw else {"value": 50}
        
        signals_stats_raw = redis_client.get("signals_stats")
        signals_stats = json.loads(signals_stats_raw) if signals_stats_raw else {}
        
        # Market overview
        market = []
        sorted_coins = sorted(
            prices.keys(),
            key=lambda x: prices[x].get("market_cap", 0) or 0,
            reverse=True
        )
        
        for symbol in sorted_coins[:100]:
            p = prices[symbol]
            market.append({
                "symbol": symbol,
                "name": p.get("name", symbol),
                "price": p.get("price", 0),
                "change_24h": p.get("change_24h", 0),
                "change_instant": p.get("change_instant", 0),
                "market_cap": p.get("market_cap", 0),
                "rank": p.get("rank", 999)
            })
        
        await ws.send_text(json.dumps({
            "type": "init",
            "prices": prices,
            "market": market,
            "fx": fx,
            "fear_greed": fear_greed,
            "signals_stats": signals_stats,
            "coins_count": len(prices),
            "time": datetime.utcnow().isoformat()
        }))
    
    except Exception as e:
        print(f"[WS] Initial data error: {e}")


async def price_update_loop():
    """
    Fiyat güncelleme döngüsü
    Worker'dan gelen güncellemeleri broadcast et
    """
    last_update = None
    
    while True:
        try:
            # Redis'den son güncelleme zamanını kontrol et
            updated = redis_client.get("prices_updated")
            
            if updated and updated != last_update:
                last_update = updated
                
                # Fiyat verilerini al
                prices_raw = redis_client.get("prices_data")
                if prices_raw:
                    prices = json.loads(prices_raw)
                    
                    # Sadece top 50 coin'i broadcast et
                    top_coins = sorted(
                        prices.keys(),
                        key=lambda x: prices[x].get("market_cap", 0) or 0,
                        reverse=True
                    )[:50]
                    
                    update_data = {
                        symbol: {
                            "price": prices[symbol].get("price", 0),
                            "change_24h": prices[symbol].get("change_24h", 0),
                            "change_instant": prices[symbol].get("change_instant", 0)
                        }
                        for symbol in top_coins
                    }
                    
                    await broadcast({
                        "type": "price_update",
                        "prices": update_data,
                        "time": datetime.utcnow().isoformat()
                    })
            
            await asyncio.sleep(2)  # 2 saniyede bir kontrol
        
        except Exception as e:
            print(f"[WS] Price update loop error: {e}")
            await asyncio.sleep(5)


def get_connected_count() -> int:
    """Bağlı client sayısı"""
    return len(ws_clients)
