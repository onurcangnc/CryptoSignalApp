# -*- coding: utf-8 -*-
"""
CryptoSignal - Database
=======================
SQLite veritabanı bağlantısı ve CRUD fonksiyonları
"""

import sqlite3
import json
import hashlib
import secrets
import redis
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, Dict, List, Any

from config import DB_PATH, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

# =============================================================================
# REDIS CONNECTION
# =============================================================================

class RedisClientProxy:
    """Lazy Redis client proxy - ilk erişimde bağlantı kur"""
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True,
                password=REDIS_PASSWORD
            )
        return self._client

    def __getattr__(self, name):
        return getattr(self._get_client(), name)

redis_client = RedisClientProxy()

# =============================================================================
# SQLITE CONNECTION
# =============================================================================

@contextmanager
def get_db():
    """SQLite bağlantısı context manager"""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Veritabanı tablolarını oluştur"""
    with get_db() as conn:
        c = conn.cursor()
        
        # Users
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT,
                password_salt TEXT,
                tier TEXT DEFAULT "free",
                created_at TEXT,
                last_login TEXT,
                ad_credits INTEGER DEFAULT 0
            )
        ''')

        # Add ad_credits column if not exists (for existing databases)
        try:
            c.execute("ALTER TABLE users ADD COLUMN ad_credits INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Portfolios
        c.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                user_id TEXT PRIMARY KEY,
                holdings TEXT DEFAULT "[]",
                updated_at TEXT
            )
        ''')
        
        # Forecasts
        c.execute('''
            CREATE TABLE IF NOT EXISTS forecasts (
                user_id TEXT PRIMARY KEY,
                data TEXT,
                created_at TEXT
            )
        ''')
        
        # Invites
        c.execute('''
            CREATE TABLE IF NOT EXISTS invites (
                token TEXT PRIMARY KEY,
                tier TEXT DEFAULT "free",
                note TEXT,
                used INTEGER DEFAULT 0,
                used_by TEXT,
                created_at TEXT
            )
        ''')
        
        # News
        c.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id TEXT PRIMARY KEY,
                title TEXT,
                summary TEXT,
                ai_summary TEXT,
                source TEXT,
                source_url TEXT UNIQUE,
                published_at TEXT,
                sentiment TEXT,
                sentiment_score REAL,
                coins TEXT DEFAULT "[]",
                risk TEXT,
                analyzed_by TEXT,
                created_at TEXT
            )
        ''')
        
        # LLM Usage
        c.execute('''
            CREATE TABLE IF NOT EXISTS llm_usage (
                user_id TEXT,
                date TEXT,
                count INTEGER DEFAULT 0,
                PRIMARY KEY(user_id, date)
            )
        ''')
        
        # News Summaries
        c.execute('''
            CREATE TABLE IF NOT EXISTS news_summaries (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                summary TEXT,
                coins TEXT,
                news_count INTEGER,
                sentiment TEXT,
                created_at TEXT
            )
        ''')

        # LLM Analytics (Enhanced tracking)
        c.execute('''
            CREATE TABLE IF NOT EXISTS llm_analytics (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                feature TEXT,
                tokens_used INTEGER,
                cost_usd REAL,
                model TEXT,
                response_time_ms INTEGER,
                created_at TEXT
            )
        ''')

        # Portfolio Simulations
        c.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_simulations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                scenario_type TEXT,
                parameters TEXT,
                results TEXT,
                created_at TEXT
            )
        ''')

        # Signal Tracking (Sinyal doğruluk takibi)
        c.execute('''
            CREATE TABLE IF NOT EXISTS signal_tracking (
                id TEXT PRIMARY KEY,
                symbol TEXT,
                signal TEXT,
                signal_tr TEXT,
                confidence INTEGER,
                entry_price REAL,
                target_price REAL,
                stop_loss REAL,
                timeframe TEXT,
                created_at TEXT,
                check_date TEXT,
                actual_price REAL,
                result TEXT,
                profit_loss_pct REAL,
                is_successful INTEGER
            )
        ''')

        # Pending Payments (Bekleyen ödemeler)
        c.execute('''
            CREATE TABLE IF NOT EXISTS pending_payments (
                payment_id TEXT PRIMARY KEY,
                user_id TEXT,
                order_id TEXT UNIQUE,
                tier TEXT,
                duration_months INTEGER,
                amount_usd REAL,
                created_at TEXT
            )
        ''')

        # Payment History (Ödeme geçmişi)
        c.execute('''
            CREATE TABLE IF NOT EXISTS payment_history (
                payment_id TEXT PRIMARY KEY,
                user_id TEXT,
                order_id TEXT,
                tier TEXT,
                amount_usd REAL,
                amount_crypto REAL,
                currency TEXT,
                created_at TEXT
            )
        ''')

        # User subscription info (users tablosuna eklenmeli ama şimdilik ayrı tablo)
        c.execute('''
            ALTER TABLE users ADD COLUMN subscription_expires TEXT
        ''' if False else '''
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                user_id TEXT PRIMARY KEY,
                tier TEXT,
                expires_at TEXT,
                auto_renew INTEGER DEFAULT 0,
                updated_at TEXT
            )
        ''')

        # User Watchlist (Favoriler)
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_watchlist (
                user_id TEXT,
                symbol TEXT,
                added_at TEXT,
                PRIMARY KEY(user_id, symbol)
            )
        ''')

        # Price Alerts (Fiyat Alarmları)
        c.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                symbol TEXT,
                target_price REAL,
                condition TEXT,
                created_at TEXT,
                triggered INTEGER DEFAULT 0,
                triggered_at TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')

        # Add indexes for performance
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_llm_usage_user_date
            ON llm_usage(user_id, date)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_portfolios_user
            ON portfolios(user_id)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_published
            ON news(published_at DESC)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_llm_analytics_user
            ON llm_analytics(user_id, created_at DESC)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_signal_tracking_symbol
            ON signal_tracking(symbol, created_at DESC)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_signal_tracking_check
            ON signal_tracking(check_date, is_successful)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_watchlist_user
            ON user_watchlist(user_id, added_at DESC)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_price_alerts_user
            ON price_alerts(user_id, is_active, triggered)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_price_alerts_active
            ON price_alerts(is_active, triggered)
        """)

        # Default invites
        c.execute(
            "INSERT OR IGNORE INTO invites VALUES (?,?,?,0,NULL,?)",
            ('ADMIN-ONURCAN-2024', 'admin', 'Admin', datetime.utcnow().isoformat())
        )
        c.execute(
            "INSERT OR IGNORE INTO invites VALUES (?,?,?,0,NULL,?)",
            ('FREE-USER-2024', 'free', 'Free', datetime.utcnow().isoformat())
        )

        conn.commit()
    
    print("[DB] Initialized")


