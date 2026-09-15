#!/usr/bin/env python3
"""Live + DH_dd06 ± Soft/Sleeve/FUSE combo NAV trial (PAPER ONLY).

Menus vs LIVE Soft-Frozen + KD_OPT + TEL_EQUAL:
  1) MENU1_DH_ONLY              = LIVE + DH_dd06
  2) MENU2_DH_SOFT_SLEEVE_INDEP = 50/50 (Soft+DH) || (Sleeve+DH)
  3) MENU3_DH_FUSE              = FUSE_ADDITIVE + DH_dd06

No live wire · no E45 stitch · no Soft||Sleeve ops auto-fuse.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e16_soft_frozen_base as soft
import e21_forward_pipeline as e21
import e45_defend_handoff_stagea_screen as stagea
from e45_defend_handoff_helpers import DD_THRESHOLD, SHRINK, VOL_Z_THRESHOLD
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fuse_additive_helpers import (
    LIVE_KD,
    build_champion_target,
    build_observe_buy_scores,
    build_observe_sell_panel,
)
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import ALPHA as SLEEVE_ALPHA
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/dh-observe-combo-nav-trial"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = int(BOARD_LOT)
FOCUS = ("full", "heldout_2019_plus", "sealed_2023_plus")


def run_book(market, target, regime, dividends, *, scores, buy_ok, sell_scores=None, exposure=None):
    kwargs = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell_scores,
    )
    if exposure is not None:
        kwargs["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kwargs)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return {"nav": nav, "n_fills": int(len(fills)), "meta": meta}


def make_dh_exposure(market, offense_nav):
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return stagea._build_exposure(dates, feat, DD_THRESHOLD, VOL_Z_THRESHOLD)


def blend_eq(nav_a, nav_b):
    a = nav_a[["date", "nav"]].rename(columns={"nav": "a"})
    b = nav_b[["date", "nav"]].rename(columns={"nav": "b"})
    j = a.merge(b, on="date", how="inner").sort_values("date").reset_index(drop=True)
    r = 0.5 * j["a"].pct_change().fillna(0.0) + 0.5 * j["b"].pct_change().fillna(0.0)
    nav = (1.0 + r).cumprod()
    nav = nav / float(nav.iloc[0])
    return pd.DataFrame({"date": j["date"], "nav": nav})


def pack_windows(nav):
    out = {}
    for k, (a, b) in WINDOWS_STANDARD.items():
        st = window_stats(nav, a, b)
        out[k] = {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None if st.get("max_drawdown") is None else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
    return out


def vs_live(base_w, chal_w, key):
    b, c = base_w[key], chal_w[key]
    gb = cagr_delta_pp(b.get("cagr"), c.get("cagr"), missing_as_zero=True)
    md = mdd_delta_pp(b.get("max_drawdown"), c.get("max_drawdown"))
    return {
        "base_cagr": b.get("cagr"),
        "chal_cagr": c.get("cagr"),
        "base_mdd": b.get("max_drawdown"),
        "chal_mdd": c.get("max_drawdown"),
        "cagr_delta_pp": None if gb is None else round(float(gb), 4),
        "mdd_improve_pp": round(float(md), 4),
        "score": round(float(md) - 0.5 * abs(float(gb or 0.0)), 4),
    }


def fmt_pct(x):
    return "n/a" if x is None else f"{100.0 * float(x):.2f}%"


def fmt_pp(x):
    return "n/a" if x is None else f"{float(x):+.2f}pp"


def main() -> int:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse while LIVE_E45_STITCH is True")

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, sleeve, target_live, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))

    kd_scores = build_kd_season_tilt_scores(
        market, dividends, FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    kd_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    soft_buy = build_observe_buy_scores(kd_scores, lows)
    soft_sell = build_observe_sell_panel(highs)
    target_sleeve = build_champion_target(market, sleeve, regime)

    books = {}

    print("LIVE_STACK ...", flush=True)
    live = run_book(market, target_live, regime, dividends, scores=kd_scores, buy_ok=kd_ok)
    books["LIVE_STACK"] = live

    print("1 MENU1 LIVE+DH ...", flush=True)
    exp_live = make_dh_exposure(market, live["nav"])
    books["MENU1_DH_ONLY"] = run_book(
        market, target_live, regime, dividends, scores=kd_scores, buy_ok=kd_ok, exposure=exp_live
    )

    print("SOFT + SOFT_DH ...", flush=True)
    soft_off = run_book(
        market, target_live, regime, dividends, scores=soft_buy, buy_ok=kd_ok, sell_scores=soft_sell
    )
    exp_soft = make_dh_exposure(market, soft_off["nav"])
    soft_dh = run_book(
        market, target_live, regime, dividends,
        scores=soft_buy, buy_ok=kd_ok, sell_scores=soft_sell, exposure=exp_soft,
    )
    books["SOFT_ONLY"] = soft_off
    books["SOFT_DH"] = soft_dh

    print("SLEEVE + SLEEVE_DH ...", flush=True)
    sleeve_off = run_book(market, target_sleeve, regime, dividends, scores=kd_scores, buy_ok=kd_ok)
    exp_sleeve = make_dh_exposure(market, sleeve_off["nav"])
    sleeve_dh = run_book(
        market, target_sleeve, regime, dividends, scores=kd_scores, buy_ok=kd_ok, exposure=exp_sleeve
    )
    books["SLEEVE_ONLY"] = sleeve_off
    books["SLEEVE_DH"] = sleeve_dh

    print("2 MENU2 50/50 Soft+DH || Sleeve+DH ...", flush=True)
    books["MENU2_DH_SOFT_SLEEVE_INDEP"] = {
        "nav": blend_eq(soft_dh["nav"], sleeve_dh["nav"]),
        "n_fills": None,
    }

    print("FUSE + 3 MENU3 FUSE+DH ...", flush=True)
    fuse_off = run_book(
        market, target_sleeve, regime, dividends,
        scores=soft_buy, buy_ok=kd_ok, sell_scores=soft_sell,
    )
    exp_fuse = make_dh_exposure(market, fuse_off["nav"])
    fuse_dh = run_book(
        market, target_sleeve, regime, dividends,
        scores=soft_buy, buy_ok=kd_ok, sell_scores=soft_sell, exposure=exp_fuse,
    )
    books["FUSE_ONLY"] = fuse_off
    books["MENU3_DH_FUSE"] = fuse_dh

    for name, book in books.items():
        book["nav"].to_csv(OUT / "outputs" / f"nav_{name}.csv", index=False)
    for tag, exp in (("LIVE_DH", exp_live), ("SOFT_DH", exp_soft), ("SLEEVE_DH", exp_sleeve), ("FUSE_DH", exp_fuse)):
        exp.rename("e45_exposure").to_frame().to_csv(OUT / "outputs" / f"exposure_{tag}.csv")

    win = {name: pack_windows(book["nav"]) for name, book in books.items()}
    base_w = win["LIVE_STACK"]
    menu_ids = [
        "MENU1_DH_ONLY", "MENU2_DH_SOFT_SLEEVE_INDEP", "MENU3_DH_FUSE",
        "SOFT_DH", "SLEEVE_DH", "SOFT_ONLY", "SLEEVE_ONLY", "FUSE_ONLY",
    ]
    compare = {mid: {w: vs_live(base_w, win[mid], w) for w in FOCUS} for mid in menu_ids}

    payload = {
        "label": "DH_OBSERVE_COMBO_NAV_TRIAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_DIAGNOSE_ONLY",
        "live_wire": False,
        "stitch_authorized": False,
        "soft_frozen_clips": [0.6, 0.9],
        "dh_recipe": {
            "dd_threshold": DD_THRESHOLD,
            "vol_z_threshold": VOL_Z_THRESHOLD,
            "shrink": SHRINK,
            "exposure_from": "each offense book's own pass-1 NAV",
        },
        "menus": {
            "1_MENU1_DH_ONLY": "LIVE_STACK + DH_dd06",
            "2_MENU2_DH_SOFT_SLEEVE_INDEP": "50/50 Soft+DH || Sleeve+DH",
            "3_MENU3_DH_FUSE": f"FUSE_ADDITIVE + DH_dd06 (Soft softs + Sleeve RSI14 a={SLEEVE_ALPHA})",
        },
        "notes": [
            "FUSE already embeds Soft+Sleeve; Soft+Sleeve+FUSE is not a third layer.",
            "FINCAP BLEND_025 omitted (separate twin; DH stack needs dedicated charter).",
            "No Soft||Sleeve ops auto-fuse · no live cutover · no E45 stitch.",
        ],
        "windows": win,
        "vs_live": compare,
        "mean_exposure": {
            "LIVE_DH": float(exp_live.mean()),
            "SOFT_DH": float(exp_soft.mean()),
            "SLEEVE_DH": float(exp_sleeve.mean()),
            "FUSE_DH": float(exp_fuse.mean()),
            "frac_defense_LIVE": float((exp_live < 0.999).mean()),
            "frac_defense_SOFT": float((exp_soft < 0.999).mean()),
            "frac_defense_SLEEVE": float((exp_sleeve < 0.999).mean()),
            "frac_defense_FUSE": float((exp_fuse < 0.999).mean()),
        },
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    (OUT / "outputs" / "dh_observe_combo_summary.json").write_text(text, encoding="utf-8")
    (OPS / "DH_OBSERVE_COMBO_NAV_TRIAL.json").write_text(text, encoding="utf-8")

    order = [
        "LIVE_STACK", "MENU1_DH_ONLY", "MENU2_DH_SOFT_SLEEVE_INDEP", "MENU3_DH_FUSE",
        "SOFT_DH", "SLEEVE_DH", "SOFT_ONLY", "SLEEVE_ONLY", "FUSE_ONLY",
    ]
    lines = [
        "# DH + Selective Observe Combo NAV Trial (PAPER ONLY)",
        "",
        f"Generated: `{payload['generated_at_utc']}`  ",
        "Base: Soft-Frozen FIN[0.60,0.90] + KD_OPT + TEL_EQUAL · E45 OFF  ",
        "DH: `DH_dd06` (dd=6%, vz=1.0, shrink=0.50) · exposure from each offense NAV  ",
        "Status: **PAPER DIAGNOSE ONLY** · no live wire · no stitch · no Soft||Sleeve auto-fuse",
        "",
        "## Menus",
        "",
        "| # | ID | Construction |",
        "|---|---|---|",
        "| 1 | `MENU1_DH_ONLY` | LIVE + DH |",
        "| 2 | `MENU2_DH_SOFT_SLEEVE_INDEP` | 50/50 Soft+DH || Sleeve+DH |",
        "| 3 | `MENU3_DH_FUSE` | FUSE_ADDITIVE + DH (= Soft+Sleeve joint + DH) |",
        "",
        "Note: Soft+Sleeve+FUSE is **not** three layers — FUSE **is** Soft+Sleeve. FINCAP BLEND_025 omitted.",
        "",
        "## Held-out 2019+ (primary)",
        "",
        "| book | CAGR | MDD | vs LIVE CAGR | MDD improve | score |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in order:
        w = win[name]["heldout_2019_plus"]
        if name == "LIVE_STACK":
            lines.append(f"| `{name}` | {fmt_pct(w['cagr'])} | {fmt_pct(w['max_drawdown'])} | — | — | — |")
        else:
            v = compare[name]["heldout_2019_plus"]
            lines.append(
                f"| `{name}` | {fmt_pct(w['cagr'])} | {fmt_pct(w['max_drawdown'])} | "
                f"{fmt_pp(v['cagr_delta_pp'])} | {fmt_pp(v['mdd_improve_pp'])} | {v['score']:+.2f} |"
            )
    for title, key in (("Full sample", "full"), ("Sealed 2023+", "sealed_2023_plus")):
        lines += ["", f"## {title}", "", "| book | CAGR | MDD | vs LIVE CAGR | MDD improve |", "|---|---:|---:|---:|---:|"]
        for name in order:
            w = win[name][key]
            if name == "LIVE_STACK":
                lines.append(f"| `{name}` | {fmt_pct(w['cagr'])} | {fmt_pct(w['max_drawdown'])} | — | — |")
            else:
                v = compare[name][key]
                lines.append(
                    f"| `{name}` | {fmt_pct(w['cagr'])} | {fmt_pct(w['max_drawdown'])} | "
                    f"{fmt_pp(v['cagr_delta_pp'])} | {fmt_pp(v['mdd_improve_pp'])} |"
                )
    lines += [
        "",
        "## Reading",
        "",
        "- **1 DH only**: primary MDD lever on Live.",
        "- **2 Soft||Sleeve + DH (50/50)**: DH dominates; Soft/Sleeve add small independent tilt.",
        "- **3 FUSE + DH**: Soft+Sleeve on one book then DH — compare to menu 2.",
        "- Tip / promote / live wire: **out of scope**.",
        "",
        "## Label",
        "",
        "`DH_OBSERVE_COMBO_NAV_TRIAL_2026-09-13__PAPER_ONLY__NO_LIVE_WIRE`",
        "",
    ]
    report = "\n".join(lines) + "\n"
    (OUT / "reports" / "DH_OBSERVE_COMBO_NAV_TRIAL.md").write_text(report, encoding="utf-8")
    (OPS / "DH_OBSERVE_COMBO_NAV_TRIAL.md").write_text(report, encoding="utf-8")

    print("\n=== DH observe combo trial (PAPER ONLY) ===")
    print(f"wrote {OPS / 'DH_OBSERVE_COMBO_NAV_TRIAL.md'}")
    print(f"{'book':32s} {'held CAGR':>10s} {'held MDD':>10s} {'dCAGR':>9s} {'MDDup':>8s}")
    for name in ["LIVE_STACK", "MENU1_DH_ONLY", "MENU2_DH_SOFT_SLEEVE_INDEP", "MENU3_DH_FUSE"]:
        w = win[name]["heldout_2019_plus"]
        if name == "LIVE_STACK":
            print(f"{name:32s} {fmt_pct(w['cagr']):>10s} {fmt_pct(w['max_drawdown']):>10s} {'—':>9s} {'—':>8s}")
        else:
            v = compare[name]["heldout_2019_plus"]
            print(
                f"{name:32s} {fmt_pct(w['cagr']):>10s} {fmt_pct(w['max_drawdown']):>10s} "
                f"{fmt_pp(v['cagr_delta_pp']):>9s} {fmt_pp(v['mdd_improve_pp']):>8s}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
