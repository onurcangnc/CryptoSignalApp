# 🚀 CryptoSignal Deployment Guide

## ✅ Yapılan Son Değişiklikler

### 1. **Premium Navigation Button** ⭐
- Free kullanıcılara Premium butonu eklendi
- Gradient stil (yellow→orange) ile dikkat çekici tasarım
- Desktop ve mobile responsive

### 2. **Signal Stats Widget** 🎯
- Dashboard'a AI sinyal doğruluğu widget'ı
- Signals sayfasına detaylı performans kartları
- Backend endpoint: `/api/signal-stats?days=30`
- Success rate, profitable/total, avg profit gösterimi

### 3. **WebSocket Real-Time Updates** ⚡
- Polling (2000ms) yerine WebSocket kullanımı
- Anlık fiyat güncellemeleri
- Automatic reconnection with exponential backoff
- Fallback: WebSocket kapanırsa polling devreye girer

### 4. **Mevcut Worker Yapısı** 📦
- Sinyal üretimi `services/analysis_service.py` ile sağlanıyor
- Haber toplama `worker_news.py` ile yapılıyor (100+ kaynak)
- AI analizi `worker_ai_analyst.py` ile gerçekleşiyor

---

## 📋 Deployment Checklist

### Backend Deployment

```bash
# 1. Servera bağlan
ssh your-server

# 2. Backend dizinine git
cd /opt/cryptosignal-app/backend

# 3. Git pull
git pull origin main

# 4. Backend'i restart et
sudo ./restart.sh
```

### Frontend Deployment

```bash
# 1. Local'de build et
cd /Users/onurcangenc/Documents/Projects/CryptoSignalApp/frontend
npm run build

# 2. Build'i servera kopyala
scp -r build/* your-server:/opt/cryptosignal-app/frontend/build/

# 3. Nginx restart (serverde)
ssh your-server
sudo systemctl restart cryptosignal-frontend
```

---

## 🔍 Verification

### 1. Tüm Servisleri Kontrol Et

```bash
sudo ./status.sh
```

**Beklenen Çıktı:**
```
📦 Core:
  ✅ redis-server (45MB)

⚙️ Workers:
  ✅ cryptosignal-prices (89MB)
  ✅ cryptosignal-futures (67MB)
  ✅ cryptosignal-news (72MB)
  ✅ cryptosignal-sentiment (98MB)
  ✅ cryptosignal-ai-analyst (156MB)
  ✅ cryptosignal-signal-checker (78MB)
  ✅ cryptosignal-telegram (82MB)

🌐 Application:
  ✅ cryptosignal-backend (234MB)
  ✅ cryptosignal-frontend
```

### 2. WebSocket Test

```bash
# Backend log'larını izle
sudo journalctl -u cryptosignal-backend -f

# Beklenen log:
# [WS] Price broadcast loop started
# [WS] +1 (1 total)  ← Frontend bağlandı
```

### 3. Frontend Test

Tarayıcıda konsolu aç ve şunları kontrol et:

```
✅ [WS] Connected
✅ Signal Stats widget görünüyor (Dashboard)
✅ Signal Performance kartları görünüyor (Signals)
✅ Premium butonu görünüyor (free kullanıcılar için)
✅ Fiyatlar real-time güncelleniyor
```

---

## 📊 Sistemdeki Tüm Worker'lar

| # | Worker | Port | Güncelleme | Açıklama |
|---|--------|------|------------|----------|
| 1 | redis-server | 6379 | - | Core cache |
| 2 | cryptosignal-backend | 8000 | - | FastAPI + WebSocket |
| 3 | cryptosignal-frontend | 3000 | - | Nginx static server |
| 4 | **worker_prices** | - | 30s | CoinGecko fiyatları |
| 5 | **worker_futures** | - | 60s | Binance futures |
| 6 | **worker_news** | - | 5dk | 100+ kaynak haber + AI özetleme |
| 7 | **worker_sentiment** | - | 15dk | Reddit/Twitter |
| 8 | **worker_ai_analyst** | - | Sürekli | AI analiz + sinyal üretimi |
| 9 | **worker_signal_checker** | - | 60dk | Sinyal performans tracking |
| 10 | **worker_telegram** | - | Sürekli | Telegram bot |

---

## 🆕 Yeni Endpoint'ler

### Signal Stats API

```bash
# GET /api/signal-stats?days=30
curl http://localhost:8000/api/signal-stats?days=30
```

**Response:**
```json
{
  "total": 45,
  "profitable": 32,
  "success_rate": 71.1,
  "avg_profit_pct": 8.3,
  "avg_loss_pct": -4.2
}
```

### WebSocket API

```javascript
// ws://localhost:8000/ws
const ws = new WebSocket('ws://localhost:8000/ws')

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)

  if (data.type === 'init') {
    // İlk bağlantı - tüm fiyatlar
    console.log('Prices:', data.prices)
  } else if (data.type === 'price_update') {
    // Real-time güncellemeler (2s)
    console.log('Updated prices:', data.prices)
  }
}
```

---

## ⚠️ Troubleshooting

### WebSocket Bağlanamıyor

```bash
# Backend'de WebSocket döngüsü çalışıyor mu?
sudo journalctl -u cryptosignal-backend | grep "WS"

# Firewall kontrolü
sudo ufw allow 8000/tcp
```

### Signal Stats Gözükmüyor

```bash
# Signal checker çalışıyor mu?
sudo systemctl status cryptosignal-signal-checker

# Redis'te veri var mı?
redis-cli -a "3f9af2788cb89aa74c06bd48dd290658" GET signal_stats
```

---

## 📈 Performance Monitoring

```bash
# CPU ve Memory kullanımı
sudo systemctl status cryptosignal-* | grep "Memory\|CPU"

# WebSocket client sayısı
curl http://localhost:8000/api/health

# Redis key sayısı
redis-cli -a "3f9af2788cb89aa74c06bd48dd290658" DBSIZE
```

---

## 🎉 Deployment Complete!

Tüm adımları tamamladıktan sonra:

1. ✅ 7 worker + 1 backend + 1 frontend = **9 servis aktif**
2. ✅ WebSocket real-time güncellemeler
3. ✅ Signal stats Dashboard ve Signals'da
4. ✅ Premium button navigation'da

**Başarıyla deploy edildi!** 🚀