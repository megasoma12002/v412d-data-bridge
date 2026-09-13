#!/usr/bin/env python3
"""Kelly exposure Stage A paper screen (charter KELLY_EXPOSURE_STAGEA).

Finite grid: EDGE_LIVE_ROLL x W in {63,126,252} x kappa in {0.25,0.50} (<=6 primary)
+ EDGE_0050_ROLL sensitivity (report-only; does not drive promote).
Actuator: kelly_exposure via e45_exposure on paper LIVE_STACK twin
(Soft-Frozen + KD_OPT + TEL_EQUAL). Exact T+1. No live wire.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
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
REPRO = ROOT / "repro" / "kelly-exposure-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "KELLY_EXPOSURE_STAGEA_CHARTER"
SCREEN_ID = "KELLY_EXPOSURE_STAGEA_SCREEN"
ARTIFACT = "research/ops/KELLY_EXPOSURE_STAGEA_SCREEN.md"

W_GRID = (63, 126, 252)
KAPPA_GRID = (0.25, 0.50)
F_LO = 0.50
F_HI = 1.00
EPS_VAR = 1e-12
HELDOUT = "heldout_2019_plus"
REPORT_WINDOWS = ("full", "heldout_2019_plus", "sealed_2023_plus")
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
BOUND_FRAC_UNSTABLE = 0.80


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _nav_series(nav: pd.DataFrame) -> pd.Series:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    return d.drop_duplicates("date").set_index("date")["nav"].astype(float).sort_index()


def _simple_returns(nav_s: pd.Series) -> pd.Series:
    return nav_s.astype(float).pct_change()


def _0050_returns(market: pd.DataFrame) -> pd.Series:
    m = market[market["code"] == "0050"].copy()
    m["date"] = pd.to_datetime(m["date"])
    px = m.drop_duplicates("date").set_index("date").sort_index()
    col = "adj_close" if "adj_close" in px.columns else "close"
    return px[col].astype(float).pct_change()


def build_kelly_exposure(
    returns: pd.Series,
    *,
    W: int,
    kappa: float,
) -> tuple[pd.Series, dict[str, Any]]:
    """Causal f*=mu/sigma^2; e=clip(kappa*f*, F_LO, F_HI). Warm-up/bad -> F_LO."""
    r = returns.astype(float)
    mu = r.rolling(int(W), min_periods=int(W)).mean()
    var = r.rolling(int(W), min_periods=int(W)).var(ddof=1)
    f_star = pd.Series(0.0, index=r.index, dtype=float)
    ok = mu.notna() & var.notna() & (var >= EPS_VAR) & (mu > 0.0)
    f_star.loc[ok] = (mu.loc[ok] / var.loc[ok]).astype(float)
    raw = (float(kappa) * f_star).astype(float)
    e = raw.clip(lower=F_LO, upper=F_HI)
    e = e.where(mu.notna() & var.notna(), F_LO)
    at_lo = e <= (F_LO + 1e-12)
    at_hi = e >= (F_HI - 1e-12)
    raw_finite = raw.replace([np.inf, -np.inf], np.nan).dropna()
    diag = {
        "mean_e": round(float(e.mean()), 6),
        "p50_e": round(float(e.median()), 6),
        "p10_e": round(float(e.quantile(0.10)), 6),
        "frac_at_lo": round(float(at_lo.mean()), 6),
        "frac_at_hi": round(float(at_hi.mean()), 6),
        "frac_at_bound": round(float((at_lo | at_hi).mean()), 6),
        "mean_raw_before_clip": round(
            float(raw_finite.mean()) if len(raw_finite) else 0.0, 6
        ),
        "mean_f_star": round(float(f_star.mean()), 6),
        "frac_f_star_pos": round(float((f_star > 0).mean()), 6),
    }
    return e.astype(float), diag


def _run_book(
    market: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    dividends: pd.DataFrame,
    *,
    scores: pd.DataFrame,
    buy_ok: pd.DataFrame,
    exposure: pd.Series | None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
    )
    if exposure is not None:
        kwargs["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kwargs)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return {"nav": nav, "n_fills": int(len(fills)), "meta": meta}


def _pack_windows(nav: pd.DataFrame) -> dict[str, Any]:
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


def _tip_gate(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
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
            out[wname] = {
                "cagr_giveback_pp": None,
                "mdd_improve_pp": None,
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
        gate = "PASS"
        if gb is not None and float(gb) > TRAIL_PAUSE_PP:
            gate = "PAUSE_REVIEW"
        elif gb is not None and float(gb) > TRAIL_ALERT_PP:
            gate = "ALERT"
        out[wname] = {
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "gate": gate,
        }
    return out


def _held_score(
    base_w: dict[str, Any], chal_w: dict[str, Any], key: str
) -> dict[str, Any] | None:
    b, c = base_w.get(key), chal_w.get(key)
    if not b or not c or b.get("cagr") is None or c.get("cagr") is None:
        return None
    gb = cagr_delta_pp(b.get("cagr"), c.get("cagr"), missing_as_zero=True)
    mdd_pp = mdd_delta_pp(b.get("max_drawdown"), c.get("max_drawdown"))
    giveback = abs(float(gb)) if gb is not None else 9.0
    return {
        "mdd_improve_pp": round(float(mdd_pp), 4),
        "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
        "score": round(float(mdd_pp) - 0.5 * giveback, 6),
        "base_cagr": b["cagr"],
        "chal_cagr": c["cagr"],
        "base_mdd": b["max_drawdown"],
        "chal_mdd": c["max_drawdown"],
    }


def _row_class(
    tip: dict[str, Any], held: dict[str, Any] | None, diag: dict[str, Any]
) -> str:
    tip_clean = (
        tip.get("ytd", {}).get("gate") == "PASS"
        and tip.get("trailing_1y", {}).get("gate") == "PASS"
    )
    tip_mdd_ok = all(
        (tip.get(w) or {}).get("mdd_improve_pp") is not None
        and float((tip.get(w) or {}).get("mdd_improve_pp")) >= 0.0
        for w in ("ytd", "trailing_1y")
    )
    score = None if held is None else held.get("score")
    if tip_clean and tip_mdd_ok and score is not None and float(score) > 0.0:
        return "KELLY_PROMOTE_SHAPED"
    if tip_clean:
        return "COEXIST_NO_LIFT"
    if float(diag.get("frac_at_bound") or 0.0) > BOUND_FRAC_UNSTABLE:
        return "ESTIMATE_UNSTABLE"
    return "NO_LIFT"


def _overall_verdict(
    primary_rows: list[dict[str, Any]],
) -> tuple[str, str | None, dict[str, Any]]:
    shaped = [r for r in primary_rows if r.get("row_class") == "KELLY_PROMOTE_SHAPED"]
    coexist = [r for r in primary_rows if r.get("row_class") == "COEXIST_NO_LIFT"]
    unstable = [r for r in primary_rows if r.get("row_class") == "ESTIMATE_UNSTABLE"]
    if shaped:
        best = max(
            shaped,
            key=lambda x: float((x.get("heldout_delta") or {}).get("score") or -9.0),
        )
        return (
            "KELLY_PROMOTE_SHAPED",
            best["variant_id"],
            {
                "held_score": (best.get("heldout_delta") or {}).get("score"),
                "n_shaped": len(shaped),
            },
        )
    if coexist:
        best = max(
            coexist,
            key=lambda x: float((x.get("heldout_delta") or {}).get("score") or -9.0),
        )
        return (
            "COEXIST_NO_LIFT",
            best["variant_id"],
            {
                "held_score": (best.get("heldout_delta") or {}).get("score"),
                "n_coexist": len(coexist),
            },
        )
    if unstable and not any(r.get("tip_clean") for r in primary_rows):
        return (
            "ESTIMATE_UNSTABLE",
            None,
            {"n_unstable": len(unstable), "n_rows": len(primary_rows)},
        )
    return "NO_LIFT", None, {"n_rows": len(primary_rows)}


def _eval_variant(
    *,
    variant_id: str,
    edge_id: str,
    W: int,
    kappa: float,
    returns: pd.Series,
    market: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    dividends: pd.DataFrame,
    scores: pd.DataFrame,
    buy_ok: pd.DataFrame,
    base_nav: pd.DataFrame,
    base_windows: dict[str, Any],
    promote_eligible: bool,
) -> dict[str, Any]:
    exp, diag = build_kelly_exposure(returns, W=W, kappa=kappa)
    idx = pd.to_datetime(target.index)
    exp = exp.reindex(idx).ffill().fillna(F_LO)
    chal = _run_book(
        market, target, regime, dividends, scores=scores, buy_ok=buy_ok, exposure=exp
    )
    chal["nav"].to_csv(OUT / f"nav_{variant_id}.csv", index=False)
    exp.rename("kelly_exposure").to_frame().to_csv(OUT / f"exposure_{variant_id}.csv")
    chal_windows = _pack_windows(chal["nav"])
    tip = _tip_gate(base_nav, chal["nav"])
    held = _held_score(base_windows, chal_windows, HELDOUT)
    sealed = _held_score(base_windows, chal_windows, "sealed_2023_plus")
    tip_clean = (
        tip.get("ytd", {}).get("gate") == "PASS"
        and tip.get("trailing_1y", {}).get("gate") == "PASS"
    )
    row_class = _row_class(tip, held, diag)
    return {
        "variant_id": variant_id,
        "edge_id": edge_id,
        "W": int(W),
        "kappa": float(kappa),
        "promote_eligible": bool(promote_eligible),
        "exact_t1_ok": bool(chal["meta"].get("exact_t1_ok")),
        "n_fills": chal["n_fills"],
        "mean_e45_exposure": chal["meta"].get("mean_e45_exposure"),
        "exposure_diag": diag,
        "windows": {k: chal_windows.get(k) for k in REPORT_WINDOWS if k in chal_windows},
        "heldout_delta": held,
        "sealed_delta": sealed,
        "tip": tip,
        "tip_clean": tip_clean,
        "row_class": row_class,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    import e21_forward_pipeline as e21

    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(
                f"LIVE_KD[{k}]={LIVE_KD[k]!r} != e21.KD_OPT[{k}]={e21.KD_OPT[k]!r}"
            )
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse Stage A while LIVE_E45_STITCH is True")

    print("[1/4] loading + baseline LIVE_STACK twin ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())

    scores = build_kd_season_tilt_scores(
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

    base = _run_book(
        market, target, regime, dividends, scores=scores, buy_ok=buy_ok, exposure=None
    )
    base["nav"].to_csv(OUT / "nav_BASE_LIVE_STACK.csv", index=False)
    base_windows = _pack_windows(base["nav"])
    base_nav_s = _nav_series(base["nav"])
    r_live = _simple_returns(base_nav_s)
    r_0050 = _0050_returns(market).reindex(base_nav_s.index)

    jobs = list(product(W_GRID, KAPPA_GRID))
    primary_rows: list[dict[str, Any]] = []
    sensitivity_rows: list[dict[str, Any]] = []

    print(f"[2/4] primary EDGE_LIVE_ROLL n={len(jobs)} ...", flush=True)
    for i, (W, kappa) in enumerate(jobs, 1):
        vid = f"KELLY_LIVE_W{W}_k{int(kappa * 100):02d}"
        print(f"  [{i}/{len(jobs)}] {vid}", flush=True)
        primary_rows.append(
            _eval_variant(
                variant_id=vid,
                edge_id="EDGE_LIVE_ROLL",
                W=W,
                kappa=kappa,
                returns=r_live,
                market=market,
                target=target,
                regime=regime,
                dividends=dividends,
                scores=scores,
                buy_ok=buy_ok,
                base_nav=base["nav"],
                base_windows=base_windows,
                promote_eligible=True,
            )
        )

    print(f"[3/4] sensitivity EDGE_0050_ROLL n={len(jobs)} ...", flush=True)
    for i, (W, kappa) in enumerate(jobs, 1):
        vid = f"KELLY_0050_W{W}_k{int(kappa * 100):02d}"
        print(f"  [{i}/{len(jobs)}] {vid}", flush=True)
        sensitivity_rows.append(
            _eval_variant(
                variant_id=vid,
                edge_id="EDGE_0050_ROLL",
                W=W,
                kappa=kappa,
                returns=r_0050,
                market=market,
                target=target,
                regime=regime,
                dividends=dividends,
                scores=scores,
                buy_ok=buy_ok,
                base_nav=base["nav"],
                base_windows=base_windows,
                promote_eligible=False,
            )
        )

    verdict, best_id, detail = _overall_verdict(primary_rows)
    best = next((r for r in primary_rows if r["variant_id"] == best_id), None)

    payload = {
        "schema_version": "kelly_exposure_stagea_screen_v1",
        "screen_id": SCREEN_ID,
        "charter_id": CHARTER_ID,
        "generated_at_utc": _utc(),
        "status": "DONE",
        "mode": "PAPER_ONLY",
        "live_wire": False,
        "observe_open": False,
        "gates": {
            "exact_t1_ok": True,
            "apply_e22": True,
            "apply_stock_div": True,
            "financial_alloc": FIN_PRE_EXDIV_KD,
            "telecom_alloc": TEL_EQUAL,
            "soft_frozen_fin_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
            "board_lot": int(BOARD_LOT),
            "initial_capital": float(DEFAULT_CAPITAL),
            "actuator": "kelly_exposure via e45_exposure",
            "f_lo": F_LO,
            "f_hi": F_HI,
            "kappa_grid": list(KAPPA_GRID),
            "W_grid": list(W_GRID),
            "full_kelly_forbidden": True,
            "trail_alert_pp": TRAIL_ALERT_PP,
            "trail_pause_pp": TRAIL_PAUSE_PP,
            "heldout_window": HELDOUT,
        },
        "base_windows": {k: base_windows.get(k) for k in REPORT_WINDOWS if k in base_windows},
        "grid": {
            "primary_edge": "EDGE_LIVE_ROLL",
            "sensitivity_edge": "EDGE_0050_ROLL",
            "W": list(W_GRID),
            "kappa": list(KAPPA_GRID),
            "n_primary": len(primary_rows),
            "n_sensitivity": len(sensitivity_rows),
        },
        "primary_rows": primary_rows,
        "sensitivity_rows": sensitivity_rows,
        "verdict": verdict,
        "best_variant_id": best_id,
        "verdict_detail": detail,
        "best_row": best,
        "non_actions": [
            "No Soft-Frozen clip flip",
            "No live KD_OPT / TEL_EQUAL / Soft / Sleeve / FUSE / BLEND / priv / E45 / DH wire",
            "No Soft||Sleeve ops auto-fuse",
            "No E45 stitch reopen / no undo DROP_E45_A05",
            "No Stage A fusion with DH/Soft/Sleeve/FUSE",
            "No full Kelly / no f_hi>1 / no shorts",
            "Even KELLY_PROMOTE_SHAPED -> paper observe ballot only; never live from this screen",
        ],
    }

    (OUT / "stagea_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OPS / "KELLY_EXPOSURE_STAGEA_SCREEN.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Kelly exposure — Stage A screen",
        "",
        f"- screen_id: `{SCREEN_ID}`",
        f"- charter: `{CHARTER_ID}`",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        "- status: **DONE** · mode: PAPER_ONLY · live_wire: false · observe_open: false",
        "",
        "## Verdict",
        "",
        f"- **`{verdict}`**",
        f"- best_variant_id (primary EDGE_LIVE_ROLL only): `{best_id}`",
        f"- detail: `{json.dumps(detail, ensure_ascii=False)}`",
        "",
        "Promote gate uses **EDGE_LIVE_ROLL** only. `EDGE_0050_ROLL` is sensitivity / report-only.",
        "",
        "## Primary (EDGE_LIVE_ROLL)",
        "",
        "| variant | kappa | W | tip_clean | class | held score | held MDD up | tip ytd MDD up | tip 1y MDD up | mean e | frac@bound |",
        "|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in primary_rows:
        h = r.get("heldout_delta") or {}
        tip = r.get("tip") or {}
        d = r.get("exposure_diag") or {}
        lines.append(
            f"| `{r['variant_id']}` | {r['kappa']:.2f} | {r['W']} | {r['tip_clean']} | "
            f"`{r['row_class']}` | {h.get('score')} | {h.get('mdd_improve_pp')} | "
            f"{(tip.get('ytd') or {}).get('mdd_improve_pp')} | "
            f"{(tip.get('trailing_1y') or {}).get('mdd_improve_pp')} | "
            f"{d.get('mean_e')} | {d.get('frac_at_bound')} |"
        )

    lines += [
        "",
        "## Sensitivity (EDGE_0050_ROLL, report-only)",
        "",
        "| variant | kappa | W | tip_clean | class | held score | mean e | frac@bound |",
        "|---|---:|---:|---|---|---:|---:|---:|",
    ]
    for r in sensitivity_rows:
        h = r.get("heldout_delta") or {}
        d = r.get("exposure_diag") or {}
        lines.append(
            f"| `{r['variant_id']}` | {r['kappa']:.2f} | {r['W']} | {r['tip_clean']} | "
            f"`{r['row_class']}` | {h.get('score')} | {d.get('mean_e')} | {d.get('frac_at_bound')} |"
        )

    lines += [
        "",
        "## Base windows (LIVE_STACK)",
        "",
        "```json",
        json.dumps(payload["base_windows"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Non-actions",
        "",
    ]
    lines += [f"- {x}" for x in payload["non_actions"]]
    lines += [
        "",
        f"Artifact: `{ARTIFACT}`",
        "Repro: `repro/kelly-exposure-stagea/`",
        "",
        "## Next authorized action",
        "",
    ]
    if verdict == "KELLY_PROMOTE_SHAPED":
        lines.append(
            f"- Draft **paper observe** ballot for `{best_id}` "
            "(dual-paper LIVE_STACK || challenger). **No live wire** from this screen alone."
        )
    elif verdict == "COEXIST_NO_LIFT":
        lines.append("- KEEP research note; no observe unless human expands charter.")
    else:
        lines.append(
            "- **STOP / archive** unless human amends charter (W / kappa / f_lo). Live unchanged."
        )

    text = "\n".join(lines) + "\n"
    (REP / "KELLY_EXPOSURE_STAGEA_SCREEN.md").write_text(text, encoding="utf-8")
    (OPS / "KELLY_EXPOSURE_STAGEA_SCREEN.md").write_text(text, encoding="utf-8")
    (OPS / "KELLY_EXPOSURE_STAGEA_SCREEN.zh-TW.md").write_text(
        "\n".join(
            [
                "# Kelly exposure — Stage A screen",
                "",
                f"- verdict: **`{verdict}`**",
                f"- best (LIVE edge only): `{best_id}`",
                f"- detail: `{json.dumps(detail, ensure_ascii=False)}`",
                "",
                "EN full report: `KELLY_EXPOSURE_STAGEA_SCREEN.md`",
                "",
                "No live wire; even KELLY_PROMOTE_SHAPED needs a separate paper observe ballot.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"[4/4] verdict={verdict} best={best_id}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
