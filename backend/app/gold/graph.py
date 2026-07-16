"""Gold driver knowledge graph (Master Doc §6).

Declarative node/edge tables compiled into a NetworkX DiGraph. Each edge carries
direction (sign), qualitative strength, a historical note, and doc tags that the
RAG layer uses to filter retrieval (graph-then-vector). The graph is data, so it
is inspectable and fully unit-tested.
"""

from __future__ import annotations

from functools import lru_cache

import networkx as nx

#: node id -> (label, kind, doc_tags)
DRIVERS: dict[str, tuple[str, str, list[str]]] = {
    # market drivers
    "gold_usd": ("Gold spot price (USD)", "price", ["price", "macro"]),
    "gold_inr": ("Gold price in India (INR)", "price", ["price", "india"]),
    "us_real_yield_10y": ("US 10y real yield", "macro", ["macro", "rates"]),
    "us_nominal_yield": ("US nominal yields", "macro", ["macro", "rates"]),
    "us_inflation_exp": ("US inflation expectations", "macro", ["macro", "rates"]),
    "usd_index": ("US dollar index (DXY)", "macro", ["macro", "currency"]),
    "fed_policy": ("Federal Reserve policy stance", "macro", ["macro", "rates"]),
    "real_rates_regime": ("Global real-rates regime", "macro", ["macro", "rates", "regime"]),
    "risk_sentiment": ("Global risk sentiment", "macro", ["macro", "crisis"]),
    "geopolitical_risk": ("Geopolitical risk", "macro", ["macro", "crisis"]),
    "central_bank_buying": ("Central bank gold buying", "flow", ["flows", "structural"]),
    "etf_flows": ("Gold ETF flows", "flow", ["flows"]),
    "mine_supply": ("Mine supply", "supply", ["structural"]),
    "recycling_supply": ("Recycled gold supply", "supply", ["structural", "india"]),
    # India-specific
    "usd_inr": ("USD/INR exchange rate", "currency", ["currency", "india"]),
    "inr_depreciation": ("INR depreciation trend", "currency", ["currency", "india"]),
    "india_cpi_yoy": ("India CPI inflation", "macro", ["india", "macro"]),
    "rbi_policy": ("RBI policy stance", "macro", ["india", "rates"]),
    "import_duty": ("Gold import duty", "policy", ["india", "policy", "duty"]),
    "domestic_premium": ("Domestic premium/discount", "price", ["india", "price"]),
    "smuggling_incentive": ("Smuggling incentive", "flow", ["india", "policy", "duty"]),
    "festival_season": ("Festival/wedding season", "demand", ["india", "seasonal"]),
    "local_demand": ("Domestic jewellery demand", "demand", ["india", "seasonal"]),
    "rural_income": ("Rural income / monsoon", "demand", ["india", "seasonal"]),
    "sgb_availability": ("Sovereign gold bond availability", "policy", ["india", "policy", "sgb"]),
    "investment_demand_india": ("Indian investment demand", "demand", ["india", "flows"]),
    # household decision nodes
    "gold_allocation_case": ("Case for gold in a household portfolio", "decision",
                             ["allocation", "india"]),
    "gold_timing_risk": ("Near-term gold timing risk", "decision", ["allocation", "price"]),
    "inflation_hedge_value": ("Gold as inflation hedge", "decision", ["allocation", "macro"]),
    "crisis_hedge_value": ("Gold as crisis hedge", "decision", ["allocation", "crisis"]),
    # asset-class reference nodes (household instruments). Each node emits ONLY its
    # class tag — never the shared "instrument" tag the docs carry — so an FD query
    # allows just FD chunks, keeping classes from leaking into each other. The docs
    # deliberately carry no "india" tag either, so instrument answers never pull in
    # gold-driver docs.
    "ac_overview": ("Household asset-class map", "reference", ["overview"]),
    "ac_cash": ("Cash and liquid holdings", "reference", ["cash"]),
    "ac_fd": ("Fixed and recurring deposits", "reference", ["fd"]),
    "ac_bonds": ("Bonds and debt funds", "reference", ["bonds"]),
    "ac_smallsavings": ("Small-savings schemes (PPF/EPF/NPS)", "reference", ["smallsavings"]),
    "ac_equity": ("Equity / shares", "reference", ["equity"]),
    "ac_index": ("Index funds and ETFs", "reference", ["index"]),
    "ac_commodities": ("Commodities beyond gold", "reference", ["commodities"]),
    "ac_realestate": ("Real estate and REITs", "reference", ["realestate"]),
    "ac_gold_class": ("Gold as an asset class", "reference", ["gold"]),
}

