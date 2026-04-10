export function LoadingState({ label = "Yuklanmoqda..." }: { label?: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 p-10 text-center text-sm text-slate-500">
      {label}
    </div>
  );
}
