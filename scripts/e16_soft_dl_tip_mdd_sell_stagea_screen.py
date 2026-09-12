#!/usr/bin/env python3
"""Stage A paper: Soft-assist tip-MDD / giveback Soft-sell role — NO live wire.

Charter: research/ops/SOFT_DL_TIP_MDD_SELL_STAGEA_CHARTER.md

New label (forward path-MDD / giveback) × Soft sell role.
Does not deepen Soft-buy MLP · does not reopen T2 Soft-buy boosts.
Soft observe KEEP: SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05 · Sleeve KEEP · no fuse.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
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
OUT = ROOT / "repro/soft-dl-tip-mdd-sell-stagea"
OPS = ROOT / "research/ops"
SOFT_BASE = base.SOFT_BASE
PATH_H = 10
MDD_TAU = 0.03
SEED = 42


def build_fwd_path_mdd(market: pd.DataFrame, codes: list[str], dates: pd.DatetimeIndex) -> np.ndarray:
    """Worst peak-to-trough drawdown over the next PATH_H bars starting at t."""
    px = (
        market.pivot_table(index="date", columns="code", values="adj_close", aggfunc="last")
        .reindex(index=dates, columns=codes)
        .sort_index()
    )
    arr = px.to_numpy(dtype=np.float64)
    n_t, n_c = arr.shape
    out = np.full((n_t, n_c), np.nan, dtype=np.float64)
    for t in range(n_t):
        end = min(n_t, t + PATH_H + 1)
        if end - t < 2:
            continue
        window = arr[t:end, :]
        base_px = window[0:1, :]
        with np.errstate(invalid="ignore", divide="ignore"):
            path = window / base_px
        peak = np.maximum.accumulate(path, axis=0)
        dd = path / peak - 1.0
        out[t, :] = np.nanmin(dd, axis=0)
    return out


def _pack_tipmdd(X, path_mdd, train_mask, *, mode: str):
    Xt = X[train_mask].reshape(-1, X.shape[-1]).astype(np.float64)
    ym = path_mdd[train_mask].reshape(-1)
    ok = np.isfinite(ym) & np.isfinite(Xt).all(axis=1)
    if int(ok.sum()) < base.MIN_TRAIN_ROWS:
        return None
    Xt, ym = Xt[ok], ym[ok]
    if mode == "reg":
        yt = np.clip(-ym, 0.0, None)
        lo, hi = np.quantile(yt, [0.01, 0.99])
        yt = np.clip(yt, lo, hi)
        w = 1.0 + yt * 5.0
        return Xt, yt.astype(np.float64), w.astype(np.float64), "reg"
    yt = (ym <= -float(MDD_TAU)).astype(np.float64)
    w = 1.0 + np.clip(-ym, 0.0, None) * 8.0
    return Xt, yt, w.astype(np.float64), "clf"


def walk_forward_sell_tipmdd(dates, codes, X, path_mdd, *, alpha: float, mode: str, seed_off: int = 0):
    boost = np.zeros((len(dates), len(codes)), dtype=np.float64)
    years = np.array([int(d.year) for d in dates])
    for y in sorted(set(years.tolist())):
        train = years < y
        apply = years == y
        if not apply.any():
            continue
        pack = _pack_tipmdd(X, path_mdd, train, mode=mode)
        if pack is None:
            continue
        Xt, yt, w, task = pack
        model = base.TinyMLP(Xt.shape[1], n_hidden=8, seed=SEED + seed_off + y, task=task)
        model.fit(Xt, yt, sample_weight=w)
        for ti in np.where(apply)[0]:
            score = model.predict(X[ti].astype(np.float64))
            if task == "reg":
                mu, sd = float(np.nanmean(score)), float(np.nanstd(score) + 1e-6)
                risk = base._sigmoid((score - mu) / sd)
            else:
                risk = np.clip(score, 0.0, 1.0)
            boost[ti, :] = float(alpha) * risk
    return pd.DataFrame(boost, index=dates, columns=codes)


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
    sell_prior = soft_sell_panel(highs[SELL_HIGH_ID], boost=SOFT_BOOST)
    sell_observe = soft_sell_panel(highs[SELL_HIGH_ID], boost=SELL_SOFT_BOOST)

    print("building HIGH features + fwd path-MDD labels ...", flush=True)
    dates, X_high = base.build_feature_cube(highs, list(base.HIGH_IDS), list(base.FIN))
    fwd = base.build_fwd_returns(market, list(base.FIN), dates)
    path_mdd = build_fwd_path_mdd(market, list(base.FIN), dates)

    print("  walk-forward T3 control (fwd<0) ...", flush=True)
    sell_t3 = base.walk_forward_sell_down(dates, list(base.FIN), X_high, fwd, alpha=0.5)
    print("  walk-forward tip-MDD clf α=0.5 ...", flush=True)
    sell_clf = walk_forward_sell_tipmdd(
        dates, list(base.FIN), X_high, path_mdd, alpha=0.5, mode="clf", seed_off=0
    )
    print("  walk-forward tip-MDD reg α=0.5 ...", flush=True)
    sell_reg = walk_forward_sell_tipmdd(
        dates, list(base.FIN), X_high, path_mdd, alpha=0.5, mode="reg", seed_off=101
    )
    sell_clf_a025 = sell_clf * 0.5

    def align(df: pd.DataFrame) -> pd.DataFrame:
        return df.reindex(index=kd_scores.index, columns=kd_scores.columns).fillna(0.0)

    sell_t3 = align(sell_t3)
    sell_clf = align(sell_clf)
    sell_reg = align(sell_reg)
    sell_clf_a025 = align(sell_clf_a025)
    rsi_gate = highs[SELL_HIGH_ID].reindex_like(kd_scores).fillna(False).astype(float)
    sell_clf_rsi = sell_clf * rsi_gate

    jobs = [
        (SOFT_BASE, "base", None, None),
        (OBSERVE_CHAL_ID, "observe", observe_buy, sell_observe),
        (PRIOR_OBSERVE_ID, "prior_soft", observe_buy, sell_prior),
        ("DL_T3_SELL_DOWN_a05", "t3_control_fwd_lt0", observe_buy, 1.0 + sell_t3),
        ("DL_TIPMDD_SELL_CLF_a05", "tipmdd_clf", observe_buy, 1.0 + sell_clf),
        ("DL_TIPMDD_SELL_REG_a05", "tipmdd_reg", observe_buy, 1.0 + sell_reg),
        ("DL_TIPMDD_SELL_CLF_a025", "tipmdd_clf", observe_buy, 1.0 + sell_clf_a025),
        ("DL_TIPMDD_SELL_CLF_a05__RSI_GATE", "tipmdd_clf_rsi_gate", observe_buy, 1.0 + sell_clf_rsi),
    ]

    print(f"Stage A books: {len(jobs)} (tip-MDD sell-role · no Soft-buy deepen)", flush=True)
    rows = []
    nav_base = win_base = asof = None
    for i, (book_id, track, scores, sell) in enumerate(jobs, 1):
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
                    "is_t3_control": book_id == "DL_T3_SELL_DOWN_a05",
                    "is_dl": track.startswith("tipmdd_") or track.startswith("t3_"),
                    "is_tipmdd": track.startswith("tipmdd_"),
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
    tipmdd_promote = [r for r in promote_vs_observe if r.get("is_tipmdd")]
    t3_promote = [r for r in promote_vs_observe if r.get("is_t3_control")]
    tipmdd_scores = [r["heldout_score"] for r in ranked if r.get("is_tipmdd")]
    observe_still_best_vs_tipmdd = observe["heldout_score"] >= (
        max(tipmdd_scores) if tipmdd_scores else -9.0
    )

    if tipmdd_promote:
        verdict = "TIPMDD_SELL_PROMOTE_SHAPED_BEATS_OBSERVE"
    elif t3_promote and not tipmdd_promote:
        verdict = "T3_CONTROL_ONLY_NO_TIPMDD_LIFT"
    elif promote_vs_observe:
        verdict = "OTHER_PROMOTE_ONLY_NO_TIPMDD_LIFT"
    elif beat_live:
        verdict = "BEATS_LIVE_NO_OBSERVE_LIFT"
    else:
        verdict = "NO_LIFT"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_DL_TIP_MDD_SELL_STAGEA_SCREEN",
        "charter": "research/ops/SOFT_DL_TIP_MDD_SELL_STAGEA_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "soft_x_sleeve_fuse": False,
        "observe_swap": False,
        "path_h": PATH_H,
        "mdd_tau": MDD_TAU,
        "asof": str(pd.Timestamp(asof).date()),
        "verdict": verdict,
        "observe_id": OBSERVE_CHAL_ID,
        "observe_heldout_score": observe["heldout_score"],
        "observe_still_best_vs_tipmdd": bool(observe_still_best_vs_tipmdd),
        "n_books": len(rows),
        "n_beat_live": len(beat_live),
        "n_promote_shaped_beats_observe": len(promote_vs_observe),
        "n_tipmdd_promote_shaped_beats_observe": len(tipmdd_promote),
        "beat_live_ids": [r["id"] for r in beat_live],
        "promote_shaped_ids": [r["id"] for r in promote_vs_observe],
        "tipmdd_promote_shaped_ids": [r["id"] for r in tipmdd_promote],
        "books": ranked,
        "non_actions": [
            "No live Soft-assist / Soft-Frozen / KD / TEL / E45 / Sleeve wire",
            "No Soft-assist or Sleeve observe swap from this screen",
            "No Soft×Sleeve auto-combo",
            "No same-MLP Soft-buy deepen",
            "No T2 Soft-buy boost reopen",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    blob = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "soft_dl_tip_mdd_sell_stagea_screen.json").write_text(blob, encoding="utf-8")
    (OPS / "SOFT_DL_TIP_MDD_SELL_STAGEA_SCREEN.json").write_text(blob, encoding="utf-8")

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
        "# Soft-Assist DL Tip-MDD / Giveback Sell-Role Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Verdict: **`{verdict}`** · books **{payload['n_books']}**",
        "Live wire: **false** · Soft×Sleeve fuse: **forbidden** · observe swap: **false**",
        "",
        "## Question",
        "",
        "Does Soft **sell** from tip-path-MDD / giveback labels promote-shaped-beat Soft observe "
        "`SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` (vs T3 `fwd<0` control)?",
        "",
        "## Summary",
        "",
        f"- Observe `{OBSERVE_CHAL_ID}` held **{observe['heldout_score']:.3f}** · tip_mdd_clean **{observe['tip_mdd_clean']}**",
        f"- Tip-MDD promote-shaped > observe: **{len(tipmdd_promote)}** → `{[r['id'] for r in tipmdd_promote]}`",
        f"- Observe still best vs tip-MDD DL: **{observe_still_best_vs_tipmdd}**",
        f"- Beat live: **{len(beat_live)}**",
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
        f"- Labels: forward path-MDD over H={PATH_H}; clf threshold τ={MDD_TAU:.0%} · reg = −path_mdd severity.",
        "- Buy soft fixed at Soft observe; only Soft **sell** amplitude is learned.",
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
        f"`SOFT_DL_TIP_MDD_SELL_STAGEA_SCREEN_{payload['asof']}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "reports" / "SOFT_DL_TIP_MDD_SELL_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")
    (OPS / "SOFT_DL_TIP_MDD_SELL_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")

    zh = "\n".join(
        [
            "# Soft-Assist DL Tip-MDD／Giveback 賣邊 Stage A 篩選",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"判決：**`{verdict}`**",
            "",
            f"- Observe held **{observe['heldout_score']:.3f}**",
            f"- Tip-MDD promote>observe **{len(tipmdd_promote)}** → `{[r['id'] for r in tipmdd_promote]}`",
            f"- Observe 仍優於 tip-MDD DL：**{observe_still_best_vs_tipmdd}**",
            "",
            "詳表見英文稿。不接 live · 不換 Soft／Sleeve observe · 不融合 · 不加深 Soft-buy。",
            "",
            f"`SOFT_DL_TIP_MDD_SELL_STAGEA_SCREEN_{payload['asof']}__{verdict}`",
            "",
        ]
    )
    (OPS / "SOFT_DL_TIP_MDD_SELL_STAGEA_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    for path, open_tok, done_tok in (
        (
            OPS / "SOFT_DL_TIP_MDD_SELL_STAGEA_CHARTER.md",
            "**PAPER STAGE A OPEN**",
            f"**PAPER STAGE A DONE** · verdict **`{verdict}`**",
        ),
        (
            OPS / "SOFT_DL_TIP_MDD_SELL_STAGEA_CHARTER.zh-TW.md",
            "**PAPER STAGE A OPEN**",
            f"**PAPER STAGE A DONE** · 判決 **`{verdict}`**",
        ),
    ):
        if path.exists():
            t = path.read_text().replace(open_tok, done_tok)
            t = t.replace(
                "`SOFT_DL_TIP_MDD_SELL_STAGEA_CHARTER_2026-09-12__PAPER_OPEN`",
                f"`SOFT_DL_TIP_MDD_SELL_STAGEA_CHARTER_2026-09-12__{verdict}`",
            )
            path.write_text(t)
    cj = OPS / "SOFT_DL_TIP_MDD_SELL_STAGEA_CHARTER.json"
    if cj.exists():
        cjd = json.loads(cj.read_text())
        cjd["status"] = "PAPER_DONE"
        cjd["verdict"] = verdict
        cjd["label"] = f"SOFT_DL_TIP_MDD_SELL_STAGEA_CHARTER_2026-09-12__{verdict}"
        cj.write_text(json.dumps(cjd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    marker = "Soft-assist DL tip-MDD sell Stage A"
    if reg.exists() and marker not in reg.read_text():
        row = (
            f"| {marker} | **PAPER DONE / {verdict}** (2026-09-12) | "
            f"new label path-MDD/giveback · Soft sell role · tip-MDD promote>observe **{len(tipmdd_promote)}** · "
            f"observe still_best_vs_tipmdd **{observe_still_best_vs_tipmdd}** · "
            f"no live / no fuse / Soft∥Sleeve OPEN unchanged · `SOFT_DL_TIP_MDD_SELL_STAGEA_SCREEN.md` |\n"
        )
        lines_r = reg.read_text().splitlines(True)
        out_r = []
        done = False
        for l in lines_r:
            out_r.append(l)
            if not done and (
                "Research posture lock (rule-path first" in l
                or "Soft-assist DL T2 tiny causal Transformer Stage A" in l
                or "Soft-assist DL 4-track Stage A" in l
            ):
                out_r.append(row)
                done = True
        if done:
            reg.write_text("".join(out_r))

    print(
        json.dumps(
            {
                "verdict": verdict,
                "tipmdd_promote": [r["id"] for r in tipmdd_promote],
                "observe_held": observe["heldout_score"],
                "observe_still_best_vs_tipmdd": observe_still_best_vs_tipmdd,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
