import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="rounded-[2rem] border border-white/80 bg-white/95 p-10 text-center shadow-panel">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">404</p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-950">Sahifa topilmadi</h1>
        <p className="mt-2 text-sm text-slate-500">Kerakli bo'lim manzili o'zgargan yoki mavjud emas.</p>
        <Link to="/" className="mt-6 inline-flex rounded-2xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
          Dashboardga qaytish
        </Link>
      </div>
    </div>
  );
}
