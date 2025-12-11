#!/bin/bash
# CryptoSignal Workers Setup Script
# Run this on your server to set up all background workers

echo "🚀 Setting up CryptoSignal Workers..."

# Create service files
cat > /etc/systemd/system/cryptosignal-prices.service << 'EOF'
[Unit]
Description=CryptoSignal Price Worker
After=redis-server.service

[Service]
Type=simple
WorkingDirectory=/opt/cryptosignal-app/backend
ExecStart=/opt/cryptosignal-app/backend/venv/bin/python worker_prices.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/cryptosignal-futures.service << 'EOF'
[Unit]
Description=CryptoSignal Futures Worker
After=redis-server.service

[Service]
Type=simple
WorkingDirectory=/opt/cryptosignal-app/backend
ExecStart=/opt/cryptosignal-app/backend/venv/bin/python worker_futures.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/cryptosignal-news.service << 'EOF'
[Unit]
Description=CryptoSignal News Worker
After=redis-server.service

[Service]
Type=simple
WorkingDirectory=/opt/cryptosignal-app/backend
ExecStart=/opt/cryptosignal-app/backend/venv/bin/python worker_news.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/cryptosignal-sentiment.service << 'EOF'
[Unit]
Description=CryptoSignal Sentiment Worker
After=redis-server.service

[Service]
Type=simple
WorkingDirectory=/opt/cryptosignal-app/backend
ExecStart=/opt/cryptosignal-app/backend/venv/bin/python worker_sentiment.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable all services
systemctl enable cryptosignal-prices
systemctl enable cryptosignal-futures
systemctl enable cryptosignal-news
systemctl enable cryptosignal-sentiment

# Start all services
systemctl start cryptosignal-prices
systemctl start cryptosignal-futures
systemctl start cryptosignal-news
systemctl start cryptosignal-sentiment

echo ""
echo "✅ Workers installed! Status:"
echo ""
systemctl status cryptosignal-prices --no-pager | head -5
systemctl status cryptosignal-futures --no-pager | head -5
systemctl status cryptosignal-news --no-pager | head -5
systemctl status cryptosignal-sentiment --no-pager | head -5

echo ""
echo "📋 Commands:"
echo "  journalctl -u cryptosignal-prices -f    # Price worker logs"
echo "  journalctl -u cryptosignal-futures -f   # Futures worker logs"
echo "  journalctl -u cryptosignal-news -f      # News worker logs"
echo "  systemctl restart cryptosignal-prices   # Restart a worker"
