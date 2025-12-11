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
from datetime import datetime
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
                last_login TEXT
            )
        ''')
        
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
