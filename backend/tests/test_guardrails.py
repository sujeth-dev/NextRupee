"""Guardrail tests: instrument refusals, output scans, number diffing."""

from __future__ import annotations

import pytest

from app.guardrails.input_guard import screen_input
from app.guardrails.output_guard import allowed_numbers, diff_numbers, scan_instruments, screen_output
from app.schemas.nbca import Evidence

BLOCKED_INPUTS = [
    "which stock should I buy with 60000",
    "best mutual fund for 2026",
    "recommend a good ETF please",
    "should I buy bitcoin",
    "give me a stock tip",
    "which crypto will double my money",
    "name a multibagger",
    "guarantee me 20% returns",
    "is Tata Motors a buy?",
    "top funds this year",
]

ALLOWED_INPUTS = [
    "why is gold expensive right now?",
    "should I pay off my credit card or invest?",
    "is buying gold for Diwali a good idea",
    "how much emergency fund do I need",
    "what does import duty do to gold prices",
    "should I put money in equity as an asset class?",
]


class TestInputGuard:
    @pytest.mark.parametrize("text", BLOCKED_INPUTS)
    def test_blocked(self, text):
        assert not screen_input(text).allowed, text

    @pytest.mark.parametrize("text", ALLOWED_INPUTS)
    def test_allowed(self, text):
        assert screen_input(text).allowed, text


class TestInstrumentScan:
    def test_ticker_symbols_caught(self):
        assert scan_instruments("consider $TSLA or NSE: RELIANCE here")

    def test_fund_names_caught(self):
        assert scan_instruments("the Parag Parikh fund is popular")

    def test_clean_asset_class_text_passes(self):
        text = "Shift the surplus toward fixed income and keep gold at 15% of the mix."
        assert scan_instruments(text) == []


class TestNumberDiff:
    EVIDENCE = [
        Evidence(claim="Credit card APR is 42% on ₹1,20,000", source="rules_engine",
                 ref="calc:x", value="₹4,200"),
    ]

    def test_evidence_numbers_allowed(self):
        allowed = allowed_numbers(self.EVIDENCE)
        assert {"42", "120000", "4200"} <= allowed

    def test_invented_number_blocked(self):
        allowed = allowed_numbers(self.EVIDENCE)
        assert diff_numbers("you will save ₹9,999 next year", allowed) == ["9,999"]

    def test_reformatted_evidence_number_allowed(self):
        allowed = allowed_numbers(self.EVIDENCE)
        assert diff_numbers("that is 4200 rupees a month at 42%", allowed) == []

    def test_screen_output_combines_checks(self):
        v = screen_output("buy bitcoin with your ₹7,777", self.EVIDENCE)
        assert not v.allowed
        assert any(x.startswith("instrument:") for x in v.violations)
        assert any(x.startswith("number:") for x in v.violations)

    def test_small_structural_numbers_free(self):
        v = screen_output("three steps: 1, 2 and 3 months of buffer", self.EVIDENCE)
        assert v.allowed
