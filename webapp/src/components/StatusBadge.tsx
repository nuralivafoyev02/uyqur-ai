import { classNames } from "lib/format";
import type { TicketStatus } from "types/api";

const palette: Record<TicketStatus, string> = {
  open: "bg-amber-50 text-amber-700 border-amber-200",
  answered: "bg-sky-50 text-sky-700 border-sky-200",
  closed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  reopened: "bg-orange-50 text-orange-700 border-orange-200",
  auto_replied: "bg-cyan-50 text-cyan-700 border-cyan-200"
};

export function StatusBadge({ status }: { status: TicketStatus }) {
  const label =
    status === "auto_replied"
      ? "Avto-javob"
      : status === "closed"
        ? "Yopilgan"
        : status === "reopened"
          ? "Qayta ochilgan"
          : status === "answered"
            ? "Javob berilgan"
            : "Ochiq";
  return <span className={classNames("inline-flex rounded-full border px-2.5 py-1 text-xs font-medium", palette[status])}>{label}</span>;
}
