import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "lib/api";
import { useAuth } from "hooks/useAuth";

export function LoginPage() {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/api/admin/auth/login", { username, password });
      await refresh();
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login bajarilmadi");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-[2rem] border border-white/80 bg-white/90 shadow-panel backdrop-blur lg:grid-cols-[1.05fr_0.95fr]">
        <div className="hidden bg-slate-950 p-10 text-white lg:block">
          <p className="text-xs uppercase tracking-[0.22em] text-emerald-200/80">Uyqur AI Admin</p>
          <h1 className="mt-4 text-4xl font-semibold leading-tight">Telegram support operatsiyalarini bitta paneldan boshqaring.</h1>
          <div className="mt-8 grid gap-4">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <p className="text-sm text-slate-300">Open / unanswered / auto-replied / closed holatlari bir joyda ko‘rinadi.</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <p className="text-sm text-slate-300">Agent productivity, guruh statistikasi va deterministic KB auto-reply training moduli mavjud.</p>
            </div>
          </div>
        </div>
        <div className="p-8 sm:p-12">
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Kirish</p>
          <h2 className="mt-3 text-3xl font-semibold text-slate-950">Admin panel</h2>
          <p className="mt-2 text-sm text-slate-500">Bootstrap akkaunt birinchi kirishda parolni almashtirishga majbur qilinadi.</p>
          <form onSubmit={submit} className="mt-10 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Username</label>
              <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Password</label>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                placeholder="Parolni kiriting"
              />
            </div>
            {error ? <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div> : null}
            <button
              disabled={loading}
              className="w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? "Kirilmoqda..." : "Tizimga kirish"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
