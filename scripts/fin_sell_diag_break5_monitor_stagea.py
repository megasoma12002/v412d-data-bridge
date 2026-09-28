#!/usr/bin/env python3
"""FIN sell **BREAK5 diagnostic monitor/log** Stage A — Track C.

Charter: research/ops/FIN_SELL_DIAG_BREAK5_MONITOR_STAGEA_CHARTER.md

Follow-up to FIN_SELL_DIAG_ROLE_STAGEA (A_BREAK5 = DIAG_SIGNAL). Simulates one
CTRL_BASE (Soft-Frozen + FUSE SELL_a75 + COOL), labels each FIN SELL fill with
A_BREAK5 via ``breakdown_ok``, and emits a monitor CSV. Diagnostic LOG only —
never passes ``fin_sell_ok``, never changes NAV, never authorizes observe/live.
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
    breakdown_ok,
    close_panel,
    conditional_wr,
    lookup_attr,
    raw_ohlcv_panels,
    sell_fill_forward_rows,
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
REPRO = ROOT / "repro" / "fin-sell-diag-break5-monitor-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SELL_DIAG_BREAK5_MONITOR_STAGEA_CHARTER"
SCREEN_ID = "FIN_SELL_DIAG_BREAK5_MONITOR_STAGEA_SCREEN"
DECISION_ID = "FIN_SELL_DIAG_BREAK5_MONITOR_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_BASE"
ATTR_ID = "A_BREAK5"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

WIN_H = 21
# Monitor bars (diagnostic — no portfolio change).
READY_LIFT_PP = 3.0
READY_N_MIN = 80
COV_LO = 5.0
COV_HI = 70.0
WEAK_LIFT_PP = 1.5
WEAK_N_MIN = 50

PARENT_CHARTER = "research/ops/FIN_SELL_DIAG_ROLE_STAGEA_CHARTER.md"
PARENT_DECISION = "research/ops/FIN_SELL_DIAG_ROLE_STAGEA_DECISION_PACK.md"


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


def _rank_flags(stat: dict[str, Any]) -> dict[str, bool]:
    lift = stat.get("wr_lift_pp")
    n = int(stat.get("n") or 0)
    cov = float(stat.get("coverage") or 0.0)
    cov_ok = COV_LO <= cov <= COV_HI
    ready = (
        lift is not None
        and float(lift) >= READY_LIFT_PP
        and n >= READY_N_MIN
        and cov_ok
    )
    weak = (
        (not ready)
        and lift is not None
        and float(lift) >= WEAK_LIFT_PP
        and n >= WEAK_N_MIN
        and cov_ok
    )
    return {"ready": bool(ready), "weak": bool(weak), "cov_ok": bool(cov_ok)}


def _verdict(stat: dict[str, Any], flags: dict[str, bool]) -> str:
    if flags["ready"]:
        return "MONITOR_READY"
    if flags["weak"]:
        return "MONITOR_WEAK"
    lift = stat.get("wr_lift_pp")
    if lift is not None and float(lift) < 0.0:
        return "DRIFT"
    if not flags["cov_ok"]:
        return "DRIFT"
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
    raw_close, _raw_high, raw_low, _raw_vol = raw_ohlcv_panels(market, cal, list(FIN))
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

    print(f"{BASE_ID} (no fin_sell_ok; BREAK5 monitor) ...", flush=True)
    # Binding: never pass fin_sell_ok — diagnostic monitor/log only.
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
    nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    fills.to_csv(OUT / f"fills_{BASE_ID}.csv", index=False)

    events = sell_fill_forward_rows(fills, closes, codes=set(FIN), horizon=WIN_H)
    n_ev = int(len(events))
    if n_ev < 1:
        raise RuntimeError("no evaluable FIN SELL events")
    base_wins = int(events["win"].sum())
    base_rate = 100.0 * base_wins / n_ev

    break5_panel = breakdown_ok(raw_close, raw_low, 5)
    events["break5"] = [
        lookup_attr(break5_panel, r.fill_date, r.code) for r in events.itertuples(index=False)
    ]

    # Monitor CSV: date, code, break5, fwd_ret_21, win
    monitor = pd.DataFrame(
        {
            "date": events["fill_date"],
            "code": events["code"],
            "break5": events["break5"].astype(bool),
            "fwd_ret_21": events["fwd_ret"].astype(float),
            "win": events["win"].astype(bool),
        }
    )
    monitor_path = OUT / "sell_break5_monitor.csv"
    monitor.to_csv(monitor_path, index=False)

    mask = events["break5"].astype(bool)
    stat = conditional_wr(events, mask, base_rate=base_rate)
    flags = _rank_flags(stat)
    verdict = _verdict(stat, flags)
    generated = _utc()

    print(
        json.dumps(
            {
                "base_sell_n": n_ev,
                "base_sell_wr": round(base_rate, 4),
                "break5": {
                    "n": stat["n"],
                    "wr": stat["win_rate"],
                    "lift_pp": stat["wr_lift_pp"],
                    "cov": stat["coverage"],
                    "ready": flags["ready"],
                    "weak": flags["weak"],
                },
                "verdict": verdict,
                "exact_t1_ok": bool(meta.get("exact_t1_ok")),
                "fin_sell_ok_applied": False,
                "monitor_csv": str(monitor_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "parent_charter": PARENT_CHARTER,
        "parent_decision": PARENT_DECISION,
        "track": "C",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "role": "diagnostic_monitor_log_only",
        "attr_id": ATTR_ID,
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
        "break5": {
            "stat": stat,
            "flags": flags,
        },
        "bars": {
            "ready_lift_pp": READY_LIFT_PP,
            "ready_n_min": READY_N_MIN,
            "cov_lo": COV_LO,
            "cov_hi": COV_HI,
            "weak_lift_pp": WEAK_LIFT_PP,
            "weak_n_min": WEAK_N_MIN,
        },
        "monitor_csv": str(monitor_path.relative_to(ROOT)),
        "binding": [
            "Diagnostic monitor/log only — labels live SELL_a75 fills with A_BREAK5; does not pass fin_sell_ok",
            "Soft-Frozen / Exact T+1 / COOL / SELL_a75 KEEP",
            "MONITOR_READY ≠ observe authorize ≠ live wire ≠ reopen hard sell gates",
            "Prior hard-gate tracks (quality / new-mech) remain STOP / MDD_BLOCK",
            "Sell loss-defer remains REJECTED",
        ],
    }

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            (
                f"Status: **{verdict}** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · "
                f"`fin_sell_ok` **not applied** · live wire **false**"
            ),
            "",
            f"Track **C** · Parent: `{PARENT_CHARTER}` (A_BREAK5 = DIAG_SIGNAL).",
            f"Base `{BASE_ID}` = live Soft-Frozen + FUSE **SELL_a75** + COOL_c8 · Exact T+1.",
            f"Role: **diagnostic monitor/log** of `{ATTR_ID}` on FIN SELL fills "
            f"(H={WIN_H}, win = fwd ret&lt;0).",
            f"Unconditional sell WR = **{base_rate:.2f}%** (n={n_ev}).",
            "",
            (
                f"Ready bar: lift≥**+{READY_LIFT_PP}pp** · n≥**{READY_N_MIN}** · "
                f"coverage ∈[{COV_LO},{COV_HI}]%."
            ),
            (
                f"Weak bar: lift≥**+{WEAK_LIFT_PP}pp** · n≥**{WEAK_N_MIN}** · "
                f"same coverage · else DRIFT/NO_SIGNAL."
            ),
            "",
            "## A_BREAK5 vs unconditional",
            "",
            "| Attr | n | WR% | WR↑pp | cov% | READY | WEAK |",
            "|---|---:|---:|---:|---:|---|---|",
            (
                f"| {ATTR_ID} | {stat['n']} | {stat['win_rate']} | "
                f"{stat['wr_lift_pp']} | {stat['coverage']} | "
                f"{flags['ready']} | {flags['weak']} |"
            ),
            "",
            f"Monitor CSV: `{monitor_path.relative_to(ROOT)}` "
            "(columns: date, code, break5, fwd_ret_21, win).",
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
        (
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · "
            f"`fin_sell_ok` **OFF** · live wire **false**"
        ),
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        f"Parent: `{PARENT_DECISION}`",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "Role: **diagnostic monitor/log** — no portfolio challenger, no hard sell gate.",
        (
            f"`{ATTR_ID}` WR↑ {stat['wr_lift_pp']}pp · n={stat['n']} · "
            f"cov={stat['coverage']}% · base WR {base_rate:.2f}% (n={n_ev}, H={WIN_H})."
        ),
        "",
        f"Monitor CSV columns: `date, code, break5, fwd_ret_21, win` → "
        f"`{monitor_path.relative_to(ROOT)}`.",
        "",
    ]
    if verdict == "MONITOR_READY":
        dlines += [
            "MONITOR_READY: BREAK5 conditional WR clears ready bar — continue paper log only.",
            "**Not** authorized to gate `fin_sell_ok`, observe, or live from this pack.",
            "",
        ]
    elif verdict == "MONITOR_WEAK":
        dlines += [
            "MONITOR_WEAK: lift present but below ready bar — keep logging; do not gate.",
            "",
        ]
    elif verdict == "DRIFT":
        dlines += [
            "DRIFT: BREAK5 lift negative or coverage outside band vs parent DIAG_SIGNAL.",
            "Do not open gate/observe; re-check parent attribution if needed.",
            "",
        ]
    else:
        dlines += [
            "NO_SIGNAL: BREAK5 did not clear READY/WEAK under coverage constraints.",
            "",
        ]

    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen / tip / Exact T+1 / **SELL_a75** KEEP",
        "2. **`fin_sell_ok` not applied** and not authorized by MONITOR_*",
        "3. MONITOR_READY ≠ observe ≠ live; separate charter needed to act",
        "4. Hard-gate sell tracks remain STOP / MDD_BLOCK (quality + new-mech)",
        "5. Sell loss-defer remains REJECTED",
        "",
        f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_GATE__NO_LIVE`",
        "",
    ]
    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_GATE__NO_LIVE",
        "status": verdict,
        "role": "diagnostic_monitor_log_only",
        "attr_id": ATTR_ID,
        "track": "C",
        "fin_sell_ok_applied": False,
        "live_wire": False,
        "soft_frozen_keep": True,
        "sell_a75_keep": True,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "parent_decision": PARENT_DECISION,
        "break5_stat": stat,
        "monitor_csv": str(monitor_path.relative_to(ROOT)),
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

    charter_json = {
        "label": f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_GATE__NO_LIVE",
        "status": "DONE",
        "verdict": verdict,
        "date": "2026-09-28",
        "track": "C",
        "role": "diagnostic_monitor_log_only",
        "attr_id": ATTR_ID,
        "fin_sell_ok_applied": False,
        "live_wire": False,
        "sell_a75_keep": True,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "script": "scripts/fin_sell_diag_break5_monitor_stagea.py",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "decision": f"research/ops/{DECISION_ID}.md",
        "parent_charter": PARENT_CHARTER,
        "monitor_csv": str(monitor_path.relative_to(ROOT)),
    }
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(charter_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "attr": ATTR_ID,
                "n": stat["n"],
                "lift_pp": stat["wr_lift_pp"],
                "fin_sell_ok_applied": False,
                "monitor_csv": str(monitor_path.relative_to(ROOT)),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
