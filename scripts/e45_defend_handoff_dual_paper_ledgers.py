#!/usr/bin/env python3
"""E45 defend→handoff dual-paper ledgers — OPERATING OBSERVE (paper only).

Books (500M / board-lot 1000):
  BASE  LIVE_STACK     Soft-Frozen + KD_OPT + TEL_EQUAL (e45_exposure=None)
  CHAL  DH_dd06_vz1p0  same + defend-window SHRINK e45_exposure (Stage A winner)

Human OPEN: OPEN E45 defend-handoff observe: DH_dd06_vz1p0
Soft-Frozen KEEP · live stack KEEP · Soft/Sleeve/FUSE observes KEEP · no stitch
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import e16_soft_frozen_base as soft
import e45_defend_handoff_stagea_screen as stagea
from e45_defend_handoff_helpers import (
    BASE_ID,
    CHAL_ID,
    DD_THRESHOLD,
    HUMAN_OPEN,
    LIVE_WIRE,
    SHRINK,
    STAGE_A_VERDICT,
    STATUS,
    STITCH_AUTHORIZED,
    VOL_Z_THRESHOLD,
)
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features
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
OUT = ROOT / "repro/e45-defend-handoff-dual-paper-observe"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT


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


def pack_windows(nav: pd.DataFrame) -> dict:
    out = {}
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


def tip_windows(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {
                "mdd_improve_pp": None,
                "cagr_giveback_pp": None,
                "gate": "INSUFFICIENT",
            }
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


def main() -> int:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    import e21_forward_pipeline as e21

    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse DH observe while LIVE_E45_STITCH is True (no stitch)")
    if STITCH_AUTHORIZED or LIVE_WIRE:
        raise SystemExit("Refuse: stitch/live flags must stay false")

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
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

    print(f"{BASE_ID} ...", flush=True)
    base = stagea._run_book(
        market,
        target,
        regime,
        dividends,
        scores=kd_scores,
        buy_ok=kd_ok,
        exposure=None,
    )
    base_nav_s = stagea._nav_series(base["nav"])
    feat = stagea._risk_features(market, base_nav_s)
    dates = pd.DatetimeIndex(base_nav_s.index)
    exposure = stagea._build_exposure(dates, feat, DD_THRESHOLD, VOL_Z_THRESHOLD)
    frac_def = float((exposure < 0.999).mean())

    print(f"{CHAL_ID} (dd={DD_THRESHOLD}, vz={VOL_Z_THRESHOLD}, shrink={SHRINK}) ...", flush=True)
    chal = stagea._run_book(
        market,
        target,
        regime,
        dividends,
        scores=kd_scores,
        buy_ok=kd_ok,
        exposure=exposure,
    )

    base["nav"].to_csv(OUT / "outputs" / "live_stack_daily_nav.csv", index=False)
    chal["nav"].to_csv(OUT / "outputs" / "dh_dd06_vz1p0_daily_nav.csv", index=False)
    exposure.rename("e45_exposure").to_frame().to_csv(
        OUT / "outputs" / "dh_dd06_vz1p0_exposure.csv"
    )
    joined = (
        base["nav"][["date", "nav"]]
        .rename(columns={"nav": "nav_base"})
        .merge(
            chal["nav"][["date", "nav"]].rename(columns={"nav": "nav_chal"}),
            on="date",
            how="inner",
        )
    )
    joined["rel_chal_vs_base"] = joined["nav_chal"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    win_base = pack_windows(base["nav"])
    win_chal = pack_windows(chal["nav"])
    held = held_score(win_base["heldout_2019_plus"], win_chal["heldout_2019_plus"])
    tip = tip_windows(base["nav"], chal["nav"])
    sealed = held_score(
        win_base.get("sealed_2023_plus") or {},
        win_chal.get("sealed_2023_plus") or {},
    )

    payload = {
        "schema_version": "e45_defend_handoff_dual_paper_observe_v1",
        "label": "E45_DEFEND_HANDOFF_DUAL_PAPER_OBSERVE_OPERATING",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": STATUS,
        "human_open": HUMAN_OPEN,
        "live_wire": False,
        "stitch_authorized": False,
        "stitch_reopen": False,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "stage_a_verdict": STAGE_A_VERDICT,
        "recipe": {
            "dd_threshold": DD_THRESHOLD,
            "vol_z_threshold": VOL_Z_THRESHOLD,
            "shrink": SHRINK,
            "frac_days_defense": round(frac_def, 6),
            "financial_alloc": FIN_PRE_EXDIV_KD,
            "telecom_alloc": TEL_EQUAL,
            "capital": CAPITAL,
            "lot_size": LOT,
        },
        "soft_frozen_fin_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "base_windows": win_base,
        "chal_windows": win_chal,
        "heldout_delta": held,
        "sealed_delta": sealed,
        "tip": tip,
        "n_fills_base": base["n_fills"],
        "n_fills_chal": chal["n_fills"],
        "non_actions": [
            "No Soft-Frozen / Soft / Sleeve / FUSE / E45 live wire",
            "No E45 stitch reopen / no undo DROP_E45_A05",
            "Soft∥Sleeve independent observes KEEP",
            "Cutover BLOCKED until dedicated ACCEPT",
        ],
    }
    (OUT / "outputs" / "dual_paper_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OPS / "E45_DEFEND_HANDOFF_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# E45 defend→handoff dual-paper observe — OPERATING",
        "",
        f"- human_open: `{HUMAN_OPEN}`",
        f"- status: **{STATUS}** | live_wire: false | stitch: FORBIDDEN",
        f"- base: `{BASE_ID}` ∥ challenger: `{CHAL_ID}`",
        f"- Stage A: `{STAGE_A_VERDICT}` · frac_defense={frac_def:.3f}",
        f"- held-out: MDD↑ {held.get('mdd_improve_pp')} pp · CAGR giveback {held.get('cagr_giveback_pp')} pp · score {held.get('score')}",
        f"- tip ytd MDD↑ {tip.get('ytd', {}).get('mdd_improve_pp')} · tip 1y MDD↑ {tip.get('trailing_1y', {}).get('mdd_improve_pp')}",
        "",
        "## Non-actions",
        "",
    ]
    lines += [f"- {x}" for x in payload["non_actions"]]
    lines += ["", f"Repro: `repro/e45-defend-handoff-dual-paper-observe/`", ""]
    text = "\n".join(lines)
    (OUT / "reports" / "E45_DEFEND_HANDOFF_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(
        text, encoding="utf-8"
    )
    (OPS / "E45_DEFEND_HANDOFF_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(
        text, encoding="utf-8"
    )

    print(
        f"done status={STATUS} held_score={held.get('score')} frac_def={frac_def:.3f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
