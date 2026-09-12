#!/usr/bin/env python3
"""Stage A paper: Soft-assist DL T2 causal sequence — numpy only, NO torch.

Charter: research/ops/SOFT_DL_T2_SEQ_STAGEA_CHARTER.md

Opens the 4-track T2 slot with flattened / linear / shallow 1D-CNN books.
No live wire / no Soft×Sleeve fuse / Soft∥Sleeve OPEN unchanged.
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
    LIVE_KD,
    OBSERVE_CHAL_ID,
    SELL_HIGH_ID,
    SOFT_BOOST,
    build_observe_buy_scores,
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
OUT = ROOT / "repro/soft-dl-t2-seq-stagea"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
SOFT_BASE = "LIVE_KD_OPT"
RULE_SELL_A05 = f"{OBSERVE_CHAL_ID}__SELL_a05"
FWD_BARS = 10
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


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-z))


class TinyMLP:
    """Flattened-seq MLP or linear (n_hidden<=0 → direct linear). Always regression."""

    def __init__(self, n_in: int, n_hidden: int = 8, seed: int = SEED):
        rng = np.random.default_rng(seed)
        self.n_hidden = int(n_hidden)
        if self.n_hidden <= 0:
            self.W = rng.normal(0.0, 0.25, size=(n_in, 1))
            self.b = np.zeros(1)
            self.W1 = self.b1 = self.W2 = self.b2 = None
        else:
            self.W1 = rng.normal(0.0, 0.25, size=(n_in, self.n_hidden))
            self.b1 = np.zeros(self.n_hidden)
            self.W2 = rng.normal(0.0, 0.25, size=(self.n_hidden, 1))
            self.b2 = np.zeros(1)
            self.W = self.b = None

    def _forward(self, X: np.ndarray):
        if self.n_hidden <= 0:
            return None, X @ self.W + self.b
        h = np.tanh(X @ self.W1 + self.b1)
        return h, h @ self.W2 + self.b2

    def predict(self, X: np.ndarray) -> np.ndarray:
        _, logit = self._forward(X)
        return logit.ravel()

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        *,
        epochs: int = 40,
        lr: float = 0.05,
        l2: float = 1e-3,
        batch: int = 256,
        sample_weight: np.ndarray | None = None,
    ) -> None:
        rng = np.random.default_rng(SEED)
        n = X.shape[0]
        y = y.reshape(-1, 1)
        w_all = (
            np.ones((n, 1), dtype=np.float64)
            if sample_weight is None
            else np.asarray(sample_weight, dtype=np.float64).reshape(-1, 1)
        )
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, batch):
                b = idx[s : s + batch]
                xb, yb, wb = X[b], y[b], w_all[b]
                h, logit = self._forward(xb)
                err = ((logit - yb) * wb) / max(float(wb.sum()), 1.0)
                if self.n_hidden <= 0:
                    self.W -= lr * (xb.T @ err + l2 * self.W)
                    self.b -= lr * err.sum(axis=0)
                else:
                    dW2 = h.T @ err + l2 * self.W2
                    db2 = err.sum(axis=0)
                    dh = err @ self.W2.T * (1.0 - h**2)
                    dW1 = xb.T @ dh + l2 * self.W1
                    db1 = dh.sum(axis=0)
                    self.W2 -= lr * dW2
                    self.b2 -= lr * db2
                    self.W1 -= lr * dW1
                    self.b1 -= lr * db1



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


class TinyCNN1D:
    """Shallow 1D conv over length-L log-return sequences (numpy only)."""

    def __init__(self, seq_len: int, n_filters: int = 4, kernel: int = 3, seed: int = SEED):
        rng = np.random.default_rng(seed)
        self.seq_len = int(seq_len)
        self.n_filters = int(n_filters)
        self.kernel = int(kernel)
        self.W = rng.normal(0.0, 0.25, size=(self.n_filters, self.kernel))
        self.b = np.zeros(self.n_filters)
        out_len = self.seq_len - self.kernel + 1
        if out_len < 1:
            raise ValueError("seq_len must be >= kernel")
        self.out_len = out_len
        self.W2 = rng.normal(0.0, 0.25, size=(self.n_filters * out_len, 1))
        self.b2 = np.zeros(1)

    def _patches(self, X: np.ndarray) -> np.ndarray:
        return np.lib.stride_tricks.sliding_window_view(X, self.kernel, axis=1).copy()

    def predict(self, X: np.ndarray) -> np.ndarray:
        patches = self._patches(X)
        h = np.tanh(np.einsum("nlk,fk->nlf", patches, self.W) + self.b)
        return (h.reshape(X.shape[0], -1) @ self.W2 + self.b2).ravel()

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        *,
        epochs: int = 35,
        lr: float = 0.04,
        l2: float = 1e-3,
        batch: int = 256,
        sample_weight: np.ndarray | None = None,
    ) -> None:
        rng = np.random.default_rng(SEED)
        n = X.shape[0]
        y = y.reshape(-1, 1)
        w_all = (
            np.ones((n, 1), dtype=np.float64)
            if sample_weight is None
            else np.asarray(sample_weight, dtype=np.float64).reshape(-1, 1)
        )
        for _ in range(epochs):
            idx = rng.permutation(n)
            for s in range(0, n, batch):
                b = idx[s : s + batch]
                xb, yb, wb = X[b], y[b], w_all[b]
                patches = self._patches(xb)
                pre = np.einsum("nlk,fk->nlf", patches, self.W) + self.b
                h_nlf = np.tanh(pre)
                h = h_nlf.reshape(xb.shape[0], -1)
                logit = h @ self.W2 + self.b2
                err = ((logit - yb) * wb) / max(float(wb.sum()), 1.0)
                dW2 = h.T @ err + l2 * self.W2
                db2 = err.sum(axis=0)
                dh = (err @ self.W2.T).reshape(xb.shape[0], self.out_len, self.n_filters)
                dpre = dh * (1.0 - h_nlf**2)
                dW = np.einsum("nlf,nlk->fk", dpre, patches) + l2 * self.W
                db = dpre.sum(axis=(0, 1))
                self.W2 -= lr * dW2
                self.b2 -= lr * db2
                self.W -= lr * dW
                self.b -= lr * db


def build_logret_seq(
    market: pd.DataFrame, codes: list[str], dates: pd.DatetimeIndex, L: int
) -> np.ndarray:
    px = (
        market.pivot_table(index="date", columns="code", values="adj_close", aggfunc="last")
        .reindex(index=dates, columns=codes)
        .sort_index()
    )
    logret = np.log(px / px.shift(1)).to_numpy(dtype=np.float64)
    n_t, n_c = logret.shape
    seq = np.full((n_t, n_c, L), np.nan, dtype=np.float64)
    for lag in range(L):
        src = np.roll(logret, lag, axis=0)
        if lag:
            src[:lag, :] = np.nan
        seq[:, :, L - 1 - lag] = src
    return seq


def build_fwd_returns(market: pd.DataFrame, codes: list[str], dates: pd.DatetimeIndex) -> np.ndarray:
    px = (
        market.pivot_table(index="date", columns="code", values="adj_close", aggfunc="last")
        .reindex(index=dates, columns=codes)
        .sort_index()
    )
    return (px.shift(-FWD_BARS) / px - 1.0).to_numpy(dtype=np.float64)


def _pack_flat(seq: np.ndarray, fwd: np.ndarray, train_mask: np.ndarray):
    Xt = seq[train_mask].reshape(-1, seq.shape[-1]).astype(np.float64)
    yr = fwd[train_mask].reshape(-1)
    ok = np.isfinite(Xt).all(axis=1) & np.isfinite(yr)
    if int(ok.sum()) < MIN_TRAIN_ROWS:
        return None
    Xt, yr = Xt[ok], yr[ok]
    lo, hi = np.quantile(yr, [0.01, 0.99])
    yt = np.clip(yr, lo, hi)
    w = 1.0 + np.clip(-yr, 0.0, None) * 5.0
    return Xt, yt.astype(np.float64), w.astype(np.float64)


def walk_forward_seq_flat(
    dates, codes, seq, fwd, *, alpha: float, n_hidden: int, seed_off: int = 0
) -> pd.DataFrame:
    boost = np.zeros((len(dates), len(codes)), dtype=np.float64)
    years = np.array([int(d.year) for d in dates])
    for y in sorted(set(years.tolist())):
        train = years < y
        apply = years == y
        if not apply.any():
            continue
        pack = _pack_flat(seq, fwd, train)
        if pack is None:
            continue
        Xt, yt, w = pack
        model = TinyMLP(Xt.shape[1], n_hidden=n_hidden, seed=SEED + seed_off + y)
        model.fit(Xt, yt, sample_weight=w)
        for ti in np.where(apply)[0]:
            Xti = seq[ti].astype(np.float64)
            ok = np.isfinite(Xti).all(axis=1)
            score = np.zeros(len(codes), dtype=np.float64)
            if ok.any():
                score[ok] = model.predict(Xti[ok])
            mu = float(np.nanmean(score))
            sd = float(np.nanstd(score) + 1e-6)
            boost[ti, :] = float(alpha) * _sigmoid((score - mu) / sd)
    return pd.DataFrame(boost, index=dates, columns=codes)


def walk_forward_seq_cnn(
    dates, codes, seq, fwd, *, alpha: float, seed_off: int = 100
) -> pd.DataFrame:
    boost = np.zeros((len(dates), len(codes)), dtype=np.float64)
    years = np.array([int(d.year) for d in dates])
    L = seq.shape[-1]
    for y in sorted(set(years.tolist())):
        train = years < y
        apply = years == y
        if not apply.any():
            continue
        pack = _pack_flat(seq, fwd, train)
        if pack is None:
            continue
        Xt, yt, w = pack
        model = TinyCNN1D(seq_len=L, n_filters=4, kernel=3, seed=SEED + seed_off + y)
        model.fit(Xt, yt, sample_weight=w)
        for ti in np.where(apply)[0]:
            Xti = seq[ti].astype(np.float64)
            ok = np.isfinite(Xti).all(axis=1)
            score = np.zeros(len(codes), dtype=np.float64)
            if ok.any():
                score[ok] = model.predict(Xti[ok])
            mu = float(np.nanmean(score))
            sd = float(np.nanstd(score) + 1e-6)
            boost[ti, :] = float(alpha) * _sigmoid((score - mu) / sd)
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
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))

    kd_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        list(FIN),
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    kd_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, list(FIN), pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    observe_buy = build_observe_buy_scores(kd_scores, lows)
    sell_a10 = soft_sell_panel(highs[SELL_HIGH_ID], boost=SOFT_BOOST)
    sell_a05 = soft_sell_panel(highs[SELL_HIGH_ID], boost=0.5)

    print("building T2 causal log-return sequences (numpy) ...", flush=True)
    dates = pd.DatetimeIndex(kd_scores.index)
    codes = list(FIN)
    fwd = build_fwd_returns(market, codes, dates)
    seq10 = build_logret_seq(market, codes, dates, L=10)
    seq20 = build_logret_seq(market, codes, dates, L=20)

    print("  walk-forward SEQ10 flat h8 ...", flush=True)
    buy_s10_h8 = walk_forward_seq_flat(dates, codes, seq10, fwd, alpha=0.5, n_hidden=8, seed_off=0)
    print("  walk-forward SEQ20 flat h8 ...", flush=True)
    buy_s20_h8 = walk_forward_seq_flat(dates, codes, seq20, fwd, alpha=0.5, n_hidden=8, seed_off=20)
    print("  walk-forward SEQ10 linear ...", flush=True)
    buy_s10_lin = walk_forward_seq_flat(dates, codes, seq10, fwd, alpha=0.5, n_hidden=0, seed_off=40)
    print("  walk-forward SEQ10 cnn ...", flush=True)
    buy_s10_cnn = walk_forward_seq_cnn(dates, codes, seq10, fwd, alpha=0.5, seed_off=60)
    buy_s10_h8_a025 = buy_s10_h8 * 0.5

    def align(df: pd.DataFrame) -> pd.DataFrame:
        return df.reindex(index=kd_scores.index, columns=kd_scores.columns).fillna(0.0)

    buy_s10_h8 = align(buy_s10_h8)
    buy_s20_h8 = align(buy_s20_h8)
    buy_s10_lin = align(buy_s10_lin)
    buy_s10_cnn = align(buy_s10_cnn)
    buy_s10_h8_a025 = align(buy_s10_h8_a025)

    jobs = [
        (SOFT_BASE, "base", None, None),
        (OBSERVE_CHAL_ID, "observe", observe_buy, sell_a10),
        (RULE_SELL_A05, "rule_sell_ref", observe_buy, sell_a05),
        ("DL_T2_SEQ10_FLAT_h8_a05", "t2_seq10_flat_h8", kd_scores.astype(float) + buy_s10_h8, sell_a10),
        ("DL_T2_SEQ20_FLAT_h8_a05", "t2_seq20_flat_h8", kd_scores.astype(float) + buy_s20_h8, sell_a10),
        ("DL_T2_SEQ10_LIN_a05", "t2_seq10_linear", kd_scores.astype(float) + buy_s10_lin, sell_a10),
        ("DL_T2_SEQ10_CNN_a05", "t2_seq10_cnn", kd_scores.astype(float) + buy_s10_cnn, sell_a10),
        ("DL_T2_SEQ10_FLAT_h8_a025", "t2_seq10_flat_h8", kd_scores.astype(float) + buy_s10_h8_a025, sell_a10),
        ("DL_T2_SEQ10_FLAT_h8_a05__SELL_a05", "t2_seq10_flat_h8_sell_a05", kd_scores.astype(float) + buy_s10_h8, sell_a05),
    ]

    print(f"Stage A books: {len(jobs)} (numpy T2 seq — no torch import)", flush=True)
    rows = []
    nav_base = win_base = asof = None
    for i, (book_id, track, scores, sell) in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] {book_id}", flush=True)
        sc = kd_scores if scores is None else scores
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
                extra={
                    "is_observe_ref": book_id == OBSERVE_CHAL_ID,
                    "is_rule_sell_ref": book_id == RULE_SELL_A05,
                    "is_dl": track.startswith("t2_"),
                },
            )
        )

    observe = next(r for r in rows if r["id"] == OBSERVE_CHAL_ID)
    rule_sell = next(r for r in rows if r["id"] == RULE_SELL_A05)
    ranked = sorted(
        rows,
        key=lambda r: (
            1 if r.get("promote_shaped") else 0,
            1 if r.get("coexist") else 0,
            r["heldout_score"],
        ),
        reverse=True,
    )
    beat_live = [r for r in ranked if r["id"] != SOFT_BASE and r.get("coexist") and r["heldout_score"] > 0]
    beat_observe = [
        r
        for r in ranked
        if r["id"] not in (SOFT_BASE, OBSERVE_CHAL_ID)
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
    dl_promote = [r for r in promote_vs_observe if r.get("is_dl")]
    dl_scores = [r["heldout_score"] for r in ranked if r.get("is_dl")]
    rule_still_best = rule_sell["heldout_score"] >= (max(dl_scores) if dl_scores else -9.0)

    if dl_promote:
        verdict = "T2_SEQ_PROMOTE_SHAPED_BEATS_OBSERVE"
    elif promote_vs_observe and not dl_promote:
        verdict = "RULE_PROMOTE_ONLY_NO_T2_LIFT"
    elif beat_live:
        verdict = "BEATS_LIVE_NO_OBSERVE_LIFT"
    else:
        verdict = "NO_LIFT"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_DL_T2_SEQ_STAGEA_SCREEN",
        "charter": "research/ops/SOFT_DL_T2_SEQ_STAGEA_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "soft_x_sleeve_fuse": False,
        "observe_swap": False,
        "torch_used": False,
        "asof": str(pd.Timestamp(asof).date()),
        "verdict": verdict,
        "observe_id": OBSERVE_CHAL_ID,
        "observe_heldout_score": observe["heldout_score"],
        "rule_sell_a05_heldout_score": rule_sell["heldout_score"],
        "rule_sell_still_best_vs_dl": bool(rule_still_best),
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
            "No Soft-assist or Sleeve observe swap from this screen",
            "No Soft×Sleeve auto-combo",
            "No same-MLP binary Soft-buy deepen",
            "No torch import in this numpy T2 screen path",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    blob = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "soft_dl_t2_seq_stagea_screen.json").write_text(blob, encoding="utf-8")
    (OPS / "SOFT_DL_T2_SEQ_STAGEA_SCREEN.json").write_text(blob, encoding="utf-8")

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
        "# Soft-Assist DL T2 Sequence Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Verdict: **`{verdict}`** · books **{payload['n_books']}** · torch_used **false**",
        "Live wire: **false** · Soft×Sleeve fuse: **forbidden** · observe swap: **false**",
        "",
        "## Question",
        "",
        "Do causal past-L log-return sequences (flat linear / MLP h8 / numpy 1D-CNN) as Soft "
        "buy boosts promote-shaped-beat Soft observe — without torch and without deepening "
        "the parked binary Soft-buy MLP?",
        "",
        "## Summary",
        "",
        f"- Observe `{OBSERVE_CHAL_ID}` held **{observe['heldout_score']:.3f}** · tip_mdd_clean **{observe['tip_mdd_clean']}**",
        f"- Rule `SELL_a05` held **{rule_sell['heldout_score']:.3f}** · tip_mdd_clean **{rule_sell['tip_mdd_clean']}** · still_best_vs_dl **{rule_still_best}**",
        f"- Beat live: **{len(beat_live)}** → `{[r['id'] for r in beat_live]}`",
        f"- Promote-shaped > observe: **{len(promote_vs_observe)}** → `{[r['id'] for r in promote_vs_observe]}`",
        f"- **DL T2** promote-shaped > observe: **{len(dl_promote)}** → `{[r['id'] for r in dl_promote]}`",
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
        "- Features: causal past L∈{10,20} daily log-return sequences (no future bars).",
        "- Models: flattened linear · flattened MLP h8 · shallow numpy 1D-CNN (no torch).",
        "- Sell isolation: observe sell on most books; one book pairs rule `SELL_a05`.",
        "- Soft∥Sleeve OPEN ballots stay independent; this screen never fuses or wires live.",
        "",
        "## Non-actions",
        "",
    ]
    lines.extend(f"- {x}" for x in payload["non_actions"])
    lines += ["", "## Label", "", f"`SOFT_DL_T2_SEQ_STAGEA_SCREEN_{payload['asof']}__{verdict}`", ""]
    md = "\n".join(lines)
    (OUT / "reports" / "SOFT_DL_T2_SEQ_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")
    (OPS / "SOFT_DL_T2_SEQ_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")

    zh = "\n".join(
        [
            "# Soft-Assist DL T2 序列 Stage A 篩選",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"判決：**`{verdict}`** · torch_used **false**",
            "",
            f"- Observe held **{observe['heldout_score']:.3f}**",
            f"- 規則 SELL_a05 held **{rule_sell['heldout_score']:.3f}** · 仍優於 DL **{rule_still_best}**",
            f"- DL T2 promote>observe **{len(dl_promote)}** → `{[r['id'] for r in dl_promote]}`",
            "",
            "詳表見英文稿。本 Stage A 為 numpy 序列 toehold（不 import torch）。",
            "",
            "## 非動作",
            "",
            "- 不接 live · 不換 Soft／Sleeve observe · 不融合 · 不再加深同一套 binary Soft-buy MLP",
            "",
            f"`SOFT_DL_T2_SEQ_STAGEA_SCREEN_{payload['asof']}__{verdict}`",
            "",
        ]
    )
    (OPS / "SOFT_DL_T2_SEQ_STAGEA_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    for path, open_tok, done_tok in (
        (
            OPS / "SOFT_DL_T2_SEQ_STAGEA_CHARTER.md",
            "**PAPER STAGE A OPEN**",
            f"**PAPER STAGE A DONE** · verdict **`{verdict}`**",
        ),
        (
            OPS / "SOFT_DL_T2_SEQ_STAGEA_CHARTER.zh-TW.md",
            "**PAPER STAGE A OPEN**",
            f"**PAPER STAGE A DONE** · 判決 **`{verdict}`**",
        ),
    ):
        if path.exists():
            t = path.read_text().replace(open_tok, done_tok)
            t = t.replace(
                "`SOFT_DL_T2_SEQ_STAGEA_CHARTER_2026-09-12__PAPER_OPEN`",
                f"`SOFT_DL_T2_SEQ_STAGEA_CHARTER_2026-09-12__{verdict}`",
            )
            path.write_text(t)
    cj = OPS / "SOFT_DL_T2_SEQ_STAGEA_CHARTER.json"
    if cj.exists():
        cjd = json.loads(cj.read_text())
        cjd["status"] = "PAPER_DONE"
        cjd["verdict"] = verdict
        cjd["label"] = f"SOFT_DL_T2_SEQ_STAGEA_CHARTER_2026-09-12__{verdict}"
        cj.write_text(json.dumps(cjd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    marker = "Soft-assist DL T2 seq Stage A"
    if reg.exists() and marker not in reg.read_text():
        row = (
            f"| {marker} | **PAPER DONE / {verdict}** (2026-09-12) | "
            f"numpy causal logret seq L10/L20 · flat linear/h8 + 1D-CNN · no torch in screen · "
            f"DL promote>observe **{len(dl_promote)}** · rule SELL_a05 still_best_vs_dl **{rule_still_best}** · "
            f"no live / no fuse / Soft∥Sleeve OPEN unchanged · `SOFT_DL_T2_SEQ_STAGEA_SCREEN.md` |\n"
        )
        lines_r = reg.read_text().splitlines(True)
        out = []
        done = False
        for l in lines_r:
            out.append(l)
            if not done and (
                "Soft-assist dual-paper observe" in l
                or "Soft-assist K9 observe ballot" in l
                or "Soft-assist DL 4-track" in l
                or "tiny-MLP Stage A" in l
                or "Soft-assist dual observe" in l
            ):
                out.append(row)
                done = True
        if not done:
            # append near Soft-assist dual-paper row search broader
            out = []
            for l in lines_r:
                out.append(l)
                if not done and "Soft-assist" in l and "observe" in l.lower():
                    out.append(row)
                    done = True
        if done:
            reg.write_text("".join(out))

    print(
        json.dumps(
            {
                "verdict": verdict,
                "dl_promote": [r["id"] for r in dl_promote],
                "promote_vs_observe": [r["id"] for r in promote_vs_observe],
                "rule_sell_held": rule_sell["heldout_score"],
                "observe_held": observe["heldout_score"],
                "rule_still_best_vs_dl": rule_still_best,
                "torch_used": False,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
