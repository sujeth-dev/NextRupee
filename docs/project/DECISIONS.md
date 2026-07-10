# NextRupee — Engineering Decision Log

Append-only. Reference before making new architectural decisions. Format: Decision · Reasoning · Alternatives · Trade-offs · Final choice · Date.

---

## D-001 — Repository layout: monorepo (`backend/`, `frontend/`, `evals/`, `supabase/`)
- **Reasoning:** Single portfolio repo; CI, docs, and evals share the golden set and schemas. Reviewers read one README.
- **Alternatives:** Split repos (extra CI plumbing, worse for portfolio review).
- **Trade-offs:** Slightly heavier CI matrix; mitigated with path filters.
- **Final:** Monorepo. — 2026-07-10

## D-002 — LLM provider: OpenRouter free-tier routing, provider-abstracted
- **Reasoning:** Owner directive (2026-07-10): $0 LLM cost via OpenRouter free routes (GLM etc.). Free routes cap ~20 req/min / ~200 req/day per model, so the client implements retry with exponential backoff and a fallback chain (primary free model → secondary free model → deterministic fallback card). Master Doc named Claude Sonnet/Haiku; the abstraction keeps that a one-env-var swap (`LLM_BASE_URL`/`LLM_MODEL`), since OpenRouter is OpenAI-compatible.
- **Alternatives:** Direct Anthropic/OpenAI APIs (cost), local model (infra weight).
- **Trade-offs:** Free-route quality/latency variance; mitigated by schema validation + retry + fallback card (product never 500s regardless).
- **Final:** OpenRouter default; provider-agnostic client. — 2026-07-10

## D-003 — Backend host: Render (Railway noted as alternative)
- **Reasoning:** Master Doc locks Render; previous-deploy rollback API and per-PR previews fit the pipeline. Railway is a viable swap but offers no advantage worth deviating from the locked choice.
- **Trade-offs:** Free tier sleeps (~30–50s cold start) — handled by frontend warm-up state + pre-computed cached demo profile.
- **Final:** Render (`render.yaml` in repo). — 2026-07-10

## D-004 — `/health` touches Supabase
- **Reasoning:** Supabase free projects auto-pause after ~1 week idle. The cron-job.org uptime ping must therefore hit an endpoint that performs a real DB read, not just process liveness. `/health` reports per-driver data freshness AND runs a cheap `select 1`-style query.
- **Final:** DB-touching `/health`. — 2026-07-10

## D-005 — Vector store: Chroma behind a `VectorStore` interface; deterministic in-memory store for CI
- **Reasoning:** Master Doc locks Chroma (local persistent) for the product. CI Tier 0/1 must be free and fast, so tests run against an in-memory store with a deterministic local embedding (hashing-based) — no network, no model download. Same interface, same retrieval logic under test.
- **Alternatives:** Chroma-in-CI (heavy install, embedding downloads), FAISS (another dep).
- **Trade-offs:** CI doesn't exercise Chroma internals; acceptable — retrieval logic (graph-then-vector, tag filtering, chunk ids) is what's ours and it's fully covered.
- **Final:** `VectorStore` protocol; `ChromaStore` (prod) + `MemoryStore` (CI). — 2026-07-10

## D-006 — Persistence: Supabase via REST (postgrest) with append-only writes; offline no-op fallback
- **Reasoning:** Keeps the API deployable without DB credentials (local dev, CI): the storage layer degrades to structured-log-only mode with a `persisted=false` flag rather than failing. Profiles are append-only (never UPDATE) per Master Doc §3.
- **Trade-offs:** No local Postgres in unit tests; storage layer is thin enough that contract tests + migration SQL cover it.
- **Final:** Thin `Storage` interface: `SupabaseStorage` + `NullStorage`. — 2026-07-10

## D-007 — All arithmetic in the rules engine; LLM fills prose fields only
- **Reasoning:** Master Doc non-negotiable #1. The engine computes `amount_range`, scores, and every `Evidence.value`; the LLM receives them read-only and any numeric token in LLM output is diffed against evidence values — mismatch blocks the card.
- **Final:** Enforced by `guardrails/output_guard.py` number-diff. — 2026-07-10

## D-008 — Money handled in integer rupees
- **Reasoning:** Avoids float drift in boundary tests (±1 rupee distress cases). Inputs accepted as numbers, normalised to `int` rupees at the schema boundary.
- **Final:** `int` rupees end-to-end in engine; display formatting in frontend. — 2026-07-10

## D-009 — Driver graph: NetworkX DiGraph built from declarative edge table
- **Reasoning:** Locked choice. Edges declared as data (direction, sign, strength, note, doc tags) so the graph is inspectable, testable, and drives both retrieval filtering and the regime signal.
- **Final:** `gold/graph.py` builds from `DRIVERS`/`EDGES` constants. — 2026-07-10

## D-010 — Gold regime signal bounded to ±5pts of gold allocation
- **Reasoning:** Master Doc §5.5 — the one place the engine touches ranking, deliberately bounded. Signal derived from real-yield + USD + INR momentum direction; clamped in code and property-tested.
- **Final:** `regime_adjustment() ∈ {-5, 0, +5}`. — 2026-07-10
