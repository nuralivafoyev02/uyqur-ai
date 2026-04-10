# Backend Cloudflare Workers deploy

## 1) Talab qilinadigan narsalar
- Cloudflare account
- Wrangler CLI
- Supabase project
- Telegram bot token va webhook secret

## 2) Supabase migratsiyalar
SQL Editor ichida quyidagilarni ketma-ket ishga tushiring:
1. `backend/migrations/001_initial_schema.sql`
2. `backend/migrations/002_reporting_and_rpc.sql`
3. `backend/migrations/003_seed_settings.sql`

## 3) Backend env / vars
`backend/wrangler.toml` ichidagi placeholder qiymatlarni o'zingiznikiga almashtiring:
- `APP_BASE_URL` = backend public URL
- `ADMIN_WEBAPP_URL` = frontend public URL
- `CORS_ORIGINS` = frontend public URL
- `SESSION_COOKIE_SAMESITE` = alohida domain/subdomain bo'lsa `none`
- `SESSION_SECURE_COOKIES` = productionda `true`

## 4) Secretlarni saqlash
`backend/` ichida quyidagilarni secret sifatida saqlang:
```bash
wrangler secret put TELEGRAM_BOT_TOKEN
wrangler secret put TELEGRAM_WEBHOOK_SECRET
wrangler secret put SUPABASE_SERVICE_ROLE_KEY
```

## 5) Python deps
```bash
cd backend
pip install -e .[dev]
```

## 6) Deploy
```bash
cd backend
uvx --from workers-py pywrangler deploy
```

## 7) Webhook o'rnatish
```bash
curl -X POST "https://api.telegram.org/bot<token>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://<backend-domain>/telegram/webhook","secret_token":"<secret>","allowed_updates":["message","edited_message"]}'
```

## 8) Tekshiruv
- `GET /health` -> `status: ok` yoki `degraded`
- `POST /api/admin/auth/login` ishlashi kerak
- browserda login bo'lgandan keyin `uyqur_admin_session` cookie backend domain uchun yaralishi kerak
