-- Payment Notifications Table
-- Created: 2025-12-11

CREATE TABLE IF NOT EXISTS payment_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tier TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TEXT NOT NULL,
    processed_at TEXT,
    processed_by TEXT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_payment_user ON payment_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_status ON payment_notifications(status);
CREATE INDEX IF NOT EXISTS idx_payment_created ON payment_notifications(created_at);
