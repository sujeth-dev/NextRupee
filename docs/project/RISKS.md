# NextRupee — Risk Register

| ID | Risk | Type | Likelihood | Impact | Mitigation | Status |
|---|---|---|---|---|---|---|
| R-01 | LLM output fails schema repeatedly | Technical | Med | Med | One retry w/ error feedback → deterministic fallback card (`degraded=true`), logged | Mitigated by design |
| R-02 | OpenRouter free-route rate limits (≈20 req/min, ≈200 req/day per model) hit during demo burst or nightly evals | Technical/Cost | Med | Med | Exponential backoff + secondary free model fallback chain → fallback card; Tier 2 sampled, not full-set, if quota low | Open |
| R-03 | Data feed breaks / stale drivers | Technical | Med | Med | `asof` stamping; >7d ⇒ flagged + confidence capped `medium`; >30d ⇒ engine facts excluded, structural knowledge only | Mitigated by design |
| R-04 | Model names a specific instrument | Security/Compliance | Med | High | Post-generation regex+lexicon scan blocks & regenerates; 25-prompt adversarial suite in CI | Mitigated by design |
| R-05 | Perceived as investment advice | Legal | Low | High | Asset-class-only actions, disclaimer in README + UI footer, refusal template for instrument requests | Mitigated by design |
| R-06 | Render cold start (~30–50s) ruins the demo | Deployment | High | Med | Frontend warm-up state + pre-computed cached demo profile renders instantly | Mitigated by design |
| R-07 | Supabase free project auto-pauses after ~1wk idle | Deployment | High | Med | cron-job.org pings `/health`, which performs a real DB read (D-004) | Mitigated by design |
| R-08 | Eval cost creep | Cost | Low | Low | Tiering (Tier 0 free, Tier 1 cents); per-PR budget assertion; free LLM routes | Mitigated by design |
| R-09 | Scope creep | Product | High | High | Roadmap frozen; nothing new after Phase 8; why-Q&A is first scope cut | Open — enforced by process |
| R-10 | Rules-engine boundary bugs (distress triggers) | Technical | Med | High | ±1-rupee boundary unit tests on every trigger; property test: no invest card under any distress trigger | Mitigated by tests |
| R-11 | Repo flipped private → GH Actions minutes capped (~2,000/mo) | Cost | Low | Low | Keep repo public (portfolio intent); noted in README | Accepted |
| R-12 | Reproducibility drift (same profile ⇒ different ranking) | Technical | Low | High | Zero randomness in engine; property test asserts identical output; LLM only fills prose | Mitigated by tests |
