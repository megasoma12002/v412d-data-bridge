#!/usr/bin/env python3
"""Stage A paper: external public Soft-sell motifs vs Soft observe — NO live wire.

Charter: research/ops/EXTERNAL_STRATEGY_BORROW_STAGEA_CHARTER.md

Maps citable public overbought/exit motifs onto Soft sell softs.
Does not scrape login walls · does not swap Soft/Sleeve observe · no fuse.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_dl_4track_stagea_screen as base
import e16_soft_frozen_base as soft
from soft_assist_helpers import (
    LIVE_KD,
    OBSERVE_CHAL_ID,
    PRIOR_OBSERVE_ID,
    SELL_HIGH_ID,
    SELL_SOFT_BOOST,
    SOFT_BOOST,
    build_observe_buy_scores,
    soft_sell_panel,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/external-strategy-borrow-stagea"
OPS = ROOT / "research/ops"
SOFT_BASE = base.SOFT_BASE


def gated_sell(high_panel: pd.DataFrame, gate: pd.DataFrame, *, boost: float) -> pd.DataFrame:
    """Soft sell active only where gate is True; else neutral 1.0."""
    g = gate.reindex_like(high_panel).fillna(False).astype(float)
    h = high_panel.reindex_like(g).fillna(False).astype(float)
    return 1.0 + float(boost) * (h * g)


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
    market = base.load_market()
    dividends = base.load_dividends()
    _p, _s, target, regime = base.e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = base.build_low_high_catalog(market, cal, list(base.FIN))

    kd_scores = base.build_kd_season_tilt_scores(
        market,
        dividends,
        base.FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    kd_ok = base.build_pre_exdiv_window_buy_ok(
        cal, dividends, base.FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    observe_buy = build_observe_buy_scores(kd_scores, lows)

    sell_observe = soft_sell_panel(highs[SELL_HIGH_ID], boost=SELL_SOFT_BOOST)
    sell_prior = soft_sell_panel(highs[SELL_HIGH_ID], boost=SOFT_BOOST)
    sell_rsi14_a05 = soft_sell_panel(highs["RSI14_GT70"], boost=0.5)
    sell_rsi14_a10 = soft_sell_panel(highs["RSI14_GT70"], boost=1.0)
    sell_bb_a05 = soft_sell_panel(highs["BB_UPPER"], boost=0.5)
    sell_mfi_a05 = soft_sell_panel(highs["MFI14_GT80"], boost=0.5)
    sell_rsi14_trend = gated_sell(highs["RSI14_GT70"], highs["ABOVE_MA60"], boost=0.5)

    jobs = [
        (SOFT_BASE, "base", None, None, None),
        (OBSERVE_CHAL_ID, "observe", observe_buy, sell_observe, "operating Soft SELL_a05"),
        (PRIOR_OBSERVE_ID, "prior_soft", observe_buy, sell_prior, "prior Soft sell@1.0"),
        (
            "EXT_RSI14_GT70_SELL_a05",
            "ext_rsi70",
            observe_buy,
            sell_rsi14_a05,
            "Investopedia-style RSI70 exit α=0.5",
        ),
        (
            "EXT_RSI14_GT70_SELL_a10",
            "ext_rsi70",
            observe_buy,
            sell_rsi14_a10,
            "Investopedia-style RSI70 exit α=1.0",
        ),
        (
            "EXT_BB_UPPER_SELL_a05",
            "ext_bb_upper",
            observe_buy,
            sell_bb_a05,
            "public BB-upper exhaustion sell α=0.5",
        ),
        (
            "EXT_MFI14_GT80_SELL_a05",
            "ext_mfi",
            observe_buy,
            sell_mfi_a05,
            "public MFI>80 overbought sell α=0.5",
        ),
        (
            "EXT_RSI14_GT70_SELL_a05__TREND_MA60",
            "ext_rsi70_trend",
            observe_buy,
            sell_rsi14_trend,
            "RSI70 sell only if ABOVE_MA60 (trend-aligned exit)",
        ),
    ]

    print(f"Stage A books: {len(jobs)} (external Soft-sell borrow · no fuse)", flush=True)
    rows = []
    nav_base = win_base = asof = None
    for i, (book_id, track, scores, sell, note) in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] {book_id}", flush=True)
        sc = kd_scores if scores is None else scores
        res = base.run_kd(
            market, target, regime, dividends, scores=sc, buy_ok=kd_ok, sell_scores=sell
        )
        win = {w: base.window_stats(res["nav"], a, b) for w, (a, b) in base.WINDOWS_STANDARD.items()}
        if book_id == SOFT_BASE:
            nav_base = res["nav"]
            win_base = win
            asof = pd.to_datetime(res["nav"]["date"]).max()
            tip = base.tip_gate(nav_base, nav_base, asof)
            held = {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "score": 0.0}
        else:
            tip = base.tip_gate(nav_base, res["nav"], asof)
            held = base.held_score(win_base["heldout_2019_plus"], win["heldout_2019_plus"])
        rows.append(
            base.book_row(
                book_id=book_id,
                track=track,
                tip=tip,
                held=held,
                win=win,
                n_fills=res["n_fills"],
                extra={
                    "is_observe_ref": book_id == OBSERVE_CHAL_ID,
                    "is_prior_soft": book_id == PRIOR_OBSERVE_ID,
                    "is_external": track.startswith("ext_"),
                    "borrow_note": note,
                },
            )
        )

    observe = next(r for r in rows if r["id"] == OBSERVE_CHAL_ID)
    ranked = sorted(
        rows,
        key=lambda r: (
            1 if r.get("promote_shaped") else 0,
            1 if r.get("coexist") else 0,
            r["heldout_score"],
        ),
        reverse=True,
    )
    beat_live = [
        r for r in ranked if r["id"] != SOFT_BASE and r.get("coexist") and r["heldout_score"] > 0
    ]
    promote_vs_observe = [
        r
        for r in ranked
        if r["id"] not in (SOFT_BASE, OBSERVE_CHAL_ID)
        and r.get("promote_shaped")
        and r["heldout_score"] > observe["heldout_score"]
    ]
    ext_promote = [r for r in promote_vs_observe if r.get("is_external")]
    ext_scores = [r["heldout_score"] for r in ranked if r.get("is_external")]
    observe_still_best_vs_ext = observe["heldout_score"] >= (
        max(ext_scores) if ext_scores else -9.0
    )

    if ext_promote:
        verdict = "EXT_BORROW_PROMOTE_SHAPED_BEATS_OBSERVE"
    elif promote_vs_observe and not ext_promote:
        verdict = "NON_EXT_PROMOTE_ONLY_NO_EXT_LIFT"
    elif beat_live:
        verdict = "BEATS_LIVE_NO_OBSERVE_LIFT"
    else:
        verdict = "NO_LIFT"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "EXTERNAL_STRATEGY_BORROW_STAGEA_SCREEN",
        "charter": "research/ops/EXTERNAL_STRATEGY_BORROW_STAGEA_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "soft_x_sleeve_fuse": False,
        "observe_swap": False,
        "scrape_login_walls": False,
        "asof": str(pd.Timestamp(asof).date()),
        "verdict": verdict,
        "observe_id": OBSERVE_CHAL_ID,
        "observe_heldout_score": observe["heldout_score"],
        "observe_still_best_vs_ext": bool(observe_still_best_vs_ext),
        "n_books": len(rows),
        "n_beat_live": len(beat_live),
        "n_promote_shaped_beats_observe": len(promote_vs_observe),
        "n_ext_promote_shaped_beats_observe": len(ext_promote),
        "beat_live_ids": [r["id"] for r in beat_live],
        "promote_shaped_ids": [r["id"] for r in promote_vs_observe],
        "ext_promote_shaped_ids": [r["id"] for r in ext_promote],
        "sources": [
            "Investopedia RSI overbought/exit motif (RSI~70)",
            "Public BB-upper / MFI>80 overbought exit folklore",
            "AQR soft-signal informs (buy soft unchanged; sell soft only)",
            "EXTERNAL_BORROW_NOTES.md Note 2 hygiene",
        ],
        "books": ranked,
        "non_actions": [
            "No login-wall scrape / no TOS bypass",
            "No live Soft-assist / Soft-Frozen / KD / TEL / E45 / Sleeve wire",
            "No Soft-assist or Sleeve observe swap from this screen",
            "No Soft×Sleeve auto-combo",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    blob = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "external_strategy_borrow_stagea_screen.json").write_text(
        blob, encoding="utf-8"
    )
    (OPS / "EXTERNAL_STRATEGY_BORROW_STAGEA_SCREEN.json").write_text(blob, encoding="utf-8")

    def pct(x):
        return "—" if x is None else f"{100 * float(x):.2f}%"

    def line(r):
        return (
            f"| `{r['id']}` | {r['track']} | {r['tip_ytd']} | {r['tip_1y']} | "
            f"{'Y' if r['tip_mdd_clean'] else 'N'} | {'Y' if r['promote_shaped'] else 'N'} | "
            f"{r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{pct(r.get('heldout_cagr'))} | {pct(r.get('heldout_mdd'))} |"
        )

    lines = [
        "# External Strategy Borrow Soft-Sell Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Verdict: **`{verdict}`** · books **{payload['n_books']}**",
        "Live wire: **false** · Soft×Sleeve fuse: **forbidden** · observe swap: **false** · login scrape: **false**",
        "",
        "## Question",
        "",
        "Do public overbought/exit Soft-sell motifs promote-shaped-beat Soft observe "
        "`SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05`?",
        "",
        "## Summary",
        "",
        f"- Observe `{OBSERVE_CHAL_ID}` held **{observe['heldout_score']:.3f}** · tip_mdd_clean **{observe['tip_mdd_clean']}**",
        f"- External promote-shaped > observe: **{len(ext_promote)}** → `{[r['id'] for r in ext_promote]}`",
        f"- Observe still best vs external: **{observe_still_best_vs_ext}**",
        f"- Beat live: **{len(beat_live)}**",
        "",
        "## Sources (motif map only)",
        "",
    ]
    lines.extend(f"- {s}" for s in payload["sources"])
    lines += [
        "",
        "## Books",
        "",
        "| ID | Track | Tip YTD | Tip 1y | Tip MDD clean | Promote-shaped | Held score | MDDΔpp | Held CAGR | Held MDD |",
        "|---|---|---|---|:---:|:---:|---:|---:|---:|---:|",
    ]
    lines.extend(line(r) for r in ranked)
    lines += [
        "",
        "## Reading",
        "",
        "- Buy soft fixed at Soft observe; only Soft **sell** motif changes.",
        "- External books are public-motif encodings, not scraped private strategies.",
        "- Soft∥Sleeve OPEN ballots unchanged; no live wire.",
        "",
        "## Non-actions",
        "",
    ]
    lines.extend(f"- {x}" for x in payload["non_actions"])
    lines += [
        "",
        "## Label",
        "",
        f"`EXTERNAL_STRATEGY_BORROW_STAGEA_SCREEN_{payload['asof']}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "reports" / "EXTERNAL_STRATEGY_BORROW_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")
    (OPS / "EXTERNAL_STRATEGY_BORROW_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")

    zh = "\n".join(
        [
            "# 外部策略借鏡 Soft 賣邊 Stage A 篩選",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"判決：**`{verdict}`**",
            "",
            f"- Observe held **{observe['heldout_score']:.3f}**",
            f"- 外部 promote>observe **{len(ext_promote)}** → `{[r['id'] for r in ext_promote]}`",
            f"- Observe 仍優於外部：**{observe_still_best_vs_ext}**",
            "",
            "詳表見英文稿。公開母題編碼 · 不爬登入牆 · 不接 live · 不換 observe · 不融合。",
            "",
            f"`EXTERNAL_STRATEGY_BORROW_STAGEA_SCREEN_{payload['asof']}__{verdict}`",
            "",
        ]
    )
    (OPS / "EXTERNAL_STRATEGY_BORROW_STAGEA_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    for path, open_tok, done_tok in (
        (
            OPS / "EXTERNAL_STRATEGY_BORROW_STAGEA_CHARTER.md",
            "**PAPER STAGE A OPEN**",
            f"**PAPER STAGE A DONE** · verdict **`{verdict}`**",
        ),
        (
            OPS / "EXTERNAL_STRATEGY_BORROW_STAGEA_CHARTER.zh-TW.md",
            "**PAPER STAGE A OPEN**",
            f"**PAPER STAGE A DONE** · 判決 **`{verdict}`**",
        ),
    ):
        if path.exists():
            t = path.read_text().replace(open_tok, done_tok)
            t = t.replace(
                "`EXTERNAL_STRATEGY_BORROW_STAGEA_CHARTER_2026-09-12__PAPER_OPEN`",
                f"`EXTERNAL_STRATEGY_BORROW_STAGEA_CHARTER_2026-09-12__{verdict}`",
            )
            path.write_text(t)
    cj = OPS / "EXTERNAL_STRATEGY_BORROW_STAGEA_CHARTER.json"
    if cj.exists():
        cjd = json.loads(cj.read_text())
        cjd["status"] = "PAPER_DONE"
        cjd["verdict"] = verdict
        cjd["label"] = f"EXTERNAL_STRATEGY_BORROW_STAGEA_CHARTER_2026-09-12__{verdict}"
        cj.write_text(json.dumps(cjd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    marker = "External strategy borrow Soft-sell Stage A"
    if reg.exists() and marker not in reg.read_text():
        row = (
            f"| {marker} | **PAPER DONE / {verdict}** (2026-09-12) | "
            f"public RSI70/BB/MFI Soft-sell motifs · ext promote>observe **{len(ext_promote)}** · "
            f"observe still_best_vs_ext **{observe_still_best_vs_ext}** · "
            f"no scrape-login / no live / no fuse · Soft∥Sleeve OPEN unchanged · "
            f"`EXTERNAL_STRATEGY_BORROW_STAGEA_SCREEN.md` |\n"
        )
        lines_r = reg.read_text().splitlines(True)
        out_r = []
        done = False
        for l in lines_r:
            out_r.append(l)
            if not done and (
                "Soft-assist DL tip-MDD sell Stage A" in l
                or "Research posture lock (rule-path first" in l
                or "Soft∥Sleeve borrow-promote Stage A" in l
            ):
                out_r.append(row)
                done = True
        if done:
            reg.write_text("".join(out_r))

    print(
        json.dumps(
            {
                "verdict": verdict,
                "ext_promote": [r["id"] for r in ext_promote],
                "observe_held": observe["heldout_score"],
                "observe_still_best_vs_ext": observe_still_best_vs_ext,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
