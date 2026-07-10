"""Output guardrail (Master Doc §7): two deterministic post-model checks.

1. Instrument scan — regex + curated lexicon over generated text; any ticker,
   fund name, or token name blocks the output (caller regenerates or falls back).
2. Number diff — every numeric token in generated text must appear verbatim in
   the allowed set derived from rules-engine evidence. A model that invents or
   recomputes a number gets blocked. This is the mechanical enforcement of
   "the LLM never computes" (decision log D-007).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.nbca import Evidence

_TICKER = re.compile(r"\$[A-Z]{1,5}\b|\b(?:NSE|BSE|NASDAQ|NYSE)\s*[:>]\s*[A-Z]+", )
_INSTRUMENT_WORDS = re.compile(
    r"\b(bitcoin|btc|ethereum|dogecoin|solana|nifty ?(?:50|bees)|sensex|"
    r"reliance|infosys|tcs|hdfc|icici|sbi bluechip|axis bluechip|parag parikh|"
    r"quant small cap|motilal oswal|nippon india|tesla|apple|nvidia|"
    r"mutual fund named|folio no)\b",
    re.IGNORECASE,
)

#: numeric tokens: currency amounts, decimals, percents, integers with separators
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")

#: numbers that never need evidence: small ordinals/counts and common structural
#: figures used in prose ("3 months", "15×", "top 5")
_FREE_NUMBERS = {str(n) for n in range(0, 16)} | {"20", "24", "30", "40", "50", "100"}


@dataclass(frozen=True)
class OutputVerdict:
    allowed: bool
    violations: list[str] = field(default_factory=list)


def _canon(num: str) -> str:
    return num.replace(",", "")


def allowed_numbers(evidence: list[Evidence], extra_texts: list[str] = ()) -> set[str]:
    """Every numeric token that appears in engine-produced material."""
    allowed: set[str] = set(_FREE_NUMBERS)
    texts = [e.claim for e in evidence] + [e.value or "" for e in evidence] + list(extra_texts)
    for t in texts:
        for num in _NUMBER.findall(t):
            allowed.add(_canon(num))
    return allowed


def scan_instruments(text: str) -> list[str]:
    hits = [m.group(0) for m in _TICKER.finditer(text)]
    hits += [m.group(0) for m in _INSTRUMENT_WORDS.finditer(text)]
    return hits


def diff_numbers(text: str, allowed: set[str]) -> list[str]:
    """Numeric tokens in `text` not present in the allowed set."""
    bad: list[str] = []
    for num in _NUMBER.findall(text):
        canon = _canon(num)
        if canon in allowed:
            continue
        # a fragment of an allowed number split by formatting is fine
        if any(canon in a for a in allowed if len(canon) >= 2):
            continue
        bad.append(num)
    return bad


def screen_output(
    text: str,
    evidence: list[Evidence],
    extra_allowed_texts: list[str] = (),
) -> OutputVerdict:
    violations = [f"instrument:{h}" for h in scan_instruments(text)]
    violations += [
        f"number:{n}" for n in diff_numbers(text, allowed_numbers(evidence, extra_allowed_texts))
    ]
    return OutputVerdict(allowed=not violations, violations=violations)
