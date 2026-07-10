"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api, type NBCAResponse, type ProfileIn } from "@/lib/api";
import NBCACard from "@/components/NBCACard";
import AskBox from "@/components/AskBox";

type Phase = "warming" | "loading" | "ready" | "error" | "no-profile";

/** Results: warm-up state for free-tier cold starts, then ranked cards. */
export default function Results() {
  const [phase, setPhase] = useState<Phase>("warming");
  const [data, setData] = useState<NBCAResponse | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const raw = sessionStorage.getItem("nextrupee_profile");
    if (!raw) {
      setPhase("no-profile");
      return;
    }
    const profile = JSON.parse(raw) as ProfileIn;

    (async () => {
      const healthy = await api.health();
      if (!healthy) {
        // Render free tier sleeps; show the warm-up state and retry briefly.
        for (let i = 0; i < 10; i++) {
          await new Promise((r) => setTimeout(r, 6000));
          if (await api.health()) break;
        }
      }
      setPhase("loading");
      try {
        setData(await api.nbca(profile));
        setPhase("ready");
      } catch {
        setPhase("error");
      }
    })();
  }, []);

  if (phase === "no-profile") {
    return (
      <div className="mx-auto max-w-xl py-24 text-center">
        <h1 className="font-display text-2xl font-semibold text-ink">Start with your numbers</h1>
        <p className="mt-2 text-ink-2">There is no profile in this session yet.</p>
        <Link href="/intake" className="btn-primary mt-6">
          Answer the 3-minute intake
        </Link>
      </div>
    );
  }

  if (phase === "warming" || phase === "loading") {
    return (
      <div className="mx-auto max-w-xl py-24 text-center" role="status" aria-live="polite">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-border-strong border-t-indigo-600" />
        <h1 className="mt-6 font-display text-xl font-semibold text-ink">
          {phase === "warming" ? "Waking the engine" : "Running the arithmetic"}
        </h1>
        <p className="mt-2 text-[14px] text-ink-3">
          {phase === "warming"
            ? "The demo runs on a free tier that sleeps when idle — first load can take up to a minute."
            : "Ranking is deterministic: same numbers in, same answer out."}
        </p>
      </div>
    );
  }

  if (phase === "error" || !data) {
    return (
      <div className="mx-auto max-w-xl py-24 text-center">
        <h1 className="font-display text-2xl font-semibold text-ink">The engine is unreachable</h1>
        <p className="mt-2 text-ink-2">
          Please try again in a minute — free-tier services take time to wake.
        </p>
        <Link href="/intake" className="btn-secondary mt-6">
          Back to intake
        </Link>
      </div>
    );
  }

  const stale = Object.entries(data.data_freshness).filter(([, v]) => v.status !== "fresh");

  return (
    <div className="mx-auto max-w-3xl py-10">
      <header>
        <p className="font-mono text-[13px] font-medium uppercase tracking-widest text-indigo-600">
          Your ranked next actions
        </p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight text-ink">
          {data.in_distress ? "Stabilize first — here's the order" : "Do these, in this order"}
        </h1>
        <p className="mt-2 text-[15px] text-ink-2">
          {data.in_distress
            ? "Your numbers tripped a stabilization rule, so investing is off the table until the base is safe. Every card shows why."
            : "One recommendation leads; alternatives stay visible. Expand any card to trace every number."}
        </p>
      </header>

      {data.in_distress && (
        <p className="mt-4 rounded-chip bg-warning-bg px-4 py-3 text-[14px] text-warning">
          Stabilization mode: investment allocations are suppressed by rule, not by judgement.
        </p>
      )}

      {stale.length > 0 && (
        <p className="mt-4 rounded-chip bg-surface-2 px-4 py-3 font-mono text-[13px] text-ink-3">
          Some data is not fresh ({stale.map(([k]) => k).join(", ")}) — confidence is capped at{" "}
          {data.confidence_cap}.
        </p>
      )}

      <div className="mt-8 space-y-4">
        {data.cards.map((card, i) => (
          <NBCACard key={i} card={card} rank={i + 1} />
        ))}
      </div>

      <div className="mt-12">
        <AskBox />
      </div>

      <p className="mt-8 text-center">
        <Link href="/intake" className="font-sans text-[14px] text-indigo-600 hover:text-indigo-700">
          Change my numbers →
        </Link>
      </p>
    </div>
  );
}
