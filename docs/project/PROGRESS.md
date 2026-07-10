# NextRupee — Progress Tracker

Statuses: Not Started · In Progress · Completed · Blocked

| Phase | Status | Notes |
|---|---|---|
| 0 — Planning | Completed | Five planning docs, 2026-07-10 |
| 1 — Backend scaffold | Completed | Schemas, profile API, migration, CI; 20 tests |
| 2 — Rules engine | Completed | ±1-rupee boundaries, hierarchy, property tests; 50 tests total |
| 3 — Gold engine | Completed | Feeds+cache+freshness, 31-node graph, regime signal; 83 total |
| 4 — RAG | Completed | 10 authored docs, graph-then-vector, 20 spot-checks; 111 total |
| 5 — LLM + guardrails | Completed | Prose-only fill, number diff, refusals, /api/nbca + /api/ask; 153 total |
| 6 — Frontend | Completed | Landing, intake, cards, ask-why; lint+build clean; journey smoke-tested |
| 7 — Evals in CI | Completed | Golden 50 @100%, Tier 0/1 gates, Tier 2 nightly runner |
| 8 — Ship | Completed | Docker, render.yaml, hardening, README, demo script, demo fallback |

**Overall completion: 100% (9/9 phases)**

Remaining owner actions (require accounts/credentials — cannot be automated here):
create the Render/Vercel/Supabase projects, set secrets (`SUPABASE_URL`,
`SUPABASE_SERVICE_KEY`, `LLM_API_KEY`, `FRED_API_KEY`), run the SQL migration,
point cron-job.org at `/health`, and paste the live URL into README.
