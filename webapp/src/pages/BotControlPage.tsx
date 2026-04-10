import { useEffect, useState } from "react";
import { ErrorState } from "components/ErrorState";
import { LoadingState } from "components/LoadingState";
import { Panel } from "components/Panel";
import { api } from "lib/api";

interface BotStatusResponse {
  bot: Record<string, unknown>;
  webhook: Record<string, unknown>;
  groups: Array<Record<string, unknown>>;
  settings: Record<string, unknown>;
}

export function BotControlPage() {
  const [data, setData] = useState<BotStatusResponse | null>(null);
  const [simulationText, setSimulationText] = useState("Assalomu alaykum, buyurtma qachon yetadi?");
  const [simulationResult, setSimulationResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      setData(await api.get<BotStatusResponse>("/api/admin/settings/bot-status"));
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

  if (loading) return <LoadingState label="Bot control yuklanmoqda..." />;
  if (error || !data) return <ErrorState message={error || "Bot status qaytmadi"} />;

  const settings = data.settings;

  return (
    <div className="space-y-6">
      <Panel title="Bot status" subtitle="Webhook, bot profilingi va kuzatilayotgan guruhlar">
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Bot username</p>
            <p className="mt-2 font-semibold text-slate-900">@{String(data.bot.username || "-")}</p>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Webhook URL</p>
            <p className="mt-2 break-all text-sm text-slate-700">{String(data.webhook.url || "-")}</p>
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Kuzatilayotgan guruhlar</p>
            <p className="mt-2 font-semibold text-slate-900">{data.groups.length}</p>
          </div>
        </div>
      </Panel>
      <Panel title="Asosiy toggles" subtitle="Auto-reply va management digest boshqaruvi">
        <div className="grid gap-4 md:grid-cols-3">
          {[
            ["auto_reply_enabled", "Auto-reply yoqilgan"],
            ["management_hourly_digest_enabled", "Soatlik digest"],
            ["management_daily_summary_enabled", "Kunlik summary"]
          ].map(([key, label]) => (
            <button
              key={key}
              onClick={async () => {
                const nextValue = !Boolean(settings[key]);
                await api.patch("/api/admin/settings", { values: { [key]: nextValue } });
                await load();
              }}
              className={`rounded-2xl border p-4 text-left ${settings[key] ? "border-emerald-200 bg-emerald-50" : "border-slate-200 bg-white"}`}
            >
              <p className="text-sm font-semibold text-slate-900">{label}</p>
              <p className="mt-2 text-sm text-slate-500">{settings[key] ? "Faol" : "Nofaol"}</p>
            </button>
          ))}
        </div>
      </Panel>
      <div className="grid gap-6 xl:grid-cols-2">
        <Panel title="Test send summary" subtitle="Management groupga bir martalik test hisobot yuborish">
          <button
            onClick={async () => {
              await api.post("/api/admin/settings/test-summary");
              await load();
            }}
            className="rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white"
          >
            Test summary yuborish
          </button>
        </Panel>
        <Panel title="Test auto-reply simulation" subtitle="KB matching natijasini oldindan ko'rish">
          <textarea rows={4} value={simulationText} onChange={(event) => setSimulationText(event.target.value)} />
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              onClick={async () => setSimulationResult(await api.post("/api/admin/settings/test-auto-reply", { text: simulationText }))}
              className="rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-white"
            >
              Simulyatsiya qilish
            </button>
          </div>
          {simulationResult ? (
            <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
              <pre className="overflow-auto whitespace-pre-wrap">{JSON.stringify(simulationResult, null, 2)}</pre>
            </div>
          ) : null}
        </Panel>
      </div>
    </div>
  );
}
