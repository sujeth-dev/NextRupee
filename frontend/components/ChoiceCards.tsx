"use client";

interface Option<T extends string> {
  value: T;
  label: string;
  description: string;
}

interface Props<T extends string> {
  label: string;
  options: Option<T>[];
  value: T | null;
  onChange: (v: T) => void;
}

/** Single-choice cards pattern from the design system. */
export default function ChoiceCards<T extends string>({ label, options, value, onChange }: Props<T>) {
  return (
    <fieldset>
      <legend className="field-label">{label}</legend>
      <div className="grid gap-3 sm:grid-cols-3">
        {options.map((o) => {
          const active = value === o.value;
          return (
            <button
              key={o.value}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(o.value)}
              className={`rounded-card border p-4 text-left transition-colors ${
                active
                  ? "border-indigo-600 bg-indigo-100/60 ring-1 ring-indigo-600"
                  : "border-border bg-white hover:border-indigo-300"
              }`}
            >
              <span className="block font-sans text-[15px] font-medium text-ink">{o.label}</span>
              <span className="mt-1 block text-[13px] leading-snug text-ink-3">
                {o.description}
              </span>
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
