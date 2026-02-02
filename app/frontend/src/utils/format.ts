export function formatDateTime(value: unknown): string {
  if (value === null || value === undefined) return "—";
  const s = String(value);
  if (!s) return "—";
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString();
}

