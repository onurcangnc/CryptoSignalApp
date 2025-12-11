# 🚀 CryptoSignal AI

> AI-Powered Cryptocurrency Trading Signals & Portfolio Management Platform

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![React](https://img.shields.io/badge/react-18+-61DAFB)
![License](https://img.shields.io/badge/license-MIT-orange)

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture & Design Patterns](#-architecture--design-patterns)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Performance & Optimizations](#-performance--optimizations)
- [Cost Analysis](#-cost-analysis)

---

## 🎯 Overview

**CryptoSignal AI** is an AI-powered cryptocurrency analysis and portfolio management platform. It provides real-time price tracking, technical analysis, AI-powered news analysis, and portfolio optimization features.

### Core Functions

1. **📊 Real-Time Dashboard** - Live price tracking for 500+ coins
2. **💡 Trading Signals** - Algorithmic signal system updated every 5 seconds
3. **🤖 AI Summary** - LLM-based portfolio analysis and recommendations
4. **📰 News Analysis** - AI sentiment analysis for crypto news
5. **💼 Portfolio Management** - Multi-currency portfolio management
6. **⚙️ Admin Panel** - Worker monitoring, user management, LLM cost analytics

---

## ✨ Features

### 🔥 Core Features

#### 1. **Real-Time Trading Signals**
- **6 timeframes**: 1d, 1w, 1m, 3m, 6m, 1y
- **12+ technical indicators**: RSI, MACD, Bollinger Bands, EMA, SMA, Stochastic, ADX, CCI, MFI, Williams %R
- **5-second updates** (real-time)
- **Futures market** integration (funding rates, open interest)
- **Risk scoring** (0-100)
- **Confidence level** (0-1)
- **BUY/SELL/HOLD** signals

#### 2. **AI-Powered News Analysis**
- **OpenAI GPT-4o-mini** sentiment analysis
- **Two-stage analysis**: Keyword filtering → LLM analysis
- **Important news filtering** (70% cost savings)
- **Coin-specific sentiment** scores
- **Impact level** (HIGH/MEDIUM/LOW)
- **Category classification** (Regulation, Hack, Partnership, Other)
- **Cost-optimized**: $0.20-$0.30/month (83-89% reduction)

#### 3. **Portfolio AI Analysis**
- **9 detailed analysis categories**:
  - 📊 Overview & Statistics
  - 💡 Trading Signals
  - 📈 Portfolio Forecast
  - ⚖️ Risk Analysis
  - 🎯 Coin Recommendations
  - 🔄 Rebalancing Suggestions
  - 📰 News Impact
  - ⚠️ Warnings & Alerts
  - 🎓 Learning Resources
- **GPT-4o-mini** in-depth analysis
- **Caching system** (1 hour TTL)
- **Daily usage limits** (tier-based)

#### 4. **Multi-Currency Support**
- **8 fiat currencies**: USD, TRY, EUR, GBP, JPY, CNY, KRW, INR
- **Real-time exchange rates** (exchangerate-api.com)
- **Fiat → Crypto** and **Crypto → Fiat** calculations

#### 5. **Advanced Admin Panel**
- **Worker health monitoring**
- **LLM analytics & cost tracking**
- **User tier management**
- **Real-time system metrics**
- **Revenue & profit margin tracking**

---

## 🏗️ Architecture & Design Patterns

### 🎨 Software Architecture

#### **1. Microservices Architecture**

```
┌─────────────────┐
│   FastAPI       │  ← Main API Gateway (port 8000)
│   main.py       │
└────────┬────────┘
         │
    ┌────┴─────┐
    │  Redis   │  ← Central Data Store
    └────┬─────┘
         │
    ┌────┴──────────────────────────────┐
    │                                   │
┌───▼────┐  ┌──────────┐  ┌──────────┐
│Worker  │  │Worker    │  │Worker    │
│Prices  │  │Signals   │  │AI News   │
│(5min)  │  │(5sec)    │  │(1hour)   │
└────────┘  └──────────┘  └──────────┘
```

**Benefits:**
- ✅ Scalable - Each worker is independent
- ✅ Fault-tolerant - If one worker crashes, others continue
- ✅ Easy deployment - Workers can be deployed separately

#### **2. Worker Pattern (Background Jobs)**

8 background workers:
- `worker_prices.py` - CoinGecko price sync (5 minutes)
- `worker_signals.py` - Trading signal generator (5 seconds) ⚡
- `worker_ai_news.py` - News AI analysis (1 hour) - **Cost-optimized**
- `worker_sentiment.py` - Market sentiment (10 minutes)
- `worker_news.py` - News crawler (30 minutes)
- `worker_futures.py` - Binance futures data (5 minutes)
- `worker_ai_analyst.py` - LLM analysis (on-demand)
- `worker_telegram.py` - Telegram bot (async)

**Pattern:** Producer-Consumer with Redis
- Workers = Producers (write data to Redis)
- API = Consumer (reads from Redis)

#### **3. Repository Pattern (Database Abstraction)**

```python
# database.py - Single source of truth
def get_portfolio(user_id: int) -> Dict
def save_portfolio(user_id: int, holdings: List) -> None
def get_llm_usage(user_id: int, date: str) -> int
```

**Benefits:**
- ✅ Database change only affects 1 file
- ✅ Testable (mock DB)
- ✅ Reusable functions

#### **4. Router Pattern (API Organization)**

```
backend/routers/
├── auth.py          # Authentication
├── portfolio.py     # Portfolio CRUD
├── signals.py       # Trading signals
├── news.py          # News feed
├── admin.py         # Admin panel
├── ai_summary.py    # AI analysis
└── websocket.py     # Real-time updates
```

FastAPI router system - modular API structure

#### **5. Dependency Injection**

```python
from dependencies import get_current_user, require_llm_quota

@router.get("/portfolio")
async def get_portfolio(user: dict = Depends(get_current_user)):
    # user automatically injected
    pass
```

**Benefits:**
- ✅ Centralized authentication logic
- ✅ Testable
- ✅ Reusable

#### **6. Caching Strategy (Redis)**

```python
# Multi-level caching
1. prices_data (5 min TTL)
2. signals_data (5 sec TTL)
3. ai_news_analyzed (12 hour TTL)
4. ai_summary_cache (1 hour TTL)
```

**Cache Invalidation:** TTL-based (Time To Live)

#### **7. Two-Stage Analysis Pattern (Cost Optimization)**

```python
def analyze_news_smart(news):
    # Stage 1: Fast keyword analysis (free)
    keyword_result = analyze_with_keywords(news)

    if keyword_result['confidence'] < 0.6:
        # Stage 2: LLM analysis (paid)
        return analyze_with_llm(news)

    return keyword_result
```

**Result:** 70-80% cost reduction, same quality

#### **8. Observer Pattern (WebSocket)**

```python
# Real-time price updates
websocket_manager.broadcast({
    "type": "price_update",
    "data": prices
})
```

Frontend automatically updates

---

### 🎯 Design Patterns Summary

| Pattern | Usage | Benefit |
|---------|-------|---------|
| **Microservices** | Worker architecture | Scalability, fault tolerance |
| **Repository** | Database layer | Abstraction, testability |
| **Dependency Injection** | FastAPI endpoints | Reusability, testing |
| **Observer** | WebSocket | Real-time updates |
| **Strategy** | Signal generation | Multiple timeframes |
| **Factory** | LLM providers | OpenAI/Claude switching |
| **Singleton** | Redis connection | Resource efficiency |
| **Cache-Aside** | Data fetching | Performance |
| **Two-Stage Pipeline** | News analysis | Cost optimization |

---

## 🛠️ Technology Stack

### Backend

| Technology | Version | Usage |
|-----------|---------|-------|
| **Python** | 3.10+ | Core language |
| **FastAPI** | 0.104+ | Web framework |
| **Redis** | 7.0+ | Caching & data store |
| **PostgreSQL** | 14+ | User data, portfolio |
| **SQLAlchemy** | 2.0+ | ORM |
| **httpx** | 0.25+ | Async HTTP client |
| **OpenAI API** | Latest | AI analysis (GPT-4o-mini) |
| **Anthropic API** | Latest | AI fallback (Claude) |

### Frontend

| Technology | Version | Usage |
|-----------|---------|-------|
| **React** | 18.2+ | UI framework |
| **Vite** | 5.0+ | Build tool |
| **Tailwind CSS** | 3.4+ | Styling |
| **Recharts** | 2.10+ | Charts (optional) |

### External APIs

- **CoinGecko** - Coin prices, market data
- **Binance** - Futures data, funding rates
- **CryptoPanic** - News aggregation
- **exchangerate-api.com** - FX rates
- **Alternative.me** - Fear & Greed Index

---

## 🚀 Installation

### Requirements

- Python 3.10+
- Node.js 18+
- Redis 7.0+
- PostgreSQL 14+

### 1. Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/cryptosignal-app.git
cd cryptosignal-app/backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Environment variables (.env file)
cp .env.example .env
# Edit .env:
# - DATABASE_URL
# - REDIS_PASSWORD
# - OPENAI_API_KEY
# - SECRET_KEY

# 5. Database migration
python -c "from database import create_tables; create_tables()"

# 6. Start Redis
redis-server --requirepass your_redis_password

# 7. Start main API
python main.py

# 8. Start workers (separate terminals)
python worker_prices.py
python worker_signals.py
python worker_ai_news.py
python worker_sentiment.py
python worker_news.py
python worker_futures.py
```

### 2. Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Development server
npm run dev

# 3. Production build
npm run build
```

---

## 🌐 Deployment

### Production Deployment (Ubuntu Server)

#### 1. Backend Deployment

```bash
# 1. Nginx reverse proxy
sudo apt install nginx
sudo nano /etc/nginx/sites-available/cryptosignal

# Nginx config:
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location / {
        root /var/www/cryptosignal/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}

# 2. Systemd service (backend)
sudo nano /etc/systemd/system/cryptosignal-backend.service

[Unit]
Description=CryptoSignal Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/cryptosignal/backend
Environment="PATH=/var/www/cryptosignal/backend/venv/bin"
ExecStart=/var/www/cryptosignal/backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target

# 3. Start service
sudo systemctl daemon-reload
sudo systemctl enable cryptosignal-backend
sudo systemctl start cryptosignal-backend

# 4. Worker services (same for each worker)
# Example: worker-signals.service
sudo nano /etc/systemd/system/cryptosignal-worker-signals.service

[Unit]
Description=CryptoSignal Signals Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/cryptosignal/backend
Environment="PATH=/var/www/cryptosignal/backend/venv/bin"
ExecStart=/var/www/cryptosignal/backend/venv/bin/python worker_signals.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Start all workers
sudo systemctl enable cryptosignal-worker-signals
sudo systemctl start cryptosignal-worker-signals
```

#### 2. Frontend Deployment

```bash
# Build frontend
cd frontend
npm run build

# Deploy to server
rsync -avz dist/ user@server:/var/www/cryptosignal/frontend/dist/

# Reload Nginx
sudo systemctl reload nginx
```

### 📱 Mobile Deployment (Android via Capacitor)

```bash
# 1. Capacitor setup
npm install @capacitor/core @capacitor/cli @capacitor/android
npx cap init
npx cap add android

# 2. Build & sync
npm run build
npx cap sync android

# 3. Open in Android Studio
npx cap open android

# 4. Create release APK/AAB
cd android
./gradlew bundleRelease

# 5. Upload to Google Play Store
# Play Console → Create Release → Upload AAB
```

---

## 📚 API Documentation

### Authentication

```bash
# Register
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "secure123",
  "username": "trader1"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "secure123"
}

# Response
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "email": "...", "tier": "free" }
}
```

### Trading Signals

```bash
# Get signals
GET /api/signals?timeframe=1d&signal_filter=BUY&limit=50

# Response
{
  "success": true,
  "timeframe": "1d",
  "count": 50,
  "stats": {
    "total_buy": 12,
    "total_sell": 8,
    "total_hold": 30
  },
  "signals": [
    {
      "symbol": "BTC",
      "signal": "BUY",
      "confidence": 85,
      "score": 7.2,
      "indicators": {
        "rsi": 35.2,
        "macd": "bullish",
        "trend": "uptrend"
      },
      "risk_level": "medium"
    }
  ]
}
```

### Portfolio

```bash
# Get portfolio
GET /api/portfolio
Authorization: Bearer {token}

# Update portfolio
PUT /api/portfolio
{
  "holdings": [
    {
      "coin": "BTC",
      "quantity": 0.5,
      "invested_usd": 20000
    }
  ]
}
```

### AI Summary

```bash
# Get AI analysis
GET /api/ai-summary/portfolio
Authorization: Bearer {token}

# Generate fresh analysis
POST /api/ai-summary/analyze
Authorization: Bearer {token}
```

**Full API Docs:** http://localhost:8000/docs (FastAPI Swagger UI)

---

## ⚡ Performance & Optimizations

### 1. **Signal Update Speed**
- **Before:** 60 seconds
- **Now:** 5 seconds
- **Result:** 12x faster signal updates

### 2. **LLM Cost Optimization**

| Strategy | Cost/Month | Reduction |
|----------|------------|-----------|
| Before | $1.80 | - |
| Important news filter | $0.60 | 67% |
| Two-stage analysis | $0.36 | 80% |
| **COMBO (Implemented)** | **$0.20-$0.30** | **83-89%** |

**Quality:** ⭐⭐⭐⭐⭐ (Higher - focuses on important news)

### 3. **Cache Strategy**

| Data Type | TTL | Hit Rate |
|-----------|-----|----------|
| Prices | 5 min | ~95% |
| Signals | 5 sec | ~80% |
| AI News | 12 hours | ~98% |
| AI Summary | 1 hour | ~90% |

### 4. **Database Query Optimization**
- ✅ Index on `user_id`, `created_at`
- ✅ Connection pooling (SQLAlchemy)
- ✅ `joinedload()` for lazy loading

### 5. **Frontend Performance**
- ✅ Code splitting (React.lazy)
- ✅ Memoization (`useMemo`, `useCallback`)
- ✅ Virtual scrolling (long lists)
- ✅ Image lazy loading

---

## 💰 Cost Analysis

### 🎯 Current Monthly Costs (All Users Combined)

#### Infrastructure Costs
| Category | Cost/Month |
|----------|------------|
| VPS (4GB RAM) | $20.00 |
| Redis Cloud | $0.00 (free tier) |
| PostgreSQL | $0.00 (self-hosted) |
| Domain | $1.00 |
| **Infrastructure Total** | **$21.00** |

#### LLM API Costs (Current - Partially Optimized)
| Service | Frequency | Cost/Month | Status |
|---------|-----------|------------|--------|
| **News Analysis** | Every 1 hour | **$0.20-$0.30** | ✅ **Optimized** (was $1.80) |
| **AI Portfolio Summary** | On-demand | **$12.00** | ⚠️ **Not optimized yet** |
| **Coin Analysis** | On-click | **$2.25** | ⚠️ **Not optimized yet** |
| **LLM API Total** | | **$14.45-$14.55** | |

#### **Grand Total: $35.45-$35.55/month**

---

### 📈 User Scale & LLM Usage

**Current assumptions** (total across all users):
- **AI Portfolio Summary**: ~400 analyses/day = 12,000/month
  - Cost per analysis: $0.001 (GPT-4o-mini)
  - Monthly cost: 12,000 × $0.001 = **$12.00**

- **Coin Analysis**: ~500 analyses/day = 15,000/month
  - Cost per analysis: $0.00015
  - Monthly cost: 15,000 × $0.00015 = **$2.25**

- **News Analysis**: 24 runs/day = 720/month
  - After optimization: **$0.20-$0.30**

**Scaling examples:**

| User Count | Portfolio Analyses/Day | Coin Analyses/Day | LLM Cost/Month |
|------------|------------------------|-------------------|----------------|
| **100 users** | 200 | 250 | $7.40 |
| **500 users** | 400 | 500 | $14.50 ← Current |
| **1,000 users** | 600 | 1,000 | $20.80 |
| **5,000 users** | 2,000 | 5,000 | $77.50 |

**Note:** News Analysis cost ($0.20-$0.30) stays constant regardless of user count.

---

### 🔥 Optimization Journey

#### Phase 1: News Analysis (✅ Implemented)
| Optimization | Cost Before | Cost After | Reduction |
|--------------|-------------|------------|-----------|
| **Important news filter** | $1.80/mo | $0.60/mo | 67% ⬇️ |
| **Two-stage analysis** | $1.80/mo | $0.36/mo | 80% ⬇️ |
| **COMBO (implemented)** | **$1.80/mo** | **$0.20-$0.30/mo** | **83-89% ⬇️** |

**Quality Impact:** ⭐⭐⭐⭐⭐ *Higher quality* (focuses on important news only)

#### Phase 2: Portfolio & Coin Analysis (⚠️ Not Implemented Yet)

**Proposed optimizations:**
| Optimization | Current | After | Reduction |
|--------------|---------|-------|-----------|
| **Portfolio cache TTL** (1h → 3h) | $12.00 | $3.60 | 70% ⬇️ |
| **Lazy tab loading** | $12.00 | $4.00 | 66% ⬇️ |
| **Summary-first approach** | $12.00 | $2.40 | 80% ⬇️ |
| **COMBO (all strategies)** | **$12.00** | **$0.72-$1.20** | **90%+ ⬇️** |

---

### 💡 Complete Cost Comparison

| Status | News | Portfolio | Coin | **Total LLM** | **Grand Total** |
|--------|------|-----------|------|---------------|-----------------|
| **Before optimization** | $1.80 | $12.00 | $2.25 | **$16.05** | **$37.05/mo** |
| **Current (news optimized)** | $0.25 | $12.00 | $2.25 | **$14.50** | **$35.50/mo** |
| **After full optimization** | $0.25 | $1.00 | $2.25 | **$3.50** | **$24.50/mo** |

**Potential Savings:** $37.05 → $24.50 = **$12.55/month (34% total cost reduction)**

---

### 🎯 Revenue Model (Example)

Assuming **500 active users** with tiered pricing:

| Tier | Users | Price/Month | Revenue |
|------|-------|-------------|---------|
| **Free** | 300 | $0 | $0 |
| **Pro** | 150 | $5 | $750 |
| **Premium** | 50 | $15 | $750 |
| **Total Revenue** | | | **$1,500/mo** |

**Profit Calculation:**
- Revenue: $1,500/month
- Costs: $35.50/month (current) or $24.50/month (optimized)
- **Profit Margin**: 97.6% (current) or 98.4% (optimized)

**Note:** LLM costs are **total system costs** shared across all users, not per-user.

---

## 📊 System Requirements

### Minimum (Development)
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB
- Network: 10 Mbps

### Recommended (Production)
- CPU: 4 cores
- RAM: 8GB
- Disk: 50GB SSD
- Network: 100 Mbps

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Developer

**Onurcan** - CryptoSignal AI

---

## 🙏 Acknowledgments

- CoinGecko API
- Binance API
- OpenAI GPT-4
- FastAPI Community
- React Community

---

**⭐ Star the project if you like it!**
