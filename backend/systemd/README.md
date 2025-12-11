# CryptoSignal Systemd Services

Bu dizinde tüm CryptoSignal servislerinin systemd service dosyaları bulunur.

## Servisler

### 🌐 Application Services

1. **cryptosignal-backend.service**
   - FastAPI backend server
   - Port: 8000
   - Worker: `main.py`

2. **cryptosignal-frontend.service**
   - Nginx frontend server
   - Port: 3000
   - Config: `nginx.conf`

### ⚙️ Worker Services

3. **cryptosignal-prices.service**
   - Kripto fiyatlarını günceller
   - Kaynak: CoinGecko API
   - Güncelleme: Her 30 saniye
   - Worker: `worker_prices.py`

4. **cryptosignal-futures.service**
   - Futures/vadeli işlem fiyatları
   - Kaynak: Binance Futures API
   - Güncelleme: Her 60 saniye
   - Worker: `worker_futures.py`

5. **cryptosignal-news.service**
   - Crypto haberleri toplar
   - Kaynak: CryptoPanic API
   - Güncelleme: Her 5 dakika
   - Worker: `worker_news.py`

6. **cryptosignal-sentiment.service**
   - Sosyal medya sentiment analizi
   - Kaynak: Reddit, Twitter
   - Güncelleme: Her 15 dakika
   - Worker: `worker_sentiment.py`

7. **cryptosignal-ai-analyst.service**
   - AI analizleri ve signal tracking
   - Model: GPT-4o-mini
   - Sürekli çalışır, queue'dan okur
   - Worker: `worker_ai_analyst.py`

8. **cryptosignal-signal-checker.service**
   - Signal doğrulama ve başarı oranı
   - Kontrol: Saatlik
   - Worker: `worker_signal_checker.py`

9. **cryptosignal-telegram.service**
   - Telegram bot servisi
   - Bildirimler ve komutlar
   - Worker: `worker_telegram.py`

## Kurulum

### Tek Komutla (Önerilen)

```bash
cd /opt/cryptosignal-app/backend
sudo ./install_services.sh
```

### Manuel Kurulum

```bash
# Tüm service dosyalarını kopyala
sudo cp systemd/*.service /etc/systemd/system/

# İzinleri ayarla
sudo chmod 644 /etc/systemd/system/cryptosignal-*.service

# systemd'yi reload et
sudo systemctl daemon-reload

# Servisleri enable et
sudo systemctl enable cryptosignal-backend
sudo systemctl enable cryptosignal-frontend
sudo systemctl enable cryptosignal-prices
sudo systemctl enable cryptosignal-futures
sudo systemctl enable cryptosignal-news
sudo systemctl enable cryptosignal-sentiment
sudo systemctl enable cryptosignal-ai-analyst
sudo systemctl enable cryptosignal-signal-checker
sudo systemctl enable cryptosignal-telegram

# Başlat
sudo ./restart.sh
```

## Yönetim Komutları

### Status Kontrol

```bash
# Tüm servislerin durumu
sudo ./status.sh

# Tek bir servis
sudo systemctl status cryptosignal-backend
```

### Restart

```bash
# Tüm servisler
sudo ./restart.sh

# Tek bir servis
sudo systemctl restart cryptosignal-backend
```

### Log İzleme

```bash
# Tüm servislerin log'ları
sudo journalctl -f

# Tek bir servis
sudo journalctl -u cryptosignal-backend -f

# Son 50 satır
sudo journalctl -u cryptosignal-backend -n 50
```

### Start/Stop

```bash
# Başlat
sudo systemctl start cryptosignal-backend

# Durdur
sudo systemctl stop cryptosignal-backend

# Yeniden başlat
sudo systemctl restart cryptosignal-backend
```

## Service Dosyası Yapısı

Her service dosyası şu yapıda:

```ini
[Unit]
Description=Service Açıklaması
After=network.target redis-server.service
Requires=redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cryptosignal-app/backend
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 worker_xxx.py
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cryptosignal-xxx

[Install]
WantedBy=multi-user.target
```

## Dependency Graph

```
redis-server (Core)
    ↓
    ├── cryptosignal-backend (API)
    ├── cryptosignal-prices (Worker)
    ├── cryptosignal-futures (Worker)
    ├── cryptosignal-news (Worker)
    ├── cryptosignal-sentiment (Worker)
    ├── cryptosignal-ai-analyst (Worker)
    ├── cryptosignal-signal-checker (Worker)
    └── cryptosignal-telegram (Worker)

cryptosignal-frontend (Nginx)
    → Independent
```

## Troubleshooting

### Service Başlamıyorsa

```bash
# Status kontrol
sudo systemctl status cryptosignal-xxx

# Detaylı log
sudo journalctl -xe -u cryptosignal-xxx

# Manuel test
cd /opt/cryptosignal-app/backend
python3 worker_xxx.py
```

### Redis Bağlantı Hatası

```bash
# Redis çalışıyor mu?
sudo systemctl status redis-server

# Test
redis-cli -a "3f9af2788cb89aa74c06bd48dd290658" PING
```

### Permission Hatası

```bash
# Database izinleri
sudo chown root:root /opt/cryptosignal-app/backend/cryptosignal.db
sudo chmod 644 /opt/cryptosignal-app/backend/cryptosignal.db

# Service dosyası izinleri
sudo chmod 644 /etc/systemd/system/cryptosignal-*.service
```

## Auto-restart Politikası

Tüm servisler `Restart=always` ile yapılandırılmıştır:

- **RestartSec=10**: Crash sonrası 10 saniye bekle
- **Restart=always**: Her durumda yeniden başlat
- **Requires=redis-server**: Redis yoksa başlatma

## Logs

Tüm log'lar systemd journal'a gider:

```bash
# Tüm log'lar
sudo journalctl

# Belirli servis
sudo journalctl -u cryptosignal-backend

# Canlı izle
sudo journalctl -u cryptosignal-backend -f

# Son 1 saat
sudo journalctl -u cryptosignal-backend --since "1 hour ago"

# Bugün
sudo journalctl -u cryptosignal-backend --since today
```

## Güncelleme

Yeni değişiklikler geldiğinde:

```bash
# 1. Git pull
cd /opt/cryptosignal-app/backend
git pull origin main

# 2. Service dosyalarını güncelle (eğer değiştiyse)
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# 3. Restart
sudo ./restart.sh
```

---

**Daha fazla bilgi için:** [DEPLOYMENT_INSTRUCTIONS.md](../../DEPLOYMENT_INSTRUCTIONS.md)