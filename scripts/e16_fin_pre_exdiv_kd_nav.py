#!/usr/bin/env python3
"""FIN_PRE_EXDIV_KD sleeve — Exact T+1 paper NAV vs FIN_EQUAL (RESEARCH ONLY).

Rule (Yahoo K9/D9 chart params):
  - May15–Jun10: first K9 < 25 → accumulate / soft-tilt that name
  - Cash-ex T-10..T0 (+ stock ex day): skip buy that name
  - Else: near-equal among buy-ok names

Soft-Frozen KEEP · live e21 untouched · capital 500M · lot 1000.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, deltas_vs_base, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_MIX_EQUAL_RS_EXDIV,
    FIN_PRE_EXDIV_KD,
    FIN_RS_SOFT_TILT_EXDIV,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_kd_season_tilt_scores,
    build_name_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-pre-exdiv-kd-nav-20260909"
RESEARCH = ROOT / "research/ops"

CHARTER_CAPITAL = 500_000_000.0
CHARTER_LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
K_THRESH = 25.0
PRE_DAYS = 10


def tip_gate(base_nav: pd.DataFrame, chal_nav: pd.DataFrame, asof: pd.Timestamp) -> dict:
    out = {}
    asof = pd.Timestamp(asof)
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"giveback_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"] / float(b["nav"].iloc[0])
        cn = c["nav"] / float(c["nav"].iloc[0])
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = None if bc is None or cc is None else (bc - cc) * 100
        gate = "PASS"
        if gb is not None and gb > TRAIL_PAUSE_PP:
            gate = "PAUSE_REVIEW"
        elif gb is not None and gb > TRAIL_ALERT_PP:
            gate = "ALERT"
        out[wname] = {
            "giveback_pp": None if gb is None else float(gb),
            "gate": gate,
            "rel_nav": float(cn.iloc[-1] / bn.iloc[-1]),
            "base_total_ret": float(bn.iloc[-1] - 1),
            "chal_total_ret": float(cn.iloc[-1] - 1),
        }
    return out


def score_vs_base(base_stats: dict, chal_stats: dict) -> dict:
    mdd_pp = mdd_delta_pp(base_stats.get("max_drawdown"), chal_stats.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(
        base_stats.get("cagr"), chal_stats.get("cagr"), missing_as_zero=True
    )
    giveback = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd_pp),
        "cagr_giveback_pp": float(cagr_pp) if cagr_pp is not None else None,
        "score": float(mdd_pp) - 0.5 * giveback,
    }


def run_book(market, dividends, target, regime, *, policy, fin_scores, fin_buy_ok, mix_lam=None):
    return simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CHARTER_CAPITAL,
        lot_size=CHARTER_LOT,
        financial_alloc=policy,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=fin_scores,
        fin_buy_ok=fin_buy_ok,
        fin_mix_lambda=mix_lam,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.5, 0.95]

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()

    print("building KD season scores + pre-ex buy_ok ...", flush=True)
    kd_scores = build_kd_season_tilt_scores(
        market, dividends, FIN, k_thresh=K_THRESH, pre_days=PRE_DAYS
    )
    pre_buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=PRE_DAYS, also_stock_ex=True
    )
    # companions for context
    rs_scores = build_name_scores(market, FIN)
    rs_buy_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)

    books = {}
    specs = [
        ("FIN_EQUAL", FIN_EQUAL, None, None, None),
        ("FIN_PRE_EXDIV_KD", FIN_PRE_EXDIV_KD, kd_scores, pre_buy_ok, None),
        ("FIN_RS_SOFT_TILT_EXDIV", FIN_RS_SOFT_TILT_EXDIV, rs_scores, rs_buy_ok, None),
        ("MIX_L75", FIN_MIX_EQUAL_RS_EXDIV, rs_scores, rs_buy_ok, 0.75),
    ]
    for label, policy, scores, buy_ok, mix in specs:
        print(f"  sim {label} ...", flush=True)
        nav, fills, meta = run_book(
            market,
            dividends,
            target,
            regime,
            policy=policy,
            fin_scores=scores,
            fin_buy_ok=buy_ok,
            mix_lam=mix,
        )
        assert meta.get("exact_t1_ok"), label
        qty = pd.to_numeric(fills["quantity"], errors="coerce") if len(fills) else pd.Series(dtype=float)
        assert len(qty) == 0 or ((qty % CHARTER_LOT == 0) & (qty >= CHARTER_LOT)).all()
        slug = label.lower()
        nav.to_csv(OUT / "outputs" / f"{slug}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{slug}_fills.csv", index=False)
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        books[label] = {"nav": nav, "meta": meta, "windows": win, "n_fills": int(len(fills))}

    base = books["FIN_EQUAL"]
    asof = pd.to_datetime(base["nav"]["date"]).max()
    ranked = []
    for label, book in books.items():
        if label == "FIN_EQUAL":
            continue
        held = score_vs_base(base["windows"]["heldout_2019_plus"], book["windows"]["heldout_2019_plus"])
        sealed = score_vs_base(base["windows"]["sealed_2023_plus"], book["windows"]["sealed_2023_plus"])
        tip = tip_gate(base["nav"], book["nav"], asof)
        tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
        row = {
            "id": label,
            "n_fills": book["n_fills"],
            "exact_t1_ok": bool(book["meta"].get("exact_t1_ok")),
            "windows": book["windows"],
            "scores": {
                "heldout_2019_plus": held,
                "sealed_2023_plus_REPORT_ONLY": sealed,
            },
            "tip_gates": tip,
            "tip_clean": tip_clean,
        }
        ranked.append(row)

    ranked.sort(key=lambda r: r["scores"]["heldout_2019_plus"]["score"], reverse=True)
    primary = next(r for r in ranked if r["id"] == "FIN_PRE_EXDIV_KD")

    # nav compare
    jb = base["nav"][["date", "nav"]].rename(columns={"nav": "nav_base"})
    for label in ("FIN_PRE_EXDIV_KD", "FIN_RS_SOFT_TILT_EXDIV", "MIX_L75"):
        jc = books[label]["nav"][["date", "nav"]].rename(columns={"nav": f"nav_{label.lower()}"})
        jb = jb.merge(jc, on="date", how="inner")
    jb.to_csv(OUT / "outputs" / "nav_compare.csv", index=False)

    # KD score coverage
    active_days = {
        c: int((kd_scores[c] > 0).sum()) for c in FIN if c in kd_scores.columns
    }
    skip_days = {
        c: int((~pre_buy_ok[c]).sum()) for c in FIN if c in pre_buy_ok.columns
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_PRE_EXDIV_KD_NAV",
        "status": "PAPER_NAV_SCREEN",
        "live_wire": False,
        "soft_frozen_keep": True,
        "cutover_authorized": False,
        "rule": {
            "id": FIN_PRE_EXDIV_KD,
            "kd": "Yahoo K9/D9 recursive",
            "k_thresh": K_THRESH,
            "season": "May15-Jun10 first K<25 → soft-tilt accumulate",
            "pre_ex_skip": f"cash-ex T-{PRE_DAYS}..T0 + stock ex day",
            "active_score": 1.5,
        },
        "execution_context": {
            "capital": CHARTER_CAPITAL,
            "board_lot": CHARTER_LOT,
            "telecom_held_at": TEL_EQUAL,
        },
        "coverage": {"kd_active_days": active_days, "pre_ex_skip_days": skip_days},
        "primary_vs_equal": {
            "heldout": primary["scores"]["heldout_2019_plus"],
            "sealed_REPORT_ONLY": primary["scores"]["sealed_2023_plus_REPORT_ONLY"],
            "tip_gates": primary["tip_gates"],
            "tip_clean": primary["tip_clean"],
        },
        "challengers": {r["id"]: {k: v for k, v in r.items()} for r in ranked},
        "ranked_heldout": [{k: v for k, v in r.items()} for r in ranked],
        "verdict": (
            f"FIN_PRE_EXDIV_KD held-out score "
            f"{primary['scores']['heldout_2019_plus']['score']:+.3f} vs EQUAL; "
            f"tip YTD={primary['tip_gates']['ytd']['gate']} "
            f"1y={primary['tip_gates']['trailing_1y']['gate']}. "
            "Paper only — Soft-Frozen KEEP · no live wire."
        ),
        "non_actions": [
            "No Soft-Frozen flip",
            "No live e21 wire",
            "Does not auto-open dual-paper observe (needs ballot)",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_PRE_EXDIV_KD_NAV.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    h = primary["scores"]["heldout_2019_plus"]
    tip = primary["tip_gates"]
    lines = [
        "# FIN_PRE_EXDIV_KD — paper NAV screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER_NAV_SCREEN** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "## Rule",
        "",
        f"- Yahoo **K9/D9** · May15–Jun10 first **K<{K_THRESH:g}** → soft-tilt accumulate",
        f"- Skip buy cash-ex **T−{PRE_DAYS}…T0** (+ stock ex day)",
        "- Capital **500M** · lot **1000** · Telecom=`TEL_EQUAL`",
        "",
        "## vs `FIN_EQUAL`",
        "",
        "| id | heldout score | MDD↑pp | CAGR giveback | YTD | 1y | tip-clean |",
        "|---|---:|---:|---:|---|---|---|",
        "| `FIN_EQUAL` | — | — | — | PASS | PASS | — |",
    ]
    for r in ranked:
        hh = r["scores"]["heldout_2019_plus"]
        t = r["tip_gates"]
        lines.append(
            f"| `{r['id']}` | {hh['score']:.3f} | {hh['mdd_improve_pp']:.3f} | "
            f"{hh['cagr_giveback_pp']:.3f} | {t['ytd']['gate']} | {t['trailing_1y']['gate']} | "
            f"{r['tip_clean']} |"
        )
    lines += [
        "",
        "## Primary detail (`FIN_PRE_EXDIV_KD`)",
        "",
        f"- Held-out score: **{h['score']:+.3f}** (MDD↑ {h['mdd_improve_pp']:.3f}pp · "
        f"CAGR giveback {h['cagr_giveback_pp']:.3f}pp)",
        f"- Tip YTD giveback: {tip['ytd'].get('giveback_pp')} → **{tip['ytd']['gate']}**",
        f"- Tip 1y giveback: {tip['trailing_1y'].get('giveback_pp')} → **{tip['trailing_1y']['gate']}**",
        "",
        "## Verdict",
        "",
        payload["verdict"],
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen KEEP · no live wire · no auto observe OPEN",
        "- Event-study probe remains `FIN_PRE_EXDIV_KD_PROBE.md`",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_PRE_EXDIV_KD_NAV.md").write_text(md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "primary": payload["primary_vs_equal"],
                "ranked": [
                    {
                        "id": r["id"],
                        "held": r["scores"]["heldout_2019_plus"]["score"],
                        "ytd": r["tip_gates"]["ytd"]["gate"],
                        "t1": r["tip_gates"]["trailing_1y"]["gate"],
                    }
                    for r in ranked
                ],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
