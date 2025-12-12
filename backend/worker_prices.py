#!/usr/bin/env python3
"""
CryptoSignal - Price Worker v3.2
================================
- 1000 coin desteği
- Top 100 Binance WebSocket real-time
- CoinGecko 5 dakika cache
- FIX: Doğru CoinGecko ID eşleştirmesi
"""

import asyncio
import json
import redis
import httpx
import websockets
import os
from datetime import datetime, timedelta
from typing import Dict, Set

# Redis
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, password=REDIS_PASSWORD)

# Ayarlar
COINGECKO_INTERVAL = 300  # 5 dakika
REDIS_SYNC_INTERVAL = 1   # 1 saniye
CLEANUP_INTERVAL = 3600   # 1 saat

# State
prices_data: Dict[str, Dict] = {}
ws_connected = False

print("[Price Worker v3.2] Starting...")

# Öncelikli CoinGecko ID -> Symbol eşleştirmesi (doğru coinler)
PRIORITY_COINS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "solana": "SOL",
    "cardano": "ADA",
    "dogecoin": "DOGE",
    "tron": "TRX",
    "avalanche-2": "AVAX",
    "polkadot": "DOT",
    "chainlink": "LINK",
    "polygon-ecosystem-token": "POL",
    "matic-network": "MATIC",
    "litecoin": "LTC",
    "bitcoin-cash": "BCH",
    "cosmos": "ATOM",
    "uniswap": "UNI",
    "stellar": "XLM",
    "ethereum-classic": "ETC",
    "filecoin": "FIL",
    "aptos": "APT",
    "near": "NEAR",
    "injective-protocol": "INJ",
    "optimism": "OP",
    "arbitrum": "ARB",
    "sui": "SUI",
    "sei-network": "SEI",
    "artificial-superintelligence-alliance": "FET",
    "render-token": "RNDR",
    "aave": "AAVE",
    "shiba-inu": "SHIB",
    "pepe": "PEPE",
    "the-open-network": "TON",
    "hedera-hashgraph": "HBAR",
    "internet-computer": "ICP",
    "stacks": "STX",
    "immutable-x": "IMX",
    "bittensor": "TAO",
    "kaspa": "KAS",
    "ondo-finance": "ONDO",
    "jupiter-exchange-solana": "JUP",
    "ethena": "ENA",
    "worldcoin-wld": "WLD",
    "celestia": "TIA",
    "pyth-network": "PYTH",
    "the-graph": "GRT",
    "algorand": "ALGO",
    "vechain": "VET",
    "fantom": "FTM",
    "the-sandbox": "SAND",
    "decentraland": "MANA",
    "axie-infinity": "AXS",
    "gala": "GALA",
    "lido-dao": "LDO",
    "maker": "MKR",
    "havven": "SNX",
    "curve-dao-token": "CRV",
    "compound-governance-token": "COMP",
    "1inch": "1INCH",
    "enjincoin": "ENJ",
    "chiliz": "CHZ",
    "flow": "FLOW",
    "mina-protocol": "MINA",
    "eos": "EOS",
    "tezos": "XTZ",
    "neo": "NEO",
    "zcash": "ZEC",
    "dash": "DASH",
    "iota": "IOTA",
    "monero": "XMR",
    "bitcoin-cash-sv": "BSV",
    "theta-token": "THETA",
    "klay-token": "KLAY",
    "elrond-erd-2": "EGLD",
    "quant-network": "QNT",
    "thorchain": "RUNE",
    "kava": "KAVA",
    "conflux-token": "CFX",
    "apecoin": "APE",
    "gmx": "GMX",
    "wormhole": "W",
    "starknet": "STRK",
    "manta-network": "MANTA",
    "dydx-chain": "DYDX",
    "pendle": "PENDLE",
    "blur": "BLUR",
    "magic": "MAGIC",
    "singularitynet": "AGIX",
    "ocean-protocol": "OCEAN",
    "floki": "FLOKI",
    "bonk": "BONK",
    "dogwifcoin": "WIF",
    "memecoin-2": "MEME",
    "ordi": "ORDI",
    "sats-ordinals": "SATS",
    "jito-governance-token": "JTO",
    "zksync": "ZK",
    "tether": "USDT",
    "usd-coin": "USDC",
    "dai": "DAI",
    "first-digital-usd": "FDUSD",
}

# Ters mapping: Symbol -> CoinGecko ID
SYMBOL_TO_ID = {v: k for k, v in PRIORITY_COINS.items()}

