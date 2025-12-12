# 🚀 CryptoSignal AI - AI-Powered Cryptocurrency Signal Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.0+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

> AI-powered real-time cryptocurrency analysis and signal platform. Professional trading signals, sentiment analysis, and portfolio management for Bitcoin, Ethereum, and 1000+ coins.

## 📋 Table of Contents

- [Overview](#-overview)
- [Software Architecture](#-software-architecture)
- [Design Patterns](#-design-patterns-gof-23-pattern-analysis)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Worker Services](#-worker-services)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## 🎯 Overview

CryptoSignal AI is an AI-powered cryptocurrency analysis platform with a hybrid architecture. The platform processes real-time market data through 8 independent worker services and delivers actionable trading signals to users.

### Core Components

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

## 🏗️ Software Architecture

### Architectural Approach: **Distributed Monolith (Hybrid Architecture)**

The platform uses a hybrid architecture that combines an **N-Tier Monolithic** base structure with **Microservice-like Worker Services**.

#### Architecture Classification

| Aspect | This System | True Microservices |
|--------|-------------|-------------------|
| **Database** | Shared SQLite + Redis | Separate DB per service |
| **Communication** | Shared State (Redis) | API/Message Queue |
| **Deployment** | Independent systemd services | Container orchestration |
| **Scalability** | Worker-based | Service-based |
| **Codebase** | Monorepo | Separate repo per service |

#### Layered Architecture (N-Tier)

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
│   Independent Python processes (systemd managed)            │
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

#### Worker Communication Model

```
worker_prices ──────┐
                    ├──→ Redis (Shared State) ──→ FastAPI ──→ Clients
worker_ai_analyst ──┤         ↓
                    │      SQLite
worker_signal_checker ──────────────────────────────────↑
```

**Why Not True Microservices:**
- All workers share the same SQLite and Redis
- No API contracts between services
- Implicit ordering dependency (prices → signals → checker)
- Single point of failure: Redis

**Why Not Pure Monolithic:**
- Each worker runs as an independent process
- Managed by separate systemd services
- Can be scaled independently
- Eventually consistent data flow

---

## 🎨 Design Patterns (GoF 23 Pattern Analysis)

Gang of Four design patterns identified in the codebase:

### Creational Patterns

#### 1. **Singleton Pattern**
**Usage:** `LLMService`, `AnalysisService`, `RedisClient`

A single instance is used throughout the application. Prevents repeated creation of expensive resources (API connections, DB connection pool).

- `llm_service = LLMService()` → All modules use this instance
- `analysis_service = AnalysisService()` → Single analysis service
- Redis connection pool → Lazy singleton

#### 2. **Factory Method Pattern**
**Usage:** Signal Generation, Empty State Components

Factory methods are used to create different types of objects.

- `generate_signal(coin, timeframe)` → Creates different signal objects based on timeframe
- `EmptyState` component → Produces different UI based on `type` parameter
- Skeleton loader variants → Customized skeleton for each page

#### 3. **Lazy Initialization (Virtual Proxy)**
**Usage:** `RedisClientProxy` in database.py

Redis connection is created on first use, not at application startup. Reduces startup time and prevents unnecessary connection opening.

### Structural Patterns

#### 4. **Proxy Pattern**
**Usage:** `RedisClientProxy`

Sits in front of the actual Redis client. Provides lazy loading, connection pooling, and error handling. Connection management is independent of client code.

#### 5. **Facade Pattern**
**Usage:** `database.py`, `api.js`

Hides complex subsystems behind a simple interface.

- `database.py` → Combines SQLite + Redis operations in a single module
- `api.js` (Frontend) → Abstracts all API calls with centralized functions
- `LLMService` → Hides OpenAI API complexity

#### 6. **Composite Pattern**
**Usage:** React Component Tree, Skeleton Loaders

Represents part-whole hierarchies.

- `DashboardSkeleton` → Composition of `SkeletonCard` + `SkeletonTable` + `SkeletonChart`
- `SignalPerformanceGrid` → Composition of 4 different card components
- Page components → Header + Content + Footer composition

#### 7. **Decorator Pattern**
**Usage:** FastAPI Dependencies, Route decorators

Dynamically adds responsibilities to objects.

- `@router.get("/signals")` → Adds HTTP handler behavior to route
- `Depends(get_current_user)` → Adds auth control to endpoint
- `Depends(require_llm_quota)` → Adds quota control to endpoint

### Behavioral Patterns

#### 8. **Observer Pattern (Pub/Sub)**
**Usage:** WebSocket Broadcasting, React State

Changes in subject are notified to observers.

- WebSocket: `broadcast(message)` → Message to all connected clients
- React: `useState` + `useEffect` → UI updates when state changes
- Redis: Workers write → API reads → Broadcast to clients

#### 9. **Strategy Pattern**
**Usage:** Signal Generation Algorithms, Analysis Methods

Defines a family of algorithms and makes them interchangeable.

- Technical Analysis Strategies: RSI, MACD, Bollinger, MA, EMA
- Backtesting Strategies: RSI Strategy, MACD Strategy, MA Crossover
- Sentiment Analysis: Keyword-based vs AI-based scoring

#### 10. **Template Method Pattern**
**Usage:** Worker Base Structure, API Response Format

Defines the skeleton of an algorithm, leaving steps to subclasses.

- All workers: `while True: process() → sleep()` template
- API responses: `{success, data, error}` template
- Signal cards: Shared layout, different data rendering

#### 11. **Command Pattern**
**Usage:** Telegram Bot Commands

Encapsulates requests as objects.

- `/start`, `/portfolio`, `/signals` → Each command has separate handler
- Command history can be maintained
- Undo/Redo potential (not yet implemented)

#### 12. **State Pattern**
**Usage:** Signal Lifecycle, WebSocket Connection

Changes behavior when internal state changes.

- Signal states: `PENDING → ACTIVE → TARGET_HIT | STOP_LOSS`
- WebSocket: `CONNECTING → CONNECTED → DISCONNECTED`
- Loading states: `loading → success | error`

#### 13. **Iterator Pattern**
**Usage:** Pagination, Data Streaming

Provides sequential access to collection elements.

- API pagination: `limit`, `offset` parameters
- Coin table: 100 items per page iteration
- News feed: Infinite scroll pattern

#### 14. **Chain of Responsibility**
**Usage:** FastAPI Middleware, Auth Flow

Passes request along a chain.

```
Request → CORS → Auth → Rate Limit → Route Handler → Response
```

- Each middleware processes request and passes to next
- Chain breaks if auth fails (401 response)

#### 15. **Mediator Pattern**
**Usage:** Redis as Central Hub

Manages inter-object communication from a central point.

- Redis acts as mediator between all workers
- Workers don't communicate directly with each other
- All data flow goes through Redis

### Frontend-Specific Patterns

#### 16. **Provider Pattern (React Context-like)**
**Usage:** App.jsx root state

- `user`, `lang`, `t` (translations) → Passed to all components via props
- Context API not used, simple prop drilling preferred

#### 17. **Render Props / Callback Pattern**
**Usage:** useWebSocket hook

- `useWebSocket(onMessage)` → Message processing via callback
- Parent component manages state, child receives callback

#### 18. **Container/Presentational Pattern**
**Usage:** Pages vs UI Components

- **Container (Smart):** Dashboard, Signals → Data fetching, state
- **Presentational (Dumb):** SkeletonLoader, EmptyState → UI only

### Pattern Summary Table

| Pattern | Category | Usage Location | Purpose |
|---------|----------|---------------|---------|
| Singleton | Creational | LLMService, Redis | Single instance |
| Factory Method | Creational | Signal/Skeleton generation | Object creation |
| Lazy Init | Creational | RedisClientProxy | Deferred creation |
| Proxy | Structural | RedisClientProxy | Access control |
| Facade | Structural | database.py, api.js | Simplification |
| Composite | Structural | React components | Hierarchy |
| Decorator | Structural | FastAPI Depends | Add behavior |
| Observer | Behavioral | WebSocket, React | Notification |
| Strategy | Behavioral | Analysis algorithms | Algorithm swap |
| Template | Behavioral | Workers, API format | Define skeleton |
| Command | Behavioral | Telegram commands | Encapsulate request |
| State | Behavioral | Signal lifecycle | State management |
| Iterator | Behavioral | Pagination | Sequential access |
| Chain of Resp. | Behavioral | Middleware | Request chain |
| Mediator | Behavioral | Redis hub | Central communication |

---

## 💻 Tech Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.9+ | Core language |
| FastAPI | 0.104+ | REST API + WebSocket |
| SQLite | 3.x | Primary database |
| Redis | 7.x | Caching + Pub/Sub |
| Uvicorn | 0.24+ | ASGI server |
| Pydantic | 2.x | Data validation |
| OpenAI API | 1.x | AI analysis |
| python-telegram-bot | 20.x | Telegram notifications |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
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

## ✨ Features

### 🎯 Core Features

#### 1. **AI-Powered Signal Generation**
- GPT-4 based technical analysis
- Multi-indicator analysis (RSI, MACD, Bollinger Bands)
- Pattern recognition (Head & Shoulders, Double Top/Bottom)
- Sentiment-aware signal adjustment

#### 2. **Real-Time Data Processing**
- Live price updates via WebSocket
- Real-time tracking for 1000+ coins
- Futures market analysis
- Volume and market cap monitoring

#### 3. **Sentiment Analysis**
- News sentiment scoring (-1 to +1)
- Social media trend analysis
- Market fear & greed index
- Keyword-based sentiment extraction

#### 4. **Multi-Channel Notifications**
- Telegram bot integration
- Dedicated admin channel
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

- **AI Analyst**: Daily market summary and strategic recommendations
- **Futures Signals**: Special signals for leverage trading
- **News Aggregation**: Coin-specific news filtering
- **Multi-Language**: TR/EN support
- **SEO Optimized**: Landing page + 6 blog articles
- **Mobile Responsive**: Compatible with all devices
- **Dark Mode**: Modern glassmorphism design

### 📈 Trading Tools

#### 7. **DCA Calculator**
- Dollar Cost Averaging strategy calculation
- Daily, weekly, monthly investment intervals
- Historical performance simulation
- Visual chart result analysis
- ROI and average cost calculation

#### 8. **Backtesting Engine**
- Strategy testing tool (RSI, MACD, Moving Average)
- Customizable parameters
- Win rate, profit factor, max drawdown metrics
- Visual chart results
- Entry/exit point analysis

#### 9. **Watchlist Management**
- Personal coin tracking list
- Quick access to favorites
- Real-time price updates
- Customizable view

#### 10. **Price Alerts**
- Custom price notifications
- Above/below threshold conditions
- Multiple alert support
- Telegram integration

#### 11. **TradingView Integration**
- Professional chart widget
- 100+ technical indicators
- Multiple timeframe support
- Drawing tools

### 🎨 UI/UX Features

- **Skeleton Loaders**: Modern loading states
- **Empty States**: Informative empty state illustrations
- **Risk Disclaimers**: Google AdSense compliant warnings
- **Ad Banner System**: Advertisement integration
- **Typography Hierarchy**: Consistent typography system
- **Color Palette**: Amber/Orange themed color palette
- **Animations**: Smooth transition animations (fade-in, slide-up, shimmer)
- **Accessibility**: Focus states and semantic HTML

---

## 🚀 Installation

### Requirements

```bash
# System requirements
- Python 3.9+
- Node.js 18+
- Redis 7+
- SQLite 3+
- Git
```

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/CryptoSignalApp.git
cd CryptoSignalApp
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env  # Add API keys
```

#### .env Example
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

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Development build
npm run dev

# Production build
npm run build
```

### 4. Redis Setup

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

### 5. Initialize Database

```bash
cd backend
python3 -c "from database import init_db; init_db()"
```

---

## 🎮 Usage

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

#### 1. Service Management with Systemd

```bash
# Copy service files
sudo cp backend/systemd/*.service /etc/systemd/system/

# Enable services
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

# Start services
sudo systemctl start cryptosignal-backend
sudo systemctl start cryptosignal-prices
sudo systemctl start cryptosignal-sentiment
# ... other services

# Check status
sudo systemctl status cryptosignal-backend
```

#### 2. Nginx Configuration

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

# Use dist/ folder for Nginx
# Files from public/ are automatically copied
ls -la dist/  # blog-*.html, robots.txt, sitemap.xml should be visible
```

---

## 📚 API Documentation

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

## 🤖 Worker Services

### Worker Architecture

Each worker runs as an independent microservice-like process and is responsible for a specific task:

```
backend/workers/
├── __init__.py
├── worker_prices.py          # Price data collection
├── worker_sentiment.py       # Sentiment analysis
├── worker_news.py            # News aggregation
├── worker_futures.py         # Futures market analysis
├── worker_ai_analyst.py      # AI-powered analysis
├── worker_signal_checker.py  # Signal validation
├── worker_telegram.py        # User notifications
├── worker_telegram_admin.py  # Admin notifications
└── worker_price_alerts.py    # Price alert trigger

frontend/src/components/ui/   # Reusable UI Components
├── index.js                  # Component exports
├── AdBanner.jsx              # Google AdSense compliant ads
├── SkeletonLoader.jsx        # Skeleton loading components
├── EmptyState.jsx            # Empty state illustrations
└── Disclaimer.jsx            # Risk disclaimer components

frontend/src/pages/           # Page Components
├── Dashboard.jsx             # Main dashboard
├── Signals.jsx               # Trading signals
├── AISummary.jsx             # AI summary page
├── News.jsx                  # News feed
├── Portfolio.jsx             # Portfolio management
├── DCACalculator.jsx         # DCA calculator tool
├── Backtesting.jsx           # Strategy backtesting
├── Premium.jsx               # Premium subscription
├── Admin.jsx                 # Admin panel
└── Landing.jsx               # Landing page
```

### 1. **worker_prices.py**
```
Task: Price data collection for 1000+ coins
API: CoinGecko API
Period: Every 60 seconds
Operations:
  - Fetch price, volume, market cap data
  - Save to database
  - Cache to Redis
  - Broadcast to WebSocket
```

### 2. **worker_sentiment.py**
```
Task: Sentiment analysis for crypto news
API: CryptoCompare News API
Period: Every 5 minutes
Operations:
  - Fetch news for top 50 coins
  - Keyword-based sentiment scoring
  - Score from -1 (bearish) to +1 (bullish)
  - Save to database
```

### 3. **worker_news.py**
```
Task: Coin-specific news aggregation
API: CryptoCompare News API
Period: Every 10 minutes
Operations:
  - Relevance-filtered news for each coin
  - Duplicate removal
  - Save to database
  - Send important news to Telegram
```

### 4. **worker_futures.py**
```
Task: Binance futures market analysis
API: Binance Futures API
Period: Every 2 minutes
Operations:
  - Open interest data
  - Funding rate
  - Long/short ratio
  - Liquidation data
```

### 5. **worker_ai_analyst.py**
```
Task: AI-powered market analysis
API: OpenAI GPT-4
Period: Every 6 hours (4 times daily)
Operations:
  - Deep analysis for top 10 coins
  - Technical + fundamental + sentiment
  - Trading strategies
  - Risk assessment
  - Save to database
```

### 6. **worker_signal_checker.py**
```
Task: Signal validation and updates
Period: Every 5 minutes
Operations:
  - Price check for active signals
  - Target/stop-loss trigger detection
  - Update signal status (hit_target, hit_stop_loss)
  - Send notifications to users
```

### 7. **worker_telegram.py**
```
Task: User notifications
Period: Event-driven (when new signal is created)
Operations:
  - New signal notification
  - Signal updates (target hit, SL hit)
  - Formatted messages
  - User-specific notifications
```

### 8. **worker_telegram_admin.py**
```
Task: Admin panel notifications
Period: Event-driven
Operations:
  - New user registration
  - Payment confirmations
  - System errors
  - Daily statistics
```

### Worker Management

```bash
# Start all workers
sudo systemctl start cryptosignal-prices
sudo systemctl start cryptosignal-sentiment
sudo systemctl start cryptosignal-news
sudo systemctl start cryptosignal-futures
sudo systemctl start cryptosignal-ai-analyst
sudo systemctl start cryptosignal-signal-checker
sudo systemctl start cryptosignal-telegram
sudo systemctl start cryptosignal-telegram-admin

# Stop all
sudo systemctl stop cryptosignal-*

# View logs
journalctl -u cryptosignal-prices -f
journalctl -u cryptosignal-ai-analyst -f
```

---

## 🌐 Deployment

### VPS Deployment (Production)

#### 1. Server Setup
```bash
# Ubuntu 22.04 LTS recommended
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
nano .env  # Add API keys

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

# Enable and start all services
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
# (Paste the Nginx config above)

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

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

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

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Developer

**Onurcan Genc**

- GitHub: [@onurcangnc](https://github.com/onurcangnc)
- LinkedIn: [onurcangenc](https://linkedin.com/in/onurcangenc)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

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

Made with ❤️ by [Onurcan Genc](https://github.com/onurcangnc)

</div>