# =============================================================================
# PASSWORD HASHING
# =============================================================================

def hash_password(password: str, salt: str) -> str:
    """Şifreyi hashle"""
    combined = f"{salt}{password}{salt}"
    for _ in range(10000):
        combined = hashlib.sha256(combined.encode()).hexdigest()
    return combined


# =============================================================================
# USER CRUD
# =============================================================================

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """ID ile kullanıcı getir"""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict]:
    """Email ile kullanıcı getir"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(email)=LOWER(?)",
            (email.strip(),)
        ).fetchone()
        return dict(row) if row else None


def create_user(user_id: str, email: str, password: str, tier: str = "free") -> bool:
    """Yeni kullanıcı oluştur"""
    salt = secrets.token_hex(32)
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO users VALUES (?,?,?,?,?,?,NULL,?)",
                (user_id, email.lower().strip(), hash_password(password, salt),
                 salt, tier, datetime.utcnow().isoformat(), 0)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def verify_user(email: str, password: str) -> Optional[Dict]:
    """Kullanıcı doğrula"""
    user = get_user_by_email(email)
    if user and hash_password(password, user["password_salt"]) == user["password_hash"]:
        with get_db() as conn:
            conn.execute(
                "UPDATE users SET last_login=? WHERE id=?",
                (datetime.utcnow().isoformat(), user["id"])
            )
            conn.commit()
        return user
    return None


def get_all_users() -> List[Dict]:
    """Tüm kullanıcıları getir"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, email, tier, created_at, last_login FROM users"
        ).fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# PORTFOLIO CRUD
# =============================================================================

def get_portfolio(user_id: str) -> Dict:
    """Kullanıcı portföyünü getir"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM portfolios WHERE user_id=?",
            (user_id,)
        ).fetchone()
        
        if row and row["holdings"]:
            try:
                data = json.loads(row["holdings"])
                if isinstance(data, list):
                    return {
                        "user_id": user_id,
                        "holdings": data,
                        "updated_at": row["updated_at"],
                        "budget": None,
                        "budget_currency": "USD"
                    }
                else:
                    return {"user_id": user_id, **data, "updated_at": row["updated_at"]}
            except json.JSONDecodeError:
                pass
        
        return {
            "user_id": user_id,
            "holdings": [],
            "updated_at": None,
            "budget": None,
            "budget_currency": "USD"
        }


def save_portfolio(user_id: str, holdings: List, budget: float = None, 
                   budget_currency: str = "USD") -> None:
    """Portföyü kaydet"""
    with get_db() as conn:
        data = {
            "holdings": holdings,
            "budget": budget,
            "budget_currency": budget_currency
        }
        conn.execute(
            "INSERT OR REPLACE INTO portfolios VALUES (?,?,?)",
            (user_id, json.dumps(data), datetime.utcnow().isoformat())
        )
        conn.commit()


# =============================================================================
# FORECAST CRUD
# =============================================================================

def get_forecast(user_id: str) -> Optional[Dict]:
    """Kullanıcı tahminini getir"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT data FROM forecasts WHERE user_id=?",
            (user_id,)
        ).fetchone()
        if row and row["data"]:
            try:
                return json.loads(row["data"])
            except json.JSONDecodeError:
                pass
    return None


def save_forecast(user_id: str, forecast_data: Dict) -> None:
    """Tahmini kaydet"""
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO forecasts VALUES (?,?,?)",
            (user_id, json.dumps(forecast_data), datetime.utcnow().isoformat())
        )
        conn.commit()


# =============================================================================
# INVITE CRUD
# =============================================================================

def get_invite(token: str) -> Optional[Dict]:
    """Davet kodunu getir"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM invites WHERE token=?",
            (token,)
        ).fetchone()
        return dict(row) if row else None


def use_invite(token: str, user_id: str) -> None:
    """Davet kodunu kullan"""
    with get_db() as conn:
        conn.execute(
            "UPDATE invites SET used=1, used_by=? WHERE token=?",
            (user_id, token)
        )
        conn.commit()


def get_all_invites() -> List[Dict]:
    """Tüm davet kodlarını getir"""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM invites").fetchall()
        return [dict(row) for row in rows]


def create_invite(token: str, tier: str, note: str) -> None:
    """Yeni davet kodu oluştur"""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO invites VALUES (?,?,?,0,NULL,?)",
            (token, tier, note, datetime.utcnow().isoformat())
        )
        conn.commit()


# =============================================================================
# AD CREDITS CRUD (Reklam izleme ile kazanılan AI kredileri)
# =============================================================================

def get_ad_credits(user_id: str) -> int:
    """Kullanıcının reklam kredilerini getir"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT ad_credits FROM users WHERE id=?",
            (user_id,)
        ).fetchone()
        return row["ad_credits"] if row and row["ad_credits"] else 0