# Top 100 Binance symbols for WebSocket
BINANCE_TOP100 = {
    "btcusdt": "BTC", "ethusdt": "ETH", "bnbusdt": "BNB", "xrpusdt": "XRP",
    "solusdt": "SOL", "adausdt": "ADA", "dogeusdt": "DOGE", "trxusdt": "TRX",
    "avaxusdt": "AVAX", "dotusdt": "DOT", "linkusdt": "LINK", "maticusdt": "POL",
    "ltcusdt": "LTC", "bchusdt": "BCH", "atomusdt": "ATOM", "uniusdt": "UNI",
    "xlmusdt": "XLM", "etcusdt": "ETC", "filusdt": "FIL", "aptusdt": "APT",
    "nearusdt": "NEAR", "injusdt": "INJ", "opusdt": "OP", "arbusdt": "ARB",
    "suiusdt": "SUI", "seiusdt": "SEI", "fetusdt": "FET", "rndrusdt": "RNDR",
    "aaveusdt": "AAVE", "shibusdt": "SHIB", "pepeusdt": "PEPE", "tonusdt": "TON",
    "hbarusdt": "HBAR", "icpusdt": "ICP", "stxusdt": "STX", "imxusdt": "IMX",
    "taousdt": "TAO", "kasusdt": "KAS", "ondousdt": "ONDO", "jupusdt": "JUP",
    "enausdt": "ENA", "wldusdt": "WLD", "tiausdt": "TIA", "pythusdt": "PYTH",
    "grtusdt": "GRT", "algousdt": "ALGO", "vetusdt": "VET", "ftmusdt": "FTM",
    "sandusdt": "SAND", "manausdt": "MANA", "axsusdt": "AXS", "galausdt": "GALA",
    "ldousdt": "LDO", "mkrusdt": "MKR", "snxusdt": "SNX", "crvusdt": "CRV",
    "compusdt": "COMP", "1inchusdt": "1INCH", "enjusdt": "ENJ", "chzusdt": "CHZ",
    "flowusdt": "FLOW", "minausdt": "MINA", "eosusdt": "EOS", "xtzusdt": "XTZ",
    "neousdt": "NEO", "zecusdt": "ZEC", "dashusdt": "DASH", "iotausdt": "IOTA",
    "xmrusdt": "XMR", "bsvusdt": "BSV", "thetausdt": "THETA", "klayusdt": "KLAY",
    "egldusdt": "EGLD", "qntusdt": "QNT", "runeusdt": "RUNE", "kavausdt": "KAVA",
    "cfxusdt": "CFX", "apeusdt": "APE", "gmxusdt": "GMX", "wusdt": "W",
    "strkusdt": "STRK", "mantausdt": "MANTA", "dydxusdt": "DYDX", "pendleusdt": "PENDLE",
    "blurusdt": "BLUR", "magicusdt": "MAGIC", "agixusdt": "AGIX", "oceanusdt": "OCEAN",
    "flokiusdt": "FLOKI", "bonkusdt": "BONK", "wifusdt": "WIF", "memeusdt": "MEME",
    "ordiusdt": "ORDI", "satsusdt": "SATS", "jtousdt": "JTO", "zkusdt": "ZK",
    "usdtusdt": "USDT",
}


