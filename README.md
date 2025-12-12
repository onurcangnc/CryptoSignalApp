# CryptoSignal AI

Real-time cryptocurrency trading signal platform powered by AI analysis.

![Version](https://img.shields.io/badge/version-6.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-yellow)
![React](https://img.shields.io/badge/react-18+-61dafb)

## Features

### Core Features
- **Real-time Trading Signals** - AI-powered BUY/SELL/HOLD signals for 200+ cryptocurrencies
- **Technical Analysis** - RSI, MACD, Bollinger Bands, Moving Averages, and more
- **Portfolio Management** - Track holdings with real-time P&L calculations
- **AI Market Summary** - GPT-4 powered daily market analysis and insights
- **Fear & Greed Index** - Real-time market sentiment tracking
- **Futures Data** - Long/short ratios and open interest analysis

### Advanced Features
- **WebSocket Real-time Updates** - Live price and signal streaming
- **News Aggregation** - Multi-source crypto news with sentiment analysis
- **Signal Performance Tracking** - Historical accuracy metrics
- **Multi-tier User System** - Free, Pro, and Admin tiers
- **Rewarded Ads** - Free users can earn AI credits by watching ads
- **Telegram Bot Integration** - Receive signals on Telegram
- **Multi-language Support** - Turkish and English

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite + Redis
- **AI**: OpenAI GPT-4
- **WebSocket**: Native FastAPI WebSocket
- **Authentication**: JWT tokens

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React

### Infrastructure
- **Web Server**: Nginx (reverse proxy)
- **Process Manager**: systemd
- **SSL**: Let's Encrypt

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Dashboard│ │Signals  │ │Portfolio│ │AI Summary│           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
└───────┼──────────┼─────────┼──────────┼─────────────────────┘
        │          │         │          │
        ▼          ▼         ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                     │
│  ┌──────┐ ┌────────┐ ┌─────────┐ ┌────────┐ ┌───────────┐  │
│  │ Auth │ │Signals │ │Portfolio│ │Analysis│ │ WebSocket │  │
│  └──────┘ └────────┘ └─────────┘ └────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────────┘
        │          │         │          │
        ▼          ▼         ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Services Layer                            │
│  ┌───────────┐ ┌────────────┐ ┌───────────┐ ┌────────────┐ │
│  │LLM Service│ │Analysis Svc│ │News Service│ │Futures Svc │ │
│  └───────────┘ └────────────┘ └───────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────┘
        │          │         │          │
        ▼          ▼         ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │   SQLite (DB)    │      │   Redis (Cache)  │            │
│  │ - Users          │      │ - Prices         │            │
│  │ - Portfolios     │      │ - Signals        │            │
│  │ - Signal Tracks  │      │ - Fear & Greed   │            │
│  │ - LLM Analytics  │      │ - Rate Limiting  │            │
│  └──────────────────┘      └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
CryptoSignalApp/
├── backend/
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Configuration constants
│   ├── database.py          # SQLite & Redis operations
│   ├── dependencies.py      # FastAPI dependencies (auth, quota)
│   ├── models.py            # Pydantic models
│   ├── routers/             # API endpoints
│   │   ├── auth.py          # Authentication
│   │   ├── signals.py       # Trading signals
│   │   ├── portfolio.py     # Portfolio management
│   │   ├── analysis.py      # Coin analysis
│   │   ├── ai_summary.py    # AI market summary
│   │   ├── news.py          # News feed
│   │   ├── admin.py         # Admin panel
│   │   ├── websocket.py     # WebSocket handler
│   │   ├── payment.py       # Payment processing
│   │   └── ads.py           # Rewarded ads system
│   ├── services/            # Business logic
│   │   ├── llm_service.py   # OpenAI integration
│   │   ├── analysis_service.py
│   │   ├── ai_summary_service.py
│   │   ├── news_service.py
│   │   └── futures_service.py
│   ├── workers/             # Background jobs
│   │   ├── worker_prices.py
│   │   ├── worker_signal_checker.py
│   │   ├── worker_telegram.py
│   │   └── worker_sentiment.py
│   └── systemd/             # Service definitions
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main application
│   │   ├── api/             # API client
│   │   ├── pages/           # Page components
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Signals.jsx
│   │   │   ├── Portfolio.jsx
│   │   │   ├── AISummary.jsx
│   │   │   ├── News.jsx
│   │   │   └── Admin.jsx
│   │   ├── components/      # Reusable components
│   │   ├── hooks/           # Custom React hooks
│   │   └── utils/           # Utilities
│   └── public/
│
└── README.md
```

## Design Patterns

### Creational Patterns
- **Singleton**: Redis client, OpenAI client instances
- **Factory**: Router creation in `routers/__init__.py`
- **Builder**: Pydantic models for request validation

### Structural Patterns
- **Adapter**: API client wrapper (`frontend/src/api/index.js`)
- **Facade**: Database operations (`database.py`)
- **Decorator**: FastAPI route decorators

### Behavioral Patterns
- **Observer**: WebSocket broadcast system
- **Strategy**: Signal evaluation algorithms
- **Command**: Router endpoints as commands
- **State**: React hooks state management

### Architectural Patterns
- **Layered Architecture**: UI → API → Services → Data
- **Repository Pattern**: Database CRUD operations
- **Dependency Injection**: FastAPI `Depends()`

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis Server
- SQLite

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY="your-secret-key"
export OPENAI_API_KEY="your-openai-key"
export DB_PATH="/path/to/cryptosignal.db"

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Development
npm run dev

# Production build
npm run build
```

### Workers Setup

```bash
# Start background workers
python workers/worker_prices.py &
python workers/worker_signal_checker.py &
python workers/worker_sentiment.py &
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | User login |
| GET | `/api/auth/me` | Get current user |

### Signals
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/signals` | Get all trading signals |
| GET | `/api/signals/stats` | Signal performance stats |

### Portfolio
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portfolio` | Get user portfolio |
| PUT | `/api/portfolio` | Update portfolio |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analyze/{symbol}` | Detailed coin analysis |
| GET | `/api/ai/summary` | AI market summary |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `/ws/{user_id}` | Real-time price updates |

## Configuration

Key configuration in `backend/config.py`:

```python
# LLM Usage Limits
LLM_LIMITS = {
    "free": 0,      # Uses ad credits
    "pro": 20,      # 20 analyses/day
    "admin": 999999
}

# Ad Reward Settings
AD_REWARD_COOLDOWN = 60  # seconds between ads
AD_WATCH_DURATION = 15   # seconds to watch
MAX_AD_CREDITS = 10      # max stored credits
```

## User Tiers

| Feature | Free | Pro | Admin |
|---------|------|-----|-------|
| Trading Signals | Unlimited | Unlimited | Unlimited |
| AI Analysis | Ad Credits | 20/day | Unlimited |
| Portfolio | Basic | Full | Full |
| Real-time Updates | Yes | Yes | Yes |
| Admin Panel | No | No | Yes |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- [CoinGecko API](https://www.coingecko.com/) - Cryptocurrency data
- [OpenAI](https://openai.com/) - AI analysis
- [Alternative.me](https://alternative.me/) - Fear & Greed Index
