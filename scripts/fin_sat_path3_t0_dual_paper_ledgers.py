#!/usr/bin/env python3
"""P3_T0_STATE dual-paper ledgers — OPERATING OBSERVE (paper only).

CTRL_LIVE_A10 ∥ P3_T0_STATE (same-day SAT_LEAD → SAT else COMP).
Requires Exact T+0 carve-out T0_CARVE_FIN_SAT_SWITCH.
Soft-Frozen clips KEEP · COMPOSITE+SAT_RELAX observes KEEP · cutover BLOCKED · no live.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sat_path3_t0_observe_helpers import (
    BASE_ID,
    CARVE_OUT_ID,
    CHAL_ID,
    HUMAN_ACCEPT,
    HUMAN_RETUNE_THETA,
    STAGE_A_VERDICT,
    STATUS,
    THETA,
    THETA_PRIOR,
)
from fin_sell_quality_helpers import cagr_lift_pp
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-sat-path3-t0-dual-paper-observe"
OPS = ROOT / "research/ops"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)[["date", "nav"]].assign(
        nav=lambda x: x["nav"].astype(float)
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
            out[wname] = {"mdd_improve_pp": None, "cagr_lift_pp": None}
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
            "cagr_lift_pp": None if cagr_lift_pp(bc, cc) is None else round(float(cagr_lift_pp(bc, cc)), 4),
        }
    return out


def _trail(r: pd.Series, n: int) -> pd.Series:
    return (1.0 + r).rolling(n, min_periods=n).apply(lambda x: float(np.prod(x) - 1.0), raw=True)


def build_p3_nav(comp: pd.DataFrame, sat: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    rc = m["nav_c"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    rel = rc - rs
    trail = _trail(rel, 63)
    sat_lead = (trail <= -THETA).fillna(False).astype(bool)
    w = sat_lead.astype(float).to_numpy()
    r = (1.0 - w) * rc.to_numpy() + w * rs.to_numpy()
    nav = (1.0 + r).cumprod() * float(m["nav_c"].iloc[0])
    chal = pd.DataFrame({"date": m["date"].to_numpy(), "nav": nav})
    sig = pd.DataFrame(
        {
            "date": m["date"].to_numpy(),
            "trail_rel_63": trail.to_numpy(),
            "sat_lead": sat_lead.to_numpy(),
            "w_sat": w,
        }
    )
    return chal, sig


def main() -> int:
    out = OUT / "outputs"
    rep = OUT / "reports"
    for d in (out, rep, OPS):
        d.mkdir(parents=True, exist_ok=True)

    live = _load(LIVE_NAV)
    comp = _load(COMP_NAV)
    sat = _load(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat = sat[sat["date"].isin(dates)].reset_index(drop=True)

    chal, sig = build_p3_nav(comp, sat)
    live.to_csv(out / "ctrl_live_a10_daily_nav.csv", index=False)
    chal.to_csv(out / "p3_t0_state_daily_nav.csv", index=False)
    sig.to_csv(out / "p3_t0_state_signal.csv", index=False)
    compare = live.rename(columns={"nav": "nav_live"}).merge(
        chal.rename(columns={"nav": "nav_p3"}), on="date"
    )
    compare.to_csv(out / "dual_paper_nav_compare.csv", index=False)

    base_w = pack_windows(live)
    chal_w = pack_windows(chal)
    tip = tip_windows(live, chal)
    held_cagr = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (chal_w.get("heldout_2019_plus") or {}).get("cagr"),
    )
    held_mdd = mdd_delta_pp(
        (base_w.get("heldout_2019_plus") or {}).get("max_drawdown"),
        (chal_w.get("heldout_2019_plus") or {}).get("max_drawdown"),
    )
    generated = _utc()
    payload = {
        "label": f"FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "status": STATUS,
        "human_accept": HUMAN_ACCEPT,
        "carve_out_id": CARVE_OUT_ID,
        "exact_t0_carve_out": True,
        "exact_t_plus_1_global_keep": True,
        "soft_frozen_clips_keep": True,
        "live_wire": False,
        "cutover": "BLOCKED",
        "books": [BASE_ID, CHAL_ID],
        "stage_a_verdict": STAGE_A_VERDICT,
        "theta": THETA,
        "theta_prior": THETA_PRIOR,
        "human_retune_theta": HUMAN_RETUNE_THETA,
        "live_t0_fill": True,
        "live_t0_emit": True,
        "pct_days_sat": round(float(sig["w_sat"].mean()) * 100, 2),
        "windows": {"base": base_w, "chal": chal_w},
        "heldout_delta": {
            "cagr_lift_pp": None if held_cagr is None else round(float(held_cagr), 4),
            "mdd_improve_pp": None if held_mdd is None else round(float(held_mdd), 4),
        },
        "tip": tip,
        "parents_keep": ["COMP_H150_x_A20_OBSERVE", "SAT_A20_RELAX_OBSERVE"],
        "register": "0ka7",
    }

    op_md = "\n".join(
        [
            f"# {CHAL_ID} dual-paper observe — OPERATING",
            "",
            f"- human_accept: `{HUMAN_ACCEPT}`",
            f"- human_retune: `{HUMAN_RETUNE_THETA}` · θ **{THETA}** (prior {THETA_PRIOR})",
            f"- status: **{STATUS}** · live T+0 fill/emit **ON** · broker write **false** · cutover: **BLOCKED** · Soft-Frozen clips KEEP",
            f"- carve-out: **`{CARVE_OUT_ID}`** (Exact T+0 for COMP↔SAT switch only) · global Exact T+1 KEEP elsewhere",
            f"- books: `{BASE_ID}` ∥ `{CHAL_ID}` (same-day SAT_LEAD→SAT else COMP · θ={THETA})",
            f"- Stage A parent: `{STAGE_A_VERDICT}` · COMPOSITE+SAT_RELAX observes **KEEP**",
            f"- held-out: CAGR↑ {payload['heldout_delta']['cagr_lift_pp']} pp · MDD↑ {payload['heldout_delta']['mdd_improve_pp']} pp",
            f"- tip ytd CAGR↑ {(tip.get('ytd') or {}).get('cagr_lift_pp')} · tip 1y CAGR↑ {(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}",
            f"- % days SAT: {payload['pct_days_sat']}",
            "",
            "## Non-actions",
            "",
            "- Soft-Frozen clips KEEP",
            "- Do not expand T+0 carve-out to other mechanisms",
            "- Do not wire live / flip CONF α from this observe",
            "- Cutover BLOCKED until dedicated ACCEPT",
            "",
            f"Repro: `repro/fin-sat-path3-t0-dual-paper-observe/`",
            "",
            f"Label: `FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_OPERATING_2026-09-28__OPEN__NO_LIVE`",
            "",
        ]
    )

    for stem, body in (
        ("FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_OPERATING.md", op_md),
        (
            "FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_OPERATING.json",
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        ),
        (
            "FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE.json",
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        ),
    ):
        (OPS / stem).write_text(body if isinstance(body, str) else body, encoding="utf-8")
        (rep / stem).write_text(
            (OPS / stem).read_text(encoding="utf-8")
            if stem.endswith(".md")
            else json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if stem.endswith(".md"):
            (rep / stem).write_text(
                "Canonical copy: `research/ops/"
                + stem
                + "`\n\n"
                + op_md,
                encoding="utf-8",
            )

    open_md = "\n".join(
        [
            f"# {CHAL_ID} dual-paper observe — OPEN",
            "",
            f"Status: **OPEN / OPERATING** · carve-out `{CARVE_OUT_ID}` · cutover **BLOCKED** · no live",
            f"Human: `{HUMAN_ACCEPT}`",
            "",
            f"See `FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_OPERATING.md`.",
            "",
        ]
    )
    (OPS / "FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_OPEN.md").write_text(open_md, encoding="utf-8")
    (rep / "FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_OPEN.md").write_text(open_md, encoding="utf-8")

    print(json.dumps({"status": STATUS, "held": payload["heldout_delta"], "tip": tip}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
