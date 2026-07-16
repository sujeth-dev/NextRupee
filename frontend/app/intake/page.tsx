"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import CurrencyInput from "@/components/CurrencyInput";
import ChoiceCards from "@/components/ChoiceCards";
import BinaryChoice from "@/components/BinaryChoice";
import type { ProfileIn } from "@/lib/api";
import { GOALS } from "@/lib/goals";

type Risk = "low" | "medium" | "high";

const STEPS = ["Cash flow", "Safety", "Household", "Preferences"] as const;

export default function Intake() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [income, setIncome] = useState<number | null>(null);
  const [expenses, setExpenses] = useState<number | null>(null);
  const [savings, setSavings] = useState<number | null>(null);
  const [hasDebt, setHasDebt] = useState<boolean | null>(null);
  const [debtAmount, setDebtAmount] = useState<number | null>(null);
  const [debtApr, setDebtApr] = useState<number | null>(null);
  const [dependents, setDependents] = useState<boolean | null>(null);
  const [termInsurance, setTermInsurance] = useState<boolean | null>(null);
  const [risk, setRisk] = useState<Risk | null>(null);
  const [goals, setGoals] = useState<string[]>([]);

  const stepValid = useMemo(() => {
    switch (step) {
      case 0:
        return income !== null && expenses !== null;
      case 1:
        if (savings === null || hasDebt === null) return false;
        return hasDebt ? debtAmount !== null && debtApr !== null : true;
      case 2:
        return dependents !== null && termInsurance !== null;
      case 3:
        return risk !== null;
      default:
        return false;
    }
  }, [step, income, expenses, savings, hasDebt, debtAmount, debtApr, dependents, termInsurance, risk]);

  function submit() {
    const profile: ProfileIn = {
      session_id:
        globalThis.crypto?.randomUUID?.() ?? `s-${Date.now()}-${Math.floor(Math.random() * 1e6)}`,
      monthly_income: income ?? 0,
      monthly_expenses: expenses ?? 0,
      cash_savings: savings ?? 0,
      hi_debt_amount: hasDebt ? debtAmount ?? 0 : 0,
      hi_debt_apr: hasDebt ? debtApr ?? 0 : 0,
      dependents: dependents ?? false,
      term_insurance: termInsurance ?? false,
      risk_tolerance: risk ?? "medium",
      goals,
    };
    sessionStorage.setItem("nextrupee_profile", JSON.stringify(profile));
    sessionStorage.removeItem("nextrupee_example");
    router.push("/results");
  }

  return (
    <div className="mx-auto max-w-2xl py-10">
      <nav aria-label="Progress" className="mb-8 flex items-center gap-2">
        {STEPS.map((name, i) => (
          <div key={name} className="flex flex-1 flex-col gap-1.5">
            <div
              className={`h-1 rounded-full ${i <= step ? "bg-indigo-600" : "bg-border-strong"}`}
            />
            <span
              className={`font-sans text-[12px] ${i === step ? "font-medium text-ink" : "text-ink-3"}`}
            >
              {name}
            </span>
          </div>
        ))}
      </nav>

      <div className="card p-8">
        {step === 0 && (
          <div className="space-y-6">
            <h1 className="font-display text-2xl font-semibold text-ink">
              What comes in, what goes out
            </h1>
            <CurrencyInput
              label="Monthly income (take-home)"
              value={income}
              onChange={setIncome}
              hint="After tax, all sources"
            />
            <CurrencyInput
              label="Monthly expenses"
              value={expenses}
              onChange={setExpenses}
              hint="Rent, EMIs, food, everything typical"
            />
          </div>
        )}

        {step === 1 && (
          <div className="space-y-6">
            <h1 className="font-display text-2xl font-semibold text-ink">Your safety position</h1>
            <CurrencyInput
              label="Cash savings you can reach quickly"
              value={savings}
              onChange={setSavings}
              hint="Bank balances, deposits — not locked investments"
            />
            <BinaryChoice
              label="Any high-interest debt? (credit cards, personal loans)"
              yesLabel="Yes, I carry a balance"
              noLabel="No high-interest debt"
              value={hasDebt}
              onChange={setHasDebt}
            />
            {hasDebt && (
              <>
                <CurrencyInput
                  label="Outstanding balance"
                  value={debtAmount}
                  onChange={setDebtAmount}
                  hint="Across high-interest debts"
                />
                <label className="block">
                  <span className="field-label">Interest rate (APR %)</span>
                  <input
                    type="text"
                    inputMode="decimal"
                    className="field-input max-w-[10rem]"
                    value={debtApr === null ? "" : String(debtApr)}
                    placeholder="42"
                    onChange={(e) => {
                      const cleaned = e.target.value.replace(/[^0-9.]/g, "");
                      if (cleaned === "") return setDebtApr(null);
                      const n = Math.min(parseFloat(cleaned), 100);
                      setDebtApr(Number.isNaN(n) ? null : n);
                    }}
                  />
                  <span className="mt-1.5 block font-sans text-[13px] text-ink-3">
                    Credit cards in India typically run 36–48%
                  </span>
                </label>
              </>
            )}
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <h1 className="font-display text-2xl font-semibold text-ink">Who depends on you</h1>
            <BinaryChoice
              label="Does anyone depend on your income?"
              yesLabel="Yes — family depends on me"
              noLabel="No dependents"
              value={dependents}
              onChange={setDependents}
            />
            <BinaryChoice
              label="Do you have term life insurance?"
              yesLabel="Yes, I have term cover"
              noLabel="No term cover"
              value={termInsurance}
              onChange={setTermInsurance}
            />
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <h1 className="font-display text-2xl font-semibold text-ink">How you carry risk</h1>
            <ChoiceCards<Risk>
              label="If your investments fell 20% in a month, you would…"
              value={risk}
              onChange={setRisk}
              options={[
                { value: "low", label: "Sell, sleep", description: "Losses cost me sleep. Stability first." },
                { value: "medium", label: "Hold on", description: "Uncomfortable, but I'd wait it out." },
                { value: "high", label: "Buy more", description: "Drawdowns are part of the deal." },
              ]}
            />
            <fieldset>
              <legend className="field-label">What are you hoping for? (optional)</legend>
              <div className="flex flex-wrap gap-2">
                {GOALS.map((g) => {
                  const active = goals.includes(g.id);
                  return (
                    <button
                      key={g.id}
                      type="button"
                      aria-pressed={active}
                      onClick={() =>
                        setGoals(active ? goals.filter((x) => x !== g.id) : [...goals, g.id])
                      }
                      className={`rounded-full border px-4 py-2 font-sans text-[14px] transition-colors ${
                        active
                          ? "border-indigo-600 bg-indigo-100/60 font-medium text-indigo-700"
                          : "border-border-strong bg-white text-ink-2 hover:border-indigo-300"
                      }`}
                    >
                      {g.label}
                    </button>
                  );
                })}
              </div>
            </fieldset>
          </div>
        )}

        <div className="mt-10 flex items-center justify-between border-t border-border pt-6">
          <button
            type="button"
            className="font-sans text-[15px] text-ink-3 hover:text-ink disabled:invisible"
            disabled={step === 0}
            onClick={() => setStep(step - 1)}
          >
            ← Back
          </button>
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              className="btn-primary"
              disabled={!stepValid}
              onClick={() => setStep(step + 1)}
            >
              Continue
            </button>
          ) : (
            <button type="button" className="btn-primary" disabled={!stepValid} onClick={submit}>
              See my ranked actions
            </button>
          )}
        </div>
      </div>

      <p className="mt-4 text-center font-sans text-[13px] text-ink-3">
        Nothing here is stored with your identity. Numbers stay numbers.
      </p>
    </div>
  );
}
