import { FormEvent, useEffect, useState } from "react";
import { ErrorState } from "components/ErrorState";
import { LoadingState } from "components/LoadingState";
import { Panel } from "components/Panel";
import { api, ApiError } from "lib/api";

export function SettingsPage() {
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [passwordState, setPasswordState] = useState({ current_password: "", new_password: "", confirm: "" });

  const load = async () => {
    setLoading(true);
    try {
      const response = await api.get<{ values: Record<string, unknown> }>("/api/admin/settings");
      setValues(response.values);
      setError("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const saveSettings = async (event: FormEvent) => {
    event.preventDefault();
    await api.patch("/api/admin/settings", { values });
    await load();
  };

  const changePassword = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    if (passwordState.new_password !== passwordState.confirm) {
      setError("Yangi parollar bir xil emas.");
      return;
    }
    try {
      await api.post("/api/admin/auth/change-password", {
        current_password: passwordState.current_password,
        new_password: passwordState.new_password
      });
      setPasswordState({ current_password: "", new_password: "", confirm: "" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Parol yangilanmadi");
    }
  };

  if (loading) return <LoadingState label="Sozlamalar yuklanmoqda..." />;
  if (error && !Object.keys(values).length) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      <Panel title="System settings" subtitle="Response window, fallback message va timezone boshqaruvi">
        <form onSubmit={saveSettings} className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Merge window (minutes)</label>
            <input value={String(values.response_merge_window_minutes ?? "")} onChange={(event) => setValues((prev) => ({ ...prev, response_merge_window_minutes: Number(event.target.value) }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Reopen window (minutes)</label>
            <input value={String(values.reopen_window_minutes ?? "")} onChange={(event) => setValues((prev) => ({ ...prev, reopen_window_minutes: Number(event.target.value) }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Auto-reply delay (minutes)</label>
            <input value={String(values.auto_reply_delay_minutes ?? "")} onChange={(event) => setValues((prev) => ({ ...prev, auto_reply_delay_minutes: Number(event.target.value) }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Confidence threshold</label>
            <input value={String(values.auto_reply_confidence_threshold ?? "")} onChange={(event) => setValues((prev) => ({ ...prev, auto_reply_confidence_threshold: Number(event.target.value) }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Timezone</label>
            <input value={String(values.timezone ?? "")} onChange={(event) => setValues((prev) => ({ ...prev, timezone: event.target.value }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Management group chat_id</label>
            <input value={String(values.management_group_chat_id ?? "")} onChange={(event) => setValues((prev) => ({ ...prev, management_group_chat_id: Number(event.target.value) }))} />
          </div>
          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Fallback message</label>
            <textarea rows={4} value={String(values.safe_fallback_message ?? "")} onChange={(event) => setValues((prev) => ({ ...prev, safe_fallback_message: event.target.value }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Hourly digest cron</label>
            <input value={String(values.hourly_digest_cron ?? "")} onChange={(event) => setValues((prev) => ({ ...prev, hourly_digest_cron: event.target.value }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Daily summary cron</label>
            <input value={String(values.daily_summary_cron ?? "")} onChange={(event) => setValues((prev) => ({ ...prev, daily_summary_cron: event.target.value }))} />
          </div>
          <div className="md:col-span-2 flex justify-end">
            <button className="rounded-2xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white">Saqlash</button>
          </div>
        </form>
      </Panel>
      <Panel title="Admin password" subtitle="Sessiya cookie saqlanadi, parol faqat backendda hash bo'ladi">
        <form onSubmit={changePassword} className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Joriy parol</label>
            <input type="password" value={passwordState.current_password} onChange={(event) => setPasswordState((prev) => ({ ...prev, current_password: event.target.value }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Yangi parol</label>
            <input type="password" value={passwordState.new_password} onChange={(event) => setPasswordState((prev) => ({ ...prev, new_password: event.target.value }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Tasdiqlash</label>
            <input type="password" value={passwordState.confirm} onChange={(event) => setPasswordState((prev) => ({ ...prev, confirm: event.target.value }))} />
          </div>
          <div className="md:col-span-3 flex justify-end">
            <button className="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700">
              Parolni yangilash
            </button>
          </div>
        </form>
        {error ? <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div> : null}
      </Panel>
    </div>
  );
}
