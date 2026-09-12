#!/usr/bin/env python3
"""Stage A paper: Soft-assist tiny MLP (numpy) buy soft — NO live wire.

Charter: research/ops/SOFT_DL_MLP_STAGEA_CHARTER.md

Walk-forward tiny feed-forward net on causal TA LOW features → additive Soft
buy boost on LIVE KD_OPT. Soft-Frozen KEEP · TEL_EQUAL KEEP · Soft-assist
observe KEEP · Sleeve observe UNCHANGED · no Soft×Sleeve fuse · E45 OFF.
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
from ta_indicator_catalog import LOW_IDS, build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/soft-dl-mlp-stagea"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
SOFT_BASE = "LIVE_KD_OPT"
FWD_BARS = 10
FEATURE_IDS = list(LOW_IDS)
MIN_TRAIN_ROWS = 800
SEED = 42


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


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-z))


class TinyMLP:
    def __init__(self, n_in: int, n_hidden: int = 8, seed: int = SEED):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0.0, 0.25, size=(n_in, n_hidden))
        self.b1 = np.zeros(n_hidden)
        self.W2 = rng.normal(0.0, 0.25, size=(n_hidden, 1))
        self.b2 = np.zeros(1)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        h = np.tanh(X @ self.W1 + self.b1)
        return _sigmoid(h @ self.W2 + self.b2).ravel()

    def fit(self, X: np.ndarray, y: np.ndarray, *, epochs: int = 40, lr: float = 0.05, l2: float = 1e-3, batch: int = 256) -> None:
        rng = np.random.default_rng(SEED)
        n = X.shape[0]
        y = y.reshape(-1, 1)
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, batch):
                b = idx[s : s + batch]
                xb, yb = X[b], y[b]
                h = np.tanh(xb @ self.W1 + self.b1)
                p = _sigmoid(h @ self.W2 + self.b2)
                dlogit = (p - yb) / max(len(b), 1)
                dW2 = h.T @ dlogit + l2 * self.W2
                db2 = dlogit.sum(axis=0)
                dh = dlogit @ self.W2.T * (1.0 - h ** 2)
                dW1 = xb.T @ dh + l2 * self.W1
                db1 = dh.sum(axis=0)
                self.W2 -= lr * dW2
                self.b2 -= lr * db2
                self.W1 -= lr * dW1
                self.b1 -= lr * db1


class TinyLinear:
    def __init__(self, n_in: int, seed: int = SEED):
        rng = np.random.default_rng(seed)
        self.w = rng.normal(0.0, 0.1, size=(n_in,))
        self.b = 0.0

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return _sigmoid(X @ self.w + self.b)

    def fit(self, X: np.ndarray, y: np.ndarray, *, epochs: int = 60, lr: float = 0.08, l2: float = 1e-3, batch: int = 256) -> None:
        rng = np.random.default_rng(SEED)
        n = X.shape[0]
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, batch):
                b = idx[s : s + batch]
                xb, yb = X[b], y[b]
                p = self.predict_proba(xb)
                err = (p - yb) / max(len(b), 1)
                self.w -= lr * (xb.T @ err + l2 * self.w)
                self.b -= lr * float(err.sum())


def build_feature_cube(lows: dict, codes: list[str]):
    ref = lows[FEATURE_IDS[0]]
    dates = pd.DatetimeIndex(ref.index)
    codes = list(codes)
    X = np.zeros((len(dates), len(codes), len(FEATURE_IDS)), dtype=np.float32)
    for j, fid in enumerate(FEATURE_IDS):
        panel = lows[fid].reindex(index=dates, columns=codes).fillna(False)
        X[:, :, j] = panel.astype(np.float32).to_numpy()
    return dates, X


def build_fwd_returns(market: pd.DataFrame, codes: list[str], dates: pd.DatetimeIndex) -> np.ndarray:
    px = (
        market.pivot_table(index="date", columns="code", values="adj_close", aggfunc="last")
        .reindex(index=dates, columns=codes)
        .sort_index()
    )
    fwd = px.shift(-FWD_BARS) / px - 1.0
    return fwd.to_numpy(dtype=np.float64)


def walk_forward_soft_panel(dates, codes, X, fwd, *, kind: str, alpha: float) -> pd.DataFrame:
    years = sorted({int(d.year) for d in dates})
    boost = np.zeros((len(dates), len(codes)), dtype=np.float64)
    date_years = np.array([int(d.year) for d in dates])
    for y in years:
        train_mask = date_years < y
        apply_mask = date_years == y
        if not apply_mask.any():
            continue
        Xt_list, yt_list = [], []
        for ti in np.where(train_mask)[0]:
            for ci in range(len(codes)):
                r = fwd[ti, ci]
                if not np.isfinite(r):
                    continue
                Xt_list.append(X[ti, ci, :])
                yt_list.append(1.0 if r > 0.0 else 0.0)
        if len(Xt_list) < MIN_TRAIN_ROWS:
            continue
        Xt = np.asarray(Xt_list, dtype=np.float64)
        yt = np.asarray(yt_list, dtype=np.float64)
        n_in = Xt.shape[1]
        if kind == "mlp":
            model = TinyMLP(n_in, n_hidden=8, seed=SEED + y)
            model.fit(Xt, yt)
        else:
            model = TinyLinear(n_in, seed=SEED + y)
            model.fit(Xt, yt)
        for ti in np.where(apply_mask)[0]:
            boost[ti, :] = float(alpha) * model.predict_proba(X[ti, :, :].astype(np.float64))
    return pd.DataFrame(boost, index=dates, columns=codes)


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
    sell_rsi6 = soft_sell_panel(highs[SELL_HIGH_ID], boost=SOFT_BOOST)

    print("building walk-forward Soft panels (linear + MLP) ...", flush=True)
    dates, X = build_feature_cube(lows, list(FIN))
    fwd = build_fwd_returns(market, list(FIN), dates)
    soft_linear = walk_forward_soft_panel(dates, list(FIN), X, fwd, kind="linear", alpha=1.0)
    soft_mlp_a10 = walk_forward_soft_panel(dates, list(FIN), X, fwd, kind="mlp", alpha=1.0)
    soft_mlp_a05 = walk_forward_soft_panel(dates, list(FIN), X, fwd, kind="mlp", alpha=0.5)

    def align_boost(boost: pd.DataFrame) -> pd.DataFrame:
        return boost.reindex(index=kd_scores.index, columns=kd_scores.columns).fillna(0.0)

    soft_linear = align_boost(soft_linear)
    soft_mlp_a10 = align_boost(soft_mlp_a10)
    soft_mlp_a05 = align_boost(soft_mlp_a05)

    jobs = [
        (SOFT_BASE, "base", None, False),
        (CHAMPION_ID, "champion", add_buy_softs(kd_scores, lows, [(BUY_LOW_ID, SOFT_BOOST)]), True),
        (OBSERVE_CHAL_ID, "observe", add_buy_softs(kd_scores, lows, [(BUY_LOW_ID, 1.0), ("K9_LT30", 1.0)]), True),
        ("DL_SOFT_LINEAR_a10", "dl_linear", kd_scores.astype(float) + soft_linear, True),
        ("DL_SOFT_MLP_h8_a10", "dl_mlp", kd_scores.astype(float) + soft_mlp_a10, True),
        ("DL_SOFT_MLP_h8_a05", "dl_mlp", kd_scores.astype(float) + soft_mlp_a05, True),
    ]

    print(f"Stage A books: {len(jobs)}", flush=True)
    rows = []
    nav_base = win_base = asof = None
    for i, (book_id, track, scores, use_sell) in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] {book_id}", flush=True)
        sc = kd_scores if scores is None else scores
        sell = sell_rsi6 if use_sell else None
        res = run_kd(market, target, regime, dividends, scores=sc, buy_ok=kd_ok, sell_scores=sell)
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
                extra={"is_observe_ref": book_id == OBSERVE_CHAL_ID, "is_dl": track.startswith("dl_")},
            )
        )

    observe = next(r for r in rows if r["id"] == OBSERVE_CHAL_ID)
    ranked = sorted(
        rows,
        key=lambda r: (1 if r.get("promote_shaped") else 0, 1 if r.get("coexist") else 0, r["heldout_score"]),
        reverse=True,
    )
    beat_live = [r for r in ranked if r["id"] != SOFT_BASE and r.get("coexist") and r["heldout_score"] > 0]
    beat_observe = [
        r for r in ranked
        if r["id"] not in (SOFT_BASE, OBSERVE_CHAL_ID, CHAMPION_ID)
        and r.get("tip_clean")
        and r["heldout_score"] > observe["heldout_score"]
    ]
    promote_vs_observe = [
        r for r in ranked
        if r["id"] not in (SOFT_BASE, OBSERVE_CHAL_ID)
        and r.get("promote_shaped")
        and r["heldout_score"] > observe["heldout_score"]
    ]
    dl_promote = [r for r in promote_vs_observe if r.get("is_dl")]
    if dl_promote:
        verdict = "DL_PROMOTE_SHAPED_BEATS_OBSERVE"
    elif promote_vs_observe:
        verdict = "RULE_PROMOTE_SHAPED_BEATS_OBSERVE_NO_DL_LIFT"
    elif beat_live:
        verdict = "BEATS_LIVE_NO_OBSERVE_LIFT"
    elif any(r.get("tip_clean") and r["id"] != SOFT_BASE for r in ranked):
        verdict = "NEAR_NO_LIFT"
    else:
        verdict = "NO_LIFT"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_DL_MLP_STAGEA_SCREEN",
        "charter": "research/ops/SOFT_DL_MLP_STAGEA_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "soft_x_sleeve_fuse": False,
        "model": {
            "type": "tiny_mlp_h8_and_linear_ablation",
            "features": FEATURE_IDS,
            "fwd_bars": FWD_BARS,
            "walk_forward": "train years < Y; apply year Y",
            "framework": "numpy_only",
        },
        "asof": str(pd.Timestamp(asof).date()),
        "verdict": verdict,
        "observe_id": OBSERVE_CHAL_ID,
        "observe_heldout_score": observe["heldout_score"],
        "n_books": len(rows),
        "n_beat_live": len(beat_live),
        "n_beat_observe": len(beat_observe),
        "n_promote_shaped_beats_observe": len(promote_vs_observe),
        "n_dl_promote_shaped_beats_observe": len(dl_promote),
        "beat_live_ids": [r["id"] for r in beat_live],
        "beat_observe_ids": [r["id"] for r in beat_observe],
        "promote_shaped_ids": [r["id"] for r in promote_vs_observe],
        "dl_promote_shaped_ids": [r["id"] for r in dl_promote],
        "books": ranked,
        "non_actions": [
            "No live Soft-assist / Soft-Frozen / KD / TEL / E45 wire",
            "No Soft-assist observe swap from this screen alone",
            "No Soft×Sleeve auto-combo",
            "No hard-AND reopen",
            "No torch/TF in live path",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    blob = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "soft_dl_mlp_stagea_screen.json").write_text(blob, encoding="utf-8")
    (OPS / "SOFT_DL_MLP_STAGEA_SCREEN.json").write_text(blob, encoding="utf-8")

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
        "# Soft-Assist Tiny-MLP Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Verdict: **`{verdict}`** · books **{payload['n_books']}** · framework **numpy tiny MLP**",
        "Live wire: **false** · Soft×Sleeve fuse: **forbidden**",
        "",
        "## Question",
        "",
        "Can a walk-forward tiny MLP (or linear ablation) additive Soft buy score tip-clean / "
        "promote-shaped beat `LIVE_KD_OPT` or lift Soft-assist observe?",
        "",
        "## Summary",
        "",
        f"- Observe `{OBSERVE_CHAL_ID}` held **{observe['heldout_score']:.3f}** · tip_mdd_clean **{observe['tip_mdd_clean']}**",
        f"- Beat live: **{len(beat_live)}** → `{[r['id'] for r in beat_live]}`",
        f"- Beat observe: **{len(beat_observe)}** → `{[r['id'] for r in beat_observe]}`",
        f"- Promote-shaped > observe: **{len(promote_vs_observe)}** → `{[r['id'] for r in promote_vs_observe]}`",
        f"- **DL** promote-shaped > observe: **{len(dl_promote)}** → `{[r['id'] for r in dl_promote]}`",
        "",
        "## Books",
        "",
        "| ID | Track | Tip YTD | Tip 1y | Tip MDD clean | Promote-shaped | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD |",
        "|---|---|---|---|:---:|:---:|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(line(r) for r in ranked)
    lines += [
        "",
        "## Reading",
        "",
        "- Tiny MLP = `feat→8→1` sigmoid soft boost; linear = logistic ablation.",
        "- Features = causal TA LOW bools; train years `< Y`, apply year `Y`.",
        "- Sell soft kept as observe `RSI6_GT80` to isolate buy-side DL.",
        "- First DL toehold under Stage A — **not** live-ready deep learning.",
        "",
        "## Non-actions",
        "",
    ]
    lines.extend(f"- {x}" for x in payload["non_actions"])
    lines += ["", "## Label", "", f"`SOFT_DL_MLP_STAGEA_SCREEN_{payload['asof']}__{verdict}`", ""]
    md = "\n".join(lines)
    (OUT / "reports" / "SOFT_DL_MLP_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")
    (OPS / "SOFT_DL_MLP_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")

    zh = "\n".join([
        "# Soft-Assist Tiny-MLP Stage A 篩選",
        "",
        f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"判決：**`{verdict}`** · books **{payload['n_books']}** · **numpy 小 MLP**",
        "Live wire：**否** · Soft×Sleeve 融合：**禁止**",
        "",
        f"- Observe held **{observe['heldout_score']:.3f}**",
        f"- Beat live **{len(beat_live)}** · beat observe **{len(beat_observe)}**",
        f"- Promote-shaped>observe **{len(promote_vs_observe)}** · 其中 DL **{len(dl_promote)}** → `{[r['id'] for r in dl_promote]}`",
        "",
        "詳表見英文 `SOFT_DL_MLP_STAGEA_SCREEN.md`。",
        "",
        "## 非動作",
        "",
        "- 不接 live Soft-assist／Soft-Frozen／KD／TEL／E45",
        "- 不單憑本 screen 換 Soft-assist observe",
        "- 不 Soft×Sleeve 融合",
        "",
        f"`SOFT_DL_MLP_STAGEA_SCREEN_{payload['asof']}__{verdict}`",
        "",
    ])
    (OPS / "SOFT_DL_MLP_STAGEA_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    charter = OPS / "SOFT_DL_MLP_STAGEA_CHARTER.md"
    if charter.exists():
        ct = charter.read_text()
        ct = ct.replace("**PAPER STAGE A OPEN**", f"**PAPER STAGE A DONE** · verdict **`{verdict}`**")
        ct = ct.replace(
            "`SOFT_DL_MLP_STAGEA_CHARTER_2026-09-12__PAPER_OPEN`",
            f"`SOFT_DL_MLP_STAGEA_CHARTER_2026-09-12__{verdict}`",
        )
        charter.write_text(ct)

    print(json.dumps({
        "verdict": verdict,
        "dl_promote": [r["id"] for r in dl_promote],
        "promote_vs_observe": [r["id"] for r in promote_vs_observe],
        "beat_live": [r["id"] for r in beat_live],
        "observe_held": observe["heldout_score"],
    }, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
