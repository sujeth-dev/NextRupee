"use client";

import { useRouter } from "next/navigation";
import { EXAMPLE_CASES } from "@/lib/examples";
import type { ProfileIn } from "@/lib/api";

/** One-click simulated cases: writes the sample profile to the session and opens
 *  the real results flow — the engine ranks it live, nothing is pre-rendered. */
export default function ExampleCases() {
  const router = useRouter();

  function open(id: string, profile: Omit<ProfileIn, "session_id">) {
    const full: ProfileIn = {
      session_id:
        globalThis.crypto?.randomUUID?.() ?? `ex-${Date.now()}-${Math.floor(Math.random() * 1e6)}`,
      ...profile,
    };
    sessionStorage.setItem("nextrupee_profile", JSON.stringify(full));
    sessionStorage.setItem("nextrupee_example", id);
    router.push("/results");
  }

  return (
    <section className="mt-16 max-w-5xl">
      <p className="font-mono text-[13px] font-medium uppercase tracking-widest text-indigo-600">
        Not ready to type numbers? Open a case
      </p>
      <h2 className="mt-2 font-display text-2xl font-semibold tracking-tight text-ink">
        Three real situations, ranked live by the engine
      </h2>
      <div className="mt-6 grid gap-6 sm:grid-cols-3">
        {EXAMPLE_CASES.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => open(c.id, c.profile)}
            className="card group flex flex-col p-6 text-left transition-shadow hover:shadow-md"
          >
            <h3 className="font-display text-[17px] font-semibold text-ink group-hover:text-indigo-700">
              {c.title}
            </h3>
            <p className="mt-2 text-[14px] leading-relaxed text-ink-2">{c.who}</p>
            <p className="mt-3 flex flex-wrap gap-1.5">
              {c.numbers.map((n) => (
                <span
                  key={n}
                  className="rounded-full bg-surface-2 px-2.5 py-1 font-mono text-[12px] text-ink-2"
                >
                  {n}
                </span>
              ))}
            </p>
            <p className="mt-4 border-t border-border pt-3 text-[13px] leading-relaxed text-ink-3">
              {c.expect}
            </p>
            <span className="mt-3 font-sans text-[14px] font-medium text-indigo-600">
              Open this case →
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
