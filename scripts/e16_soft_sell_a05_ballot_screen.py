#!/usr/bin/env python3
"""Stage A paper: Soft-assist SELL_a05 confirm + OPEN-ballot evidence (NO live wire).

Charter: research/ops/SOFT_SELL_A05_BALLOT_CHARTER.md

Borrow-promote found SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05 promote-shaped > observe.
This Soft-only reconfirm screen + draft OPEN Soft-assist observe ballot (await human).
Soft-Frozen KEEP · KD_OPT KEEP · TEL_EQUAL KEEP · Sleeve observe UNCHANGED ·
no Soft×Sleeve fuse · E45 OFF · observe NOT swapped until human OPEN string.
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
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from soft_assist_helpers import (
    BUY_LOW_ID,
    CHAMPION_ID,
    LIVE_KD,
    OBSERVE_CHAL_ID,
    SELL_HIGH_ID,
    SOFT_BOOST,
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
OUT = ROOT / "repro/soft-sell-a05-ballot"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
SOFT_BASE = "LIVE_KD_OPT"
CANDIDATE_ID = "SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05"


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
            out[wname] = {"giveback_pp": None, "gate": "INSUFFICIENT", "mdd_improve_pp": None}
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
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        out[wname] = {
            "giveback_pp": None if gb is None else float(gb),
            "gate": gate,
            "mdd_improve_pp": float(mdd_delta_pp(b_mdd, c_mdd)),
        }
    return out


def tip_mdd_clean(tip: dict) -> bool:
    for w in ("ytd", "trailing_1y"):
        md = tip.get(w, {}).get("mdd_improve_pp")
        if md is None or float(md) < 0.0:
            return False
    return True


def held_score(base_stats: dict, chal_stats: dict) -> dict:
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


def run_kd(market, target, regime, dividends, *, scores, buy_ok, sell_scores=None):
    nav, fills, meta = simulate_core(
        market,
        target,
        regime,
        dividends,
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
    assert meta.get("exact_t1_ok")
    return {"nav": nav, "n_fills": int(len(fills)), "meta": meta}


def add_buy_softs(kd_scores: pd.DataFrame, lows: dict, specs: list[tuple[str, float]]) -> pd.DataFrame:
    out = kd_scores.astype(float)
    for lid, boost in specs:
        out = soft_boost_scores(out, lows[lid], float(boost))
    return out


def book_row(*, book_id, track, tip, held, win, n_fills, extra=None):
    tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
    mdd_ok = tip_mdd_clean(tip)
    row = {
        "id": book_id,
        "track": track,
        "heldout_score": float(held["score"]),
        "mdd_improve_pp": float(held["mdd_improve_pp"]),
        "cagr_giveback_pp": held["cagr_giveback_pp"],
        "tip_ytd": tip["ytd"]["gate"],
        "tip_1y": tip["trailing_1y"]["gate"],
        "tip_clean": tip_clean,
        "tip_mdd_ytd_pp": tip["ytd"].get("mdd_improve_pp"),
        "tip_mdd_1y_pp": tip["trailing_1y"].get("mdd_improve_pp"),
        "tip_mdd_clean": mdd_ok,
        "promote_shaped": bool(tip_clean and mdd_ok and held["score"] > 0),
        "coexist": bool(tip_clean and held["score"] > 0),
        "full_cagr": win["full"].get("cagr"),
        "full_mdd": win["full"].get("max_drawdown"),
        "heldout_cagr": win["heldout_2019_plus"].get("cagr"),
        "heldout_mdd": win["heldout_2019_plus"].get("max_drawdown"),
        "sealed_cagr": win["sealed_2023_plus"].get("cagr"),
        "sealed_mdd": win["sealed_2023_plus"].get("max_drawdown"),
        "n_fills": int(n_fills),
    }
    if extra:
        row.update(extra)
    return row


def main() -> int:
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    import e21_forward_pipeline as e21

    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse screen while LIVE_E45_STITCH is True")

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))

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
    sell_panels = {
        0.5: soft_sell_panel(highs[SELL_HIGH_ID], boost=0.5),
        1.0: soft_sell_panel(highs[SELL_HIGH_ID], boost=SOFT_BOOST),
        1.5: soft_sell_panel(highs[SELL_HIGH_ID], boost=1.5),
    }
    observe_buy = [(BUY_LOW_ID, 1.0), ("K9_LT30", 1.0)]

    # Finite Soft-only books around SELL_a05 / buy-amp neighbors
    jobs: list[tuple[str, str, list[tuple[str, float]], float | None]] = [
        (SOFT_BASE, "base", [], None),
        (CHAMPION_ID, "champion", [(BUY_LOW_ID, SOFT_BOOST)], 1.0),
        (OBSERVE_CHAL_ID, "observe", observe_buy, 1.0),
        (CANDIDATE_ID, "sell_amp", observe_buy, 0.5),
        ("SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a15", "sell_amp", observe_buy, 1.5),
        ("SOFT_CHAMP_PLUS_K9_LT30_a15", "buy_amp", [(BUY_LOW_ID, 1.0), ("K9_LT30", 1.5)], 1.0),
    ]

    print(f"Soft SELL_a05 ballot books: {len(jobs)}", flush=True)
    rows = []
    nav_base = win_base = asof = None
    for i, (book_id, track, buy_specs, sell_boost) in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] {book_id}", flush=True)
        if not buy_specs:
            scores = kd_scores
            sell = None
        else:
            scores = add_buy_softs(kd_scores, lows, buy_specs)
            sell = sell_panels[float(sell_boost)] if sell_boost is not None else None
        res = run_kd(market, target, regime, dividends, scores=scores, buy_ok=kd_ok, sell_scores=sell)
        win = {w: window_stats(res["nav"], a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        if book_id == SOFT_BASE:
            nav_base = res["nav"]
            win_base = win
            asof = pd.to_datetime(res["nav"]["date"]).max()
            tip = tip_gate(nav_base, nav_base, asof)
            held = {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "score": 0.0}
        else:
            tip = tip_gate(nav_base, res["nav"], asof)
            held = held_score(win_base["heldout_2019_plus"], win["heldout_2019_plus"])
        rows.append(
            book_row(
                book_id=book_id,
                track=track,
                tip=tip,
                held=held,
                win=win,
                n_fills=res["n_fills"],
                extra={
                    "buy_soft": "+".join(f"{a}@{b:g}" for a, b in buy_specs) if buy_specs else "none",
                    "sell_soft": f"{SELL_HIGH_ID}@{sell_boost:g}" if sell_boost else "none",
                    "is_observe_ref": book_id == OBSERVE_CHAL_ID,
                    "is_candidate": book_id == CANDIDATE_ID,
                },
            )
        )

    observe = next(r for r in rows if r["id"] == OBSERVE_CHAL_ID)
    cand = next(r for r in rows if r["id"] == CANDIDATE_ID)
    ranked = sorted(
        rows,
        key=lambda r: (1 if r.get("promote_shaped") else 0, 1 if r.get("coexist") else 0, r["heldout_score"]),
        reverse=True,
    )
    beat_live = [r for r in ranked if r["id"] != SOFT_BASE and r.get("coexist") and r["heldout_score"] > 0]
    beat_observe = [
        r
        for r in ranked
        if r["id"] not in (SOFT_BASE, OBSERVE_CHAL_ID, CHAMPION_ID)
        and r.get("tip_clean")
        and r["heldout_score"] > observe["heldout_score"]
    ]
    promote_vs_observe = [
        r
        for r in ranked
        if r["id"] not in (SOFT_BASE, OBSERVE_CHAL_ID)
        and r.get("promote_shaped")
        and r["heldout_score"] > observe["heldout_score"]
    ]
    cand_ok = bool(
        cand.get("promote_shaped") and cand["heldout_score"] > observe["heldout_score"]
    )
    if cand_ok:
        verdict = "SELL_A05_PROMOTE_SHAPED_BEATS_OBSERVE"
    elif promote_vs_observe:
        verdict = "OTHER_PROMOTE_SHAPED_BEATS_OBSERVE"
    elif beat_live:
        verdict = "BEATS_LIVE_NO_OBSERVE_LIFT"
    else:
        verdict = "NO_LIFT"

    ballot_status = "OPEN_AWAIT_HUMAN" if cand_ok else "NO_BALLOT_NO_LIFT"
    open_string = f"OPEN Soft-assist observe: {CANDIDATE_ID}"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_SELL_A05_BALLOT_SCREEN",
        "charter": "research/ops/SOFT_SELL_A05_BALLOT_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "soft_x_sleeve_fuse": False,
        "observe_swap": False,
        "asof": str(pd.Timestamp(asof).date()),
        "verdict": verdict,
        "ballot_status": ballot_status,
        "candidate_id": CANDIDATE_ID,
        "candidate_promote_shaped_beats_observe": cand_ok,
        "open_string": open_string if cand_ok else None,
        "observe_id": OBSERVE_CHAL_ID,
        "observe_heldout_score": observe["heldout_score"],
        "candidate_heldout_score": cand["heldout_score"],
        "n_books": len(rows),
        "n_beat_live": len(beat_live),
        "n_beat_observe": len(beat_observe),
        "n_promote_shaped_beats_observe": len(promote_vs_observe),
        "beat_live_ids": [r["id"] for r in beat_live],
        "beat_observe_ids": [r["id"] for r in beat_observe],
        "promote_shaped_ids": [r["id"] for r in promote_vs_observe],
        "books": ranked,
        "non_actions": [
            "No Soft-assist observe swap until human exact OPEN string",
            "No live Soft-assist / Soft-Frozen / KD / TEL / E45 wire",
            "No Soft×Sleeve auto-combo",
            "No hard-AND reopen",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    blob = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "soft_sell_a05_ballot_screen.json").write_text(blob, encoding="utf-8")
    (OPS / "SOFT_SELL_A05_BALLOT_SCREEN.json").write_text(blob, encoding="utf-8")

    def pct(x):
        return "—" if x is None else f"{100 * float(x):.2f}%"

    def line(r):
        return (
            f"| `{r['id']}` | {r['track']} | {r['tip_ytd']} | {r['tip_1y']} | "
            f"{'Y' if r['tip_mdd_clean'] else 'N'} | {'Y' if r['promote_shaped'] else 'N'} | "
            f"{r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{pct(r['heldout_cagr'])} | {pct(r['heldout_mdd'])} | "
            f"{pct(r['sealed_cagr'])} | {pct(r['sealed_mdd'])} |"
        )

    lines = [
        "# Soft-Assist SELL_a05 Ballot Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Verdict: **`{verdict}`** · ballot **`{ballot_status}`** · books **{payload['n_books']}**",
        "Live wire: **false** · observe swap: **false** · Soft×Sleeve fuse: **forbidden**",
        "",
        "## Question",
        "",
        f"Does Soft-only reconfirm show `{CANDIDATE_ID}` promote-shaped tip-clean "
        f"beating observe `{OBSERVE_CHAL_ID}` enough to draft an OPEN Soft-assist observe ballot?",
        "",
        "## Summary",
        "",
        f"- Observe `{OBSERVE_CHAL_ID}` held **{observe['heldout_score']:.3f}** · tip_mdd_clean **{observe['tip_mdd_clean']}**",
        f"- Candidate `{CANDIDATE_ID}` held **{cand['heldout_score']:.3f}** · tip_mdd_clean **{cand['tip_mdd_clean']}** · promote_shaped **{cand['promote_shaped']}**",
        f"- Promote-shaped > observe: **{len(promote_vs_observe)}** → `{[r['id'] for r in promote_vs_observe]}`",
        f"- Candidate beats observe (promote-shaped): **{cand_ok}**",
        "",
        "## Books",
        "",
        "| ID | Track | Tip YTD | Tip 1y | Tip MDD clean | Promote-shaped | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD |",
        "|---|---|---|---|:---:|:---:|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(line(r) for r in ranked)
    lines += ["", "## Ballot", ""]
    if cand_ok:
        lines += [
            "Status: **OPEN — await human** (draft only; observe not swapped).",
            "",
            "Exact reply string:",
            "",
            "```",
            open_string,
            "```",
            "",
            "Also allowed: `KEEP Soft-assist observe` · `DEFER Soft-assist SELL_a05 ballot` · `REJECT Soft-assist SELL_a05 ballot`",
        ]
    else:
        lines += [
            "Status: **NO BALLOT** — candidate did not promote-shaped beat observe on Soft-only reconfirm.",
        ]
    lines += ["", "## Non-actions", ""]
    lines.extend(f"- {x}" for x in payload["non_actions"])
    lines += ["", "## Label", "", f"`SOFT_SELL_A05_BALLOT_SCREEN_{payload['asof']}__{verdict}`", ""]
    md = "\n".join(lines)
    (OUT / "reports" / "SOFT_SELL_A05_BALLOT_SCREEN.md").write_text(md, encoding="utf-8")
    (OPS / "SOFT_SELL_A05_BALLOT_SCREEN.md").write_text(md, encoding="utf-8")

    zh = "\n".join(
        [
            "# Soft-Assist SELL_a05 選票篩選",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"判決：**`{verdict}`** · 選票 **`{ballot_status}`**",
            "",
            f"- Observe held **{observe['heldout_score']:.3f}**",
            f"- Candidate `{CANDIDATE_ID}` held **{cand['heldout_score']:.3f}** · promote>observe **{cand_ok}**",
            "",
            ("人話回覆字串（僅草稿，未換 observe）：" if cand_ok else "未達選票門檻。"),
            *(["", "```", open_string, "```"] if cand_ok else []),
            "",
            "## 非動作",
            "",
            "- 未收到人話 OPEN 字串前不換 Soft-assist observe",
            "- 不接 live Soft-assist／Soft-Frozen／KD／TEL／E45",
            "- 不 Soft×Sleeve 融合",
            "",
            f"`SOFT_SELL_A05_BALLOT_SCREEN_{payload['asof']}__{verdict}`",
            "",
        ]
    )
    (OPS / "SOFT_SELL_A05_BALLOT_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    # Draft OPEN ballot doc only if candidate clears
    if cand_ok:
        ballot = "\n".join(
            [
                "# Soft-Assist SELL_a05 — Observe Ballot OPEN (draft)",
                "",
                f"Date: {payload['asof']}",
                "Status: **OPEN — await human reply**",
                f"Evidence: `SOFT_SELL_A05_BALLOT_SCREEN.md` · verdict `{verdict}`",
                "Soft-Frozen **KEEP** · live **`KD_OPT` KEEP** · **`TEL_EQUAL` KEEP** · Sleeve-tilt observe **UNCHANGED** · E45 **OFF**",
                "",
                "## Purpose",
                "",
                "Decide whether Soft-assist dual-paper observe retargets from operating",
                f"`{OBSERVE_CHAL_ID}` to promote-shaped `{CANDIDATE_ID}` (sell soft amplitude 0.5).",
                "",
                "| Field | Value |",
                "|---|---|",
                f"| Candidate | `{CANDIDATE_ID}` |",
                f"| Buy soft | `BELOW_MA120@1` + `K9_LT30@1` (same as observe) |",
                f"| Sell soft | `{SELL_HIGH_ID}@0.5` (was @1.0) |",
                f"| Held score | **{cand['heldout_score']:.3f}** vs observe **{observe['heldout_score']:.3f}** |",
                f"| Tip MDD clean | **{cand['tip_mdd_clean']}** |",
                "",
                "## Reply with exactly one of",
                "",
                "### A — OPEN Soft-assist observe (recommended if accepting retarget)",
                "",
                "```",
                open_string,
                "```",
                "",
                "Effect: authorizes dual-paper Soft-assist observe retarget to candidate. **No live wire.**",
                "",
                "### B — KEEP current Soft-assist observe",
                "",
                "```",
                "KEEP Soft-assist observe",
                "```",
                "",
                "### C — DEFER",
                "",
                "```",
                "DEFER Soft-assist SELL_a05 ballot",
                "```",
                "",
                "### D — REJECT",
                "",
                "```",
                "REJECT Soft-assist SELL_a05 ballot",
                "```",
                "",
                "## Explicit non-choices",
                "",
                "- Live Soft-assist / Soft-Frozen / KD / TEL / E45 wire",
                "- Soft×Sleeve auto-combo",
                "- Hard-AND indicator reopen",
                "",
                "## Label",
                "",
                f"`SOFT_SELL_A05_OBSERVE_BALLOT_OPEN_{payload['asof']}__AWAIT_HUMAN`",
                "",
            ]
        )
        (OPS / "SOFT_SELL_A05_OBSERVE_BALLOT_OPEN.md").write_text(ballot, encoding="utf-8")
        zh_b = "\n".join(
            [
                "# Soft-Assist SELL_a05 — Observe 選票 OPEN（草稿）",
                "",
                f"狀態：**OPEN — 等人回覆** · 證據判決 `{verdict}`",
                "",
                "人話擇一回覆：",
                "",
                "```",
                open_string,
                "```",
                "",
                "或 `KEEP Soft-assist observe` / `DEFER Soft-assist SELL_a05 ballot` / `REJECT Soft-assist SELL_a05 ballot`",
                "",
                "未回覆前 **不** 換 observe、**不** 接 live。",
                "",
                f"`SOFT_SELL_A05_OBSERVE_BALLOT_OPEN_{payload['asof']}__AWAIT_HUMAN`",
                "",
            ]
        )
        (OPS / "SOFT_SELL_A05_OBSERVE_BALLOT_OPEN.zh-TW.md").write_text(zh_b, encoding="utf-8")

    charter = OPS / "SOFT_SELL_A05_BALLOT_CHARTER.md"
    if charter.exists():
        ct = charter.read_text()
        ct = ct.replace("**PAPER STAGE A OPEN**", f"**PAPER STAGE A DONE** · verdict **`{verdict}`**")
        ct = ct.replace(
            "`SOFT_SELL_A05_BALLOT_CHARTER_2026-09-12__PAPER_OPEN`",
            f"`SOFT_SELL_A05_BALLOT_CHARTER_2026-09-12__{verdict}`",
        )
        charter.write_text(ct)

    print(
        json.dumps(
            {
                "verdict": verdict,
                "ballot_status": ballot_status,
                "cand_ok": cand_ok,
                "cand_held": cand["heldout_score"],
                "observe_held": observe["heldout_score"],
                "promote_vs_observe": [r["id"] for r in promote_vs_observe],
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
