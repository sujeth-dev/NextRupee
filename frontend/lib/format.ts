/** Indian-style rupee grouping: 1234567 → ₹12,34,567. Display only — no arithmetic. */
export function rupees(n: number): string {
  const sign = n < 0 ? "-" : "";
  const s = Math.abs(Math.round(n)).toString();
  if (s.length <= 3) return `${sign}₹${s}`;
  const tail = s.slice(-3);
  let head = s.slice(0, -3);
  const parts: string[] = [];
  while (head.length > 2) {
    parts.unshift(head.slice(-2));
    head = head.slice(0, -2);
  }
  if (head) parts.unshift(head);
  return `${sign}₹${parts.join(",")},${tail}`;
}

export function rangeLabel([lo, hi]: [number, number]): string {
  return lo === hi ? rupees(hi) : `${rupees(lo)} – ${rupees(hi)}`;
}
