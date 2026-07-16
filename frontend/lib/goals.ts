/** Life goals shared by intake (picker) and results (header framing).
 *  Ids are stable — the backend receives them in ProfileIn.goals. */
export const GOALS = [
  { id: "emergency", label: "Feel financially safe" },
  { id: "debt_free", label: "Get out of debt" },
  { id: "wealth", label: "Grow long-term wealth" },
  { id: "retirement", label: "Retire comfortably" },
  { id: "house", label: "A house deposit" },
  { id: "child_education", label: "My child's education" },
  { id: "wedding", label: "A wedding" },
  { id: "diwali_gold", label: "Gold for Diwali" },
  { id: "big_purchase", label: "A big purchase soon" },
  { id: "dream_trip", label: "A dream trip" },
] as const;

export function goalLabel(id: string): string | null {
  return GOALS.find((g) => g.id === id)?.label ?? null;
}
