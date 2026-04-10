import { formatDate } from "lib/format";
import { StatusBadge } from "./StatusBadge";
import type { TicketItem } from "types/api";

export function TicketDrawer({
  ticket,
  onClose
}: {
  ticket: TicketItem | null;
  onClose: () => void;
}) {
  if (!ticket) return null;
  return (
    <div className="fixed inset-y-0 right-0 z-30 w-full max-w-2xl border-l border-slate-200 bg-white shadow-panel">
      <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Ticket tafsiloti</p>
          <h3 className="mt-1 text-lg font-semibold text-slate-900">{ticket.customer_name || "Mijoz"}</h3>
        </div>
        <button onClick={onClose} className="rounded-xl border border-slate-200 px-3 py-1.5 text-sm text-slate-500">
          Yopish
        </button>
      </div>
      <div className="space-y-4 overflow-y-auto p-6">
        <div className="flex items-center gap-3">
          <StatusBadge status={ticket.status} />
          <span className="text-sm text-slate-500">{formatDate(ticket.created_at)}</span>
        </div>
        <div className="rounded-2xl bg-slate-50 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Asosiy ma'lumot</p>
          <p className="mt-2 text-sm text-slate-700">{ticket.latest_customer_message_text || "Asosiy xabar ko'rsatilmagan"}</p>
        </div>
        <div className="space-y-3">
          {(ticket.messages || []).map((message) => (
            <article key={message.id} className="rounded-2xl border border-slate-200 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-slate-900">{message.full_name}</p>
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{message.sender_type}</p>
                </div>
                <span className="text-xs text-slate-500">{formatDate(message.created_at)}</span>
              </div>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                {message.text_content || message.text || "Bo'sh xabar"}
              </p>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
