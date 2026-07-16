"""RAG tests: corpus integrity, chunking, graph-filtered retrieval spot-checks.

The 20 spot-checks (Phase 4 exit criteria) assert that for each query the
expected document is retrieved AND the citation carries a chunk id.
"""

from __future__ import annotations

import pytest

from app.gold.rag import MemoryStore, causal_context, load_corpus, retrieve


@pytest.fixture(scope="module")
def store() -> MemoryStore:
    s = MemoryStore()
    s.add(load_corpus())
    return s


class TestCorpus:
    def test_all_docs_load_with_frontmatter(self):
        chunks = load_corpus()
        doc_ids = {c.doc_id for c in chunks}
        assert len(doc_ids) == 20  # 10 gold-regime docs + 10 asset-class docs

    def test_chunk_ids_are_stable_citation_refs(self):
        for c in load_corpus():
            doc_id, _, n = c.id.partition("#")
            assert doc_id == c.doc_id and n.isdigit()

    def test_chunks_are_reasonably_sized(self):
        for c in load_corpus():
            assert 30 <= len(c.text.split()) <= 220, c.id

    def test_every_chunk_tagged(self):
        assert all(c.tags for c in load_corpus())


class TestGraphFilteredRetrieval:
    def test_tag_filter_excludes_offtopic_chunks(self, store):
        # pure-India duty query must not surface the US-macro structural note
        results = store.query("import duty smuggling premium", k=8,
                              allowed_tags={"duty", "policy"})
        assert results
        assert all({"duty", "policy"} & set(r.chunk.tags) for r in results)

    def test_no_filter_returns_topk(self, store):
        assert len(store.query("gold", k=3, allowed_tags=None)) == 3

    def test_deterministic_ordering(self, store):
        q = "why is gold expensive right now?"
        a = [r.chunk.id for r in store.query(q, 5, None)]
        b = [r.chunk.id for r in store.query(q, 5, None)]
        assert a == b

    def test_causal_context_carries_graph_edges(self):
        edges = causal_context("why is gold expensive right now?")
        assert any(e["from"] == "us_real_yield_10y" for e in edges)


# 20 retrieval spot-checks: (query, doc_id expected among top-4)
SPOT_CHECKS = [
    ("why is gold expensive right now?", "real-yields-structural"),
    ("what do real yields do to gold", "real-yields-structural"),
    ("gold and TIPS opportunity cost", "real-yields-structural"),
    ("should I buy gold for Diwali?", "festival-seasonality"),
    ("does wedding season move gold prices", "festival-seasonality"),
    ("festival premium on gold", "festival-seasonality"),
    ("what happened to gold import duty in 2013", "regime-2013-duty-hikes"),
    ("import duty history India", "import-duty-history"),
    ("duty cut effect on resale value", "import-duty-history"),
    ("smuggling and the grey market", "regime-2013-duty-hikes"),
    ("gold in the 2008 financial crisis", "regime-2008-gfc"),
    ("gold crashed during a crisis why", "regime-2008-gfc"),
    ("covid pandemic gold record high", "regime-2020-covid"),
    ("gold discount during lockdown India", "regime-2020-covid"),
    ("why didn't gold fall when the Fed hiked in 2022", "regime-2022-rate-cycle"),
    ("central bank buying tonnes record", "regime-2022-rate-cycle"),
    ("sovereign gold bond interest tax", "sgb-and-paper-routes"),
    ("jewellery making charges investment", "sgb-and-paper-routes"),
    ("rupee depreciation gold hedge", "inr-depreciation"),
    ("who sets the gold price jewellery or investors", "demand-structure-wgc"),
]


@pytest.mark.parametrize("query,expected_doc", SPOT_CHECKS)
def test_retrieval_spot_check(store, query, expected_doc):
    results = retrieve(query, k=4, store=store)
    assert results, query
    got_docs = [r.chunk.doc_id for r in results]
    assert expected_doc in got_docs, f"{query!r} → {got_docs}"
    for r in results:
        assert "#" in r.chunk.id  # citation-ready chunk id
        assert r.related_nodes    # graph routing recorded
