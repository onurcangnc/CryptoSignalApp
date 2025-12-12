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

### Mimari Yaklaşım: **Mikroservis Mimarisi + Event-Driven Architecture**

Platform, aşağıdaki mimari prensipleri benimser:

#### 1. **Mikroservis Mimarisi**
- Her worker bağımsız bir mikroservis olarak çalışır
- Servisler arası haberleşme: Redis Pub/Sub + Database
- Her servis kendi sorumluluk alanında otonom
- Horizontal scaling desteği (her worker bağımsız ölçeklenebilir)

#### 2. **Layered Architecture (Katmanlı Mimari)**
```
Presentation Layer   → React Frontend
API Gateway Layer    → FastAPI (REST + WebSocket)
Business Logic Layer → Services + Routers
Data Access Layer    → Database module (ORM abstraction)
Persistence Layer    → SQLite + Redis
```

#### 3. **Event-Driven Architecture**
- Workers: Periodic event triggers (cron-like)
- Real-time events: WebSocket için pub/sub pattern
- Asynchronous processing: Background tasks

#### 4. **Repository Pattern**
- `database.py`: Centralized data access
- Abstract database operations from business logic
- Easy to swap database (SQLite → PostgreSQL)

---

## 🎨 Tasarım Desenleri

### Backend Design Patterns

#### 1. **Dependency Injection (DI)**
```python
# dependencies.py
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # JWT validation and user retrieval
    return user

# Usage in routers
@router.get("/signals")
async def get_signals(user = Depends(get_current_user)):
    # Automatic user injection
```

**Avantajlar:**
- Loose coupling
- Testability (mock dependencies)
- Single Responsibility Principle

#### 2. **Repository Pattern**
```python
# database.py
class Database:
    def get_user_signals(user_id: int):
        # Centralized data access

    def save_signal(signal_data: dict):
        # Encapsulated database logic
```

**Avantajlar:**
- Separation of concerns
- Easy database migration
- Testable business logic

#### 3. **Factory Pattern**
```python
# services/
- ai_service.py       # AI model creation
- data_service.py     # Data source factories
- notification.py     # Notification channel factory
```

**Avantajlar:**
- Object creation abstraction
- Easy to add new implementations
- Configuration-based instantiation

#### 4. **Observer Pattern (Pub/Sub)**
```python
# Redis Pub/Sub for real-time updates
redis_client.publish('price_update', json.dumps(price_data))

# WebSocket subscribers receive updates
websocket.send_json(price_data)
```

**Avantajlar:**
- Decoupled communication
- Real-time updates
- Scalable notification system

#### 5. **Strategy Pattern**
```python
# Different AI models for different analysis types
class TechnicalAnalysisStrategy:
    def analyze(data): ...

class SentimentAnalysisStrategy:
    def analyze(data): ...
```

#### 6. **Singleton Pattern**
```python
# Database connection pool
# Redis connection pool
# Shared resources across workers
```

### Frontend Design Patterns

#### 1. **Component Composition**
```jsx
<Dashboard>
  <Header />
  <SignalList />
  <PriceChart />
  <Footer />
</Dashboard>
```

#### 2. **Custom Hooks**
```jsx
// useAuth.js - Authentication logic
// useWebSocket.js - Real-time data
// useSignals.js - Signal fetching
```

#### 3. **Context API**
```jsx
<AuthContext>
  <LanguageContext>
    <App />
  </LanguageContext>
</AuthContext>
```

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
└── worker_telegram_admin.py  # Admin bildirimleri
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