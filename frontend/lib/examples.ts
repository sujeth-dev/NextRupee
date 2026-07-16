import type { ProfileIn } from "@/lib/api";

/** Three simulated cases a visitor can open with one click. Each routes to the
 *  real /results flow — the engine computes these live, nothing is canned.
 *  Chosen to exercise three different leading actions. */

export interface ExampleCase {
  id: string;
  title: string;
  who: string;
  numbers: string[];
  expect: string;
  profile: Omit<ProfileIn, "session_id">;
}

export const EXAMPLE_CASES: ExampleCase[] = [
  {
    id: "diwali-dilemma",
    title: "The Diwali dilemma",
    who: "Salaried, 32 — family wants gold this Diwali, but the credit card is loaded.",
    numbers: ["₹1,00,000/mo in", "₹60,000/mo out", "₹4L saved", "₹1.2L card debt at 42%"],
    expect: "See why clearing the card beats buying gold — with the exact arithmetic.",
    profile: {
      monthly_income: 100000,
      monthly_expenses: 60000,
      cash_savings: 400000,
      hi_debt_amount: 120000,
      hi_debt_apr: 42,
      dependents: false,
      term_insurance: true,
      risk_tolerance: "medium",
      goals: ["diwali_gold"],
    },
  },
  {
    id: "fresh-starter",
    title: "The fresh starter",
    who: "First job, 24 — no debt, wants to start investing but has a thin cushion.",
    numbers: ["₹45,000/mo in", "₹30,000/mo out", "₹40,000 saved", "no debt"],
    expect: "See why the safety net comes before the first SIP — and how big it should be.",
    profile: {
      monthly_income: 45000,
      monthly_expenses: 30000,
      cash_savings: 40000,
      hi_debt_amount: 0,
      hi_debt_apr: 0,
      dependents: false,
      term_insurance: false,
      risk_tolerance: "medium",
      goals: ["emergency", "wealth"],
    },
  },
  {
    id: "family-shield",
    title: "The family shield",
    who: "Two kids, 41 — solid savings, family depends on one income, no term cover.",
    numbers: ["₹1,50,000/mo in", "₹90,000/mo out", "₹7L saved", "family depends on them"],
    expect: "See why protection ranks above investing when people depend on your income.",
    profile: {
      monthly_income: 150000,
      monthly_expenses: 90000,
      cash_savings: 700000,
      hi_debt_amount: 0,
      hi_debt_apr: 0,
      dependents: true,
      term_insurance: false,
      risk_tolerance: "low",
      goals: ["child_education"],
    },
  },
];
