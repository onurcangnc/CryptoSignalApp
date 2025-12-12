#!/usr/bin/env python3
"""
CryptoSignal - Signal Generator Worker v1.0
===========================================
Multi-Factor Confidence System ile sinyal uretimi

Ozellikler:
- analysis_service.generate_signal() kullanimi
- News sentiment entegrasyonu
- Futures data entegrasyonu
- 6 farkli timeframe destegi
- Signal tracking (DB'ye kayit)
"""

import asyncio
import json
import redis
import httpx
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

# Parent path ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analysis_service import AnalysisService
from database import save_signal_track

# Redis connection
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
    password=REDIS_PASSWORD
)

# Config
UPDATE_INTERVAL = 300  # 5 dakika
TIMEFRAMES = ["1d", "1w", "1m", "3m", "6m", "1y"]
TIMEFRAME_LABELS = {
    "1d": "1 Gun",
    "1w": "1 Hafta",
    "1m": "1 Ay",
    "3m": "3 Ay",
    "6m": "6 Ay",
    "1y": "1 Yil"
}

# Analysis Service instance
analysis_service = AnalysisService()

print("[Signal Worker v1.0] Starting...")
print(f"  Update interval: {UPDATE_INTERVAL}s")
print(f"  Timeframes: {', '.join(TIMEFRAMES)}")


def get_news_sentiment_for_coin(symbol: str, news_db: Dict) -> Optional[Dict]:
    """
    Coin icin news sentiment hesapla

    Returns:
        Dict with score (-1 to 1) and news_count
    """
    if not news_db:
        return None

    # Son 24 saatteki haberler
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    relevant_news = []
    for news in news_db.values():
        if news.get("crawled_at", "") < cutoff:
            continue

        coins = news.get("coins", [])
        if symbol in coins or "GENERAL" in coins:
            relevant_news.append(news)

    if not relevant_news:
        return None

    # Sentiment skorlarini topla
    total_score = 0
    for news in relevant_news:
        sentiment = news.get("sentiment", "neutral")
        score = news.get("sentiment_score", 0)

        if sentiment == "bullish":
            total_score += abs(score)
        elif sentiment == "bearish":
            total_score -= abs(score)

    # Ortalama al
    avg_score = total_score / len(relevant_news) if relevant_news else 0

    return {
        "score": round(avg_score, 3),
        "news_count": len(relevant_news)
    }


async def fetch_historical_prices(symbol: str, days: int = 365) -> List:
    """
    CoinGecko'dan historical price data cek
    """
    # CoinGecko ID mapping
    SYMBOL_TO_ID = {
        "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
        "XRP": "ripple", "SOL": "solana", "ADA": "cardano",
        "DOGE": "dogecoin", "TRX": "tron", "AVAX": "avalanche-2",
        "DOT": "polkadot", "LINK": "chainlink", "MATIC": "matic-network",
        "POL": "polygon-ecosystem-token", "LTC": "litecoin",
        "BCH": "bitcoin-cash", "ATOM": "cosmos", "UNI": "uniswap",
        "XLM": "stellar", "ETC": "ethereum-classic", "FIL": "filecoin",
        "APT": "aptos", "NEAR": "near", "INJ": "injective-protocol",
        "OP": "optimism", "ARB": "arbitrum", "SUI": "sui",
        "SEI": "sei-network", "FET": "artificial-superintelligence-alliance",
        "RNDR": "render-token", "AAVE": "aave", "SHIB": "shiba-inu",
        "PEPE": "pepe", "TON": "the-open-network", "HBAR": "hedera-hashgraph",
        "ICP": "internet-computer", "STX": "stacks", "IMX": "immutable-x",
        "TAO": "bittensor", "KAS": "kaspa", "ONDO": "ondo-finance",
        "JUP": "jupiter-exchange-solana", "ENA": "ethena",
        "WLD": "worldcoin-wld", "TIA": "celestia", "PYTH": "pyth-network",
        "GRT": "the-graph", "ALGO": "algorand", "VET": "vechain",
        "FTM": "fantom", "SAND": "the-sandbox", "MANA": "decentraland",
        "AXS": "axie-infinity", "GALA": "gala", "LDO": "lido-dao",
        "MKR": "maker", "SNX": "havven", "CRV": "curve-dao-token",
        "COMP": "compound-governance-token", "ENJ": "enjincoin",
        "CHZ": "chiliz", "FLOW": "flow", "MINA": "mina-protocol",
        "EOS": "eos", "XTZ": "tezos", "NEO": "neo", "ZEC": "zcash",
        "DASH": "dash", "IOTA": "iota", "XMR": "monero",
        "THETA": "theta-token", "EGLD": "elrond-erd-2",
        "QNT": "quant-network", "RUNE": "thorchain", "KAVA": "kava",
        "CFX": "conflux-token", "APE": "apecoin", "GMX": "gmx",
        "W": "wormhole", "STRK": "starknet", "MANTA": "manta-network",
        "DYDX": "dydx-chain", "PENDLE": "pendle", "BLUR": "blur",
        "AGIX": "singularitynet", "OCEAN": "ocean-protocol",
        "FLOKI": "floki", "BONK": "bonk", "WIF": "dogwifcoin",
        "MEME": "memecoin-2", "ORDI": "ordi", "JTO": "jito-governance-token",
        "ZK": "zksync",
    }

    coin_id = SYMBOL_TO_ID.get(symbol)
    if not coin_id:
        return []

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                params={
                    "vs_currency": "usd",
                    "days": str(days),
                    "interval": "daily"
                }
            )

            if resp.status_code == 200:
                data = resp.json()
                return data.get("prices", [])
            elif resp.status_code == 429:
                print(f"[CoinGecko] Rate limited for {symbol}")
                await asyncio.sleep(60)
    except Exception as e:
        print(f"[Historical] {symbol} error: {e}")

    return []


