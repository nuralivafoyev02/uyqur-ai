import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { EmptyState } from "components/EmptyState";
import { ErrorState } from "components/ErrorState";
import { LoadingState } from "components/LoadingState";
import { Panel } from "components/Panel";
import { StatusBadge } from "components/StatusBadge";
import { TicketDrawer } from "components/TicketDrawer";
import { api } from "lib/api";
import { formatDate, formatDuration } from "lib/format";
import type { GroupItem, TicketItem, TicketStatus } from "types/api";

const statuses: Array<{ label: string; value: TicketStatus | "all" }> = [
  { label: "Barchasi", value: "all" },
  { label: "Ochiq", value: "open" },
  { label: "Yopilgan", value: "closed" },
  { label: "Avto-javob", value: "auto_replied" },
  { label: "Qayta ochilgan", value: "reopened" }
];

export function GroupDetailPage() {
  const { groupId } = useParams();
  const [group, setGroup] = useState<GroupItem | null>(null);
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<TicketItem | null>(null);
  const [status, setStatus] = useState<TicketStatus | "all">("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    if (!groupId) return;
    setLoading(true);
    try {
      const [groupResponse, ticketsResponse] = await Promise.all([
        api.get<GroupItem>(`/api/admin/groups/${groupId}`),
        api.get<TicketItem[]>(`/api/admin/tickets?group_id=${groupId}&include_closed=true`)
      ]);
      setGroup(groupResponse);
      setTickets(ticketsResponse);
      setError("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [groupId]);

  const filtered = useMemo(
    () =>
      tickets.filter((ticket) => {
        const statusMatch = status === "all" || ticket.status === status;
        const searchMatch =
          !search ||
          (ticket.customer_name || "").toLowerCase().includes(search.toLowerCase()) ||
          (ticket.latest_customer_message_text || "").toLowerCase().includes(search.toLowerCase());
        return statusMatch && searchMatch;
      }),
    [search, status, tickets]
  );

  const openTicket = async (ticketId: string) => {
    const detail = await api.get<TicketItem>(`/api/admin/tickets/${ticketId}`);
    setSelectedTicket(detail);
  };

  if (loading) return <LoadingState label="Guruh ma'lumotlari yuklanmoqda..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <>
      <div className="space-y-6">
        <Panel title="Guruh tafsiloti" subtitle={group?.title || "Guruh topilmadi"}>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Chat ID</p>
              <p className="mt-2 font-semibold text-slate-900">{group?.chat_id}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Turi</p>
              <p className="mt-2 font-semibold capitalize text-slate-900">{group?.group_type}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Holati</p>
              <p className="mt-2 font-semibold text-slate-900">{group?.is_active ? "Faol" : "Nofaol"}</p>
            </div>
          </div>
        </Panel>
        <Panel title="Ticketlar" subtitle="Status, qidiruv va detal oynasi bilan">
          <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Mijoz yoki matn bo'yicha qidirish" className="lg:max-w-sm" />
            <div className="flex flex-wrap gap-2">
              {statuses.map((item) => (
                <button
                  key={item.value}
                  onClick={() => setStatus(item.value)}
                  className={`rounded-full px-3 py-1.5 text-sm ${status === item.value ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-600"}`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          {filtered.length === 0 ? (
            <EmptyState title="Ticket topilmadi" description="Tanlangan filtrga mos ticket yo'q." />
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-[0.16em] text-slate-500">
                  <tr>
                    <th className="pb-3">Mijoz</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3">So'nggi xabar</th>
                    <th className="pb-3">Ilk javob</th>
                    <th className="pb-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((ticket) => (
                    <tr key={ticket.id}>
                      <td className="py-3">
                        <p className="font-medium text-slate-900">{ticket.customer_name || "Mijoz"}</p>
                        <p className="text-xs text-slate-500">{ticket.customer_username || "username yo'q"}</p>
                      </td>
                      <td className="py-3"><StatusBadge status={ticket.status} /></td>
                      <td className="py-3 text-slate-600">{formatDate(ticket.last_customer_message_at)}</td>
                      <td className="py-3 text-slate-600">{formatDuration(ticket.first_response_seconds)}</td>
                      <td className="py-3 text-right">
                        <button onClick={() => openTicket(ticket.id)} className="rounded-xl border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:border-slate-300">
                          Ochish
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>
      <TicketDrawer ticket={selectedTicket} onClose={() => setSelectedTicket(null)} />
    </>
  );
}
