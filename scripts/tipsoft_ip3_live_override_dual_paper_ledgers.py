#!/usr/bin/env python3
"""TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3 dual-paper ledgers — OPERATING OBSERVE.

BASE_LIVE_FUSE_COOL ∥ OVERRIDE_LIVE_W42_M05_K3 under tip Soft Exact T+1.
0kb1 MUTE_S3_SAT base · force LIVE when lag42 live leads champ by >0.5% for 3d.
Soft KEEP · Path4 OFF · hybrid T+0 carve FORBIDDEN · no live wire · cutover BLOCKED.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from stagea_screen_helpers import (
    utc_now_z as _utc,
    pack_nav_windows as pack_windows,
    tip_lift,
)

def tip_windows(base_nav, chal_nav):
    """Dual-paper tip pack (cagr_lift_pp + gate)."""
    return tip_lift(base_nav, chal_nav, include_gate=True)

from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/tipsoft-ip3-live-override-paper-observe"
OPS = ROOT / "research/ops"
REP = OUT / "reports"

BASE_ID = "BASE_LIVE_FUSE_COOL"
CHAL_ID = "OVERRIDE_LIVE_W42_M05_K3"
HUMAN_OPEN = (
    "OPEN paper observe: TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3 "
    "(tip Soft Exact T+1 · 0kb1 MUTE_S3_SAT base · force LIVE when lag42 "
    "live leads champ by >0.5% for 3d · NOT hybrid T+0)"
)
STATUS = "OPERATING_OBSERVE"
OPERATING_ID = "TIPSOFT_IP3_LIVE_OVERRIDE_DUAL_PAPER_OBSERVE_OPERATING"

def main() -> int:
    for d in (OUT / "outputs", OUT / "reports", OPS):
        d.mkdir(parents=True, exist_ok=True)

    base = pd.read_csv(OUT / "outputs/nav_BASE_LIVE_FUSE_COOL.csv", parse_dates=["date"])
    chal = pd.read_csv(
        OUT / f"outputs/nav_{CHAL_ID}.csv", parse_dates=["date"]
    )
    base = base[["date", "nav"]].assign(nav=lambda x: x["nav"].astype(float))
    chal = chal[["date", "nav"]].assign(nav=lambda x: x["nav"].astype(float))
    base.to_csv(OUT / "outputs/base_live_fuse_cool_daily_nav.csv", index=False)
    chal.to_csv(OUT / "outputs/override_live_w42_m05_k3_daily_nav.csv", index=False)
    cmp = base.merge(chal, on="date", suffixes=("_base", "_chal"))
    cmp.to_csv(OUT / "outputs/dual_paper_nav_compare.csv", index=False)

    bw, cw = pack_windows(base), pack_windows(chal)
    tip = tip_windows(base, chal)
    b_h, c_h = bw["heldout_2019_plus"], cw["heldout_2019_plus"]
    held = {
        "cagr_lift_pp": round(float(cagr_lift_pp(b_h["cagr"], c_h["cagr"])), 4),
        "mdd_improve_pp": round(
            float(mdd_delta_pp(b_h["max_drawdown"], c_h["max_drawdown"])), 4
        ),
    }
    b_s, c_s = bw["sealed_2023_plus"], cw["sealed_2023_plus"]
    sealed = {
        "cagr_lift_pp": round(float(cagr_lift_pp(b_s["cagr"], c_s["cagr"])), 4),
        "mdd_improve_pp": round(
            float(mdd_delta_pp(b_s["max_drawdown"], c_s["max_drawdown"])), 4
        ),
    }

    payload = {
        "generated_at_utc": _utc(),
        "label": OPERATING_ID,
        "status": STATUS,
        "register": "0kb2",
        "human_open": HUMAN_OPEN,
        "live_wire": False,
        "cutover_authorized": False,
        "soft_frozen_keep": True,
        "path4_live": False,
        "hybrid_t0_carve": False,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "policy_id": "TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3",
        "gate": (
            "0kb1 MUTE_S3_SAT; force LIVE when lag42 (live-champ) cumret "
            "> 0.005 for 3 consecutive days"
        ),
        "base_windows": bw,
        "chal_windows": cw,
        "heldout_delta": held,
        "sealed_delta": sealed,
        "tip": tip,
        "non_actions": [
            "Soft-Frozen KEEP",
            "Path4 live OFF",
            "hybrid Soft-core T+0 carve FORBIDDEN",
            "year-cut / lookahead promote FORBIDDEN",
            "Cutover BLOCKED until dedicated ACCEPT",
        ],
    }
    (OUT / "outputs/dual_paper_operating.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    (OPS / f"{OPERATING_ID}.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{OPERATING_ID}.json",
        REP / f"{OPERATING_ID}.json",
        kind="dual-paper operating",
    )

    md = "\n".join(
        [
            "# TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3 dual-paper observe — OPERATING",
            "",
            f"- human_open: `{HUMAN_OPEN}`",
            "- status: **OPERATING_OBSERVE** · live_wire: false · cutover: **BLOCKED** · "
            "Soft KEEP · Path4 OFF · hybrid T+0 carve FORBIDDEN",
            f"- books: `{BASE_ID}` ∥ `{CHAL_ID}` (Exact T+1)",
            "- gate: 0kb1 MUTE_S3_SAT · force LIVE when lag42 live leads champ by "
            ">0.5% for 3d",
            f"- held-out: CAGR↑ {held['cagr_lift_pp']} pp · MDD↑ {held['mdd_improve_pp']} pp",
            f"- sealed: CAGR↑ {sealed['cagr_lift_pp']} pp · MDD↑ {sealed['mdd_improve_pp']} pp",
            f"- tip ytd CAGR↑ {(tip.get('ytd') or {}).get('cagr_lift_pp')} · "
            f"tip 1y CAGR↑ {(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}",
            "",
            "## Non-actions",
            "",
            "- Soft-Frozen KEEP",
            "- Path4 live OFF",
            "- hybrid Soft-core T+0 carve FORBIDDEN",
            "- year-cut / lookahead promote FORBIDDEN",
            "- Cutover BLOCKED until dedicated ACCEPT",
            "",
            "Repro: `repro/tipsoft-ip3-live-override-paper-observe/`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{OPERATING_ID}.md",
        REP / f"{OPERATING_ID}.md",
        md,
        kind="dual-paper operating",
    )
    print(json.dumps({"status": STATUS, "heldout_delta": held, "sealed_delta": sealed, "tip": tip}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