async def fetch_coingecko():
    """CoinGecko'dan 1000 coin çek"""
    global prices_data
    
    all_coins = []
    
    async with httpx.AsyncClient(timeout=30) as client:
        for page in [1, 2, 3, 4]:  # 4 sayfa = 1000 coin
            try:
                resp = await client.get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "order": "market_cap_desc",
                        "per_page": 250,
                        "page": page,
                        "sparkline": "false",
                        "price_change_percentage": "24h,7d,30d"
                    }
                )
                
                if resp.status_code == 200:
                    all_coins.extend(resp.json())
                elif resp.status_code == 429:
                    print(f"[CoinGecko] Rate limited, waiting...")
                    await asyncio.sleep(60)
                
                await asyncio.sleep(1.5)  # Rate limit
                
            except Exception as e:
                print(f"[CoinGecko] Page {page} error: {e}")
    
    # Önce ID'ye göre işle (öncelikli coinler)
    processed_symbols = set()
    
    for c in all_coins:
        coin_id = c["id"]
        symbol = c["symbol"].upper()
        
        # Öncelikli coin mi? (ID eşleşmesi)
        if coin_id in PRIORITY_COINS:
            correct_symbol = PRIORITY_COINS[coin_id]
            processed_symbols.add(correct_symbol)
            
            # WS varsa sadece metadata güncelle
            if correct_symbol in prices_data and prices_data[correct_symbol].get("source") == "binance_ws":
                prices_data[correct_symbol].update({
                    "id": coin_id,
                    "name": c["name"],
                    "rank": c.get("market_cap_rank", 999),
                    "market_cap": c.get("market_cap") or 0,
                    "change_7d": c.get("price_change_percentage_7d_in_currency") or 0,
                    "change_30d": c.get("price_change_percentage_30d_in_currency") or 0,
                    "ath": c.get("ath") or 0,
                    "ath_change_percentage": c.get("ath_change_percentage") or 0,
                    "image": c.get("image", ""),
                })
            else:
                prices_data[correct_symbol] = {
                    "id": coin_id,
                    "name": c["name"],
                    "symbol": correct_symbol,
                    "rank": c.get("market_cap_rank", 999),
                    "price": c["current_price"] or 0,
                    "change_24h": c.get("price_change_percentage_24h") or 0,
                    "change_7d": c.get("price_change_percentage_7d_in_currency") or 0,
                    "change_30d": c.get("price_change_percentage_30d_in_currency") or 0,
                    "market_cap": c.get("market_cap") or 0,
                    "volume_24h": c.get("total_volume") or 0,
                    "high_24h": c.get("high_24h") or 0,
                    "low_24h": c.get("low_24h") or 0,
                    "ath": c.get("ath") or 0,
                    "ath_change_percentage": c.get("ath_change_percentage") or 0,
                    "circulating_supply": c.get("circulating_supply") or 0,
                    "total_supply": c.get("total_supply") or 0,
                    "image": c.get("image", ""),
                    "source": "coingecko",
                    "updated_at": datetime.utcnow().isoformat(),
                }
    
    # Sonra diğer coinleri ekle (öncelikli olmayanlar)
    for c in all_coins:
        coin_id = c["id"]
        symbol = c["symbol"].upper()
        
        # Zaten işlendiyse atla
        if symbol in processed_symbols:
            continue
        
        # Öncelikli coin listesinde farklı ID ile varsa atla (yanlış coin)
        if symbol in SYMBOL_TO_ID:
            continue
            
        # WS source varsa sadece metadata güncelle
        if symbol in prices_data and prices_data[symbol].get("source") == "binance_ws":
            prices_data[symbol].update({
                "id": coin_id,
                "name": c["name"],
                "rank": c.get("market_cap_rank", 999),
                "market_cap": c.get("market_cap") or 0,
                "change_7d": c.get("price_change_percentage_7d_in_currency") or 0,
                "change_30d": c.get("price_change_percentage_30d_in_currency") or 0,
                "ath": c.get("ath") or 0,
                "ath_change_percentage": c.get("ath_change_percentage") or 0,
                "image": c.get("image", ""),
            })
            processed_symbols.add(symbol)
        elif symbol not in prices_data:
            prices_data[symbol] = {
                "id": coin_id,
                "name": c["name"],
                "symbol": symbol,
                "rank": c.get("market_cap_rank", 999),
                "price": c["current_price"] or 0,
                "change_24h": c.get("price_change_percentage_24h") or 0,
                "change_7d": c.get("price_change_percentage_7d_in_currency") or 0,
                "change_30d": c.get("price_change_percentage_30d_in_currency") or 0,
                "market_cap": c.get("market_cap") or 0,
                "volume_24h": c.get("total_volume") or 0,
                "high_24h": c.get("high_24h") or 0,
                "low_24h": c.get("low_24h") or 0,
                "ath": c.get("ath") or 0,
                "ath_change_percentage": c.get("ath_change_percentage") or 0,
                "circulating_supply": c.get("circulating_supply") or 0,
                "total_supply": c.get("total_supply") or 0,
                "image": c.get("image", ""),
                "source": "coingecko",
                "updated_at": datetime.utcnow().isoformat(),
            }
            processed_symbols.add(symbol)
    
    print(f"[CoinGecko] Loaded {len(all_coins)} coins, total: {len(prices_data)}")


async def coingecko_loop():
    """CoinGecko loop - 5 dakikada bir"""
    while True:
        await fetch_coingecko()
        await asyncio.sleep(COINGECKO_INTERVAL)


