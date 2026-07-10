# NextRupee — 90-second demo script

**0:00 — The hook (landing page).**
"It's October. You have ₹60,000 spare. Family says buy gold for Diwali. Your credit
card is at 42% APR. What should you actually do?" Point at the tagline: every number
shows its work.

**0:10 — Intake (3 steps shown, ~25s).**
Enter the hero household: income ₹1,00,000 · expenses ₹60,000 · savings ₹4,00,000 ·
credit card ₹1,20,000 at 42% · no dependents gap · medium risk · goal chip "Gold for
Diwali". Note the calm form patterns — currency inputs group Indian-style, nothing
is gamified.

**0:35 — The answer.**
Two cards, ranked. #1: *pay the 42% debt* — not gold. Say the line: "the engine
ranked this deterministically; the language model only wrote the sentences."

**0:45 — Show the work (expand card #1).**
Walk the cascade: causal chain → evidence chips (every number carries a `calc:` ref) →
confidence basis → alternatives → the amber box: *what would change this advice*.
"Every recommendation is falsifiable — those invalidators are testable conditions."

**1:05 — Ask why.**
Click the suggested question: *why is gold expensive right now?* The answer cites
document chunk ids and live driver values with as-of dates. Mention: retrieval is
graph-then-vector — the causal driver graph picks which documents are even eligible.

**1:20 — The guardrail flex.**
Type: *which gold ETF should I buy?* → calm refusal that reframes to asset-class
reasoning. "Instrument picks are blocked in code, and a 25-prompt adversarial suite
in CI keeps it that way."

**1:30 — Close.**
"Rules engine owns the math, the model is never trusted with a number, and CI fails
if answer quality regresses. Repo README has the eval table."
