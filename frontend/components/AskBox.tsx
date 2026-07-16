"use client";

import { useState } from "react";
import { api, type AskResponse } from "@/lib/api";

/** Shown before "More questions" is opened: one from each theme, mixed. */
const FEATURED = [
  "How much should I invest each month?",
  "Why is gold expensive right now?",
  "How much emergency fund do I actually need?",
  "Is it better to prepay debt or invest?",
  "How do I save for a house deposit?",
];

const CATEGORIES: { label: string; questions: string[] }[] = [
  {
    label: "Getting started",
    questions: [
      "How much should I invest each month?",
      "What's a SIP and how do I start one?",
      "How do I build the habit of investing regularly?",
      "What should I do first — save or invest?",
    ],
  },
  {
    label: "Your goals",
    questions: [
      "How do I save for a house deposit?",
      "What's a realistic plan for retirement?",
      "How do I plan for my child's education?",
    ],
  },
  {
    label: "Risk & safety",
    questions: [
      "How much emergency fund do I actually need?",
      "What happens if the market drops right after I invest?",
      "Should I be worried about my debt?",
    ],
  },
  {
    label: "Gold & the market",
    questions: [
      "Why is gold expensive right now?",
      "Should I buy gold for Diwali?",
      "What does import duty do to gold prices?",
    ],
  },
  {
    label: "Tax & practical",
    questions: [
      "Do I pay tax on investment gains?",
      "Is it better to prepay debt or invest?",
    ],
  },
];

/** Why-Q&A: a one-line plain answer up top, the cited detail beneath.
 *  Refusals render calmly, not as errors. */
export default function AskBox() {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  async function submit(q: string) {
    if (q.trim().length < 3 || busy) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.ask(q.trim()));
    } catch {
      setError("The engine could not be reached. It may be waking up — try again shortly.");
    } finally {
      setBusy(false);
    }
  }

  const chip = (s: string) => (
    <button
      key={s}
      type="button"
      className="rounded-full border border-border-strong bg-white px-3 py-1.5 font-sans text-[13px] text-ink-2 transition-colors hover:border-indigo-300 hover:text-indigo-700"
      onClick={() => {
        setQuestion(s);
        void submit(s);
      }}
    >
      {s}
    </button>
  );

  return (
    <section className="card p-6">
      <h2 className="font-display text-lg font-semibold text-ink">Ask why</h2>
      <p className="mt-1 text-[13px] text-ink-3">
        Answers cite live drivers and source documents. No instrument picks — ever.
      </p>

      <form
        className="mt-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void submit(question);
        }}
      >
        <input
          type="text"
          className="field-input flex-1 !font-sans"
          placeholder="Why is gold expensive right now?"
          value={question}
          maxLength={500}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" className="btn-primary shrink-0" disabled={busy}>
          {busy ? "Thinking…" : "Ask"}
        </button>
      </form>

      {!showAll ? (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {FEATURED.map(chip)}
          <button
            type="button"
            className="rounded-full px-3 py-1.5 font-sans text-[13px] font-medium text-indigo-600 transition-colors hover:text-indigo-700"
            onClick={() => setShowAll(true)}
          >
            More questions →
          </button>
        </div>
      ) : (
        <div className="mt-3 space-y-3">
          {CATEGORIES.map((cat) => (
            <div key={cat.label}>
              <p className="mb-1.5 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-3">
                {cat.label}
              </p>
              <div className="flex flex-wrap gap-2">{cat.questions.map(chip)}</div>
            </div>
          ))}
          <button
            type="button"
            className="font-sans text-[13px] font-medium text-indigo-600 hover:text-indigo-700"
            onClick={() => setShowAll(false)}
          >
            ← Fewer questions
          </button>
        </div>
      )}

      {error && (
        <p className="mt-4 rounded-chip bg-error-bg px-4 py-3 text-[14px] text-error">{error}</p>
      )}

      {busy && (
        <div
          className="mt-4 flex items-center gap-2.5 rounded-chip border border-border bg-surface-2 px-4 py-3.5"
          role="status"
          aria-label="Thinking"
        >
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="font-sans text-[13px] text-ink-3">reading the sources…</span>
        </div>
      )}

      {result && result.refused && (
        <div className="reveal mt-4 rounded-chip border border-indigo-100 bg-indigo-100/40 p-4">
          <div className="flex gap-3">
            <svg
              viewBox="0 0 24 24"
              className="mt-0.5 h-5 w-5 shrink-0 text-indigo-600"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="9" />
              <path d="m15.5 8.5-2 5-5 2 2-5 5-2Z" />
            </svg>
            <div>
              <p className="font-display text-[16px] font-semibold leading-snug text-ink">
                {result.headline}
              </p>
              <p className="mt-2 text-[14px] leading-relaxed text-ink-2">{result.detail}</p>
            </div>
          </div>
        </div>
      )}

      {result && !result.refused && (
        <div className="mt-4 rounded-chip border border-border bg-surface-2 p-4">
          <div className="reveal flex gap-3">
            <span className="mt-0.5 w-1 shrink-0 self-stretch rounded-full bg-indigo-600" aria-hidden="true" />
            <p className="font-display text-[17px] font-semibold leading-snug text-ink">
              {result.headline}
            </p>
          </div>
          <div className="reveal reveal-1 mt-3 border-t border-border pt-3">
            <p className="font-mono text-[11px] font-medium uppercase tracking-widest text-ink-3">
              Detail
            </p>
            <p className="mt-1.5 whitespace-pre-line text-[14px] leading-relaxed text-ink-2">
              {result.detail}
            </p>
          </div>
          {result.citations.length > 0 && (
            <p className="reveal reveal-2 mt-3 border-t border-border pt-3 font-mono text-[12px] text-ink-3">
              sources: {result.citations.join(" · ")}
              {result.degraded && " · assembled from sources without a language model"}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