def add_ad_credit(user_id: str, amount: int = 1) -> int:
    """Kullanıcıya reklam kredisi ekle"""
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET ad_credits = COALESCE(ad_credits, 0) + ? WHERE id=?",
            (amount, user_id)
        )
        conn.commit()
    return get_ad_credits(user_id)


def use_ad_credit(user_id: str) -> bool:
    """Reklam kredisi kullan (varsa)"""
    credits = get_ad_credits(user_id)
    if credits <= 0:
        return False

    with get_db() as conn:
        conn.execute(
            "UPDATE users SET ad_credits = ad_credits - 1 WHERE id=? AND ad_credits > 0",
            (user_id,)
        )
        conn.commit()
    return True


def get_last_ad_reward_time(user_id: str) -> Optional[str]:
    """Son reklam ödülü zamanını getir (spam önleme)"""
    key = f"last_ad_reward:{user_id}"
    return redis_client.get(key)


def set_last_ad_reward_time(user_id: str) -> None:
    """Son reklam ödülü zamanını kaydet"""
    key = f"last_ad_reward:{user_id}"
    redis_client.setex(key, 60, datetime.utcnow().isoformat())  # 60 saniye cooldown


# =============================================================================
# LLM USAGE CRUD
# =============================================================================

def today_str() -> str:
    """Bugünün tarihini string olarak döndür"""
    return datetime.utcnow().strftime("%Y-%m-%d")


def get_llm_usage(user_id: str, date: str) -> int:
    """Kullanıcının LLM kullanımını getir"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT count FROM llm_usage WHERE user_id=? AND date=?",
            (user_id, date)
        ).fetchone()
        return row["count"] if row else 0


def increment_llm_usage(user_id: str, date: str) -> None:
    """LLM kullanımını artır"""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO llm_usage VALUES (?,?,1) ON CONFLICT(user_id,date) DO UPDATE SET count=count+1",
            (user_id, date)
        )
        conn.commit()


def get_total_llm_usage(user_id: str) -> int:
    """Kullanıcının toplam LLM kullanımını getir"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT SUM(count) as total FROM llm_usage WHERE user_id=?",
            (user_id,)
        ).fetchone()
        return row["total"] if row and row["total"] else 0


# =============================================================================
# NEWS SUMMARY CRUD
# =============================================================================

def save_news_summary(user_id: str, summary: str, coins: List[str], 
                      news_count: int, sentiment: str) -> None:
    """Haber özetini kaydet"""
    from uuid import uuid4
    with get_db() as conn:
        conn.execute(
            "INSERT INTO news_summaries VALUES (?,?,?,?,?,?,?)",
            (str(uuid4()), user_id, summary, json.dumps(coins), 
             news_count, sentiment, datetime.utcnow().isoformat())
        )
        conn.commit()


def get_news_summaries(user_id: str, limit: int = 10) -> List[Dict]:
    """Kullanıcının haber özetlerini getir"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM news_summaries WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return [
            {
                "id": r["id"],
                "summary": r["summary"],
                "coins": json.loads(r["coins"]) if r["coins"] else [],
                "news_count": r["news_count"],
                "sentiment": r["sentiment"],
                "created_at": r["created_at"]
            }
            for r in rows
        ]


# =============================================================================
# LLM ANALYTICS CRUD
# =============================================================================

def save_llm_analytics(user_id: str, feature: str, tokens_used: int,
                       cost_usd: float, model: str, response_time_ms: int) -> None:
    """LLM analytics kaydı"""
    from uuid import uuid4
    with get_db() as conn:
        conn.execute(
            "INSERT INTO llm_analytics VALUES (?,?,?,?,?,?,?,?)",
            (str(uuid4()), user_id, feature, tokens_used, cost_usd,
             model, response_time_ms, datetime.utcnow().isoformat())
        )
        conn.commit()


def get_llm_analytics(start_date: str = None, end_date: str = None) -> List[Dict]:
    """LLM analytics verilerini getir"""
    with get_db() as conn:
        if start_date and end_date:
            rows = conn.execute(
                "SELECT * FROM llm_analytics WHERE created_at >= ? AND created_at <= ? ORDER BY created_at DESC",
                (start_date, end_date)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM llm_analytics ORDER BY created_at DESC LIMIT 1000"
            ).fetchall()
        return [dict(row) for row in rows]


def get_llm_stats_by_feature() -> Dict[str, Dict]:
    """Feature bazlı LLM istatistikleri"""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT feature, COUNT(*) as calls, SUM(cost_usd) as total_cost,
                   SUM(tokens_used) as total_tokens
            FROM llm_analytics
            GROUP BY feature
        """).fetchall()
        return {row["feature"]: dict(row) for row in rows}


def get_llm_stats_by_user(limit: int = 10) -> List[Dict]:
    """Kullanıcı bazlı LLM istatistikleri"""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT user_id, COUNT(*) as calls, SUM(cost_usd) as total_cost,
                   users.email, users.tier
            FROM llm_analytics
            LEFT JOIN users ON llm_analytics.user_id = users.id
            GROUP BY user_id
            ORDER BY calls DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]


