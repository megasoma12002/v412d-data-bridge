#!/usr/bin/env python3
"""Path3 0050 ETF recon feature cut-gate Stage A (0kaj) — paper only · T+0.

Parent 0kai: ``ADD_FULL_CUT_D05`` HIT but 2024 still ~−4pp. No look-ahead years.
This pack gates **large 0050 cuts** with causal tip-gap / book-tenure features:

- ``prior_book_days`` — completed prior-book run length as of flip day
- tipgap ``*_l1`` — ``r0050_63_l1``, ``trail_drag_l1``, ``zz08_bear_l1``
- deeper SAT enter via same-bar ``trail_rel_63`` (flip definition depth)

Base policy: ADD_FULL_CUT_D05 (full follow on adds; deadband 5pp on cuts).
Cut-gate only fires when a cut would otherwise execute (|Δw|≥5pp & Δw<0).

Soft KEEP · broker false · cutover BLOCKED · no live.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from fin_sat_path3_etf_recon_harden_stagea import (
    ETF,
    SEALED_MDD_FLOOR_PP,
    SOFT_CORE,
    TIP_Y_FLOOR_PP,
    _arm_verdict,
    _book_soft_weights,
    _close_panel,
    _delta_windows,
    _normalize_with_etf,
    _pack,
    _tip,
    yearly_compare,
)
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, load_or_build_signal
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from path3_comp_sat_daily_share_ssot import load_book_shares

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-etf-recon-cutgate-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
TIPGAP_PANEL = ROOT / "repro/fin-sat-tipgap-pred-stagea/outputs/feature_panel.csv"

CHARTER_ID = "FIN_SAT_PATH3_ETF_RECON_CUTGATE_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_ETF_RECON_CUTGATE_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_ETF_RECON_CUTGATE_STAGEA_DECISION_PACK"
REGISTER = "0kaj"

LOSER_YEARS = (2016, 2020, 2023, 2024)
CUT_DEADBAND = 0.05

GateFn = Callable[[pd.Series], bool]  # True => BLOCK the cut


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _attach_prior_book_days(sig: pd.DataFrame) -> pd.DataFrame:
    """Causal prior-book run length on each row (completed before today's book)."""
    s = sig.copy()
    s["date"] = pd.to_datetime(s["date"]).dt.normalize()
    s = s.sort_values("date").reset_index(drop=True)
    books = s["book"].astype(str).to_numpy()
    prior = np.zeros(len(s), dtype=int)
    run = 1
    for i in range(1, len(s)):
        if books[i] == books[i - 1]:
            run += 1
        else:
            # entering a new book: prior tenure = just-finished run length
            prior[i] = run
            run = 1
    s["prior_book_days"] = prior
    return s


def _load_feat(sig: pd.DataFrame) -> pd.DataFrame:
    s = _attach_prior_book_days(sig)
    if not TIPGAP_PANEL.exists():
        raise FileNotFoundError(TIPGAP_PANEL)
    fp = pd.read_csv(TIPGAP_PANEL, parse_dates=["date"])
    fp["date"] = pd.to_datetime(fp["date"]).dt.normalize()
    cols = [
        "date",
        "r0050_63_l1",
        "trail_drag_l1",
        "zz08_bear_l1",
        "trail_rel_63_l1",
        "mdd0050_63_l1",
    ]
    miss = [c for c in cols if c not in fp.columns and c != "date"]
    if miss:
        raise RuntimeError(f"tipgap panel missing {miss}")
    out = s.merge(fp[cols], on="date", how="left")
    return out


def _base_etf_target(prev_e: float, dest_e: float) -> float:
    """ADD_FULL_CUT_D05 target before cut-gate."""
    delta = dest_e - prev_e
    if delta > 0:
        return dest_e
    if abs(delta) < CUT_DEADBAND:
        return prev_e
    return dest_e


GATES: dict[str, GateFn | None] = {
    "KEEP": None,  # special
    "RATIO": None,
    "DEAD_05": None,
    "ADD_FULL_CUT_D05": None,  # parent — no extra gate
    "CG_TENURE_LT5": lambda r: int(r.get("prior_book_days") or 0) < 5,
    "CG_TENURE_LT10": lambda r: int(r.get("prior_book_days") or 0) < 10,
    "CG_R50_POS": lambda r: float(r.get("r0050_63_l1") or 0.0) > 0.0,
    "CG_DRAG_ONLY": lambda r: not bool(int(float(r.get("trail_drag_l1") or 0))),
    "CG_ZZ08_ALLOW": lambda r: not bool(int(float(r.get("zz08_bear_l1") or 0))),
    "CG_DEEP_SAT": lambda r: not (
        str(r.get("book") or "") == BOOK_SAT and float(r.get("trail_rel_63") or 0.0) <= -0.01
    ),
    "CG_TENURE5_R50": lambda r: (
        int(r.get("prior_book_days") or 0) < 5 or float(r.get("r0050_63_l1") or 0.0) > 0.0
    ),
}


def _apply_arm(
    *,
    arm: str,
    gate: GateFn | None,
    feat_row: pd.Series,
    w_prev: np.ndarray,
    w_dest: np.ndarray,
    etf_idx: int,
    fin_tel_idx: list[int],
) -> tuple[np.ndarray, bool, bool]:
    """Returns (w_new, cut_would, cut_blocked)."""
    prev_e = float(w_prev[etf_idx])
    dest_e = float(w_dest[etf_idx])
    delta = dest_e - prev_e

    if arm == "KEEP":
        return (
            _normalize_with_etf(
                w_prev=w_prev,
                w_dest=w_dest,
                etf_idx=etf_idx,
                fin_tel_idx=fin_tel_idx,
                etf_w=prev_e,
            ),
            False,
            False,
        )
    if arm == "RATIO":
        out = w_dest.astype(float).copy()
        s = float(out.sum())
        return (out / s if s > 1e-12 else w_prev.copy()), False, False
    if arm == "DEAD_05":
        etf_w = prev_e if abs(delta) < CUT_DEADBAND else dest_e
        return (
            _normalize_with_etf(
                w_prev=w_prev,
                w_dest=w_dest,
                etf_idx=etf_idx,
                fin_tel_idx=fin_tel_idx,
                etf_w=etf_w,
            ),
            False,
            False,
        )

    # ADD_FULL_CUT_D05 ± cut gate
    etf_w = _base_etf_target(prev_e, dest_e)
    cut_would = bool(delta <= -CUT_DEADBAND)
    cut_blocked = False
    if cut_would and gate is not None and gate(feat_row):
        etf_w = prev_e
        cut_blocked = True
    return (
        _normalize_with_etf(
            w_prev=w_prev,
            w_dest=w_dest,
            etf_idx=etf_idx,
            fin_tel_idx=fin_tel_idx,
            etf_w=etf_w,
        ),
        cut_would,
        cut_blocked,
    )


def simulate_arm(
    *,
    arm: str,
    gate: GateFn | None,
    weights_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    feat: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    dates = feat["date"]
    for wdf in weights_by_book.values():
        dates = dates[dates.isin(wdf.index)]
    dates = dates[dates.isin(px.index)].reset_index(drop=True)
    if len(dates) < 100:
        raise RuntimeError("insufficient overlap")

    feat_i = feat.set_index("date")
    rets = px.pct_change().reindex(dates).fillna(0.0)
    etf_idx = SOFT_CORE.index(ETF)
    fin_tel_idx = [SOFT_CORE.index(c) for c in list(FIN) + list(TEL)]

    row0 = feat_i.loc[dates.iloc[0]]
    if isinstance(row0, pd.DataFrame):
        row0 = row0.iloc[-1]
    book0 = str(row0.get("book") or BOOK_COMP)
    if book0 not in weights_by_book:
        book0 = BOOK_COMP
    w = weights_by_book[book0].loc[dates.iloc[0], SOFT_CORE].to_numpy(dtype=float)
    w = w / w.sum() if w.sum() > 1e-12 else np.ones(len(SOFT_CORE)) / len(SOFT_CORE)

    nav = [1.0]
    n_flip = 0
    n_cut_would = 0
    n_cut_blocked = 0
    etf_turnover = 0.0

    for i in range(1, len(dates)):
        d = dates.iloc[i]
        r = rets.loc[d, SOFT_CORE].to_numpy(dtype=float)
        frow = feat_i.loc[d]
        if isinstance(frow, pd.DataFrame):
            frow = frow.iloc[-1]
        if bool(frow.get("flip", False)):
            book = str(frow.get("book") or BOOK_COMP)
            if book in weights_by_book and d in weights_by_book[book].index:
                w_dest = weights_by_book[book].loc[d, SOFT_CORE].to_numpy(dtype=float)
                if w_dest.sum() > 1e-12:
                    w_dest = w_dest / w_dest.sum()
                    before = float(w[etf_idx])
                    w, cut_would, cut_blocked = _apply_arm(
                        arm=arm,
                        gate=gate,
                        feat_row=frow,
                        w_prev=w,
                        w_dest=w_dest,
                        etf_idx=etf_idx,
                        fin_tel_idx=fin_tel_idx,
                    )
                    n_flip += 1
                    if cut_would:
                        n_cut_would += 1
                    if cut_blocked:
                        n_cut_blocked += 1
                    etf_turnover += abs(float(w[etf_idx]) - before)
        port_r = float(np.dot(w, r))
        nav.append(nav[-1] * (1.0 + port_r))
        w = w * (1.0 + r)
        s = float(w.sum())
        w = w / s if s > 1e-12 else w

    out = pd.DataFrame({"date": dates.to_numpy(), "nav": np.asarray(nav, dtype=float)})
    meta = {
        "arm": arm,
        "fill_timing": "t0",
        "n_days": int(len(out)),
        "n_flips_applied": int(n_flip),
        "n_large_cuts_would": int(n_cut_would),
        "n_large_cuts_blocked": int(n_cut_blocked),
        "sum_abs_etf_weight_delta_on_flips": round(float(etf_turnover), 6),
        "start": str(pd.Timestamp(out["date"].iloc[0]).date()),
        "end": str(pd.Timestamp(out["date"].iloc[-1]).date()),
    }
    return out, meta


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    px = _close_panel(SOFT_CORE)
    weights = {
        BOOK_COMP: _book_soft_weights(load_book_shares(BOOK_COMP), px),
        BOOK_SAT: _book_soft_weights(load_book_shares(BOOK_SAT), px),
    }
    sig = load_or_build_signal()
    feat = _load_feat(sig)
    # Persist feature snapshot on flips for audit
    flips = feat[feat["flip"].astype(bool)].copy()
    flips.to_csv(OUT / "flip_features.csv", index=False)

    arms = list(GATES.keys())
    navs: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict[str, Any]] = {}
    wins: dict[str, dict[str, Any]] = {}
    for arm in arms:
        nav, meta = simulate_arm(
            arm=arm, gate=GATES[arm], weights_by_book=weights, px=px, feat=feat
        )
        navs[arm] = nav
        metas[arm] = meta
        wins[arm] = _pack(nav)
        nav.to_csv(OUT / f"nav_{arm}.csv", index=False)

    rows = []
    for arm in arms:
        if arm == "KEEP":
            continue
        delta = _delta_windows(wins["KEEP"], wins[arm])
        tip = _tip(navs["KEEP"], navs[arm])
        yearly = yearly_compare(navs["KEEP"], navs[arm])
        ymap = {r["year"]: r for r in yearly}
        ret_w = int(sum(1 for r in yearly if r["ret_win"]))
        ret_l = int(sum(1 for r in yearly if not r["ret_win"]))
        loser_sum = round(
            sum(float(ymap[y]["ret_lift_pp"]) for y in LOSER_YEARS if y in ymap), 4
        )
        v = _arm_verdict(delta, tip)
        rows.append(
            {
                "arm": arm,
                "verdict_vs_keep": v,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "yearly_ret_w": ret_w,
                "yearly_ret_l": ret_l,
                "loser_years_ret_lift_sum_pp": loser_sum,
                "y2024_ret_lift_pp": (ymap.get(2024) or {}).get("ret_lift_pp"),
                "y2025_ret_lift_pp": (ymap.get(2025) or {}).get("ret_lift_pp"),
                "n_large_cuts_would": metas[arm]["n_large_cuts_would"],
                "n_large_cuts_blocked": metas[arm]["n_large_cuts_blocked"],
                "etf_turnover": metas[arm]["sum_abs_etf_weight_delta_on_flips"],
                "delta": delta,
                "tip": tip,
                "yearly": yearly,
                "meta": metas[arm],
            }
        )

    parent = next(r for r in rows if r["arm"] == "ADD_FULL_CUT_D05")
    hit_rows = [r for r in rows if r["verdict_vs_keep"] in {"HIT", "HELD_HIT"}]
    gated = [r for r in hit_rows if str(r["arm"]).startswith("CG_")]
    improved = [
        r
        for r in gated
        if float(r["loser_years_ret_lift_sum_pp"])
        > float(parent["loser_years_ret_lift_sum_pp"])
    ]
    if improved:
        champion = max(
            improved,
            key=lambda r: (
                float(r["held_cagr_lift_pp"] or -999),
                float(r["loser_years_ret_lift_sum_pp"]),
                float(r["tip_ytd_cagr_lift_pp"] or -999),
            ),
        )
        pack_verdict = "ETF_CUTGATE_HIT"
    elif gated and any(r["verdict_vs_keep"] in {"HIT", "HELD_HIT"} for r in gated):
        # HIT gated arms exist but none beat parent loserΣ
        champion = max(
            gated,
            key=lambda r: (
                float(r["loser_years_ret_lift_sum_pp"]),
                float(r["held_cagr_lift_pp"] or -999),
            ),
        )
        pack_verdict = "ETF_CUTGATE_PARENT_STILL_BEST"
        champion = parent
    elif parent["verdict_vs_keep"] in {"HIT", "HELD_HIT"}:
        champion = parent
        pack_verdict = "ETF_CUTGATE_PARENT_STILL_BEST"
    else:
        champion = max(rows, key=lambda r: float(r["held_cagr_lift_pp"] or -999))
        pack_verdict = f"ETF_CUTGATE_{champion['verdict_vs_keep']}"

    summary = [
        {
            "arm": r["arm"],
            "verdict_vs_keep": r["verdict_vs_keep"],
            "held_cagr_lift_pp": r["held_cagr_lift_pp"],
            "full_cagr_lift_pp": r["full_cagr_lift_pp"],
            "sealed_mdd_improve_pp": r["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": r["tip_ytd_cagr_lift_pp"],
            "tip_1y_cagr_lift_pp": r["tip_1y_cagr_lift_pp"],
            "yearly_ret_wl": f"{r['yearly_ret_w']}-{r['yearly_ret_l']}",
            "loser_years_ret_lift_sum_pp": r["loser_years_ret_lift_sum_pp"],
            "y2024_ret_lift_pp": r["y2024_ret_lift_pp"],
            "y2025_ret_lift_pp": r["y2025_ret_lift_pp"],
            "n_large_cuts_would": r["n_large_cuts_would"],
            "n_large_cuts_blocked": r["n_large_cuts_blocked"],
            "etf_turnover": r["etf_turnover"],
        }
        for r in rows
    ]
    pd.DataFrame(summary).to_csv(OUT / "arms_vs_keep.csv", index=False)
    pd.DataFrame(champion["yearly"]).to_csv(OUT / "yearly_champion_vs_keep.csv", index=False)

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parent": "0kai",
        "verdict": pack_verdict,
        "fill_timing": "t0",
        "champion_arm": champion["arm"],
        "base_policy": "ADD_FULL_CUT_D05",
        "features": [
            "prior_book_days",
            "r0050_63_l1",
            "trail_drag_l1",
            "zz08_bear_l1",
            "trail_rel_63",
        ],
        "arms_vs_keep": summary,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_keep": champion["verdict_vs_keep"],
            "loser_years_ret_lift_sum_pp": champion["loser_years_ret_lift_sum_pp"],
            "y2024_ret_lift_pp": champion["y2024_ret_lift_pp"],
            "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
            "delta": champion["delta"],
            "tip": champion["tip"],
            "meta": champion["meta"],
        },
        "parent_add_full_cut_d05": {
            "held_cagr_lift_pp": parent["held_cagr_lift_pp"],
            "loser_years_ret_lift_sum_pp": parent["loser_years_ret_lift_sum_pp"],
            "y2024_ret_lift_pp": parent["y2024_ret_lift_pp"],
        },
        "gates": {
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
            "tip_y_floor_pp": TIP_Y_FLOOR_PP,
        },
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage A — Path3 0050 ETF feature cut-gate** · Soft **KEEP** · "
            "broker **false** · cutover **BLOCKED** · no live",
            "Parent: 0kai `ETF_YEARMIT_HIT` / `ADD_FULL_CUT_D05`",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Can **causal** tip-gap / book-tenure features gate large Soft `0050` cuts "
            "to shrink loser-year drag vs parent `ADD_FULL_CUT_D05` without look-ahead "
            "year labels, while keeping HIT vs sticky KEEP?",
            "",
            "## Features (as-of)",
            "",
            "- `prior_book_days` — completed prior-book run length on flip",
            "- `r0050_63_l1`, `trail_drag_l1`, `zz08_bear_l1` — tipgap panel lag-1",
            "- `trail_rel_63` — Path3 flip depth (same-bar definition)",
            "",
            "## Arms",
            "",
            "- Baselines: KEEP · RATIO · DEAD_05 · ADD_FULL_CUT_D05",
            "- Gates on large cuts (|Δw|≥5pp): TENURE_LT{5,10} · R50_POS · DRAG_ONLY · "
            "ZZ08_ALLOW · DEEP_SAT · TENURE5_R50",
            "",
            "## Non-goals",
            "",
            "- Year labels · live wire · mute expand · Soft Exact T+1 · satellite · broker",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__CUTGATE__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parent": "0kai",
                "fill_timing": "t0",
                "soft_keep": True,
                "broker": False,
                "cutover_blocked": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    def _fmt(r: dict) -> str:
        return (
            f"| {r['arm']} | {r['verdict_vs_keep']} | {r['held_cagr_lift_pp']} | "
            f"{r['tip_ytd_cagr_lift_pp']} | {r['yearly_ret_wl']} | "
            f"{r['loser_years_ret_lift_sum_pp']} | {r['y2024_ret_lift_pp']} | "
            f"{r['y2025_ret_lift_pp']} | {r['n_large_cuts_blocked']}/{r['n_large_cuts_would']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · fill=`t0` · "
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · parent 0kai · end=`{metas['KEEP']['end']}`",
            "",
            "## Arms vs KEEP (T+0)",
            "",
            "| Arm | vs KEEP | held | tipY | ret W–L | loserΣ | 2024 | 2025 | blocked/would |",
            "|---|---|---:|---:|---|---:|---:|---:|---|",
            *[_fmt(r) for r in summary],
            "",
            f"Parent ADD_FULL_CUT_D05 loserΣ={parent['loser_years_ret_lift_sum_pp']} · "
            f"2024={parent['y2024_ret_lift_pp']}",
            "",
            f"## Champion `{champion['arm']}` yearly vs KEEP",
            "",
            "| Year | KEEP ret% | Chal ret% | Ret lift pp | MDD improve pp |",
            "|---:|---:|---:|---:|---:|",
            *[
                f"| {y['year']} | {y['ret_keep_pct']:.2f} | {y['ret_chal_pct']:.2f} | "
                f"{y['ret_lift_pp']:+.2f} | {y['mdd_improve_pp']:+.2f} |"
                for y in champion["yearly"]
            ],
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_recon_cutgate_stagea.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{pack_verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = []
    if pack_verdict == "ETF_CUTGATE_HIT":
        next_steps.append(
            f"Carry `{champion['arm']}` into coexist Stage C — still no live"
        )
    else:
        next_steps.append(
            "Keep 0kai `ADD_FULL_CUT_D05` — tip-gap/tenure cut gates no loserΣ edge"
        )
    next_steps.append("0kac PAPER_WITHIN_HIT remains primary Path3 roadmap")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{pack_verdict}__NO_LIVE",
        "verdict": pack_verdict,
        "register": REGISTER,
        "parent": "0kai",
        "champion_arm": champion["arm"],
        "fill_timing": "t0",
        "champion_held_cagr_lift_pp": champion["held_cagr_lift_pp"],
        "champion_loser_sum_pp": champion["loser_years_ret_lift_sum_pp"],
        "champion_y2024_pp": champion["y2024_ret_lift_pp"],
        "parent_loser_sum_pp": parent["loser_years_ret_lift_sum_pp"],
        "soft_keep": True,
        "broker": False,
        "cutover_blocked": True,
        "live_wire": False,
        "next": next_steps,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`** · fill=`t0`",
            f"Register: **{REGISTER}** · Parent: **0kai**",
            "",
            "## Champion vs KEEP / parent",
            "",
            f"- held CAGR lift: **{champion['held_cagr_lift_pp']}** pp "
            f"(parent {parent['held_cagr_lift_pp']})",
            f"- tipY: **{champion['tip_ytd_cagr_lift_pp']}**",
            f"- loser-year Σ: **{champion['loser_years_ret_lift_sum_pp']}** pp "
            f"(parent {parent['loser_years_ret_lift_sum_pp']})",
            f"- 2024: **{champion['y2024_ret_lift_pp']}** pp "
            f"(parent {parent['y2024_ret_lift_pp']})",
            "",
            "## Disposition",
            "",
            "- Causal tip-gap / tenure gates only · no year labels.",
            "- Live Path3 remains `keep_0050=True`.",
            "",
            "## Next",
            "",
            *[f"{i+1}. {s}" for i, s in enumerate(next_steps)],
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    print(
        json.dumps(
            {
                "verdict": pack_verdict,
                "champion": champion["arm"],
                "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
                "loser_sum_pp": champion["loser_years_ret_lift_sum_pp"],
                "y2024_pp": champion["y2024_ret_lift_pp"],
                "parent_loser_sum_pp": parent["loser_years_ret_lift_sum_pp"],
                "parent_y2024_pp": parent["y2024_ret_lift_pp"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
