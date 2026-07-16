"""Driver graph integrity + query routing + regime signal bounds."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.gold import feeds
from app.gold.feeds import DriverValue, save_driver
from app.gold.graph import DRIVERS, EDGES, build_graph, doc_tags_for, explain_edges, related_drivers
from app.gold.regime import regime_adjustment, regime_score

TODAY = date(2026, 7, 10)


class TestGraphIntegrity:
    def test_node_count_around_30(self):
        # 30 gold-driver nodes + 10 asset-class reference nodes
        assert 28 <= len(DRIVERS) <= 45

    def test_every_edge_references_declared_nodes(self):
        for src, dst, _sign, _strength, _note in EDGES:
            assert src in DRIVERS, src
            assert dst in DRIVERS, dst

    def test_edge_metadata_valid(self):
        for src, dst, sign, strength, note in EDGES:
            assert sign in (-1, 1), (src, dst)
            assert strength in ("weak", "medium", "strong")
            assert len(note) > 10

    def test_graph_builds_and_is_connected_enough(self):
        g = build_graph()
        assert g.number_of_nodes() == len(DRIVERS)
        assert g.number_of_edges() == len(EDGES)
        isolated = [n for n in g.nodes if g.degree(n) == 0]
        assert not isolated, f"isolated nodes: {isolated}"

    def test_key_causal_paths_exist(self):
        import networkx as nx

        g = build_graph()
        assert nx.has_path(g, "fed_policy", "gold_inr")
        assert nx.has_path(g, "import_duty", "gold_timing_risk")
        assert nx.has_path(g, "festival_season", "gold_inr")


class TestQueryRouting:
    def test_expensive_query_routes_to_price_and_timing(self):
        nodes = related_drivers("why is gold expensive right now?")
        assert "gold_usd" in nodes and "gold_timing_risk" in nodes
        # 1-hop expansion pulls in causes
        assert "us_real_yield_10y" in nodes or "usd_index" in nodes

    def test_diwali_query_routes_to_seasonal(self):
        nodes = related_drivers("should I buy gold for Diwali?")
        assert "festival_season" in nodes and "local_demand" in nodes

    def test_duty_query(self):
        nodes = related_drivers("what does import duty do to prices")
        assert "import_duty" in nodes

    def test_unmatched_query_gets_defaults(self):
        nodes = related_drivers("zzz qqq")
        assert "gold_allocation_case" in nodes

    def test_routing_is_deterministic(self):
        q = "why is gold expensive right now?"
        assert related_drivers(q) == related_drivers(q)

    def test_doc_tags_collected(self):
        tags = doc_tags_for(["import_duty", "festival_season"])
        assert {"india", "policy", "duty", "seasonal"} <= tags

    def test_explain_edges_subgraph_only(self):
        edges = explain_edges(["import_duty", "gold_inr"])
        assert all(e["from"] in ("import_duty", "gold_inr") for e in edges)
        assert any(e["from"] == "import_duty" and e["to"] == "gold_inr" for e in edges)


class TestRegimeSignal:
    @pytest.fixture(autouse=True)
    def isolated_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr(feeds, "CACHE_DIR", tmp_path)

    def _seed(self, real_yield=None, dxy=None, days_old=0):
        asof = (TODAY - timedelta(days=days_old)).isoformat()
        if real_yield is not None:
            save_driver(DriverValue("us_real_yield_10y", "ry", real_yield, "%", asof, "t"))
        if dxy is not None:
            save_driver(DriverValue("usd_index", "dxy", dxy, "index", asof, "t"))

    def test_low_real_yield_supportive(self):
        self._seed(real_yield=0.5)
        assert regime_adjustment(TODAY) == 5

    def test_high_real_yield_and_strong_dollar_hostile(self):
        self._seed(real_yield=2.5, dxy=107.0)
        assert regime_adjustment(TODAY) == -5

    def test_neutral_zone_zero(self):
        self._seed(real_yield=1.5, dxy=100.0)
        assert regime_adjustment(TODAY) == 0

    def test_no_data_zero(self):
        assert regime_adjustment(TODAY) == 0

    def test_expired_driver_ignored(self):
        self._seed(real_yield=0.5, days_old=45)
        assert regime_adjustment(TODAY) == 0

    def test_score_is_bounded_signal_input(self):
        self._seed(real_yield=0.5, dxy=100.0)
        from app.gold.feeds import usable_drivers

        assert regime_score(usable_drivers(TODAY)) in (-2, -1, 0, 1, 2)
