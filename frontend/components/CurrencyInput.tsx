"use client";

import { rupees } from "@/lib/format";

interface Props {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
  hint?: string;
  max?: number;
}

/** Currency input pattern: mono digits, live Indian grouping preview, no arithmetic. */
export default function CurrencyInput({ label, value, onChange, hint, max = 100_000_000 }: Props) {
  return (
    <label className="block">
      <span className="field-label">{label}</span>
      <div className="relative">
        <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 font-mono text-[15px] text-ink-3">
          ₹
        </span>
        <input
          type="text"
          inputMode="numeric"
          className="field-input pl-9"
          value={value === null ? "" : value.toString()}
          placeholder="0"
          onChange={(e) => {
            const digits = e.target.value.replace(/[^0-9]/g, "");
            if (digits === "") return onChange(null);
            const n = Math.min(parseInt(digits, 10), max);
            onChange(Number.isNaN(n) ? null : n);
          }}
        />
      </div>
      <span className="mt-1.5 flex justify-between font-sans text-[13px] text-ink-3">
        <span>{hint}</span>
        {value !== null && value > 0 && <span className="font-mono">{rupees(value)}</span>}
      </span>
    </label>
  );
}
