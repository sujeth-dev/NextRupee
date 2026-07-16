/** API client. All numbers come from the server's rules engine — never computed here. */

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Evidence {
  claim: string;
  source: "rules_engine" | "gold_engine" | "document";
  ref: string;
  value: string | null;
}

export interface NBCA {
  action: string;
  category: "stabilize" | "emergency_fund" | "debt" | "insurance" | "invest_allocation";
  amount_range: [number, number];
  rationale_chain: string[];
  evidence: Evidence[];
  confidence: "high" | "medium" | "low";
  confidence_basis: string;
  invalidation_conditions: string[];
  alternatives: string[];
  opportunity_cost: string;
  degraded: boolean;
}

export interface NBCAResponse {
  cards: NBCA[];
  in_distress: boolean;
  gold_adjustment_pts: number;
  confidence_cap: string;
  data_freshness: Record<string, { asof: string; days_old: number; status: string }>;
  model: string;
  prompt_version: string;
  degraded_count: number;
}

export interface ProfileIn {
  session_id: string;
  monthly_income: number;
  monthly_expenses: number;
  cash_savings: number;
  hi_debt_amount: number;
  hi_debt_apr: number;
  dependents: boolean;
  term_insurance: boolean;
  risk_tolerance: "low" | "medium" | "high";
  goals: string[];
}

export interface AskResponse {
  /** One-line, plain-language answer. */
  headline: string;
  /** Grounded explanation with inline [chunk-id]/[driver:id] citations. */
  detail: string;
  /** Deprecated: headline + detail concatenated; kept for older consumers. */
  answer: string;
  citations: string[];
  refused: boolean;
  degraded: boolean;
  confidence_cap: string | null;
}

async function post<T>(path: string, body: unknown, timeoutMs = 90_000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  nbca: (profile: ProfileIn) => post<NBCAResponse>("/api/nbca", { profile }),
  ask: (question: string) => post<AskResponse>("/api/ask", { question }),
  /** Cheap wake-up call for Render free-tier cold starts. */
  health: async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
      return res.ok;
    } catch {
      return false;
    }
  },
};
