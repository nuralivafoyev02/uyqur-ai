import type { ReactNode } from "react";

export function StatCard({
  title,
  value,
  helper,
  accent
}: {
  title: string;
  value: ReactNode;
  helper?: string;
  accent?: string;
}) {
  return (
    <div className={`rounded-2xl border border-white/70 bg-white/90 p-4 shadow-panel ${accent ?? ""}`}>
      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{title}</p>
      <div className="mt-3 text-3xl font-semibold text-slate-950">{value}</div>
      {helper ? <p className="mt-2 text-sm text-slate-500">{helper}</p> : null}
    </div>
  );
}