# =============================================================================
# PORTFOLIO SIMULATION CRUD
# =============================================================================

def save_portfolio_simulation(user_id: str, scenario_type: str,
                              parameters: Dict, results: Dict) -> str:
    """Portfolio simulation kaydı"""
    from uuid import uuid4
    sim_id = str(uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO portfolio_simulations VALUES (?,?,?,?,?,?)",
            (sim_id, user_id, scenario_type, json.dumps(parameters),
             json.dumps(results), datetime.utcnow().isoformat())
        )
        conn.commit()
    return sim_id


def get_portfolio_simulations(user_id: str, limit: int = 10) -> List[Dict]:
    """Kullanıcının simulation geçmişini getir"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM portfolio_simulations WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return [
            {
                "id": r["id"],
                "scenario_type": r["scenario_type"],
                "parameters": json.loads(r["parameters"]) if r["parameters"] else {},
                "results": json.loads(r["results"]) if r["results"] else {},
                "created_at": r["created_at"]
            }
            for r in rows
        ]


# =============================================================================
# SIGNAL TRACKING CRUD
# =============================================================================

def save_signal_track(symbol: str, signal: str, signal_tr: str, confidence: int,
                      entry_price: float, target_price: float, stop_loss: float,
                      timeframe: str,
                      # v2.1 yeni parametreler
                      trailing_stop: float = None,
                      trailing_stop_pct: float = 2.0,
                      risk_reward_ratio: str = None,
                      stop_loss_pct: float = None,
                      take_profit_pct: float = None
                      ) -> str:
    """Sinyal kaydı oluştur (v2.1 - Exit Strategy destegi)"""
    from uuid import uuid4
    signal_id = str(uuid4())

    # Check date hesapla (timeframe'e göre)
    check_days = {
        "1d": 1,
        "1w": 7,
        "1m": 30,
        "3m": 90,
        "6m": 180,
        "1y": 365
    }
    days = check_days.get(timeframe, 7)
    check_date = (datetime.utcnow() + timedelta(days=days)).isoformat()

    with get_db() as conn:
        conn.execute("""
            INSERT INTO signal_tracking (
                id, symbol, signal, signal_tr, confidence, entry_price,
                target_price, stop_loss, timeframe, created_at, check_date,
                trailing_stop, trailing_stop_pct, highest_price, lowest_price,
                risk_reward_ratio, stop_loss_pct, take_profit_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_id, symbol, signal, signal_tr, confidence, entry_price,
            target_price, stop_loss, timeframe, datetime.utcnow().isoformat(),
            check_date,
            trailing_stop, trailing_stop_pct, entry_price, entry_price,
            risk_reward_ratio, stop_loss_pct, take_profit_pct
        ))
        conn.commit()

    return signal_id


def check_signal_results() -> List[Dict]:
    """Kontrol tarihi gelen sinyalleri değerlendir"""
    with get_db() as conn:
        now = datetime.utcnow().isoformat()

        # Henüz kontrol edilmemiş ve tarihi gelmiş sinyaller
        rows = conn.execute(
            "SELECT * FROM signal_tracking WHERE check_date <= ? AND result IS NULL",
            (now,)
        ).fetchall()

        return [dict(row) for row in rows]


def update_signal_result(signal_id: str, actual_price: float) -> None:
    """Sinyal sonucunu güncelle"""
    with get_db() as conn:
        # Sinyal bilgilerini al
        row = conn.execute(
            "SELECT * FROM signal_tracking WHERE id=?",
            (signal_id,)
        ).fetchone()

        if not row:
            return

        entry_price = row["entry_price"]
        target_price = row["target_price"]
        stop_loss = row["stop_loss"]
        signal = row["signal"]

        # Ham fiyat değişimi
        raw_price_change_pct = ((actual_price - entry_price) / entry_price * 100) if entry_price > 0 else 0

        # Başarılı mı?
        is_successful = 0
        result = ""
        profit_loss_pct = 0  # Gerçek kar/zarar (sinyal yönüne göre)

        if signal in ["BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"]:
            # AL sinyali - fiyat yükseldi mi?
            # AL sinyalinde: fiyat yükselirse kâr
            profit_loss_pct = raw_price_change_pct

            if actual_price >= target_price:
                is_successful = 1
                result = "TARGET_HIT"
            elif actual_price <= stop_loss:
                is_successful = 0
                result = "STOP_LOSS"
            elif actual_price > entry_price:
                is_successful = 1
                result = "PROFIT"
            else:
                is_successful = 0
                result = "LOSS"

        elif signal in ["SELL", "SAT", "STRONG_SELL", "GÜÇLÜ SAT"]:
            # SAT sinyali - fiyat düştü mü?
            # SAT sinyalinde: fiyat düşerse kâr (short pozisyon mantığı)
            # Yani fiyat %10 düşerse, bu %10 kâr demek
            profit_loss_pct = -raw_price_change_pct  # Ters çevir

            if actual_price <= target_price:
                is_successful = 1
                result = "TARGET_HIT"
            elif actual_price >= stop_loss:
                is_successful = 0
                result = "STOP_LOSS"
            elif actual_price < entry_price:
                is_successful = 1
                result = "PROFIT"
            else:
                is_successful = 0
                result = "LOSS"

        else:  # HOLD, BEKLE
            # Bekle sinyali - stabilite kontrolü
            # BEKLE sinyali = pozisyon alma = kar/zarar yok
            profit_loss_pct = 0  # BEKLE sinyallerinde kar/zarar yok

            if abs(raw_price_change_pct) < 5:
                is_successful = 1
                result = "STABLE"
            else:
                is_successful = 0
                result = "VOLATILE"

        # Güncelle
        conn.execute(
            """UPDATE signal_tracking
               SET actual_price=?, result=?, profit_loss_pct=?, is_successful=?
               WHERE id=?""",
            (actual_price, result, profit_loss_pct, is_successful, signal_id)
        )
        conn.commit()


