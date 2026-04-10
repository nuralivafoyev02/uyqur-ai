# Tuzatilgan joylar

## 1. Login / sessiya
- Backend cookie sozlamasi `SameSite=Lax` dan konfiguratsiyaga o'tkazildi.
- Production uchun default `SESSION_COOKIE_SAMESITE=none` bo'ldi.
- `ADMIN_WEBAPP_URL` va `CORS_ORIGINS` fallbacklari qo'shildi.
- Optional `SESSION_COOKIE_DOMAIN` qo'shildi.
- `logout` cookie delete jarayoni domain bilan moslashtirildi.

## 2. Frontend auth barqarorligi
- API layerga network/CORS xatolari uchun aniqroq xabar qo'shildi.
- `useAuth.refresh()` endi backendga ulanmasa ham appni yiqitmaydi.

## 3. Deploy / konfiguratsiya
- Backend va webapp `wrangler.toml` fayllariga alohida deploy uchun placeholder URL lar qo'shildi.
- Cloudflare uchun alohida backend va webapp deploy yo'riqnomalari yozildi.

## 4. Repo sanitizatsiyasi
- `.gitignore` kuchaytirildi.
- Packaging vaqtida `.env`, `.cloudflare-secrets.env`, `node_modules`, `.venv`, cache va boshqa build artefaktlar chiqarib tashlandi.