async def binance_ws():
    """Binance WebSocket - Top 100 real-time"""
    global prices_data, ws_connected
    
    streams = [f"{s}@ticker" for s in BINANCE_TOP100.keys()]
    url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
    
    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                ws_connected = True
                print(f"[Binance WS] Connected - {len(BINANCE_TOP100)} coins real-time")
                
                async for msg in ws:
                    try:
                        data = json.loads(msg)
                        if "data" in data:
                            d = data["data"]
                            ws_symbol = d.get("s", "").lower()
                            
                            # Find symbol
                            symbol = None
                            for k, v in BINANCE_TOP100.items():
                                if k == ws_symbol or k.replace("usdt", "") == ws_symbol.replace("usdt", ""):
                                    symbol = v
                                    break
                            
                            if symbol:
                                new_price = float(d.get("c", 0))
                                old_price = prices_data.get(symbol, {}).get("price", new_price)
                                
                                # Instant change calculation
                                change_instant = 0
                                if old_price > 0 and new_price > 0:
                                    change_instant = ((new_price - old_price) / old_price * 100)
                                
                                # Update or create
                                if symbol in prices_data:
                                    prices_data[symbol].update({
                                        "price": new_price,
                                        "change_24h": float(d.get("P", 0)),
                                        "change_instant": round(change_instant, 4),
                                        "high_24h": float(d.get("h", 0)),
                                        "low_24h": float(d.get("l", 0)),
                                        "volume_24h": float(d.get("q", 0)),
                                        "bid": float(d.get("b", 0)),
                                        "ask": float(d.get("a", 0)),
                                        "trades_24h": int(d.get("n", 0)),
                                        "source": "binance_ws",
                                        "updated_at": datetime.utcnow().isoformat(),
                                    })
                                else:
                                    prices_data[symbol] = {
                                        "symbol": symbol,
                                        "price": new_price,
                                        "change_24h": float(d.get("P", 0)),
                                        "change_instant": round(change_instant, 4),
                                        "high_24h": float(d.get("h", 0)),
                                        "low_24h": float(d.get("l", 0)),
                                        "volume_24h": float(d.get("q", 0)),
                                        "source": "binance_ws",
                                        "updated_at": datetime.utcnow().isoformat(),
                                    }
                    except:
                        pass
                        
        except Exception as e:
            ws_connected = False
            print(f"[Binance WS] Error: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)


async def redis_sync():
    """Redis'e her saniye sync"""
    while True:
        try:
            if prices_data:
                r.set("prices_data", json.dumps(prices_data))
                r.set("prices_updated", datetime.utcnow().isoformat())
                r.set("prices_count", len(prices_data))
                
                # WS status
                ws_coins = sum(1 for p in prices_data.values() if p.get("source") == "binance_ws")
                r.set("prices_ws_count", ws_coins)
                
        except Exception as e:
            print(f"[Redis] Error: {e}")
        
        await asyncio.sleep(REDIS_SYNC_INTERVAL)


async def cleanup():
    """Her saat eski news temizle"""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        
        try:
            news_data = r.get("news_db")
            if news_data:
                news = json.loads(news_data)
                cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
                
                cleaned = {k: v for k, v in news.items() 
                          if v.get("crawled_at", "") > cutoff}
                
                removed = len(news) - len(cleaned)
                if removed > 0:
                    r.set("news_db", json.dumps(cleaned))
                    print(f"[Cleanup] Removed {removed} old news, kept {len(cleaned)}")
        except Exception as e:
            print(f"[Cleanup] Error: {e}")


async def status_printer():
    """Durum yazdır - her 30 saniye"""
    while True:
        await asyncio.sleep(30)
        
        ws_coins = sum(1 for p in prices_data.values() if p.get("source") == "binance_ws")
        cg_coins = sum(1 for p in prices_data.values() if p.get("source") == "coingecko")
        
        btc = prices_data.get("BTC", {})
        eth = prices_data.get("ETH", {})
        rndr = prices_data.get("RNDR", {})
        
        print(f"[Status] Total: {len(prices_data)} | WS: {ws_coins} | CG: {cg_coins} | "
              f"BTC: ${btc.get('price', 0):,.0f} ({btc.get('change_24h', 0):+.1f}%) | "
              f"ETH: ${eth.get('price', 0):,.0f} | RNDR: ${rndr.get('price', 0):.2f}")


async def main():
    print(f"[Prices] CoinGecko interval: {COINGECKO_INTERVAL}s")
    print(f"[Prices] Redis sync: {REDIS_SYNC_INTERVAL}s")
    print(f"[Prices] WebSocket coins: {len(BINANCE_TOP100)}")
    print(f"[Prices] Priority coins: {len(PRIORITY_COINS)}")
    
    # Initial load
    await fetch_coingecko()
    
    # Run all tasks
    await asyncio.gather(
        coingecko_loop(),
        binance_ws(),
        redis_sync(),
        cleanup(),
        status_printer(),
    )


if __name__ == "__main__":
    asyncio.run(main())