def calculate_compound_return(profit_loss_pcts: list, initial_amount: float = 100) -> Dict:
    """
    Bileşik getiri simülasyonu hesapla

    Args:
        profit_loss_pcts: Her sinyalin P/L yüzdeleri listesi (tarih sırasına göre)
        initial_amount: Başlangıç tutarı (varsayılan 100₺)

    Returns:
        Dict: initial_amount, final_amount, total_return_pct

    Örnek:
        [+10%, -5%, +15%] -> 100 * 1.10 * 0.95 * 1.15 = 120.175₺ (+20.175%)
    """
    if not profit_loss_pcts:
        return {
            "initial_amount": initial_amount,
            "final_amount": initial_amount,
            "total_return_pct": 0
        }

    amount = initial_amount

    for pnl_pct in profit_loss_pcts:
        # Aşırı değerleri sınırla (±50% max)
        capped_pnl = max(-50, min(50, pnl_pct))
        amount *= (1 + capped_pnl / 100)

    total_return_pct = ((amount - initial_amount) / initial_amount) * 100

    return {
        "initial_amount": round(initial_amount, 2),
        "final_amount": round(amount, 2),
        "total_return_pct": round(total_return_pct, 2)
    }


def get_signal_success_rate(days: int = 30, symbol: str = None) -> Dict:
    """Sinyal başarı oranı istatistikleri - Gelişmiş versiyon"""
    MIN_SIGNALS_REQUIRED = 30  # İstatistiksel anlamlılık için minimum

    try:
        with get_db() as conn:
            # Tarih filtresi
            since = (datetime.utcnow() - timedelta(days=days)).isoformat()

            if symbol:
                # Belirli bir coin için
                total = conn.execute(
                    "SELECT COUNT(*) as cnt FROM signal_tracking WHERE symbol=? AND created_at >= ? AND result IS NOT NULL",
                    (symbol, since)
                ).fetchone()["cnt"]

                successful = conn.execute(
                    "SELECT COUNT(*) as cnt FROM signal_tracking WHERE symbol=? AND created_at >= ? AND is_successful=1",
                    (symbol, since)
                ).fetchone()["cnt"]
            else:
                # Tüm coinler
                total = conn.execute(
                    "SELECT COUNT(*) as cnt FROM signal_tracking WHERE created_at >= ? AND result IS NOT NULL",
                    (since,)
                ).fetchone()["cnt"]

                successful = conn.execute(
                    "SELECT COUNT(*) as cnt FROM signal_tracking WHERE created_at >= ? AND is_successful=1",
                    (since,)
                ).fetchone()["cnt"]

            # Yetersiz veri kontrolü
            if total < MIN_SIGNALS_REQUIRED:
                return {
                    "insufficient_data": True,
                    "total_signals": total,
                    "min_required": MIN_SIGNALS_REQUIRED,
                    "message": f"AI henüz yeterli veri toplamadı. {MIN_SIGNALS_REQUIRED - total} sinyal daha gerekiyor.",
                    "progress_pct": round((total / MIN_SIGNALS_REQUIRED) * 100, 1)
                }

            success_rate = (successful / total * 100) if total > 0 else 0

            # YENİ: Ortalama kazanç (sadece kârlı sinyaller)
            avg_profit_row = conn.execute(
                """SELECT AVG(profit_loss_pct) as avg_profit
                   FROM signal_tracking
                   WHERE created_at >= ? AND is_successful=1 AND profit_loss_pct > 0""",
                (since,)
            ).fetchone()
            avg_profit = avg_profit_row["avg_profit"] if avg_profit_row["avg_profit"] else 0

            # YENİ: Ortalama kayıp (sadece zararlı sinyaller)
            avg_loss_row = conn.execute(
                """SELECT AVG(profit_loss_pct) as avg_loss
                   FROM signal_tracking
                   WHERE created_at >= ? AND is_successful=0 AND profit_loss_pct < 0""",
                (since,)
            ).fetchone()
            avg_loss = avg_loss_row["avg_loss"] if avg_loss_row["avg_loss"] else 0

            # YENİ: Bileşik getiri simülasyonu - SADECE AL/SAT sinyalleri (BEKLE hariç)
            # BEKLE = pozisyon yok = bileşik getiriye dahil edilmemeli
            trade_signals = conn.execute(
                """SELECT profit_loss_pct, signal FROM signal_tracking
                   WHERE created_at >= ? AND result IS NOT NULL
                   AND signal IN ('AL', 'BUY', 'STRONG_BUY', 'GÜÇLÜ AL', 'SAT', 'SELL', 'STRONG_SELL', 'GÜÇLÜ SAT')
                   ORDER BY created_at ASC""",
                (since,)
            ).fetchall()

            compound_return = calculate_compound_return([s["profit_loss_pct"] for s in trade_signals])

            # YENİ: En başarılı 3 sinyal
            top_signals_rows = conn.execute(
                """SELECT symbol, profit_loss_pct, created_at, signal
                   FROM signal_tracking
                   WHERE created_at >= ? AND is_successful=1
                   ORDER BY profit_loss_pct DESC LIMIT 3""",
                (since,)
            ).fetchall()

            top_signals = [
                {
                    "symbol": row["symbol"],
                    "profit_pct": round(row["profit_loss_pct"], 1),
                    "date": row["created_at"],
                    "signal": row["signal"]
                }
                for row in top_signals_rows
            ]

            # YENİ: En kötü sinyal (şeffaflık için)
            worst_signal_row = conn.execute(
                """SELECT symbol, profit_loss_pct, created_at, signal
                   FROM signal_tracking
                   WHERE created_at >= ? AND result IS NOT NULL
                   ORDER BY profit_loss_pct ASC LIMIT 1""",
                (since,)
            ).fetchone()

            worst_signal = None
            if worst_signal_row and worst_signal_row["profit_loss_pct"] < 0:
                worst_signal = {
                    "symbol": worst_signal_row["symbol"],
                    "loss_pct": round(worst_signal_row["profit_loss_pct"], 1),
                    "date": worst_signal_row["created_at"],
                    "signal": worst_signal_row["signal"]
                }

            # Sinyal tiplerine göre breakdown
            signal_breakdown = conn.execute(
                """SELECT signal, COUNT(*) as total,
                          SUM(is_successful) as successful,
                          AVG(profit_loss_pct) as avg_pnl
                   FROM signal_tracking
                   WHERE created_at >= ? AND result IS NOT NULL
                   GROUP BY signal""",
                (since,)
            ).fetchall()

            # YENİ: Trade (AL/SAT) vs BEKLE ayrımı
            # trade_total: Tüm üretilen trade sinyalleri (result şartı YOK)
            trade_total = conn.execute(
                """SELECT COUNT(*) as cnt FROM signal_tracking
                   WHERE created_at >= ?
                   AND signal IN ('AL', 'BUY', 'STRONG_BUY', 'GÜÇLÜ AL', 'SAT', 'SELL', 'STRONG_SELL', 'GÜÇLÜ SAT')""",
                (since,)
            ).fetchone()["cnt"]

            # trade_evaluated: Sonucu kesinleşmiş trade'ler (result/actual_price dolu)
            trade_evaluated = conn.execute(
                """SELECT COUNT(*) as cnt FROM signal_tracking
                   WHERE created_at >= ? AND result IS NOT NULL AND actual_price IS NOT NULL
                   AND signal IN ('AL', 'BUY', 'STRONG_BUY', 'GÜÇLÜ AL', 'SAT', 'SELL', 'STRONG_SELL', 'GÜÇLÜ SAT')""",
                (since,)
            ).fetchone()["cnt"]

            # trade_successful: Başarılı trade'ler (evaluated içinden)
            trade_successful = conn.execute(
                """SELECT COUNT(*) as cnt FROM signal_tracking
                   WHERE created_at >= ? AND is_successful=1 AND result IS NOT NULL
                   AND signal IN ('AL', 'BUY', 'STRONG_BUY', 'GÜÇLÜ AL', 'SAT', 'SELL', 'STRONG_SELL', 'GÜÇLÜ SAT')""",
                (since,)
            ).fetchone()["cnt"]

            # Success rate: evaluated trade'ler üzerinden hesapla
            trade_success_rate = (trade_successful / trade_evaluated * 100) if trade_evaluated > 0 else 0

            # YENİ: Gelişmiş Trading Metrikleri
            # Avg Win (sadece kazançlı trade'ler)
            avg_win_row = conn.execute(
                """SELECT AVG(profit_loss_pct) as avg_win, COUNT(*) as win_count
                   FROM signal_tracking
                   WHERE created_at >= ? AND profit_loss_pct > 0
                   AND signal IN ('AL', 'BUY', 'STRONG_BUY', 'GÜÇLÜ AL', 'SAT', 'SELL', 'STRONG_SELL', 'GÜÇLÜ SAT')""",
                (since,)
            ).fetchone()
            avg_win = avg_win_row["avg_win"] if avg_win_row["avg_win"] else 0
            win_count = avg_win_row["win_count"] or 0

            # Avg Loss (sadece kayıplı trade'ler)
            avg_loss_row = conn.execute(
                """SELECT AVG(profit_loss_pct) as avg_loss, COUNT(*) as loss_count
                   FROM signal_tracking
                   WHERE created_at >= ? AND profit_loss_pct < 0
                   AND signal IN ('AL', 'BUY', 'STRONG_BUY', 'GÜÇLÜ AL', 'SAT', 'SELL', 'STRONG_SELL', 'GÜÇLÜ SAT')""",
                (since,)
            ).fetchone()
            avg_loss_trade = avg_loss_row["avg_loss"] if avg_loss_row["avg_loss"] else 0
            loss_count = avg_loss_row["loss_count"] or 0

            # Profit Factor = Toplam Kazanç / Toplam Kayıp (mutlak değer)
            total_wins_row = conn.execute(
                """SELECT SUM(profit_loss_pct) as total_wins
                   FROM signal_tracking
                   WHERE created_at >= ? AND profit_loss_pct > 0
                   AND signal IN ('AL', 'BUY', 'STRONG_BUY', 'GÜÇLÜ AL', 'SAT', 'SELL', 'STRONG_SELL', 'GÜÇLÜ SAT')""",
                (since,)
            ).fetchone()
            total_wins = total_wins_row["total_wins"] if total_wins_row["total_wins"] else 0

            total_losses_row = conn.execute(
                """SELECT SUM(ABS(profit_loss_pct)) as total_losses
                   FROM signal_tracking
                   WHERE created_at >= ? AND profit_loss_pct < 0
                   AND signal IN ('AL', 'BUY', 'STRONG_BUY', 'GÜÇLÜ AL', 'SAT', 'SELL', 'STRONG_SELL', 'GÜÇLÜ SAT')""",
                (since,)
            ).fetchone()
            total_losses = total_losses_row["total_losses"] if total_losses_row["total_losses"] else 0

            profit_factor = (total_wins / total_losses) if total_losses > 0 else (999 if total_wins > 0 else 0)

            # Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
            # Bu her trade başına beklenen ortalama getiri
            win_rate = (win_count / trade_total) if trade_total > 0 else 0
            loss_rate = (loss_count / trade_total) if trade_total > 0 else 0
            expectancy = (win_rate * avg_win) - (loss_rate * abs(avg_loss_trade))

            # Risk/Reward Ratio = Avg Win / Avg Loss (mutlak değer)
            risk_reward = (avg_win / abs(avg_loss_trade)) if avg_loss_trade != 0 else 0

            return {
                "total_signals": total,
                "successful_signals": successful,
                "success_rate": round(success_rate, 2),
                "days": days,
                "symbol": symbol,

                # YENİ: Trade-only metrikler (AL/SAT - BEKLE hariç)
                "trade_total": trade_total,           # Tüm trade sinyalleri (henüz değerlendirilmemiş dahil)
                "trade_evaluated": trade_evaluated,   # Sonucu kesinleşmiş trade'ler
                "trade_successful": trade_successful, # Başarılı trade'ler
                "trade_success_rate": round(trade_success_rate, 2),  # evaluated üzerinden hesaplanır

                # YENİ: Gelişmiş metrikler
                "avg_profit_pct": round(avg_profit, 2),
                "avg_loss_pct": round(avg_loss, 2),
                "compound_return": compound_return,
                "top_signals": top_signals,
                "worst_signal": worst_signal,

                # YENİ: Profesyonel Trading Metrikleri
                "avg_win": round(avg_win, 2),           # Ortalama kazanç %
                "avg_loss": round(avg_loss_trade, 2),   # Ortalama kayıp %
                "win_count": win_count,                  # Kazançlı trade sayısı
                "loss_count": loss_count,                # Kayıplı trade sayısı
                "profit_factor": round(profit_factor, 2),  # Toplam Kazanç / Toplam Kayıp
                "expectancy": round(expectancy, 2),     # Trade başına beklenen getiri %
                "risk_reward": round(risk_reward, 2),   # Risk/Ödül oranı

                # Mevcut breakdown
                "by_signal": [
                    {
                        "signal": row["signal"],
                        "total": row["total"],
                        "successful": row["successful"],
                        "success_rate": round((row["successful"] / row["total"] * 100) if row["total"] > 0 else 0, 2),
                        "avg_pnl": round(row["avg_pnl"], 2) if row["avg_pnl"] else 0
                    }
                    for row in signal_breakdown
                ]
            }
    except sqlite3.OperationalError as e:
        # Tablo yoksa veya schema hatası varsa boş sonuç dön
        print(f"[DB] Signal tracking error: {e}")
        return {
            "total_signals": 0,
            "successful_signals": 0,
            "success_rate": 0,
            "days": days,
            "symbol": symbol,
            "by_signal": []
        }


