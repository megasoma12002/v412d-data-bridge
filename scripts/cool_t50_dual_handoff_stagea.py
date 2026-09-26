#!/usr/bin/env python3
"""COOL dual-handoff Stage A — defend 00632R → exit pulse 00631L (mutex).

Charter: research/ops/COOL_T50_DUAL_HANDOFF_STAGEA_CHARTER.md
Soft-Frozen KEEP · no live wire · separate-leg priors do not compose.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import cool_t50_lev_rebound_stagea as reb
import cool_t50_lev_short_assist_stagea as short
import e45_defend_handoff_stagea_screen as stagea
from e50_early_stack_combined_nav import FIN, simulate_core
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import FIN_PRE_EXDIV_KD, TEL_EQUAL

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "cool-t50-dual-handoff-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "COOL_T50_DUAL_HANDOFF_STAGEA_CHARTER"
SCREEN_ID = "COOL_T50_DUAL_HANDOFF_STAGEA_SCREEN"
DECISION_ID = "COOL_T50_DUAL_HANDOFF_DECISION_PACK"
BASE_ID = "BASE_LIVE_FUSE_COOL"
INV_CODE = "00632R"
LEV_CODE = "00631L"
INV_PRICE = ROOT / "data" / "def_proxies" / "00632R_ohlcv.csv"
LEV_PRICE = ROOT / "data" / "def_proxies" / "00631L_ohlcv.csv"
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)
HELDOUT = sat.HELDOUT
SEALED = sat.SEALED
CAGR_FLOOR_PP = sat.CAGR_FLOOR_PP
HELD_MDD_MIN_PP = sat.HELD_MDD_MIN_PP
SEALED_MDD_MIN_PP = sat.SEALED_MDD_MIN_PP
TIP_MDD_TOL_PP = sat.TIP_MDD_TOL_PP


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_bars(path: Path, code: str) -> pd.DataFrame:
    raw = pd.read_csv(path, parse_dates=["date"])
    raw["code"] = code
    for c in ("open", "high", "low", "close", "adj_close"):
        if c not in raw.columns:
            raise ValueError(f"missing {c} in {path}")
    raw["volume"] = raw.get("volume", 0)
    return raw[["date", "code", "open", "high", "low", "close", "adj_close", "volume"]]


def _attach_one(market: pd.DataFrame, bars: pd.DataFrame, code: str) -> tuple[pd.DataFrame, pd.Timestamp]:
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    inv = bars.copy()
    inv["date"] = pd.to_datetime(inv["date"])
    eq_dates = pd.DatetimeIndex(sorted(m["date"].unique()))
    piv_o = inv.set_index("date")["open"].reindex(eq_dates)
    piv_c = inv.set_index("date")["close"].reindex(eq_dates)
    piv_a = inv.set_index("date")["adj_close"].reindex(eq_dates)
    first = piv_c.first_valid_index()
    if first is None:
        raise RuntimeError(f"{code} has no valid bars on equity calendar")
    piv_o = piv_o.ffill().bfill()
    piv_c = piv_c.ffill().bfill()
    piv_a = piv_a.ffill().bfill()
    rows = pd.DataFrame(
        {
            "date": eq_dates,
            "code": code,
            "open": piv_o.to_numpy(),
            "high": piv_c.to_numpy(),
            "low": piv_c.to_numpy(),
            "close": piv_c.to_numpy(),
            "adj_close": piv_a.to_numpy(),
            "volume": 0.0,
        }
    )
    out = pd.concat([m, rows], ignore_index=True).sort_values(["date", "code"])
    return out, pd.Timestamp(first)


def build_dual_schedule(
    target3: pd.DataFrame,
    cool: pd.Series,
    *,
    alpha_inv: float,
    alpha_lev: float,
    hold_h: int,
    listed_inv: pd.Timestamp,
    listed_lev: pd.Timestamp,
    confirm: str | None,
    ret1: pd.Series,
    ret3: pd.Series,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """DEF=00632R while defending; OFF=00631L pulse on exit; mutex handoff lock."""
    idx = target3.index
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    inv_ok = pd.Series(idx >= listed_inv, index=idx)
    lev_ok = pd.Series(idx >= listed_lev, index=idx)
    exits = reb.cool_exits(c)
    entry = exits & lev_ok
    if confirm == "RET1":
        entry = entry & (ret1.reindex(idx) > 0)
    elif confirm == "RET3":
        entry = entry & (ret3.reindex(idx) > 0)
    elif confirm in (None, "NONE"):
        pass
    else:
        raise ValueError(confirm)

    pulse = pd.Series(False, index=idx)
    entry_locs = [i for i, v in enumerate(entry.to_numpy()) if bool(v)]
    n = len(idx)
    for i0 in entry_locs:
        for k in range(int(hold_h)):
            j = i0 + k
            if j < n:
                pulse.iloc[j] = True

    off_w = pd.Series(0.0, index=idx, dtype=float)
    off_w = off_w.where(~pulse, float(alpha_lev))
    off_w = off_w.where(lev_ok, 0.0)

    defending = (c < 1.0 - 1e-12) & inv_ok
    residual = (1.0 - c).clip(lower=0.0)
    def_w = (float(alpha_inv) * residual).where(defending, 0.0)
    # Handoff lock: suppress INV while LEV pulse active
    def_w = def_w.where(~(off_w > 0), 0.0)

    soft_scale = c * (1.0 - off_w).clip(lower=0.0)
    sched = pd.DataFrame(
        {
            "Financial": target3["Financial"].astype(float) * soft_scale,
            "Telecom": target3["Telecom"].astype(float) * soft_scale,
            "0050": target3["0050"].astype(float) * soft_scale,
            "DEF": def_w.astype(float),
            "OFF": off_w.astype(float),
        },
        index=idx,
    )
    meta = {
        "confirm": confirm,
        "alpha_inv": float(alpha_inv),
        "alpha_lev": float(alpha_lev),
        "hold_h": int(hold_h),
        "n_entries": int(len(entry_locs)),
        "pulse_frac": round(float((off_w > 0).mean()), 6),
        "mean_off": round(float(off_w.mean()), 6),
        "mean_def": round(float(def_w.mean()), 6),
        "defend_frac_inv": round(float((def_w > 0).mean()), 6),
    }
    return sched, meta


def _sim_dual(market, tgt, regime, dividends, *, scores, buy_ok, sell, schedule):
    nav, fills, meta = simulate_core(
        market,
        tgt[["Financial", "Telecom", "0050"]],
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
        e22_version=sat.E22_VERSION,
        sleeve_weight_schedule=schedule,
        def_code=INV_CODE,
        off_code=LEV_CODE,
    )
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, int(len(fills)), meta


def _score_dual(base_w, chal_w, tip, *, rid, meta, n_fills, defend_frac):
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
        "held_cagr_floor": (held_cagr_lift or 0.0) >= CAGR_FLOOR_PP,
    }
    score = 0.5 * ((held_cagr_lift or 0.0) + (sealed_cagr_lift or 0.0)) + 0.5 * (
        held_mdd_up + sealed_mdd_up
    )
    coexist = all(gates.values())
    return {
        "id": rid,
        "n_fills": n_fills,
        "defend_frac": round(float(defend_frac), 6),
        "held_cagr_lift_pp": None if held_cagr_lift is None else round(held_cagr_lift, 4),
        "sealed_cagr_lift_pp": None if sealed_cagr_lift is None else round(sealed_cagr_lift, 4),
        "held_mdd_improve_pp": round(held_mdd_up, 4),
        "sealed_mdd_improve_pp": round(sealed_mdd_up, 4),
        "score": round(float(score), 4),
        "gates": gates,
        "coexist": coexist,
        "tip": tip,
        "meta": meta,
        "windows": chal_w,
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert INV_PRICE.exists(), INV_PRICE
    assert LEV_PRICE.exists(), LEV_PRICE
    assert sat.soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]

    print("loading ...", flush=True)
    market0 = sat.load_market()
    dividends = sat.load_dividends()
    inv_bars = _load_bars(INV_PRICE, INV_CODE)
    lev_bars = _load_bars(LEV_PRICE, LEV_CODE)
    market, listed_inv = _attach_one(market0, inv_bars, INV_CODE)
    market, listed_lev = _attach_one(market, lev_bars, LEV_CODE)

    from e50_early_stack_combined_nav import e16_features
    from soft_assist_helpers import LIVE_KD
    from ta_indicator_catalog import build_low_high_catalog
    from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

    _p, sleeve, _tgt, regime = e16_features(market0)
    cal = pd.DatetimeIndex(pd.to_datetime(market0["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market0, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market0,
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
    buy_live = sat._buy(kd, lows)
    sell_live = sat._sell(highs, SELL_AMP)
    score_live = sat._sleeve_score(market0, sleeve, float(sat.LIVE_SLEEVE_ALPHA))
    tgt_live = sat._target_live(score_live, regime)

    fuse_off, _, _ = sat._sim(
        market0,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=pd.Series(1.0, index=tgt_live.index),
    )
    cool = sat._cool_from_offense(market0, fuse_off)
    defend_frac = float((cool.reindex(tgt_live.index).fillna(1.0) < 1.0 - 1e-12).mean())
    nav_s = stagea._nav_series(fuse_off)
    feat = stagea._risk_features(market0, nav_s)
    proxy = feat["proxy_mdd63"].reindex(tgt_live.index).fillna(0.0)
    ret1, ret3 = short._0050_rets(market0, tgt_live.index)

    print(f"{BASE_ID} ...", flush=True)
    base_nav, n_base, _ = sat._sim(
        market0,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=cool,
    )
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    base_w = sat._pack(base_nav)

    # Reference INV-only (α=0.25) via single DEF on market with both attached unused
    print("REF_INV_A25 ...", flush=True)
    sat.DEF_CODE = INV_CODE
    sat.DEF_PRICE = INV_PRICE
    inv_sched = sat.build_schedule(
        tgt_live, cool, alpha=0.25, mode="defending", listed_from=listed_inv
    )
    # schedule only DEF — use market with INV only path via sat._sim after setting DEF
    # Attach INV-only market for clean REF (reuse dual market: OFF column absent)
    inv_only_market, _ = _attach_one(market0, inv_bars, INV_CODE)
    inv_nav, n_inv, _ = sat._sim(
        inv_only_market,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        schedule=inv_sched,
    )
    inv_nav.to_csv(OUT / "nav_REF_INV_A25.csv", index=False)

    print("REF_LEV_RET3_A10_H5 ...", flush=True)
    sat.DEF_CODE = LEV_CODE
    sat.DEF_PRICE = LEV_PRICE
    lev_only_market, _ = _attach_one(market0, lev_bars, LEV_CODE)
    lev_sched, lev_meta = short.build_schedule(
        tgt_live,
        cool,
        alpha=0.10,
        hold_h=5,
        listed_from=listed_lev,
        track="CONFIRM",
        confirm="RET3",
        ret1=ret1,
        ret3=ret3,
        proxy=proxy,
        off_px=short._off_close(lev_bars, tgt_live.index),
    )
    lev_nav, n_lev, _ = sat._sim(
        lev_only_market,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        schedule=lev_sched,
    )
    lev_nav.to_csv(OUT / "nav_REF_LEV_RET3_A10_H5.csv", index=False)

    dual_books = [
        ("DH_I25_L_RET3_A10_H5", 0.25, "RET3", 0.10, 5),
        ("DH_I25_L_RET3_A10_H3", 0.25, "RET3", 0.10, 3),
        ("DH_I25_L_RET1_A10_H3", 0.25, "RET1", 0.10, 3),
        ("DH_I10_L_RET3_A10_H5", 0.10, "RET3", 0.10, 5),
        ("DH_I25_L_RET3_A05_H5", 0.25, "RET3", 0.05, 5),
        ("DH_I25_L_NONE_A10_H5", 0.25, "NONE", 0.10, 5),
    ]

    rows: list[dict[str, Any]] = []

    tip_b = sat._tip(base_nav, base_nav)
    base_row = _score_dual(
        base_w, base_w, tip_b, rid=BASE_ID, meta={}, n_fills=n_base, defend_frac=defend_frac
    )
    base_row.update({"kind": "BASE", "coexist": False})
    rows.append(base_row)

    tip_i = sat._tip(base_nav, inv_nav)
    inv_row = _score_dual(
        base_w,
        sat._pack(inv_nav),
        tip_i,
        rid="REF_INV_A25",
        meta={"alpha_inv": 0.25, "alpha_lev": 0.0},
        n_fills=n_inv,
        defend_frac=defend_frac,
    )
    inv_row["kind"] = "REF_INV"
    rows.append(inv_row)

    tip_l = sat._tip(base_nav, lev_nav)
    lev_row = _score_dual(
        base_w,
        sat._pack(lev_nav),
        tip_l,
        rid="REF_LEV_RET3_A10_H5",
        meta=lev_meta,
        n_fills=n_lev,
        defend_frac=defend_frac,
    )
    lev_row["kind"] = "REF_LEV"
    rows.append(lev_row)

    for i, (bid, a_inv, conf, a_lev, hold_h) in enumerate(dual_books, 1):
        print(f"  [{i}/{len(dual_books)}] {bid} ...", flush=True)
        sched, meta = build_dual_schedule(
            tgt_live,
            cool,
            alpha_inv=float(a_inv),
            alpha_lev=float(a_lev),
            hold_h=int(hold_h),
            listed_inv=listed_inv,
            listed_lev=listed_lev,
            confirm=conf,
            ret1=ret1,
            ret3=ret3,
        )
        sched.to_csv(OUT / f"schedule_{bid}.csv")
        nav, n_fills, _ = _sim_dual(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            schedule=sched,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = sat._tip(base_nav, nav)
        row = _score_dual(
            base_w,
            sat._pack(nav),
            tip,
            rid=bid,
            meta=meta,
            n_fills=n_fills,
            defend_frac=defend_frac,
        )
        row["kind"] = "DUAL"
        rows.append(row)

    dual = [r for r in rows if r["kind"] == "DUAL"]
    hits = [r for r in dual if r["coexist"]]
    softs = [
        r
        for r in dual
        if r["gates"]["tip_mdd_ok"]
        and r["gates"]["sealed_mdd"]
        and r["gates"]["held_mdd"]
        and not r["gates"]["held_cagr_floor"]
    ]
    if hits:
        verdict = "DUAL_HANDOFF_HIT"
    elif softs:
        verdict = "DUAL_HANDOFF_SOFT"
    elif any(r["gates"]["tip_clean"] for r in dual):
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

    ranked = sorted(dual, key=lambda r: float(r["score"]), reverse=True)
    payload = {
        "generated_at_utc": _utc(),
        "schema_version": "cool_t50_dual_handoff_stagea_v1",
        "charter_id": CHARTER_ID,
        "screen_id": SCREEN_ID,
        "decision_id": DECISION_ID,
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "sell_amp": SELL_AMP,
        "inv_code": INV_CODE,
        "lev_code": LEV_CODE,
        "listed_inv": str(listed_inv.date()),
        "listed_lev": str(listed_lev.date()),
        "defend_frac": round(defend_frac, 6),
        "n_dual": len(dual),
        "n_hit": len(hits),
        "n_soft": len(softs),
        "books": rows,
        "ranked_dual_ids": [r["id"] for r in ranked],
        "hit_ids": [r["id"] for r in hits],
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    def _fmt(r: dict) -> str:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        return (
            f"| `{r['id']}` | {r['held_cagr_lift_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{r['held_mdd_improve_pp']:+.2f} | {tip_ok} | {r['score']:+.2f} |"
        )

    screen_md = [
        "# COOL dual-handoff — Stage A Screen",
        "",
        f"Date: 2026-09-26 · Generated `{payload['generated_at_utc']}`",
        f"Verdict: **`{verdict}`** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        f"DEF=`{INV_CODE}` · OFF=`{LEV_CODE}` · sell_amp=**{SELL_AMP}** · defend_frac=**{defend_frac:.2%}**",
        f"listed_inv **{listed_inv.date()}** · listed_lev **{listed_lev.date()}**",
        "",
        f"Dual books: **{len(dual)}** · HIT: **{len(hits)}** · SOFT: **{len(softs)}**",
        "",
        "## Dual challengers (vs BASE)",
        "",
        "| id | held CAGR↑ | sealed MDD↑ | held MDD↑ | tip | score |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for r in ranked:
        screen_md.append(_fmt(r))
    screen_md += [
        "",
        "## References",
        "",
        "| id | held CAGR↑ | sealed MDD↑ | held MDD↑ | tip |",
        "|---|---:|---:|---:|---|",
        (
            f"| `REF_INV_A25` | {inv_row['held_cagr_lift_pp']:+.2f} | {inv_row['sealed_mdd_improve_pp']:+.2f} | "
            f"{inv_row['held_mdd_improve_pp']:+.2f} | {'Y' if inv_row['gates']['tip_mdd_ok'] else 'N'} |"
        ),
        (
            f"| `REF_LEV_RET3_A10_H5` | {lev_row['held_cagr_lift_pp']:+.2f} | {lev_row['sealed_mdd_improve_pp']:+.2f} | "
            f"{lev_row['held_mdd_improve_pp']:+.2f} | {'Y' if lev_row['gates']['tip_mdd_ok'] else 'N'} |"
        ),
        "",
        "## Binding",
        "",
        "1. Soft-Frozen + COOL params **KEEP**.",
        "2. Separate-leg HIT/SOFT **do not compose** — only dual books decide verdict.",
        "3. Even HIT → paper observe only; live needs Class D for both satellites.",
        "",
        f"Label: `{SCREEN_ID}_2026-09-26__{verdict}`",
        "",
    ]
    (REP / f"{SCREEN_ID}.md").write_text("\n".join(screen_md) + "\n")
    (OPS / f"{SCREEN_ID}.md").write_text("\n".join(screen_md) + "\n")

    best = hits[0] if hits else (softs[0] if softs else (ranked[0] if ranked else None))
    decision_md = [
        "# COOL dual-handoff — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-26 · Generated `{payload['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "Human: `開 dual-handoff Stage A`",
        "",
        f"Dual HIT: **{len(hits)}** · SOFT: **{len(softs)}** / {len(dual)} dual books.",
        "",
    ]
    if hits:
        decision_md += [
            "HIT books (predeclared gates):",
            "",
            "| id | held CAGR↑ | sealed MDD↑ | held MDD↑ |",
            "|---|---:|---:|---:|",
        ]
        for r in hits:
            decision_md.append(
                f"| `{r['id']}` | {r['held_cagr_lift_pp']:+.2f} | "
                f"{r['sealed_mdd_improve_pp']:+.2f} | {r['held_mdd_improve_pp']:+.2f} |"
            )
        decision_md += ["", "Next: paper observe ballot only — not live.", ""]
    elif softs:
        decision_md += [
            "SOFT (MDD/tip OK, CAGR short of +0.20):",
            "",
            "| id | held CAGR↑ | sealed MDD↑ |",
            "|---|---:|---:|",
        ]
        for r in softs[:5]:
            decision_md.append(
                f"| `{r['id']}` | {r['held_cagr_lift_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} |"
            )
        decision_md += ["", "Reading: dual stack does not clear CAGR floor under KEEP objective.", ""]
    else:
        decision_md += [
            "No dual book cleared tip+MDD coexistence under predeclared gates.",
            "",
            f"Score-top dual: `{best['id']}` held CAGR↑ {best['held_cagr_lift_pp']:+.2f} · "
            f"sealed MDD↑ {best['sealed_mdd_improve_pp']:+.2f}."
            if best
            else "",
            "",
            "Reading: stacking INV ahead of LEV does **not** inherit LEV-only HIT.",
            "",
        ]
    decision_md += [
        "## Refs",
        "",
        f"- Charter: `{CHARTER_ID}.md`",
        f"- Screen: `{SCREEN_ID}.md`",
        "- Parents: `COOL_T50_INV_SATELLITE_DECISION_PACK.md` · `COOL_T50_LEV_SHORT_ASSIST_DECISION_PACK.md`",
        "",
        f"Label: `{DECISION_ID}_2026-09-26__{verdict}`",
        "",
    ]
    decision = {
        **{k: payload[k] for k in ("generated_at_utc", "verdict", "n_hit", "n_soft", "hit_ids")},
        "best_dual_id": None if best is None else best["id"],
        "soft_frozen_keep": True,
        "live_wire": False,
    }
    (REP / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (REP / f"{DECISION_ID}.md").write_text("\n".join(decision_md) + "\n")
    (OPS / f"{DECISION_ID}.md").write_text("\n".join(decision_md) + "\n")

    # Seal charter status
    charter_path = OPS / f"{CHARTER_ID}.md"
    if charter_path.exists():
        txt = charter_path.read_text()
        txt = txt.replace(
            "Status: **CHARTER OPEN · Stage A RUNNING**",
            f"Status: **CHARTER OPEN · Stage A DONE → `{verdict}`**",
        )
        charter_path.write_text(txt)

    print(json.dumps({"verdict": verdict, "n_hit": len(hits), "n_soft": len(softs)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
