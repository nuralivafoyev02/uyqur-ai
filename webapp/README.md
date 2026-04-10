# Webapp

`webapp/` admin panelni saqlaydi. UI React + TypeScript + Vite + Tailwind asosida qurilgan va backend bilan HttpOnly cookie sessiyasi orqali ishlaydi.

## Lokal ishga tushirish

```bash
cd webapp
npm install
npm run dev
```

## Build

```bash
cd webapp
npm run build
```

## Cloudflare deploy

```bash
cd webapp
npm run build
npx wrangler deploy
```