# =============================================================================
# WATCHLIST (Favoriler)
# =============================================================================

def add_to_watchlist(user_id: str, symbol: str) -> bool:
    """Favori listesine coin ekle"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR IGNORE INTO user_watchlist (user_id, symbol, added_at)
                VALUES (?, ?, ?)
            """, (user_id, symbol.upper(), datetime.utcnow().isoformat()))
            conn.commit()
            return True
    except Exception as e:
        print(f"[DB] Watchlist add error: {e}")
        return False


def remove_from_watchlist(user_id: str, symbol: str) -> bool:
    """Favori listesinden coin çıkar"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                DELETE FROM user_watchlist
                WHERE user_id = ? AND symbol = ?
            """, (user_id, symbol.upper()))
            conn.commit()
            return True
    except Exception as e:
        print(f"[DB] Watchlist remove error: {e}")
        return False


def get_user_watchlist(user_id: str) -> List[str]:
    """Kullanıcının favori coin listesini getir"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT symbol, added_at
                FROM user_watchlist
                WHERE user_id = ?
                ORDER BY added_at DESC
            """, (user_id,))

            return [
                {
                    "symbol": row["symbol"],
                    "added_at": row["added_at"]
                }
                for row in c.fetchall()
            ]
    except Exception as e:
        print(f"[DB] Watchlist get error: {e}")
        return []


