"""Input guardrail: specific-instrument requests are refused and reframed
(Master Doc §7). Deterministic regex screening — runs before any model call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Phrasings that ask for instrument-level picks.
_INSTRUMENT_PATTERNS: list[re.Pattern[str]] = [re.compile(p, re.IGNORECASE) for p in [
    r"\bwhich (?:\w+ ){0,2}"
    r"(stock|share|scrip|fund|mutual fund|etf|scheme|coin|crypto|token|ipo)s?\b",
    r"\bwhat (stock|share|fund|etf|coin|crypto)s? (should|do|can|to)\b",
    r"\b(best|top|good) (?:\d+ )?"
    r"(stock|share|fund|mutual fund|etf|scheme|coin|crypto|token|ipo)s?\b",
    r"\b(recommend|suggest|name|pick|tip)\w* .{0,40}"
    r"\b(stock|share|fund|etf|scheme|coin|crypto|token)s?\b",
    r"\b(stock|share|crypto|coin) (tip|pick|recommendation)s?\b",
    r"\bshould i buy .{0,30}\b(stock|share|coin|token|ipo)s?\b",
    r"\bmultibagger\b",
    r"\bguarantee[ds]? .{0,20}(return|profit)s?\b",
    r"\b(double|triple) my money\b",
]]

#: Known instrument names/tickers that signal an instrument-level ask.
_INSTRUMENT_LEXICON = re.compile(
    r"\b(nifty ?50|sensex|bitcoin|btc|ethereum|eth|dogecoin|tsla|tesla stock|reliance shares?|"
    r"tata motors|infosys|hdfc bank|adani|zomato|paytm)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InputVerdict:
    allowed: bool
    reason: str | None = None


REFUSAL_TEXT = (
    "NextRupee doesn't recommend specific stocks, funds, or coins — that line is where "
    "decision support ends and regulated investment advice begins. What it can show you "
    "is whether this rupee amount belongs in equity, fixed income, or gold at all, given "
    "your situation — and why. Try asking that version of the question."
)


def screen_input(text: str) -> InputVerdict:
    for pattern in _INSTRUMENT_PATTERNS:
        if pattern.search(text):
            return InputVerdict(allowed=False, reason=f"instrument_request:{pattern.pattern[:40]}")
    if _INSTRUMENT_LEXICON.search(text):
        return InputVerdict(allowed=False, reason="instrument_lexicon")
    return InputVerdict(allowed=True)
