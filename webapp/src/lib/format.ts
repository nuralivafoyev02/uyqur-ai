export function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("uz-UZ", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatDuration(seconds?: number | null) {
  if (seconds == null) return "-";
  const total = Math.round(seconds);
  const mins = Math.floor(total / 60);
  const secs = total % 60;
  if (mins >= 60) {
    const hours = Math.floor(mins / 60);
    return `${hours} soat ${mins % 60} daqiqa`;
  }
  if (mins > 0) return `${mins} daqiqa ${secs} soniya`;
  return `${secs} soniya`;
}

export function classNames(...items: Array<string | false | null | undefined>) {
  return items.filter(Boolean).join(" ");
}
