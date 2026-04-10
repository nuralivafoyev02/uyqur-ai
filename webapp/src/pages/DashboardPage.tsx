import { useEffect, useState } from "react";
import { EmptyState } from "components/EmptyState";
import { ErrorState } from "components/ErrorState";
import { LoadingState } from "components/LoadingState";
import { Panel } from "components/Panel";
import { StatCard } from "components/StatCard";
import { StatusBadge } from "components/StatusBadge";
import { api } from "lib/api";
import { formatDate, formatDuration } from "lib/format";
import type { OverviewStats } from "types/api";

export function DashboardPage() {
  const [data, setData] = useState<OverviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<OverviewStats>("/api/admin/stats/overview?window=today")
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState label="Dashboard yuklanmoqda..." />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <EmptyState title="Ma'lumot topilmadi" description="Dashboard uchun statistika qaytmadi." />;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Bugungi murojaatlar" value={data.total_requests} helper="Trak qilinayotgan support guruhlar bo'yicha" />
        <StatCard title="Ochiq ticketlar" value={data.open_requests} helper="Agent javobi kutilayotganlar" />
        <StatCard title="Javob berish foizi" value={`${data.response_rate}%`} helper="Inson yoki bot tomonidan ilk javob" />
        <StatCard title="O'rtacha ilk javob" value={formatDuration(data.average_first_response_seconds)} helper="Bugungi kesim" />
      </section>
      <section className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
        <Panel title="Guruhlar bo'yicha tez ko'rinish" subtitle="Bugungi asosiy support oqimi">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.16em] text-slate-500">
                <tr>
                  <th className="pb-3">Guruh</th>
                  <th className="pb-3">Jami</th>
                  <th className="pb-3">Ochiq</th>
                  <th className="pb-3">Yopilgan</th>
                  <th className="pb-3">Foiz</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.groups.map((group) => (
                  <tr key={group.id}>
                    <td className="py-3 font-medium text-slate-900">{group.title}</td>
                    <td className="py-3 text-slate-600">{group.total_requests}</td>
                    <td className="py-3 text-slate-600">{group.open_requests}</td>
                    <td className="py-3 text-slate-600">{group.closed_requests}</td>
                    <td className="py-3 text-slate-600">{group.response_rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
        <Panel title="Agent performance" subtitle="Bugungi handled ticketlar">
          <div className="space-y-3">
            {data.agents.length === 0 ? (
              <EmptyState title="Agent statistikasi yo'q" description="Hozircha yopilgan ticketlar topilmadi." />
            ) : (
              data.agents.map((agent) => (
                <div key={agent.id} className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <h3 className="font-medium text-slate-900">{agent.display_name}</h3>
                      <p className="text-sm text-slate-500">{agent.handled_tickets} ta handled ticket</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-slate-900">{formatDuration(agent.avg_first_response_seconds)}</p>
                      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Avg first response</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Panel>
      </section>
      <Panel title="Yaqinda hal qilinmagan ticketlar" subtitle="Tezkor operator e'tiborini talab qiladiganlar">
        {data.recent_unresolved.length === 0 ? (
          <EmptyState title="Hal qilinmagan ticket yo'q" description="Hozircha barcha ticketlar nazorat ostida." />
        ) : (
          <div className="grid gap-3">
            {data.recent_unresolved.map((ticket) => (
              <div key={ticket.id} className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="font-medium text-slate-900">{ticket.customer_name}</p>
                  <p className="text-sm text-slate-500">{ticket.group_title}</p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={ticket.status} />
                  <span className="text-sm text-slate-500">{formatDate(ticket.last_customer_message_at)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
