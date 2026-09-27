#!/usr/bin/env python3
"""Earn-beta / defense rhythm Stage A — BETA / COOL / FIN_DYN / VOL / CLOSE (paper).

Exact T+1 KEEP · Soft-Frozen clips KEEP · live L1=0.05 KEEP · no live wire.
Charter: research/ops/EARN_BETA_DEFENSE_STAGEA_CHARTER.md
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
import live_cool_c8_cutover as cool_cut
import live_dh_fuse_cutover as fuse_cut
from cool_c8_proxy_observe_helpers import COOL, EXIT_X, FLOOR, MAX_DWELL, PROXY_X
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import (
    ALPHA,
    SIGN,
    SIGNAL_KIND,
    SIGNAL_WINDOW,
    sleeve_signal_panel,
)
from soft_assist_helpers import (
    LIVE_KD,
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
REPRO = ROOT / "repro" / "earn-beta-defense-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "EARN_BETA_DEFENSE_STAGEA_CHARTER"
SCREEN_ID = "EARN_BETA_DEFENSE_STAGEA_SCREEN"
DECISION_ID = "EARN_BETA_DEFENSE_STAGEA_DECISION_PACK"
BOOK_ID = "LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8_L1_05"
HELDOUT = "heldout_2019_plus"
SEALED = "sealed_2023_plus"

CAGR_LIFT_PP = 0.50
MDD_SLACK_PP = -0.50

LIVE_TEL = (float(soft.SOFT_FROZEN_TEL_LO), float(soft.SOFT_FROZEN_TEL_HI))
LIVE_FIN = (float(soft.SOFT_FROZEN_FIN_LO), float(soft.SOFT_FROZEN_FIN_HI))
LIVE_ETF = (float(soft.SOFT_FROZEN_ETF_LO), float(soft.SOFT_FROZEN_ETF_HI))


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _kd_panels(market: pd.DataFrame, dividends: pd.DataFrame):
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    kd = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    buy = build_observe_buy_scores(kd, lows)
    sell = build_observe_sell_panel(highs, boost=float(fuse_cut.SELL_BOOST_LIVE))
    return buy_ok, buy, sell


def _champion_score(market: pd.DataFrame, sleeve: pd.DataFrame) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, SIGNAL_KIND, SIGNAL_WINDOW)
    return base_score + float(SIGN) * float(ALPHA) * tilt


def _rebuild_regime_clips(
    score: pd.DataFrame,
    regime: pd.Series,
    *,
    gate_regimes: set[str],
    on_fin_hi: float,
    on_etf_hi: float,
    on_fin_lo: float | None = None,
) -> pd.DataFrame:
    """Live clips off-gate; challenger FIN/ETF hi on gate regimes. Uses live L1."""
    fin_lo = LIVE_FIN[0] if on_fin_lo is None else float(on_fin_lo)
    live_lo = np.array([LIVE_FIN[0], LIVE_TEL[0], LIVE_ETF[0]], dtype=float)
    live_hi = np.array([LIVE_FIN[1], LIVE_TEL[1], LIVE_ETF[1]], dtype=float)
    on_lo = np.array([fin_lo, LIVE_TEL[0], LIVE_ETF[0]], dtype=float)
    on_hi = np.array([float(on_fin_hi), LIVE_TEL[1], float(on_etf_hi)], dtype=float)
    start = clip.apply_clip_box((live_lo + live_hi) / 2.0, live_lo, live_hi, soft.START_WEIGHTS.copy())
    out = []
    cur = start.copy()
    for i, _dt in enumerate(score.index):
        reg = str(regime.iloc[i])
        lo, hi = (on_lo, on_hi) if reg in gate_regimes else (live_lo, live_hi)
        pri = soft.REGIME_PRIORS[reg]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = clip.apply_clip_box(cand, lo, hi, start)
        desired = soft.BLEND_OLD * cur + soft.BLEND_NEW * cand
        desired = clip.apply_clip_box(desired, lo, hi, start)
        if float(np.abs(desired - cur).sum()) >= float(soft.REBALANCE_L1_MIN):
            cur = desired
        out.append(cur.copy())
    return pd.DataFrame(out, index=score.index, columns=["Financial", "Telecom", "0050"])


def _cool_custom(
    dates: pd.DatetimeIndex,
    proxy_mdd63: pd.Series,
    *,
    floor: float | None = None,
    proxy_x: float | None = None,
    exit_x: float | None = None,
) -> pd.Series:
    px = proxy_mdd63.reindex(dates).fillna(0.0)
    out = pd.Series(1.0, index=dates, dtype=float)
    defending = False
    dwell = 0
    cool_left = 0
    floor_f = float(FLOOR if floor is None else floor)
    proxy_f = float(PROXY_X if proxy_x is None else proxy_x)
    exit_f = float(EXIT_X if exit_x is None else exit_x)
    for i in range(len(dates)):
        v = float(px.iloc[i])
        if cool_left > 0:
            out.iloc[i] = 1.0
            cool_left -= 1
            defending = False
            dwell = 0
            continue
        if not defending:
            if v <= -proxy_f:
                defending = True
                dwell = 1
                out.iloc[i] = floor_f
            else:
                out.iloc[i] = 1.0
        else:
            dwell += 1
            if v >= -exit_f or dwell >= int(MAX_DWELL):
                defending = False
                dwell = 0
                cool_left = int(COOL)
                out.iloc[i] = 1.0
            else:
                out.iloc[i] = floor_f
    return out


def _vol_scale(market: pd.DataFrame, dates: pd.DatetimeIndex, target: float) -> pd.Series:
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"]).dt.normalize()
    taiex = (
        m[m["code"].astype(str) == "TAIEX"]
        .drop_duplicates("date")
        .sort_values("date")
        .set_index("date")
    )
    px = taiex["adj_close"].astype(float) if "adj_close" in taiex.columns else taiex["close"].astype(float)
    ret = px.pct_change()
    rv = ret.rolling(20, min_periods=10).std() * np.sqrt(252)
    rv = rv.reindex(dates).ffill().bfill().replace(0, np.nan)
    scale = (float(target) / rv).clip(lower=0.50, upper=1.0).fillna(1.0)
    return scale.astype(float)


def _run_book(
    market,
    dividends,
    *,
    target,
    regime,
    buy,
    buy_ok,
    sell,
    exposure,
):
    kwargs: dict[str, Any] = dict(
        apply_e22=True,
        e22_version=e22div.PRESERVED_CASH_ON_EX,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=buy,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
    )
    if exposure is not None:
        kwargs["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kwargs)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


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


def _vs(base_w: dict, chal_w: dict, key: str) -> dict[str, Any]:
    b, c = base_w[key], chal_w[key]
    gb = cagr_delta_pp(b.get("cagr"), c.get("cagr"), missing_as_zero=True)
    # lift = chal - base = -giveback when giveback is base-chal
    lift = None if gb is None else round(-float(gb), 4)
    md = mdd_delta_pp(b.get("max_drawdown"), c.get("max_drawdown"))
    return {
        "base_cagr": b.get("cagr"),
        "chal_cagr": c.get("cagr"),
        "cagr_lift_pp": lift,
        "base_mdd": b.get("max_drawdown"),
        "chal_mdd": c.get("max_drawdown"),
        "mdd_improve_pp": round(float(md), 4),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    assert float(soft.REBALANCE_L1_MIN) == 0.05, soft.REBALANCE_L1_MIN

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, sleeve, _lt, regime = e16_features(market)
    buy_ok, buy, sell = _kd_panels(market, dividends)
    score = _champion_score(market, sleeve)
    target_live = fuse_cut.fuse_target_for_market(market)

    print("building BASE_LIVE_L1_05 ...", flush=True)
    fuse_nav, _, _ = fuse_cut.build_fuse_offense_sim(market, dividends)
    cool_live = cool_cut.build_cool_exposure_from_offense(market, fuse_nav)
    base_nav, base_fills, base_meta = _run_book(
        market,
        dividends,
        target=target_live,
        regime=regime,
        buy=buy,
        buy_ok=buy_ok,
        sell=sell,
        exposure=cool_live,
    )
    base_w = _pack(base_nav)
    print(
        f"BASE held CAGR={base_w[HELDOUT]['cagr']} MDD={base_w[HELDOUT]['max_drawdown']} "
        f"L1={soft.REBALANCE_L1_MIN}",
        flush=True,
    )

    specs: list[dict[str, Any]] = [
        {"track": "BETA", "id": "B_BULL_E055", "kind": "regime", "fin_hi": 0.80, "etf_hi": 0.55},
        {"track": "BETA", "id": "B_BULL_E060", "kind": "regime", "fin_hi": 0.80, "etf_hi": 0.60},
        {"track": "COOL", "id": "C_FLOOR_070", "kind": "cool", "floor": 0.70},
        {"track": "COOL", "id": "C_EXIT_04", "kind": "cool", "exit_x": 0.04},
        {
            "track": "FIN_DYN",
            "id": "F_BULL_F070_E050",
            "kind": "regime",
            "fin_hi": 0.70,
            "etf_hi": 0.50,
        },
        {
            "track": "FIN_DYN",
            "id": "F_BULL_F065_E055",
            "kind": "regime",
            "fin_hi": 0.65,
            "etf_hi": 0.55,
        },
        {"track": "VOL", "id": "V_TVOL_12", "kind": "vol", "tvol": 0.12},
        {"track": "VOL", "id": "V_TVOL_15", "kind": "vol", "tvol": 0.15},
    ]

    rows: list[dict[str, Any]] = []
    for spec in specs:
        cid = spec["id"]
        print(f"building {cid} ...", flush=True)
        target = target_live
        exposure: pd.Series | None = cool_live

        if spec["kind"] == "regime":
            target = _rebuild_regime_clips(
                score,
                regime,
                gate_regimes={"Bull"},
                on_fin_hi=float(spec["fin_hi"]),
                on_etf_hi=float(spec["etf_hi"]),
            )
            off_nav, _, _ = _run_book(
                market, dividends, target=target, regime=regime,
                buy=buy, buy_ok=buy_ok, sell=sell, exposure=None,
            )
            exposure = cool_cut.build_cool_exposure_from_offense(market, off_nav)
        elif spec["kind"] == "cool":
            off_nav, _, _ = _run_book(
                market, dividends, target=target, regime=regime,
                buy=buy, buy_ok=buy_ok, sell=sell, exposure=None,
            )
            nav_s = stagea._nav_series(off_nav)
            feat = stagea._risk_features(market, nav_s)
            dates = pd.DatetimeIndex(nav_s.index)
            exposure = _cool_custom(
                dates,
                feat["proxy_mdd63"],
                floor=spec.get("floor"),
                exit_x=spec.get("exit_x"),
            )
        elif spec["kind"] == "vol":
            off_nav, _, _ = _run_book(
                market, dividends, target=target, regime=regime,
                buy=buy, buy_ok=buy_ok, sell=sell, exposure=None,
            )
            cool = cool_cut.build_cool_exposure_from_offense(market, off_nav)
            dates = pd.DatetimeIndex(pd.to_datetime(cool.index))
            vscale = _vol_scale(market, dates, float(spec["tvol"]))
            exposure = (cool.astype(float) * vscale.reindex(cool.index).fillna(1.0)).clip(0.0, 1.0)
        else:
            raise ValueError(spec["kind"])

        nav, fills, meta = _run_book(
            market, dividends, target=target, regime=regime,
            buy=buy, buy_ok=buy_ok, sell=sell, exposure=exposure,
        )
        win = _pack(nav)
        held = _vs(base_w, win, HELDOUT)
        sealed = _vs(base_w, win, SEALED)
        cagr_gate = held["cagr_lift_pp"] is not None and float(held["cagr_lift_pp"]) >= CAGR_LIFT_PP
        mdd_gate = held["mdd_improve_pp"] is not None and float(held["mdd_improve_pp"]) >= MDD_SLACK_PP
        row = {
            "track": spec["track"],
            "id": cid,
            "spec": {k: v for k, v in spec.items() if k != "kind"},
            "heldout": held,
            "sealed": sealed,
            "cagr_gate": bool(cagr_gate),
            "mdd_gate": bool(mdd_gate),
            "hit": bool(cagr_gate and mdd_gate),
            "n_fills": int(len(fills)),
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
        }
        rows.append(row)
        print(
            f"  {cid}: cagr_lift={held['cagr_lift_pp']} mdd={held['mdd_improve_pp']} "
            f"hit={row['hit']}",
            flush=True,
        )

    hits = [r for r in rows if r["hit"]]
    cagr_soft = [r for r in rows if r["cagr_gate"] and not r["mdd_gate"]]
    any_cagr = any(r["cagr_gate"] for r in rows)

    track_verdicts: dict[str, str] = {}
    for track in ("BETA", "COOL", "FIN_DYN", "VOL"):
        tr = [r for r in rows if r["track"] == track]
        if any(r["hit"] for r in tr):
            track_verdicts[track] = f"{track}_HIT"
        elif any(r["cagr_gate"] for r in tr):
            track_verdicts[track] = f"{track}_CAGR_SOFT"
        else:
            track_verdicts[track] = f"{track}_NO_LIFT"

    if hits:
        verdict = "EARN_HIT"
        close_rec = False
    elif cagr_soft:
        verdict = "CAGR_SOFT"
        close_rec = False
    elif not any_cagr:
        verdict = "CLOSE_OBSERVE_RECOMMENDED"
        close_rec = True
    elif any(r["mdd_gate"] for r in rows) and not any_cagr:
        verdict = "MDD_ONLY"
        close_rec = False
    else:
        verdict = "NO_LIFT"
        close_rec = False
    track_verdicts["CLOSE"] = (
        "CLOSE_OBSERVE_RECOMMENDED" if close_rec else "CLOSE_NOT_YET"
    )

    generated = _utc()
    payload = {
        "schema_version": "earn_beta_defense_stagea_v1",
        "id": SCREEN_ID,
        "generated_at": generated,
        "status": verdict,
        "live_wire": False,
        "exact_t1": "KEEP",
        "soft_frozen_clips": "KEEP",
        "rebalance_l1_live": float(soft.REBALANCE_L1_MIN),
        "book_id": BOOK_ID,
        "gates": {"cagr_lift_pp": CAGR_LIFT_PP, "mdd_slack_pp": MDD_SLACK_PP, "nav_window": HELDOUT},
        "base": {
            "id": "BASE_LIVE_L1_05",
            "n_fills": int(len(base_fills)),
            "exact_t1_ok": bool(base_meta.get("exact_t1_ok")),
            "windows": {HELDOUT: base_w.get(HELDOUT), SEALED: base_w.get(SEALED)},
        },
        "challengers": rows,
        "track_verdicts": track_verdicts,
        "close_observe_recommended": bool(close_rec),
        "binding": [
            "Soft-Frozen clips KEEP",
            "Exact T+1 KEEP",
            "live REBALANCE_L1_MIN=0.05 KEEP",
            "No tip rewrite",
            "No live wire from this Stage A",
            "At most one track for follow-up ACCEPT discussion",
        ],
    }

    lines = [
        "# Earn-beta / defense rhythm Stage A — Screen",
        "",
        f"Generated: `{generated}`",
        f"Status: **`{verdict}`** · clips KEEP · Exact T+1 KEEP · L1={soft.REBALANCE_L1_MIN} KEEP · **no live wire**",
        "",
        "## Track verdicts",
        "",
        "| track | verdict |",
        "|---|---|",
    ]
    for t, v in track_verdicts.items():
        lines.append(f"| `{t}` | `{v}` |")
    bh = base_w[HELDOUT]
    lines += [
        "",
        f"## Base heldout CAGR **{bh.get('cagr')}** · MDD **{bh.get('max_drawdown')}**",
        "",
        "| id | track | CAGR Δpp | CAGR gate | MDD Δpp | MDD gate | HIT | sealed CAGR Δpp |",
        "|---|---|---:|:---:|---:|:---:|:---:|---:|",
    ]
    for r in rows:
        h, s = r["heldout"], r["sealed"]
        lines.append(
            f"| `{r['id']}` | `{r['track']}` | {h.get('cagr_lift_pp')} | "
            f"{'Y' if r['cagr_gate'] else 'n'} | {h.get('mdd_improve_pp')} | "
            f"{'Y' if r['mdd_gate'] else 'n'} | {'Y' if r['hit'] else 'n'} | "
            f"{s.get('cagr_lift_pp')} |"
        )
    read = {
        "EARN_HIT": "≥1 challenger clears heldout CAGR + MDD gates.",
        "CAGR_SOFT": "CAGR lifts but MDD outside slack.",
        "MDD_ONLY": "MDD ok; CAGR gate not cleared.",
        "NO_LIFT": "no material lift.",
        "CLOSE_OBSERVE_RECOMMENDED": "Tracks 1–4 miss CAGR gate → close this earn-beta menu; tip monitor.",
    }[verdict]
    lines += [
        "",
        "### Read",
        "",
        read,
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/earn_beta_defense_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{generated[:10].replace('-', '')}__{verdict}`",
        "",
    ]
    screen_md = "\n".join(lines)

    decision = {
        "schema_version": "earn_beta_defense_stagea_decision_v1",
        "id": DECISION_ID,
        "generated_at": generated,
        "status": verdict,
        "track_verdicts": track_verdicts,
        "live_wire": False,
        "hits": [r["id"] for r in hits],
        "cagr_soft": [r["id"] for r in cagr_soft],
        "close_observe_recommended": bool(close_rec),
        "binding": payload["binding"],
        "next": (
            "CLOSE_OBSERVE — tip monitor; do not reopen this menu without new lever"
            if close_rec
            else "Discussion only — pick ZERO or ONE track; Exact T+1 / clips / L1 KEEP"
        ),
        "label": f"{DECISION_ID}_{generated[:10].replace('-', '')}__{verdict}",
    }
    decision_md = "\n".join(
        [
            "# Earn-beta / defense rhythm Stage A — Decision Pack",
            "",
            f"Date: 2026-09-27 · Generated `{generated}`",
            f"Status: **{verdict}** · clips **KEEP** · Exact T+1 **KEEP** · L1=0.05 **KEEP** · live wire **false**",
            "",
            "Tracks: " + " · ".join(f"`{track_verdicts[t]}`" for t in track_verdicts),
            "",
            "## Binding",
            "",
            "1. Soft-Frozen clips KEEP",
            "2. Exact T+1 KEEP",
            "3. live REBALANCE_L1_MIN=0.05 KEEP",
            "4. No tip rewrite / no live wire from this Stage A",
            "5. At most one track for follow-up ACCEPT discussion",
            "",
            f"Next: {decision['next']}",
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )

    for path, obj in (
        (OUT / f"{SCREEN_ID}.json", payload),
        (REP / f"{SCREEN_ID}.json", payload),
        (OPS / f"{SCREEN_ID}.json", payload),
        (OUT / f"{DECISION_ID}.json", decision),
        (REP / f"{DECISION_ID}.json", decision),
        (OPS / f"{DECISION_ID}.json", decision),
    ):
        path.write_text(json.dumps(obj, indent=2) + "\n")
    for path, text in (
        (OUT / f"{SCREEN_ID}.md", screen_md),
        (REP / f"{SCREEN_ID}.md", screen_md),
        (OPS / f"{SCREEN_ID}.md", screen_md),
        (OUT / f"{DECISION_ID}.md", decision_md),
        (REP / f"{DECISION_ID}.md", decision_md),
        (OPS / f"{DECISION_ID}.md", decision_md),
    ):
        path.write_text(text)
    (REPRO / "README.md").write_text(
        "# Earn-beta / defense rhythm Stage A\n\n"
        "```bash\nPYTHONPATH=scripts python3 scripts/earn_beta_defense_stagea.py\n```\n"
    )
    print(json.dumps({"verdict": verdict, "tracks": track_verdicts, "hits": decision["hits"]}, indent=2))


if __name__ == "__main__":
    main()
