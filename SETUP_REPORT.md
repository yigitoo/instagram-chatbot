# Instagram DM Chatbot — Setup Report

## Proje Özeti
Instagram DM'lerine Google Gemini API ile otomatik yanıt veren bir chatbot pipeline'ı. Admin manuel yanıt verdiğinde bot otomatik olarak duraklar.

## Stack
- **Python + FastAPI** — Async webhook endpoint
- **Instagram Graph API (v21.0)** — DM alma/gönderme
- **Google Gemini API** (`google-genai` SDK, model: `gemini-2.5-flash`) — AI yanıt üretme
- **In-memory pause tracking** — Konuşma bazlı duraklama

## Dosya Yapısı
```
app/
├── __init__.py
├── main.py              # FastAPI app, webhook GET/POST, health check
├── config.py            # Pydantic Settings (.env okuma)
├── instagram.py         # Instagram Graph API client (mesaj gönderme)
├── gemini.py            # Gemini API wrapper (yanıt üretme)
├── pause_manager.py     # Konuşma bazlı pause state
└── webhook_handler.py   # Ana orkestrasyon: parse → filter → generate → send
```

## Ortam Değişkenleri (.env)
| Değişken | Açıklama |
|---|---|
| `META_VERIFY_TOKEN` | Webhook doğrulama token'ı (kendin belirle) |
| `META_PAGE_ACCESS_TOKEN` | Meta App Dashboard'dan alınan Page Access Token |
| `INSTAGRAM_ACCOUNT_ID` | Instagram Business hesap ID'si |
| `GEMINI_API_KEY` | Google AI Studio'dan alınan API key |
| `GEMINI_MODEL` | Kullanılacak model (default: `gemini-2.5-flash`) |
| `ADMIN_PAUSE_DURATION_MINUTES` | Admin yanıtından sonra bot duraklama süresi (default: 30) |

## Endpoint'ler
| Method | Path | Açıklama |
|---|---|---|
| GET | `/webhook` | Meta webhook verification (hub.mode, hub.verify_token, hub.challenge) |
| POST | `/webhook` | Gelen DM event'lerini alır, background task olarak işler |
| GET | `/health` | Health check |

## Admin Auto-Pause Mantığı
1. Meta, sayfadan gönderilen TÜM mesajlar için `is_echo: true` gönderir
2. Bot mesajları → `is_echo: true` + `app_id` var → görmezden gel
3. Admin mesajları → `is_echo: true` + `app_id` YOK → o konuşmayı duraklat
4. Duraklama süresi dolunca bot otomatik aktif olur

## VPS Deployment Adımları

### 1. VPS'e Kodu Kopyala
```bash
git clone <repo-url> /opt/instagram-chatbot
cd /opt/instagram-chatbot
pip install -r requirements.txt
cp .env.example .env
# .env dosyasını gerçek değerlerle doldur
```

### 2. Uvicorn'u Systemd Service Olarak Kur
```bash
sudo tee /etc/systemd/system/instagram-bot.service << 'EOF'
[Unit]
Description=Instagram DM Chatbot
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/instagram-chatbot
ExecStart=/usr/local/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=/opt/instagram-chatbot/.env

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now instagram-bot
```

### 3. Nginx Reverse Proxy + SSL
```bash
sudo tee /etc/nginx/sites-available/instagram-bot << 'EOF'
server {
    listen 80;
    server_name bot.senindomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/instagram-bot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# SSL
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d bot.senindomain.com
```

### 4. Meta App Dashboard Ayarları
1. https://developers.facebook.com → App oluştur/seç
2. Instagram → Webhooks → Callback URL: `https://bot.senindomain.com/webhook`
3. Verify Token: `.env`'deki `META_VERIFY_TOKEN` değeri
4. Subscribe to: `messages` field
5. Instagram Basic/Messaging permissions'ları aktif et

### 5. Test
```bash
# Health check
curl https://bot.senindomain.com/health

# Logları izle
sudo journalctl -u instagram-bot -f
```

## Hosting Alternatifleri (Tartışılan)
| Seçenek | Durum |
|---|---|
| ngrok | Geliştirme/test için uygun, production'da kullanılmaz |
| Cloudflare Tunnel | Ücretsiz, 20-30 kişi/ay için fazlasıyla yeterli, port açmaya gerek yok |
| **Nginx + Certbot** | **Seçilen çözüm** — VPS + domain zaten var, en basit ve bağımsız |

## Sonraki Adımlar
- [ ] VPS'e deploy et
- [ ] Meta App Dashboard'da webhook ayarla
- [ ] `.env` değerlerini gerçek credentials ile doldur
- [ ] Test DM gönder, bot yanıtını doğrula
- [ ] Admin pause'u test et
