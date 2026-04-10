import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "lib/api";
import { useAuth } from "hooks/useAuth";

export function ForcePasswordChangePage() {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("Yangi parollar bir xil emas.");
      return;
    }
    if (newPassword.length < 12) {
      setError("Yangi parol kamida 12 belgidan iborat bo'lishi kerak.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/api/admin/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword
      });
      await refresh();
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Parol o'zgartirilmadi");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-xl rounded-[2rem] border border-white/80 bg-white/95 p-8 shadow-panel">
        <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Majburiy bosqich</p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-950">Bootstrap parolni almashtiring</h1>
        <p className="mt-2 text-sm text-slate-500">Boshlang‘ich parol faqat ilk kirish uchun. Ishga tushirishdan oldin kamida 12 belgili kuchli parol o‘rnating.</p>
        <form onSubmit={submit} className="mt-8 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Joriy parol</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              autoComplete="current-password"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Yangi parol</label>
            <input
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              minLength={12}
              autoComplete="new-password"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Yangi parolni tasdiqlang</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              minLength={12}
              autoComplete="new-password"
            />
          </div>
          {error ? <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div> : null}
          <button className="w-full rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-white hover:bg-teal-700" disabled={loading}>
            {loading ? "Saqlanmoqda..." : "Parolni yangilash"}
          </button>
        </form>
      </div>
    </div>
  );
}
