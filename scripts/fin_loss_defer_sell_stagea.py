#!/usr/bin/env python3
"""FIN loss-defer sell Stage A — paper only (COOL gate prior).

Charter: research/ops/FIN_LOSS_DEFER_SELL_STAGEA_CHARTER.md
Soft-Frozen KEEP · Exact T+1 KEEP · COOL_c8 KEEP · no live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, TEL, e16_features, simulate_core
from fin_loss_defer_sell_helpers import LossDeferPolicy
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from ops_repro_ssot import write_ops_and_repro_pointer
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
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    TEL_RS_SOFT_TILT,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-loss-defer-sell-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_LOSS_DEFER_SELL_STAGEA_CHARTER"
SCREEN_ID = "FIN_LOSS_DEFER_SELL_STAGEA_SCREEN"
DECISION_ID = "FIN_LOSS_DEFER_SELL_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_NO_DEFER"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

CAGR_FLOOR_PP = 0.15
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0

GRID: list[dict[str, Any]] = [
    {"id": "CTRL_NO_DEFER", "policy": None},
    {"id": "D_FIN_LOSS0_W5", "universe": "FIN", "max_wait": 5, "loss_band": 0.0, "cool_gate": True},
    {"id": "D_FIN_LOSS0_W10", "universe": "FIN", "max_wait": 10, "loss_band": 0.0, "cool_gate": True},
    {"id": "D_FIN_LOSS0_W21", "universe": "FIN", "max_wait": 21, "loss_band": 0.0, "cool_gate": True},
    {"id": "D_FIN_LOSS2_W10", "universe": "FIN", "max_wait": 10, "loss_band": -0.02, "cool_gate": True},
    {"id": "D_FIN_LOSS5_W10", "universe": "FIN", "max_wait": 10, "loss_band": -0.05, "cool_gate": True},
    {
        "id": "D_FIN_WORST_FIRST_W10",
        "universe": "FIN",
        "max_wait": 10,
        "loss_band": 0.0,
        "cool_gate": True,
        "worst_first": True,
    },
    {"id": "D_TEL_LOSS0_W10", "universe": "TEL", "max_wait": 10, "loss_band": 0.0, "cool_gate": True},
    {
        "id": "D_FIN_LOSS0_W10_NOCOOLGATE",
        "universe": "FIN",
        "max_wait": 10,
        "loss_band": 0.0,
        "cool_gate": False,
    },
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _cool_from_offense(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def _sim(
    market,
    target,
    regime,
    dividends,
    *,
    scores,
    buy_ok,
    sell,
    exposure,
    policy=None,
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
        fin_sell_scores=sell,
        e45_exposure=exposure.astype(float),
        e22_version=E22_VERSION,
        loss_defer_policy=policy,
    )
    if tel_scores is not None:
        kw["tel_name_scores"] = tel_scores
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kw)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def _make_policy(spec: dict[str, Any]) -> LossDeferPolicy | None:
    if spec.get("policy") is None and "universe" not in spec:
        return None
    univ = set(FIN) if spec.get("universe") == "FIN" else set(TEL)
    return LossDeferPolicy(
        universe=univ,
        max_wait=int(spec.get("max_wait", 10)),
        loss_band=float(spec.get("loss_band", 0.0)),
        cool_gate=bool(spec.get("cool_gate", True)),
        worst_first=bool(spec.get("worst_first", False)),
    )


def _eval_row(base_w: dict, chal_w: dict, tip: dict, meta: dict, book_id: str) -> dict[str, Any]:
    held_b = base_w.get("heldout_2019_plus") or {}
    held_c = chal_w.get("heldout_2019_plus") or {}
    cagr_pp = cagr_delta_pp(held_b.get("cagr"), held_c.get("cagr"))
    mdd_pp = mdd_delta_pp(held_b.get("max_drawdown"), held_c.get("max_drawdown"))
    abs_mdd = held_c.get("max_drawdown")
    tip_ytd = (tip.get("ytd") or {}).get("mdd_improve_pp")
    tip_1y = (tip.get("trailing_1y") or {}).get("mdd_improve_pp")
    tip_ok = (
        tip_ytd is not None
        and tip_1y is not None
        and float(tip_ytd) >= TIP_MDD_MIN_PP
        and float(tip_1y) >= TIP_MDD_MIN_PP
    )
    cagr_ok = cagr_pp is not None and float(cagr_pp) >= CAGR_FLOOR_PP
    mdd_ok = mdd_pp is not None and float(mdd_pp) >= HELD_MDD_MIN_PP
    band_ok = abs_mdd is not None and abs(float(abs_mdd)) <= HELD_ABS_MDD_MAX
    cool_viol = int((meta.get("loss_defer") or {}).get("cool_gate_violations") or 0)
    cool_ok = cool_viol == 0 or book_id.endswith("NOCOOLGATE")
    return {
        "held_cagr_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_mdd_pp": tip_ytd,
        "tip_1y_mdd_pp": tip_1y,
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_safe": bool(tip_ok),
            "cool_integrity": bool(cool_ok),
        },
        "hit": bool(cagr_ok and mdd_ok and band_ok and tip_ok and cool_ok and not book_id.endswith("NOCOOLGATE")),
        "loss_defer": meta.get("loss_defer"),
        "n_fills": int(meta.get("n_fills") or 0),
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    legal = [r for r in rows if r["id"] != "CTRL_NO_DEFER"]
    hits = [r for r in legal if r["eval"]["hit"]]
    if hits:
        return "LOSS_DEFER_HIT"
    nocool = next((r for r in legal if r["id"].endswith("NOCOOLGATE")), None)
    gated = [r for r in legal if not r["id"].endswith("NOCOOLGATE")]
    # If only nocool looks CAGR-strong while gated fail MDD → COOL_GATE_REQUIRED
    if nocool is not None:
        ng = nocool["eval"]
        gated_mdd_fail = all(
            not (r["eval"]["gates"]["mdd_near_flat"] and r["eval"]["gates"]["tip_safe"])
            for r in gated
        )
        if (
            ng["gates"]["cagr"]
            and ng["loss_defer"]
            and int(ng["loss_defer"].get("cool_gate_violations") or 0) > 0
            and gated_mdd_fail
        ):
            return "COOL_GATE_REQUIRED"
    mdd_block = any(
        (r["eval"]["held_mdd_pp"] is not None and float(r["eval"]["held_mdd_pp"]) < HELD_MDD_MIN_PP)
        or not r["eval"]["gates"]["tip_safe"]
        for r in gated
    )
    if mdd_block and not any(r["eval"]["gates"]["cagr"] for r in gated):
        return "MDD_BLOCK"
    if any(
        r["eval"]["gates"]["mdd_near_flat"]
        and r["eval"]["gates"]["tip_safe"]
        and r["eval"]["gates"]["mdd_band"]
        and not r["eval"]["gates"]["cagr"]
        for r in gated
    ):
        return "CAGR_SOFT"
    if mdd_block:
        return "MDD_BLOCK"
    return "NO_LIFT"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)

    market = load_market()
    dividends = load_dividends()
    prices, sleeve, _turn, regime = e16_features(market)
    _ = prices
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(market["date"].unique())))
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market,
        dividends,
        list(FIN),
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, list(FIN), pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    scores = _buy(kd, lows)
    sell = _sell(highs)
    sleeve_sc = _sleeve_score(market, sleeve, LIVE_SLEEVE_ALPHA)
    target = _target_live(sleeve_sc, regime)

    # Shared COOL path from FUSE offense (no exposure)
    off_nav, _fills, _meta = simulate_core(
        market,
        target,
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
        e22_version=E22_VERSION,
    )
    cool = _cool_from_offense(market, off_nav)

    # Flat TEL scores so TEL_RS_SOFT_TILT still routes through allocate_sleeve_orders (sell_ok).
    tel_flat = pd.DataFrame(1.0, index=cal, columns=list(TEL))

    rows: list[dict[str, Any]] = []
    base_nav = None
    base_w = None
    for spec in GRID:
        bid = str(spec["id"])
        policy = _make_policy(spec)
        tel_alloc = TEL_RS_SOFT_TILT if spec.get("universe") == "TEL" else TEL_EQUAL
        tel_sc = tel_flat if spec.get("universe") == "TEL" else None
        nav, fills, meta = _sim(
            market,
            target,
            regime,
            dividends,
            scores=scores,
            buy_ok=buy_ok,
            sell=sell,
            exposure=cool,
            policy=policy,
            telecom_alloc=tel_alloc,
            tel_scores=tel_sc,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        fills.to_csv(OUT / f"fills_{bid}.csv", index=False)
        w = _pack(nav)
        if bid == BASE_ID:
            base_nav = nav
            base_w = w
            tip = {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
            }
        else:
            assert base_nav is not None and base_w is not None
            tip = _tip(base_nav, nav)
        ev = _eval_row(base_w or w, w, tip, meta, bid)
        rows.append({"id": bid, "windows": w, "tip": tip, "eval": ev, "spec": {k: v for k, v in spec.items() if k != "policy"}})
        print(json.dumps({"book": bid, "eval": ev}, ensure_ascii=False))

    verdict = _verdict(rows)
    generated = _utc()
    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "exact_t1_keep": True,
        "cool_keep": True,
        "base_id": BASE_ID,
        "gates": {
            "held_cagr_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "held_abs_mdd_max": HELD_ABS_MDD_MAX,
            "tip_mdd_pp_floor": TIP_MDD_MIN_PP,
        },
        "books": rows,
        "binding": [
            "Soft-Frozen live KEEP — Stage A does not authorize sell-overlay live wire",
            "Exact T+1 KEEP",
            "COOL forced de-risk lexically prior to loss-defer (except NOCOOLGATE negative control)",
            "Not a FIFO accounting rewrite",
            "No tip history rewrite",
        ],
    }

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
            "",
            f"Base `{BASE_ID}` = live Soft-Frozen + FUSE SELL_a75 + COOL_c8 · Exact T+1.",
            "",
            "## Books",
            "",
            "| ID | held CAGR↑pp | held MDD↑pp | tip YTD MDD↑pp | tip 1y MDD↑pp | HIT | defer |",
            "|---|---:|---:|---:|---:|---|---:|",
        ]
        + [
            "| {id} | {cagr} | {mdd} | {ytd} | {t1y} | {hit} | {def_} |".format(
                id=r["id"],
                cagr=r["eval"]["held_cagr_pp"],
                mdd=r["eval"]["held_mdd_pp"],
                ytd=r["eval"]["tip_ytd_mdd_pp"],
                t1y=r["eval"]["tip_1y_mdd_pp"],
                hit=r["eval"]["hit"],
                def_=(r["eval"]["loss_defer"] or {}).get("deferred_sells"),
            )
            for r in rows
        ]
        + [
            "",
            f"Verdict: **`{verdict}`**",
            "",
            f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`",
            "",
        ]
    )

    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (REP / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OPS / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")

    best = None
    for r in rows:
        if r["eval"]["hit"]:
            best = r
            break
    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · COOL **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
    ]
    if best:
        dlines += [
            f"Best HIT book: `{best['id']}` · held CAGR↑ {best['eval']['held_cagr_pp']}pp · held MDD↑ {best['eval']['held_mdd_pp']}pp",
            "",
        ]
    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen / tip / Exact T+1 KEEP",
        "2. COOL forced de-risk prior to loss-defer",
        "3. Even HIT → paper observe ballot only (separate ACCEPT for live)",
        "4. Not FIFO accounting rewrite",
        "",
        f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
        "",
    ]
    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "best_hit": None if best is None else best["id"],
        "generated_at_utc": generated,
    }
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(decision, indent=2, ensure_ascii=False) + "\n",
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        "\n".join(dlines),
    )

    # charter status line
    ch = (OPS / f"{CHARTER_ID}.md").read_text(encoding="utf-8")
    ch2 = ch.replace(
        "Status: **Stage A OPEN**",
        f"Status: **Stage A DONE — `{verdict}`**",
        1,
    )
    if ch2 != ch:
        (OPS / f"{CHARTER_ID}.md").write_text(ch2, encoding="utf-8")

    print(json.dumps({"verdict": verdict, "n_books": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
