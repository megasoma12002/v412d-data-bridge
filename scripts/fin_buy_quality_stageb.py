#!/usr/bin/env python3
"""FIN buy-quality Stage B — MA120 seed micro-tune (paper).

Charter: research/ops/FIN_BUY_QUALITY_STAGEB_CHARTER.md
Parent Stage A WIN_SOFT · Soft-Frozen KEEP · no live wire.
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
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fin_buy_quality_helpers import (
    and_buy_ok,
    apply_filter_in_season,
    below_ma_ok,
    catalog_gate,
    close_panel,
    forward_win_stats,
    kd_season_mask,
    or_buy_ok,
    rsi_lt_ok,
)
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
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-buy-quality-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_BUY_QUALITY_STAGEB_CHARTER"
SCREEN_ID = "FIN_BUY_QUALITY_STAGEB_SCREEN"
DECISION_ID = "FIN_BUY_QUALITY_STAGEB_DECISION_PACK"
BALLOT_ID = "FIN_BUY_QUALITY_MA120_OBSERVE_BALLOT_DRAFT"
BASE_ID = "CTRL_BASE"
SEED_ID = "SEED_MA120"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

CAGR_FLOOR_PP = 0.15
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
WIN_HIT_PP = 1.0
WIN_OBSERVE_FLOOR_PP = -1.0
WIN_H = 21

GRID: list[dict[str, Any]] = [
    {"id": "CTRL_BASE", "kind": "ctrl"},
    {"id": "SEED_MA120", "kind": "seed", "ma": 120},
    {"id": "B_MA90", "kind": "ma", "ma": 90},
    {"id": "B_MA100", "kind": "ma", "ma": 100},
    {"id": "B_MA150", "kind": "ma", "ma": 150},
    {"id": "B_MA180", "kind": "ma", "ma": 180},
    {"id": "B_MA120_KD_ONLY", "kind": "ma_season", "ma": 120, "in_season": True},
    {"id": "B_MA120_OFF_ONLY", "kind": "ma_season", "ma": 120, "in_season": False},
    {"id": "B_MA120_OR_K9", "kind": "ma_or_k9", "ma": 120},
    {"id": "B_MA120_OR_RSI50", "kind": "ma_or_rsi50", "ma": 120},
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


def _sim(market, target, regime, dividends, *, scores, buy_ok, sell, exposure):
    nav, fills, meta = simulate_core(
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
        e45_exposure=exposure.astype(float),
        e22_version=E22_VERSION,
    )
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def _extra_for_spec(
    spec: dict[str, Any],
    *,
    closes: pd.DataFrame,
    lows: dict,
    season: pd.Series,
) -> pd.DataFrame | None:
    kind = str(spec.get("kind") or "ctrl")
    if kind == "ctrl":
        return None
    ma = int(spec.get("ma") or 120)
    gate = below_ma_ok(closes, ma)
    if kind in ("seed", "ma"):
        return gate
    if kind == "ma_season":
        return apply_filter_in_season(gate, season, in_season=bool(spec.get("in_season")))
    if kind == "ma_or_k9":
        return or_buy_ok(gate, catalog_gate(lows["K9_LT30"]))
    if kind == "ma_or_rsi50":
        return or_buy_ok(gate, rsi_lt_ok(closes, thresh=50.0, n=14))
    raise ValueError(f"unknown kind {kind}")


def _eval_row(
    base_w: dict,
    chal_w: dict,
    tip: dict,
    *,
    book_id: str,
    buy_wr: dict,
    base_buy_wr: dict | None,
) -> dict[str, Any]:
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
    base_rate = None if base_buy_wr is None else base_buy_wr.get("win_rate")
    chal_rate = buy_wr.get("win_rate")
    wr_pp = None
    if base_rate is not None and chal_rate is not None:
        wr_pp = round(float(chal_rate) - float(base_rate), 4)
    wr_hit = wr_pp is not None and float(wr_pp) >= WIN_HIT_PP
    wr_obs = wr_pp is not None and float(wr_pp) >= WIN_OBSERVE_FLOOR_PP
    economic = bool(cagr_ok and mdd_ok and band_ok and tip_ok)
    hit = bool(economic and wr_hit and book_id not in (BASE_ID,))
    observe_ok = bool(economic and wr_obs and book_id != BASE_ID)
    return {
        "held_cagr_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_mdd_pp": tip_ytd,
        "tip_1y_mdd_pp": tip_1y,
        "buy_win_rate": chal_rate,
        "buy_win_rate_pp": wr_pp,
        "buy_win_n": buy_wr.get("n"),
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_safe": bool(tip_ok),
            "buy_win_hit": bool(wr_hit),
            "buy_win_observe": bool(wr_obs),
            "economic": economic,
        },
        "hit": hit,
        "observe_ok": observe_ok,
    }


def _verdict(rows: list[dict[str, Any]]) -> tuple[str, str | None]:
    legal = [r for r in rows if r["id"] != BASE_ID]
    hits = [r for r in legal if r["eval"]["hit"]]
    if hits:
        best = max(hits, key=lambda r: (r["eval"]["held_cagr_pp"] or -9, r["eval"]["held_mdd_pp"] or -9))
        return "BUY_QUALITY_HIT", best["id"]
    obs = [r for r in legal if r["eval"]["observe_ok"]]
    seed = next((r for r in legal if r["id"] == SEED_ID), None)
    micros = [r for r in legal if r["id"] != SEED_ID]
    if obs:
        # Prefer seed if observe-ok; else best economic micro
        if seed and seed["eval"]["observe_ok"]:
            better = [
                r
                for r in micros
                if r["eval"]["observe_ok"]
                and (r["eval"]["held_cagr_pp"] or -9) >= (seed["eval"]["held_cagr_pp"] or -9) + 0.05
                and (r["eval"]["held_mdd_pp"] or -9) >= (seed["eval"]["held_mdd_pp"] or -9) - 0.05
            ]
            if better:
                champ = max(
                    better,
                    key=lambda r: (r["eval"]["held_cagr_pp"] or -9, r["eval"]["held_mdd_pp"] or -9),
                )
                return "OBSERVE_RECOMMENDED", champ["id"]
            # no micro clearly beats seed
            if any(r["eval"]["observe_ok"] for r in micros) and not better:
                # still observe seed; note parent keep flavor
                return "OBSERVE_RECOMMENDED", SEED_ID
            return "OBSERVE_RECOMMENDED", SEED_ID
        champ = max(obs, key=lambda r: (r["eval"]["held_cagr_pp"] or -9, r["eval"]["held_mdd_pp"] or -9))
        return "OBSERVE_RECOMMENDED", champ["id"]
    econ = [r for r in legal if r["eval"]["gates"]["economic"]]
    if econ:
        return "MICRO_SOFT", econ[0]["id"]
    mdd_block = any(
        (r["eval"]["held_mdd_pp"] is not None and float(r["eval"]["held_mdd_pp"]) < HELD_MDD_MIN_PP)
        or not r["eval"]["gates"]["tip_safe"]
        for r in legal
    )
    if mdd_block:
        return "MDD_BLOCK", None
    return "NO_LIFT", None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)

    market = load_market()
    dividends = load_dividends()
    prices, sleeve, _turn, regime = e16_features(market)
    _ = prices
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(market["date"].unique())))
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    closes = close_panel(market, cal, list(FIN))
    season = kd_season_mask(
        cal,
        season_start=tuple(LIVE_KD["season_start"]),
        season_end=tuple(LIVE_KD["season_end"]),
    )
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
    base_buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, list(FIN), pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    scores = _buy(kd, lows)
    sell = _sell(highs)
    sleeve_sc = _sleeve_score(market, sleeve, LIVE_SLEEVE_ALPHA)
    target = _target_live(sleeve_sc, regime)

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
        fin_buy_ok=base_buy_ok,
        fin_sell_scores=sell,
        e22_version=E22_VERSION,
    )
    cool = _cool_from_offense(market, off_nav)

    rows: list[dict[str, Any]] = []
    base_nav = None
    base_w = None
    base_buy_wr: dict[str, Any] | None = None
    fin_set = set(map(str, FIN))

    for spec in GRID:
        bid = str(spec["id"])
        extra = _extra_for_spec(spec, closes=closes, lows=lows, season=season)
        buy_ok = base_buy_ok if extra is None else and_buy_ok(base_buy_ok, extra)
        nav, fills, meta = _sim(
            market,
            target,
            regime,
            dividends,
            scores=scores,
            buy_ok=buy_ok,
            sell=sell,
            exposure=cool,
        )
        _ = meta
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        fills.to_csv(OUT / f"fills_{bid}.csv", index=False)
        w = _pack(nav)
        buy_wr = forward_win_stats(fills, closes, codes=fin_set, side="BUY", horizon=WIN_H)
        if bid == BASE_ID:
            base_nav = nav
            base_w = w
            base_buy_wr = buy_wr
            tip = {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
            }
        else:
            assert base_nav is not None and base_w is not None
            tip = _tip(base_nav, nav)
        ev = _eval_row(
            base_w or w,
            w,
            tip,
            book_id=bid,
            buy_wr=buy_wr,
            base_buy_wr=base_buy_wr,
        )
        rows.append(
            {
                "id": bid,
                "windows": w,
                "tip": tip,
                "eval": ev,
                "buy_wr": buy_wr,
                "spec": spec,
                "n_fills": int(len(fills)),
            }
        )
        print(json.dumps({"book": bid, "eval": ev}, ensure_ascii=False))

    verdict, champ = _verdict(rows)
    # PARENT_KEEP flavor when observe seed and no micro beats it
    if verdict == "OBSERVE_RECOMMENDED" and champ == SEED_ID:
        seed = next(r for r in rows if r["id"] == SEED_ID)
        micros = [r for r in rows if r["id"] not in (BASE_ID, SEED_ID) and r["eval"]["observe_ok"]]
        if not micros:
            pass  # keep OBSERVE_RECOMMENDED
        else:
            # already preferred seed in _verdict
            pass

    generated = _utc()
    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_B_SCREEN_DONE",
        "verdict": verdict,
        "champion": champ,
        "live_wire": False,
        "soft_frozen_keep": True,
        "parent_stage_a": "WIN_SOFT",
        "seed": SEED_ID,
        "gates_hit": {
            "held_cagr_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "buy_win_rate_pp": WIN_HIT_PP,
        },
        "gates_observe": {
            "held_cagr_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "buy_win_rate_pp_floor": WIN_OBSERVE_FLOOR_PP,
        },
        "books": [
            {
                "id": r["id"],
                "windows": r["windows"],
                "tip": r["tip"],
                "eval": r["eval"],
                "buy_wr": r["buy_wr"],
                "spec": r["spec"],
                "n_fills": r["n_fills"],
            }
            for r in rows
        ],
        "binding": [
            "Soft-Frozen KEEP — Stage B does not authorize live wire",
            "Even HIT/OBSERVE → human ballot only",
            "Accept WIN_SOFT → observe when economic clear and WR near-flat",
        ],
    }
    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · champion `{champ}` · Soft-Frozen **KEEP** · live wire **false**",
            "",
            f"Parent Stage A `WIN_SOFT` · seed `{SEED_ID}` (= Stage A `Q_BELOW_MA120`).",
            "",
            "## Books",
            "",
            "| ID | held CAGR↑pp | held MDD↑pp | tip MDD↑pp | buy WR↑pp | HIT | OBS |",
            "|---|---:|---:|---:|---:|---|---|",
        ]
        + [
            "| {id} | {cagr} | {mdd} | {ytd} | {wrpp} | {hit} | {obs} |".format(
                id=r["id"],
                cagr=r["eval"]["held_cagr_pp"],
                mdd=r["eval"]["held_mdd_pp"],
                ytd=r["eval"]["tip_ytd_mdd_pp"],
                wrpp=r["eval"]["buy_win_rate_pp"],
                hit=r["eval"]["hit"],
                obs=r["eval"]["observe_ok"],
            )
            for r in rows
        ]
        + [
            "",
            f"Verdict: **`{verdict}`** · champion **`{champ}`**",
            "",
            f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`",
            "",
        ]
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OPS / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")
    (REP / f"{SCREEN_ID}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (REP / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")

    champ_row = next((r for r in rows if r["id"] == champ), None)
    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · live wire **false**",
        "",
        f"Parent: Stage A `WIN_SOFT` · seed `{SEED_ID}`",
        f"Screen: `{SCREEN_ID}.md`",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
    ]
    if champ_row is not None:
        dlines += [
            (
                f"Champion: `{champ}` · held CAGR↑ {champ_row['eval']['held_cagr_pp']}pp · "
                f"held MDD↑ {champ_row['eval']['held_mdd_pp']}pp · "
                f"buy WR↑ {champ_row['eval']['buy_win_rate_pp']}pp"
            ),
            "",
        ]
    if verdict == "OBSERVE_RECOMMENDED":
        dlines += [
            "## Accept WIN_SOFT → observe",
            "",
            "No Stage B HIT. Economic gates clear with near-flat buy win-rate → "
            "**recommend OPEN paper observe** (draft ballot).",
            "",
            f"Ballot draft: `{BALLOT_ID}.md`",
            "",
        ]
    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen / tip / Exact T+1 KEEP",
        "2. No live wire from Stage B",
        "3. Observe requires human OPEN ballot",
        "",
        f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
        "",
    ]
    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "status": verdict,
        "champion": champ,
        "live_wire": False,
        "soft_frozen_keep": True,
        "parent_stage_a": "WIN_SOFT",
        "seed": SEED_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "ballot_draft": f"research/ops/{BALLOT_ID}.md" if verdict == "OBSERVE_RECOMMENDED" else None,
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

    if verdict == "OBSERVE_RECOMMENDED" and champ_row is not None:
        ballot = "\n".join(
            [
                f"# {BALLOT_ID}",
                "",
                "Status: **DRAFT — not executed** · Soft-Frozen **KEEP** · live wire **false**",
                "",
                "## Proposed human line",
                "",
                "```",
                f"OPEN paper observe: FIN buy-quality `{champ}` (BELOW_MA seed under Soft-Frozen+COOL)",
                "```",
                "",
                "## Why",
                "",
                f"- Stage A `WIN_SOFT` · Stage B `{verdict}`",
                f"- Champion `{champ}`: held CAGR↑ {champ_row['eval']['held_cagr_pp']}pp · "
                f"held MDD↑ {champ_row['eval']['held_mdd_pp']}pp · tip OK · "
                f"buy WR↑ {champ_row['eval']['buy_win_rate_pp']}pp (observe floor −1pp)",
                "- Explicit accept: joint win-rate HIT not required for paper observe",
                "",
                "## Non-goals",
                "",
                "- Live wire · Soft-Frozen retune · tip rewrite",
                "",
                f"Label: `{BALLOT_ID}_2026-09-28__DRAFT`",
                "",
            ]
        )
        (OPS / f"{BALLOT_ID}.md").write_text(ballot, encoding="utf-8")
        write_ops_and_repro_pointer(
            OPS / f"{BALLOT_ID}.md",
            REP / f"{BALLOT_ID}.md",
            ballot,
        )

    for path in (OPS / f"{CHARTER_ID}.md", OPS / f"{CHARTER_ID}.zh-TW.md"):
        txt = path.read_text(encoding="utf-8")
        if "Stage B OPEN" in txt or "Stage B OPEN" in txt.replace("**", ""):
            txt2 = txt.replace(
                "Status: **Stage B OPEN**",
                f"Status: **Stage B DONE — `{verdict}`**",
                1,
            ).replace(
                "狀態：**Stage B OPEN**",
                f"狀態：**Stage B DONE — `{verdict}`**",
                1,
            )
            if txt2 != txt:
                path.write_text(txt2, encoding="utf-8")

    print(json.dumps({"verdict": verdict, "champion": champ, "n_books": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
