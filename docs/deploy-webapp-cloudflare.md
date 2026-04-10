# Webapp Cloudflare Workers deploy

## 1) API URL
`webapp/wrangler.toml` ichida:
```toml
[vars]
VITE_API_BASE_URL = "https://your-backend-domain"
```

## 2) Local build
```bash
cd webapp
rm -rf node_modules dist
npm install
npm run build
```

## 3) Deploy
```bash
cd webapp
npx wrangler deploy
```

## 4) Login ishlamasa tekshiruv
- `VITE_API_BASE_URL` to'g'rimi
- backendda `CORS_ORIGINS` frontend URL bilan mosmi
- backendda `SESSION_COOKIE_SAMESITE=none` va `SESSION_SECURE_COOKIES=true` qo'yilganmi
- browser Network ichida `Set-Cookie` qaytdimi
- Application/Cookies ichida backend domain uchun cookie saqlandimi
