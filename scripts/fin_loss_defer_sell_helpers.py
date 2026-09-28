#!/usr/bin/env python3
"""Paper-only FIN/TEL loss-defer sell policy (Stage A).

FIFO all-in lot ledger + sell-eligibility overlay. Soft-Frozen / live tip untouched.
COOL exposure < 1 → never defer (unless cool_gate=False negative control).
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LossDeferPolicy:
    """Mutable path-dependent sell gate for ``simulate_core``."""

    universe: set[str]
    max_wait: int = 10
    loss_band: float = 0.0  # defer if pnl_pct <= loss_band (0 => any loss; -0.02 => ≤−2%)
    cool_gate: bool = True
    worst_first: bool = False
    lots: dict[str, deque] = field(default_factory=lambda: defaultdict(deque))
    wait: dict[str, int] = field(default_factory=dict)
    deferred_sells: int = 0
    forced_sells: int = 0
    cool_gate_violations: int = 0  # deferred while cool<1 (only if cool_gate False)

    def on_fill(self, *, code: str, side: str, qty: int, fill_price: float, fees_tax: float) -> None:
        c = str(code)
        if c not in self.universe:
            return
        q = int(qty)
        if q < 1:
            return
        side_u = str(side).upper()
        if side_u == "BUY":
            unit = float(fill_price) + float(fees_tax) / float(q)
            self.lots[c].append([q, unit])
            self.wait[c] = 0
            return
        if side_u != "SELL":
            return
        remain = q
        while remain > 0 and self.lots[c]:
            lq, unit = self.lots[c][0]
            take = min(lq, remain)
            lq -= take
            remain -= take
            if lq <= 0:
                self.lots[c].popleft()
            else:
                self.lots[c][0][0] = lq
        if not self.lots[c]:
            self.wait[c] = 0

    def _underwater_pct(self, code: str, mark: float) -> float | None:
        dq = self.lots.get(code)
        if not dq:
            return None
        # FIFO head (next lots that would be sold)
        lq, unit = dq[0]
        if unit <= 0:
            return None
        return (float(mark) - float(unit)) / float(unit)

    def sell_ok_and_scores(
        self,
        *,
        codes: list[str],
        marks: dict[str, float],
        cool_scale: float,
    ) -> tuple[dict[str, bool], dict[str, float] | None]:
        """Return sell_ok map and optional sell_scores (worst-first)."""
        cool_lt1 = float(cool_scale) < 1.0 - 1e-12
        ok: dict[str, bool] = {}
        scores: dict[str, float] = {}
        for c in codes:
            if c not in self.universe:
                ok[c] = True
                continue
            mark = marks.get(c)
            if mark is None:
                ok[c] = True
                continue
            up = self._underwater_pct(c, float(mark))
            if up is None:
                ok[c] = True
                self.wait[c] = 0
                continue
            # up < 0 means loss vs FIFO head
            in_band = up <= float(self.loss_band)
            w = int(self.wait.get(c, 0))
            if cool_lt1 and self.cool_gate:
                ok[c] = True
                self.wait[c] = 0
                self.forced_sells += 1
            elif in_band and w < int(self.max_wait):
                ok[c] = False
                self.wait[c] = w + 1
                self.deferred_sells += 1
                if cool_lt1 and not self.cool_gate:
                    self.cool_gate_violations += 1
            else:
                ok[c] = True
                self.wait[c] = 0
            if self.worst_first:
                # More underwater → higher sell score when allowed
                scores[c] = float(-up)
        return ok, (scores if self.worst_first else None)

    def meta(self) -> dict[str, Any]:
        return {
            "deferred_sells": int(self.deferred_sells),
            "forced_sells_cool": int(self.forced_sells),
            "cool_gate_violations": int(self.cool_gate_violations),
            "max_wait": int(self.max_wait),
            "loss_band": float(self.loss_band),
            "cool_gate": bool(self.cool_gate),
            "worst_first": bool(self.worst_first),
            "universe_n": len(self.universe),
        }
