#!/usr/bin/env python3
"""Stage A paper: Soft × Sleeve joint-actuator fuse screen — NO live / NO ops auto-fuse.

Charter: research/ops/SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER.md
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
from sleeve_tilt_helpers import (
    ALPHA,
    CHAMPION_ID,
    SIGN,
    SIGNAL_KIND,
    SIGNAL_WINDOW,
    rebuild_targets_from_score,
    sleeve_signal_panel,
)
from soft_assist_helpers import (
    LIVE_KD,
    OBSERVE_CHAL_ID,
    build_observe_buy_scores,
    build_observe_sell_panel,
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
OUT = ROOT / "repro/soft-sleeve-paper-fuse-stagea"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
LIVE_STACK = "LIVE_STACK"
SOFT_ONLY = "SOFT_ONLY_ON_STACK"
SLEEVE_ONLY = "SLEEVE_ONLY"
HALF_ALPHA = float(ALPHA) * 0.5


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


def run_book(market, target, regime, dividends, *, scores, buy_ok, sell_scores=None):
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


def build_tilt_target(
    market: pd.DataFrame,
    sleeve: pd.DataFrame,
    regime: pd.Series,
    *,
    alpha: float,
    tilt_scale: pd.Series | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, SIGNAL_KIND, SIGNAL_WINDOW)
    if tilt_scale is not None:
        scale = tilt_scale.reindex(tilt.index).fillna(0.0).astype(float)
        tilt = tilt.mul(scale, axis=0)
    new_score = base_score + float(SIGN) * float(alpha) * tilt
    return rebuild_targets_from_score(new_score, regime), tilt


def gate_panel_by_days(panel: pd.DataFrame, day_gate: pd.Series, *, neutral: float) -> pd.DataFrame:
    g = day_gate.reindex(panel.index).fillna(False).astype(float)
    return float(neutral) + (panel.astype(float) - float(neutral)).mul(g, axis=0)


def blend_nav(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    j = (
        a[["date", "nav"]]
        .rename(columns={"nav": "nav_a"})
        .merge(b[["date", "nav"]].rename(columns={"nav": "nav_b"}), on="date", how="inner")
        .sort_values("date")
        .reset_index(drop=True)
    )
    ra = j["nav_a"] / float(j["nav_a"].iloc[0])
    rb = j["nav_b"] / float(j["nav_b"].iloc[0])
    return pd.DataFrame({"date": j["date"], "nav": 0.5 * (ra + rb) * float(a["nav"].iloc[0])})


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
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
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
    _p, sleeve, target_live, regime = e16_features(market)
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
    soft_buy = build_observe_buy_scores(kd_scores, lows)
    soft_sell = build_observe_sell_panel(highs)

    target_sleeve, tilt = build_tilt_target(market, sleeve, regime, alpha=float(ALPHA))
    target_half, _ = build_tilt_target(market, sleeve, regime, alpha=HALF_ALPHA)
    sleeve_fire = tilt.max(axis=1) > 0.0
    soft_sell_fire = (soft_sell > 1.0 + 1e-12).any(axis=1)

    soft_buy_gated = kd_scores.astype(float) + (
        soft_buy.astype(float) - kd_scores.astype(float)
    ).mul(sleeve_fire.reindex(kd_scores.index).fillna(False).astype(float), axis=0)
    soft_sell_gated = gate_panel_by_days(soft_sell, sleeve_fire, neutral=1.0)
    target_sleeve_gate_soft, _ = build_tilt_target(
        market, sleeve, regime, alpha=float(ALPHA), tilt_scale=soft_sell_fire.astype(float)
    )

    jobs = [
        (LIVE_STACK, "base", target_live, kd_scores, None),
        (SOFT_ONLY, "soft_only", target_live, soft_buy, soft_sell),
        (SLEEVE_ONLY, "sleeve_only", target_sleeve, kd_scores, None),
        ("FUSE_ADDITIVE", "fuse", target_sleeve, soft_buy, soft_sell),
        ("FUSE_SOFT_GATE_SLEEVE", "fuse", target_live, soft_buy_gated, soft_sell_gated),
        ("FUSE_SLEEVE_GATE_SOFT", "fuse", target_sleeve_gate_soft, kd_scores, None),
        ("FUSE_HALF_ALPHA", "fuse", target_half, soft_buy, soft_sell),
    ]

    print(f"Stage A books: {len(jobs) + 1} (incl NAV_BLEND_50 diagnostic)", flush=True)
    rows = []
    navs: dict[str, pd.DataFrame] = {}
    win_base = asof = None
    for i, (book_id, track, target, scores, sell) in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] {book_id}", flush=True)
        res = run_book(
            market, target, regime, dividends, scores=scores, buy_ok=kd_ok, sell_scores=sell
        )
        navs[book_id] = res["nav"]
        safe = book_id.lower().replace(" ", "_")
        res["nav"].to_csv(OUT / "outputs" / f"{safe}_daily_nav.csv", index=False)
        win = {w: window_stats(res["nav"], a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        if book_id == LIVE_STACK:
            win_base = win
            asof = pd.to_datetime(res["nav"]["date"]).max()
            tip = tip_gate(res["nav"], res["nav"], asof)
            held = {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "score": 0.0}
        else:
            tip = tip_gate(navs[LIVE_STACK], res["nav"], asof)
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
                    "is_soft_only": book_id == SOFT_ONLY,
                    "is_sleeve_only": book_id == SLEEVE_ONLY,
                    "is_fuse": track == "fuse",
                    "is_diagnostic": False,
                    "soft_observe_ref": OBSERVE_CHAL_ID,
                    "sleeve_observe_ref": CHAMPION_ID,
                },
            )
        )

    print("  [diag] NAV_BLEND_50", flush=True)
    blend = blend_nav(navs[SOFT_ONLY], navs[SLEEVE_ONLY])
    blend.to_csv(OUT / "outputs" / "nav_blend_50_daily_nav.csv", index=False)
    win_b = {w: window_stats(blend, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    tip_b = tip_gate(navs[LIVE_STACK], blend, asof)
    held_b = held_score(win_base["heldout_2019_plus"], win_b["heldout_2019_plus"])
    rows.append(
        book_row(
            book_id="NAV_BLEND_50",
            track="diagnostic",
            tip=tip_b,
            held=held_b,
            win=win_b,
            n_fills=0,
            extra={
                "is_soft_only": False,
                "is_sleeve_only": False,
                "is_fuse": False,
                "is_diagnostic": True,
                "soft_observe_ref": OBSERVE_CHAL_ID,
                "sleeve_observe_ref": CHAMPION_ID,
            },
        )
    )

    soft_row = next(r for r in rows if r["id"] == SOFT_ONLY)
    sleeve_row = next(r for r in rows if r["id"] == SLEEVE_ONLY)
    ranked = sorted(
        rows,
        key=lambda r: (1 if r.get("promote_shaped") else 0, r["heldout_score"]),
        reverse=True,
    )
    fuse_promote = [r for r in ranked if r.get("is_fuse") and r.get("promote_shaped")]
    beats_soft = [r for r in fuse_promote if r["heldout_score"] > soft_row["heldout_score"]]
    beats_sleeve = [r for r in fuse_promote if r["heldout_score"] > sleeve_row["heldout_score"]]
    beats_both = [
        r
        for r in fuse_promote
        if r["heldout_score"] > soft_row["heldout_score"]
        and r["heldout_score"] > sleeve_row["heldout_score"]
    ]
    better_indep = max(soft_row["heldout_score"], sleeve_row["heldout_score"])

    if beats_both:
        verdict = "FUSE_PROMOTE_SHAPED_BEATS_BOTH"
    elif beats_soft or beats_sleeve:
        verdict = "FUSE_BEATS_ONE_NOT_BOTH"
    elif fuse_promote:
        verdict = "BEATS_LIVE_NO_INDEPENDENT_LIFT"
    else:
        verdict = "NO_LIFT"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN",
        "charter": "research/ops/SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "ops_auto_fuse": False,
        "observe_swap": False,
        "asof": str(pd.Timestamp(asof).date()),
        "verdict": verdict,
        "soft_observe_id": OBSERVE_CHAL_ID,
        "sleeve_observe_id": CHAMPION_ID,
        "sleeve_alpha": float(ALPHA),
        "soft_only_heldout_score": soft_row["heldout_score"],
        "sleeve_only_heldout_score": sleeve_row["heldout_score"],
        "better_independent_heldout_score": better_indep,
        "n_books": len(rows),
        "n_fuse_promote_shaped": len(fuse_promote),
        "n_fuse_beats_both": len(beats_both),
        "n_fuse_beats_soft_only": len(beats_soft),
        "n_fuse_beats_sleeve_only": len(beats_sleeve),
        "fuse_promote_shaped_ids": [r["id"] for r in fuse_promote],
        "fuse_beats_both_ids": [r["id"] for r in beats_both],
        "books": ranked,
        "non_actions": [
            "No Soft×Sleeve auto-fuse on operating path (Gate H stays)",
            "No Soft or Sleeve observe swap",
            "No live Soft-assist / Sleeve-tilt / Soft-Frozen / KD / TEL / E45 wire",
            "No joint ACCEPT / cutover unlock",
            "No Soft-buy MLP deepen",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    blob = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "soft_sleeve_paper_fuse_stagea_screen.json").write_text(
        blob, encoding="utf-8"
    )
    (OPS / "SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN.json").write_text(blob, encoding="utf-8")

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
        "# Soft × Sleeve Paper Fuse Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Verdict: **`{verdict}`** · books **{payload['n_books']}**",
        "Live wire: **false** · ops auto-fuse: **false** · observe swap: **false**",
        "",
        "## Question",
        "",
        "Does any Soft×Sleeve joint-actuator fuse book promote-shaped-beat Soft-only "
        f"and Sleeve-only on `{LIVE_STACK}`?",
        "",
        "## Summary",
        "",
        f"- Soft-only `{SOFT_ONLY}` held **{soft_row['heldout_score']:.3f}** "
        f"(Soft observe softs `{OBSERVE_CHAL_ID}` on stack)",
        f"- Sleeve-only `{SLEEVE_ONLY}` (`{CHAMPION_ID}`) held **{sleeve_row['heldout_score']:.3f}**",
        f"- Better independent held **{better_indep:.3f}**",
        f"- Fuse promote-shaped: **{len(fuse_promote)}** → `{[r['id'] for r in fuse_promote]}`",
        f"- Fuse beats both independents: **{len(beats_both)}** → `{[r['id'] for r in beats_both]}`",
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
        "- `FUSE_*` books apply Soft observe softs and/or Sleeve observe tilt together on `LIVE_STACK`.",
        "- `NAV_BLEND_50` is post-hoc diagnostic only (not a tradable joint book).",
        "- Operating Soft∥Sleeve dual observe and Gate H auto-fuse ban are unchanged.",
        "",
        "## Non-actions",
        "",
    ]
    lines.extend(f"- {x}" for x in payload["non_actions"])
    lines += [
        "",
        "## Label",
        "",
        f"`SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN_{payload['asof']}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "reports" / "SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")
    (OPS / "SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")

    zh = "\n".join(
        [
            "# Soft × Sleeve 紙上合體 Stage A 篩選",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"判決：**`{verdict}`**",
            "",
            f"- Soft-only held **{soft_row['heldout_score']:.3f}**",
            f"- Sleeve-only held **{sleeve_row['heldout_score']:.3f}**",
            f"- Fuse promote-shaped **{len(fuse_promote)}** · beats both **{len(beats_both)}**",
            "",
            "操作路徑仍禁自動 fuse · 不換 observe · 不接 live。詳表見英文稿。",
            "",
            f"`SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN_{payload['asof']}__{verdict}`",
            "",
        ]
    )
    (OPS / "SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    for path in (
        OPS / "SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER.md",
        OPS / "SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER.zh-TW.md",
    ):
        if not path.exists():
            continue
        t = path.read_text()
        t = t.replace(
            "Status: **PAPER STAGE A CHARTER OPEN** · screen **NOT RUN** until explicit human go",
            f"Status: **PAPER STAGE A DONE** · verdict **`{verdict}`**",
        )
        t = t.replace(
            "狀態：**PAPER STAGE A CHARTER OPEN** · 篩選**未跑**（等你明確說開始）",
            f"狀態：**PAPER STAGE A DONE** · 判決 **`{verdict}`**",
        )
        t = t.replace(
            "`SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER_2026-09-12__PAPER_OPEN__SCREEN_NOT_RUN`",
            f"`SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER_2026-09-12__{verdict}`",
        )
        path.write_text(t)

    cj = OPS / "SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER.json"
    if cj.exists():
        cjd = json.loads(cj.read_text())
        cjd["status"] = "PAPER_SCREEN_DONE"
        cjd["screen_run"] = True
        cjd["verdict"] = verdict
        cjd["label"] = f"SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER_2026-09-12__{verdict}"
        cj.write_text(json.dumps(cjd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    marker = "Soft×Sleeve paper fuse Stage A screen"
    if reg.exists() and marker not in reg.read_text():
        row = (
            f"| {marker} | **PAPER DONE / {verdict}** (2026-09-12) | "
            f"fuse promote-shaped **{len(fuse_promote)}** · beats both **{len(beats_both)}** · "
            f"Soft-only held **{soft_row['heldout_score']:.3f}** · Sleeve-only held "
            f"**{sleeve_row['heldout_score']:.3f}** · ops auto-fuse still FORBIDDEN · "
            f"no live / no observe swap · `SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN.md` |\n"
        )
        lines_r = reg.read_text().splitlines(True)
        out_r = []
        done = False
        for l in lines_r:
            if "Soft×Sleeve paper fuse Stage A charter" in l and "SCREEN NOT RUN" in l:
                l = l.replace(
                    "**PAPER CHARTER OPEN / SCREEN NOT RUN**",
                    f"**PAPER CHARTER OPEN / SCREEN DONE {verdict}**",
                )
            out_r.append(l)
            if not done and (
                "Soft×Sleeve paper fuse Stage A charter" in l
                or "Month-end Soft∥Sleeve promote gate" in l
            ):
                out_r.append(row)
                done = True
        if done:
            reg.write_text("".join(out_r))

    print(
        json.dumps(
            {
                "verdict": verdict,
                "fuse_promote": [r["id"] for r in fuse_promote],
                "beats_both": [r["id"] for r in beats_both],
                "soft_only_held": soft_row["heldout_score"],
                "sleeve_only_held": sleeve_row["heldout_score"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
