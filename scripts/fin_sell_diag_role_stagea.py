#!/usr/bin/env python3
"""FIN sell **diagnostic role** Stage A — label only; never gate ``fin_sell_ok``.

Charter: research/ops/FIN_SELL_DIAG_ROLE_STAGEA_CHARTER.md
Simulates live CTRL_BASE once (SELL_a75 + Soft-Frozen + COOL), then attributes
each FIN SELL fill. Conditional WR is diagnostic — does **not** change NAV,
does **not** authorize observe/live, does **not** reopen hard sell gates.
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
from e45_paper_harness import load_dividends, load_market
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fin_sell_diag_role_helpers import (
    atr_expand_ok,
    breakdown_ok,
    close_panel,
    conditional_wr,
    down_days_ok,
    lookup_attr,
    macd_flip_neg_ok,
    persist_ok,
    raw_ohlcv_panels,
    sell_fill_forward_rows,
    volume_spike_ok,
)
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from ops_repro_ssot import write_ops_and_repro_pointer
from portfolio_capital import DEFAULT_CAPITAL
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
REPRO = ROOT / "repro" / "fin-sell-diag-role-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SELL_DIAG_ROLE_STAGEA_CHARTER"
SCREEN_ID = "FIN_SELL_DIAG_ROLE_STAGEA_SCREEN"
DECISION_ID = "FIN_SELL_DIAG_ROLE_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_BASE"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

WIN_H = 21
# Diagnostic bars (not economic CAGR/MDD gates — no portfolio change).
SIGNAL_LIFT_PP = 3.0
SIGNAL_N_MIN = 80
SIGNAL_COV_LO = 5.0
SIGNAL_COV_HI = 70.0
WEAK_LIFT_PP = 1.5
WEAK_N_MIN = 50

# Attribute ids evaluated on live fills (no fin_sell_ok applied).
ATTR_SPECS: list[dict[str, str]] = [
    {"id": "A_PERSIST2", "label": "sell-fire RSI6_GT80 persist 2d"},
    {"id": "A_PERSIST3", "label": "sell-fire persist 3d"},
    {"id": "A_DN1", "label": "today ret < 0"},
    {"id": "A_DN2", "label": "2 consecutive down days"},
    {"id": "A_BREAK5", "label": "close < prior 5d low"},
    {"id": "A_BREAK10", "label": "close < prior 10d low"},
    {"id": "A_VOL1P5", "label": "volume > 1.5× MA20"},
    {"id": "A_VOL2", "label": "volume > 2× MA20"},
    {"id": "A_ATR_UP", "label": "ATR14 rising vs 5d ago"},
    {"id": "A_MACD_NEG", "label": "MACD_HIST_NEG"},
    {"id": "A_MACD_FLIP", "label": "MACD hist flip to neg"},
    {"id": "A_BB_UPPER", "label": "BB_UPPER"},
    {"id": "A_MFI80", "label": "MFI14_GT80"},
    {"id": "A_RSI6_GT80", "label": "RSI6_GT80 (live sell-fire same day)"},
    {"id": "A_UP1", "label": "today ret > 0 (NEG expect)"},
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _build_attr_panels(
    *,
    highs: dict,
    lows: dict,
    closes_adj: pd.DataFrame,
    raw_close: pd.DataFrame,
    raw_high: pd.DataFrame,
    raw_low: pd.DataFrame,
    raw_vol: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    fire = highs[SELL_HIGH_ID].fillna(False).astype(bool)
    return {
        "A_PERSIST2": persist_ok(fire, 2),
        "A_PERSIST3": persist_ok(fire, 3),
        "A_DN1": down_days_ok(closes_adj, 1),
        "A_DN2": down_days_ok(closes_adj, 2),
        "A_BREAK5": breakdown_ok(raw_close, raw_low, 5),
        "A_BREAK10": breakdown_ok(raw_close, raw_low, 10),
        "A_VOL1P5": volume_spike_ok(raw_vol, ma=20, mult=1.5),
        "A_VOL2": volume_spike_ok(raw_vol, ma=20, mult=2.0),
        "A_ATR_UP": atr_expand_ok(raw_high, raw_low, raw_close, lookback=5),
        "A_MACD_NEG": lows["MACD_HIST_NEG"].fillna(False).astype(bool),
        "A_MACD_FLIP": macd_flip_neg_ok(raw_close),
        "A_BB_UPPER": highs["BB_UPPER"].fillna(False).astype(bool),
        "A_MFI80": highs["MFI14_GT80"].fillna(False).astype(bool),
        "A_RSI6_GT80": fire,
        "A_UP1": (closes_adj.pct_change(1) > 0.0).fillna(False),
    }


def _rank_flags(stat: dict[str, Any]) -> dict[str, bool]:
    lift = stat.get("wr_lift_pp")
    n = int(stat.get("n") or 0)
    cov = float(stat.get("coverage") or 0.0)
    cov_ok = SIGNAL_COV_LO <= cov <= SIGNAL_COV_HI
    signal = (
        lift is not None
        and float(lift) >= SIGNAL_LIFT_PP
        and n >= SIGNAL_N_MIN
        and cov_ok
    )
    weak = (
        (not signal)
        and lift is not None
        and float(lift) >= WEAK_LIFT_PP
        and n >= WEAK_N_MIN
        and cov_ok
    )
    return {"signal": bool(signal), "weak": bool(weak), "cov_ok": bool(cov_ok)}


def _verdict(attr_rows: list[dict[str, Any]]) -> str:
    if any(r["flags"]["signal"] for r in attr_rows if not str(r["id"]).endswith("NEG") and r["id"] != "A_UP1"):
        return "DIAG_SIGNAL"
    if any(r["flags"]["weak"] for r in attr_rows if r["id"] != "A_UP1"):
        return "DIAG_WEAK"
    return "NO_SIGNAL"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert abs(SELL_AMP - 0.75) < 1e-12, f"SELL_a75 KEEP required, got amp={SELL_AMP}"

    market = load_market()
    dividends = load_dividends()
    prices, sleeve, _turn, regime = e16_features(market)
    _ = prices
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(market["date"].unique())))
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    closes = close_panel(market, cal, list(FIN))
    raw_close, raw_high, raw_low, raw_vol = raw_ohlcv_panels(market, cal, list(FIN))
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

    print("offense NAV for cool ...", flush=True)
    off_nav, _f0, _m0 = simulate_core(
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

    print(f"{BASE_ID} (no fin_sell_ok) ...", flush=True)
    # Binding: never pass fin_sell_ok — diagnostic role only.
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
        fin_buy_ok=base_buy_ok,
        fin_sell_scores=sell,
        e45_exposure=cool.astype(float),
        e22_version=E22_VERSION,
    )
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    # Binding enforced by omission: simulate_core called without fin_sell_ok.
    nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    fills.to_csv(OUT / f"fills_{BASE_ID}.csv", index=False)

    events = sell_fill_forward_rows(fills, closes, codes=set(FIN), horizon=WIN_H)
    events.to_csv(OUT / "sell_events_labeled_base.csv", index=False)
    n_ev = int(len(events))
    if n_ev < 1:
        raise RuntimeError("no evaluable FIN SELL events")
    base_wins = int(events["win"].sum())
    base_rate = 100.0 * base_wins / n_ev
    print(
        json.dumps(
            {
                "base_sell_n": n_ev,
                "base_sell_wr": round(base_rate, 4),
                "exact_t1_ok": bool(meta.get("exact_t1_ok")),
                "fin_sell_ok_applied": False,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    panels = _build_attr_panels(
        highs=highs,
        lows=lows,
        closes_adj=closes,
        raw_close=raw_close,
        raw_high=raw_high,
        raw_low=raw_low,
        raw_vol=raw_vol,
    )

    # Attach attribute columns to events for artifact.
    for aid, panel in panels.items():
        events[aid] = [
            lookup_attr(panel, r.fill_date, r.code) for r in events.itertuples(index=False)
        ]
    events.to_csv(OUT / "sell_events_with_attrs.csv", index=False)

    attr_rows: list[dict[str, Any]] = []
    for spec in ATTR_SPECS:
        aid = spec["id"]
        mask = events[aid].astype(bool)
        stat = conditional_wr(events, mask, base_rate=base_rate)
        flags = _rank_flags(stat)
        row = {
            "id": aid,
            "label": spec["label"],
            "stat": stat,
            "flags": flags,
            "neg_expect": aid == "A_UP1",
        }
        attr_rows.append(row)
        print(
            json.dumps(
                {
                    "attr": aid,
                    "n": stat["n"],
                    "wr": stat["win_rate"],
                    "lift_pp": stat["wr_lift_pp"],
                    "cov": stat["coverage"],
                    "signal": flags["signal"],
                    "weak": flags["weak"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    verdict = _verdict(attr_rows)
    generated = _utc()
    signals = [r for r in attr_rows if r["flags"]["signal"] and not r["neg_expect"]]
    weaks = [r for r in attr_rows if r["flags"]["weak"] and not r["neg_expect"]]
    signals.sort(key=lambda r: float(r["stat"]["wr_lift_pp"] or -9), reverse=True)
    weaks.sort(key=lambda r: float(r["stat"]["wr_lift_pp"] or -9), reverse=True)

    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "role": "diagnostic_label_only",
        "fin_sell_ok_applied": False,
        "live_wire": False,
        "soft_frozen_keep": True,
        "exact_t1_keep": True,
        "cool_keep": True,
        "sell_a75_keep": True,
        "sell_amp": SELL_AMP,
        "base_id": BASE_ID,
        "base_sell": {
            "n": n_ev,
            "wins": base_wins,
            "win_rate": round(base_rate, 4),
            "horizon": WIN_H,
            "win_def": "fwd_ret_lt_0",
        },
        "bars": {
            "signal_lift_pp": SIGNAL_LIFT_PP,
            "signal_n_min": SIGNAL_N_MIN,
            "signal_cov_lo": SIGNAL_COV_LO,
            "signal_cov_hi": SIGNAL_COV_HI,
            "weak_lift_pp": WEAK_LIFT_PP,
            "weak_n_min": WEAK_N_MIN,
        },
        "attributes": [
            {
                "id": r["id"],
                "label": r["label"],
                "stat": r["stat"],
                "flags": r["flags"],
                "neg_expect": r["neg_expect"],
            }
            for r in attr_rows
        ],
        "binding": [
            "Diagnostic role only — labels live SELL_a75 fills; does not pass fin_sell_ok",
            "Soft-Frozen / Exact T+1 / COOL / SELL_a75 KEEP",
            "DIAG_SIGNAL ≠ observe authorize ≠ live wire ≠ reopen hard sell gates",
            "Prior hard-gate tracks (quality / new-mech) remain STOP / MDD_BLOCK",
            "Sell loss-defer remains REJECTED",
        ],
    }

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · `fin_sell_ok` **not applied** · live wire **false**",
            "",
            f"Base `{BASE_ID}` = live Soft-Frozen + FUSE **SELL_a75** + COOL_c8 · Exact T+1.",
            f"Role: **diagnostic label only** on FIN SELL fills (H={WIN_H}, win = fwd ret&lt;0).",
            f"Unconditional sell WR = **{base_rate:.2f}%** (n={n_ev}).",
            "",
            f"Signal bar: lift≥**+{SIGNAL_LIFT_PP}pp** · n≥**{SIGNAL_N_MIN}** · coverage ∈[{SIGNAL_COV_LO},{SIGNAL_COV_HI}]%.",
            "",
            "## Attributes",
            "",
            "| ID | n | WR% | WR↑pp | cov% | SIGNAL | WEAK |",
            "|---|---:|---:|---:|---:|---|---|",
        ]
        + [
            "| {id} | {n} | {wr} | {lift} | {cov} | {sig} | {wk} |".format(
                id=r["id"],
                n=r["stat"]["n"],
                wr=r["stat"]["win_rate"],
                lift=r["stat"]["wr_lift_pp"],
                cov=r["stat"]["coverage"],
                sig=r["flags"]["signal"],
                wk=r["flags"]["weak"],
            )
            for r in attr_rows
        ]
        + [
            "",
            f"Verdict: **`{verdict}`**",
            "",
            f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`",
            "",
        ]
    )

    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OPS / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md",
        REP / f"{SCREEN_ID}.md",
        screen_md,
        kind="screen",
    )
    (REP / f"{SCREEN_ID}.json").write_text(
        json.dumps(
            {
                "canonical": f"research/ops/{SCREEN_ID}.json",
                "verdict": verdict,
                "generated_at_utc": generated,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · `fin_sell_ok` **OFF** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "Role: **diagnostic label only** — no portfolio challenger, no hard sell gate.",
        f"Base sell WR {base_rate:.2f}% (n={n_ev}, H={WIN_H}).",
        "",
    ]
    if signals:
        top = signals[0]
        dlines += [
            (
                f"Top SIGNAL: `{top['id']}` · WR↑ **{top['stat']['wr_lift_pp']}pp** · "
                f"n={top['stat']['n']} · cov={top['stat']['coverage']}% · "
                f"WR={top['stat']['win_rate']}%"
            ),
            "",
            "Follow-up allowed: paper **monitor/log** attribute on live fills — "
            "**not** `fin_sell_ok` gate, **not** observe promote from this pack alone.",
            "",
        ]
    elif weaks:
        top = weaks[0]
        dlines += [
            (
                f"Top WEAK: `{top['id']}` · WR↑ {top['stat']['wr_lift_pp']}pp · "
                f"n={top['stat']['n']} · cov={top['stat']['coverage']}%"
            ),
            "",
            "Insufficient for DIAG_SIGNAL — do not open gate/observe from this.",
            "",
        ]
    else:
        dlines += [
            "No attribute cleared SIGNAL or WEAK bars under coverage constraints.",
            "",
        ]

    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen / tip / Exact T+1 / **SELL_a75** KEEP",
        "2. **`fin_sell_ok` not applied** and not authorized by DIAG_*",
        "3. DIAG_SIGNAL ≠ observe ≠ live; separate charter needed to act",
        "4. Hard-gate sell tracks remain STOP / MDD_BLOCK (quality + new-mech)",
        "5. Sell loss-defer remains REJECTED",
        "",
        f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_GATE__NO_LIVE`",
        "",
    ]
    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_GATE__NO_LIVE",
        "status": verdict,
        "role": "diagnostic_label_only",
        "fin_sell_ok_applied": False,
        "live_wire": False,
        "soft_frozen_keep": True,
        "sell_a75_keep": True,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "top_signal": None if not signals else signals[0]["id"],
        "top_weak": None if not weaks else weaks[0]["id"],
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

    ch = (OPS / f"{CHARTER_ID}.md").read_text(encoding="utf-8")
    ch2 = ch.replace(
        "Status: **Stage A OPEN**",
        f"Status: **Stage A DONE — `{verdict}`**",
        1,
    )
    if ch2 != ch:
        (OPS / f"{CHARTER_ID}.md").write_text(ch2, encoding="utf-8")
    zh_path = OPS / f"{CHARTER_ID}.zh-TW.md"
    if zh_path.exists():
        zh = zh_path.read_text(encoding="utf-8")
        zh2 = zh.replace(
            "狀態：**Stage A OPEN**",
            f"狀態：**Stage A DONE — `{verdict}`**",
            1,
        )
        if zh2 != zh:
            zh_path.write_text(zh2, encoding="utf-8")

    charter_json = {
        "label": f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_GATE__NO_LIVE",
        "status": "DONE",
        "verdict": verdict,
        "date": "2026-09-28",
        "role": "diagnostic_label_only",
        "fin_sell_ok_applied": False,
        "live_wire": False,
        "sell_a75_keep": True,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "script": "scripts/fin_sell_diag_role_stagea.py",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "decision": f"research/ops/{DECISION_ID}.md",
    }
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(charter_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_attrs": len(attr_rows),
                "n_signal": len(signals),
                "n_weak": len(weaks),
                "fin_sell_ok_applied": False,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