def is_in_watchlist(user_id: str, symbol: str) -> bool:
    """Coin favori listesinde mi kontrol et"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT 1 FROM user_watchlist
                WHERE user_id = ? AND symbol = ?
            """, (user_id, symbol.upper()))
            return c.fetchone() is not None
    except Exception as e:
        print(f"[DB] Watchlist check error: {e}")
        return False


# =============================================================================
# PRICE ALERTS (Fiyat Alarmları)
# =============================================================================

def create_price_alert(user_id: str, symbol: str, target_price: float, condition: str) -> Optional[str]:
    """
    Fiyat alarmı oluştur

    Args:
        user_id: Kullanıcı ID
        symbol: Coin sembolü
        target_price: Hedef fiyat
        condition: 'above' (yukarı) veya 'below' (aşağı)

    Returns:
        Alert ID veya None
    """
    import uuid

    try:
        alert_id = str(uuid.uuid4())
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO price_alerts
                (id, user_id, symbol, target_price, condition, created_at, triggered, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 0, 1)
            """, (alert_id, user_id, symbol.upper(), target_price, condition, datetime.utcnow().isoformat()))
            conn.commit()
            return alert_id
    except Exception as e:
        print(f"[DB] Price alert create error: {e}")
        return None


def get_user_price_alerts(user_id: str, active_only: bool = True) -> List[Dict]:
    """Kullanıcının fiyat alarmlarını getir"""
    try:
        with get_db() as conn:
            c = conn.cursor()

            if active_only:
                c.execute("""
                    SELECT * FROM price_alerts
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                """, (user_id,))
            else:
                c.execute("""
                    SELECT * FROM price_alerts
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))

            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        print(f"[DB] Price alerts get error: {e}")
        return []


