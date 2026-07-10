"use client";

import { useState } from "react";
import { api, type AskResponse } from "@/lib/api";

const SUGGESTIONS = [
  "Why is gold expensive right now?",
  "Should I buy gold for Diwali?",
  "What does import duty do to gold prices?",
];

/** Why-Q&A: cited, live-data answers. Refusals render calmly, not as errors. */
export default function AskBox() {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

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

      <div className="mt-3 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
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
        ))}
      </div>

      {error && (
        <p className="mt-4 rounded-chip bg-error-bg px-4 py-3 text-[14px] text-error">{error}</p>
      )}

      {result && (
        <div className="mt-4 rounded-chip border border-border bg-surface-2 p-4">
          <p className="whitespace-pre-line text-[14px] leading-relaxed text-ink-2">
            {result.answer}
          </p>
          {!result.refused && result.citations.length > 0 && (
            <p className="mt-3 border-t border-border pt-3 font-mono text-[12px] text-ink-3">
              sources: {result.citations.join(" · ")}
              {result.degraded && " · assembled from sources without a language model"}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
