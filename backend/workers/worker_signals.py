#!/usr/bin/env python3
"""
CryptoSignal - Signal Generator Worker v1.2
===========================================
Multi-Factor Confidence System ile sinyal uretimi

v1.2 Guncellemeler:
- ADD: Quality Gate - Dusuk kaliteli trade sinyallerini filtrele
  - MIN_CONFIDENCE_FOR_TRADE = 50 (HIGH risk icin +10)
  - MIN_FACTOR_ALIGNMENT = 3 (en az 3/6 faktor uyumlu olmali)
- ADD: signal_raw ve quality_gate metadata
- ADD: Quality Gate stats loglama

v1.1 Guncellemeler (GPT-5.2 feedback):
- FIX: String tarih karsilastirmasi -> datetime.fromisoformat()
- FIX: Signal tracking aktif (top 20 coin)
- ADD: Timeframe uyarisi (ayni veri kullanildigi belirtiliyor)
- ADD: Semaphore ile rate limiting

Ozellikler:
- analysis_service.generate_signal() kullanimi
- News sentiment entegrasyonu
- Futures data entegrasyonu
- 6 farkli timeframe destegi
- Signal tracking (DB'ye kayit)
- Quality Gate (trade kalite filtresi)
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

# CoinGecko rate limiting
COINGECKO_SEMAPHORE = asyncio.Semaphore(3)  # Max 3 concurrent requests
COINGECKO_BACKOFF = 5  # Seconds between batches

# Analysis Service instance
analysis_service = AnalysisService()

# --- Quality Gate (Trade kalitesi filtresi) ---
# v1.3: Daha dengeli ayarlar (eskisi çok sıkıydı, hiç BUY sinyali üretmiyordu)
MIN_CONFIDENCE_FOR_TRADE = 35          # %35 altı → BEKLE (eskisi 50)
MIN_FACTOR_ALIGNMENT = 2               # En az 2/6 faktör uyumlu olmalı (eskisi 3)
HIGH_RISK_CONFIDENCE_PENALTY = 5       # HIGH risk → +5 threshold (eskisi 10)

BUY_SIGNALS = {"BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"}
SELL_SIGNALS = {"SELL", "SAT", "STRONG_SELL", "GÜÇLÜ SAT"}
HOLD_SIGNALS = {"HOLD", "BEKLE"}


def _norm_risk(risk_level: str) -> str:
    """Risk seviyesini normalize et"""
    if not risk_level:
        return "UNKNOWN"
    r = risk_level.strip().upper()
    if r in {"HIGH", "YÜKSEK"}:
        return "HIGH"
    if r in {"MEDIUM", "ORTA"}:
        return "MEDIUM"
    if r in {"LOW", "DÜŞÜK", "DUSUK"}:
        return "LOW"
    return r


def _extract_alignment(details: dict) -> int:
    """
    confidence_details içinden factor uyum sayısını çıkarır.
    Hem int alanlar hem list alanlar için tolerant.
    """
    if not isinstance(details, dict):
        return 0

    fb = details.get("factors_buy")
    fs = details.get("factors_sell")

    # int olarak geliyorsa
    if isinstance(fb, (int, float)) or isinstance(fs, (int, float)):
        try:
            fb = int(fb or 0)
            fs = int(fs or 0)
            return max(fb, fs)
        except Exception:
            return 0

    # list olarak geliyorsa
    if isinstance(fb, list) or isinstance(fs, list):
        fb_n = len(fb or [])
        fs_n = len(fs or [])
        return max(fb_n, fs_n)

    return 0


def _has_indicators(analysis: dict) -> bool:
    """
    İndikatör verisi var mı kontrol et.
    RSI, MACD, MA gibi temel indikatörler yoksa False döner.
    """
    ind = analysis.get("indicators") or {}
    vals = [
        analysis.get("rsi"), analysis.get("macd"), analysis.get("ma"),
        ind.get("rsi"), ind.get("macd"), ind.get("ma"),
    ]
    # En az bir geçerli indikatör değeri olmalı
    ok = any(v not in (None, "N/A", "na", "NA", "") for v in vals)
    return ok


def should_emit_signal(analysis: dict, risk_level: str) -> tuple:
    """
    AL/SAT üretmeden önce kalite kontrolü.
    Düşük kaliteyi BEKLE'ye çevirir.

    Returns:
        (final_signal, confidence, gate_reason)
    """
    signal = (analysis.get("signal") or "BEKLE").strip()
    confidence = float(analysis.get("confidence") or 0)
    details = analysis.get("confidence_details") or {}

    # Zaten BEKLE ise
    if signal in HOLD_SIGNALS:
        return "HOLD", confidence, "already_hold"

    # Trade sinyali değilse güvenli tarafta kal
    if signal not in BUY_SIGNALS and signal not in SELL_SIGNALS:
        return "HOLD", confidence, f"unknown_signal_{signal}"

    # İndikatör verisi yoksa trade verme (GPT-5.2 önerisi)
    if not _has_indicators(analysis):
        return "HOLD", confidence, "missing_indicators"

    # Risk seviyesine göre threshold ayarla
    risk = _norm_risk(risk_level)
    threshold = MIN_CONFIDENCE_FOR_TRADE + (HIGH_RISK_CONFIDENCE_PENALTY if risk == "HIGH" else 0)

    # Confidence kontrolü
    if confidence < threshold:
        return "HOLD", confidence, f"low_confidence_{confidence:.1f}<{threshold}"

    # Faktör uyumu kontrolü
    alignment = _extract_alignment(details)
    if alignment < MIN_FACTOR_ALIGNMENT:
        return "HOLD", confidence, f"low_alignment_{alignment}<{MIN_FACTOR_ALIGNMENT}"

    return signal, confidence, "passed"


print("[Signal Worker v1.2] Starting with Quality Gate...")
print(f"  Update interval: {UPDATE_INTERVAL}s")
print(f"  Timeframes: {', '.join(TIMEFRAMES)}")
print(f"  CoinGecko concurrency: 3")
print(f"  Quality Gate: min_conf={MIN_CONFIDENCE_FOR_TRADE}, min_align={MIN_FACTOR_ALIGNMENT}")


def get_news_sentiment_for_coin(symbol: str, news_db: Dict) -> Optional[Dict]:
    """
    Coin icin news sentiment hesapla

    Returns:
        Dict with score (-1 to 1) and news_count
    """
    if not news_db:
        return None

    # Son 24 saatteki haberler (FIX: datetime karsilastirmasi)
    cutoff_dt = datetime.utcnow() - timedelta(hours=24)

    relevant_news = []
    for news in news_db.values():
        crawled_str = news.get("crawled_at", "")
        if not crawled_str:
            continue
        try:
            # ISO format string -> datetime
            crawled_dt = datetime.fromisoformat(crawled_str.replace("Z", "+00:00"))
            if crawled_dt.tzinfo:
                crawled_dt = crawled_dt.replace(tzinfo=None)  # Naive datetime
            if crawled_dt < cutoff_dt:
                continue
        except (ValueError, TypeError):
            continue  # Invalid date format, skip

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
        # Semaphore ile rate limiting
        async with COINGECKO_SEMAPHORE:
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
                    print(f"[CoinGecko] Rate limited for {symbol}, backing off {COINGECKO_BACKOFF}s")
                    await asyncio.sleep(COINGECKO_BACKOFF)
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

    # Technical indicators hesapla (public wrapper kullan)
    if historical_prices:
        technical = analysis_service.calculate_indicators(historical_prices)
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

    # --- Apply Quality Gate ---
    raw_signal = signal_result["signal"]
    raw_signal_tr = signal_result["signal_tr"]
    risk_level = risk_result["level"]

    final_signal, final_conf, gate_reason = should_emit_signal(signal_result, risk_level)

    # Signal TR'yi de güncelle
    signal_tr_map = {
        "HOLD": "BEKLE",
        "BUY": "AL",
        "STRONG_BUY": "GÜÇLÜ AL",
        "SELL": "SAT",
        "STRONG_SELL": "GÜÇLÜ SAT"
    }
    final_signal_tr = signal_tr_map.get(final_signal, raw_signal_tr)

    # Quality gate metadata
    quality_gate = {
        "passed": gate_reason == "passed",
        "reason": gate_reason,
        "original_signal": raw_signal,
        "min_conf": MIN_CONFIDENCE_FOR_TRADE,
        "min_align": MIN_FACTOR_ALIGNMENT,
    }

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
        "signal": final_signal,
        "signal_tr": final_signal_tr,
        "signal_raw": raw_signal,
        "quality_gate": quality_gate,
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
    quality_gate_stats = {"passed": 0, "blocked": 0, "reasons": {}}

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

                # Quality gate stats (sadece 1d için)
                if tf == "1d":
                    qg = signal_data.get("quality_gate", {})
                    if qg.get("passed"):
                        quality_gate_stats["passed"] += 1
                    elif qg.get("original_signal") in BUY_SIGNALS | SELL_SIGNALS:
                        # Sadece trade sinyali engellenenleri say
                        quality_gate_stats["blocked"] += 1
                        reason = qg.get("reason", "unknown")
                        # Reason'ı kategorize et
                        if reason.startswith("low_confidence"):
                            reason_key = "low_confidence"
                        elif reason.startswith("low_alignment"):
                            reason_key = "low_alignment"
                        else:
                            reason_key = reason
                        quality_gate_stats["reasons"][reason_key] = quality_gate_stats["reasons"].get(reason_key, 0) + 1

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

    # Quality Gate stats
    qg_passed = quality_gate_stats["passed"]
    qg_blocked = quality_gate_stats["blocked"]
    qg_reasons = quality_gate_stats["reasons"]
    print(f"  [QualityGate] Passed: {qg_passed} | Blocked: {qg_blocked} | Reasons: {qg_reasons}")

    # Signal tracking icin kayit - Tum coinler (akilli filtreleme ile)
    await track_all_signals(all_signals["1d"]["signals"])


async def track_all_signals(signals_1d: Dict):
    """
    Tum coinler icin akilli sinyal tracking

    Filtreleme kurallari:
    1. HOLD sinyalleri hariç
    2. Confidence < 30 hariç (dusuk guvenli sinyaller)
    3. Son 24 saat icinde ayni coin+sinyal duplicate hariç
    """
    # Son 24 saat icindeki kayitlari kontrol icin
    recent_tracks = set()
    try:
        from database import get_db
        with get_db() as conn:
            rows = conn.execute("""
                SELECT symbol, signal FROM signal_tracking
                WHERE created_at >= datetime('now', '-24 hours')
            """).fetchall()
            recent_tracks = {(row["symbol"], row["signal"]) for row in rows}
    except Exception as e:
        print(f"  [Track] Recent check error: {e}")

    tracked = 0
    skipped_hold = 0
    skipped_low_conf = 0
    skipped_duplicate = 0

    for symbol, signal_data in signals_1d.items():
        if not signal_data:
            continue

        # 1. HOLD sinyalleri hariç
        signal = signal_data.get("signal", "")
        if signal not in ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"]:
            skipped_hold += 1
            continue

        # 2. Dusuk confidence hariç
        confidence = signal_data.get("confidence", 0)
        if confidence < 30:
            skipped_low_conf += 1
            continue

        # 3. Duplicate kontrolu (son 24 saat)
        if (symbol, signal) in recent_tracks:
            skipped_duplicate += 1
            continue

        try:
            # Target ve stop-loss hesapla (basit ATR bazli)
            price = signal_data.get("price", 0)
            volatility = signal_data.get("technical", {}).get("volatility", {})
            atr_pct = volatility.get("atr_percent", 3.0)  # Default %3

            if signal in ["STRONG_BUY", "BUY"]:
                target_price = price * (1 + atr_pct / 100 * 2)  # 2x ATR profit
                stop_loss = price * (1 - atr_pct / 100)  # 1x ATR stop
            else:  # SELL
                target_price = price * (1 - atr_pct / 100 * 2)
                stop_loss = price * (1 + atr_pct / 100)

            # Signal TR mapping
            signal_tr = signal_data.get("signal_tr", signal)

            # DB'ye kaydet (check_date fonksiyon içinde hesaplanıyor)
            save_signal_track(
                symbol=symbol,
                signal=signal,
                signal_tr=signal_tr,
                confidence=int(signal_data.get("confidence", 0)),
                entry_price=price,
                target_price=target_price,
                stop_loss=stop_loss,
                timeframe="1d"
            )
            tracked += 1

        except Exception as e:
            print(f"  [Track] Error {symbol}: {e}")
            continue

    # Detayli log
    print(f"  [Track] Saved: {tracked} | Skip: HOLD={skipped_hold}, LowConf={skipped_low_conf}, Dup={skipped_duplicate}")


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