# 🚀 CryptoSignal AI - Yapay Zeka Destekli Kripto Para Sinyal Platformu

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.0+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

> AI destekli gerçek zamanlı kripto para analiz ve sinyal platformu. Bitcoin, Ethereum ve 1000+ coin için profesyonel trading sinyalleri, sentiment analizi ve portföy yönetimi.

## 📋 İçindekiler

- [Genel Bakış](#-genel-bakış)
- [Yazılım Mimarisi](#-yazılım-mimarisi)
- [Tasarım Desenleri](#-tasarım-desenleri)
- [Teknoloji Stack](#-teknoloji-stack)
- [Özellikler](#-özellikler)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [API Dokümantasyonu](#-api-dokümantasyonu)
- [Worker Servisleri](#-worker-servisleri)
- [Deployment](#-deployment)
- [Katkıda Bulunma](#-katkıda-bulunma)

---

## 🎯 Genel Bakış

CryptoSignal AI, **mikroservis mimarisinde** tasarlanmış, yapay zeka destekli bir kripto para analiz platformudur. Platform, 8 bağımsız worker servisi ile gerçek zamanlı piyasa verilerini işler ve kullanıcılara actionable trading sinyalleri sunar.

### Temel Bileşenler

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   React SPA  │  │  Landing Page│  │  Blog Pages  │     │
│  │ (Dashboard)  │  │    (SEO)     │  │   (Static)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        FastAPI Backend (main.py)                     │  │
│  │  REST API + WebSocket + Authentication + CORS       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Routers    │  │  Services   │  │Dependencies │        │
│  │  (REST)     │  │  (Business) │  │  (DI)       │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     WORKER SERVICES LAYER                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Prices  │ │ Sentiment│ │   News   │ │ Futures  │      │
│  │  Worker  │ │  Worker  │ │  Worker  │ │  Worker  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │   AI     │ │  Signal  │ │ Telegram │ │ Telegram │      │
│  │ Analyst  │ │ Checker  │ │  Worker  │ │  Admin   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA PERSISTENCE LAYER                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  SQLite DB  │  │   Redis     │  │  External   │        │
│  │  (Primary)  │  │  (Cache)    │  │   APIs      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Yazılım Mimarisi

### Mimari Yaklaşım: **Distributed Monolith (Hybrid Architecture)**

Platform, **N-Tier Monolitik** temel yapı üzerine **Mikroservis benzeri Worker Servisleri** eklenmiş hibrit bir mimari kullanır.

#### Mimari Sınıflandırma

| Özellik | Bu Sistem | Gerçek Mikroservis |
|---------|-----------|-------------------|
| **Veritabanı** | Paylaşımlı SQLite + Redis | Servis başına ayrı DB |
| **İletişim** | Shared State (Redis) | API/Message Queue |
| **Deployment** | Bağımsız systemd servisleri | Container orchestration |
| **Ölçeklenebilirlik** | Worker bazlı | Servis bazlı |
| **Kod Tabanı** | Monorepo | Servis başına repo |

#### Katmanlı Mimari (N-Tier)

```
┌─────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                         │
│              React SPA + Landing Pages                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│         FastAPI (REST API + WebSocket + Auth)               │
│    ┌─────────────────────────────────────────────────┐      │
│    │  Routers → Services → Dependencies (DI)         │      │
│    └─────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 BACKGROUND WORKERS LAYER                     │
│   Bağımsız Python prosesleri (systemd managed)              │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐              │
│   │ Prices │ │Signals │ │  AI    │ │Telegram│              │
│   └────────┘ └────────┘ └────────┘ └────────┘              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  DATA PERSISTENCE LAYER                      │
│        SQLite (Persistent) + Redis (Cache/State)            │
└─────────────────────────────────────────────────────────────┘
```

#### Worker İletişim Modeli

```
worker_prices ──────┐
                    ├──→ Redis (Shared State) ──→ FastAPI ──→ Clients
worker_ai_analyst ──┤         ↓
                    │      SQLite
worker_signal_checker ──────────────────────────────────↑
```

**Neden Tam Mikroservis Değil:**
- Tüm worker'lar aynı SQLite ve Redis'i paylaşır
- Servisler arası API kontratı yok
- Implicit ordering dependency (prices → signals → checker)
- Single point of failure: Redis

**Neden Tam Monolitik Değil:**
- Her worker bağımsız process olarak çalışır
- Ayrı systemd servisleri ile yönetilir
- Bağımsız scale edilebilir
- Eventually consistent data flow

---

## 🎨 Tasarım Desenleri (GoF 23 Pattern Analysis)

Kod tabanında tespit edilen Gang of Four tasarım desenleri:

### Creational Patterns (Yaratımsal)

#### 1. **Singleton Pattern**
**Kullanım Yeri:** `LLMService`, `AnalysisService`, `RedisClient`

Uygulama boyunca tek instance kullanılır. Pahalı kaynakların (API bağlantıları, DB connection pool) tekrar tekrar oluşturulmasını engeller.

- `llm_service = LLMService()` → Tüm modül bu instance'ı kullanır
- `analysis_service = AnalysisService()` → Tek analiz servisi
- Redis connection pool → Lazy singleton

#### 2. **Factory Method Pattern**
**Kullanım Yeri:** Signal Generation, Empty State Components

Farklı türde nesneler üretmek için fabrika metotları kullanılır.

- `generate_signal(coin, timeframe)` → Timeframe'e göre farklı sinyal nesnesi
- `EmptyState` component → `type` parametresine göre farklı UI üretir
- Skeleton loader variants → Her sayfa için özelleştirilmiş skeleton

#### 3. **Lazy Initialization (Virtual Proxy)**
**Kullanım Yeri:** `RedisClientProxy` in database.py

Redis bağlantısı ilk kullanımda oluşturulur, uygulama başlangıcında değil. Startup süresini kısaltır ve gereksiz bağlantı açılmasını engeller.

### Structural Patterns (Yapısal)

#### 4. **Proxy Pattern**
**Kullanım Yeri:** `RedisClientProxy`

Gerçek Redis client'ın önünde durur. Lazy loading, connection pooling ve error handling sağlar. Client kodundan bağımsız olarak bağlantı yönetimi yapılır.

#### 5. **Facade Pattern**
**Kullanım Yeri:** `database.py`, `api.js`

Karmaşık alt sistemleri basit bir arayüz arkasına gizler.

- `database.py` → SQLite + Redis işlemlerini tek modülde birleştirir
- `api.js` (Frontend) → Tüm API çağrılarını merkezi fonksiyonlarla soyutlar
- `LLMService` → OpenAI API karmaşıklığını gizler

#### 6. **Composite Pattern**
**Kullanım Yeri:** React Component Tree, Skeleton Loaders

Parça-bütün hiyerarşisini temsil eder.

- `DashboardSkeleton` → `SkeletonCard` + `SkeletonTable` + `SkeletonChart` birleşimi
- `SignalPerformanceGrid` → 4 farklı card component'inin kompozisyonu
- Page components → Header + Content + Footer kompozisyonu

#### 7. **Decorator Pattern**
**Kullanım Yeri:** FastAPI Dependencies, Route decorators

Nesnelere dinamik olarak sorumluluk ekler.

- `@router.get("/signals")` → Route'a HTTP handler davranışı ekler
- `Depends(get_current_user)` → Endpoint'e auth kontrolü ekler
- `Depends(require_llm_quota)` → Endpoint'e quota kontrolü ekler

### Behavioral Patterns (Davranışsal)

#### 8. **Observer Pattern (Pub/Sub)**
**Kullanım Yeri:** WebSocket Broadcasting, React State

Subject'teki değişiklikler observer'lara bildirilir.

- WebSocket: `broadcast(message)` → Tüm bağlı client'lara mesaj
- React: `useState` + `useEffect` → State değişince UI güncellenir
- Redis: Worker'lar yazar → API okur → Client'lara broadcast

#### 9. **Strategy Pattern**
**Kullanım Yeri:** Signal Generation Algorithms, Analysis Methods

Algoritma ailesini tanımlar ve birbirinin yerine kullanılabilir hale getirir.

- Technical Analysis Strategies: RSI, MACD, Bollinger, MA, EMA
- Backtesting Strategies: RSI Strategy, MACD Strategy, MA Crossover
- Sentiment Analysis: Keyword-based vs AI-based scoring

#### 10. **Template Method Pattern**
**Kullanım Yeri:** Worker Base Structure, API Response Format

Bir algoritmanın iskeletini tanımlar, adımları alt sınıflara bırakır.

- Tüm worker'lar: `while True: process() → sleep()` şablonu
- API responses: `{success, data, error}` şablonu
- Signal cards: Shared layout, farklı data rendering

#### 11. **Command Pattern**
**Kullanım Yeri:** Telegram Bot Commands

İstekleri nesne olarak kapsüller.

- `/start`, `/portfolio`, `/signals` → Her komut ayrı handler
- Komut geçmişi tutulabilir
- Undo/Redo potansiyeli (henüz implemente edilmedi)

#### 12. **State Pattern**
**Kullanım Yeri:** Signal Lifecycle, WebSocket Connection

Nesnenin iç durumu değişince davranışını değiştirir.

- Signal states: `PENDING → ACTIVE → TARGET_HIT | STOP_LOSS`
- WebSocket: `CONNECTING → CONNECTED → DISCONNECTED`
- Loading states: `loading → success | error`

#### 13. **Iterator Pattern**
**Kullanım Yeri:** Pagination, Data Streaming

Koleksiyon elemanlarına sıralı erişim sağlar.

- API pagination: `limit`, `offset` parametreleri
- Coin table: 100 items per page iteration
- News feed: Infinite scroll pattern

#### 14. **Chain of Responsibility**
**Kullanım Yeri:** FastAPI Middleware, Auth Flow

İsteği bir zincir boyunca iletir.

```
Request → CORS → Auth → Rate Limit → Route Handler → Response
```

- Her middleware isteği işleyip bir sonrakine geçirir
- Auth başarısız olursa zincir kırılır (401 response)

#### 15. **Mediator Pattern**
**Kullanım Yeri:** Redis as Central Hub

Nesneler arası iletişimi merkezi bir noktadan yönetir.

- Redis, tüm worker'lar arasında mediator görevi görür
- Worker'lar birbirleriyle doğrudan konuşmaz
- Tüm veri akışı Redis üzerinden geçer

### Frontend-Specific Patterns

#### 16. **Provider Pattern (React Context benzeri)**
**Kullanım Yeri:** App.jsx root state

- `user`, `lang`, `t` (translations) → Tüm component'lere props ile geçer
- Context API kullanılmamış, basit prop drilling tercih edilmiş

#### 17. **Render Props / Callback Pattern**
**Kullanım Yeri:** useWebSocket hook

- `useWebSocket(onMessage)` → Callback ile mesaj işleme
- Parent component state'i yönetir, child callback alır

#### 18. **Container/Presentational Pattern**
**Kullanım Yeri:** Pages vs UI Components

- **Container (Smart):** Dashboard, Signals → Data fetching, state
- **Presentational (Dumb):** SkeletonLoader, EmptyState → Sadece UI

### Pattern Özet Tablosu

| Pattern | Kategori | Kullanım Yeri | Amaç |
|---------|----------|---------------|------|
| Singleton | Creational | LLMService, Redis | Tek instance |
| Factory Method | Creational | Signal/Skeleton generation | Nesne üretimi |
| Lazy Init | Creational | RedisClientProxy | Gecikmeli oluşturma |
| Proxy | Structural | RedisClientProxy | Erişim kontrolü |
| Facade | Structural | database.py, api.js | Basitleştirme |
| Composite | Structural | React components | Hiyerarşi |
| Decorator | Structural | FastAPI Depends | Davranış ekleme |
| Observer | Behavioral | WebSocket, React | Bildirim |
| Strategy | Behavioral | Analysis algorithms | Algoritma değişimi |
| Template | Behavioral | Workers, API format | İskelet tanımlama |
| Command | Behavioral | Telegram commands | İstek kapsülleme |
| State | Behavioral | Signal lifecycle | Durum yönetimi |
| Iterator | Behavioral | Pagination | Sıralı erişim |
| Chain of Resp. | Behavioral | Middleware | İstek zinciri |
| Mediator | Behavioral | Redis hub | Merkezi iletişim |

---

## 💻 Teknoloji Stack

### Backend
| Teknoloji | Versiyon | Kullanım Amacı |
|-----------|----------|----------------|
| Python | 3.9+ | Core language |
| FastAPI | 0.104+ | REST API + WebSocket |
| SQLite | 3.x | Primary database |
| Redis | 7.x | Caching + Pub/Sub |
| Uvicorn | 0.24+ | ASGI server |
| Pydantic | 2.x | Data validation |
| OpenAI API | 1.x | AI analysis |
| python-telegram-bot | 20.x | Telegram notifications |

### Frontend
| Teknoloji | Versiyon | Kullanım Amacı |
|-----------|----------|----------------|
| React | 18.2+ | UI framework |
| Vite | 5.x | Build tool |
| TailwindCSS | 3.x | Styling |
| Recharts | 2.x | Charts |
| Axios | 1.x | HTTP client |
| React Router | 6.x | Routing |

### External APIs
- **CoinGecko API**: Price data (1000+ coins)
- **Binance API**: Futures data
- **CryptoCompare API**: News aggregation
- **OpenAI GPT-4**: AI-powered analysis
- **Telegram Bot API**: User notifications

### Infrastructure
- **Nginx**: Reverse proxy + static file serving
- **systemd**: Service management
- **Let's Encrypt**: SSL/TLS certificates
- **GitHub**: Version control + CI/CD

---

## ✨ Özellikler

### 🎯 Core Features

#### 1. **AI-Powered Signal Generation**
- GPT-4 tabanlı teknik analiz
- Multi-indicator analysis (RSI, MACD, Bollinger Bands)
- Pattern recognition (Head & Shoulders, Double Top/Bottom)
- Sentiment-aware signal adjustment

#### 2. **Real-Time Data Processing**
- WebSocket ile canlı fiyat güncellemeleri
- 1000+ coin için anlık takip
- Futures market analizi
- Volume ve market cap monitoring

#### 3. **Sentiment Analysis**
- News sentiment scoring (-1 to +1)
- Social media trend analysis
- Market fear & greed index
- Keyword-based sentiment extraction

#### 4. **Multi-Channel Notifications**
- Telegram bot integration
- Admin panel için özel kanal
- Real-time signal alerts
- Payment confirmation notifications

#### 5. **User Management**
- JWT-based authentication
- Free vs Premium tiers
- Payment integration (flexible)
- Subscription management

#### 6. **Portfolio Tracking**
- Watchlist management
- Signal history
- Performance metrics
- Profit/loss calculations

### 🔥 Advanced Features

- **AI Analyst**: Günlük piyasa özeti ve stratejik öneriler
- **Futures Signals**: Leverage trading için özel sinyaller
- **News Aggregation**: Coinlere özel haber filtreleme
- **Multi-Language**: TR/EN desteği
- **SEO Optimized**: Landing page + 6 blog articles
- **Mobile Responsive**: Tüm cihazlarda uyumlu
- **Dark Mode**: Modern glassmorphism design

### 📈 Trading Tools

#### 7. **DCA Calculator**
- Dollar Cost Averaging stratejisi hesaplama
- Günlük, haftalık, aylık yatırım aralıkları
- Geçmiş performans simülasyonu
- Görsel grafiklerle sonuç analizi
- ROI ve ortalama maliyet hesaplama

#### 8. **Backtesting Engine**
- Strateji test aracı (RSI, MACD, Moving Average)
- Özelleştirilebilir parametreler
- Win rate, profit factor, max drawdown metrikleri
- Görsel grafik sonuçları
- Entry/exit point analizi

#### 9. **Watchlist Management**
- Kişisel coin takip listesi
- Favorilere hızlı erişim
- Gerçek zamanlı fiyat güncellemeleri
- Özelleştirilebilir görünüm

#### 10. **Price Alerts**
- Özel fiyat bildirimleri
- Üst/alt eşik koşulları
- Çoklu alert desteği
- Telegram entegrasyonu

#### 11. **TradingView Integration**
- Profesyonel grafik widget'ı
- 100+ teknik indikatör
- Çoklu zaman dilimi desteği
- Çizim araçları

### 🎨 UI/UX Features

- **Skeleton Loaders**: Modern loading durumları
- **Empty States**: Bilgilendirici boş durum illüstrasyonları
- **Risk Disclaimers**: Google AdSense uyumlu uyarılar
- **Ad Banner System**: Reklam entegrasyonu
- **Typography Hierarchy**: Tutarlı tipografi sistemi
- **Color Palette**: Amber/Orange temalı renk paleti
- **Animations**: Smooth geçiş animasyonları (fade-in, slide-up, shimmer)
- **Accessibility**: Focus states ve semantic HTML

---

## 🚀 Kurulum

### Gereksinimler

```bash
# System requirements
- Python 3.9+
- Node.js 18+
- Redis 7+
- SQLite 3+
- Git
```

### 1. Repository Clone

```bash
git clone https://github.com/yourusername/CryptoSignalApp.git
cd CryptoSignalApp
```

### 2. Backend Kurulumu

```bash
cd backend

# Virtual environment oluştur
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

# Dependencies yükle
pip install -r requirements.txt

# .env dosyası oluştur
cp .env.example .env
nano .env  # API keys'leri ekle
```

#### .env Örneği
```env
# Database
DATABASE_URL=sqlite:///./cryptosignal.db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# OpenAI
OPENAI_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_ADMIN_CHAT_ID=your-chat-id

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Frontend Kurulumu

```bash
cd frontend

# Dependencies yükle
npm install

# Development build
npm run dev

# Production build
npm run build
```

### 4. Redis Kurulumu

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# macOS (Homebrew)
brew install redis
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 5. Database Initialize

```bash
cd backend
python3 -c "from database import init_db; init_db()"
```

---

## 🎮 Kullanım

### Development Mode

#### Terminal 1: Backend API
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2: Frontend Dev Server
```bash
cd frontend
npm run dev
# http://localhost:5173
```

#### Terminal 3: Workers (Manual Test)
```bash
cd backend
source venv/bin/activate

# Test individual workers
python3 workers/worker_prices.py
python3 workers/worker_sentiment.py
python3 workers/worker_ai_analyst.py
```

### Production Mode

#### 1. Systemd ile Servis Yönetimi

```bash
# Service dosyalarını kopyala
sudo cp backend/systemd/*.service /etc/systemd/system/

# Servisleri etkinleştir
sudo systemctl daemon-reload
sudo systemctl enable cryptosignal-backend
sudo systemctl enable cryptosignal-prices
sudo systemctl enable cryptosignal-sentiment
sudo systemctl enable cryptosignal-news
sudo systemctl enable cryptosignal-futures
sudo systemctl enable cryptosignal-ai-analyst
sudo systemctl enable cryptosignal-signal-checker
sudo systemctl enable cryptosignal-telegram
sudo systemctl enable cryptosignal-telegram-admin

# Servisleri başlat
sudo systemctl start cryptosignal-backend
sudo systemctl start cryptosignal-prices
sudo systemctl start cryptosignal-sentiment
# ... diğer servisler

# Durum kontrolü
sudo systemctl status cryptosignal-backend
```

#### 2. Nginx Konfigürasyonu

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend static files
    root /opt/cryptosignal-app/frontend/dist;
    index index.html;

    # Try static files first, then proxy to React
    location / {
        try_files $uri $uri.html $uri/ @frontend;
    }

    location @frontend {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

#### 3. Frontend Build & Deploy

```bash
cd frontend
npm run build

# Nginx için dist/ klasörünü kullan
# Otomatik olarak public/ içindeki dosyalar kopyalanır
ls -la dist/  # blog-*.html, robots.txt, sitemap.xml görünmeli
```

---

## 📚 API Dokümantasyonu

### Base URL
```
Development: http://localhost:8000
Production:  https://yourdomain.com/api
```

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepassword"
}

Response:
{
  "id": 1,
  "username": "user123",
  "email": "user@example.com",
  "subscription_type": "free"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user123&password=securepassword

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbG...",
  "token_type": "bearer"
}
```

### Signals

#### Get All Signals
```http
GET /api/signals?limit=20&offset=0&coin=BTC
Authorization: Bearer {token}

Response:
{
  "signals": [
    {
      "id": 1,
      "coin": "BTC",
      "signal": "BUY",
      "confidence": 0.85,
      "entry_price": 65000.0,
      "target_price": 70000.0,
      "stop_loss": 62000.0,
      "analysis": "Strong bullish momentum...",
      "created_at": "2025-12-12T10:00:00Z"
    }
  ],
  "total": 150,
  "has_more": true
}
```

#### Get Signal by ID
```http
GET /api/signals/{signal_id}
Authorization: Bearer {token}
```

#### Delete Signal
```http
DELETE /api/signals/{signal_id}
Authorization: Bearer {token}
```

### Prices

#### Get Real-Time Prices
```http
GET /api/prices?limit=100

Response:
{
  "prices": [
    {
      "coin": "BTC",
      "symbol": "bitcoin",
      "price": 65432.10,
      "change_24h": 3.45,
      "market_cap": 1280000000000,
      "volume_24h": 45000000000,
      "updated_at": "2025-12-12T10:05:00Z"
    }
  ]
}
```

### User

#### Get Current User
```http
GET /api/user/me
Authorization: Bearer {token}
```

#### Update Subscription
```http
PUT /api/user/subscription
Authorization: Bearer {token}
Content-Type: application/json

{
  "subscription_type": "premium"
}
```

### WebSocket

#### Real-Time Price Updates
```javascript
const ws = new WebSocket('wss://yourdomain.com/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    coins: ['BTC', 'ETH', 'SOL']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Price update:', data);
  // { coin: 'BTC', price: 65432.10, change_24h: 3.45 }
};
```

### DCA Calculator

#### Calculate DCA
```http
POST /api/dca/calculate
Content-Type: application/json

{
  "coin": "BTC",
  "investment_amount": 100,
  "frequency": "weekly",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}

Response:
{
  "total_invested": 5200,
  "current_value": 6500,
  "total_coins": 0.085,
  "average_cost": 61176.47,
  "roi_percentage": 25.0,
  "chart_data": [...]
}
```

### Backtesting

#### Run Backtest
```http
POST /api/backtesting/run
Content-Type: application/json

{
  "coin": "BTC",
  "strategy": "rsi",
  "parameters": {
    "rsi_period": 14,
    "oversold": 30,
    "overbought": 70
  },
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000
}

Response:
{
  "total_trades": 45,
  "winning_trades": 28,
  "losing_trades": 17,
  "win_rate": 62.2,
  "profit_factor": 1.85,
  "max_drawdown": 12.5,
  "final_capital": 14250,
  "trades": [...]
}
```

### Watchlist

#### Get Watchlist
```http
GET /api/watchlist
Authorization: Bearer {token}
```

#### Add to Watchlist
```http
POST /api/watchlist
Authorization: Bearer {token}
Content-Type: application/json

{
  "coin": "SOL"
}
```

### Price Alerts

#### Get Alerts
```http
GET /api/price-alerts
Authorization: Bearer {token}
```

#### Create Alert
```http
POST /api/price-alerts
Authorization: Bearer {token}
Content-Type: application/json

{
  "coin": "BTC",
  "condition": "above",
  "target_price": 70000
}
```

### Interactive API Docs

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🤖 Worker Servisleri

### Worker Mimarisi

Her worker bağımsız bir mikroservis olarak çalışır ve belirli bir görevden sorumludur:

```
backend/workers/
├── __init__.py
├── worker_prices.py          # Fiyat verisi toplama
├── worker_sentiment.py       # Sentiment analizi
├── worker_news.py            # Haber toplama
├── worker_futures.py         # Futures market analizi
├── worker_ai_analyst.py      # AI-powered analiz
├── worker_signal_checker.py  # Sinyal doğrulama
├── worker_telegram.py        # Kullanıcı bildirimleri
├── worker_telegram_admin.py  # Admin bildirimleri
└── worker_price_alerts.py    # Fiyat alert tetikleyici

frontend/src/components/ui/   # Reusable UI Components
├── index.js                  # Component exports
├── AdBanner.jsx              # Google AdSense uyumlu reklam
├── SkeletonLoader.jsx        # Skeleton loading components
├── EmptyState.jsx            # Empty state illüstrasyonları
└── Disclaimer.jsx            # Risk disclaimer components

frontend/src/pages/           # Page Components
├── Dashboard.jsx             # Ana dashboard
├── Signals.jsx               # Trading sinyalleri
├── AISummary.jsx             # AI özet sayfası
├── News.jsx                  # Haber akışı
├── Portfolio.jsx             # Portföy yönetimi
├── DCACalculator.jsx         # DCA hesaplama aracı
├── Backtesting.jsx           # Strateji backtesting
├── Premium.jsx               # Premium abonelik
├── Admin.jsx                 # Admin paneli
└── Landing.jsx               # Landing page
```

### 1. **worker_prices.py**
```python
Görev: 1000+ coin için fiyat verisi toplama
API: CoinGecko API
Periyot: Her 60 saniye
İşlemler:
  - Fiyat, hacim, market cap verisi çekme
  - Database'e kaydetme
  - Redis'e cache'leme
  - WebSocket'e broadcast
```

### 2. **worker_sentiment.py**
```python
Görev: Kripto haberleri için sentiment analizi
API: CryptoCompare News API
Periyot: Her 5 dakika
İşlemler:
  - Top 50 coin için haber çekme
  - Keyword-based sentiment scoring
  - -1 (bearish) ile +1 (bullish) arası skor
  - Database'e kaydetme
```

### 3. **worker_news.py**
```python
Görev: Coin-specific haber toplama
API: CryptoCompare News API
Periyot: Her 10 dakika
İşlemler:
  - Her coin için relevance-filtered news
  - Duplicate removal
  - Database'e kaydetme
  - Telegram'a önemli haberleri gönderme
```

### 4. **worker_futures.py**
```python
Görev: Binance futures market analizi
API: Binance Futures API
Periyot: Her 2 dakika
İşlemler:
  - Open interest data
  - Funding rate
  - Long/short ratio
  - Liquidation data
```

### 5. **worker_ai_analyst.py**
```python
Görev: AI-powered piyasa analizi
API: OpenAI GPT-4
Periyot: Her 6 saat (günde 4 kez)
İşlemler:
  - Top 10 coin için deep analysis
  - Technical + fundamental + sentiment
  - Trading stratejileri
  - Risk assessment
  - Database'e kaydetme
```

### 6. **worker_signal_checker.py**
```python
Görev: Sinyal validasyonu ve güncelleme
Periyot: Her 5 dakika
İşlemler:
  - Aktif sinyallerin fiyat kontrolü
  - Target/stop-loss trigger detection
  - Sinyal durumu güncelleme (hit_target, hit_stop_loss)
  - Kullanıcılara bildirim gönderme
```

### 7. **worker_telegram.py**
```python
Görev: Kullanıcı bildirimleri
Periyot: Event-driven (yeni sinyal oluşunca)
İşlemler:
  - Yeni sinyal bildirimi
  - Sinyal güncellemeleri (target hit, SL hit)
  - Formatlanmış mesajlar
  - User-specific notifications
```

### 8. **worker_telegram_admin.py**
```python
Görev: Admin panel bildirimleri
Periyot: Event-driven
İşlemler:
  - Yeni kullanıcı kaydı
  - Ödeme onayları
  - Sistem hataları
  - Günlük istatistikler
```

### Worker Yönetimi

```bash
# Tüm worker'ları başlat
sudo systemctl start cryptosignal-prices
sudo systemctl start cryptosignal-sentiment
sudo systemctl start cryptosignal-news
sudo systemctl start cryptosignal-futures
sudo systemctl start cryptosignal-ai-analyst
sudo systemctl start cryptosignal-signal-checker
sudo systemctl start cryptosignal-telegram
sudo systemctl start cryptosignal-telegram-admin

# Hepsini durdur
sudo systemctl stop cryptosignal-*

# Log'ları görüntüle
journalctl -u cryptosignal-prices -f
journalctl -u cryptosignal-ai-analyst -f
```

---

## 🌐 Deployment

### VPS Deployment (Production)

#### 1. Server Setup
```bash
# Ubuntu 22.04 LTS önerilir
sudo apt update && sudo apt upgrade -y

# Dependencies
sudo apt install -y python3.9 python3-pip python3-venv
sudo apt install -y nodejs npm
sudo apt install -y nginx certbot python3-certbot-nginx
sudo apt install -y redis-server
sudo apt install -y git

# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/CryptoSignalApp.git
sudo chown -R $USER:$USER cryptosignal-app
cd cryptosignal-app
```

#### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env
nano .env  # API keys ekle

# Initialize database
python3 -c "from database import init_db; init_db()"
```

#### 3. Frontend Build
```bash
cd frontend
npm install
npm run build
```

#### 4. Systemd Services
```bash
sudo cp backend/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable ve start all services
for service in cryptosignal-*.service; do
  sudo systemctl enable $service
  sudo systemctl start $service
done
```

#### 5. Nginx Setup
```bash
# SSL certificate
sudo certbot --nginx -d yourdomain.com

# Nginx config
sudo nano /etc/nginx/sites-available/cryptosignal
# (Yukarıdaki Nginx config'i yapıştır)

sudo ln -s /etc/nginx/sites-available/cryptosignal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Monitoring
```bash
# Service status
sudo systemctl status cryptosignal-backend
sudo systemctl status cryptosignal-prices

# Logs
journalctl -u cryptosignal-backend -f
journalctl -u cryptosignal-prices -n 100
```

---

## 🤝 Katkıda Bulunma

Contributions are welcome! Lütfen şu adımları takip edin:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Development Guidelines

- **Code Style**: PEP 8 for Python, ESLint for JavaScript
- **Commits**: Conventional commits (feat:, fix:, docs:, refactor:)
- **Tests**: Unit tests for critical business logic
- **Documentation**: Update README for new features

---

## 📄 License

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

---

## 👨‍💻 Geliştirici

**Onurcan Genç**

- GitHub: [@onurcangnc](https://github.com/onurcangnc)
- LinkedIn: [onurcangenc](https://linkedin.com/in/onurcangenc)
- Email: your.email@example.com

---

## 🙏 Teşekkürler

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - UI library
- [CoinGecko](https://www.coingecko.com/) - Crypto data API
- [OpenAI](https://openai.com/) - AI analysis
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS

---

## 📊 Project Stats

```
Lines of Code: ~25,000
Backend: ~15,000 lines (Python)
Frontend: ~8,000 lines (React/JSX)
Config: ~2,000 lines (JSON, YAML, etc)

Files: 150+
Commits: 200+
Contributors: 1
```

---

## 🚀 Roadmap

### Q1 2025
- [ ] PostgreSQL migration
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Advanced charting library

### Q2 2025
- [ ] Mobile app (React Native)
- [ ] Advanced portfolio analytics
- [ ] Social trading features
- [ ] Multi-exchange support

### Q3 2025
- [ ] Machine learning model training
- [ ] Automated trading bot integration
- [ ] Advanced risk management tools
- [ ] Community features

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by [Onurcan Genç](https://github.com/onurcangnc)

</div>