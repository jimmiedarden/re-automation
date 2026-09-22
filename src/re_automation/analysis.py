"""Deal math: maximum allowable offer (MAO) and a simple offer verdict."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_MAO_PERCENT = 0.65
# Asking prices up to this much above MAO are still worth a counter-offer.
NEGOTIATE_MARGIN = 0.10


def mao(arv: float, rehab: float, pct: float = DEFAULT_MAO_PERCENT) -> float:
    """Maximum allowable offer: ARV x pct - rehab, never below zero."""
    if arv < 0 or rehab < 0:
        raise ValueError("ARV and rehab must be non-negative")
    if not 0 < pct <= 1:
        raise ValueError("pct must be between 0 and 1")
    return max(round(arv * pct - rehab, 2), 0.0)


@dataclass(frozen=True)
class DealAnalysis:
    arv: float
    rehab: float
    asking: float | None
    mao: float

    @property
    def spread(self) -> float | None:
        """MAO minus asking price; positive means the deal fits the formula."""
        if self.asking is None:
            return None
        return round(self.mao - self.asking, 2)

    @property
    def verdict(self) -> str:
        """'offer', 'negotiate', 'pass', or 'no-asking' when price is unknown."""
        if self.asking is None:
            return "no-asking"
        if self.mao <= 0:
            return "pass"
        if self.asking <= self.mao:
            return "offer"
        if self.asking <= self.mao * (1 + NEGOTIATE_MARGIN):
            return "negotiate"
        return "pass"


def analyze(
    arv: float,
    rehab: float,
    asking: float | None = None,
    pct: float = DEFAULT_MAO_PERCENT,
) -> DealAnalysis:
    return DealAnalysis(arv=arv, rehab=rehab, asking=asking, mao=mao(arv, rehab, pct))