#: (src, dst, sign, strength, note)
EDGES: list[tuple[str, str, int, str, str]] = [
    ("us_real_yield_10y", "gold_usd", -1, "strong",
     "Higher real yields raise gold's opportunity cost; the dominant 2022 driver"),
    ("us_nominal_yield", "us_real_yield_10y", +1, "strong", "Real = nominal − inflation exp."),
    ("us_inflation_exp", "us_real_yield_10y", -1, "strong", "Real = nominal − inflation exp."),
    ("fed_policy", "us_nominal_yield", +1, "strong", "Hiking cycles lift nominal yields"),
    ("fed_policy", "usd_index", +1, "medium", "Tightening attracts dollar flows"),
    ("usd_index", "gold_usd", -1, "strong",
     "Gold is dollar-denominated; a stronger dollar pressures USD gold"),
    ("real_rates_regime", "gold_usd", -1, "strong", "Structural version of the yield link"),
    ("risk_sentiment", "gold_usd", -1, "medium",
     "Risk-off episodes bid gold; risk-on drains the hedge premium"),
    ("geopolitical_risk", "gold_usd", +1, "medium", "2020 and 2022 safe-haven bids"),
    ("geopolitical_risk", "central_bank_buying", +1, "medium",
     "Reserve diversification accelerated after 2022 sanctions"),
    ("central_bank_buying", "gold_usd", +1, "strong",
     "Record official-sector buying underpinned 2022–24 prices"),
    ("etf_flows", "gold_usd", +1, "medium", "Investment flows amplify trends"),
    ("mine_supply", "gold_usd", -1, "weak", "Supply is inelastic; weak short-run effect"),
    ("gold_usd", "gold_inr", +1, "strong", "INR price = USD price × fx × (1+duty)"),
    ("usd_inr", "gold_inr", +1, "strong", "Rupee depreciation raises INR gold directly"),
    ("inr_depreciation", "usd_inr", +1, "strong", "Trend node for the fx level"),
    ("india_cpi_yoy", "inr_depreciation", +1, "medium", "Inflation differentials drive fx"),
    ("rbi_policy", "usd_inr", -1, "medium", "Tight RBI policy supports the rupee"),
    ("import_duty", "gold_inr", +1, "strong", "Duty is a direct price wedge (2013 hikes)"),
    ("import_duty", "smuggling_incentive", +1, "strong", "High duty widens grey-market margin"),
    ("smuggling_incentive", "domestic_premium", -1, "medium",
     "Grey supply compresses official premia"),
    ("import_duty", "domestic_premium", +1, "medium", "Duty props up local premia"),
    ("festival_season", "local_demand", +1, "strong", "Diwali/wedding season demand"),
    ("rural_income", "local_demand", +1, "strong", "Monsoon-linked rural gold buying"),
    ("local_demand", "domestic_premium", +1, "medium", "Seasonal demand lifts local premia"),
    ("local_demand", "gold_inr", +1, "weak", "India is a price-taker; effect shows in premia"),
    ("recycling_supply", "domestic_premium", -1, "weak", "Old-gold selling absorbs demand"),
    ("india_cpi_yoy", "inflation_hedge_value", +1, "medium",
     "Households hedge sustained inflation with gold"),
    ("sgb_availability", "investment_demand_india", +1, "weak",
     "Paper-gold routes redirect physical demand"),
    ("investment_demand_india", "local_demand", +1, "medium", "Investment adds to jewellery"),
    ("gold_usd", "gold_timing_risk", +1, "medium",
     "Elevated spot after a run-up raises entry-timing risk"),
    ("domestic_premium", "gold_timing_risk", +1, "medium",
     "Paying festival premium worsens entry price"),
    ("inflation_hedge_value", "gold_allocation_case", +1, "medium",
     "Hedge value supports allocation"),
    ("crisis_hedge_value", "gold_allocation_case", +1, "medium",
     "Crisis value supports allocation"),
    ("risk_sentiment", "crisis_hedge_value", -1, "medium", "Hedge value rises when risk is off"),
    ("gold_timing_risk", "gold_allocation_case", -1, "medium",
     "Timing risk argues for staggered entry, not absence"),
    # asset-class map: each class informs the overview, so a "where do I spread my
    # money" query (seeded at ac_overview) expands to every class; class-specific
    # queries stay narrow because these nodes have no predecessors of their own.
    ("ac_cash", "ac_overview", +1, "medium", "Safety base of the map"),
    ("ac_fd", "ac_overview", +1, "medium", "Fixed-return slice"),
    ("ac_bonds", "ac_overview", +1, "medium", "Income-and-stability slice"),
    ("ac_smallsavings", "ac_overview", +1, "medium", "Tax-efficient long-term slice"),
    ("ac_equity", "ac_overview", +1, "strong", "Growth engine"),
    ("ac_index", "ac_overview", +1, "strong", "Low-cost equity exposure"),
    ("ac_commodities", "ac_overview", +1, "weak", "Specialist diversifier"),
    ("ac_realestate", "ac_overview", +1, "medium", "Illiquid growth/consumption slice"),
    ("ac_gold_class", "ac_overview", +1, "medium", "Hedge slice"),
]


@lru_cache(maxsize=1)
def build_graph() -> nx.DiGraph:
    g = nx.DiGraph()
    for node_id, (label, kind, tags) in DRIVERS.items():
        g.add_node(node_id, label=label, kind=kind, doc_tags=tuple(tags))
    for src, dst, sign, strength, note in EDGES:
        g.add_edge(src, dst, sign=sign, strength=strength, note=note)
    return g


