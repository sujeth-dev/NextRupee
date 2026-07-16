"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api, type NBCAResponse, type ProfileIn } from "@/lib/api";
import NBCACard from "@/components/NBCACard";
import AllocationPanel from "@/components/AllocationPanel";
import AskBox from "@/components/AskBox";
import DemoNotice from "@/components/DemoNotice";
import demoData from "@/lib/demoData.json";
import { goalLabel } from "@/lib/goals";
import { EXAMPLE_CASES } from "@/lib/examples";

type Phase = "warming" | "loading" | "ready" | "demo" | "error" | "no-profile";

const WARMING_LINES = [
  "Waking the engine…",
  "Checking today's gold drivers…",
  "Loading the rules that rank your actions…",
];
const LOADING_LINES = [
  "Crunching your numbers…",
  "Same numbers in, same answer out — ranking is deterministic.",
  "Writing the plain-language explanations…",
];

/** Results: skeleton warm-up for free-tier cold starts, then a staged reveal —
 *  header, top action, then the rest. Other ranked options behind a quiet expander. */
export default function Results() {
  const [phase, setPhase] = useState<Phase>("warming");
  const [data, setData] = useState<NBCAResponse | null>(null);
  const [goal, setGoal] = useState<string | null>(null);
  const [example, setExample] = useState<string | null>(null);
  const [showOthers, setShowOthers] = useState(false);
  const [tick, setTick] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 3500);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const raw = sessionStorage.getItem("nextrupee_profile");
    if (!raw) {
      setPhase("no-profile");
      return;
    }
    const profile = JSON.parse(raw) as ProfileIn;
    setGoal(profile.goals?.length ? goalLabel(profile.goals[0]) : null);
    const exampleId = sessionStorage.getItem("nextrupee_example");
    setExample(EXAMPLE_CASES.find((c) => c.id === exampleId)?.title ?? null);

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
        // Demo resilience: render the pre-computed hero result instead of a dead end.
        setData(demoData as unknown as NBCAResponse);
        setPhase("demo");
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
    const lines = phase === "warming" ? WARMING_LINES : LOADING_LINES;
    return (
      <div className="mx-auto max-w-3xl py-10" role="status" aria-live="polite">
        {/* Ghost of the results layout, so the wait previews the destination. */}
        <div className="skeleton h-4 w-48" />
        <div className="skeleton mt-3 h-9 w-80 max-w-full" />
        <div className="skeleton mt-3 h-4 w-full max-w-xl" />

        <div className="card mt-8 p-6">
          <div className="flex items-start gap-4">
            <div className="skeleton h-8 w-8 !rounded-full" />
            <div className="min-w-0 flex-1">
              <div className="skeleton h-3.5 w-32" />
              <div className="skeleton mt-3 h-6 w-3/4" />
              <div className="skeleton mt-2.5 h-4 w-40" />
            </div>
            <div className="skeleton h-7 w-20 !rounded-full" />
          </div>
        </div>
        <div className="card mt-4 p-6 opacity-60">
          <div className="flex items-start gap-4">
            <div className="skeleton h-8 w-8 !rounded-full" />
            <div className="min-w-0 flex-1">
              <div className="skeleton h-3.5 w-28" />
              <div className="skeleton mt-3 h-6 w-2/3" />
            </div>
          </div>
        </div>

        <p className="mt-8 text-center font-sans text-[14px] text-ink-2">
          {lines[tick % lines.length]}
        </p>
        {phase === "warming" && (
          <p className="mt-1 text-center text-[13px] text-ink-3">
            The demo runs on a free tier that sleeps when idle — first load can take up to a minute.
          </p>
        )}
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
      <header className="reveal">
        <p className="font-mono text-[13px] font-medium uppercase tracking-widest text-indigo-600">
          {goal ? `Building toward: ${goal}` : "Your next best move"}
        </p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight text-ink">
          {data.in_distress ? "Get steady first — here's how" : "Do this first"}
        </h1>
        <p className="mt-2 text-[15px] text-ink-2">
          {data.in_distress
            ? "Your numbers show the base needs securing before any investing — a rule decided that, not a judgement call. Every card shows why."
            : "One clear move leads. Open Details to see every number and why it's there."}
        </p>
      </header>

      {phase === "demo" && <DemoNotice />}

      {example && (
        <p className="reveal reveal-1 mt-4 rounded-chip bg-indigo-100/50 px-4 py-3 text-[14px] text-ink-2">
          You&rsquo;re viewing an example — <strong>{example}</strong>, ranked live by the engine.{" "}
          <Link href="/intake" className="font-medium text-indigo-600 hover:text-indigo-700">
            Use my own numbers →
          </Link>
        </p>
      )}

      {data.in_distress && (
        <p className="reveal reveal-1 mt-4 rounded-chip bg-warning-bg px-4 py-3 text-[14px] text-warning">
          Safety first: investing is paused by a fixed rule until your base is steady — not by opinion.
        </p>
      )}

      {stale.length > 0 && (
        <p className="reveal reveal-1 mt-4 rounded-chip bg-surface-2 px-4 py-3 font-mono text-[13px] text-ink-3">
          Some data is not fresh ({stale.map(([k]) => k).join(", ")}) — confidence is capped at{" "}
          {data.confidence_cap}.
        </p>
      )}

      <div className="reveal reveal-2 mt-8 space-y-4">
        <NBCACard card={data.cards[0]} rank={1} />

        {data.cards.length > 1 && !showOthers && (
          <p className="text-center">
            <button
              type="button"
              className="font-sans text-[14px] font-medium text-indigo-600 hover:text-indigo-700"
              onClick={() => setShowOthers(true)}
            >
              See {data.cards.length - 1} other option{data.cards.length > 2 ? "s" : ""} ▾
            </button>
          </p>
        )}

        {showOthers &&
          data.cards.slice(1).map((card, i) => <NBCACard key={i + 1} card={card} rank={i + 2} />)}
      </div>

      {data.allocation && (
        <div className="reveal reveal-3 mt-8">
          <AllocationPanel allocation={data.allocation} />
        </div>
      )}

      <div className="reveal reveal-4 mt-12">
        <AskBox />
      </div>

      <p className="reveal reveal-4 mt-8 text-center">
        <Link href="/intake" className="font-sans text-[14px] text-indigo-600 hover:text-indigo-700">
          Change my numbers →
        </Link>
      </p>
    </div>
  );
}
