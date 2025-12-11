#!/usr/bin/env python3
"""
CryptoSignal AI Analyst Worker v3.0
- Günlük tüm coinler için AI analizi
- 5 zaman dilimi: 1G, 1H, 3A, 6A, 1Y
- Profesyonel kripto analist perspektifi
- Basit Türkçe açıklamalar
- Haber özetleme
"""

import json
import time
import redis
import requests
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3

# Config
REDIS_PASS = "3f9af2788cb89aa74c06bd48dd290658"
DB_PATH = "/opt/cryptosignal-app/backend/cryptosignal.db"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Redis connection
r = redis.Redis(host='localhost', port=6379, password=REDIS_PASS, decode_responses=True)

# OpenAI API
def call_openai(messages: list, max_tokens: int = 2000, temperature: float = 0.7) -> Optional[str]:
    """OpenAI API çağrısı"""
    if not OPENAI_API_KEY:
        print("[AI] No API key!")
        return None
    
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=60
        )
        
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            print(f"[AI] Error: {resp.status_code} - {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"[AI] Exception: {e}")
        return None

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

# Import signal tracking
from database import save_signal_track

# ============================================
# HABER ÖZETLEME
# ============================================

def summarize_news_batch(news_list: List[dict]) -> List[dict]:
    """Haberleri AI ile özetle"""
    if not news_list:
        return []
    
    # Batch halinde özetle (maliyet optimizasyonu)
    news_texts = []
    for i, news in enumerate(news_list[:20]):  # Max 20 haber
        news_texts.append(f"{i+1}. {news.get('title', '')}: {news.get('content', '')[:300]}")
    
    prompt = f"""Aşağıdaki kripto para haberlerini Türkçe olarak özetle. Her haber için:
1. Maksimum 2 cümle özet
2. Etkilenen coinler
3. Piyasa etkisi (pozitif/negatif/nötr)

Haberler:
{chr(10).join(news_texts)}

JSON formatında yanıt ver:
[{{"id": 1, "summary_tr": "...", "coins": ["BTC"], "impact": "pozitif"}}]"""

    result = call_openai([
        {"role": "system", "content": "Sen kripto para uzmanı bir editörsün. Haberleri kısa ve öz şekilde Türkçe özetlersin."},
        {"role": "user", "content": prompt}
    ], max_tokens=2000)
    
    if result:
        try:
            # JSON parse
            json_str = result
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                json_str = result.split("```")[1].split("```")[0]
            
            summaries = json.loads(json_str.strip())
            
            # Haberlere özet ekle
            for i, news in enumerate(news_list[:20]):
                if i < len(summaries):
                    news['ai_summary_tr'] = summaries[i].get('summary_tr', '')
                    news['ai_impact'] = summaries[i].get('impact', 'nötr')
            
            return news_list
        except Exception as e:
            print(f"[AI] JSON parse error: {e}")
    
    return news_list

# ============================================
# COİN ANALİZİ
# ============================================

def analyze_coin_ai(symbol: str, coin_data: dict, news_list: List[dict], futures_data: dict, fear_greed: dict) -> dict:
    """Tek bir coin için kapsamlı AI analizi"""
    
    price = coin_data.get('price', 0)
    change_24h = coin_data.get('change_24h', 0)
    change_7d = coin_data.get('change_7d', 0)
    volume = coin_data.get('volume', 0)
    market_cap = coin_data.get('market_cap', 0)
    
    # Futures verisi
    fut = futures_data.get(symbol, {})
    funding_rate = fut.get('funding_rate', 0)
    ls_ratio = fut.get('long_short_ratio', 1)
    
    # İlgili haberler
    coin_news = [n for n in news_list if symbol in n.get('coins', []) or symbol.lower() in str(n.get('title', '')).lower()][:5]
    news_summary = "\n".join([f"- {n.get('title', '')[:80]}" for n in coin_news]) if coin_news else "Son 24 saatte önemli haber yok."
    
    # Fear & Greed
    fg_value = fear_greed.get('value', 50)
    fg_class = fear_greed.get('classification', 'Neutral')
    
    prompt = f"""Sen dünyaca ünlü bir kripto para analistisin. {symbol} için kapsamlı analiz yap.

## MEVCUT VERİLER:
- Fiyat: ${price:,.2f}
- 24s Değişim: {change_24h:+.2f}%
- 7g Değişim: {change_7d:+.2f}%
- Hacim (24s): ${volume:,.0f}
- Piyasa Değeri: ${market_cap:,.0f}
- Fear & Greed Index: {fg_value} ({fg_class})
- Funding Rate: {funding_rate:.4f}%
- Long/Short Oranı: {ls_ratio:.2f}

## SON HABERLER:
{news_summary}

## GÖREV:
5 farklı zaman dilimi için analiz yap. Her analizde:
1. Sinyal (GÜÇLÜ AL / AL / BEKLE / SAT / GÜÇLÜ SAT)
2. Güven oranı (0-100)
3. Hedef fiyat
4. Stop loss seviyesi
5. Basit Türkçe açıklama (teknik terim kullanma, herkesin anlayacağı dilde)

JSON formatında yanıt ver:
{{
  "symbol": "{symbol}",
  "current_price": {price},
  "overall_sentiment": "pozitif/negatif/nötr",
  "risk_level": "düşük/orta/yüksek",
  "news_impact": "özet açıklama",
  "timeframes": {{
    "1d": {{
      "signal": "AL/SAT/BEKLE",
      "signal_tr": "AL/SAT/BEKLE",
      "confidence": 75,
      "target_price": 0,
      "stop_loss": 0,
      "explanation": "Basit açıklama..."
    }},
    "1w": {{ ... }},
    "3m": {{ ... }},
    "6m": {{ ... }},
    "1y": {{ ... }}
  }},
  "simple_summary": "Herkesin anlayacağı 2-3 cümlelik genel değerlendirme"
}}"""

    result = call_openai([
        {"role": "system", "content": "Sen 20 yıllık deneyime sahip profesyonel bir kripto para analistisin. Analizlerini hem uzmanlar hem de yeni başlayanlar anlayabilecek şekilde sunarsın. Türkçe yanıt ver."},
        {"role": "user", "content": prompt}
    ], max_tokens=1500, temperature=0.5)
    
    if result:
        try:
            json_str = result
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                json_str = result.split("```")[1].split("```")[0]
            
            analysis = json.loads(json_str.strip())
            analysis['analyzed_at'] = datetime.utcnow().isoformat()
            analysis['news_count'] = len(coin_news)

            # Sinyalleri tracking tablosuna kaydet
            try:
                timeframes = analysis.get('timeframes', {})
                for tf, tf_data in timeframes.items():
                    signal = tf_data.get('signal', 'BEKLE')
                    signal_tr = tf_data.get('signal_tr', 'BEKLE')
                    confidence = tf_data.get('confidence', 50)
                    target = tf_data.get('target_price', 0)
                    stop = tf_data.get('stop_loss', 0)

                    if signal and target > 0 and stop > 0:
                        save_signal_track(
                            symbol=symbol,
                            signal=signal,
                            signal_tr=signal_tr,
                            confidence=confidence,
                            entry_price=price,
                            target_price=target,
                            stop_loss=stop,
                            timeframe=tf
                        )
            except Exception as track_err:
                print(f"[AI] Signal tracking error for {symbol}: {track_err}")

            return analysis
        except Exception as e:
            print(f"[AI] Parse error for {symbol}: {e}")
    
    # Fallback - basit analiz
    return create_fallback_analysis(symbol, coin_data, fear_greed)

def create_fallback_analysis(symbol: str, coin_data: dict, fear_greed: dict) -> dict:
    """AI başarısız olursa basit analiz"""
    price = coin_data.get('price', 0)
    change_24h = coin_data.get('change_24h', 0)
    fg_value = fear_greed.get('value', 50)
    
    # Basit sinyal hesaplama
    if change_24h < -10 and fg_value < 30:
        signal = "AL"
        confidence = 65
    elif change_24h > 15 and fg_value > 70:
        signal = "SAT"
        confidence = 60
    else:
        signal = "BEKLE"
        confidence = 50
    
    return {
        "symbol": symbol,
        "current_price": price,
        "overall_sentiment": "nötr",
        "risk_level": "orta",
        "news_impact": "Analiz yapılamadı",
        "timeframes": {
            tf: {
                "signal": signal,
                "signal_tr": signal,
                "confidence": confidence,
                "target_price": price * 1.1 if signal == "AL" else price * 0.95,
                "stop_loss": price * 0.95 if signal == "AL" else price * 1.05,
                "explanation": "Otomatik analiz - AI geçici olarak kullanılamıyor"
            } for tf in ["1d", "1w", "3m", "6m", "1y"]
        },
        "simple_summary": "Şu an için net bir yorum yapılamıyor. Piyasayı takip etmeye devam edin.",
        "analyzed_at": datetime.utcnow().isoformat(),
        "news_count": 0,
        "is_fallback": True
    }

# ============================================
# PORTFÖY ANALİZİ
# ============================================

def analyze_portfolio(user_id: str, holdings: List[dict], prices: dict, news_db: dict, futures: dict, fear_greed: dict) -> dict:
    """Kullanıcı portföyü için kişiselleştirilmiş AI analizi"""
    
    if not holdings:
        return {"error": "Portföy boş", "holdings": []}
    
    # Portföy özeti oluştur
    portfolio_summary = []
    total_value = 0
    total_invested = 0
    
    for h in holdings:
        coin = h.get('coin', '')
        qty = h.get('quantity', 0)
        invested = h.get('invested_usd', 0)
        price = prices.get(coin, {}).get('price', 0)
        value = qty * price
        pnl = ((value - invested) / invested * 100) if invested > 0 else 0
        
        total_value += value
        total_invested += invested
        
        portfolio_summary.append({
            "coin": coin,
            "quantity": qty,
            "invested": invested,
            "current_value": value,
            "pnl_percent": pnl,
            "price": price
        })
    
    total_pnl = ((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
    
    # İlgili haberler
    portfolio_coins = [h['coin'] for h in holdings]
    relevant_news = []
    for nid, news in news_db.items():
        news_coins = news.get('coins', [])
        if any(c in news_coins for c in portfolio_coins):
            relevant_news.append(news)
    relevant_news = relevant_news[:10]
    
    news_text = "\n".join([f"- {n.get('title', '')[:80]}" for n in relevant_news]) if relevant_news else "İlgili haber yok"
    
    # Portföy detayları
    holdings_text = "\n".join([
        f"- {p['coin']}: ${p['current_value']:.2f} (Kar/Zarar: {p['pnl_percent']:+.1f}%)"
        for p in portfolio_summary
    ])
    
    fg_value = fear_greed.get('value', 50)
    
    prompt = f"""Sen kişisel kripto para danışmanısın. Kullanıcının portföyünü analiz et.

## PORTFÖY:
{holdings_text}

Toplam Değer: ${total_value:,.2f}
Toplam Yatırım: ${total_invested:,.2f}
Toplam Kar/Zarar: {total_pnl:+.1f}%

## PİYASA DURUMU:
Fear & Greed: {fg_value}

## İLGİLİ HABERLER:
{news_text}

## GÖREV:
Portföyü değerlendir ve şunları sağla:
1. Genel risk değerlendirmesi
2. Her coin için öneri
3. Haber özetleri ve etkileri
4. Somut aksiyon önerileri

ÖNEMLI: Teknik terimler kullanma. Arkadaşına anlatır gibi, samimi ve anlaşılır bir dilde yaz.

JSON formatında yanıt ver:
{{
  "portfolio_health": "sağlıklı/riskli/çok riskli",
  "total_value_usd": {total_value:.2f},
  "total_pnl_percent": {total_pnl:.1f},
  "risk_score": 1-10 arası,
  "general_summary": "2-3 cümle genel değerlendirme",
  "news_summary": "Haberlerin portföye etkisi hakkında özet",
  "coin_analysis": [
    {{
      "coin": "BTC",
      "action": "TUT/AL/AZALT/SAT",
      "reason": "Basit açıklama",
      "risk": "düşük/orta/yüksek"
    }}
  ],
  "recommendations": [
    "Öneri 1",
    "Öneri 2"
  ],
  "warnings": ["Varsa uyarılar"]
}}"""

    result = call_openai([
        {"role": "system", "content": "Sen samimi ve yardımsever bir kripto para danışmanısın. Karmaşık konuları basit anlatırsın. Türkçe yanıt ver."},
        {"role": "user", "content": prompt}
    ], max_tokens=1500, temperature=0.6)
    
    if result:
        try:
            json_str = result
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                json_str = result.split("```")[1].split("```")[0]
            
            analysis = json.loads(json_str.strip())
            analysis['analyzed_at'] = datetime.utcnow().isoformat()
            analysis['holdings'] = portfolio_summary
            analysis['news_count'] = len(relevant_news)
            return analysis
        except Exception as e:
            print(f"[AI] Portfolio parse error: {e}")
    
    # Fallback
    return {
        "portfolio_health": "belirsiz",
        "total_value_usd": total_value,
        "total_pnl_percent": total_pnl,
        "risk_score": 5,
        "general_summary": "Analiz şu an yapılamıyor. Portföyünüz çeşitlendirilmiş görünüyor.",
        "news_summary": f"{len(relevant_news)} ilgili haber bulundu.",
        "coin_analysis": [{"coin": h['coin'], "action": "TUT", "reason": "Analiz yapılamadı", "risk": "orta"} for h in holdings],
        "recommendations": ["Piyasayı takip etmeye devam edin"],
        "warnings": [],
        "analyzed_at": datetime.utcnow().isoformat(),
        "holdings": portfolio_summary,
        "is_fallback": True
    }

# ============================================
# BATCH ANALİZ (TÜM COİNLER)
# ============================================

def run_daily_analysis():
    """Günlük toplu analiz - tüm coinler için"""
    print(f"\n{'='*60}")
    print(f"[AI Analyst] Günlük analiz başlıyor - {datetime.now()}")
    print(f"{'='*60}")
    
    # Verileri yükle
    prices = json.loads(r.get("prices_data") or "{}")
    futures = json.loads(r.get("futures_data") or "{}")
    fear_greed = json.loads(r.get("fear_greed") or "{}")
    news_db = json.loads(r.get("news_db") or "{}")
    
    print(f"[AI] Veriler: {len(prices)} coin, {len(news_db)} haber")
    
    if not OPENAI_API_KEY:
        print("[AI] HATA: OPENAI_API_KEY ayarlanmamış!")
        return
    
    # Coinleri market cap'e göre sırala
    coins_list = []
    for symbol, data in prices.items():
        if data.get('market_cap', 0) > 0:
            coins_list.append({'symbol': symbol, **data})
    
    coins_list = sorted(coins_list, key=lambda x: x.get('market_cap', 0), reverse=True)
    
    # Top 100 coin için analiz (maliyet kontrolü)
    top_coins = coins_list[:100]
    print(f"[AI] Top {len(top_coins)} coin analiz edilecek")
    
    # Haberleri özetle
    news_list = list(news_db.values())
    print(f"[AI] {len(news_list)} haber özetleniyor...")
    summarized_news = summarize_news_batch(news_list)
    
    # Her coin için analiz
    all_analyses = {}
    
    for i, coin in enumerate(top_coins):
        symbol = coin['symbol']
        print(f"[AI] [{i+1}/{len(top_coins)}] {symbol} analiz ediliyor...")
        
        try:
            analysis = analyze_coin_ai(symbol, coin, summarized_news, futures, fear_greed)
            all_analyses[symbol] = analysis
            
            # Rate limiting
            time.sleep(1)  # API rate limit için bekle
            
        except Exception as e:
            print(f"[AI] {symbol} hatası: {e}")
            all_analyses[symbol] = create_fallback_analysis(symbol, coin, fear_greed)
        
        # Her 10 coinde bir kaydet (güvenlik için)
        if (i + 1) % 10 == 0:
            r.set("ai_signals", json.dumps(all_analyses))
            print(f"[AI] {i+1} coin kaydedildi")
    
    # Final kayıt
    r.set("ai_signals", json.dumps(all_analyses))
    r.set("ai_signals_updated", datetime.utcnow().isoformat())
    r.set("ai_signals_count", len(all_analyses))
    
    # Özetlenmiş haberleri de kaydet
    r.set("news_summarized", json.dumps({n.get('id', ''): n for n in summarized_news}))
    
    print(f"\n[AI] ✅ Analiz tamamlandı: {len(all_analyses)} coin")
    print(f"[AI] Sonraki analiz: 24 saat sonra")

def run_portfolio_analysis_all():
    """Tüm kullanıcıların portföylerini analiz et"""
    print(f"\n[AI] Portföy analizleri başlıyor...")
    
    prices = json.loads(r.get("prices_data") or "{}")
    futures = json.loads(r.get("futures_data") or "{}")
    fear_greed = json.loads(r.get("fear_greed") or "{}")
    news_db = json.loads(r.get("news_db") or "{}")
    
    conn = get_db()
    users = conn.execute("SELECT id FROM users").fetchall()
    
    for user in users:
        user_id = user['id']
        
        # Portföyü al
        portfolio_row = conn.execute("SELECT holdings FROM portfolios WHERE user_id = ?", (user_id,)).fetchone()
        
        if portfolio_row and portfolio_row['holdings']:
            try:
                data = json.loads(portfolio_row['holdings'])
                holdings = data.get('holdings', []) if isinstance(data, dict) else data
                
                if holdings:
                    print(f"[AI] Portföy analizi: {user_id[:8]}... ({len(holdings)} varlık)")
                    
                    analysis = analyze_portfolio(user_id, holdings, prices, news_db, futures, fear_greed)
                    
                    # Kullanıcıya özel kaydet
                    r.set(f"portfolio_analysis:{user_id}", json.dumps(analysis))
                    
                    time.sleep(1)  # Rate limit
                    
            except Exception as e:
                print(f"[AI] Portföy hatası {user_id[:8]}: {e}")
    
    conn.close()
    print(f"[AI] ✅ Portföy analizleri tamamlandı")

# ============================================
# MAIN LOOP
# ============================================

def main():
    print("="*60)
    print("CryptoSignal AI Analyst Worker v3.0")
    print("="*60)
    
    if not OPENAI_API_KEY:
        print("\n⚠️  UYARI: OPENAI_API_KEY ayarlanmamış!")
        print("Şu komutu çalıştırın:")
        print("echo 'OPENAI_API_KEY=sk-xxx' > /opt/cryptosignal-app/backend/.env")
        print("\nWorker fallback modunda çalışacak...\n")
    
    # İlk çalıştırmada hemen analiz yap
    last_analysis = r.get("ai_signals_updated")
    
    if not last_analysis:
        print("[AI] İlk analiz yapılıyor...")
        run_daily_analysis()
        run_portfolio_analysis_all()
    else:
        # Son analizden bu yana geçen süre
        try:
            last_time = datetime.fromisoformat(last_analysis)
            hours_passed = (datetime.utcnow() - last_time).total_seconds() / 3600
            print(f"[AI] Son analiz: {hours_passed:.1f} saat önce")
            
            if hours_passed >= 24:
                run_daily_analysis()
                run_portfolio_analysis_all()
        except:
            run_daily_analysis()
    
    # Her gün 09:00 UTC'de çalış
    while True:
        now = datetime.utcnow()
        
        # Sonraki 09:00'ı hesapla
        next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now.hour >= 9:
            next_run += timedelta(days=1)
        
        wait_seconds = (next_run - now).total_seconds()
        print(f"[AI] Sonraki analiz: {next_run} ({wait_seconds/3600:.1f} saat sonra)")
        
        # Bekle (her saat kontrol et)
        while wait_seconds > 0:
            sleep_time = min(3600, wait_seconds)
            time.sleep(sleep_time)
            wait_seconds -= sleep_time
            
            # Yeni portföy eklendiyse anlık analiz için kontrol
            # (Bu kısım isteğe bağlı - API maliyetini artırır)
        
        # Günlük analiz
        run_daily_analysis()
        run_portfolio_analysis_all()

if __name__ == "__main__":
    main()