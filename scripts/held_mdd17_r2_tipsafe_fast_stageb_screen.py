#!/usr/bin/env python3
"""R2 Stage B: tip-safe FAST family (paper only).

Anchor: FAST_x08_ex06_f50_d21 (held gb~+0.56pp, tip MDD fail).
Tracks: FLOOR_UP · DUAL_ENTRY · FAST_EXIT · BOOK_GATE · COOL_EXT.

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
REPRO = ROOT / "repro" / "held-mdd17-r2-tipsafe-fast-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_CHARTER"
SCREEN_ID = "HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_SCREEN"
HELDOUT = "heldout_2019_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
MDD_LO, MDD_HI = -0.145, -0.13
GB_STRETCH, GB_PRESERVE, GB_OK = 0.56, 0.70, 1.00


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


def exp_fast(
    dates: pd.DatetimeIndex,
    px: pd.Series,
    *,
    x: float,
    floor: float,
    exit_x: float,
    max_dwell: int,
    cool: int = 2,
    book_mdd: pd.Series | None = None,
    book_dd_need: float | None = None,
    book_peak_dd: pd.Series | None = None,
    peak_gate: float | None = None,
) -> pd.Series:
    """FAST with optional dual book_mdd63 and/or book peak-DD gate."""
    out = pd.Series(1.0, index=dates, dtype=float)
    defending = False
    dwell = 0
    cool_left = 0
    bm = None if book_mdd is None else book_mdd.reindex(dates).fillna(0.0)
    bp = None if book_peak_dd is None else book_peak_dd.reindex(dates).fillna(0.0)
    for i in range(len(dates)):
        v = float(px.iloc[i])
        if cool_left > 0:
            cool_left -= 1
            out.iloc[i] = 1.0
            continue
        if not defending:
            ok = v <= -float(x)
            if ok and book_dd_need is not None and bm is not None:
                ok = ok and float(bm.iloc[i]) <= -float(book_dd_need)
            if ok and peak_gate is not None and bp is not None:
                ok = ok and float(bp.iloc[i]) <= -float(peak_gate)
            if ok:
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


def book_peak_dd_series(nav: pd.Series) -> pd.Series:
    peak = nav.cummax()
    return nav / peak - 1.0


def _tips_ok(tip: dict[str, Any]) -> bool:
    return all(
        (tip.get(w) or {}).get("gate") == "PASS"
        and (tip.get(w) or {}).get("mdd_improve_pp") is not None
        and float((tip.get(w) or {}).get("mdd_improve_pp")) >= 0.0
        for w in ("ytd", "trailing_1y")
    )


def _verdict(rows: list[dict[str, Any]]) -> tuple[str, list[str]]:
    stretch, preserve, ok, tip_fail = [], [], [], []
    any_band = False
    for r in rows:
        if r["track"] in ("BASE",):
            continue
        h = r.get("held") or {}
        if not h.get("in_band"):
            continue
        any_band = True
        tip = r.get("tip") or {}
        gb = h.get("cagr_giveback_pp")
        if gb is None:
            continue
        if not _tips_ok(tip):
            tip_fail.append(r["id"])
            continue
        gb = float(gb)
        if gb <= GB_STRETCH:
            stretch.append(r["id"])
        elif gb <= GB_PRESERVE:
            preserve.append(r["id"])
        elif gb <= GB_OK:
            ok.append(r["id"])
        else:
            tip_fail.append(r["id"])  # band but gb too high — still not tipsafe-ok class
    if stretch:
        return "TIPSAFE_STRETCH", stretch
    if preserve:
        return "TIPSAFE_PRESERVE", preserve
    if ok:
        return "TIPSAFE_OK", ok
    if tip_fail or any_band:
        return "TIP_FAIL", tip_fail
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
    peak_dd = book_peak_dd_series(base_s)

    recipes: list[tuple[str, str, pd.Series | None, dict[str, Any]]] = [
        ("BASE_LIVE", "BASE", None, {}),
    ]

    # Anchor (expected TIP_FAIL)
    recipes.append(
        (
            "ANCHOR_FAST_x08_ex06_f50_d21",
            "CTRL",
            exp_fast(dates, px, x=0.08, floor=0.50, exit_x=0.06, max_dwell=21, cool=2),
            {"x": 0.08, "exit_x": 0.06, "floor": 0.50, "max_dwell": 21, "cool": 2},
        )
    )

    # FLOOR_UP
    for floor in (0.55, 0.60, 0.65, 0.70):
        for dwell in (18, 21, 24):
            rid = f"FLOOR_f{int(floor*100):02d}_d{dwell}"
            recipes.append(
                (
                    rid,
                    "FLOOR_UP",
                    exp_fast(dates, px, x=0.08, floor=floor, exit_x=0.06, max_dwell=dwell, cool=2),
                    {"x": 0.08, "exit_x": 0.06, "floor": floor, "max_dwell": dwell, "cool": 2},
                )
            )

    # DUAL_ENTRY
    for b in (0.04, 0.05, 0.06, 0.08):
        for floor in (0.50, 0.55, 0.60):
            for dwell in (18, 21):
                rid = f"DUAL_b{int(b*100):02d}_f{int(floor*100):02d}_d{dwell}"
                recipes.append(
                    (
                        rid,
                        "DUAL_ENTRY",
                        exp_fast(
                            dates,
                            px,
                            x=0.08,
                            floor=floor,
                            exit_x=0.06,
                            max_dwell=dwell,
                            cool=2,
                            book_mdd=book_mdd,
                            book_dd_need=b,
                        ),
                        {"x": 0.08, "book_dd": b, "floor": floor, "max_dwell": dwell},
                    )
                )

    # FAST_EXIT
    for exit_x, dwell, floor in (
        (0.07, 15, 0.50),
        (0.07, 18, 0.50),
        (0.07, 21, 0.50),
        (0.075, 18, 0.50),
        (0.065, 15, 0.55),
        (0.07, 18, 0.55),
        (0.08, 12, 0.50),  # exit at enter threshold
        (0.07, 21, 0.55),
    ):
        rid = f"EXIT_ex{int(exit_x*1000):03d}_f{int(floor*100):02d}_d{dwell}"
        recipes.append(
            (
                rid,
                "FAST_EXIT",
                exp_fast(dates, px, x=0.08, floor=floor, exit_x=exit_x, max_dwell=dwell, cool=2),
                {"x": 0.08, "exit_x": exit_x, "floor": floor, "max_dwell": dwell},
            )
        )

    # BOOK_GATE (peak DD)
    for gate in (0.02, 0.03, 0.04, 0.05):
        for floor in (0.50, 0.55, 0.60):
            rid = f"GATE_g{int(gate*100):02d}_f{int(floor*100):02d}_d21"
            recipes.append(
                (
                    rid,
                    "BOOK_GATE",
                    exp_fast(
                        dates,
                        px,
                        x=0.08,
                        floor=floor,
                        exit_x=0.06,
                        max_dwell=21,
                        cool=2,
                        book_peak_dd=peak_dd,
                        peak_gate=gate,
                    ),
                    {"x": 0.08, "peak_gate": gate, "floor": floor, "max_dwell": 21},
                )
            )

    # COOL_EXT
    for cool in (3, 5, 8, 10):
        for floor in (0.50, 0.55):
            rid = f"COOL_c{cool}_f{int(floor*100):02d}_d21"
            recipes.append(
                (
                    rid,
                    "COOL_EXT",
                    exp_fast(dates, px, x=0.08, floor=floor, exit_x=0.06, max_dwell=21, cool=cool),
                    {"x": 0.08, "exit_x": 0.06, "floor": floor, "max_dwell": 21, "cool": cool},
                )
            )

    # Hybrid tip-hopeful cells (small finite)
    for floor, b, dwell, cool in (
        (0.55, 0.05, 21, 5),
        (0.60, 0.05, 21, 5),
        (0.55, 0.06, 18, 5),
        (0.55, 0.04, 21, 8),
        (0.60, 0.06, 21, 5),
    ):
        rid = f"HYB_b{int(b*100):02d}_f{int(floor*100):02d}_d{dwell}_c{cool}"
        recipes.append(
            (
                rid,
                "DUAL_ENTRY",
                exp_fast(
                    dates,
                    px,
                    x=0.08,
                    floor=floor,
                    exit_x=0.06,
                    max_dwell=dwell,
                    cool=cool,
                    book_mdd=book_mdd,
                    book_dd_need=b,
                ),
                {"x": 0.08, "book_dd": b, "floor": floor, "max_dwell": dwell, "cool": cool},
            )
        )

    rows: list[dict[str, Any]] = []
    keep_nav: set[str] = {"BASE_LIVE", "ANCHOR_FAST_x08_ex06_f50_d21"}

    for rid, track, exposure, params in recipes:
        print(f"sim {rid} ...", flush=True)
        if rid == "BASE_LIVE":
            nav, n_fills = base_nav, base_fills
            chal_w = base_w
        else:
            nav, n_fills = _sim(market, target, regime, dividends, kd_scores, kd_ok, exposure)
            chal_w = _pack(nav)
        bh, ch = base_w[HELDOUT], chal_w[HELDOUT]
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
            "tip_ok": True if rid == "BASE_LIVE" else _tips_ok(tip),
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
        if in_band or rid in keep_nav or (held.get("tip_ok") and held.get("cagr_giveback_pp") is not None and float(held["cagr_giveback_pp"]) <= GB_PRESERVE and mdd >= -0.16):
            keep_nav.add(rid)
            nav.to_csv(OUT / f"nav_{rid}.csv", index=False)
        print(
            f"  MDD {100*mdd:.2f}% CAGR {100*float(ch['cagr']):.2f}% "
            f"gb={held['cagr_giveback_pp']} band={in_band} tip_ok={held['tip_ok']}",
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
            "giveback_preserve_pp": GB_PRESERVE,
            "giveback_ok_pp": GB_OK,
            "heldout": HELDOUT,
        },
        "base_held": base_w[HELDOUT],
        "anchor": "FAST_x08_ex06_f50_d21 / ANCHOR_FAST_x08_ex06_f50_d21",
        "verdict": verdict,
        "winners": winners,
        "n_recipes": len(rows),
        "rows": rows,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (OPS / "HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_SCREEN.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Tip-safe FAST — Stage B Screen (R2)",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        f"Books: `{E22_VERSION}` · Soft-Frozen **KEEP** · live wire **False**",
        f"Anchor: `FAST_x08_ex06_f50_d21` (held gb~+0.56pp, tip MDD fail)",
        f"Band: `[{MDD_LO}, {MDD_HI}]` · stretch gb≤{GB_STRETCH} · preserve≤{GB_PRESERVE} · ok≤{GB_OK}",
        f"Verdict: **`{verdict}`** · winners: `{winners}`",
        "",
        "| id | track | held CAGR | held MDD | band | gb | tip_ok | tip ytd↑ | tip 1y↑ |",
        "|---|---|---:|---:|---|---:|---|---:|---:|",
    ]
    ranked = sorted(
        rows,
        key=lambda r: (
            0 if (r.get("held") or {}).get("tip_ok") and (r.get("held") or {}).get("in_band") else 1,
            0 if (r.get("held") or {}).get("in_band") else 1,
            float((r.get("held") or {}).get("cagr_giveback_pp") or 99),
        ),
    )
    for r in ranked:
        h = r.get("held") or {}
        tip = r.get("tip") or {}
        w = (r.get("windows") or {}).get(HELDOUT) or {}
        # show band or tip_ok near-preserve or controls
        if not (
            h.get("in_band")
            or r["track"] in ("BASE", "CTRL")
            or (h.get("tip_ok") and h.get("cagr_giveback_pp") is not None and float(h["cagr_giveback_pp"]) <= 1.0 and float(h.get("max_drawdown") or -9) >= -0.16)
        ):
            continue
        lines.append(
            "| `{id}` | {track} | {cagr} | {mdd} | {band} | {gb} | {tok} | {ty} | {t1} |".format(
                id=r["id"],
                track=r["track"],
                cagr="n/a" if w.get("cagr") is None else f"{100*float(w['cagr']):.2f}%",
                mdd="n/a" if w.get("max_drawdown") is None else f"{100*float(w['max_drawdown']):.2f}%",
                band=h.get("in_band"),
                gb=h.get("cagr_giveback_pp"),
                tok=h.get("tip_ok"),
                ty=(tip.get("ytd") or {}).get("mdd_improve_pp"),
                t1=(tip.get("trailing_1y") or {}).get("mdd_improve_pp"),
            )
        )
    lines += [
        "",
        "## Reading",
        "",
        "- Stage B seeks tip-safe variants that preserve ~+0.56pp held giveback.",
        "- Soft-Frozen tip untouched; HIT → paper observe only.",
        "",
        f"Repro: `repro/held-mdd17-r2-tipsafe-fast-stageb/` · Charter: `{CHARTER_ID}`",
        "",
        f"Label: `{SCREEN_ID}_{summary['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    text = "\n".join(lines)
    (REP / "HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_SCREEN.md").write_text(text, encoding="utf-8")
    (OPS / "HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_SCREEN.md").write_text(text, encoding="utf-8")
    (REPRO / "README.md").write_text(
        "\n".join(
            [
                "# Tip-safe FAST Stage B repro",
                "",
                f"Verdict: **{verdict}**",
                "",
                "```bash",
                "PYTHONPATH=scripts python3 scripts/held_mdd17_r2_tipsafe_fast_stageb_screen.py",
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
