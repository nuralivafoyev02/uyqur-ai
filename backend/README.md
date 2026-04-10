# Backend

`backend/` Cloudflare Workers uchun webhook-first Python xizmatini saqlaydi. U Telegram update'larni qabul qiladi, Supabase orqali ticketlarni yuritadi, boshqaruv guruhiga hisobot yuboradi va admin panel uchun xavfsiz API beradi.

## Asosiy komponentlar

- `bot.py`: Telegram group domen logikasining markazi.
- `app/main.py`: FastAPI ilovasi va route registratsiyasi.
- `app/entry.py`: Cloudflare Worker entrypoint.
- `app/services/`: bot, stats, auth, knowledge va scheduler servislar.
- `app/repositories/`: Supabase PostgREST/RPC client qatlamlari.
- `migrations/`: Supabase schema va RPC funksiyalari.
- `tests/`: domen va auth oqimlari uchun real testlar.

## Lokal ishga tushirish

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.asgi:app --reload --port 8788
```

## Cloudflare Workers dev

```bash
cd backend
uvx --from workers-py pywrangler dev --test-scheduled
```

## Test

```bash
cd backend
pytest
```


## Login / cookie eslatma

Agar webapp va backend alohida deploy qilinsa, backend vars ichida quyidagilar to'g'ri bo'lishi kerak:
- `ADMIN_WEBAPP_URL` = frontend public URL
- `CORS_ORIGINS` = frontend public URL
- `SESSION_COOKIE_SAMESITE=none`
- `SESSION_SECURE_COOKIES=true`
