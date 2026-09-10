#!/usr/bin/env python3
"""Round-3: finite market TA catalog singles + buy×sell combinations (PAPER).

Charter: research/ops/INDICATOR_COMBO_CATALOG_CHARTER.md
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from ta_indicator_catalog import (
    HIGH_IDS,
    LOW_IDS,
    build_low_high_catalog,
    combine_and,
    combine_majority,
    combine_or,
)
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_EXDIV_SKIP_BUY,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/indicator-combo-catalog-r3"
RESEARCH = ROOT / "research/ops"
CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
LIVE_KD = {
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}


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


def sim(market, target, regime, dividends, *, buy_ok=None, sell_ok=None, policy=FIN_EXDIV_SKIP_BUY, scores=None):
    return simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        financial_alloc=policy,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        fin_sell_ok=sell_ok,
    )


def and_ex(signal: pd.DataFrame, ex_ok: pd.DataFrame) -> pd.DataFrame:
    out = signal.copy()
    for c in out.columns:
        if c in ex_ok.columns:
            out[c] = out[c] & ex_ok[c].reindex(out.index).fillna(True)
    return out


def eval_one(
    *,
    book_id: str,
    layer: str,
    buy_id: str | None,
    sell_id: str | None,
    nav_eq,
    win_eq,
    held_live: float,
    asof,
    market,
    target,
    regime,
    dividends,
    buy_ok,
    sell_ok,
    policy=FIN_EXDIV_SKIP_BUY,
    scores=None,
):
    nav, fills, meta = sim(
        market,
        target,
        regime,
        dividends,
        buy_ok=buy_ok,
        sell_ok=sell_ok,
        policy=policy,
        scores=scores,
    )
    assert meta.get("exact_t1_ok"), book_id
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    tip = tip_gate(nav_eq, nav, asof)
    held = score_vs_base(win_eq["heldout_2019_plus"], win["heldout_2019_plus"])
    tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
    return {
        "id": book_id,
        "layer": layer,
        "buy_id": buy_id,
        "sell_id": sell_id,
        "heldout_score": float(held["score"]),
        "mdd_improve_pp": float(held["mdd_improve_pp"]),
        "cagr_giveback_pp": held["cagr_giveback_pp"],
        "tip_ytd": tip["ytd"]["gate"],
        "tip_1y": tip["trailing_1y"]["gate"],
        "tip_clean": tip_clean,
        "coexist": bool(tip_clean and held["score"] > 0),
        "vs_live_heldout_delta": float(held["score"] - held_live),
        "n_fills": int(len(fills)),
        "full_cagr": win["full"].get("cagr"),
        "full_mdd": win["full"].get("max_drawdown"),
    }


def rank_key(r: dict) -> tuple:
    beat = bool(r.get("coexist") and r.get("vs_live_heldout_delta", 0) > 0 and r["id"] != "LIVE_KD_OPT")
    no_pause = r["tip_ytd"] != "PAUSE_REVIEW" and r["tip_1y"] != "PAUSE_REVIEW"
    return (
        1 if r.get("coexist") else 0,
        1 if beat else 0,
        1 if no_pause else 0,
        float(r.get("heldout_score") or -999),
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    codes = list(FIN)
    ex_ok = build_exdiv_buy_ok(cal, dividends, codes, also_stock_ex=True)

    print("anchors ...", flush=True)
    nav_eq, _, meta_eq = sim(market, target, regime, dividends, policy=FIN_EQUAL)
    assert meta_eq.get("exact_t1_ok")
    win_eq = {w: window_stats(nav_eq, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    asof = pd.to_datetime(nav_eq["date"]).max()

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
    nav_live, _, meta_live = sim(
        market,
        target,
        regime,
        dividends,
        policy=FIN_PRE_EXDIV_KD,
        scores=kd_scores,
        buy_ok=kd_ok,
    )
    assert meta_live.get("exact_t1_ok")
    win_live = {w: window_stats(nav_live, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    held_live = score_vs_base(win_eq["heldout_2019_plus"], win_live["heldout_2019_plus"])["score"]
    live_tip = tip_gate(nav_eq, nav_live, asof)

    rows: list[dict] = [
        {
            "id": "FIN_EQUAL",
            "layer": "anchor",
            "buy_id": None,
            "sell_id": None,
            "heldout_score": 0.0,
            "mdd_improve_pp": 0.0,
            "cagr_giveback_pp": 0.0,
            "tip_ytd": "PASS",
            "tip_1y": "PASS",
            "tip_clean": True,
            "coexist": False,
            "vs_live_heldout_delta": float(0.0 - held_live),
            "n_fills": None,
            "full_cagr": win_eq["full"].get("cagr"),
            "full_mdd": win_eq["full"].get("max_drawdown"),
        },
        {
            "id": "LIVE_KD_OPT",
            "layer": "anchor",
            "buy_id": "KD_SEASON",
            "sell_id": "EQUAL",
            "heldout_score": float(held_live),
            "mdd_improve_pp": float(
                score_vs_base(win_eq["heldout_2019_plus"], win_live["heldout_2019_plus"])[
                    "mdd_improve_pp"
                ]
            ),
            "cagr_giveback_pp": score_vs_base(
                win_eq["heldout_2019_plus"], win_live["heldout_2019_plus"]
            )["cagr_giveback_pp"],
            "tip_ytd": live_tip["ytd"]["gate"],
            "tip_1y": live_tip["trailing_1y"]["gate"],
            "tip_clean": live_tip["ytd"]["gate"] == "PASS" and live_tip["trailing_1y"]["gate"] == "PASS",
            "coexist": live_tip["ytd"]["gate"] == "PASS"
            and live_tip["trailing_1y"]["gate"] == "PASS"
            and held_live > 0,
            "vs_live_heldout_delta": 0.0,
            "n_fills": None,
            "full_cagr": win_live["full"].get("cagr"),
            "full_mdd": win_live["full"].get("max_drawdown"),
        },
    ]

    print("building TA catalog ...", flush=True)
    lows, highs = build_low_high_catalog(market, cal, codes)

    jobs: list[tuple] = []
    # A: BUY_LOW singles
    for lid in LOW_IDS:
        jobs.append((f"BUY_LOW_{lid}", "BUY_LOW", lid, None, and_ex(lows[lid], ex_ok), None))
    # B: SELL_HIGH singles
    for hid in HIGH_IDS:
        jobs.append((f"SELL_HIGH_{hid}", "SELL_HIGH", None, hid, ex_ok, highs[hid]))
    # D: aggregates
    jobs.append(
        (
            "BUY_OR_ALL",
            "AGG",
            "OR_ALL",
            None,
            and_ex(combine_or([lows[k] for k in LOW_IDS], cal, codes), ex_ok),
            None,
        )
    )
    jobs.append(
        (
            "BUY_MAJ3",
            "AGG",
            "MAJ3",
            None,
            and_ex(combine_majority([lows[k] for k in LOW_IDS], cal, codes, k=3), ex_ok),
            None,
        )
    )
    jobs.append(
        (
            "BUY_AND_RSI_BB_K",
            "AGG",
            "AND_RSI_BB_K",
            None,
            and_ex(
                combine_and([lows["RSI14_LT30"], lows["BB_LOWER"], lows["K9_LT30"]], cal, codes),
                ex_ok,
            ),
            None,
        )
    )
    jobs.append(
        (
            "SELL_OR_ALL",
            "AGG",
            None,
            "OR_ALL",
            ex_ok,
            combine_or([highs[k] for k in HIGH_IDS], cal, codes),
        )
    )
    jobs.append(
        (
            "SELL_MAJ3",
            "AGG",
            None,
            "MAJ3",
            ex_ok,
            combine_majority([highs[k] for k in HIGH_IDS], cal, codes, k=3),
        )
    )
    # C: full cross
    for lid in LOW_IDS:
        for hid in HIGH_IDS:
            jobs.append(
                (
                    f"X__{lid}__{hid}",
                    "CROSS",
                    lid,
                    hid,
                    and_ex(lows[lid], ex_ok),
                    highs[hid],
                )
            )

    total = len(jobs)
    print(f"running {total} books ...", flush=True)
    for i, (book_id, layer, buy_id, sell_id, buy_ok, sell_ok) in enumerate(jobs, 1):
        if i == 1 or i % 25 == 0 or i == total:
            print(f"  [{i}/{total}] {book_id}", flush=True)
        rows.append(
            eval_one(
                book_id=book_id,
                layer=layer,
                buy_id=buy_id,
                sell_id=sell_id,
                nav_eq=nav_eq,
                win_eq=win_eq,
                held_live=held_live,
                asof=asof,
                market=market,
                target=target,
                regime=regime,
                dividends=dividends,
                buy_ok=buy_ok,
                sell_ok=sell_ok,
            )
        )

    ranked = sorted(rows, key=rank_key, reverse=True)
    coexist = [r for r in ranked if r.get("coexist")]
    beat_live = [
        r
        for r in ranked
        if r.get("coexist") and r["id"] != "LIVE_KD_OPT" and r.get("vs_live_heldout_delta", 0) > 0
    ]
    top_cross = [r for r in ranked if r["layer"] == "CROSS"][:15]
    top_buy = [r for r in ranked if r["layer"] == "BUY_LOW"][:8]
    top_sell = [r for r in ranked if r["layer"] == "SELL_HIGH"][:8]

    verdict = (
        "PROMOTE_CANDIDATE_TO_DUAL_PAPER"
        if beat_live
        else ("COEXIST_NO_LIFT_VS_LIVE" if coexist else "NO_COEXIST_STOP_OR_AUTOPSY")
    )
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "INDICATOR_COMBO_CATALOG_SCREEN_R3",
        "charter": "research/ops/INDICATOR_COMBO_CATALOG_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "soft_frozen_clip": soft.SOFT_FROZEN_FIN_CLIP,
        "asof": str(pd.Timestamp(asof).date()),
        "catalog": {"lows": LOW_IDS, "highs": HIGH_IDS},
        "n_books": len(rows),
        "n_cross": len(LOW_IDS) * len(HIGH_IDS),
        "n_coexist": len(coexist),
        "n_beat_live": len(beat_live),
        "coexist_ids": [r["id"] for r in coexist[:50]],
        "beat_live_ids": [r["id"] for r in beat_live[:50]],
        "top15_overall": [r["id"] for r in ranked[:15]],
        "top_cross": [r["id"] for r in top_cross],
        "top_buy_low": [r["id"] for r in top_buy],
        "top_sell_high": [r["id"] for r in top_sell],
        "verdict": verdict,
        "books": ranked,
        "non_actions": [
            "No Soft-Frozen flip",
            "No live KD_OPT change",
            "No E45 stitch",
            "No auto cutover",
            "Catalog is finite market-standard TA — not literally every indicator ever published",
        ],
    }

    csv_path = OUT / "reports" / "combo_scoreboard.csv"
    pd.DataFrame(ranked).to_csv(csv_path, index=False)
    (OUT / "reports" / "indicator_combo_catalog_screen_r3.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # Slim research JSON (drop full books list to keep ops readable? keep full for SSOT)
    (RESEARCH / "INDICATOR_COMBO_CATALOG_SCREEN_R3.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def line(r: dict) -> str:
        cagr = r["cagr_giveback_pp"]
        return (
            f"| `{r['id']}` | {r['layer']} | {r['tip_ytd']} | {r['tip_1y']} | "
            f"{r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{'—' if cagr is None else f'{cagr:.3f}'} | {r['vs_live_heldout_delta']:.3f} | "
            f"{'Y' if r.get('coexist') else ''} |"
        )

    lines = [
        "# Indicator Combo Catalog Screen — Round 3",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Asof: **{payload['asof']}** · Soft-Frozen **{soft.SOFT_FROZEN_FIN_CLIP}** KEEP",
        f"Charter: `INDICATOR_COMBO_CATALOG_CHARTER.md`",
        f"Verdict: **`{verdict}`**",
        "",
        "## Scope",
        "",
        f"- Low gates: **{len(LOW_IDS)}** · High gates: **{len(HIGH_IDS)}** · Cross: **{payload['n_cross']}**",
        f"- Total books: **{payload['n_books']}** (singles + aggregates + full buy×sell cross + anchors)",
        "- Finite market-standard TA catalog (not unbounded universe).",
        "",
        "## Summary",
        "",
        f"- Coexist: **{payload['n_coexist']}**",
        f"- Beat live KD_OPT: **{payload['n_beat_live']}** → `{payload['beat_live_ids'][:20]}`",
        f"- Top overall: `{payload['top15_overall'][:10]}`",
        "",
        "## Top 20 scoreboard",
        "",
        "| ID | Layer | Tip YTD | Tip 1y | Held | MDDΔpp | CAGRΔpp | vs live Δ | Coexist |",
        "|---|---|---|---|---:|---:|---:|---:|:---:|",
    ]
    lines.extend(line(r) for r in ranked[:20])
    lines += [
        "",
        "### Top BUY_LOW singles",
        "",
        "| ID | Tip YTD | Tip 1y | Held | vs live Δ | Coexist |",
        "|---|---|---|---:|---:|:---:|",
    ]
    for r in top_buy:
        lines.append(
            f"| `{r['id']}` | {r['tip_ytd']} | {r['tip_1y']} | {r['heldout_score']:.3f} | {r['vs_live_heldout_delta']:.3f} | {'Y' if r.get('coexist') else ''} |"
        )
    lines += [
        "",
        "### Top SELL_HIGH singles",
        "",
        "| ID | Tip YTD | Tip 1y | Held | vs live Δ | Coexist |",
        "|---|---|---|---:|---:|:---:|",
    ]
    for r in top_sell:
        lines.append(
            f"| `{r['id']}` | {r['tip_ytd']} | {r['tip_1y']} | {r['heldout_score']:.3f} | {r['vs_live_heldout_delta']:.3f} | {'Y' if r.get('coexist') else ''} |"
        )
    lines += [
        "",
        "### Top CROSS (buy×sell)",
        "",
        "| ID | Tip YTD | Tip 1y | Held | vs live Δ | Coexist |",
        "|---|---|---|---:|---:|:---:|",
    ]
    for r in top_cross:
        lines.append(
            f"| `{r['id']}` | {r['tip_ytd']} | {r['tip_1y']} | {r['heldout_score']:.3f} | {r['vs_live_heldout_delta']:.3f} | {'Y' if r.get('coexist') else ''} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        "- Beat-live empty → keep live KD_OPT.",
        "- Full CSV: `repro/indicator-combo-catalog-r3/reports/combo_scoreboard.csv`",
        "",
        "## Non-actions",
        "",
        "- No Soft-Frozen / KD_OPT / TEL live change · no E45 stitch · no auto cutover",
        "",
        "## Label",
        "",
        "`INDICATOR_COMBO_CATALOG_SCREEN_R3_2026-09-10`",
        "",
    ]
    md = "\n".join(lines)
    (RESEARCH / "INDICATOR_COMBO_CATALOG_SCREEN_R3.md").write_text(md, encoding="utf-8")
    (OUT / "reports" / "INDICATOR_COMBO_CATALOG_SCREEN_R3.md").write_text(md, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_books": payload["n_books"],
                "n_coexist": payload["n_coexist"],
                "n_beat_live": payload["n_beat_live"],
                "beat_live_ids": payload["beat_live_ids"][:20],
                "top15": payload["top15_overall"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
