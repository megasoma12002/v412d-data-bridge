#!/usr/bin/env python3
"""Stage A paper screen: Sleeve tip-MDD-first denser grid vs LIVE_STACK (paper only).

Charter: research/ops/SLEEVE_TIP_MDD_GRID_CHARTER.md

Mechanism: sleeve NAV signals tilt Soft-Frozen router score → clip/blend
targets. Within-sleeve KD_OPT + TEL_EQUAL unchanged. Soft-Frozen clips KEEP.
No Soft-assist / E45 / live wire.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
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
OUT = ROOT / "repro/sleeve-tip-mdd-grid"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0

# Tip-MDD-first denser grid (finite ≤14 challengers + LIVE)
# Prioritize hygiene around seed MA60 + sole prior tip-MDD-clean RSI14_LT30_a02
SEED_ID = "SLEEVE_BELOW_MA60_a01"
SPECS = (
    # (short, window, kind, alpha)
    ("BELOW_MA60", 60, "ma", 0.025),
    ("BELOW_MA60", 60, "ma", 0.05),
    ("BELOW_MA60", 60, "ma", 0.075),
    ("BELOW_MA60", 60, "ma", 0.10),
    ("BELOW_MA60", 60, "ma", 0.125),
    ("RSI14_LT30", 14, "rsi_lt30", 0.10),
    ("RSI14_LT30", 14, "rsi_lt30", 0.125),
    ("RSI14_LT30", 14, "rsi_lt30", 0.15),
    ("RSI14_LT30", 14, "rsi_lt30", 0.175),
    ("RSI14_LT30", 14, "rsi_lt30", 0.20),
    ("RSI14_LT30", 14, "rsi_lt30", 0.225),
    ("BELOW_MA40", 40, "ma", 0.025),
    ("BELOW_MA40", 40, "ma", 0.05),
)


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
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        out[wname] = {
            "giveback_pp": None if gb is None else float(gb),
            "gate": gate,
            "rel_nav": float(cn.iloc[-1] / bn.iloc[-1]),
            "mdd_improve_pp": float(mdd_delta_pp(b_mdd, c_mdd)),
        }
    return out


def tip_mdd_clean(tip: dict) -> bool:
    for w in ("ytd", "trailing_1y"):
        md = tip.get(w, {}).get("mdd_improve_pp")
        if md is None or float(md) < 0.0:
            return False
    return True


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


def rebuild_targets_from_score(score: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    out = []
    cur = soft.START_WEIGHTS.copy()
    for i, _dt in enumerate(score.index):
        pri = soft.REGIME_PRIORS[str(regime.iloc[i])]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = soft.apply_soft_frozen_clips(cand)
        desired = soft.BLEND_OLD * cur + soft.BLEND_NEW * cand
        if float(np.abs(desired - cur).sum()) >= soft.REBALANCE_L1_MIN:
            cur = desired
        out.append(cur.copy())
    return pd.DataFrame(out, index=score.index, columns=["Financial", "Telecom", "0050"])


def sleeve_signal_panel(sleeve_rets: pd.DataFrame, kind: str, window: int) -> pd.DataFrame:
    """Causal same-day panel matching prior Track C (seed reconfirm)."""
    nav = (1.0 + sleeve_rets.fillna(0.0)).cumprod()
    out = pd.DataFrame(0.0, index=sleeve_rets.index, columns=list(sleeve_rets.columns))
    for col in sleeve_rets.columns:
        close = nav[col]
        if kind == "ma":
            min_p = max(20, window // 2)
            ma = close.rolling(window, min_periods=min_p).mean()
            out[col] = (close < ma).astype(float)
        elif kind == "rsi_lt30":
            delta = close.diff()
            gain = delta.clip(lower=0.0)
            loss = (-delta).clip(lower=0.0)
            avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
            avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
            rs = avg_gain / avg_loss.replace(0.0, np.nan)
            rsi = 100.0 - (100.0 / (1.0 + rs))
            out[col] = (rsi < 30.0).astype(float)
        elif kind == "mom_neg":
            mom = close / close.shift(window) - 1.0
            out[col] = (mom < 0.0).astype(float)
        else:
            raise ValueError(kind)
    return out.fillna(0.0)


def sim_live_stack(market, target, regime, dividends, scores, buy_ok):
    return simulate_core(
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
    )


def alpha_tag(a: float) -> str:
    return str(a).replace(".", "")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    import e21_forward_pipeline as e21

    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse sleeve-tilt screen while LIVE_E45_STITCH is True")

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, sleeve, target_live, regime = e16_features(market)
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
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

    print("LIVE_STACK ...", flush=True)
    nav_live, fills_live, meta_live = sim_live_stack(
        market, target_live, regime, dividends, kd_scores, kd_ok
    )
    assert meta_live.get("exact_t1_ok")
    win_live = {w: window_stats(nav_live, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    asof = pd.to_datetime(nav_live["date"]).max()
    held_live_score = 0.0  # self

    jobs = []
    for short, window, kind, alpha in SPECS:
        tilt = sleeve_signal_panel(sleeve, kind, window)
        book_id = f"SLEEVE_{short}_a{alpha_tag(alpha)}"
        new_score = base_score + 1.0 * float(alpha) * tilt
        new_target = rebuild_targets_from_score(new_score, regime)
        jobs.append((book_id, short, float(alpha), new_target))

    assert any(j[0] == SEED_ID for j in jobs), "seed SLEEVE_BELOW_MA60_a01 missing from grid"
    print(f"Tip-MDD grid challengers: {len(jobs)} (+ LIVE_STACK)", flush=True)

    rows = []
    live_tip = tip_gate(nav_live, nav_live, asof)
    rows.append(
        {
            "id": "LIVE_STACK",
            "signal": "none",
            "alpha": None,
            "heldout_score": 0.0,
            "mdd_improve_pp": 0.0,
            "cagr_giveback_pp": 0.0,
            "tip_ytd": live_tip["ytd"]["gate"],
            "tip_1y": live_tip["trailing_1y"]["gate"],
            "tip_clean": True,
            "tip_mdd_ytd_pp": live_tip["ytd"].get("mdd_improve_pp", 0.0),
            "tip_mdd_1y_pp": live_tip["trailing_1y"].get("mdd_improve_pp", 0.0),
            "tip_mdd_clean": True,
            "promote_shaped": False,
            "coexist": False,
            "vs_live_heldout_delta": 0.0,
            "full_cagr": win_live["full"].get("cagr"),
            "full_mdd": win_live["full"].get("max_drawdown"),
            "heldout_cagr": win_live["heldout_2019_plus"].get("cagr"),
            "heldout_mdd": win_live["heldout_2019_plus"].get("max_drawdown"),
            "sealed_cagr": win_live["sealed_2023_plus"].get("cagr"),
            "sealed_mdd": win_live["sealed_2023_plus"].get("max_drawdown"),
            "n_fills": int(len(fills_live)),
            "is_seed": False,
        }
    )

    for i, (book_id, signal, alpha, tgt) in enumerate(jobs, 1):
        if i == 1 or i % 5 == 0 or i == len(jobs):
            print(f"  [{i}/{len(jobs)}] {book_id}", flush=True)
        nav, fills, meta = sim_live_stack(
            market, tgt, regime, dividends, kd_scores, kd_ok
        )
        assert meta.get("exact_t1_ok"), book_id
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        tip = tip_gate(nav_live, nav, asof)
        held = score_vs_base(win_live["heldout_2019_plus"], win["heldout_2019_plus"])
        tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
        mdd_ok = tip_mdd_clean(tip)
        coexist = bool(tip_clean and held["score"] > 0)
        rows.append(
            {
                "id": book_id,
                "signal": signal,
                "alpha": alpha,
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
                "coexist": coexist,
                "vs_live_heldout_delta": float(held["score"] - held_live_score),
                "full_cagr": win["full"].get("cagr"),
                "full_mdd": win["full"].get("max_drawdown"),
                "heldout_cagr": win["heldout_2019_plus"].get("cagr"),
                "heldout_mdd": win["heldout_2019_plus"].get("max_drawdown"),
                "sealed_cagr": win["sealed_2023_plus"].get("cagr"),
                "sealed_mdd": win["sealed_2023_plus"].get("max_drawdown"),
                "n_fills": int(len(fills)),
                "is_seed": book_id == SEED_ID,
            }
        )

    def rank_key(r):
        beat = bool(
            r.get("coexist") and r["id"] != "LIVE_STACK" and r.get("vs_live_heldout_delta", 0) > 0
        )
        no_pause = r["tip_ytd"] != "PAUSE_REVIEW" and r["tip_1y"] != "PAUSE_REVIEW"
        return (
            1 if r.get("promote_shaped") else 0,
            1 if r.get("tip_mdd_clean") else 0,
            1 if r.get("coexist") else 0,
            1 if beat else 0,
            1 if no_pause else 0,
            r["heldout_score"],
        )

    ranked = sorted(rows, key=rank_key, reverse=True)
    beat = [
        r
        for r in ranked
        if r["id"] != "LIVE_STACK" and r.get("coexist") and r["vs_live_heldout_delta"] > 0
    ]
    near = [
        r
        for r in ranked
        if r["id"] != "LIVE_STACK"
        and r.get("tip_clean")
        and r.get("vs_live_heldout_delta", -9) > -0.05
    ]
    coexist_other = [r for r in ranked if r["id"] != "LIVE_STACK" and r.get("coexist")]
    promote = [
        r for r in ranked
        if r["id"] != "LIVE_STACK" and r.get("promote_shaped")
    ]
    tip_mdd_clear_beat = [
        r for r in beat if r.get("tip_mdd_clean")
    ]
    if tip_mdd_clear_beat:
        verdict = "MDD_CLEAR_BEATS_LIVE"
    elif promote:
        verdict = "PROMOTE_SHAPED_NO_HELD_BEAT"  # shouldn't usually fire
    elif beat:
        verdict = "BEATS_LIVE_TIP_MDD_DIRTY"
    elif near:
        verdict = "NEAR_NO_BEAT"
    elif coexist_other:
        verdict = "COEXIST_NO_LIFT"
    else:
        verdict = "NO_LIFT"

    seed_row = next(r for r in ranked if r["id"] == SEED_ID)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SLEEVE_TIP_MDD_GRID_SCREEN",
        "charter": "research/ops/SLEEVE_TIP_MDD_GRID_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "asof": str(pd.Timestamp(asof).date()),
        "seed_id": SEED_ID,
        "seed": {
            "id": seed_row["id"],
            "tip_clean": seed_row["tip_clean"],
            "coexist": seed_row["coexist"],
            "heldout_score": seed_row["heldout_score"],
            "vs_live_heldout_delta": seed_row["vs_live_heldout_delta"],
        },
        "n_books": len(rows),
        "n_challengers": len(jobs),
        "n_beat_live": len(beat),
        "n_tip_clean_challengers": sum(
            1 for r in ranked if r["id"] != "LIVE_STACK" and r.get("tip_clean")
        ),
        "n_tip_mdd_clean_challengers": sum(
            1 for r in ranked if r["id"] != "LIVE_STACK" and r.get("tip_mdd_clean")
        ),
        "n_promote_shaped": len(promote),
        "n_coexist": len(coexist_other),
        "beat_live_ids": [r["id"] for r in beat[:40]],
        "tip_mdd_clear_beat_ids": [r["id"] for r in tip_mdd_clear_beat],
        "promote_shaped_ids": [r["id"] for r in promote],
        "near_ids": [r["id"] for r in near[:40]],
        "top20": [r["id"] for r in ranked[:20]],
        "verdict": verdict,
        "stage_a_grid": {
            "specs": [
                {"signal": s, "window": w, "kind": k, "alpha": a} for s, w, k, a in SPECS
            ],
            "sign": "+1 (oversold / below-trend)",
            "priority": "tip_mdd_clean first",
        },
        "books": ranked,
        "non_actions": [
            "No Soft-Frozen clip flip",
            "No live KD/TEL change",
            "No Soft-assist wire or observe pause",
            "No E45 stitch",
            "No Soft-assist x sleeve auto-combo",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    (OUT / "reports" / "sleeve_layer_tilt_screen.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OPS / "SLEEVE_TIP_MDD_GRID_SCREEN.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def pct(x):
        return "—" if x is None else f"{100 * float(x):.2f}%"

    def line(r):
        a = "—" if r["alpha"] is None else f"{r['alpha']:.2f}"
        seed = "Y" if r.get("is_seed") else ""
        return (
            f"| `{r['id']}` | {r['signal']} | {a} | {r['tip_ytd']} | {r['tip_1y']} | "
            f"{r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{pct(r['heldout_cagr'])} | {pct(r['heldout_mdd'])} | "
            f"{pct(r['sealed_cagr'])} | {pct(r['sealed_mdd'])} | {seed} |"
        )

    lines = [
        "# Sleeve-Layer Tilt Screen — Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Charter: `SLEEVE_TIP_MDD_GRID_CHARTER.md`",
        f"Verdict: **`{verdict}`** · books **{payload['n_books']}** · seed `{SEED_ID}`",
        "",
        "## Question",
        "",
        "Does Soft-Frozen router sleeve-NAV tilt tip-clean beat **LIVE_STACK** (clips KEEP, KD/TEL unchanged)?",
        "",
        "## Summary",
        "",
        f"- Beat live: **{payload['n_beat_live']}** → `{payload['beat_live_ids'][:12]}`",
        f"- Tip-clean challengers: **{payload['n_tip_clean_challengers']}** · coexist **{payload['n_coexist']}**",
        f"- Near (tip-clean, score &gt; −0.05): `{payload['near_ids'][:12]}`",
        f"- Seed `{SEED_ID}`: tip_clean={seed_row['tip_clean']} · coexist={seed_row['coexist']} · "
        f"held={seed_row['heldout_score']:.3f} · vs live Δ={seed_row['vs_live_heldout_delta']:.3f}",
        f"- Grid: tip-MDD-first SPECS ({len(SPECS)}) · seed `{SEED_ID}` · sign +1",
        "",
        "## Top 20",
        "",
        "| ID | Signal | α | Tip YTD | Tip 1y | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD | Seed |",
        "|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    lines.extend(line(r) for r in ranked[:20])
    lines += [
        "",
        "## LIVE_STACK reference",
        "",
        f"- full CAGR/MDD: {pct(rows[0]['full_cagr'])} / {pct(rows[0]['full_mdd'])}",
        f"- heldout CAGR/MDD: {pct(rows[0]['heldout_cagr'])} / {pct(rows[0]['heldout_mdd'])}",
        f"- sealed CAGR/MDD: {pct(rows[0]['sealed_cagr'])} / {pct(rows[0]['sealed_mdd'])}",
        "",
        "## Reading",
        "",
        "- Held score = MDD↑pp − 0.5·|CAGRΔpp| vs **LIVE_STACK**.",
        "- Prior Track C seed is hypothesis; this Stage A re-scores vs live stack + sealed.",
        "- Soft-assist observe stays independent.",
        "",
        "## Non-actions",
        "",
        "- No Soft-Frozen clip / KD / TEL / Soft-assist / E45 wire from this screen",
        "",
        "## Label",
        "",
        f"`SLEEVE_TIP_MDD_GRID_SCREEN_2026-09-10__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (OPS / "SLEEVE_TIP_MDD_GRID_SCREEN.md").write_text(md, encoding="utf-8")
    (OUT / "reports" / "SLEEVE_TIP_MDD_GRID_SCREEN.md").write_text(md, encoding="utf-8")

    zh = "\n".join(
        [
            "# Sleeve 層 tilt Screen — Stage A（paper）",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"總評：**`{verdict}`** · books **{payload['n_books']}** · 種子 `{SEED_ID}`",
            f"- 勝過 live：**{payload['n_beat_live']}** → `{payload['beat_live_ids'][:10]}`",
            f"- tip-clean：**{payload['n_tip_clean_challengers']}** · coexist：**{payload['n_coexist']}**",
            f"- 種子 held={seed_row['heldout_score']:.3f} · tip_clean={seed_row['tip_clean']}",
            "",
            "Soft-Frozen clips / KD_OPT / TEL **KEEP**。Soft-assist observe **不動**。",
            "",
            "英文：`SLEEVE_TIP_MDD_GRID_SCREEN.md`",
            "",
        ]
    )
    (OPS / "SLEEVE_TIP_MDD_GRID_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_books": payload["n_books"],
                "n_beat_live": payload["n_beat_live"],
                "n_tip_clean": payload["n_tip_clean_challengers"],
                "n_coexist": payload["n_coexist"],
                "seed": payload["seed"],
                "beat_live_ids": payload["beat_live_ids"][:15],
                "top10": payload["top20"][:10],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