def generate_signals_for_coin(
    symbol: str,
    price_data: Dict,
    futures_data: Dict,
    news_sentiment: Optional[Dict],
    historical_prices: List
) -> Dict:
    """
    Tek coin icin tum timeframe'lerde sinyal uret
    """
    results = {}

    # Technical indicators hesapla
    if historical_prices:
        technical = analysis_service._calculate_indicators(historical_prices, [])
    else:
        # Fallback - sadece current price
        technical = {
            "current_price": price_data.get("price", 0),
            "change_24h": price_data.get("change_24h", 0),
            "change_7d": price_data.get("change_7d", 0),
            "rsi": None,
            "macd": None,
            "bollinger": {},
            "ma": {},
            "volatility": {},
            "trend": "NEUTRAL"
        }

    # Futures bilgisi
    futures = futures_data.get(symbol, {}) if futures_data else None

    # Sinyal uret
    signal_result = analysis_service.generate_signal(
        technical=technical,
        futures=futures,
        news_sentiment=news_sentiment
    )

    # Risk seviyesi hesapla
    risk_result = analysis_service.calculate_risk_level(symbol, technical)

    # Sonucu hazirla
    base_result = {
        "symbol": symbol,
        "name": price_data.get("name", symbol),
        "price": price_data.get("price", 0),
        "change_24h": price_data.get("change_24h", 0),
        "change_7d": price_data.get("change_7d", 0),
        "change_30d": price_data.get("change_30d", 0),
        "market_cap": price_data.get("market_cap", 0),
        "volume_24h": price_data.get("volume_24h", 0),
        "rank": price_data.get("rank", 999),
        "image": price_data.get("image", ""),
        "source": price_data.get("source", "coingecko"),
        "signal": signal_result["signal"],
        "signal_tr": signal_result["signal_tr"],
        "score": signal_result["score"],
        "confidence": signal_result["confidence"],
        "confidence_details": signal_result["confidence_details"],
        "reasons": signal_result["reasons"],
        "risk_level": risk_result["level"],
        "risk_score": risk_result["score"],
        "risk_factors": risk_result["factors"],
        "category": risk_result["category"],
        "technical": technical,
        "news_sentiment": news_sentiment,
        "updated_at": datetime.utcnow().isoformat()
    }

    # Tum timeframe'ler icin ayni sinyal (su anlik basit implementasyon)
    # TODO: Timeframe'e gore farkli periyotlar kullan
    for tf in TIMEFRAMES:
        results[tf] = base_result.copy()
        results[tf]["timeframe"] = tf
        results[tf]["timeframe_label"] = TIMEFRAME_LABELS.get(tf, tf)

    return results


