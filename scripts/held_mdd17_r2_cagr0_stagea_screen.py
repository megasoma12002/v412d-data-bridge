#!/usr/bin/env python3
"""R2 Stage A: MDD band [-14%,-13%] with CAGR giveback → 0 (paper only).

New roles vs R1 PROXY densify:
  DUAL_CONFIRM · FAST_REBOUND · SOFT_THEN_HARD · TIMEBOX
Controls: BASE_LIVE · REF_PROXY_x08_f50

Soft-Frozen KEEP · Stage-E DEFAULT · no live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as dh
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from soft_assist_helpers import LIVE_KD
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "held-mdd17-r2-cagr0-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "HELD_MDD17_R2_CAGR0_PAPER_CHARTER"
SCREEN_ID = "HELD_MDD17_R2_CAGR0_STAGEA_SCREEN"
HELDOUT = "heldout_2019_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
MDD_LO, MDD_HI = -0.14, -0.13
GB_STRETCH, GB_PRIMARY, GB_BEATS_R1 = 0.3, 0.5, 1.0


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
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


def _tip(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"mdd_improve_pp": None, "cagr_giveback_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = cagr_delta_pp(bc, cc)
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "gate": "PASS",
        }
    return out


def _sim(market, target, regime, dividends, scores, buy_ok, exposure=None):
    kw: dict[str, Any] = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        e22_version=E22_VERSION,
    )
    if exposure is not None:
        kw["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kw)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, int(len(fills))


def _nav_s(nav: pd.DataFrame) -> pd.Series:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    return d.set_index("date")["nav"].astype(float).sort_index()


def exp_proxy_ref(dates, px, x=0.08, floor=0.50, cool=5):
    out = pd.Series(1.0, index=dates, dtype=float)
    cool_left = 0
    for i in range(len(dates)):
        if cool_left > 0:
            cool_left -= 1
            out.iloc[i] = float(floor)
            continue
        if float(px.iloc[i]) <= -float(x):
            out.iloc[i] = float(floor)
            cool_left = int(cool)
        else:
            out.iloc[i] = 1.0
    return out


def exp_dual_confirm(dates, px, book_mdd, x, b, floor, cool):
    out = pd.Series(1.0, index=dates, dtype=float)
    cool_left = 0
    for i in range(len(dates)):
        if cool_left > 0:
            cool_left -= 1
            out.iloc[i] = float(floor)
            continue
        if float(px.iloc[i]) <= -float(x) and float(book_mdd.iloc[i]) <= -float(b):
            out.iloc[i] = float(floor)
            cool_left = int(cool)
        else:
            out.iloc[i] = 1.0
    return out


def exp_fast_rebound(dates, px, x, floor, exit_x, max_dwell, cool=0):
    out = pd.Series(1.0, index=dates, dtype=float)
    defending = False
    dwell = 0
    cool_left = 0
    for i in range(len(dates)):
        v = float(px.iloc[i])
        if cool_left > 0:
            cool_left -= 1
            out.iloc[i] = 1.0
            continue
        if not defending:
            if v <= -float(x):
                defending = True
                dwell = 0
                out.iloc[i] = float(floor)
            else:
                out.iloc[i] = 1.0
        else:
            dwell += 1
            out.iloc[i] = float(floor)
            if v > -float(exit_x) or dwell >= int(max_dwell):
                defending = False
                cool_left = int(cool)
                out.iloc[i] = 1.0
    return out


def exp_soft_then_hard(dates, px, x, delta, soft_floor, hard_floor):
    """Shallow: soft_floor when -x-delta < px <= -x; deep: hard_floor when px <= -x-delta."""
    out = pd.Series(1.0, index=dates, dtype=float)
    for i in range(len(dates)):
        v = float(px.iloc[i])
        if v >= -float(x):
            out.iloc[i] = 1.0
        elif v <= -float(x) - float(delta):
            out.iloc[i] = float(hard_floor)
        else:
            # interpolate soft_floor at -x toward hard at -x-delta
            t = (-float(x) - v) / float(delta)
            out.iloc[i] = float(soft_floor + t * (hard_floor - soft_floor))
    return out


def exp_timebox(dates, px, x, floor, max_dwell, cool):
    return exp_fast_rebound(dates, px, x, floor, exit_x=x, max_dwell=max_dwell, cool=cool)


def _verdict(rows: list[dict[str, Any]]) -> tuple[str, list[str]]:
    stretch, primary, beats, band_only = [], [], [], []
    for r in rows:
        if r["track"] in ("BASE", "CTRL"):
            continue
        h = r.get("held") or {}
        tip = r.get("tip") or {}
        if not h.get("in_band"):
            continue
        tips_ok = all(
            (tip.get(w) or {}).get("gate") == "PASS"
            and (tip.get(w) or {}).get("mdd_improve_pp") is not None
            and float((tip.get(w) or {}).get("mdd_improve_pp")) >= 0.0
            for w in ("ytd", "trailing_1y")
        )
        gb = h.get("cagr_giveback_pp")
        if gb is None or not tips_ok:
            band_only.append(r["id"])
            continue
        gb = float(gb)
        if gb <= GB_STRETCH:
            stretch.append(r["id"])
        elif gb <= GB_PRIMARY:
            primary.append(r["id"])
        elif gb <= GB_BEATS_R1:
            beats.append(r["id"])
        else:
            band_only.append(r["id"])
    if stretch:
        return "BAND_CAGR_STRETCH", stretch
    if primary:
        return "BAND_CAGR_PRIMARY", primary
    if beats:
        return "BAND_BEATS_R1_REF", beats
    if band_only:
        return "BAND_ONLY", band_only
    return "NO_BAND", []


def main() -> int:
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _sleeve, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    kd_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    kd_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )

    print("BASE_LIVE ...", flush=True)
    base_nav, base_fills = _sim(market, target, regime, dividends, kd_scores, kd_ok, None)
    base_w = _pack(base_nav)
    base_s = _nav_s(base_nav)
    feat = dh._risk_features(market, base_s)
    dates = pd.DatetimeIndex(base_s.index)
    px = feat["proxy_mdd63"].reindex(dates).fillna(0.0)
    book_mdd = feat["book_mdd63"].reindex(dates).fillna(0.0)

    recipes: list[tuple[str, str, pd.Series | None, dict[str, Any]]] = [
        ("BASE_LIVE", "BASE", None, {}),
        (
            "REF_PROXY_x08_f50",
            "CTRL",
            exp_proxy_ref(dates, px),
            {"x": 0.08, "floor": 0.50, "cool": 5},
        ),
    ]

    # DUAL_CONFIRM finite
    for x in (0.08, 0.09, 0.10):
        for b in (0.06, 0.08, 0.10):
            for floor in (0.45, 0.50, 0.55):
                rid = f"DUAL_x{int(x*100):02d}_b{int(b*100):02d}_f{int(floor*100):02d}"
                recipes.append(
                    (
                        rid,
                        "DUAL_CONFIRM",
                        exp_dual_confirm(dates, px, book_mdd, x, b, floor, 5),
                        {"x": x, "book_dd": b, "floor": floor, "cool": 5},
                    )
                )

    # FAST_REBOUND finite
    for x, exit_x, floor, max_dwell in (
        (0.08, 0.06, 0.50, 10),
        (0.08, 0.06, 0.50, 15),
        (0.08, 0.05, 0.50, 10),
        (0.08, 0.06, 0.55, 10),
        (0.08, 0.07, 0.50, 8),
        (0.09, 0.06, 0.50, 10),
        (0.08, 0.06, 0.50, 21),
        (0.08, 0.04, 0.50, 15),
    ):
        rid = f"FAST_x{int(x*100):02d}_ex{int(exit_x*100):02d}_f{int(floor*100):02d}_d{max_dwell}"
        recipes.append(
            (
                rid,
                "FAST_REBOUND",
                exp_fast_rebound(dates, px, x, floor, exit_x, max_dwell, cool=2),
                {"x": x, "exit_x": exit_x, "floor": floor, "max_dwell": max_dwell},
            )
        )

    # SOFT_THEN_HARD finite
    for x, delta, soft_f, hard_f in (
        (0.08, 0.03, 0.75, 0.45),
        (0.08, 0.04, 0.70, 0.40),
        (0.08, 0.05, 0.70, 0.50),
        (0.08, 0.04, 0.80, 0.50),
        (0.09, 0.04, 0.70, 0.45),
        (0.08, 0.03, 0.65, 0.50),
        (0.07, 0.04, 0.75, 0.50),
        (0.08, 0.06, 0.70, 0.35),
    ):
        rid = f"STH_x{int(x*100):02d}_d{int(delta*100):02d}_s{int(soft_f*100):02d}_h{int(hard_f*100):02d}"
        recipes.append(
            (
                rid,
                "SOFT_THEN_HARD",
                exp_soft_then_hard(dates, px, x, delta, soft_f, hard_f),
                {"x": x, "delta": delta, "soft_floor": soft_f, "hard_floor": hard_f},
            )
        )

    # TIMEBOX finite
    for x, floor, max_dwell, cool in (
        (0.08, 0.50, 8, 3),
        (0.08, 0.50, 12, 3),
        (0.08, 0.50, 15, 5),
        (0.08, 0.45, 10, 3),
        (0.08, 0.55, 10, 3),
        (0.09, 0.50, 10, 3),
        (0.08, 0.50, 5, 2),
        (0.08, 0.40, 12, 3),
    ):
        rid = f"TB_x{int(x*100):02d}_f{int(floor*100):02d}_d{max_dwell}_c{cool}"
        recipes.append(
            (
                rid,
                "TIMEBOX",
                exp_timebox(dates, px, x, floor, max_dwell, cool),
                {"x": x, "floor": floor, "max_dwell": max_dwell, "cool": cool},
            )
        )

    rows: list[dict[str, Any]] = []
    keep_nav_ids = {"BASE_LIVE", "REF_PROXY_x08_f50"}

    for rid, track, exposure, params in recipes:
        print(f"sim {rid} ...", flush=True)
        if rid == "BASE_LIVE":
            nav, n_fills = base_nav, base_fills
            chal_w = base_w
        else:
            nav, n_fills = _sim(market, target, regime, dividends, kd_scores, kd_ok, exposure)
            chal_w = _pack(nav)
        bh = base_w[HELDOUT]
        ch = chal_w[HELDOUT]
        gb = cagr_delta_pp(bh.get("cagr"), ch.get("cagr"))
        mdd_up = mdd_delta_pp(bh.get("max_drawdown"), ch.get("max_drawdown"))
        mdd = float(ch["max_drawdown"])
        in_band = (mdd + 1e-12 >= MDD_LO) and (mdd - 1e-12 <= MDD_HI)
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
            }
            if rid == "BASE_LIVE"
            else _tip(base_nav, nav)
        )
        mean_exp = 1.0 if exposure is None else float(np.asarray(exposure, dtype=float).mean())
        held = {
            "cagr": ch["cagr"],
            "max_drawdown": ch["max_drawdown"],
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "mdd_improve_pp": round(float(mdd_up), 4),
            "in_band": in_band,
        }
        row = {
            "id": rid,
            "track": track,
            "params": params,
            "windows": chal_w,
            "held": held,
            "tip": tip,
            "mean_exposure": round(mean_exp, 4),
            "n_fills": n_fills,
        }
        rows.append(row)
        if in_band or rid in keep_nav_ids:
            keep_nav_ids.add(rid)
            nav.to_csv(OUT / f"nav_{rid}.csv", index=False)
        print(
            f"  MDD {100*mdd:.2f}% CAGR {100*float(ch['cagr']):.2f}% "
            f"gb={held['cagr_giveback_pp']} band={in_band}",
            flush=True,
        )

    verdict, winners = _verdict(rows)
    summary = {
        "label": SCREEN_ID,
        "charter": CHARTER_ID,
        "generated_at_utc": _utc(),
        "status": "PAPER_ONLY",
        "live_wire": False,
        "soft_frozen_keep": True,
        "e22_books_version": E22_VERSION,
        "target": {
            "mdd_band": [MDD_LO, MDD_HI],
            "giveback_stretch_pp": GB_STRETCH,
            "giveback_primary_pp": GB_PRIMARY,
            "giveback_beats_r1_pp": GB_BEATS_R1,
            "heldout": HELDOUT,
        },
        "base_held": base_w[HELDOUT],
        "verdict": verdict,
        "winners": winners,
        "n_recipes": len(rows),
        "rows": rows,
        "parent_r1_ref": "PROXY_x08_f50 ~ gb +1.11pp at MDD ~-14.34%",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (OPS / "HELD_MDD17_R2_CAGR0_STAGEA_SCREEN.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Held-MDD band −14%～−13% · CAGR→0 — Stage A Screen (R2)",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        f"Books: `{E22_VERSION}` · Soft-Frozen **KEEP** · live wire **False**",
        f"Base held: CAGR `{100*float(base_w[HELDOUT]['cagr']):.2f}%` · "
        f"MDD `{100*float(base_w[HELDOUT]['max_drawdown']):.2f}%`",
        f"Target band: `[{MDD_LO}, {MDD_HI}]` · stretch gb≤`{GB_STRETCH}` · "
        f"primary≤`{GB_PRIMARY}` · beats R1≤`{GB_BEATS_R1}`",
        f"Verdict: **`{verdict}`** · winners: `{winners}`",
        "",
        "## Leaderboard (in-band first, then by giveback)",
        "",
        "| id | track | held CAGR | held MDD | in_band | gb pp | MDD↑ pp | mean exp |",
        "|---|---|---:|---:|---|---:|---:|---:|",
    ]
    ranked = sorted(
        rows,
        key=lambda r: (
            0 if (r.get("held") or {}).get("in_band") else 1,
            float((r.get("held") or {}).get("cagr_giveback_pp") or 99),
            -float((r.get("held") or {}).get("max_drawdown") or -9),
        ),
    )
    for r in ranked:
        h = r.get("held") or {}
        w = (r.get("windows") or {}).get(HELDOUT) or {}
        lines.append(
            "| `{id}` | {track} | {cagr} | {mdd} | {band} | {gb} | {md} | {mex} |".format(
                id=r["id"],
                track=r["track"],
                cagr="n/a" if w.get("cagr") is None else f"{100*float(w['cagr']):.2f}%",
                mdd="n/a" if w.get("max_drawdown") is None else f"{100*float(w['max_drawdown']):.2f}%",
                band=h.get("in_band"),
                gb=h.get("cagr_giveback_pp"),
                md=h.get("mdd_improve_pp"),
                mex=r.get("mean_exposure"),
            )
        )
    lines += [
        "",
        "## Reading",
        "",
        "- R2 asks whether **new roles** beat R1 ref giveback (~1.11pp) inside MDD band.",
        "- PROXY densify alone is control/exhausted; Soft-Frozen tip untouched.",
        "",
        f"Repro: `repro/held-mdd17-r2-cagr0-stagea/` · Charter: `{CHARTER_ID}`",
        "",
        f"Label: `{SCREEN_ID}_{summary['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    text = "\n".join(lines)
    (REP / "HELD_MDD17_R2_CAGR0_STAGEA_SCREEN.md").write_text(text, encoding="utf-8")
    (OPS / "HELD_MDD17_R2_CAGR0_STAGEA_SCREEN.md").write_text(text, encoding="utf-8")
    (REPRO / "README.md").write_text(
        "\n".join(
            [
                "# R2 CAGR→0 Stage A repro",
                "",
                f"Verdict: **{verdict}**",
                "",
                "```bash",
                "PYTHONPATH=scripts python3 scripts/held_mdd17_r2_cagr0_stagea_screen.py",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"verdict": verdict, "winners": winners, "base": base_w[HELDOUT]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
