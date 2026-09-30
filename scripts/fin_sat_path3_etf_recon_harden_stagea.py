#!/usr/bin/env python3
"""Path3 0050 ETF recon harden Stage A (0kah) — paper only · T+0.

Parent 0kag: Soft-core carve-only NAV dual under T+0 fill — full RATIO HIT but
yearly ret W–L 7–8 (2024 drag). This pack probes **slew / clip / deadband**
on flip-day ``Δw_0050`` to improve CAGR/MDD vs sticky KEEP while reducing
yearly losers vs full ``LEDGER_SOFT_RATIO``.

Between flips: hold Soft-core weights. Soft KEEP · broker false · cutover
BLOCKED · no live.
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
REPRO = ROOT / "repro" / "fin-sat-path3-etf-recon-harden-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_ETF_RECON_HARDEN_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_ETF_RECON_HARDEN_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_ETF_RECON_HARDEN_STAGEA_DECISION_PACK"
REGISTER = "0kah"

ETF = "0050"
SOFT_CORE = list(FIN) + list(TEL) + [ETF]
MARKET = ROOT / "forward/e21/live_market.csv"

SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0

# Arms: (policy_id, kind, param)
# kind: keep | ratio | clip | slew | deadband
ARMS: list[tuple[str, str, float | None]] = [
    ("KEEP", "keep", None),
    ("RATIO", "ratio", None),
    ("CLIP_05", "clip", 0.05),
    ("CLIP_10", "clip", 0.10),
    ("CLIP_15", "clip", 0.15),
    ("SLEW_50", "slew", 0.50),
    ("SLEW_75", "slew", 0.75),
    ("DEAD_02", "deadband", 0.02),
    ("DEAD_05", "deadband", 0.05),
]


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


def _normalize_with_etf(
    *,
    w_prev: np.ndarray,
    w_dest: np.ndarray,
    etf_idx: int,
    fin_tel_idx: list[int],
    etf_w: float,
) -> np.ndarray:
    etf_w = float(min(max(etf_w, 0.0), 1.0))
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


def _apply_arm(
    *,
    kind: str,
    param: float | None,
    w_prev: np.ndarray,
    w_dest: np.ndarray,
    etf_idx: int,
    fin_tel_idx: list[int],
) -> np.ndarray:
    if kind == "keep":
        return _normalize_with_etf(
            w_prev=w_prev,
            w_dest=w_dest,
            etf_idx=etf_idx,
            fin_tel_idx=fin_tel_idx,
            etf_w=float(w_prev[etf_idx]),
        )
    if kind == "ratio":
        out = w_dest.astype(float).copy()
        s = float(out.sum())
        return out / s if s > 1e-12 else w_prev.copy()

    prev_e = float(w_prev[etf_idx])
    dest_e = float(w_dest[etf_idx])
    delta = dest_e - prev_e

    if kind == "clip":
        step = float(param or 0.0)
        delta = float(np.clip(delta, -step, step))
        return _normalize_with_etf(
            w_prev=w_prev,
            w_dest=w_dest,
            etf_idx=etf_idx,
            fin_tel_idx=fin_tel_idx,
            etf_w=prev_e + delta,
        )
    if kind == "slew":
        a = float(param or 0.0)
        a = min(max(a, 0.0), 1.0)
        return _normalize_with_etf(
            w_prev=w_prev,
            w_dest=w_dest,
            etf_idx=etf_idx,
            fin_tel_idx=fin_tel_idx,
            etf_w=(1.0 - a) * prev_e + a * dest_e,
        )
    if kind == "deadband":
        thr = float(param or 0.0)
        if abs(delta) < thr:
            etf_w = prev_e
        else:
            etf_w = dest_e
        return _normalize_with_etf(
            w_prev=w_prev,
            w_dest=w_dest,
            etf_idx=etf_idx,
            fin_tel_idx=fin_tel_idx,
            etf_w=etf_w,
        )
    raise ValueError(kind)


def simulate_arm(
    *,
    weights_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    signal: pd.DataFrame,
    kind: str,
    param: float | None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """T+0 Path3-carve Soft-core NAV under harden arm."""
    sig = signal.copy()
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.sort_values("date").reset_index(drop=True)
    dates = sig["date"]
    for wdf in weights_by_book.values():
        dates = dates[dates.isin(wdf.index)]
    dates = dates[dates.isin(px.index)].reset_index(drop=True)
    if len(dates) < 100:
        raise RuntimeError("insufficient overlap for Soft-core NAV sim")

    rets = px.pct_change().reindex(dates).fillna(0.0)
    etf_idx = SOFT_CORE.index(ETF)
    fin_tel_idx = [SOFT_CORE.index(c) for c in list(FIN) + list(TEL)]

    row0 = sig[sig["date"] == dates.iloc[0]].iloc[0]
    book0 = str(row0.get("book") or BOOK_COMP)
    if book0 not in weights_by_book:
        book0 = BOOK_COMP
    w = weights_by_book[book0].loc[dates.iloc[0], SOFT_CORE].to_numpy(dtype=float)
    w = w / w.sum() if w.sum() > 1e-12 else np.ones(len(SOFT_CORE)) / len(SOFT_CORE)

    nav = [1.0]
    n_flip = 0
    etf_turnover = 0.0
    sig_by_date = sig.set_index("date")

    for i in range(1, len(dates)):
        d = dates.iloc[i]
        r = rets.loc[d, SOFT_CORE].to_numpy(dtype=float)
        flipped = False
        dw = 0.0
        if d in sig_by_date.index:
            srow = sig_by_date.loc[d]
            if isinstance(srow, pd.DataFrame):
                srow = srow.iloc[-1]
            if bool(srow.get("flip", False)):
                book = str(srow.get("book") or BOOK_COMP)
                if book in weights_by_book and d in weights_by_book[book].index:
                    w_dest = weights_by_book[book].loc[d, SOFT_CORE].to_numpy(dtype=float)
                    if w_dest.sum() > 1e-12:
                        w_dest = w_dest / w_dest.sum()
                        w_before = w.copy()
                        w = _apply_arm(
                            kind=kind,
                            param=param,
                            w_prev=w,
                            w_dest=w_dest,
                            etf_idx=etf_idx,
                            fin_tel_idx=fin_tel_idx,
                        )
                        dw = abs(float(w[etf_idx] - w_before[etf_idx]))
                        flipped = True
        if flipped:
            n_flip += 1
            etf_turnover += dw
        port_r = float(np.dot(w, r))
        nav.append(nav[-1] * (1.0 + port_r))
        w = w * (1.0 + r)
        s = float(w.sum())
        w = w / s if s > 1e-12 else w

    out = pd.DataFrame({"date": dates.to_numpy(), "nav": np.asarray(nav, dtype=float)})
    meta = {
        "kind": kind,
        "param": param,
        "fill_timing": "t0",
        "n_days": int(len(out)),
        "n_flips_applied": int(n_flip),
        "sum_abs_etf_weight_delta_on_flips": round(float(etf_turnover), 6),
        "start": str(pd.Timestamp(out["date"].iloc[0]).date()),
        "end": str(pd.Timestamp(out["date"].iloc[-1]).date()),
    }
    return out, meta


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
                "n_days": float(len(g)),
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
                "mdd_win": bool(kb["mdd"] > ka["mdd"]),
            }
        )
    return rows


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


def _arm_verdict(delta: dict[str, Any], tip: dict[str, Any]) -> str:
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
        return "HIT"
    if held_ok and sealed_ok and tip_ok:
        return "HELD_HIT"
    if sealed_ok and tip_ok and float(held["cagr_lift_pp"]) > -0.5:
        return "SOFT"
    if float(sealed["mdd_improve_pp"]) < SEALED_MDD_FLOOR_PP:
        return "MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "TIP_BLOCK"
    return "NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    comp = load_book_shares(BOOK_COMP)
    sat = load_book_shares(BOOK_SAT)
    px = _close_panel(SOFT_CORE)
    weights = {
        BOOK_COMP: _book_soft_weights(comp, px),
        BOOK_SAT: _book_soft_weights(sat, px),
    }
    sig = load_or_build_signal()

    navs: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict[str, Any]] = {}
    wins: dict[str, dict[str, Any]] = {}
    for arm_id, kind, param in ARMS:
        nav, meta = simulate_arm(
            weights_by_book=weights, px=px, signal=sig, kind=kind, param=param
        )
        navs[arm_id] = nav
        metas[arm_id] = meta
        wins[arm_id] = _pack(nav)
        nav.to_csv(OUT / f"nav_{arm_id}.csv", index=False)

    base_id = "KEEP"
    rows = []
    for arm_id, kind, param in ARMS:
        if arm_id == base_id:
            continue
        delta = _delta_windows(wins[base_id], wins[arm_id])
        tip = _tip(navs[base_id], navs[arm_id])
        yearly = yearly_compare(navs[base_id], navs[arm_id])
        ret_w = int(sum(1 for r in yearly if r["ret_win"]))
        ret_l = int(sum(1 for r in yearly if not r["ret_win"]))
        mdd_w = int(sum(1 for r in yearly if r["mdd_win"]))
        mdd_l = int(sum(1 for r in yearly if not r["mdd_win"]))
        v = _arm_verdict(delta, tip)
        row = {
            "arm": arm_id,
            "kind": kind,
            "param": param,
            "verdict_vs_keep": v,
            "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
            "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
            "sealed_cagr_lift_pp": delta["sealed_2023_plus"]["cagr_lift_pp"],
            "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
            "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
            "yearly_ret_w": ret_w,
            "yearly_ret_l": ret_l,
            "yearly_mdd_w": mdd_w,
            "yearly_mdd_l": mdd_l,
            "etf_turnover": metas[arm_id]["sum_abs_etf_weight_delta_on_flips"],
            "delta": delta,
            "tip": tip,
            "yearly": yearly,
            "meta": metas[arm_id],
        }
        rows.append(row)

    # Champion: among HIT/HELD_HIT, maximize yearly ret net W–L (pack goal: cut
    # calendar losers), then held CAGR, tipY, sealed MDD.
    rankable = [r for r in rows if r["verdict_vs_keep"] in {"HIT", "HELD_HIT"}]
    if not rankable:
        rankable = [r for r in rows if r["verdict_vs_keep"] == "SOFT"]
    if rankable:
        champion = max(
            rankable,
            key=lambda r: (
                int(r["yearly_ret_w"]) - int(r["yearly_ret_l"]),
                float(r["held_cagr_lift_pp"] or -999),
                float(r["tip_ytd_cagr_lift_pp"] or -999),
                float(r["sealed_mdd_improve_pp"] or -999),
            ),
        )
    else:
        champion = max(rows, key=lambda r: float(r["held_cagr_lift_pp"] or -999))

    ratio_row = next(r for r in rows if r["arm"] == "RATIO")
    beats_ratio_held = float(champion["held_cagr_lift_pp"] or 0) > float(
        ratio_row["held_cagr_lift_pp"] or 0
    )
    beats_ratio_wl = (int(champion["yearly_ret_w"]) - int(champion["yearly_ret_l"])) > (
        int(ratio_row["yearly_ret_w"]) - int(ratio_row["yearly_ret_l"])
    )

    if champion["verdict_vs_keep"] in {"HIT", "HELD_HIT"} and (
        beats_ratio_held or beats_ratio_wl or champion["arm"] == "RATIO"
    ):
        if champion["arm"] == "RATIO" and not any(
            r["arm"] != "RATIO"
            and r["verdict_vs_keep"] in {"HIT", "HELD_HIT"}
            and (
                float(r["held_cagr_lift_pp"] or 0) > float(ratio_row["held_cagr_lift_pp"] or 0)
                or (int(r["yearly_ret_w"]) - int(r["yearly_ret_l"]))
                > (int(ratio_row["yearly_ret_w"]) - int(ratio_row["yearly_ret_l"]))
            )
            for r in rows
        ):
            pack_verdict = "ETF_HARDEN_RATIO_STILL_BEST"
        elif champion["arm"] != "RATIO" and (beats_ratio_held or beats_ratio_wl):
            pack_verdict = "ETF_HARDEN_HIT"
        else:
            pack_verdict = "ETF_HARDEN_HIT"
    elif champion["verdict_vs_keep"] == "SOFT":
        pack_verdict = "ETF_HARDEN_SOFT"
    elif champion["verdict_vs_keep"] == "MDD_BLOCK":
        pack_verdict = "ETF_HARDEN_MDD_BLOCK"
    elif champion["verdict_vs_keep"] == "TIP_BLOCK":
        pack_verdict = "ETF_HARDEN_TIP_BLOCK"
    else:
        pack_verdict = "ETF_HARDEN_NO_EDGE"

    # Prefer explicit RATIO_STILL_BEST when no harden arm beats RATIO on held or W–L
    harden_better = [
        r
        for r in rows
        if r["arm"] != "RATIO"
        and r["verdict_vs_keep"] in {"HIT", "HELD_HIT"}
        and (
            float(r["held_cagr_lift_pp"] or 0) > float(ratio_row["held_cagr_lift_pp"] or 0)
            or (int(r["yearly_ret_w"]) - int(r["yearly_ret_l"]))
            > (int(ratio_row["yearly_ret_w"]) - int(ratio_row["yearly_ret_l"]))
        )
    ]
    if ratio_row["verdict_vs_keep"] in {"HIT", "HELD_HIT"} and not harden_better:
        pack_verdict = "ETF_HARDEN_RATIO_STILL_BEST"
        champion = ratio_row

    summary_rows = [
        {
            "arm": r["arm"],
            "kind": r["kind"],
            "param": r["param"],
            "verdict_vs_keep": r["verdict_vs_keep"],
            "full_cagr_lift_pp": r["full_cagr_lift_pp"],
            "held_cagr_lift_pp": r["held_cagr_lift_pp"],
            "sealed_mdd_improve_pp": r["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": r["tip_ytd_cagr_lift_pp"],
            "tip_1y_cagr_lift_pp": r["tip_1y_cagr_lift_pp"],
            "yearly_ret_wl": f"{r['yearly_ret_w']}-{r['yearly_ret_l']}",
            "yearly_mdd_wl": f"{r['yearly_mdd_w']}-{r['yearly_mdd_l']}",
            "etf_turnover": r["etf_turnover"],
        }
        for r in rows
    ]
    pd.DataFrame(summary_rows).to_csv(OUT / "arms_vs_keep.csv", index=False)
    pd.DataFrame(champion["yearly"]).to_csv(OUT / "yearly_champion_vs_keep.csv", index=False)

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parent": "0kag",
        "verdict": pack_verdict,
        "fill_timing": "t0",
        "champion_arm": champion["arm"],
        "method": {
            "universe": SOFT_CORE,
            "fill_timing": "t0",
            "between_flips": "hold Soft-core weights",
            "arms": [a[0] for a in ARMS],
            "note": "clip/slew/deadband only reshape flip-day Δw_0050; FIN∪TEL from dest",
        },
        "arms_vs_keep": summary_rows,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_keep": champion["verdict_vs_keep"],
            "delta": champion["delta"],
            "tip": champion["tip"],
            "yearly_ret_wl": {
                "w": champion["yearly_ret_w"],
                "l": champion["yearly_ret_l"],
            },
            "meta": champion["meta"],
        },
        "ratio_baseline": {
            "held_cagr_lift_pp": ratio_row["held_cagr_lift_pp"],
            "yearly_ret_wl": {
                "w": ratio_row["yearly_ret_w"],
                "l": ratio_row["yearly_ret_l"],
            },
            "tip_ytd_cagr_lift_pp": ratio_row["tip_ytd_cagr_lift_pp"],
        },
        "gates": {
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
            "tip_y_floor_pp": TIP_Y_FLOOR_PP,
        },
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage A — Path3 0050 ETF recon harden** · Soft **KEEP** · "
            "broker **false** · cutover **BLOCKED** · no live",
            "Parent: 0kag `ETF_NAV_DUAL_HIT` (T+0 full RATIO)",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Can flip-day **clip / slew / deadband** on Soft `0050` weight change "
            "improve Soft-core tip/held/sealed vs sticky `KEEP`, and beat or match "
            "parent full `LEDGER_SOFT_RATIO` on held CAGR or yearly ret W–L?",
            "",
            "## Method",
            "",
            "- Soft-core = FIN∪TEL∪0050 · Path3 flips · **fill `t0`**",
            "- Arms: KEEP · RATIO · CLIP_{05,10,15} · SLEW_{50,75} · DEAD_{02,05}",
            "- Between flips: hold Soft-core weights (carve-only)",
            "",
            "## Gates (vs KEEP)",
            "",
            f"- held CAGR lift > 0 · sealed MDD improve ≥ {SEALED_MDD_FLOOR_PP} pp · "
            f"tip YTD ≥ {TIP_Y_FLOOR_PP} pp",
            "- Champion: HIT arm maximizing held; prefer harden if beats RATIO held or W–L",
            "",
            "## Non-goals",
            "",
            "- Live `keep_0050=False` · mute expand · Soft Exact T+1 between flips · "
            "satellite · broker · cutover ACCEPT",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__HARDEN__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parent": "0kag",
                "fill_timing": "t0",
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

    def _fmt(r: dict) -> str:
        return (
            f"| {r['arm']} | {r['verdict_vs_keep']} | {r['full_cagr_lift_pp']} | "
            f"{r['held_cagr_lift_pp']} | {r['sealed_mdd_improve_pp']} | "
            f"{r['tip_ytd_cagr_lift_pp']} | {r['tip_1y_cagr_lift_pp']} | "
            f"{r['yearly_ret_wl']} | {r['etf_turnover']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · fill=`t0` · "
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · parent 0kag · end=`{metas['KEEP']['end']}`",
            "",
            "## Arms vs KEEP (T+0)",
            "",
            "| Arm | vs KEEP | full CAGR | held CAGR | sealed MDD↑ | tipY | tip1y | ret W–L | sum|Δw_0050| |",
            "|---|---|---:|---:|---:|---:|---:|---|---:|",
            *[_fmt(r) for r in summary_rows],
            "",
            f"## Champion `{champion['arm']}` yearly vs KEEP",
            "",
            f"- Ret W–L **{champion['yearly_ret_w']}–{champion['yearly_ret_l']}** · "
            f"RATIO baseline **{ratio_row['yearly_ret_w']}–{ratio_row['yearly_ret_l']}**",
            "",
            "| Year | KEEP ret% | Chal ret% | Ret lift pp | MDD improve pp |",
            "|---:|---:|---:|---:|---:|",
            *[
                f"| {y['year']} | {y['ret_keep_pct']:.2f} | {y['ret_chal_pct']:.2f} | "
                f"{y['ret_lift_pp']:+.2f} | {y['mdd_improve_pp']:+.2f} |"
                for y in champion["yearly"]
            ],
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_recon_harden_stagea.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{pack_verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = []
    if pack_verdict == "ETF_HARDEN_HIT":
        next_steps.append(
            f"Carry champion `{champion['arm']}` into coexist Stage C / e21 smoke — still no live"
        )
    elif pack_verdict == "ETF_HARDEN_RATIO_STILL_BEST":
        next_steps.append(
            "Keep full `LEDGER_SOFT_RATIO` as 0050 flip policy; harden slew/clip no edge over parent"
        )
        next_steps.append(
            "Optional coexist Stage C (Soft Exact T+1 between flips) before any ballot"
        )
    else:
        next_steps.append("No harden promote — live Path3 remains keep_0050=True")
    next_steps.append("0kac PAPER_WITHIN_HIT remains primary Path3 roadmap")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{pack_verdict}__NO_LIVE",
        "verdict": pack_verdict,
        "register": REGISTER,
        "parent": "0kag",
        "champion_arm": champion["arm"],
        "fill_timing": "t0",
        "champion_held_cagr_lift_pp": champion["held_cagr_lift_pp"],
        "champion_tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
        "ratio_held_cagr_lift_pp": ratio_row["held_cagr_lift_pp"],
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
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`** · fill=`t0`",
            f"Register: **{REGISTER}** · Parent: **0kag**",
            "",
            "## Champion vs KEEP",
            "",
            f"- held CAGR lift: **{champion['held_cagr_lift_pp']}** pp",
            f"- full CAGR lift: **{champion['full_cagr_lift_pp']}** pp",
            f"- sealed MDD improve: **{champion['sealed_mdd_improve_pp']}** pp",
            f"- tipY / tip1y: **{champion['tip_ytd_cagr_lift_pp']}** / "
            f"**{champion['tip_1y_cagr_lift_pp']}** pp",
            f"- yearly ret W–L: **{champion['yearly_ret_w']}–{champion['yearly_ret_l']}** "
            f"(RATIO {ratio_row['yearly_ret_w']}–{ratio_row['yearly_ret_l']})",
            "",
            "## Disposition",
            "",
            "- Paper Soft-core carve-only · T+0 flip harden probe.",
            "- Live Path3 remains `keep_0050=True` unless human ACCEPT after coexist pack.",
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
                "verdict": pack_verdict,
                "champion": champion["arm"],
                "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
                "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
                "yearly_ret_wl": f"{champion['yearly_ret_w']}-{champion['yearly_ret_l']}",
                "ratio_held_cagr_lift_pp": ratio_row["held_cagr_lift_pp"],
                "ratio_yearly_ret_wl": f"{ratio_row['yearly_ret_w']}-{ratio_row['yearly_ret_l']}",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
