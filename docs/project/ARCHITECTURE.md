# NextRupee — Architecture Map

## System overview

```
┌───────────────────────────────┐
│  Next.js 14 (Vercel)          │  landing · intake · NBCA cards · why-Q&A
└──────────────┬────────────────┘
               │ REST/JSON
┌──────────────▼────────────────┐
│  FastAPI (Render)             │
│  ┌─────────────────────────┐  │
│  │ Guardrail middleware    │  │  input refusals · output scans · number diff
│  └───────────┬─────────────┘  │
│  ┌───────────▼─────────────┐  │
│  │ Rules Engine (pure py)  │  │  owns ranking + ALL math, emits Evidence
│  └───────────┬─────────────┘  │
│  ┌───────────▼─────────────┐  │
│  │ Explanation Layer (LLM) │  │  OpenRouter free routes → fallback chain
│  └───────────┬─────────────┘  │  schema-validated or rejected
│  ┌───────────▼─────────────┐  │
│  │ Gold Engine             │  │  feeds (FRED/yfinance/spot) · NetworkX graph
│  │  feeds · graph · RAG    │  │  graph-then-vector retrieval (Chroma)
│  └─────────────────────────┘  │
└──────┬────────────────────────┘
       │ postgrest
┌──────▼─────────┐   ┌──────────────────┐
│ Supabase PG    │   │ GitHub Actions   │ lint · Tier0 · Tier1 · deploy · nightly Tier2
│ profiles       │   └──────────────────┘
│ nbca_log       │
│ eval_runs      │
└────────────────┘
```

## Folder structure

```
backend/
  app/
    config.py              # Settings (env) + rule constants (unit-tested)
    main.py                # FastAPI factory, middleware, router mounting
    schemas/               # nbca.py (NBCA/Evidence), profile.py
    rules/                 # calcs.py, distress.py, engine.py
    gold/                  # feeds.py, graph.py, regime.py, rag.py, corpus/
    llm/                   # client.py (OpenRouter chain), explain.py, ask.py
    llm/prompts/           # versioned prompt files + CHANGELOG
    guardrails/            # input_guard.py, output_guard.py
    storage/               # base.py, supabase.py, null.py
    api/                   # routes: profile, nbca, ask, health
  tests/                   # unit + property + contract tests
  pyproject.toml
  Dockerfile
frontend/                  # Next.js 14 app router + Tailwind (design-guide tokens)
  app/                     # page (landing), intake/, results/
  components/              # NBCACard, EvidenceChip, ConfidenceSignal, ...
  lib/api.ts
evals/
  golden/profiles.json     # 50 expert-authored profiles + expected rankings
  run_tier0.py             # deterministic ranking agreement (blocks merge)
  run_tier1.py             # schema-fill rate, guardrail suite, grounding diff
  run_tier2.py             # nightly LLM-judge rubric → eval_runs
  adversarial.json         # 25 guardrail prompts
supabase/migrations/       # 001_init.sql
.github/workflows/         # ci.yml (PR gates), nightly.yml
docs/project/              # this map, roadmap, decisions, progress, risks
```

## Data flow (happy path)

1. `POST /api/profile` → validated `ProfileIn` → normalised int rupees → append-only insert (`profiles`, versioned by `session_id`).
2. `POST /api/nbca` → rules engine ranks → list of `RankedAction` (category, amount_range, priority, evidence[]) → for each, explanation layer fills prose fields of `NBCA` (never numbers) → output guard: schema, instrument scan, number diff vs evidence → cards logged to `nbca_log` → response.
3. `POST /api/ask` → input guard (instrument refusal) → gold engine: graph lookup → Chroma search filtered by driver doc-tags → top-k chunks → LLM answer w/ chunk-id citations → output guard.
4. Validation failure ⇒ one retry with error feedback ⇒ deterministic fallback card (`degraded=true`).

## State & security boundaries

- LLM never computes: numbers cross the boundary read-only; output number diff enforces it.
- Distress mode re-verified server-side post-generation.
- Secrets only in env (Render/Vercel/GH secrets); `.env.example` documents keys.
- Rate limit 10 req/min/IP; per-day LLM spend/request cap → "demo budget reached".
- Append-only `profiles`; `nbca_log` is the audit trail.

## Deployment

PR → lint + Tier 0 + Tier 1 + Docker build → previews (Render/Vercel).
Merge → deploy → smoke test (health + 1 golden profile) → auto-rollback on failure.
Nightly → feed refresh + Tier 2 → `eval_runs`, fail on >5pt regression.
Uptime: cron-job.org pings `/health` (which performs a real Supabase read — keeps free project unpaused).