#: keyword -> node ids, for query routing (lowercase substring match)
_KEYWORDS: dict[str, list[str]] = {
    "expensive": ["gold_usd", "gold_inr", "gold_timing_risk", "domestic_premium"],
    "price": ["gold_usd", "gold_inr", "domestic_premium"],
    "why": [],
    "duty": ["import_duty", "smuggling_incentive", "domestic_premium"],
    "import": ["import_duty"],
    "rupee": ["usd_inr", "inr_depreciation"],
    "inr": ["usd_inr", "inr_depreciation", "gold_inr"],
    "dollar": ["usd_index"],
    "yield": ["us_real_yield_10y", "us_nominal_yield"],
    "rate": ["us_real_yield_10y", "fed_policy", "rbi_policy"],
    "fed": ["fed_policy"],
    "inflation": ["india_cpi_yoy", "us_inflation_exp", "inflation_hedge_value"],
    "diwali": ["festival_season", "local_demand", "domestic_premium"],
    "festival": ["festival_season", "local_demand"],
    "wedding": ["festival_season", "local_demand"],
    "season": ["festival_season", "local_demand"],
    "premium": ["domestic_premium"],
    "central bank": ["central_bank_buying"],
    "etf": ["etf_flows", "ac_index"],
    "sgb": ["sgb_availability"],
    "bond": ["sgb_availability", "ac_bonds"],
    "hedge": ["inflation_hedge_value", "crisis_hedge_value"],
    "crisis": ["crisis_hedge_value", "geopolitical_risk", "risk_sentiment"],
    "war": ["geopolitical_risk"],
    "buy": ["gold_allocation_case", "gold_timing_risk"],
    "invest": ["gold_allocation_case"],
    "allocation": ["gold_allocation_case"],
    "timing": ["gold_timing_risk"],
    "now": ["gold_timing_risk"],
    # asset-class routing (household instruments)
    "asset class": ["ac_overview"],
    "spread my money": ["ac_overview"],
    "where to invest": ["ac_overview"],
    "diversif": ["ac_overview"],
    "portfolio": ["ac_overview"],
    "liquid": ["ac_cash"],
    "savings account": ["ac_cash"],
    "fixed deposit": ["ac_fd"],
    "fd": ["ac_fd"],
    "recurring deposit": ["ac_fd"],
    "debt fund": ["ac_bonds"],
    "g-sec": ["ac_bonds"],
    "small saving": ["ac_smallsavings"],
    "ppf": ["ac_smallsavings"],
    "epf": ["ac_smallsavings"],
    "provident": ["ac_smallsavings"],
    "nps": ["ac_smallsavings"],
    "sukanya": ["ac_smallsavings"],
    "equity": ["ac_equity"],
    "share market": ["ac_equity"],
    "shares": ["ac_equity"],
    "stock market": ["ac_equity"],
    "stock": ["ac_equity"],
    "index fund": ["ac_index"],
    "index": ["ac_index"],
    "nifty": ["ac_index"],
    "sensex": ["ac_index"],
    "mutual fund": ["ac_index", "ac_equity"],
    "sip": ["ac_index"],
    "commodit": ["ac_commodities"],
    "silver": ["ac_commodities"],
    "real estate": ["ac_realestate"],
    "property": ["ac_realestate"],
    "reit": ["ac_realestate"],
    "how much gold": ["ac_gold_class"],
    "gold play": ["ac_gold_class"],
    "role of gold": ["ac_gold_class"],
}

_DEFAULT_NODES = ["gold_usd", "gold_inr", "gold_allocation_case"]


def related_drivers(query: str, hops: int = 1) -> list[str]:
    """Map a natural-language query to graph nodes, expanded by n-hop neighbours.

    Deterministic: seed nodes from keyword table (query order), then BFS
    predecessors (causes) up to `hops`, preserving first-seen order.
    """
    q = query.lower()
    seeds: list[str] = []
    for kw, nodes in _KEYWORDS.items():
        if kw in q:
            for n in nodes:
                if n not in seeds:
                    seeds.append(n)
    if not seeds:
        seeds = list(_DEFAULT_NODES)

    g = build_graph()
    result = list(seeds)
    frontier = list(seeds)
    for _ in range(hops):
        nxt: list[str] = []
        for node in frontier:
            for pred in sorted(g.predecessors(node)):
                if pred not in result:
                    result.append(pred)
                    nxt.append(pred)
        frontier = nxt
    return result


def doc_tags_for(nodes: list[str]) -> set[str]:
    g = build_graph()
    tags: set[str] = set()
    for n in nodes:
        if n in g:
            tags.update(g.nodes[n]["doc_tags"])
    return tags


def explain_edges(nodes: list[str]) -> list[dict]:
    """Edges among the given nodes — the causal skeleton shown to the LLM/user."""
    g = build_graph()
    node_set = set(nodes)
    out = []
    for src, dst, data in g.edges(data=True):
        if src in node_set and dst in node_set:
            out.append({
                "from": src, "to": dst,
                "sign": "+" if data["sign"] > 0 else "−",
                "strength": data["strength"], "note": data["note"],
            })
    return out
