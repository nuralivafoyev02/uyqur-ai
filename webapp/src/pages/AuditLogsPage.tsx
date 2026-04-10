import { useEffect, useState } from "react";
import { EmptyState } from "components/EmptyState";
import { ErrorState } from "components/ErrorState";
import { LoadingState } from "components/LoadingState";
import { Panel } from "components/Panel";
import { api } from "lib/api";
import { formatDate } from "lib/format";
import type { AuditLogItem } from "types/api";

export function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [action, setAction] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const query = action ? `?action=${encodeURIComponent(action)}` : "";
      setLogs(await api.get<AuditLogItem[]>(`/api/admin/audit-logs${query}`));
      setError("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [action]);

  if (loading) return <LoadingState label="Audit loglar yuklanmoqda..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <Panel title="Audit Logs" subtitle="Kritik admin amallari, login va sozlama o'zgarishlari">
      <div className="mb-4 max-w-sm">
        <input value={action} onChange={(event) => setAction(event.target.value)} placeholder="Action bo'yicha filter" />
      </div>
      {logs.length === 0 ? (
        <EmptyState title="Audit log yo'q" description="Tanlangan filtr bo'yicha audit yozuvi topilmadi." />
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-[0.16em] text-slate-500">
              <tr>
                <th className="pb-3">Vaqt</th>
                <th className="pb-3">Action</th>
                <th className="pb-3">Actor</th>
                <th className="pb-3">Entity</th>
                <th className="pb-3">Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((log, index) => (
                <tr key={`${log.action}-${index}`}>
                  <td className="py-3 text-slate-600">{formatDate(log.created_at)}</td>
                  <td className="py-3 font-medium text-slate-900">{log.action}</td>
                  <td className="py-3 text-slate-600">{log.actor_type} {log.actor_id || ""}</td>
                  <td className="py-3 text-slate-600">{log.entity_type || "-"} {log.entity_id || ""}</td>
                  <td className="py-3 text-slate-600">
                    <pre className="max-w-xl overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(log.metadata, null, 2)}</pre>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
