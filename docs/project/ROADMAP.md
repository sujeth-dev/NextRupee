# NextRupee — Master Roadmap

Source of truth for execution order. Derived from `docs/NextRupee_Master_Doc.md` §8 (build plan). Phases map 1:1 to the weekly plan; each phase ends demo-able.

| # | Phase | Objective | Deliverables | Depends on | Success criteria | Risks | Complexity |
|---|---|---|---|---|---|---|---|
| 0 | Planning | Project blueprint | Roadmap, architecture map, decision log, progress tracker, risk register | — | Docs exist, consistent with Master Doc | Drift from Master Doc | Low |
| 1 | Scaffold | Runnable API + contracts | FastAPI app, NBCA + profile Pydantic schemas, profile intake endpoint, Supabase migration SQL, pyproject, CI workflow | 0 | Profile POST→stored (or offline log); NBCA schema round-trips; pytest green | Schema churn later | Low |
| 2 | Rules engine | Deterministic ranking core | Distress triggers, allocation hierarchy, evidence emission, config constants | 1 | 30+ unit tests incl. ±1-rupee distress boundaries; identical-input⇒identical-ranking property test | Boundary bugs | Medium |
| 3 | Gold engine | Live drivers + graph + freshness | Feed fetchers (cached, `asof`-stamped), NetworkX driver graph (~30 nodes), regime signal, staleness rules | 1 | Fetch job runs (graceful offline); stale >7d caps confidence, >30d excludes facts — tested | Feed outages | Medium |
| 4 | RAG | Grounded gold knowledge | Regime corpus (authored docs), ingestion, graph-then-vector retrieval with chunk-id citations, vector-store abstraction | 3 | 20 retrieval spot-checks pass; citations carry chunk ids | Retrieval quality | Medium |
| 5 | LLM + guardrails | Safe explanation layer | Provider abstraction, versioned prompts, schema-validated fill, retry→deterministic fallback, input/output guardrails | 2, 4 | Golden profile → valid NBCA cards; instrument refusal works; fallback path tested; numbers diffed against evidence | Model drift, cost | High |
| 6 | Frontend | Full user journey | Next.js 14 + Tailwind: landing w/ hero scenario, multi-step intake, ranked NBCA cards w/ reasoning disclosure, why-Q&A box | 5 | Full click-through journey against local API | Scope creep; why-box is first cut | High |
| 7 | Evals in CI | Regression gate | Golden set (50 profiles), Tier 0/1 PR gates, Tier 2 nightly runner, cost budget assertion | 2, 5 | Deliberately broken ranking/prompt fails CI; Tier 0 = 100% agreement | Eval cost creep | Medium |
| 8 | Ship | Prod-ready package | Dockerfile, docker-compose, Render/Vercel config, GH Actions deploy pipeline, rate limit, spend cap, `/health`, portfolio README, demo script | all | Builds pass; smoke test path defined; README checklist (§11) complete | Free-tier cold starts | Medium |

Scope rule: nothing new after Phase 8 — only fixes. First cut if behind: why-Q&A box.
