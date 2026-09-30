#!/usr/bin/env python3
"""Path3 0050 ETF recon — Stage B paper NAV dual (improvement vs KEEP).

Parent 0kae: champion ``LEDGER_SOFT_RATIO`` on flip probes.
This pack rebuilds Soft-core (FIN∪TEL∪0050) path NAV under Path3 flips:

- ``KEEP`` — on flip, recon FIN∪TEL to dest Soft-core mix; **sticky 0050 weight**
- ``LEDGER_SOFT_RATIO`` — on flip, full Soft-core weights → dest book (incl. 0050)
- ``FULL_DAILY`` — context: every day Soft-core weights = active book (cutover-like)

Between flips: hold Soft-core weights (Path3-carve-only paper; no Soft Exact T+1).
Soft-Frozen KEEP · broker false · cutover BLOCKED · no live.
Register: 0kag
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, load_or_build_signal
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from path3_comp_sat_daily_share_ssot import load_book_shares
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-etf-recon-nav-dual-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_DECISION_PACK"
REGISTER = "0kag"

ETF = "0050"
SOFT_CORE = list(FIN) + list(TEL) + [ETF]
MARKET = ROOT / "forward/e21/live_market.csv"
CTRL_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
P3_NAV = ROOT / "repro/fin-sat-path3-t0-dual-paper-observe/outputs/p3_t0_state_daily_nav.csv"

# Gates (paper HIT): held lift>0 · sealed MDD not worse than -0.25pp vs KEEP · tipY not < -1pp
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _close_panel(codes: list[str]) -> pd.DataFrame:
    m = pd.read_csv(MARKET, dtype={"code": str}, parse_dates=["date"])
    m = m[m["code"].isin(codes)]
    px = (
        m.pivot_table(index="date", columns="code", values="close", aggfunc="last")
        .sort_index()
        .astype(float)
    )
    return px.reindex(columns=codes)


def _book_soft_weights(panel: pd.DataFrame, px: pd.DataFrame) -> pd.DataFrame:
    """EOD Soft-core dollar weights by date (rows sum≈1)."""
    dates = panel.index.intersection(px.index)
    w = pd.DataFrame(0.0, index=dates, columns=SOFT_CORE)
    for c in SOFT_CORE:
        if c not in panel.columns or c not in px.columns:
            continue
        w[c] = panel.loc[dates, c].astype(float) * px.loc[dates, c].astype(float)
    tot = w.sum(axis=1).replace(0.0, np.nan)
    w = w.div(tot, axis=0).fillna(0.0)
    return w


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
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


def _tip(base: pd.DataFrame, chal: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base["date"]).max())
    b_dates = pd.to_datetime(base["date"])
    c_dates = pd.to_datetime(chal["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"cagr_lift_pp": None, "mdd_improve_pp": None}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        out[wname] = {
            "cagr_lift_pp": None if cagr_lift_pp(bc, cc) is None else round(float(cagr_lift_pp(bc, cc)), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
        }
    return out


def _apply_flip_weights(
    *,
    policy: str,
    w_prev: np.ndarray,
    w_dest: np.ndarray,
    etf_idx: int,
    fin_tel_idx: list[int],
) -> np.ndarray:
    """Return new Soft-core weights after Path3 flip."""
    if policy == "LEDGER_SOFT_RATIO":
        out = w_dest.astype(float).copy()
        s = out.sum()
        return out / s if s > 1e-12 else w_prev.copy()

    if policy == "KEEP":
        etf_w = float(w_prev[etf_idx])
        etf_w = min(max(etf_w, 0.0), 1.0)
        ft = w_dest[fin_tel_idx].astype(float).copy()
        ft_sum = float(ft.sum())
        out = np.zeros_like(w_prev, dtype=float)
        out[etf_idx] = etf_w
        if ft_sum > 1e-12 and etf_w < 1.0 - 1e-12:
            out[fin_tel_idx] = ft / ft_sum * (1.0 - etf_w)
        elif etf_w >= 1.0 - 1e-12:
            out[etf_idx] = 1.0
        else:
            # no FIN/TEL in dest — keep prev FIN∪TEL mass
            prev_ft = w_prev[fin_tel_idx]
            psum = float(prev_ft.sum())
            if psum > 1e-12:
                out[fin_tel_idx] = prev_ft / psum * (1.0 - etf_w)
            else:
                out[etf_idx] = 1.0
        s = out.sum()
        return out / s if s > 1e-12 else w_prev.copy()

    raise ValueError(policy)


def simulate_soft_core_nav(
    *,
    weights_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    signal: pd.DataFrame,
    policy: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Path3-carve Soft-core NAV under KEEP or LEDGER_SOFT_RATIO (flip-only recon)."""
    sig = signal.copy()
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.sort_values("date").reset_index(drop=True)

    # Align to intersection of signal, px, both books
    dates = sig["date"]
    for w in weights_by_book.values():
        dates = dates[dates.isin(w.index)]
    dates = dates[dates.isin(px.index)].reset_index(drop=True)
    if len(dates) < 100:
        raise RuntimeError("insufficient overlap for Soft-core NAV sim")

    rets = px.pct_change().reindex(dates).fillna(0.0)
    etf_idx = SOFT_CORE.index(ETF)
    fin_tel_idx = [SOFT_CORE.index(c) for c in list(FIN) + list(TEL)]

    # Start on first date with book from signal
    row0 = sig[sig["date"] == dates.iloc[0]].iloc[0]
    book0 = str(row0.get("book") or BOOK_COMP)
    if book0 not in weights_by_book:
        book0 = BOOK_COMP
    w = weights_by_book[book0].loc[dates.iloc[0], SOFT_CORE].to_numpy(dtype=float)
    if w.sum() <= 1e-12:
        w = np.ones(len(SOFT_CORE)) / len(SOFT_CORE)
    else:
        w = w / w.sum()

    nav = [1.0]
    n_flip = 0
    n_etf_move = 0
    etf_turnover = 0.0  # sum |Δw_etf| on flips

    sig_by_date = sig.set_index("date")
    for i in range(1, len(dates)):
        d = dates.iloc[i]
        d_prev = dates.iloc[i - 1]
        r = rets.loc[d, SOFT_CORE].to_numpy(dtype=float)
        # earn
        port_r = float(np.dot(w, r))
        nav.append(nav[-1] * (1.0 + port_r))
        # weight drift from returns
        w = w * (1.0 + r)
        s = float(w.sum())
        w = w / s if s > 1e-12 else w

        # flip recon at EOD of flip day (signal date == d)
        if d not in sig_by_date.index:
            continue
        srow = sig_by_date.loc[d]
        if isinstance(srow, pd.DataFrame):
            srow = srow.iloc[-1]
        if not bool(srow.get("flip", False)):
            continue
        book = str(srow.get("book") or BOOK_COMP)
        if book not in weights_by_book or d not in weights_by_book[book].index:
            continue
        w_dest = weights_by_book[book].loc[d, SOFT_CORE].to_numpy(dtype=float)
        if w_dest.sum() <= 1e-12:
            continue
        w_dest = w_dest / w_dest.sum()
        w_before = w.copy()
        w = _apply_flip_weights(
            policy=policy, w_prev=w, w_dest=w_dest, etf_idx=etf_idx, fin_tel_idx=fin_tel_idx
        )
        n_flip += 1
        dw = abs(float(w[etf_idx] - w_before[etf_idx]))
        etf_turnover += dw
        if dw > 1e-6:
            n_etf_move += 1

    out = pd.DataFrame({"date": dates.to_numpy(), "nav": np.asarray(nav, dtype=float)})
    meta = {
        "policy": policy,
        "n_days": int(len(out)),
        "n_flips_applied": int(n_flip),
        "n_flips_etf_weight_moved": int(n_etf_move),
        "sum_abs_etf_weight_delta_on_flips": round(float(etf_turnover), 6),
        "start": str(pd.Timestamp(out["date"].iloc[0]).date()),
        "end": str(pd.Timestamp(out["date"].iloc[-1]).date()),
    }
    return out, meta


