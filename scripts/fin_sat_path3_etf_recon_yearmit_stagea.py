#!/usr/bin/env python3
"""Path3 0050 ETF recon year-mitigation Stage A (0kai) — paper only · T+0.

Parent 0kah: harden champion ``DEAD_05`` HIT but calendar losers remain
(2016/2020/2023/2024; 2024 ≈ −5pp). Diagnosis: 2024 hurt by large *cuts* of
0050; 2025 gain needs a large cut — static block-all-cuts MDD-blocks.

This pack probes **asymmetric / larger deadband** rules to shrink loser-year
drag while keeping HIT gates vs sticky KEEP.

Soft KEEP · broker false · cutover BLOCKED · no live.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
REPRO = ROOT / "repro" / "fin-sat-path3-etf-recon-yearmit-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_ETF_RECON_YEARMIT_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_ETF_RECON_YEARMIT_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_ETF_RECON_YEARMIT_STAGEA_DECISION_PACK"
REGISTER = "0kai"

LOSER_YEARS = (2016, 2020, 2023, 2024)

# (arm_id, kind, param)
# kind:
#   keep | ratio | dead | add_full_cut_dead | cut_full_add_dead | clip
ARMS: list[tuple[str, str, float | None]] = [
    ("KEEP", "keep", None),
    ("RATIO", "ratio", None),
    ("DEAD_05", "dead", 0.05),  # parent 0kah champion
    ("DEAD_07", "dead", 0.07),
    ("DEAD_08", "dead", 0.08),
    ("ADD_FULL_CUT_D05", "add_full_cut_dead", 0.05),
    ("ADD_FULL_CUT_D07", "add_full_cut_dead", 0.07),
    ("CUT_FULL_ADD_D05", "cut_full_add_dead", 0.05),
    ("CLIP_08", "clip", 0.08),
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _apply(
    *,
    kind: str,
    param: float | None,
    w_prev: np.ndarray,
    w_dest: np.ndarray,
    etf_idx: int,
    fin_tel_idx: list[int],
) -> np.ndarray:
    if kind == "keep":
        return _normalize_with_etf(
            w_prev=w_prev,
            w_dest=w_dest,
            etf_idx=etf_idx,
            fin_tel_idx=fin_tel_idx,
            etf_w=float(w_prev[etf_idx]),
        )
    if kind == "ratio":
        out = w_dest.astype(float).copy()
        s = float(out.sum())
        return out / s if s > 1e-12 else w_prev.copy()

    prev_e = float(w_prev[etf_idx])
    dest_e = float(w_dest[etf_idx])
    delta = dest_e - prev_e
    p = float(param or 0.0)

    if kind == "dead":
        etf_w = prev_e if abs(delta) < p else dest_e
    elif kind == "add_full_cut_dead":
        # Full follow on 0050 *adds*; deadband only on cuts.
        if delta > 0:
            etf_w = dest_e
        elif abs(delta) < p:
            etf_w = prev_e
        else:
            etf_w = dest_e
    elif kind == "cut_full_add_dead":
        # Full follow on cuts; deadband on adds (0kah-style opposite).
        if delta < 0:
            etf_w = dest_e
        elif abs(delta) < p:
            etf_w = prev_e
        else:
            etf_w = dest_e
    elif kind == "clip":
        etf_w = prev_e + float(np.clip(delta, -p, p))
    else:
        raise ValueError(kind)

    return _normalize_with_etf(
        w_prev=w_prev,
        w_dest=w_dest,
        etf_idx=etf_idx,
        fin_tel_idx=fin_tel_idx,
        etf_w=etf_w,
    )


def simulate_arm(
    *,
    weights_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    signal: pd.DataFrame,
    kind: str,
    param: float | None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    sig = signal.copy()
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.sort_values("date").reset_index(drop=True)
    dates = sig["date"]
    for wdf in weights_by_book.values():
        dates = dates[dates.isin(wdf.index)]
    dates = dates[dates.isin(px.index)].reset_index(drop=True)
    if len(dates) < 100:
        raise RuntimeError("insufficient overlap")

    rets = px.pct_change().reindex(dates).fillna(0.0)
    etf_idx = SOFT_CORE.index(ETF)
    fin_tel_idx = [SOFT_CORE.index(c) for c in list(FIN) + list(TEL)]
    row0 = sig[sig["date"] == dates.iloc[0]].iloc[0]
    book0 = str(row0.get("book") or BOOK_COMP)
    if book0 not in weights_by_book:
        book0 = BOOK_COMP
    w = weights_by_book[book0].loc[dates.iloc[0], SOFT_CORE].to_numpy(dtype=float)
    w = w / w.sum() if w.sum() > 1e-12 else np.ones(len(SOFT_CORE)) / len(SOFT_CORE)

    nav = [1.0]
    n_flip = 0
    n_move = 0
    etf_turnover = 0.0
    sig_by_date = sig.set_index("date")

    for i in range(1, len(dates)):
        d = dates.iloc[i]
        r = rets.loc[d, SOFT_CORE].to_numpy(dtype=float)
        if d in sig_by_date.index:
            srow = sig_by_date.loc[d]
            if isinstance(srow, pd.DataFrame):
                srow = srow.iloc[-1]
            if bool(srow.get("flip", False)):
                book = str(srow.get("book") or BOOK_COMP)
                if book in weights_by_book and d in weights_by_book[book].index:
                    w_dest = weights_by_book[book].loc[d, SOFT_CORE].to_numpy(dtype=float)
                    if w_dest.sum() > 1e-12:
                        w_dest = w_dest / w_dest.sum()
                        before = float(w[etf_idx])
                        w = _apply(
                            kind=kind,
                            param=param,
                            w_prev=w,
                            w_dest=w_dest,
                            etf_idx=etf_idx,
                            fin_tel_idx=fin_tel_idx,
                        )
                        dw = abs(float(w[etf_idx]) - before)
                        n_flip += 1
                        etf_turnover += dw
                        if dw > 1e-6:
                            n_move += 1
        port_r = float(np.dot(w, r))
        nav.append(nav[-1] * (1.0 + port_r))
        w = w * (1.0 + r)
        s = float(w.sum())
        w = w / s if s > 1e-12 else w

    out = pd.DataFrame({"date": dates.to_numpy(), "nav": np.asarray(nav, dtype=float)})
    meta = {
        "kind": kind,
        "param": param,
        "fill_timing": "t0",
        "n_days": int(len(out)),
        "n_flips_applied": int(n_flip),
        "n_flips_etf_moved": int(n_move),
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

    navs: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict[str, Any]] = {}
    wins: dict[str, dict[str, Any]] = {}
    for arm_id, kind, param in ARMS:
        nav, meta = simulate_arm(
            weights_by_book=weights, px=px, signal=sig, kind=kind, param=param
        )
        navs[arm_id] = nav
        metas[arm_id] = meta
        wins[arm_id] = _pack(nav)
        nav.to_csv(OUT / f"nav_{arm_id}.csv", index=False)

    rows = []
    for arm_id, kind, param in ARMS:
        if arm_id == "KEEP":
            continue
        delta = _delta_windows(wins["KEEP"], wins[arm_id])
        tip = _tip(navs["KEEP"], navs[arm_id])
        yearly = yearly_compare(navs["KEEP"], navs[arm_id])
        ymap = {r["year"]: r for r in yearly}
        ret_w = int(sum(1 for r in yearly if r["ret_win"]))
        ret_l = int(sum(1 for r in yearly if not r["ret_win"]))
        loser_sum = round(sum(float(ymap[y]["ret_lift_pp"]) for y in LOSER_YEARS if y in ymap), 4)
        v = _arm_verdict(delta, tip)
        rows.append(
            {
                "arm": arm_id,
                "kind": kind,
                "param": param,
                "verdict_vs_keep": v,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_cagr_lift_pp": delta["sealed_2023_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "yearly_ret_w": ret_w,
                "yearly_ret_l": ret_l,
                "loser_years_ret_lift_sum_pp": loser_sum,
                "y2024_ret_lift_pp": (ymap.get(2024) or {}).get("ret_lift_pp"),
                "y2025_ret_lift_pp": (ymap.get(2025) or {}).get("ret_lift_pp"),
                "y2022_ret_lift_pp": (ymap.get(2022) or {}).get("ret_lift_pp"),
                "etf_turnover": metas[arm_id]["sum_abs_etf_weight_delta_on_flips"],
                "n_etf_moves": metas[arm_id]["n_flips_etf_moved"],
                "delta": delta,
                "tip": tip,
                "yearly": yearly,
                "meta": metas[arm_id],
            }
        )

    parent = next(r for r in rows if r["arm"] == "DEAD_05")
    hit_rows = [r for r in rows if r["verdict_vs_keep"] in {"HIT", "HELD_HIT"}]
    # Prefer HIT arms that improve loser-year Σ vs parent; among them max held.
    improved = [
        r
        for r in hit_rows
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
                int(r["yearly_ret_w"]) - int(r["yearly_ret_l"]),
            ),
        )
    elif hit_rows:
        champion = max(
            hit_rows,
            key=lambda r: (
                float(r["loser_years_ret_lift_sum_pp"]),
                float(r["held_cagr_lift_pp"] or -999),
            ),
        )
    else:
        champion = max(rows, key=lambda r: float(r["held_cagr_lift_pp"] or -999))

    beats_parent_losers = float(champion["loser_years_ret_lift_sum_pp"]) > float(
        parent["loser_years_ret_lift_sum_pp"]
    )
    beats_parent_held = float(champion["held_cagr_lift_pp"] or 0) >= float(
        parent["held_cagr_lift_pp"] or 0
    ) - 0.05

    if champion["verdict_vs_keep"] in {"HIT", "HELD_HIT"} and beats_parent_losers:
        pack_verdict = "ETF_YEARMIT_HIT"
    elif champion["verdict_vs_keep"] in {"HIT", "HELD_HIT"} and champion["arm"] == "DEAD_05":
        pack_verdict = "ETF_YEARMIT_PARENT_STILL_BEST"
    elif champion["verdict_vs_keep"] in {"HIT", "HELD_HIT"}:
        pack_verdict = "ETF_YEARMIT_SOFT"  # HIT vs KEEP but no loser-year edge vs parent
    elif champion["verdict_vs_keep"] == "SOFT":
        pack_verdict = "ETF_YEARMIT_SOFT"
    elif champion["verdict_vs_keep"] == "MDD_BLOCK":
        pack_verdict = "ETF_YEARMIT_MDD_BLOCK"
    elif champion["verdict_vs_keep"] == "TIP_BLOCK":
        pack_verdict = "ETF_YEARMIT_TIP_BLOCK"
    else:
        pack_verdict = "ETF_YEARMIT_NO_EDGE"

    summary = [
        {
            "arm": r["arm"],
            "kind": r["kind"],
            "param": r["param"],
            "verdict_vs_keep": r["verdict_vs_keep"],
            "full_cagr_lift_pp": r["full_cagr_lift_pp"],
            "held_cagr_lift_pp": r["held_cagr_lift_pp"],
            "sealed_mdd_improve_pp": r["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": r["tip_ytd_cagr_lift_pp"],
            "tip_1y_cagr_lift_pp": r["tip_1y_cagr_lift_pp"],
            "yearly_ret_wl": f"{r['yearly_ret_w']}-{r['yearly_ret_l']}",
            "loser_years_ret_lift_sum_pp": r["loser_years_ret_lift_sum_pp"],
            "y2024_ret_lift_pp": r["y2024_ret_lift_pp"],
            "y2025_ret_lift_pp": r["y2025_ret_lift_pp"],
            "etf_turnover": r["etf_turnover"],
            "n_etf_moves": r["n_etf_moves"],
        }
        for r in rows
    ]
    pd.DataFrame(summary).to_csv(OUT / "arms_vs_keep.csv", index=False)
    pd.DataFrame(champion["yearly"]).to_csv(OUT / "yearly_champion_vs_keep.csv", index=False)

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parent": "0kah",
        "verdict": pack_verdict,
        "fill_timing": "t0",
        "champion_arm": champion["arm"],
        "loser_years": list(LOSER_YEARS),
        "method": {
            "note": (
                "Asymmetric/larger deadband on flip Δw_0050 to shrink "
                "2016/2020/2023/2024 drag without look-ahead year labels"
            ),
            "arms": [a[0] for a in ARMS],
        },
        "arms_vs_keep": summary,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_keep": champion["verdict_vs_keep"],
            "loser_years_ret_lift_sum_pp": champion["loser_years_ret_lift_sum_pp"],
            "delta": champion["delta"],
            "tip": champion["tip"],
            "yearly_ret_wl": {"w": champion["yearly_ret_w"], "l": champion["yearly_ret_l"]},
            "beats_parent_losers": beats_parent_losers,
            "beats_parent_held_within_5bp": beats_parent_held,
            "meta": champion["meta"],
        },
        "parent_dead_05": {
            "held_cagr_lift_pp": parent["held_cagr_lift_pp"],
            "loser_years_ret_lift_sum_pp": parent["loser_years_ret_lift_sum_pp"],
            "y2024_ret_lift_pp": parent["y2024_ret_lift_pp"],
            "yearly_ret_wl": {"w": parent["yearly_ret_w"], "l": parent["yearly_ret_l"]},
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
            "Status: **Stage A — Path3 0050 ETF recon year-mitigation** · Soft **KEEP** · "
            "broker **false** · cutover **BLOCKED** · no live",
            "Parent: 0kah `ETF_HARDEN_HIT` / `DEAD_05`",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Can **asymmetric** or **larger deadband** rules on flip-day Soft `0050` "
            "shrink calendar-loser drag (esp. 2024) vs parent `DEAD_05` while still "
            "HITting sticky `KEEP` on held/sealed/tip?",
            "",
            "## Diagnosis (0kah)",
            "",
            "- Loser years under DEAD_05: 2016 / 2020 / 2023 / **2024 (~−5pp)**",
            "- 2024 large *cut* of 0050 hurt; 2025 large cut helped → no look-ahead "
            "block-all-cuts (MDD_BLOCK in probe)",
            "",
            "## Method",
            "",
            "- Soft-core carve-only · Path3 flips · **fill `t0`**",
            "- Arms: KEEP · RATIO · DEAD_{05,07,08} · ADD_FULL_CUT_D{05,07} · "
            "CUT_FULL_ADD_D05 · CLIP_08",
            "- Champion: HIT arms that improve loser-year Σ vs `DEAD_05`, then max held",
            "",
            "## Non-goals",
            "",
            "- Look-ahead year labels · live wire · mute expand · Soft Exact T+1 · "
            "satellite · broker",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__YEARMIT__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parent": "0kah",
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
            f"{r['y2025_ret_lift_pp']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · fill=`t0` · "
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · parent 0kah · end=`{metas['KEEP']['end']}`",
            "",
            "## Arms vs KEEP (T+0)",
            "",
            "| Arm | vs KEEP | held CAGR | tipY | ret W–L | loserΣ pp | 2024 | 2025 |",
            "|---|---|---:|---:|---|---:|---:|---:|",
            *[_fmt(r) for r in summary],
            "",
            f"Parent DEAD_05 loserΣ={parent['loser_years_ret_lift_sum_pp']} · "
            f"2024={parent['y2024_ret_lift_pp']}",
            "",
            f"## Champion `{champion['arm']}` yearly vs KEEP",
            "",
            f"- Ret W–L **{champion['yearly_ret_w']}–{champion['yearly_ret_l']}** · "
            f"loserΣ **{champion['loser_years_ret_lift_sum_pp']}** pp",
            "",
            "| Year | KEEP ret% | Chal ret% | Ret lift pp | MDD improve pp |",
            "|---:|---:|---:|---:|---:|",
            *[
                f"| {y['year']} | {y['ret_keep_pct']:.2f} | {y['ret_chal_pct']:.2f} | "
                f"{y['ret_lift_pp']:+.2f} | {y['mdd_improve_pp']:+.2f} |"
                for y in champion["yearly"]
            ],
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_recon_yearmit_stagea.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{pack_verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = []
    if pack_verdict == "ETF_YEARMIT_HIT":
        next_steps.append(
            f"Carry `{champion['arm']}` (not raw DEAD_05) into coexist Stage C — still no live"
        )
    elif pack_verdict == "ETF_YEARMIT_PARENT_STILL_BEST":
        next_steps.append("Keep 0kah `DEAD_05`; year-mitigation no edge on loserΣ")
    else:
        next_steps.append("No year-mitigation promote over 0kah; live keep_0050=True")
    next_steps.append("Optional: feature-conditioned cut gate (tip-gap / book tenure) Stage A+")
    next_steps.append("0kac PAPER_WITHIN_HIT remains primary Path3 roadmap")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{pack_verdict}__NO_LIVE",
        "verdict": pack_verdict,
        "register": REGISTER,
        "parent": "0kah",
        "champion_arm": champion["arm"],
        "fill_timing": "t0",
        "champion_held_cagr_lift_pp": champion["held_cagr_lift_pp"],
        "champion_loser_sum_pp": champion["loser_years_ret_lift_sum_pp"],
        "champion_y2024_pp": champion["y2024_ret_lift_pp"],
        "parent_dead05_loser_sum_pp": parent["loser_years_ret_lift_sum_pp"],
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
            f"Register: **{REGISTER}** · Parent: **0kah**",
            "",
            "## Champion vs KEEP / parent",
            "",
            f"- held CAGR lift: **{champion['held_cagr_lift_pp']}** pp "
            f"(parent DEAD_05 {parent['held_cagr_lift_pp']})",
            f"- tipY / tip1y: **{champion['tip_ytd_cagr_lift_pp']}** / "
            f"**{champion['tip_1y_cagr_lift_pp']}**",
            f"- loser-year Σ ret lift: **{champion['loser_years_ret_lift_sum_pp']}** pp "
            f"(parent {parent['loser_years_ret_lift_sum_pp']})",
            f"- 2024 ret lift: **{champion['y2024_ret_lift_pp']}** pp "
            f"(parent {parent['y2024_ret_lift_pp']})",
            f"- yearly ret W–L: **{champion['yearly_ret_w']}–{champion['yearly_ret_l']}**",
            "",
            "## Disposition",
            "",
            "- Paper Soft-core carve-only · no look-ahead year labels.",
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
                "parent_dead05_loser_sum_pp": parent["loser_years_ret_lift_sum_pp"],
                "parent_y2024_pp": parent["y2024_ret_lift_pp"],
                "yearly_ret_wl": f"{champion['yearly_ret_w']}-{champion['yearly_ret_l']}",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
