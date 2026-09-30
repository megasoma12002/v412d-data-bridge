#!/usr/bin/env python3
"""Path3 + Path4 Soft-0050 coexist paper dual (0kao) — Soft-core carve · T+0.

**Live-intent coexistence (paper only):**
- Path3 ``WITHIN_DAILY`` owns FIN∪TEL every day (sticky Soft 0050 baseline)
- Path4 Soft-own trail gate on Soft **0050 only**
- Coexist OFF book = ``OFF_CASH_ETF`` (0050→0 / cash; FIN∪TEL absolute KEEP)
- Diagnostic control: ``OFF_RENORM`` (forbidden live — would fight P3 FIN∪TEL)
- Soft sticky state is **separate** from Path4 overlay (OFF must re-enter Soft 0050)

Baseline: ``REF_P3_WITHIN`` · Champion Path4 θ grid on CASH_ETF · Soft KEEP ·
broker false · **no Path4 live wire** · forbid Path3 trail as P4 input.
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
REPRO = ROOT / "repro" / "fin-sat-path3-path4-coexist-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
MARKET = ROOT / "forward/e21/live_market.csv"

CHARTER_ID = "FIN_SAT_PATH3_PATH4_COEXIST_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_PATH4_COEXIST_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_PATH4_COEXIST_STAGEA_DECISION_PACK"
REGISTER = "0kao"
PARENTS = ("0kac", "0kak", "0kan")

ETF = "0050"
SOFT_CORE = list(FIN) + list(TEL) + [ETF]
TRAIL = 63
# Align with Path4 Stage A + extreme CASH_ETF runners (dead θ=0.05 kept for no-op check)
THETAS = (0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02)

SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _close_panel(codes: list[str]) -> pd.DataFrame:
    m = pd.read_csv(MARKET, dtype={"code": str}, parse_dates=["date"])
    m = m[m["code"].isin(codes)]
    return (
        m.pivot_table(index="date", columns="code", values="close", aggfunc="last")
        .sort_index()
        .astype(float)
        .reindex(columns=codes)
    )


def _book_soft_weights(panel: pd.DataFrame, px: pd.DataFrame) -> pd.DataFrame:
    dates = panel.index.intersection(px.index)
    w = pd.DataFrame(0.0, index=dates, columns=SOFT_CORE)
    for c in SOFT_CORE:
        if c not in panel.columns or c not in px.columns:
            continue
        dol = panel.loc[dates, c].astype(float) * px.loc[dates, c].astype(float)
        w[c] = dol.clip(lower=0.0)
    s = w.sum(axis=1).replace(0.0, np.nan)
    return w.div(s, axis=0).fillna(0.0)


def _apply_keep0050(
    w_prev: np.ndarray,
    w_dest: np.ndarray,
    etf_idx: int,
    fin_tel_idx: list[int],
) -> np.ndarray:
    etf_w = float(min(max(w_prev[etf_idx], 0.0), 1.0))
    out = np.zeros_like(w_prev, dtype=float)
    out[etf_idx] = etf_w
    ft = w_dest[fin_tel_idx].astype(float).copy()
    ft_sum = float(ft.sum())
    if ft_sum > 1e-12 and etf_w < 1.0 - 1e-12:
        out[fin_tel_idx] = ft / ft_sum * (1.0 - etf_w)
    elif etf_w >= 1.0 - 1e-12:
        out[etf_idx] = 1.0
    else:
        prev_ft = w_prev[fin_tel_idx]
        psum = float(prev_ft.sum())
        if psum > 1e-12:
            out[fin_tel_idx] = prev_ft / psum * (1.0 - etf_w)
        else:
            out[etf_idx] = 1.0
    s = float(out.sum())
    return out / s if s > 1e-12 else w_prev.copy()


def _port_rets(w: pd.DataFrame, px: pd.DataFrame) -> pd.Series:
    dates = w.index.intersection(px.index)
    rets = px.pct_change().reindex(dates).fillna(0.0)
    ww = w.reindex(dates).fillna(0.0)
    return (ww * rets.reindex(columns=SOFT_CORE).fillna(0.0)).sum(axis=1).astype(float)


def _trail_rel(r_on: pd.Series, r_off: pd.Series, window: int = TRAIL) -> pd.Series:
    rel = (r_on - r_off).astype(float)
    x = np.log1p(rel.clip(lower=-0.999999))
    return np.expm1(x.rolling(window, min_periods=window).sum())


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, (start, end) in WINDOWS_STANDARD.items():
        st = window_stats(nav, start, end)
        out[name] = {
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
            "cagr_lift_pp": None
            if cagr_lift_pp(bc, cc) is None
            else round(float(cagr_lift_pp(bc, cc)), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
        }
    return out


def _delta_windows(base_w: dict, chal_w: dict) -> dict[str, Any]:
    out = {}
    for k in ("full", "heldout_2019_plus", "sealed_2023_plus"):
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


def yearly_compare(nav_keep: pd.DataFrame, nav_chal: pd.DataFrame) -> list[dict[str, Any]]:
    def _yr(nav: pd.DataFrame) -> dict[int, dict[str, float]]:
        x = nav.copy()
        x["date"] = pd.to_datetime(x["date"])
        x["year"] = x["date"].dt.year
        out: dict[int, dict[str, float]] = {}
        for y, g in x.groupby("year"):
            g = g.reset_index(drop=True)
            if len(g) < 2:
                continue
            n0 = float(g["nav"].iloc[0])
            bn = g["nav"].astype(float) / n0
            out[int(y)] = {
                "ret": float(bn.iloc[-1] - 1.0),
                "mdd": float((bn / bn.cummax() - 1.0).min()),
            }
        return out

    a, b = _yr(nav_keep), _yr(nav_chal)
    rows = []
    for y in sorted(set(a) | set(b)):
        ka, kb = a.get(y), b.get(y)
        if not ka or not kb:
            continue
        rows.append(
            {
                "year": y,
                "ret_keep_pct": round(ka["ret"] * 100, 4),
                "ret_chal_pct": round(kb["ret"] * 100, 4),
                "ret_lift_pp": round((kb["ret"] - ka["ret"]) * 100, 4),
                "mdd_improve_pp": round((kb["mdd"] - ka["mdd"]) * 100, 4),
                "ret_win": bool(kb["ret"] > ka["ret"]),
            }
        )
    return rows


def _arm_verdict(
    delta: dict[str, Any], tip: dict[str, Any], *, n_off_days: int = 0
) -> str:
    held = delta["heldout_2019_plus"]
    sealed = delta["sealed_2023_plus"]
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    if held.get("cagr_lift_pp") is None or sealed.get("mdd_improve_pp") is None:
        return "INCOMPLETE"
    # No Path4 activity → identical to REF; not a promote candidate
    if int(n_off_days) <= 0:
        return "NO_EDGE"
    held_ok = float(held["cagr_lift_pp"]) >= HELD_CAGR_FLOOR_PP
    sealed_ok = float(sealed["mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
    tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
    full_ok = float(delta["full"].get("cagr_lift_pp") or 0) > 0
    if held_ok and sealed_ok and tip_ok and full_ok:
        return "HIT"
    if held_ok and sealed_ok and tip_ok:
        return "HELD_HIT"
    # SOFT requires a non-trivial held edge (exclude ~0 no-ops)
    if (
        sealed_ok
        and tip_ok
        and float(held["cagr_lift_pp"]) > 0.02
    ):
        return "SOFT"
    if float(sealed["mdd_improve_pp"]) < SEALED_MDD_FLOOR_PP:
        return "MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "TIP_BLOCK"
    return "NO_EDGE"


def _theta_tag(th: float) -> str:
    s = f"{th:.4f}".rstrip("0").rstrip(".")
    return s.replace(".", "")


def simulate_p3_within_p4_gate(
    *,
    weights_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    signal: pd.DataFrame,
    off_lead: pd.Series | None,
    off_mode: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """P3 WITHIN_DAILY Soft-core + optional Path4 0050 gate.

    off_mode:
      - ``none``: sticky Soft 0050 (REF_P3_WITHIN)
      - ``cash_etf``: OFF → ETF=0, FIN∪TEL absolute KEEP (cash residual)
      - ``renorm``: OFF → ETF=0, renorm FIN∪TEL (diagnostic / forbidden live)
    """
    sig = signal.copy()
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.sort_values("date").reset_index(drop=True)
    dates = sig["date"]
    for wdf in weights_by_book.values():
        dates = dates[dates.isin(wdf.index)]
    dates = dates[dates.isin(px.index)].reset_index(drop=True)
    if off_lead is not None:
        dates = dates[dates.isin(off_lead.index)].reset_index(drop=True)
    if len(dates) < 100:
        raise RuntimeError("insufficient overlap")

    rets = px.pct_change().reindex(dates).fillna(0.0)
    etf_idx = SOFT_CORE.index(ETF)
    fin_tel_idx = [SOFT_CORE.index(c) for c in list(FIN) + list(TEL)]
    sig_i = sig.set_index("date")

    row0 = sig[sig["date"] == dates.iloc[0]].iloc[0]
    book0 = str(row0.get("book") or BOOK_COMP)
    if book0 not in weights_by_book:
        book0 = BOOK_COMP
    # Soft sticky Path3 WITHIN state — Path4 never mutates this (avoids sticky-death
    # after cash_etf OFF where KEEP would otherwise freeze etf=0 forever).
    w_soft = weights_by_book[book0].loc[dates.iloc[0], SOFT_CORE].to_numpy(dtype=float)
    w_soft = (
        w_soft / w_soft.sum()
        if w_soft.sum() > 1e-12
        else np.ones(len(SOFT_CORE)) / len(SOFT_CORE)
    )

    nav = [1.0]
    n_recon = 0
    n_off = 0
    n_flip_days = 0

    for i in range(1, len(dates)):
        d = dates.iloc[i]
        r = rets.loc[d, SOFT_CORE].to_numpy(dtype=float)
        srow = sig_i.loc[d] if d in sig_i.index else None
        if isinstance(srow, pd.DataFrame):
            srow = srow.iloc[-1]
        flip = bool(srow.get("flip", False)) if srow is not None else False
        book = str(srow.get("book") or BOOK_COMP) if srow is not None else BOOK_COMP
        if book not in weights_by_book:
            book = BOOK_COMP
        if flip:
            n_flip_days += 1

        # Path3 WITHIN: daily FIN∪TEL recon, sticky Soft 0050 (Soft-own state)
        if d in weights_by_book[book].index:
            w_dest = weights_by_book[book].loc[d, SOFT_CORE].to_numpy(dtype=float)
            if w_dest.sum() > 1e-12:
                w_dest = w_dest / w_dest.sum()
                w_soft = _apply_keep0050(w_soft, w_dest, etf_idx, fin_tel_idx)
                n_recon += 1

        # Path4 Soft-0050 gate overlays Soft sticky — does not rewrite Soft state
        lead = False
        if off_lead is not None and d in off_lead.index:
            lead = bool(off_lead.loc[d])
        w_inv = w_soft.copy()
        if lead and off_mode != "none":
            n_off += 1
            if off_mode == "cash_etf":
                w_inv[etf_idx] = 0.0
                # FIN∪TEL absolute KEEP — cash residual earns 0
            elif off_mode == "renorm":
                w_inv[etf_idx] = 0.0
                ft = w_inv[fin_tel_idx]
                sft = float(ft.sum())
                if sft > 1e-12:
                    w_inv[fin_tel_idx] = ft / sft
            else:
                raise ValueError(off_mode)

        port_r = float(np.dot(w_inv, r))
        nav.append(nav[-1] * (1.0 + port_r))
        # Soft sticky always evolves Soft-ON (incl. 0050) so OFF days can re-enter
        w_soft = w_soft * (1.0 + r)
        s = float(w_soft.sum())
        if s > 1e-12:
            w_soft = w_soft / s

    out = pd.DataFrame({"date": dates.to_numpy(), "nav": np.asarray(nav, dtype=float)})
    meta = {
        "fill_timing": "t0",
        "p3_policy": "WITHIN_DAILY",
        "p4_off_mode": off_mode,
        "n_days": int(len(out)),
        "n_flip_days": int(n_flip_days),
        "n_recon_days": int(n_recon),
        "n_off_days": int(n_off),
        "pct_off": round(float(n_off) / max(len(out) - 1, 1), 4),
        "start": str(pd.Timestamp(out["date"].iloc[0]).date()),
        "end": str(pd.Timestamp(out["date"].iloc[-1]).date()),
        "soft_sticky_separate_from_p4": True,
    }
    return out, meta


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    px = _close_panel(SOFT_CORE)
    weights = {
        BOOK_COMP: _book_soft_weights(load_book_shares(BOOK_COMP), px),
        BOOK_SAT: _book_soft_weights(load_book_shares(BOOK_SAT), px),
    }
    sig = load_or_build_signal()

    # Soft-own ON vs CASH_ETF OFF trail (Path4 feature — not Path3 trail)
    w_on = weights[BOOK_COMP]
    w_cash = w_on.copy()
    w_cash[ETF] = 0.0
    r_on = _port_rets(w_on, px)
    r_cash = _port_rets(w_cash, px)
    idx = r_on.index.intersection(r_cash.index)
    r_on, r_cash = r_on.reindex(idx), r_cash.reindex(idx)
    trail_cash = _trail_rel(r_on, r_cash)

    w_renorm = w_on.copy()
    w_renorm[ETF] = 0.0
    ft = list(FIN) + list(TEL)
    s = w_renorm[ft].sum(axis=1)
    for c in ft:
        w_renorm[c] = np.where(s.to_numpy() > 1e-12, w_renorm[c] / s, 0.0)
    r_renorm = _port_rets(w_renorm, px).reindex(idx)
    trail_renorm = _trail_rel(r_on, r_renorm)

    # Diagnostic: corr vs Path3 trail (must not be an input)
    p3 = load_or_build_signal()
    p3["date"] = pd.to_datetime(p3["date"]).dt.normalize()
    p3i = p3.set_index("date")["trail_rel_63"]
    both = pd.concat(
        [trail_cash.rename("p4"), p3i.rename("p3")], axis=1, join="inner"
    ).dropna()
    corr = float(both["p4"].corr(both["p3"])) if len(both) > 50 else None

    panel = pd.DataFrame(
        {
            "date": idx,
            "r_soft_on": r_on.to_numpy(),
            "r_off_cash_etf": r_cash.to_numpy(),
            "trail_rel_on_cash_etf_63": trail_cash.reindex(idx).to_numpy(),
            "trail_rel_on_renorm_63": trail_renorm.reindex(idx).to_numpy(),
        }
    )
    panel.to_csv(OUT / "coexist_feature_panel.csv", index=False)

    arms: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict[str, Any]] = {}

    nav_base, meta_base = simulate_p3_within_p4_gate(
        weights_by_book=weights,
        px=px,
        signal=sig,
        off_lead=None,
        off_mode="none",
    )
    arms["REF_P3_WITHIN"] = nav_base
    metas["REF_P3_WITHIN"] = {**meta_base, "kind": "p3_within_only"}

    for th in THETAS:
        lead = (trail_cash.reindex(idx) <= -float(th)) & trail_cash.reindex(idx).notna()
        name = f"P3_P4_CASH_{_theta_tag(th)}"
        nav, meta = simulate_p3_within_p4_gate(
            weights_by_book=weights,
            px=px,
            signal=sig,
            off_lead=lead,
            off_mode="cash_etf",
        )
        arms[name] = nav
        metas[name] = {
            **meta,
            "kind": "p3_within_p4_cash_etf",
            "theta": th,
            "live_intent_off_book": "CASH_ETF",
        }

    # Diagnostic forbidden live OFF=RENORM at Stage A θ
    lead001 = (trail_renorm.reindex(idx) <= -0.01) & trail_renorm.reindex(idx).notna()
    nav_r, meta_r = simulate_p3_within_p4_gate(
        weights_by_book=weights,
        px=px,
        signal=sig,
        off_lead=lead001,
        off_mode="renorm",
    )
    arms["P3_P4_RENORM_001"] = nav_r
    metas["P3_P4_RENORM_001"] = {
        **meta_r,
        "kind": "diagnostic_renorm_forbidden_live",
        "theta": 0.01,
        "live_intent_off_book": "RENORM_FORBIDDEN",
    }

    for k, nav in arms.items():
        nav.to_csv(OUT / f"nav_{k}.csv", index=False)

    base = arms["REF_P3_WITHIN"]
    bw = _pack(base)
    rows = []
    for arm, nav in arms.items():
        if arm == "REF_P3_WITHIN":
            continue
        delta = _delta_windows(bw, _pack(nav))
        tip = _tip(base, nav)
        yearly = yearly_compare(base, nav)
        ret_w = int(sum(1 for r in yearly if r["ret_win"]))
        ret_l = int(sum(1 for r in yearly if not r["ret_win"]))
        meta_arm = metas.get(arm, {})
        v = _arm_verdict(delta, tip, n_off_days=int(meta_arm.get("n_off_days") or 0))
        rows.append(
            {
                "arm": arm,
                "verdict_vs_p3_within": v,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "yearly_ret_wl": f"{ret_w}-{ret_l}",
                "meta": meta_arm,
                "delta": delta,
                "tip": tip,
                "yearly": yearly,
            }
        )

    def _rank_key(r: dict[str, Any]) -> tuple[float, float, float]:
        return (
            float(r["held_cagr_lift_pp"] or -999),
            float(r["tip_ytd_cagr_lift_pp"] or -999),
            float(r["sealed_mdd_improve_pp"] or -999),
        )

    cash_rows = [
        r
        for r in rows
        if (r.get("meta") or {}).get("kind") == "p3_within_p4_cash_etf"
        and int((r.get("meta") or {}).get("n_off_days") or 0) > 0
    ]
    cash_hit = [
        r for r in cash_rows if r["verdict_vs_p3_within"] in {"HIT", "HELD_HIT"}
    ]
    if cash_hit:
        champion = max(cash_hit, key=_rank_key)
        pack_verdict = "P3_P4_COEXIST_HIT"
    else:
        soft = [r for r in cash_rows if r["verdict_vs_p3_within"] == "SOFT"]
        if soft:
            champion = max(soft, key=_rank_key)
            pack_verdict = "P3_P4_COEXIST_SOFT"
        else:
            champion = max(cash_rows or rows, key=_rank_key)
            pack_verdict = f"P3_P4_COEXIST_{champion['verdict_vs_p3_within']}"

    summary = [
        {
            "arm": r["arm"],
            "verdict_vs_p3_within": r["verdict_vs_p3_within"],
            "full_cagr_lift_pp": r["full_cagr_lift_pp"],
            "held_cagr_lift_pp": r["held_cagr_lift_pp"],
            "sealed_mdd_improve_pp": r["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": r["tip_ytd_cagr_lift_pp"],
            "tip_1y_cagr_lift_pp": r["tip_1y_cagr_lift_pp"],
            "yearly_ret_wl": r["yearly_ret_wl"],
            **{f"meta_{k}": v for k, v in (r["meta"] or {}).items()},
        }
        for r in rows
    ]
    pd.DataFrame(summary).to_csv(OUT / "arms_vs_p3_within.csv", index=False)
    pd.DataFrame(champion["yearly"]).to_csv(
        OUT / "yearly_champion_vs_p3_within.csv", index=False
    )

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": "PATH3_PATH4_COEXIST",
        "verdict": pack_verdict,
        "fill_timing": "t0",
        "base": "REF_P3_WITHIN",
        "champion_arm": champion["arm"],
        "coexist_off_book_live_intent": "CASH_ETF",
        "forbid_live_off_books": ["RENORM", "FULL_CASH"],
        "forbid_path3_inputs_to_p4": True,
        "corr_p4_cash_trail_vs_p3_trail_rel_63": None
        if corr is None
        else round(corr, 4),
        "arms_vs_p3_within": summary,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_p3_within": champion["verdict_vs_p3_within"],
            "delta": champion["delta"],
            "tip": champion["tip"],
            "meta": champion["meta"],
        },
        "gates": {
            "held_cagr_floor_pp": HELD_CAGR_FLOOR_PP,
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
            "tip_y_floor_pp": TIP_Y_FLOOR_PP,
        },
        "note": (
            "Soft-core carve paper: P3 WITHIN owns FIN∪TEL daily; "
            "P4 Soft-own trail gates Soft 0050 via CASH_ETF. "
            "RENORM arm is diagnostic only (forbidden live under P3 cutover)."
        ),
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage A — Path3×Path4 coexist paper** · Soft **KEEP** · "
            "broker **false** · Path4 live **OFF** · P3 cutover separate",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Under Path3 ``WITHIN_DAILY`` Soft-core ownership, does a Soft-own "
            "Path4 Soft-0050 gate with **``OFF_CASH_ETF``** (not renorm) beat sticky "
            "Soft 0050 on tip/held — without Path3 trail hitchhiking?",
            "",
            "## Coexist map",
            "",
            "| Sleeve | Owner |",
            "|---|---|",
            "| FIN∪TEL | Path3 WITHIN daily |",
            "| Soft 0050 | Soft sticky · Path4 ON↔CASH_ETF gate |",
            "",
            "## Non-goals",
            "",
            "- Path4 live wire · OFF_RENORM / FULL_CASH live · broker · Soft clip flip",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__P3_P4_COEXIST__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter"
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "mech": "PATH3_PATH4_COEXIST",
                "soft_keep": True,
                "broker": False,
                "path4_live": False,
                "off_book_live_intent": "CASH_ETF",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    def _fmt(r: dict) -> str:
        return (
            f"| {r['arm']} | {r['verdict_vs_p3_within']} | {r['held_cagr_lift_pp']} | "
            f"{r['full_cagr_lift_pp']} | {r['sealed_mdd_improve_pp']} | "
            f"{r['tip_ytd_cagr_lift_pp']} | {r['tip_1y_cagr_lift_pp']} | "
            f"{r['yearly_ret_wl']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`** · fill=`t0`",
            f"Register: **{REGISTER}** · base=`REF_P3_WITHIN` · "
            f"corr(P4 cash trail, P3)=**{None if corr is None else round(corr, 3)}**",
            "",
            "## Arms vs Path3 WITHIN (sticky Soft 0050)",
            "",
            "| Arm | vs P3 | held | full | sealed MDD↑ | tipY | tip1y | ret W–L |",
            "|---|---|---:|---:|---:|---:|---:|---|",
            *[_fmt(r) for r in summary],
            "",
            f"## Champion `{champion['arm']}` yearly vs REF_P3_WITHIN",
            "",
            "| Year | P3 ret% | Chal ret% | Ret lift pp |",
            "|---:|---:|---:|---:|",
            *[
                f"| {y['year']} | {y['ret_keep_pct']:.2f} | {y['ret_chal_pct']:.2f} | "
                f"{y['ret_lift_pp']:+.2f} |"
                for y in champion["yearly"]
            ],
            "",
            "Repro: `PYTHONPATH=scripts python3 "
            "scripts/fin_sat_path3_path4_coexist_stagea.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{pack_verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps: list[str] = []
    if pack_verdict == "P3_P4_COEXIST_HIT":
        next_steps.append(
            f"Carry `{champion['arm']}` coexist design (OFF=CASH_ETF) — still no Path4 live"
        )
        next_steps.append(
            "Optional Stage B: tip Soft twin smoke under live P3 cutover stack — no wire"
        )
    elif pack_verdict == "P3_P4_COEXIST_SOFT":
        next_steps.append("Borderline — tip/held disposition before any Path4 ballot")
    elif "TIP_BLOCK" in pack_verdict:
        next_steps.append(
            f"Best active `{champion['arm']}` tip-blocked vs P3 WITHIN — "
            "do not promote Path4 CASH_ETF gate under P3"
        )
        next_steps.append(
            "Keep Soft sticky 0050 under Path3 WITHIN; Path4 live stays OFF"
        )
    else:
        next_steps.append(
            "P4 CASH_ETF gate on P3 WITHIN no promote; keep Soft 0050 sticky under P3"
        )
    next_steps.append("OFF_RENORM remains forbidden live under P3 FIN∪TEL ownership")
    next_steps.append("Soft KEEP · broker false · Path4 live flag OFF")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{pack_verdict}__NO_LIVE",
        "verdict": pack_verdict,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": "PATH3_PATH4_COEXIST",
        "champion_arm": champion["arm"],
        "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
        "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
        "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
        "corr_p4_vs_p3_trail": None if corr is None else round(corr, 4),
        "off_book_live_intent": "CASH_ETF",
        "soft_keep": True,
        "broker": False,
        "path4_live": False,
        "next": next_steps,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · base **REF_P3_WITHIN**",
            "",
            "## Champion vs Path3 WITHIN (sticky Soft 0050)",
            "",
            f"- held CAGR lift: **{champion['held_cagr_lift_pp']}** pp",
            f"- full CAGR lift: **{champion['full_cagr_lift_pp']}** pp",
            f"- sealed MDD improve: **{champion['sealed_mdd_improve_pp']}** pp",
            f"- tipY / tip1y: **{champion['tip_ytd_cagr_lift_pp']}** / "
            f"**{champion['tip_1y_cagr_lift_pp']}**",
            f"- corr(P4 cash trail, P3 trail): **"
            f"{None if corr is None else round(corr, 3)}**",
            "",
            "## Disposition",
            "",
            "- Coexist OFF book = **CASH_ETF** (live intent).",
            "- ``P3_P4_RENORM_001`` is diagnostic only — forbidden live.",
            "- Path4 live flag stays **OFF** · Soft KEEP · broker false.",
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
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="decision pack",
    )
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    print(
        json.dumps(
            {
                "verdict": pack_verdict,
                "champion": champion["arm"],
                "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
                "full_cagr_lift_pp": champion["full_cagr_lift_pp"],
                "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
                "tip_1y_cagr_lift_pp": champion["tip_1y_cagr_lift_pp"],
                "corr_p4_vs_p3_trail": None if corr is None else round(corr, 4),
                "base_held_cagr": bw["heldout_2019_plus"]["cagr"],
                "base_held_mdd": bw["heldout_2019_plus"]["max_drawdown"],
                "chal_held_cagr": champion["delta"]["heldout_2019_plus"]["chal_cagr"],
                "chal_held_mdd": champion["delta"]["heldout_2019_plus"]["chal_mdd"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