def simulate_full_daily(
    weights_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    signal: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Every day Soft-core weights = active Path3 book (context upper bound)."""
    sig = signal.copy()
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    dates = sig["date"]
    for w in weights_by_book.values():
        dates = dates[dates.isin(w.index)]
    dates = dates[dates.isin(px.index)].reset_index(drop=True)
    rets = px.pct_change().reindex(dates).fillna(0.0)
    sig_i = sig.set_index("date")
    nav = [1.0]
    w = None
    for i, d in enumerate(dates):
        book = str(sig_i.loc[d, "book"]) if d in sig_i.index else BOOK_COMP
        if isinstance(book, pd.Series):
            book = str(book.iloc[-1])
        if book not in weights_by_book:
            book = BOOK_COMP
        w_new = weights_by_book[book].loc[d, SOFT_CORE].to_numpy(dtype=float)
        if w_new.sum() > 1e-12:
            w_new = w_new / w_new.sum()
        else:
            w_new = np.ones(len(SOFT_CORE)) / len(SOFT_CORE)
        if i == 0:
            w = w_new
            continue
        r = rets.loc[d, SOFT_CORE].to_numpy(dtype=float)
        # use prior day weights for return, then snap to today's book weights
        port_r = float(np.dot(w, r))
        nav.append(nav[-1] * (1.0 + port_r))
        w = w_new
    out = pd.DataFrame({"date": dates.to_numpy(), "nav": np.asarray(nav, dtype=float)})
    return out, {"policy": "FULL_DAILY", "n_days": int(len(out))}


def _delta_windows(base_w: dict, chal_w: dict) -> dict[str, Any]:
    keys = ("full", "heldout_2019_plus", "sealed_2023_plus")
    out = {}
    for k in keys:
        b, c = base_w.get(k) or {}, chal_w.get(k) or {}
        out[k] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(b.get("cagr"), c.get("cagr")) is None
            else round(float(cagr_lift_pp(b.get("cagr"), c.get("cagr"))), 4),
            "mdd_improve_pp": None
            if b.get("max_drawdown") is None or c.get("max_drawdown") is None
            else round(float(mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])), 4),
            "base_cagr": b.get("cagr"),
            "chal_cagr": c.get("cagr"),
            "base_mdd": b.get("max_drawdown"),
            "chal_mdd": c.get("max_drawdown"),
        }
    return out


def _verdict(delta: dict[str, Any], tip: dict[str, Any]) -> str:
    held = delta["heldout_2019_plus"]
    sealed = delta["sealed_2023_plus"]
    full = delta["full"]
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    if held.get("cagr_lift_pp") is None or sealed.get("mdd_improve_pp") is None:
        return "INCOMPLETE"
    held_ok = float(held["cagr_lift_pp"]) > 0
    sealed_ok = float(sealed["mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
    tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
    if held_ok and sealed_ok and tip_ok and float(full.get("cagr_lift_pp") or 0) > 0:
        return "ETF_NAV_DUAL_HIT"
    if held_ok and sealed_ok and tip_ok:
        return "ETF_NAV_DUAL_HELD_HIT"
    if (not held_ok) and sealed_ok and tip_ok and float(held["cagr_lift_pp"]) > -0.5:
        return "ETF_NAV_DUAL_SOFT"
    if float(sealed["mdd_improve_pp"]) < SEALED_MDD_FLOOR_PP:
        return "ETF_NAV_DUAL_MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "ETF_NAV_DUAL_TIP_BLOCK"
    return "ETF_NAV_DUAL_NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    comp = load_book_shares(BOOK_COMP)
    sat = load_book_shares(BOOK_SAT)
    px = _close_panel(SOFT_CORE)
    w_comp = _book_soft_weights(comp, px)
    w_sat = _book_soft_weights(sat, px)
    weights = {BOOK_COMP: w_comp, BOOK_SAT: w_sat}
    sig = load_or_build_signal()

    nav_keep, meta_keep = simulate_soft_core_nav(
        weights_by_book=weights, px=px, signal=sig, policy="KEEP"
    )
    nav_ratio, meta_ratio = simulate_soft_core_nav(
        weights_by_book=weights, px=px, signal=sig, policy="LEDGER_SOFT_RATIO"
    )
    nav_full, meta_full = simulate_full_daily(weights, px, sig)

    nav_keep.to_csv(OUT / "nav_KEEP_0050.csv", index=False)
    nav_ratio.to_csv(OUT / "nav_LEDGER_SOFT_RATIO.csv", index=False)
    nav_full.to_csv(OUT / "nav_FULL_DAILY.csv", index=False)

    win_keep = _pack(nav_keep)
    win_ratio = _pack(nav_ratio)
    win_full = _pack(nav_full)
    delta = _delta_windows(win_keep, win_ratio)
    tip = _tip(nav_keep, nav_ratio)
    delta_full_ctx = _delta_windows(win_keep, win_full)
    verdict = _verdict(delta, tip)

    # Context vs published Path3 blend / CTRL if available
    context = {}
    if CTRL_NAV.exists() and P3_NAV.exists():
        ctrl = pd.read_csv(CTRL_NAV, parse_dates=["date"])
        p3 = pd.read_csv(P3_NAV, parse_dates=["date"])
        context = {
            "ctrl_windows": _pack(ctrl),
            "p3_blend_windows": _pack(p3),
            "note": "CTRL/P3_T0_STATE are full-book NAVs (incl DEF/overlays); Soft-core dual is carve-only",
        }

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parent": "0kae",
        "verdict": verdict,
        "method": {
            "universe": SOFT_CORE,
            "between_flips": "hold Soft-core weights",
            "KEEP": "flip: FIN∪TEL → dest Soft-core mix; sticky 0050 weight",
            "LEDGER_SOFT_RATIO": "flip: full Soft-core → dest book",
            "FULL_DAILY": "context: daily Soft-core = active book",
        },
        "meta_keep": meta_keep,
        "meta_ratio": meta_ratio,
        "meta_full_daily": meta_full,
        "windows_keep": win_keep,
        "windows_ratio": win_ratio,
        "windows_full_daily": win_full,
        "delta_ratio_minus_keep": delta,
        "delta_full_minus_keep": delta_full_ctx,
        "tip_ratio_minus_keep": tip,
        "gates": {
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
            "tip_y_floor_pp": TIP_Y_FLOOR_PP,
        },
        "context": context,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage B — Path3 0050 ETF recon paper NAV dual** · Soft **KEEP** · "
            "broker **false** · cutover **BLOCKED** · no live",
            "Parent: 0kae `ETF_POLICY_LEDGER_RATIO_HIT`",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Does flip-day `LEDGER_SOFT_RATIO` (move Soft 0050 toward dest book Soft-core weight) "
            "**improve** Path3 Soft-core tip/held/sealed vs status-quo sticky-0050 `KEEP`?",
            "",
            "## Method",
            "",
            "- Soft-core = FIN∪TEL∪0050 from COMP/SAT daily share ledgers × close",
            "- Path3 flips from `p3_t0_state` signal",
            "- Between flips: **hold** Soft-core weights (carve-only paper)",
            "- Arms: `KEEP` vs `LEDGER_SOFT_RATIO` (+ `FULL_DAILY` context)",
            "- Metrics: WINDOWS_STANDARD + tip YTD/1y · lift = chal − KEEP",
            "",
            "## Gates",
            "",
            f"- held CAGR lift > 0",
            f"- sealed MDD improve ≥ {SEALED_MDD_FLOOR_PP} pp",
            f"- tip YTD CAGR lift ≥ {TIP_Y_FLOOR_PP} pp (or null)",
            "",
            "## Non-goals",
            "",
            "- Live wire · mute expand · Soft Exact T+1 between flips · satellite · broker",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__NAV_DUAL__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parent": "0kae",
                "base": "KEEP",
                "chal": "LEDGER_SOFT_RATIO",
                "soft_keep": True,
                "broker": False,
                "cutover_blocked": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    def _row(name: str, d: dict) -> str:
        return (
            f"| {name} | {d.get('cagr_lift_pp')} | {d.get('mdd_improve_pp')} | "
            f"{d.get('base_cagr')} → {d.get('chal_cagr')} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · parent 0kae · end=`{meta_keep['end']}` · "
            f"flips KEEP/RATIO={meta_keep['n_flips_applied']}/{meta_ratio['n_flips_applied']} · "
            f"etf_moves RATIO={meta_ratio['n_flips_etf_weight_moved']}",
            "",
            "## Improvement: `LEDGER_SOFT_RATIO` − `KEEP` (pp)",
            "",
            "| Window | CAGR lift pp | MDD improve pp | KEEP → RATIO CAGR |",
            "|---|---:|---:|---|",
            _row("full", delta["full"]),
            _row("heldout_2019_plus", delta["heldout_2019_plus"]),
            _row("sealed_2023_plus", delta["sealed_2023_plus"]),
            "",
            "## Tip",
            "",
            f"- YTD CAGR lift pp: **{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · "
            f"MDD improve pp: {(tip.get('ytd') or {}).get('mdd_improve_pp')}",
            f"- Trailing 1y CAGR lift pp: **{(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}** · "
            f"MDD improve pp: {(tip.get('trailing_1y') or {}).get('mdd_improve_pp')}",
            "",
            "## ETF turnover on flips",
            "",
            f"- KEEP sum |Δw_0050|: {meta_keep['sum_abs_etf_weight_delta_on_flips']}",
            f"- RATIO sum |Δw_0050|: {meta_ratio['sum_abs_etf_weight_delta_on_flips']}",
            "",
            "## Context FULL_DAILY − KEEP",
            "",
            _row("full", delta_full_ctx["full"]),
            _row("held", delta_full_ctx["heldout_2019_plus"]),
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_recon_nav_dual_stageb.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = []
    if verdict in {"ETF_NAV_DUAL_HIT", "ETF_NAV_DUAL_HELD_HIT"}:
        next_steps.append(
            "Optional Stage C: add Soft Exact T+1 between flips / e21 coexistence smoke — still no live"
        )
        next_steps.append("Human ballot only after coexistence pack; default still KEEP until ACCEPT")
    elif verdict == "ETF_NAV_DUAL_SOFT":
        next_steps.append("Borderline — require tip/held disposition before any ballot")
    else:
        next_steps.append("Keep live Path3 `keep_0050=True` — no ETF recon promote")
    next_steps.append("0kac PAPER_WITHIN_HIT remains primary Path3 roadmap")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "parent": "0kae",
        "base": "KEEP",
        "chal": "LEDGER_SOFT_RATIO",
        "delta_ratio_minus_keep": delta,
        "tip_ratio_minus_keep": tip,
        "meta_ratio": meta_ratio,
        "soft_keep": True,
        "broker": False,
        "cutover_blocked": True,
        "live_wire": False,
        "next": next_steps,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parent: **0kae**",
            "",
            "## Improvement (`LEDGER_SOFT_RATIO` − `KEEP`)",
            "",
            f"- full CAGR lift: **{delta['full']['cagr_lift_pp']}** pp · "
            f"MDD improve: {delta['full']['mdd_improve_pp']} pp",
            f"- held CAGR lift: **{delta['heldout_2019_plus']['cagr_lift_pp']}** pp · "
            f"MDD improve: {delta['heldout_2019_plus']['mdd_improve_pp']} pp",
            f"- sealed CAGR lift: **{delta['sealed_2023_plus']['cagr_lift_pp']}** pp · "
            f"MDD improve: {delta['sealed_2023_plus']['mdd_improve_pp']} pp",
            f"- tip YTD CAGR lift: **{(tip.get('ytd') or {}).get('cagr_lift_pp')}** pp",
            f"- tip 1y CAGR lift: **{(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}** pp",
            "",
            "## Disposition",
            "",
            "- Paper Soft-core carve-only dual (not full Soft Exact T+1 path).",
            "- Live Path3 remains `keep_0050=True` unless human ACCEPT after stronger pack.",
            "",
            "## Next",
            "",
            *[f"{i+1}. {s}" for i, s in enumerate(next_steps)],
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