async def generate_all_signals():
    """
    Tum coinler icin sinyal uret
    """
    print(f"\n[Signals] Generating at {datetime.utcnow().strftime('%H:%M:%S')}")

    # Redis'ten verileri al
    prices_raw = r.get("prices_data")
    futures_raw = r.get("futures_data")
    news_raw = r.get("news_db")

    prices_data = json.loads(prices_raw) if prices_raw else {}
    futures_data = json.loads(futures_raw) if futures_raw else {}
    news_db = json.loads(news_raw) if news_raw else {}

    if not prices_data:
        print("[Signals] No price data available")
        return

    print(f"  Coins: {len(prices_data)} | News: {len(news_db)} | Futures: {len(futures_data)}")

    # Market cap'e gore sirala
    sorted_coins = sorted(
        prices_data.items(),
        key=lambda x: x[1].get("market_cap", 0) or 0,
        reverse=True
    )

    # Top 200 coin icin sinyal uret
    all_signals = {tf: {"signals": {}, "stats": {}, "risk_stats": {}, "count": 0} for tf in TIMEFRAMES}
    processed = 0

    for symbol, price_data in sorted_coins[:200]:
        try:
            # News sentiment
            news_sentiment = get_news_sentiment_for_coin(symbol, news_db)

            # Historical prices (rate limit icin sadece top 50)
            historical_prices = []
            if processed < 50:
                historical_prices = await fetch_historical_prices(symbol, days=90)
                if historical_prices:
                    await asyncio.sleep(0.5)  # Rate limit

            # Sinyalleri uret
            coin_signals = generate_signals_for_coin(
                symbol=symbol,
                price_data=price_data,
                futures_data=futures_data,
                news_sentiment=news_sentiment,
                historical_prices=historical_prices
            )

            # Timeframe'lere ekle
            for tf, signal_data in coin_signals.items():
                all_signals[tf]["signals"][symbol] = signal_data

                # Stats guncelle
                sig = signal_data["signal"]
                if sig not in all_signals[tf]["stats"]:
                    all_signals[tf]["stats"][sig] = 0
                all_signals[tf]["stats"][sig] += 1

                # Risk stats guncelle
                risk = signal_data["risk_level"]
                if risk not in all_signals[tf]["risk_stats"]:
                    all_signals[tf]["risk_stats"][risk] = 0
                all_signals[tf]["risk_stats"][risk] += 1

            processed += 1

            if processed % 50 == 0:
                print(f"  Processed: {processed}")

        except Exception as e:
            print(f"  Error {symbol}: {e}")
            continue

    # Count'lari guncelle
    for tf in TIMEFRAMES:
        all_signals[tf]["count"] = len(all_signals[tf]["signals"])

    # Redis'e yaz
    r.set("signals_all_timeframes", json.dumps(all_signals))
    r.set("signals_data", json.dumps(all_signals["1d"]["signals"]))  # Legacy uyumluluk
    r.set("signals_stats", json.dumps(all_signals["1d"]["stats"]))
    r.set("signals_risk_stats", json.dumps(all_signals["1d"]["risk_stats"]))
    r.set("signals_updated", datetime.utcnow().isoformat())
    r.set("signals_count", str(processed))

    # Stats yazdir
    stats_1d = all_signals["1d"]["stats"]
    buy_count = stats_1d.get("BUY", 0) + stats_1d.get("STRONG_BUY", 0)
    sell_count = stats_1d.get("SELL", 0) + stats_1d.get("STRONG_SELL", 0)
    hold_count = stats_1d.get("HOLD", 0)

    print(f"  Total: {processed} | BUY: {buy_count} | HOLD: {hold_count} | SELL: {sell_count}")

    # Signal tracking icin kayit (opsiyonel - top 20)
    # Bu kisim signal checker worker'a birakilabilir


async def main():
    """Main loop"""
    print(f"[Signal Worker] Starting main loop")

    while True:
        try:
            await generate_all_signals()
        except Exception as e:
            print(f"[Signal Worker] Error: {e}")

        print(f"[Signals] Next update in {UPDATE_INTERVAL}s")
        await asyncio.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())