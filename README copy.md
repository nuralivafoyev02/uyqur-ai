# Uyqur AI

Telegram support analytics bot va admin panel monoreposi.

## Arxitektura

- `backend/`: Python webhook-first backend. Telegram update parser, `backend/bot.py` ichidagi support-group domen logikasi, Supabase persistence, admin auth/session API, deterministic KB auto-reply engine, scheduled jobs va management digest.
- `webapp/`: React + TypeScript + Vite + Tailwind admin panel. HttpOnly cookie orqali login qiladi va groups, tickets, agents, bot control, settings, audit logs hamda knowledge base boshqaruvini beradi.
- `Supabase`: asosiy storage. Schema SQL migratsiyalar, RPC funksiyalar va row-level security bilan keladi.
- `Cloudflare`: backend uchun Python Workers entrypoint + cron triggers, frontend uchun Cloudflare Workers static assets SPA deploy.

## Monorepo Tuzilishi

```text
uyqur-ai/
  backend/
  webapp/
```

## Environment Variables

### Backend

- `APP_ENV`: `development` yoki `production`
- `APP_BASE_URL`: backend bazaviy URL
- `ADMIN_WEBAPP_URL`: admin panel public URL
- `APP_TIMEZONE`: default `Asia/Tashkent`
- `CORS_ORIGINS`: vergul bilan ajratilgan webapp originlari
- `TELEGRAM_BOT_TOKEN`: Telegram bot tokeni
- `TELEGRAM_BOT_USERNAME`: bot username
- `TELEGRAM_WEBHOOK_SECRET`: `X-Telegram-Bot-Api-Secret-Token` uchun secret
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: faqat backendda ishlatiladi
- `SUPABASE_REST_URL`: PostgREST endpoint
- `SUPABASE_RPC_URL`: RPC endpoint
- `SESSION_COOKIE_NAME`: admin cookie nomi
- `SESSION_COOKIE_DOMAIN`: custom domain kerak bo'lsa optional
- `SESSION_COOKIE_SAMESITE`: alohida deployda odatda `none`
- `SESSION_SECURE_COOKIES`: productionda `true`
- `SESSION_TTL_HOURS`: session davomiyligi
- `PASSWORD_HASH_ITERATIONS`: PBKDF2 iteratsiya soni
- `AUTO_REPLY_DELAY_MINUTES`: SLA auto-reply kechikishi
- `TICKET_MERGE_WINDOW_MINUTES`: bir ticketga xabarlarni biriktirish oynasi
- `TICKET_REOPEN_WINDOW_MINUTES`: qayta ochish oynasi
- `AUTO_REPLY_CONFIDENCE_THRESHOLD`: default confidence threshold
- `SAFE_FALLBACK_MESSAGE`: past confidence fallback javob
- `MANAGEMENT_GROUP_CHAT_ID`: management group chat_id
- `BOOTSTRAP_ADMIN_USERNAME`: default `admin`
- `BOOTSTRAP_ADMIN_PASSWORD`: default `admin123`

### Webapp

- `VITE_API_BASE_URL`: frontenddan backend API bazaviy URL

## Local Development

### 1. Supabase tayyorlash

1. Yangi Supabase project yarating.
2. `backend/migrations/001_initial_schema.sql`, `002_reporting_and_rpc.sql`, `003_seed_settings.sql` ni ketma-ket ishga tushiring.
3. Service role key va project URL ni env faylga joylang.
4. `backend/scripts/bootstrap_admin.py` orqali default adminni yaratib oling.

### 2. Backend

```bash
cd backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python scripts/bootstrap_admin.py
uvicorn app.asgi:app --reload --port 8788
```

### 3. Webapp

```bash
cd webapp
cp .env.example .env
npm install
npm run dev
```

## Deployment Steps

### Backend to Cloudflare Workers