def get_active_price_alerts() -> List[Dict]:
    """Tüm aktif fiyat alarmlarını getir (worker için)"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT * FROM price_alerts
                WHERE is_active = 1 AND triggered = 0
            """)
            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        print(f"[DB] Active alerts get error: {e}")
        return []


def trigger_price_alert(alert_id: str) -> bool:
    """Fiyat alarmını tetiklenmiş olarak işaretle"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE price_alerts
                SET triggered = 1, triggered_at = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), alert_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"[DB] Alert trigger error: {e}")
        return False


def delete_price_alert(alert_id: str, user_id: str) -> bool:
    """Fiyat alarmını sil"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                DELETE FROM price_alerts
                WHERE id = ? AND user_id = ?
            """, (alert_id, user_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"[DB] Alert delete error: {e}")
        return False


def deactivate_price_alert(alert_id: str, user_id: str) -> bool:
    """Fiyat alarmını deaktif et"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE price_alerts
                SET is_active = 0
                WHERE id = ? AND user_id = ?
            """, (alert_id, user_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"[DB] Alert deactivate error: {e}")
        return False


# =============================================================================
# AI PORTFOLIO ANALYSIS (Kalıcı Kayıt)
# =============================================================================

def init_ai_analysis_table():
    """AI analiz tablosunu oluştur (yoksa)"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS ai_portfolio_analysis (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    analysis_data TEXT NOT NULL,
                    health_score INTEGER,
                    risk_level TEXT,
                    total_value REAL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    UNIQUE(user_id)
                )
            ''')
            c.execute("""
                CREATE INDEX IF NOT EXISTS idx_ai_analysis_user
                ON ai_portfolio_analysis(user_id, created_at DESC)
            """)
            conn.commit()
            print("[DB] AI portfolio analysis table initialized")
    except Exception as e:
        print(f"[DB] AI analysis table init error: {e}")


def save_ai_analysis(user_id: str, analysis_data: Dict, expires_hours: int = 24) -> bool:
    """
    AI portfolio analizini veritabanına kaydet

    Args:
        user_id: Kullanıcı ID
        analysis_data: Analiz verisi (dict)
        expires_hours: Geçerlilik süresi (saat)

    Returns:
        Başarılı mı
    """
    import uuid

    try:
        # Tabloyu oluştur (yoksa)
        init_ai_analysis_table()

        analysis_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(hours=expires_hours)

        # Metrikler çıkar
        health_score = analysis_data.get('portfolio_health', {}).get('score', 0)
        risk_level = analysis_data.get('risk_level', 'unknown')
        total_value = analysis_data.get('total_value', 0)

        with get_db() as conn:
            c = conn.cursor()
            # Eski kayıt varsa sil (UPSERT)
            c.execute("DELETE FROM ai_portfolio_analysis WHERE user_id = ?", (user_id,))
            c.execute("""
                INSERT INTO ai_portfolio_analysis
                (id, user_id, analysis_data, health_score, risk_level, total_value, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_id,
                user_id,
                json.dumps(analysis_data, ensure_ascii=False),
                health_score,
                risk_level,
                total_value,
                created_at.isoformat(),
                expires_at.isoformat()
            ))
            conn.commit()
            print(f"[DB] AI analysis saved for user {user_id}")
            return True
    except Exception as e:
        print(f"[DB] AI analysis save error: {e}")
        return False


def get_ai_analysis(user_id: str) -> Optional[Dict]:
    """
    Kullanıcının AI analizini veritabanından getir

    Returns:
        Geçerli analiz verisi veya None (süresi dolmuş/yok)
    """
    try:
        # Tabloyu oluştur (yoksa)
        init_ai_analysis_table()

        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT analysis_data, created_at, expires_at
                FROM ai_portfolio_analysis
                WHERE user_id = ?
            """, (user_id,))

            row = c.fetchone()

            if not row:
                return None

            # Süre kontrolü
            expires_at = datetime.fromisoformat(row['expires_at'])
            if datetime.utcnow() > expires_at:
                print(f"[DB] AI analysis expired for user {user_id}")
                return None

            # Analizi parse et
            analysis = json.loads(row['analysis_data'])
            analysis['_db_created_at'] = row['created_at']
            analysis['_db_expires_at'] = row['expires_at']

            return analysis
    except Exception as e:
        print(f"[DB] AI analysis get error: {e}")
        return None


def get_ai_analysis_history(user_id: str, limit: int = 10) -> List[Dict]:
    """Kullanıcının AI analiz geçmişini getir (admin için)"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, health_score, risk_level, total_value, created_at
                FROM ai_portfolio_analysis
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))

            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        print(f"[DB] AI analysis history error: {e}")
        return []
