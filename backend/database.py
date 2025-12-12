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

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    password=REDIS_PASSWORD
)

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
                "INSERT INTO users VALUES (?,?,?,?,?,?,NULL)",
                (user_id, email.lower().strip(), hash_password(password, salt), 
                 salt, tier, datetime.utcnow().isoformat())
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
                      timeframe: str) -> str:
    """Sinyal kaydı oluştur"""
    from uuid import uuid4
    signal_id = str(uuid4())

    # Check date hesapla (timeframe'e göre)
    check_days = {
        "1d": 1,
        "1w": 7,
        "3m": 90,
        "6m": 180,
        "1y": 365
    }
    days = check_days.get(timeframe, 7)
    check_date = (datetime.utcnow() + timedelta(days=days)).isoformat()

    with get_db() as conn:
        conn.execute(
            "INSERT INTO signal_tracking VALUES (?,?,?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
            (signal_id, symbol, signal, signal_tr, confidence, entry_price,
             target_price, stop_loss, timeframe, datetime.utcnow().isoformat(),
             check_date)
        )
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

        # Kar/Zarar hesapla
        profit_loss_pct = ((actual_price - entry_price) / entry_price * 100) if entry_price > 0 else 0

        # Başarılı mı?
        is_successful = 0
        result = ""

        if signal in ["BUY", "AL", "STRONG_BUY", "GÜÇLÜ AL"]:
            # AL sinyali - fiyat yükseldi mi?
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
            if abs(profit_loss_pct) < 5:
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


def get_signal_success_rate(days: int = 30, symbol: str = None) -> Dict:
    """Sinyal başarı oranı istatistikleri"""
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

        success_rate = (successful / total * 100) if total > 0 else 0

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

        return {
            "total_signals": total,
            "successful_signals": successful,
            "success_rate": round(success_rate, 2),
            "days": days,
            "symbol": symbol,
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