1. `backend/.env.example` asosida Cloudflare secrets va vars ni tayyorlang.
2. `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `SUPABASE_SERVICE_ROLE_KEY` ni secret sifatida saqlang.
3. `backend/wrangler.toml` dagi cron triggerlar:
   - `* * * * *`: har daqiqalik SLA scan
   - `0 * * * *`: soatlik digest
   - `0 19 * * *`: Tashkent bo'yicha kun yakuni summary
4. Deploy:

```bash
cd backend
uvx --from workers-py pywrangler deploy
```

### Webapp to Cloudflare

```bash
cd webapp
npm install
npm run build
npx wrangler deploy
```

## Telegram Bot Setup

1. BotFather orqali bot yarating va token oling.
2. Botni support guruhlari va management guruhga qo'shing.
3. Botga group message va reply ko'rish uchun kerakli admin huquqlarini bering.
4. Webhook o'rnating:

```bash
curl -X POST "https://api.telegram.org/bot<token>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://<backend-domain>/telegram/webhook","secret_token":"<TELEGRAM_WEBHOOK_SECRET>","allowed_updates":["message","edited_message"]}'
```

5. Management group chat_id va kerakli agent username/chat_id larni admin panel orqali kiriting.
6. Agentlar private chatda `/registerme` yuborib o'z chat_id sini biriktirishi mumkin.

## Supabase Setup Notes

- Frontendga service role key bermang.
- Barcha admin endpointlar server-side cookie sessiya bilan ishlaydi.
- RLS barcha asosiy jadvallarda yoqilgan; backend service role bu siyosatlardan bypass qiladi.
- Analytics va scheduler uchun `stats_*`, `stale_open_tickets`, `claim_processed_update`, `claim_management_report` RPC funksiyalari yaratiladi.

## Default Admin Bootstrap

- Bootstrap login: `admin / admin123`
- Bu akkaunt yaratishda `must_change_password = true` holatda saqlanadi.
- Birinchi kirishda webapp darhol parol almashtirish ekraniga olib boradi.
- Parol server tomonda PBKDF2-HMAC-SHA256 bilan hash qilinadi.
- Sessionlar `HttpOnly` cookie orqali boshqariladi, localStorage ishlatilmaydi.

## Command Reference

### Backend

- `cd backend && python scripts/bootstrap_admin.py`
- `cd backend && uvicorn app.asgi:app --reload --port 8788`
- `cd backend && pytest`
- `cd backend && uvx --from workers-py pywrangler dev --test-scheduled`

### Webapp

- `cd webapp && npm run dev`
- `cd webapp && npm run build`
- `cd webapp && npm run preview`
- `cd webapp && npm run deploy`

### Telegram Commands

- `/help`
- `/stats`
- `/stats_today`
- `/stats_week`
- `/groupstats`
- `/agentstats`
- `/open`
- `/registerme`

## Test Instructions

1. Backend dependencylarni o'rnating.
2. `cd backend && pytest`
3. Zarur minimal qamrov:
   - ticket creation va merge
   - agent reply close
   - non-agent reply close qilmasligi
   - 5 daqiqalik auto-reply
   - fallback confidence logic
   - command auth protection
   - admin login / first password change
   - duplicate update idempotency

## Operational Notes

- Auto-reply engine external AI ishlatmaydi; u keyword, synonym, pattern va similarity score kombinatsiyasiga tayangan deterministic qoidalar bilan ishlaydi.
- Auto-replied ticketlar `auto_replied` statusiga o'tadi, lekin ular hali operator kuzatuvida qoladi.
- Agent reply faqat customer message’ga reply bo‘lsa ticketni yopadi.
- Support group’larda non-agent mijoz xabarlari ticket sifatida olinadi; management group xabarlari statistik request hisoblanmaydi.
- Cloudflare cron UTC bo‘yicha ishlaydi, shu sabab `0 19 * * *` Tashkent yarim tuniga moslangan.


## Alohida deploy yo'riqnomalari

- Backend: `docs/deploy-backend-cloudflare.md`
- Webapp: `docs/deploy-webapp-cloudflare.md`
