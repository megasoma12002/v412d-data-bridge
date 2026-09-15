#!/usr/bin/env python3
"""E45 defend→handoff dual-paper ledgers — thin wrapper (OPERATING OBSERVE).

Two-pass via ``post_base``: BASE live-stack NAV → DH exposure → CHAL.
Soft-Frozen KEEP · paper shadow twin (live DH may already be wired).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import e16_soft_frozen_base as soft
import e45_defend_handoff_stagea_screen as stagea
from e45_defend_handoff_helpers import (
    BASE_ID,
    CHAL_ID,
    DD_THRESHOLD,
    HUMAN_OPEN,
    SHRINK,
    STAGE_A_VERDICT,
    STATUS,
    STITCH_AUTHORIZED,
    VOL_Z_THRESHOLD,
)
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from e50_early_stack_combined_nav import FIN, e16_features
from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    LedgerResult,
    PostBaseCtx,
    PreparedBooks,
    cli_main,
    live_kd_sim_kwargs,
    preflight_live_kd,
    write_json_md_pair,
)
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


def _preflight() -> None:
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    preflight_live_kd(LIVE_KD)()
    if STITCH_AUTHORIZED:
        raise SystemExit("Refuse: stitch flag must stay false")


def prepare(market: pd.DataFrame, dividends: pd.DataFrame) -> PreparedBooks:
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
    base_kw = live_kd_sim_kwargs(scores=kd_scores, buy_ok=kd_ok, e45_exposure=None)
    # CHAL kwargs filled in post_base after BASE NAV → exposure.
    return PreparedBooks(
        base_target=target,
        base_regime=regime,
        chal_target=target,
        chal_regime=regime,
        base_kwargs=base_kw,
        chal_kwargs=dict(base_kw),
        context={"kd_scores": kd_scores, "kd_ok": kd_ok},
    )


def post_base(ctx: PostBaseCtx) -> None:
    base_nav_s = stagea._nav_series(ctx.nav_base)
    feat = stagea._risk_features(ctx.market, base_nav_s)
    dates = pd.DatetimeIndex(base_nav_s.index)
    exposure = stagea._build_exposure(dates, feat, DD_THRESHOLD, VOL_Z_THRESHOLD)
    frac_def = float((exposure < 0.999).mean())
    ctx.prepared.chal_kwargs = live_kd_sim_kwargs(
        scores=ctx.prepared.context["kd_scores"],
        buy_ok=ctx.prepared.context["kd_ok"],
        e45_exposure=exposure.astype(float),
    )
    ctx.prepared.extras["dh_dd06_vz1p0_exposure.csv"] = exposure.rename("e45_exposure")
    ctx.prepared.context["frac_days_defense"] = frac_def
    ctx.prepared.context["exposure"] = exposure


def report(result: LedgerResult) -> None:
    import json
    from datetime import datetime, timezone

    frac_def = float(result.prepared.context.get("frac_days_defense") or 0.0)
    win_base = pack_windows(result.nav_base)
    win_chal = pack_windows(result.nav_chal)
    held = held_score(win_base["heldout_2019_plus"], win_chal["heldout_2019_plus"])
    tip = tip_windows(result.nav_base, result.nav_chal)
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
        "n_fills_base": int(len(result.fills_base)),
        "n_fills_chal": int(len(result.fills_chal)),
        "non_actions": [
            "No Soft-Frozen / Soft / Sleeve / FUSE / E45 live wire",
            "No E45 stitch reopen / no undo DROP_E45_A05",
            "Soft∥Sleeve independent observes KEEP",
            "Cutover BLOCKED until dedicated ACCEPT",
        ],
    }

    body_lines = [
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
    body_lines += [f"- {x}" for x in payload["non_actions"]]
    body_lines += ["", f"Repro: `repro/e45-defend-handoff-dual-paper-observe/`", ""]

    write_json_md_pair(
        out_dir=OUT,
        report_stem="E45_DEFEND_HANDOFF_DUAL_PAPER_OBSERVE_OPERATING",
        payload=payload,
        md_lines=body_lines,
        mirror_dirs=(OPS,),
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "outputs" / "dual_paper_summary.json").write_text(text, encoding="utf-8")
    (OPS / "E45_DEFEND_HANDOFF_DUAL_PAPER_OBSERVE.json").write_text(text, encoding="utf-8")


SPEC = DualPaperLedgerSpec(
    label="E45_DEFEND_HANDOFF_DUAL_PAPER_OBSERVE_OPERATING",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    prepare=prepare,
    post_base=post_base,
    base_nav_name="live_stack_daily_nav.csv",
    chal_nav_name="dh_dd06_vz1p0_daily_nav.csv",
    write_fills=False,
    base_targets_name=None,
    soft_frozen_clip=(0.6, 0.9),
    preflight=_preflight,
    report_fn=report,
    status=STATUS,
    capital=CAPITAL,
    lot_size=LOT,
)


if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
