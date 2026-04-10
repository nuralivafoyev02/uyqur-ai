import { FormEvent, useEffect, useState } from "react";
import { EmptyState } from "components/EmptyState";
import { ErrorState } from "components/ErrorState";
import { LoadingState } from "components/LoadingState";
import { Modal } from "components/Modal";
import { Panel } from "components/Panel";
import { api } from "lib/api";
import { formatDuration } from "lib/format";
import type { AgentItem } from "types/api";

const emptyForm = {
  display_name: "",
  telegram_username: "",
  telegram_chat_id: "",
  role: "agent",
  is_active: true
};

export function AgentsPage() {
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);

  const load = async () => {
    setLoading(true);
    try {
      setAgents(await api.get<AgentItem[]>("/api/admin/agents"));
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

  const startCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setOpen(true);
  };

  const startEdit = (agent: AgentItem) => {
    setEditingId(agent.id);
    setForm({
      display_name: agent.display_name,
      telegram_username: agent.telegram_username || "",
      telegram_chat_id: agent.telegram_chat_id?.toString() || "",
      role: agent.role,
      is_active: agent.is_active
    });
    setOpen(true);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const payload = {
      display_name: form.display_name,
      telegram_username: form.telegram_username || null,
      telegram_chat_id: form.telegram_chat_id ? Number(form.telegram_chat_id) : null,
      role: form.role,
      is_active: form.is_active
    };
    if (editingId) {
      await api.patch(`/api/admin/agents/${editingId}`, payload);
    } else {
      await api.post("/api/admin/agents", payload);
    }
    setOpen(false);
    await load();
  };

  if (loading) return <LoadingState label="Agentlar yuklanmoqda..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <>
      <Panel
        title="Agentlar"
        subtitle="Username yoki chat_id bo'yicha biriktirish va productivity monitoring"
        action={
          <button onClick={startCreate} className="rounded-2xl bg-slate-950 px-4 py-2 text-sm font-medium text-white">
            Agent qo'shish
          </button>
        }
      >
        {agents.length === 0 ? (
          <EmptyState title="Agent topilmadi" description="Hali birorta agent biriktirilmagan." />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.16em] text-slate-500">
                <tr>
                  <th className="pb-3">Agent</th>
                  <th className="pb-3">Biriktirish</th>
                  <th className="pb-3">Handled</th>
                  <th className="pb-3">Avg javob</th>
                  <th className="pb-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {agents.map((agent) => (
                  <tr key={agent.id}>
                    <td className="py-3">
                      <p className="font-medium text-slate-900">{agent.display_name}</p>
                      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{agent.role}</p>
                    </td>
                    <td className="py-3 text-slate-600">
                      <div>@{agent.telegram_username || "yo'q"}</div>
                      <div>{agent.telegram_chat_id || "chat_id yo'q"}</div>
                    </td>
                    <td className="py-3 text-slate-600">{agent.handled_tickets ?? 0}</td>
                    <td className="py-3 text-slate-600">{formatDuration(agent.avg_first_response_seconds)}</td>
                    <td className="py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => startEdit(agent)} className="rounded-xl border border-slate-200 px-3 py-1.5 text-sm text-slate-600">
                          Tahrirlash
                        </button>
                        <button
                          onClick={async () => {
                            await api.delete(`/api/admin/agents/${agent.id}`);
                            await load();
                          }}
                          className="rounded-xl border border-rose-200 px-3 py-1.5 text-sm text-rose-700"
                        >
                          O'chirish
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
      <Modal open={open} onClose={() => setOpen(false)} title={editingId ? "Agentni tahrirlash" : "Yangi agent"}>
        <form onSubmit={submit} className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Display name</label>
            <input value={form.display_name} onChange={(event) => setForm((prev) => ({ ...prev, display_name: event.target.value }))} required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Telegram username</label>
            <input value={form.telegram_username} onChange={(event) => setForm((prev) => ({ ...prev, telegram_username: event.target.value }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Telegram chat_id</label>
            <input value={form.telegram_chat_id} onChange={(event) => setForm((prev) => ({ ...prev, telegram_chat_id: event.target.value }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Role</label>
            <select value={form.role} onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value }))}>
              <option value="agent">agent</option>
              <option value="manager">manager</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <div className="flex items-center gap-3 pt-8">
            <input id="agent-active" type="checkbox" checked={form.is_active} onChange={(event) => setForm((prev) => ({ ...prev, is_active: event.target.checked }))} />
            <label htmlFor="agent-active" className="text-sm font-medium text-slate-700">Faol agent</label>
          </div>
          <div className="md:col-span-2 flex justify-end">
            <button className="rounded-2xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
              Saqlash
            </button>
          </div>
        </form>
      </Modal>
    </>
  );
}
