import type { NBCA } from "@/lib/api";

/** Inline SVG icon per action category, drawn in a soft tinted circle.
 *  anchor=stabilize, shield=safety net, flame=debt, umbrella=protection, sprout=grow. */

const PATHS: Record<NBCA["category"], JSX.Element> = {
  stabilize: (
    // anchor
    <>
      <circle cx="12" cy="5" r="2.2" />
      <path d="M12 7.2V20M12 20c-3.8 0-7-2.6-7.6-6.2M12 20c3.8 0 7-2.6 7.6-6.2M4.4 13.8 3 15.4m1.4-1.6 2 .6m13.2-.6 1.4 1.6m-1.4-1.6-2 .6" />
    </>
  ),
  emergency_fund: (
    // shield
    <path d="M12 3 5 5.8v5.4c0 4.3 2.9 8 7 9.3 4.1-1.3 7-5 7-9.3V5.8L12 3Zm-2.6 8.9 1.9 1.9 3.6-3.7" />
  ),
  debt: (
    // flame
    <path d="M12 3.5c.4 2.7-.8 4.2-2.2 5.7C8.3 10.8 7 12.3 7 14.6a5 5 0 0 0 10 0c0-1.6-.7-2.9-1.6-4-.5 1-1.2 1.6-2 2 .3-2.6-.4-6-1.4-9.1Z" />
  ),
  insurance: (
    // umbrella
    <path d="M12 3a8.5 8.5 0 0 0-8.5 8.5c2.5-1.8 5.2-1.8 5.7 0 .8-1.8 4.8-1.8 5.6 0 .5-1.8 3.2-1.8 5.7 0A8.5 8.5 0 0 0 12 3Zm0 8.8V18a2 2 0 0 0 4 0" />
  ),
  invest_allocation: (
    // sprout
    <path d="M12 20v-7m0 0c0-3.3-2.7-6-6-6H4.5v.5c0 3.3 2.7 6 6 6H12Zm0-2c0-3 2.5-5.5 5.5-5.5h2v.5c0 3-2.5 5.5-5.5 5.5H12" />
  ),
};

const TINT: Record<NBCA["category"], string> = {
  stabilize: "bg-surface-2 text-ink-2",
  emergency_fund: "bg-success-bg text-success",
  debt: "bg-error-bg text-error",
  insurance: "bg-indigo-100 text-indigo-600",
  invest_allocation: "bg-warning-bg text-gold-signal",
};

export default function CategoryIcon({ category }: { category: NBCA["category"] }) {
  return (
    <span
      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${TINT[category]}`}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 24 24"
        className="h-[18px] w-[18px]"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {PATHS[category]}
      </svg>
    </span>
  );
}
