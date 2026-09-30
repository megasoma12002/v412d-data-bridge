#!/usr/bin/env python3
"""Research↔live gap attribution + alignment Stage A (0kar).

**Question:** Why Soft-core research NAVs diverge from live tip Soft, and what
protocol makes research books converge toward live (closer → consistent)?

Method
1. Build Exact T+1 tip Soft **layer ladder** (same Soft clips / KD / E22):
   - ``L1_SOFT_T1`` — Soft clips only (no FUSE sell amp, no COOL)
   - ``L2_SOFT_FUSE_T1`` — + FUSE ``SELL_a75``
   - ``L3_LIVE_FUSE_COOL`` — + COOL_c8 (reuse 0kap base)
   - ``L4_LIVE_P3_WITHIN`` — + Path3 WITHIN tip Soft (reuse 0kap)
2. Soft-core research books (reuse 0kao T+0):
   - ``R0_T0_P3_WITHIN`` / ``R1_T0_P3_P4_CASH_00025``
3. Attribute held/full/sealed/tip gaps of ``R0`` vs each live layer + layer deltas.

Soft KEEP · broker false · Path4 live OFF · no wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fin_sell_quality_helpers import cagr_lift_pp
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import mdd_delta_pp
from sleeve_tilt_helpers import ALPHA as LIVE_SLEEVE_ALPHA, sleeve_signal_panel
from soft_assist_helpers import (
    BUY_LOW_ID,
    LIVE_KD,
    SELL_HIGH_ID,
    soft_boost_scores,
    soft_sell_panel,
)
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "research-live-align-gap-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

SOFTCORE = ROOT / "repro" / "fin-sat-path3-path4-coexist-stagea" / "outputs"
LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"

CHARTER_ID = "RESEARCH_LIVE_ALIGN_GAP_STAGEA_CHARTER"
SCREEN_ID = "RESEARCH_LIVE_ALIGN_GAP_STAGEA_SCREEN"
DECISION_ID = "RESEARCH_LIVE_ALIGN_GAP_STAGEA_DECISION_PACK"
REGISTER = "0kar"
PARENTS = ("0kao", "0kap", "0kaq")

E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

# Soft-core research reference for gap attribution
RESEARCH_REF = "R0_T0_P3_WITHIN"


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
            out[wname] = {"cagr_lift_pp": None, "mdd_improve_pp": None}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        out[wname] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(bc, cc) is None
            else round(float(cagr_lift_pp(bc, cc)), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
        }
    return out


def _delta(base_w: dict, chal_w: dict) -> dict[str, Any]:
    out = {}
    for k in ("full", "heldout_2019_plus", "sealed_2023_plus"):
        b, c = base_w.get(k) or {}, chal_w.get(k) or {}
        out[k] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(b.get("cagr"), c.get("cagr")) is None
            else round(float(cagr_lift_pp(b.get("cagr"), c.get("cagr"))), 4),
            "mdd_improve_pp": None
            if b.get("max_drawdown") is None or c.get("max_drawdown") is None
            else round(float(mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])), 4),
            "base_cagr": b.get("cagr"),
            "chal_cagr": c.get("cagr"),
            "base_mdd": b.get("max_drawdown"),
            "chal_mdd": c.get("max_drawdown"),
        }
    return out


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return df[["date", "nav"]].sort_values("date").reset_index(drop=True)


def _buy(kd, lows, k9_amp: float = 1.0) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], float(k9_amp))


def _sell(highs, amp: float) -> pd.DataFrame:
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=float(amp))


def _sleeve_score(market, sleeve, alpha: float) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    return base_score + float(alpha) * tilt


def _target_live(score, regime):
    return clip.build_targets_with_clips(
        regime=regime,
        score=score,
        fin_lo=float(soft.SOFT_FROZEN_FIN_LO),
        fin_hi=float(soft.SOFT_FROZEN_FIN_HI),
        tel_lo=float(soft.SOFT_FROZEN_TEL_LO),
        tel_hi=float(soft.SOFT_FROZEN_TEL_HI),
        etf_lo=float(soft.SOFT_FROZEN_ETF_LO),
        etf_hi=float(soft.SOFT_FROZEN_ETF_HI),
    )


def _cool_from_offense(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def _sim(market, target, regime, dividends, *, scores, buy_ok, sell=None, exposure=None):
    kw: dict[str, Any] = {
        "apply_e22": True,
        "apply_stock_div": True,
        "capital": float(DEFAULT_CAPITAL),
        "lot_size": int(BOARD_LOT),
        "financial_alloc": FIN_PRE_EXDIV_KD,
        "telecom_alloc": TEL_EQUAL,
        "fin_name_scores": scores,
        "fin_buy_ok": buy_ok,
        "e22_version": E22_VERSION,
    }
    if sell is not None:
        kw["fin_sell_scores"] = sell
    if exposure is not None:
        kw["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kw)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def _gap_row(name: str, research_w: dict, other_w: dict, tip: dict, meta: dict) -> dict:
    d = _delta(research_w, other_w)
    return {
        "compare": name,
        "held_cagr_lift_pp": d["heldout_2019_plus"]["cagr_lift_pp"],
        "full_cagr_lift_pp": d["full"]["cagr_lift_pp"],
        "sealed_mdd_improve_pp": d["sealed_2023_plus"]["mdd_improve_pp"],
        "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
        "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
        "research_held_cagr": d["heldout_2019_plus"]["base_cagr"],
        "other_held_cagr": d["heldout_2019_plus"]["chal_cagr"],
        "research_held_mdd": d["heldout_2019_plus"]["base_mdd"],
        "other_held_mdd": d["heldout_2019_plus"]["chal_mdd"],
        **{f"meta_{k}": v for k, v in meta.items()},
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert abs(SELL_AMP - 0.75) < 1e-12

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, sleeve, _t, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(market["date"].unique())))
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market,
        dividends,
        list(FIN),
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, list(FIN), pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    scores = _buy(kd, lows)
    sell_fuse = _sell(highs, SELL_AMP)
    sleeve_sc = _sleeve_score(market, sleeve, LIVE_SLEEVE_ALPHA)
    target = _target_live(sleeve_sc, regime)

    arms: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict[str, Any]] = {}

    print("L1_SOFT_T1 (clips only, no FUSE/COOL) ...", flush=True)
    nav_l1, fills_l1, _m = _sim(
        market, target, regime, dividends, scores=scores, buy_ok=buy_ok
    )
    nav_l1.to_csv(OUT / "nav_L1_SOFT_T1.csv", index=False)
    arms["L1_SOFT_T1"] = nav_l1
    metas["L1_SOFT_T1"] = {
        "layer": 1,
        "fill_timing": "exact_t1",
        "fuse": False,
        "cool": False,
        "path3": False,
        "n_fills": int(len(fills_l1)),
    }

    print("L2_SOFT_FUSE_T1 (+SELL_a75, no COOL) ...", flush=True)
    nav_l2, fills_l2, _m = _sim(
        market,
        target,
        regime,
        dividends,
        scores=scores,
        buy_ok=buy_ok,
        sell=sell_fuse,
    )
    nav_l2.to_csv(OUT / "nav_L2_SOFT_FUSE_T1.csv", index=False)
    arms["L2_SOFT_FUSE_T1"] = nav_l2
    metas["L2_SOFT_FUSE_T1"] = {
        "layer": 2,
        "fill_timing": "exact_t1",
        "fuse": True,
        "cool": False,
        "path3": False,
        "n_fills": int(len(fills_l2)),
    }

    # L3/L4 reuse 0kap
    for arm, path, layer, extra in (
        (
            "L3_LIVE_FUSE_COOL",
            LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv",
            3,
            {"fuse": True, "cool": True, "path3": False},
        ),
        (
            "L4_LIVE_P3_WITHIN",
            LIVESTACK / "nav_LIVE_P3_WITHIN.csv",
            4,
            {"fuse": True, "cool": True, "path3": True},
        ),
    ):
        if not path.exists():
            raise FileNotFoundError(path)
        nav = _load_nav(path)
        nav.to_csv(OUT / f"nav_{arm}.csv", index=False)
        arms[arm] = nav
        metas[arm] = {
            "layer": layer,
            "fill_timing": "exact_t1",
            "reuse": "0kap",
            **extra,
        }

    # Research Soft-core T+0
    for arm, src, extra in (
        (
            "R0_T0_P3_WITHIN",
            SOFTCORE / "nav_REF_P3_WITHIN.csv",
            {"path3": True, "path4": False},
        ),
        (
            "R1_T0_P3_P4_CASH_00025",
            SOFTCORE / "nav_P3_P4_CASH_00025.csv",
            {"path3": True, "path4": True},
        ),
    ):
        if not src.exists():
            raise FileNotFoundError(src)
        nav = _load_nav(src)
        nav.to_csv(OUT / f"nav_{arm}.csv", index=False)
        arms[arm] = nav
        metas[arm] = {
            "layer": 0,
            "fill_timing": "t0",
            "book": "softcore_carve",
            "reuse": "0kao",
            "fuse": False,
            "cool": False,
            **extra,
        }

    packs = {k: _pack(v) for k, v in arms.items()}
    research = arms[RESEARCH_REF]
    research_w = packs[RESEARCH_REF]

    # Gap: research Soft-core T0 P3 vs each tip Soft layer (chal − research)
    gap_vs_research = []
    for arm in (
        "L1_SOFT_T1",
        "L2_SOFT_FUSE_T1",
        "L3_LIVE_FUSE_COOL",
        "L4_LIVE_P3_WITHIN",
        "R1_T0_P3_P4_CASH_00025",
    ):
        tip = _tip(research, arms[arm])
        gap_vs_research.append(
            _gap_row(
                f"{arm}_minus_{RESEARCH_REF}",
                research_w,
                packs[arm],
                tip,
                metas[arm],
            )
        )

    # Layer increments on tip Soft ladder (L2−L1, L3−L2, L4−L3)
    layer_deltas = []
    ladder = [
        ("L1_SOFT_T1", "L2_SOFT_FUSE_T1", "+FUSE_SELL_a75"),
        ("L2_SOFT_FUSE_T1", "L3_LIVE_FUSE_COOL", "+COOL_c8"),
        ("L3_LIVE_FUSE_COOL", "L4_LIVE_P3_WITHIN", "+Path3_WITHIN_tipSoft"),
    ]
    for base_a, chal_a, label in ladder:
        tip = _tip(arms[base_a], arms[chal_a])
        d = _delta(packs[base_a], packs[chal_a])
        layer_deltas.append(
            {
                "step": label,
                "from": base_a,
                "to": chal_a,
                "held_cagr_lift_pp": d["heldout_2019_plus"]["cagr_lift_pp"],
                "full_cagr_lift_pp": d["full"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": d["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
            }
        )

    # Absolute window prints for all arms (for SSOT)
    abs_rows = []
    for arm, w in packs.items():
        abs_rows.append(
            {
                "arm": arm,
                "held_cagr": (w.get("heldout_2019_plus") or {}).get("cagr"),
                "held_mdd": (w.get("heldout_2019_plus") or {}).get("max_drawdown"),
                "full_cagr": (w.get("full") or {}).get("cagr"),
                "sealed_mdd": (w.get("sealed_2023_plus") or {}).get("max_drawdown"),
                **metas.get(arm, {}),
            }
        )

    pd.DataFrame(gap_vs_research).to_csv(OUT / "gap_vs_research_r0.csv", index=False)
    pd.DataFrame(layer_deltas).to_csv(OUT / "tipsoft_layer_deltas.csv", index=False)
    pd.DataFrame(abs_rows).to_csv(OUT / "absolute_windows.csv", index=False)

    # Dominant gap drivers: largest |held| move from research → L3 (live base)
    g_l3 = next(g for g in gap_vs_research if g["compare"].startswith("L3_"))
    g_l1 = next(g for g in gap_vs_research if g["compare"].startswith("L1_"))
    g_l4 = next(g for g in gap_vs_research if g["compare"].startswith("L4_"))

    # Attribution narrative from layer deltas
    step_by_abs = sorted(
        layer_deltas,
        key=lambda r: abs(float(r["held_cagr_lift_pp"] or 0)),
        reverse=True,
    )
    top_step = step_by_abs[0] if step_by_abs else None

    # Alignment protocol (actionable)
    protocol = [
        {
            "id": "P1_DUAL_TRACK",
            "rule": "Every promote-candidate mechanism ships Soft-core carve AND tip Soft twin in the same decision pack",
            "closes": "Soft-core HIT alone cannot promote",
        },
        {
            "id": "P2_CLOCK_SSOT",
            "rule": "tip Soft twin fill timing must match live carve (P3/P4 → Exact T+0; Soft elsewhere Exact T+1)",
            "closes": "T+0 research vs T+1 live clock mismatch",
        },
        {
            "id": "P3_OVERLAY_FREEZE",
            "rule": "tip Soft twin freezes live COOL_c8 + FUSE SELL_a75 + Soft clips from live_config",
            "closes": "missing COOL/FUSE in research books",
        },
        {
            "id": "P4_LAYER_LADDER",
            "rule": "Before ACCEPT, publish Soft→FUSE→COOL→mech layer deltas (this Stage A template)",
            "closes": "unknown which overlay creates research↔live gap",
        },
        {
            "id": "P5_GAP_GATE",
            "rule": "Report held/tip/sealed gap of Soft-core vs L3_LIVE_FUSE_COOL; promote only if tip Soft twin clears gates",
            "closes": "large silent divergence",
        },
        {
            "id": "P6_NO_CROSS_BASE",
            "rule": "Do not score Soft-core T+0 absolute CAGR against Exact T+1 live base for HIT/STOP — use within-track deltas",
            "closes": "apples-to-oranges MDD_BLOCK from book mismatch",
        },
    ]

    # Verdict: alignment path readiness
    # Dominant gap magnitude research→live base
    held_gap_l3 = float(g_l3["held_cagr_lift_pp"] or 0)
    if abs(held_gap_l3) < 0.5:
        pack_verdict = "ALIGN_NEAR"
    elif abs(held_gap_l3) < 2.0:
        pack_verdict = "ALIGN_GAP_MODERATE"
    else:
        pack_verdict = "ALIGN_GAP_LARGE"

    recommendations = [
        f"Research Soft-core `{RESEARCH_REF}` vs live `L3_LIVE_FUSE_COOL` held gap = "
        f"**{held_gap_l3:+.2f}** pp (tipY {(g_l3.get('tip_ytd_cagr_lift_pp'))}) → `{pack_verdict}`",
        f"Vs tip Soft Soft-only `L1_SOFT_T1` held gap = "
        f"**{float(g_l1['held_cagr_lift_pp'] or 0):+.2f}** pp — clock/book still diverge even without FUSE/COOL",
        f"Vs tip Soft +P3 `L4_LIVE_P3_WITHIN` held gap = "
        f"**{float(g_l4['held_cagr_lift_pp'] or 0):+.2f}** pp",
    ]
    if top_step:
        recommendations.append(
            f"Largest tip Soft layer step: `{top_step['step']}` held "
            f"{top_step['held_cagr_lift_pp']} / sealedMDD {top_step['sealed_mdd_improve_pp']} / "
            f"tipY {top_step['tip_ytd_cagr_lift_pp']}"
        )
    recommendations.extend(
        [
            "Adopt protocol P1–P6 as research↔live alignment SSOT (see decision pack)",
            "Next implementable fix: tip Soft hybrid runner (Soft Exact T+1 overlays + P3/P4 Exact T+0 carve) as default twin template",
            "Soft KEEP · broker false · Path4 live OFF · no wire this pack",
        ]
    )

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": "RESEARCH_LIVE_ALIGN_GAP",
        "verdict": pack_verdict,
        "research_ref": RESEARCH_REF,
        "live_base": "L3_LIVE_FUSE_COOL",
        "held_gap_research_to_live_pp": held_gap_l3,
        "gap_vs_research": gap_vs_research,
        "tipsoft_layer_deltas": layer_deltas,
        "absolute_windows": abs_rows,
        "alignment_protocol": protocol,
        "recommendations": recommendations,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, default=str) + "\n")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage A — research↔live gap attribution + alignment protocol**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "How do we shrink Soft-core research vs live tip Soft divergence toward "
            "closer / consistent promote decisions?",
            "",
            "## Method",
            "",
            "- Tip Soft layer ladder: Soft → +FUSE → +COOL → +P3",
            "- Soft-core T+0 research refs from 0kao",
            "- Gap table + layer deltas + alignment protocol P1–P6",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__ALIGN_GAP`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter"
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "mech": "RESEARCH_LIVE_ALIGN_GAP",
            },
            indent=2,
        )
        + "\n"
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    def _fmt_gap(g: dict) -> str:
        return (
            f"| {g['compare']} | {g['held_cagr_lift_pp']} | {g['full_cagr_lift_pp']} | "
            f"{g['sealed_mdd_improve_pp']} | {g['tip_ytd_cagr_lift_pp']} | "
            f"{g['tip_1y_cagr_lift_pp']} |"
        )

    def _fmt_step(s: dict) -> str:
        return (
            f"| {s['step']} | {s['held_cagr_lift_pp']} | {s['full_cagr_lift_pp']} | "
            f"{s['sealed_mdd_improve_pp']} | {s['tip_ytd_cagr_lift_pp']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"held gap research→live = **{held_gap_l3:+.2f}** pp",
            f"Register: **{REGISTER}** · research=`{RESEARCH_REF}` · live=`L3_LIVE_FUSE_COOL`",
            "",
            "## Gap: tip Soft / Path4 arm **minus** Soft-core research R0",
            "",
            "| Compare | held | full | sealed MDD↑ | tipY | tip1y |",
            "|---|---:|---:|---:|---:|---:|",
            *[_fmt_gap(g) for g in gap_vs_research],
            "",
            "## Tip Soft layer ladder deltas",
            "",
            "| Step | held | full | sealed MDD↑ | tipY |",
            "|---|---:|---:|---:|---:|",
            *[_fmt_step(s) for s in layer_deltas],
            "",
            "## Recommendations",
            "",
            *[f"{i+1}. {r}" for i, r in enumerate(recommendations)],
            "",
            "Repro: `PYTHONPATH=scripts python3 "
            "scripts/research_live_align_gap_stagea.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{pack_verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(screen, indent=2, default=str) + "\n"
    )
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{pack_verdict}__NO_LIVE",
        "verdict": pack_verdict,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": "RESEARCH_LIVE_ALIGN_GAP",
        "held_gap_research_to_live_pp": held_gap_l3,
        "alignment_protocol": protocol,
        "recommendations": recommendations,
        "soft_keep": True,
        "broker": False,
        "path4_live": False,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`**",
            f"Register: **{REGISTER}** · held gap Soft-core→live = **{held_gap_l3:+.2f}** pp",
            "",
            "## How to make research ≈ live",
            "",
            *[f"{i+1}. {r}" for i, r in enumerate(recommendations)],
            "",
            "## Alignment protocol (SSOT)",
            "",
            *[f"- **{p['id']}**: {p['rule']} _(closes: {p['closes']})_" for p in protocol],
            "",
            "## Disposition",
            "",
            "- Adopt P1–P6 for future P3/P4 / overlay paper.",
            "- Soft KEEP · broker false · Path4 live OFF · no wire.",
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="decision pack",
    )
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    print(
        json.dumps(
            {
                "verdict": pack_verdict,
                "held_gap_research_to_live_pp": held_gap_l3,
                "layer_deltas": layer_deltas,
                "gap_vs_research_held": {
                    g["compare"]: g["held_cagr_lift_pp"] for g in gap_vs_research
                },
                "recommendations": recommendations,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
