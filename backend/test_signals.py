#!/usr/bin/env python3
"""Test script - Generate sample signals for testing"""

import redis
import json
from datetime import datetime, timedelta
import random

REDIS_PASS = "3f9af2788cb89aa74c06bd48dd290658"

r = redis.Redis(host='localhost', port=6379, password=REDIS_PASS, decode_responses=True)

# Test sinyalleri
test_signals = {
    "BTC": {
        "symbol": "BTC",
        "coin": "BTC",
        "signal": "BUY",
        "signal_type": "BUY",
        "confidence": 85,
        "score": 85,
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "price": 97234.50,
        "target": 105000,
        "stop_loss": 92000
    },
    "ETH": {
        "symbol": "ETH",
        "coin": "ETH",
        "signal": "HOLD",
        "signal_type": "HOLD",
        "confidence": 72,
        "score": 72,
        "created_at": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
        "price": 3721.30,
        "target": 4000,
        "stop_loss": 3500
    },
    "SOL": {
        "symbol": "SOL",
        "coin": "SOL",
        "signal": "BUY",
        "signal_type": "BUY",
        "confidence": 91,
        "score": 91,
        "created_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "price": 201.45,
        "target": 230,
        "stop_loss": 185
    },
    "XRP": {
        "symbol": "XRP",
        "coin": "XRP",
        "signal": "HOLD",
        "signal_type": "HOLD",
        "confidence": 65,
        "score": 65,
        "created_at": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
        "price": 2.38,
        "target": 2.80,
        "stop_loss": 2.10
    },
    "ADA": {
        "symbol": "ADA",
        "coin": "ADA",
        "signal": "SELL",
        "signal_type": "SELL",
        "confidence": 78,
        "score": 78,
        "created_at": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
        "price": 1.05,
        "target": 0.85,
        "stop_loss": 1.15
    }
}

# Redis'e kaydet
r.set("signals_data", json.dumps(test_signals))
r.set("signals_updated", datetime.utcnow().isoformat())

# Signal stats
stats = {
    "success_rate": 73.5,
    "total": 127,
    "profitable": 93,
    "avg_profit_pct": 8.2,
    "total_pnl_pct": 147.3
}
r.set("signal_stats", json.dumps(stats))

print("✅ Test signals created successfully!")
print(f"   - {len(test_signals)} signals")
print(f"   - Success rate: {stats['success_rate']}%")
print(f"   - Redis keys: signals_data, signals_updated, signal_stats")
