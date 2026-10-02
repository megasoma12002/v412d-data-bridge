#!/usr/bin/env python3
"""TIPSOFT_P3_TRAIL42_L4_DD_SWITCH dual-paper ledgers refresh (observe KEEP).

Rebases L4 ∥ DD_SWITCH NAV to a common 1.0 start for month-end compare.
Does not re-simulate Stage A; copies sealed observe NAV SSOT.
Soft FIN/TEL OFF · Path4 OFF · broker false · year-switch FORBIDDEN.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/tipsoft-ip3-trail42-l4-switch-paper-observe/outputs"
REP = ROOT / "repro/tipsoft-ip3-trail42-l4-switch-paper-observe/reports"
OPS = ROOT / "research/ops"
STAGEA = ROOT / "repro/tipsoft-ip3-trail42-l4-signal-switch-stagea/outputs"

BASE_ID = "L4_LIVE_P3_WITHIN"
CHAL_ID = "TRAIL42_L4_DD_SWITCH"
OPERATING_ID = "TIPSOFT_IP3_TRAIL42_L4_SWITCH_DUAL_PAPER_OBSERVE_OPERATING"
STATUS = "OPERATING_OBSERVE"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return (
        df[["date", "nav"]]
        .assign(nav=lambda x: x["nav"].astype(float))
        .sort_values("date")
        .reset_index(drop=True)
    )


def pack_windows(nav: pd.DataFrame) -> dict:
    out = {}
    for k, (a, b) in WINDOWS_STANDARD.items():
        st = window_stats(nav, a, b)
        out[k] = {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None
            if st.get("max_drawdown") is None
            else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
    return out


def tip_windows(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {
                "mdd_improve_pp": None,
                "cagr_lift_pp": None,
                "gate": "INSUFFICIENT",
            }
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_lift_pp": None
            if cagr_lift_pp(bc, cc) is None
            else round(float(cagr_lift_pp(bc, cc)), 4),
            "gate": "PASS",
        }
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)

    base_path = OUT / f"nav_{BASE_ID}.csv"
    chal_path = OUT / f"nav_{CHAL_ID}.csv"
    if not base_path.exists():
        alt = STAGEA / "nav_REF_L4.csv"
        if alt.exists():
            base_path = alt
    if not chal_path.exists():
        alt = STAGEA / "nav_TRAIL_WHEN_TR_DD_GTE_L4.csv"
        if alt.exists():
            chal_path = alt
    if not base_path.exists() or not chal_path.exists():
        raise SystemExit(
            f"missing DD_SWITCH observe NAV ({base_path} / {chal_path}); "
            "run tipsoft_ip3_trail42_l4_switch_observe_open_execute.py first"
        )

    base = _load_nav(base_path)
    chal = _load_nav(chal_path)
    # Persist canonical copies under observe outputs.
    base.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    chal.to_csv(OUT / f"nav_{CHAL_ID}.csv", index=False)

    # Common-scale compare for month-end (rebase after inner-join so tip starts at 1.0).
    merged = (
        pd.merge(
            base.rename(columns={"nav": "nav_base"})[["date", "nav_base"]],
            chal.rename(columns={"nav": "nav_chal"})[["date", "nav_chal"]],
            on="date",
            how="inner",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )
    merged["nav_base"] = merged["nav_base"] / float(merged["nav_base"].iloc[0])
    merged["nav_chal"] = merged["nav_chal"] / float(merged["nav_chal"].iloc[0])
    merged.to_csv(OUT / "dual_paper_nav_compare.csv", index=False)

    bw = pack_windows(base)
    cw = pack_windows(chal)
    held_b = bw["heldout_2019_plus"]
    held_c = cw["heldout_2019_plus"]
    sealed_b = bw["sealed_2023_plus"]
    sealed_c = cw["sealed_2023_plus"]
    tip = tip_windows(base, chal)

    operating = {
        "generated_at_utc": _utc(),
        "label": OPERATING_ID,
        "status": STATUS,
        "register": "0kbd",
        "stabilize_parent": "0kbe",
        "live_wire": True,
        "cutover_authorized": False,
        "apply_authorized": True,
        "wire_mode": "path3_gate_ft_cash_apply",
        "soft_frozen_keep": True,
        "soft_fin_tel": "OFF",
        "path4_live": False,
        "broker": False,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "policy_id": "TIPSOFT_P3_TRAIL42_L4_DD_SWITCH",
        "signal": "TRAIL_WHEN_TR_DD_GTE_L4",
        "base_windows": bw,
        "chal_windows": cw,
        "heldout_delta": {
            "cagr_lift_pp": None
            if held_b["cagr"] is None or held_c["cagr"] is None
            else round(float(cagr_lift_pp(held_b["cagr"], held_c["cagr"])), 4),
            "mdd_improve_pp": None
            if held_b["max_drawdown"] is None or held_c["max_drawdown"] is None
            else round(
                float(mdd_delta_pp(held_b["max_drawdown"], held_c["max_drawdown"])),
                4,
            ),
        },
        "sealed_delta": {
            "cagr_lift_pp": None
            if sealed_b["cagr"] is None or sealed_c["cagr"] is None
            else round(float(cagr_lift_pp(sealed_b["cagr"], sealed_c["cagr"])), 4),
            "mdd_improve_pp": None
            if sealed_b["max_drawdown"] is None or sealed_c["max_drawdown"] is None
            else round(
                float(
                    mdd_delta_pp(sealed_b["max_drawdown"], sealed_c["max_drawdown"])
                ),
                4,
            ),
        },
        "tip": tip,
        "non_actions": [
            "Soft-Frozen KEEP",
            "Soft FIN/TEL Exact T+1 stay OFF",
            "Path4 live OFF",
            "Calendar-year switch / year-oracle FORBIDDEN",
            "broker false",
            "Tip apply LIVE WIRED KEEP (stabilize 0kbe)",
        ],
    }
    (OUT / "dual_paper_operating.json").write_text(
        json.dumps(operating, indent=2) + "\n", encoding="utf-8"
    )

    md = "\n".join(
        [
            f"# {OPERATING_ID} — ledger refresh",
            "",
            f"- status: **{STATUS}** · live tip apply **KEEP** · wire `path3_gate_ft_cash_apply`",
            f"- books: `{BASE_ID}` ∥ `{CHAL_ID}`",
            f"- held-out: CAGR↑ {operating['heldout_delta']['cagr_lift_pp']} pp · "
            f"MDD↑ {operating['heldout_delta']['mdd_improve_pp']} pp",
            f"- sealed: CAGR↑ {operating['sealed_delta']['cagr_lift_pp']} pp · "
            f"MDD↑ {operating['sealed_delta']['mdd_improve_pp']} pp",
            f"- tip ytd CAGR↑ {tip.get('ytd', {}).get('cagr_lift_pp')} · "
            f"tip 1y CAGR↑ {tip.get('trailing_1y', {}).get('cagr_lift_pp')}",
            "",
            "Soft FIN/TEL OFF · Path4 OFF · broker false · year-switch FORBIDDEN",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{OPERATING_ID}.md",
        REP / f"{OPERATING_ID}.md",
        md,
    )
    write_ops_and_repro_pointer(
        OPS / f"{OPERATING_ID}.json",
        REP / f"{OPERATING_ID}.json",
        json.dumps(operating, indent=2) + "\n",
    )
    print(f"OK {OPERATING_ID} n_compare={len(merged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
