"use client";

interface Props {
  label: string;
  yesLabel: string;
  noLabel: string;
  value: boolean | null;
  onChange: (v: boolean) => void;
}

/** Binary decision cards pattern. */
export default function BinaryChoice({ label, yesLabel, noLabel, value, onChange }: Props) {
  return (
    <fieldset>
      <legend className="field-label">{label}</legend>
      <div className="grid grid-cols-2 gap-3">
        {[
          { v: true, text: yesLabel },
          { v: false, text: noLabel },
        ].map(({ v, text }) => {
          const active = value === v;
          return (
            <button
              key={String(v)}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(v)}
              className={`rounded-card border p-4 text-left font-sans text-[15px] transition-colors ${
                active
                  ? "border-indigo-600 bg-indigo-100/60 ring-1 ring-indigo-600 text-ink font-medium"
                  : "border-border bg-white text-ink-2 hover:border-indigo-300"
              }`}
            >
              {text}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
