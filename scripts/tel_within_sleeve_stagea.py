#!/usr/bin/env python3
"""TEL within-sleeve Stage A — T1 tech / T2 structure / T3 COOL-gated (paper only).

Charter: research/ops/TEL_WITHIN_SLEEVE_STAGEA_CHARTER.md
Soft-Frozen KEEP · live twin SELL_a75 + COOL_c8 + KD_OPT + TEL_EQUAL base · no 00631L · no live wire.
Challengers: TEL_RS_SOFT_TILT + custom tel_name_scores (≠ seasonal KD · ≠ old pack).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, TEL, e16_features, simulate_core
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import ALPHA as LIVE_SLEEVE_ALPHA, sleeve_signal_panel
from soft_assist_helpers import (
    BUY_LOW_ID,
    LIVE_KD,
    SELL_HIGH_ID,
    soft_boost_scores,
    soft_sell_panel,
)
from ta_indicator_catalog import build_low_high_catalog, rsi
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    TEL_RS_SOFT_TILT,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tel-within-sleeve-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TEL_WITHIN_SLEEVE_STAGEA_CHARTER"
SCREEN_ID = "TEL_WITHIN_SLEEVE_STAGEA_SCREEN"
DECISION_ID = "TEL_WITHIN_SLEEVE_DECISION_PACK"
BASE_ID = "BASE_LIVE_FUSE_COOL"
HELDOUT = "heldout_2019_plus"
SEALED = "sealed_2023_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

CAGR_FLOOR_PP = 0.20
HELD_MDD_MIN_PP = -0.25
SEALED_MDD_MIN_PP = 0.0
TIP_MDD_TOL_PP = -0.5


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _xz(df: pd.DataFrame) -> pd.DataFrame:
    mu = df.mean(axis=1)
    sd = df.std(axis=1).replace(0.0, np.nan)
    return df.sub(mu, axis=0).div(sd, axis=0).fillna(0.0).clip(-3.0, 3.0)


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
            out[wname] = {"mdd_improve_pp": None, "cagr_giveback_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = cagr_delta_pp(bc, cc)
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "gate": "PASS",
        }
    return out


def _sim(
    market,
    target,
    regime,
    dividends,
    *,
    scores,
    buy_ok,
    sell=None,
    exposure=None,
    telecom_alloc=TEL_EQUAL,
    tel_scores=None,
):
    kw: dict[str, Any] = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=telecom_alloc,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        e22_version=E22_VERSION,
    )
    if sell is not None:
        kw["fin_sell_scores"] = sell
    if exposure is not None:
        kw["e45_exposure"] = exposure.astype(float)
    if tel_scores is not None:
        kw["tel_name_scores"] = tel_scores
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kw)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, int(len(fills))


def _cool_from_offense(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def _buy(kd, lows, k9_amp: float = 1.0) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], float(k9_amp))


def _sell(highs, amp: float = SELL_AMP) -> pd.DataFrame:
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


def _panel_closes(market: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    adj = (
        m.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    for c in codes:
        if c not in adj.columns:
            raise ValueError(f"missing code {c}")
    return adj[list(codes)]


def _panel_volume(market: pd.DataFrame, codes: list[str], cal: pd.DatetimeIndex) -> pd.DataFrame:
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    vol = m.pivot(index="date", columns="code", values="volume").sort_index()
    return vol.reindex(cal)[list(codes)].fillna(0.0)


def build_score_family(market: pd.DataFrame, cal: pd.DatetimeIndex) -> dict[str, pd.DataFrame]:
    """Causal TEL name-score families (cross-sectional z, clipped)."""
    codes = list(TEL)
    close = _panel_closes(market, codes).reindex(cal).ffill()
    vol = _panel_volume(market, codes, cal)
    # 0050 for beta
    m0050 = _panel_closes(market, ["0050"]).reindex(cal).ffill().iloc[:, 0]
    r0050 = m0050.pct_change()
    rets = close.pct_change()

    hh60 = close.rolling(60, min_periods=40).max()
    dist60_raw = ((hh60 - close) / hh60.replace(0.0, np.nan)).clip(lower=0.0)
    dist60 = _xz(dist60_raw)

    rsi_panel = pd.DataFrame({c: rsi(close[c], 14) for c in codes}, index=cal)
    rsi_inv = _xz(50.0 - rsi_panel)

    ma60 = close.rolling(60, min_periods=40).mean()
    below_raw = ((ma60 - close) / ma60.replace(0.0, np.nan)).clip(lower=0.0)
    below_ma60 = _xz(below_raw)

    vol20 = rets.rolling(20, min_periods=10).std()
    inv_vol = _xz(1.0 / (vol20 + 1e-8))

    adv20 = (close * vol).rolling(20, min_periods=10).mean()
    adv = _xz(adv20)

    beta = pd.DataFrame(index=cal, columns=codes, dtype=float)
    var_m = r0050.rolling(60, min_periods=40).var()
    for c in codes:
        cov = rets[c].rolling(60, min_periods=40).cov(r0050)
        beta[c] = cov / var_m.replace(0.0, np.nan)
    inv_beta = _xz(-beta.abs())

    return {
        "DIST60": dist60,
        "RSI14_INV": rsi_inv,
        "BELOW_MA60": below_ma60,
        "DIST60_RSI": _xz(0.5 * dist60_raw.fillna(0.0) + 0.5 * ((50.0 - rsi_panel) / 50.0).fillna(0.0)),
        "INV_VOL20": inv_vol,
        "ADV20": adv,
        "INV_BETA0050": inv_beta,
        "ADV_INVVOL": _xz(0.5 * adv20.fillna(0.0) + 0.5 * (1.0 / (vol20 + 1e-8)).fillna(0.0)),
    }


def cool_gate_scores(scores: pd.DataFrame, cool: pd.Series) -> pd.DataFrame:
    """T3: equal scores when cool_exposure=1 (off-defense); active scores when defending."""
    out = scores.copy().astype(float)
    c = cool.reindex(out.index).fillna(1.0).astype(float)
    off = c >= 1.0 - 1e-12
    out.loc[off, :] = 0.0
    return out


def _score_row(base_w, chal_w, tip, *, rid, track, meta, n_fills) -> dict[str, Any]:
    h, s = chal_w[HELDOUT], chal_w[SEALED]
    bh, bs = base_w[HELDOUT], base_w[SEALED]
    held_cagr_lift = cagr_delta_pp(bh.get("cagr"), h.get("cagr"), missing_as_zero=True)
    sealed_cagr_lift = cagr_delta_pp(bs.get("cagr"), s.get("cagr"), missing_as_zero=True)
    if held_cagr_lift is not None:
        held_cagr_lift = -float(held_cagr_lift)
    if sealed_cagr_lift is not None:
        sealed_cagr_lift = -float(sealed_cagr_lift)
    held_mdd_up = float(mdd_delta_pp(bh.get("max_drawdown"), h.get("max_drawdown")))
    sealed_mdd_up = float(mdd_delta_pp(bs.get("max_drawdown"), s.get("max_drawdown")))
    tip_clean = all(tip[w]["gate"] == "PASS" for w in ("ytd", "trailing_1y"))
    tip_mdd_ok = tip_clean and all(
        tip[w]["mdd_improve_pp"] is not None and float(tip[w]["mdd_improve_pp"]) >= TIP_MDD_TOL_PP
        for w in ("ytd", "trailing_1y")
    )
    gates = {
        "tip_clean": tip_clean,
        "tip_mdd_ok": tip_mdd_ok,
        "held_mdd": held_mdd_up >= HELD_MDD_MIN_PP,
        "sealed_mdd": sealed_mdd_up >= SEALED_MDD_MIN_PP,
        "held_cagr_floor": held_cagr_lift is not None and held_cagr_lift >= CAGR_FLOOR_PP,
    }
    hit = all(gates.values())
    soft_ok = (
        gates["tip_mdd_ok"]
        and gates["held_mdd"]
        and gates["sealed_mdd"]
        and not gates["held_cagr_floor"]
    )
    return {
        "id": rid,
        "track": track,
        "meta": meta,
        "n_fills": n_fills,
        "windows": chal_w,
        "held_cagr": h.get("cagr"),
        "held_mdd": h.get("max_drawdown"),
        "sealed_cagr": s.get("cagr"),
        "sealed_mdd": s.get("max_drawdown"),
        "held_cagr_lift_pp": None if held_cagr_lift is None else round(held_cagr_lift, 4),
        "sealed_cagr_lift_pp": None if sealed_cagr_lift is None else round(sealed_cagr_lift, 4),
        "held_mdd_improve_pp": round(held_mdd_up, 4),
        "sealed_mdd_improve_pp": round(sealed_mdd_up, 4),
        "tip": tip,
        "gates": gates,
        "hit": bool(hit),
        "soft": bool(soft_ok),
    }


CHALLENGERS: list[tuple[str, str, str, bool]] = [
    # id, track, family_key, cool_gated
    ("T1_DIST60", "T1", "DIST60", False),
    ("T1_RSI14_INV", "T1", "RSI14_INV", False),
    ("T1_BELOW_MA60", "T1", "BELOW_MA60", False),
    ("T1_DIST60_RSI", "T1", "DIST60_RSI", False),
    ("T2_INV_VOL20", "T2", "INV_VOL20", False),
    ("T2_ADV20", "T2", "ADV20", False),
    ("T2_INV_BETA0050", "T2", "INV_BETA0050", False),
    ("T2_ADV_INVVOL", "T2", "ADV_INVVOL", False),
    ("T3_COOL_DIST60", "T3", "DIST60", True),
    ("T3_COOL_RSI14", "T3", "RSI14_INV", True),
    ("T3_COOL_INV_VOL20", "T3", "INV_VOL20", True),
    ("T3_COOL_ADV20", "T3", "ADV20", True),
]


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert soft.SOFT_FROZEN_ETF_CLIP == [0.0, 0.5]
    assert abs(SELL_AMP - 0.75) < 1e-9, SELL_AMP

    print(f"challengers={len(CHALLENGERS)} sell_amp={SELL_AMP}", flush=True)
    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, sleeve, _tgt, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    score_live = _sleeve_score(market, sleeve, float(LIVE_SLEEVE_ALPHA))
    tgt_live = _target_live(score_live, regime)
    sell_live = _sell(highs)

    kd_live = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok_live = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = _buy(kd_live, lows)

    print("building TEL score families ...", flush=True)
    families = build_score_family(market, cal)
    for k, df in families.items():
        df.to_csv(OUT / f"tel_scores_{k}.csv")

    print("offense NAV for BASE cool ...", flush=True)
    fuse_off, _ = _sim(
        market, tgt_live, regime, dividends, scores=buy_live, buy_ok=buy_ok_live, sell=sell_live
    )
    cool_base = _cool_from_offense(market, fuse_off)
    cool_base.to_frame("e45_exposure").to_csv(OUT / "exposure_cool_from_fuse.csv")

    print(f"{BASE_ID} ...", flush=True)
    base_nav, _ = _sim(
        market,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok_live,
        sell=sell_live,
        exposure=cool_base,
    )
    base_w = _pack(base_nav)
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    rows: list[dict[str, Any]] = []
    for i, (rid, track, fam, gated) in enumerate(CHALLENGERS, 1):
        print(f"  [{i}/{len(CHALLENGERS)}] {rid} ...", flush=True)
        base_scores = families[fam]
        # Rebuild cool from challenger offense (TEL tilt may change path)
        tel_off = base_scores  # offense pass without cool gate first
        off, _ = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok_live,
            sell=sell_live,
            telecom_alloc=TEL_RS_SOFT_TILT,
            tel_scores=tel_off,
        )
        cool = _cool_from_offense(market, off)
        tel_scores = cool_gate_scores(base_scores, cool) if gated else base_scores
        nav, nf = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok_live,
            sell=sell_live,
            exposure=cool,
            telecom_alloc=TEL_RS_SOFT_TILT,
            tel_scores=tel_scores,
        )
        nav.to_csv(OUT / f"nav_{rid}.csv", index=False)
        cool.to_frame("e45_exposure").to_csv(OUT / f"exposure_{rid}.csv")
        rows.append(
            _score_row(
                base_w,
                _pack(nav),
                _tip(base_nav, nav),
                rid=rid,
                track=track,
                meta={
                    "telecom_alloc": TEL_RS_SOFT_TILT,
                    "score_family": fam,
                    "cool_gated": gated,
                    "sell_amp": SELL_AMP,
                },
                n_fills=nf,
            )
        )

    hits = [r for r in rows if r["hit"]]
    softs = [r for r in rows if r["soft"]]
    tip_ok_rows = [r for r in rows if r["gates"]["tip_mdd_ok"]]
    mdd_block = [
        r
        for r in tip_ok_rows
        if not (r["gates"]["held_mdd"] and r["gates"]["sealed_mdd"])
    ]
    if hits:
        verdict = "TEL_WITHIN_HIT"
    elif softs:
        verdict = "TEL_WITHIN_SOFT"
    elif mdd_block:
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

    ranked = sorted(
        rows,
        key=lambda r: (
            -int(r["hit"]),
            -int(r["soft"]),
            -float(r["held_cagr_lift_pp"] or -9),
            -float(r["sealed_mdd_improve_pp"]),
            -float(r["held_mdd_improve_pp"]),
        ),
    )
    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "baseline": BASE_ID,
        "sell_amp": SELL_AMP,
        "baseline_windows": base_w,
        "n_challengers": len(rows),
        "n_hits": len(hits),
        "n_soft": len(softs),
        "hit_ids": [r["id"] for r in hits],
        "soft_ids": [r["id"] for r in softs],
        "mdd_block_ids": [r["id"] for r in mdd_block],
        "ranked": ranked,
        "gates": {
            "cagr_floor_pp": CAGR_FLOOR_PP,
            "held_mdd_min_pp": HELD_MDD_MIN_PP,
            "sealed_mdd_min_pp": SEALED_MDD_MIN_PP,
            "tip_mdd_tol_pp": TIP_MDD_TOL_PP,
        },
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# TEL within-sleeve — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Verdict: **`{verdict}`** · base `{BASE_ID}` · SELL_a{int(SELL_AMP * 100):02d} · Soft-Frozen KEEP · **no live wire**",
        "",
        f"Hits: `{[r['id'] for r in hits]}`",
        f"SOFT: `{[r['id'] for r in softs]}`",
        f"MDD_BLOCK (tip OK): `{[r['id'] for r in mdd_block]}`",
        "",
        "| id | track | CAGR↑h | MDD↑h | MDD↑s | tip | soft | hit |",
        "|---|---|---:|---:|---:|:---:|:---:|:---:|",
    ]
    for r in ranked:
        tip_y = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['track']} | {r['held_cagr_lift_pp']:+.2f}pp | "
            f"{r['held_mdd_improve_pp']:+.2f}pp | {r['sealed_mdd_improve_pp']:+.2f}pp | "
            f"{tip_y} | {'Y' if r['soft'] else 'N'} | {'Y' if r['hit'] else 'N'} |"
        )
    lines += [
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tel_within_sleeve_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    best = ranked[0] if ranked else None
    decision = {
        "label": DECISION_ID,
        "generated_at_utc": _utc(),
        "status": verdict,
        "verdict": verdict,
        "live_wire": False,
        "n_hits": len(hits),
        "hit_ids": [r["id"] for r in hits],
        "soft_ids": [r["id"] for r in softs],
        "mdd_block_ids": [r["id"] for r in mdd_block],
        "best": best["id"] if best else None,
        "best_metrics": None
        if best is None
        else {
            "id": best["id"],
            "track": best["track"],
            "held_cagr_lift_pp": best.get("held_cagr_lift_pp"),
            "held_mdd_improve_pp": best.get("held_mdd_improve_pp"),
            "sealed_mdd_improve_pp": best.get("sealed_mdd_improve_pp"),
            "gates": best.get("gates"),
            "hit": best.get("hit"),
            "soft": best.get("soft"),
        },
        "binding": [
            "Soft-Frozen live clip KEEP until Class D ACCEPT",
            "Live KD_OPT + TEL_EQUAL KEEP until dedicated ACCEPT",
            "Do not reopen TEL_PRE_EXDIV_KD / async STOP path",
            "CONF_RET3 / 00631L orthogonal KEEP — not in this paper twin",
            "Passing ≠ live wire",
        ],
        "next": (
            "Open paper observe ballot on hit_ids (no live wire from Stage A)"
            if hits
            else (
                "MDD/tip OK but CAGR short — densify only on soft_ids if human asks"
                if softs
                else "STOP this TEL within-sleeve grid; next lever ≠ Soft-Frozen clip / ≠ reopen STOP KD"
            )
        ),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
        "order": "research/ops/RESEARCH_ORDER_BETA_DEFENSE.md",
    }
    dlines = [
        "# TEL within-sleeve — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-26 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false** · SELL_a75 twin",
        "",
        f"HIT: **{len(hits)}** · SOFT: **{len(softs)}** · MDD_BLOCK: **{len(mdd_block)}** / {len(rows)}.",
        "",
    ]
    if hits:
        b = hits[0]
        dlines.append(
            f"Best HIT: `{b['id']}` · CAGR↑h {b['held_cagr_lift_pp']:+.2f} · "
            f"MDD↑h {b['held_mdd_improve_pp']:+.2f} · MDD↑s {b['sealed_mdd_improve_pp']:+.2f}"
        )
    elif softs:
        b = softs[0]
        dlines.append(
            f"Best SOFT: `{b['id']}` · CAGR↑h {b['held_cagr_lift_pp']:+.2f} · "
            f"MDD↑h {b['held_mdd_improve_pp']:+.2f} · MDD↑s {b['sealed_mdd_improve_pp']:+.2f}"
        )
        dlines.append("")
        dlines.append("MDD/tip OK · held CAGR short of +0.20pp.")
    elif best is not None:
        dlines.append(
            f"Best by CAGR lift: `{best['id']}` · CAGR↑h {best['held_cagr_lift_pp']:+.2f} · "
            f"MDD↑h {best['held_mdd_improve_pp']:+.2f} · MDD↑s {best['sealed_mdd_improve_pp']:+.2f} · "
            f"tip={'Y' if best['gates']['tip_mdd_ok'] else 'N'}"
        )
    dlines += ["", "## Binding", ""] + [f"{i}. {b}" for i, b in enumerate(decision["binding"], 1)]
    dlines += [
        "",
        f"Next: {decision['next']}",
        "",
        f"Label: `{DECISION_ID}_2026-09-26__{verdict}`",
        "",
    ]
    for path in (OPS, REP):
        (path / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
        (path / f"{DECISION_ID}.md").write_text("\n".join(dlines) + "\n")
    (OUT / "stagea_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_hits": len(hits),
                "n_soft": len(softs),
                "best": decision["best"],
                "best_metrics": decision["best_metrics"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
