#!/usr/bin/env python3
"""Path3 strategy cutover Stage B — paper WITHIN_SLEEVE vs flip-carve (0kam).

Parent 0kac: ``CUTOVER_SCOPE_DEFINED`` · default scope ``WITHIN_SLEEVE_PATH3``.
This pack is the paper dual seeking **``PAPER_WITHIN_HIT``** before any live
``live_path3_strategy_cutover`` ACCEPT.

Arms (Soft-core carve paper · T+0 · sticky Soft 0050):
- ``FLIP_CARVE`` — status quo: Path3 flip-only FIN∪TEL recon to dest Soft-core;
  0050 weight sticky (live flip carve + keep_0050).
- ``WITHIN_DAILY`` — challenger: **every day** FIN∪TEL → active Path3 book
  Soft-core mix; 0050 sticky (scope WITHIN_SLEEVE_PATH3 paper).
- ``FULL_DAILY`` — context upper bound: full Soft-core = active book daily.

Soft clips KEEP · broker false · cutover flag OFF · no live.
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
REPRO = ROOT / "repro" / "fin-sat-path3-strategy-cutover-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
MARKET = ROOT / "forward/e21/live_market.csv"
CHECKLIST = OPS / "CUTOVER_CHECKLIST_PATH3_STRATEGY.md"

CHARTER_ID = "FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEB_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEB_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEB_DECISION_PACK"
REGISTER = "0kam"
PARENT = "0kac"
MECH = "PATH3_STRATEGY_CUTOVER"
SCOPE = "WITHIN_SLEEVE_PATH3"

ETF = "0050"
SOFT_CORE = list(FIN) + list(TEL) + [ETF]
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0


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


def simulate_policy(
    *,
    policy: str,
    weights_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    signal: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """T+0 Soft-core NAV under FLIP_CARVE | WITHIN_DAILY | FULL_DAILY."""
    sig = signal.copy()
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.sort_values("date").reset_index(drop=True)
    dates = sig["date"]
    for wdf in weights_by_book.values():
        dates = dates[dates.isin(wdf.index)]
    dates = dates[dates.isin(px.index)].reset_index(drop=True)
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
    w = weights_by_book[book0].loc[dates.iloc[0], SOFT_CORE].to_numpy(dtype=float)
    w = w / w.sum() if w.sum() > 1e-12 else np.ones(len(SOFT_CORE)) / len(SOFT_CORE)

    nav = [1.0]
    n_recon = 0
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

        do_recon = False
        if policy == "FLIP_CARVE":
            do_recon = flip
        elif policy == "WITHIN_DAILY":
            do_recon = True
        elif policy == "FULL_DAILY":
            do_recon = True
        else:
            raise ValueError(policy)

        if do_recon and d in weights_by_book[book].index:
            w_dest = weights_by_book[book].loc[d, SOFT_CORE].to_numpy(dtype=float)
            if w_dest.sum() > 1e-12:
                w_dest = w_dest / w_dest.sum()
                if policy == "FULL_DAILY":
                    w = w_dest
                else:
                    w = _apply_keep0050(w, w_dest, etf_idx, fin_tel_idx)
                n_recon += 1

        port_r = float(np.dot(w, r))
        nav.append(nav[-1] * (1.0 + port_r))
        w = w * (1.0 + r)
        s = float(w.sum())
        w = w / s if s > 1e-12 else w

    out = pd.DataFrame({"date": dates.to_numpy(), "nav": np.asarray(nav, dtype=float)})
    meta = {
        "policy": policy,
        "fill_timing": "t0",
        "keep_0050": policy != "FULL_DAILY",
        "n_days": int(len(out)),
        "n_flip_days": int(n_flip_days),
        "n_recon_days": int(n_recon),
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
            out[int(y)] = {"ret": float(bn.iloc[-1] - 1.0), "mdd": float((bn / bn.cummax() - 1.0).min())}
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
                "ret_base_pct": round(ka["ret"] * 100, 4),
                "ret_chal_pct": round(kb["ret"] * 100, 4),
                "ret_lift_pp": round((kb["ret"] - ka["ret"]) * 100, 4),
                "mdd_improve_pp": round((kb["mdd"] - ka["mdd"]) * 100, 4),
                "ret_win": bool(kb["ret"] > ka["ret"]),
            }
        )
    return rows


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
    edge = held_ok or float(full.get("cagr_lift_pp") or 0) > 0 or (
        tip_y is not None and float(tip_y) > 0
    )
    if not sealed_ok:
        return "PAPER_MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "PAPER_TIP_BLOCK"
    if held_ok and sealed_ok and tip_ok and edge:
        return "PAPER_WITHIN_HIT"
    if sealed_ok and tip_ok and float(held["cagr_lift_pp"]) > -0.5:
        return "PAPER_WITHIN_SOFT"
    if not edge:
        return "PAPER_NO_EDGE"
    return "PAPER_NO_EDGE"


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

    policies = ("FLIP_CARVE", "WITHIN_DAILY", "FULL_DAILY")
    navs: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict[str, Any]] = {}
    wins: dict[str, dict[str, Any]] = {}
    for p in policies:
        nav, meta = simulate_policy(
            policy=p, weights_by_book=weights, px=px, signal=sig
        )
        navs[p] = nav
        metas[p] = meta
        wins[p] = _pack(nav)
        nav.to_csv(OUT / f"nav_{p}.csv", index=False)

    base = "FLIP_CARVE"
    chal = "WITHIN_DAILY"
    delta = _delta_windows(wins[base], wins[chal])
    tip = _tip(navs[base], navs[chal])
    yearly = yearly_compare(navs[base], navs[chal])
    ret_w = int(sum(1 for r in yearly if r["ret_win"]))
    ret_l = int(sum(1 for r in yearly if not r["ret_win"]))
    verdict = _verdict(delta, tip)

    delta_full = _delta_windows(wins[base], wins["FULL_DAILY"])
    tip_full = _tip(navs[base], navs["FULL_DAILY"])

    pd.DataFrame(yearly).to_csv(OUT / "yearly_WITHIN_vs_FLIP.csv", index=False)

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parent": PARENT,
        "mechanism": MECH,
        "scope": SCOPE,
        "verdict": verdict,
        "fill_timing": "t0",
        "base": base,
        "chal": chal,
        "meta": metas,
        "delta_within_minus_flip": delta,
        "tip_within_minus_flip": tip,
        "delta_full_minus_flip": delta_full,
        "tip_full_minus_flip": tip_full,
        "yearly_within_minus_flip": yearly,
        "yearly_ret_wl": {"w": ret_w, "l": ret_l},
        "gates": {
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
            "tip_y_floor_pp": TIP_Y_FLOOR_PP,
        },
        "live_flag": False,
        "broker": False,
        "note": (
            "Soft-core carve paper dual; Soft Exact T+1 FIN/TEL retire is scope intent — "
            "this pack measures Path3 daily FIN∪TEL ownership vs flip-carve with sticky 0050"
        ),
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage B — Path3 strategy cutover paper dual** · Soft **KEEP** · "
            "broker **false** · live cutover flag **OFF**",
            f"Parent: {PARENT} `CUTOVER_SCOPE_DEFINED` · scope `{SCOPE}`",
            f"Register: **{REGISTER}** · mech `{MECH}`",
            "",
            "## Question",
            "",
            "Does paper `WITHIN_SLEEVE_PATH3` (daily Path3 FIN∪TEL Soft-core ownership, "
            "sticky 0050) beat status-quo flip-carve on tip/held/sealed enough to justify "
            "cutover ACCEPT later?",
            "",
            "## Arms",
            "",
            "- `FLIP_CARVE` — flip-only FIN∪TEL recon · sticky 0050 (status quo)",
            "- `WITHIN_DAILY` — daily FIN∪TEL → active book · sticky 0050 (challenger)",
            "- `FULL_DAILY` — context: Soft-core = book daily (0050 moves too)",
            "",
            "## Gates → `PAPER_WITHIN_HIT`",
            "",
            f"- held CAGR lift > 0 · sealed MDD improve ≥ {SEALED_MDD_FLOOR_PP} pp · "
            f"tipY ≥ {TIP_Y_FLOOR_PP} pp · edge vs flip-carve",
            "",
            "## Non-goals",
            "",
            "- `live_path3_strategy_cutover=True` · broker · Soft clip flip · FULL_SOFT_REPLACE",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__PAPER_WITHIN__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parent": PARENT,
                "mechanism": MECH,
                "scope": SCOPE,
                "soft_keep": True,
                "broker": False,
                "live_path3_strategy_cutover": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · fill=`t0`",
            f"Register: **{REGISTER}** · parent {PARENT} · scope `{SCOPE}` · "
            f"end=`{metas[base]['end']}`",
            f"recon days FLIP/WITHIN/FULL = "
            f"{metas['FLIP_CARVE']['n_recon_days']}/"
            f"{metas['WITHIN_DAILY']['n_recon_days']}/"
            f"{metas['FULL_DAILY']['n_recon_days']} · flips={metas[base]['n_flip_days']}",
            "",
            "## WITHIN_DAILY − FLIP_CARVE (pp)",
            "",
            "| Window | CAGR lift | MDD improve |",
            "|---|---:|---:|",
            f"| full | {delta['full']['cagr_lift_pp']} | {delta['full']['mdd_improve_pp']} |",
            f"| held | {delta['heldout_2019_plus']['cagr_lift_pp']} | "
            f"{delta['heldout_2019_plus']['mdd_improve_pp']} |",
            f"| sealed | {delta['sealed_2023_plus']['cagr_lift_pp']} | "
            f"{delta['sealed_2023_plus']['mdd_improve_pp']} |",
            "",
            "## Tip",
            "",
            f"- tipY CAGR lift: **{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · "
            f"tip1y: **{(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}**",
            f"- yearly ret W–L: **{ret_w}–{ret_l}**",
            "",
            "## Context FULL_DAILY − FLIP_CARVE",
            "",
            f"- held CAGR: {(delta_full.get('heldout_2019_plus') or {}).get('cagr_lift_pp')} · "
            f"tipY: {(tip_full.get('ytd') or {}).get('cagr_lift_pp')}",
            "",
            "## Yearly WITHIN − FLIP",
            "",
            "| Year | FLIP ret% | WITHIN ret% | Ret lift pp |",
            "|---:|---:|---:|---:|",
            *[
                f"| {r['year']} | {r['ret_base_pct']:.2f} | {r['ret_chal_pct']:.2f} | "
                f"{r['ret_lift_pp']:+.2f} |"
                for r in yearly
            ],
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_strategy_cutover_stageb.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = []
    if verdict == "PAPER_WITHIN_HIT":
        next_steps.append(
            "Human ballot only: ACCEPT Path3 strategy cutover WITHIN_SLEEVE_PATH3 — still no auto wire"
        )
        next_steps.append("Overlay coexistence smoke + wrong-stay/2022 disposition before ACCEPT")
        next_steps.append("Broker remains separate ballot · cutover flag stays OFF until ACCEPT")
    elif verdict == "PAPER_WITHIN_SOFT":
        next_steps.append("Borderline — require tip/held human disposition")
    elif verdict == "PAPER_MDD_BLOCK":
        next_steps.append("Do not cut over — sealed/held MDD fails")
    else:
        next_steps.append("Keep FLIP_CARVE_ONLY live status quo — no WITHIN_SLEEVE cutover")
    next_steps.append("Path4 Soft-0050 mutex remains separate track")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "parent": PARENT,
        "mechanism": MECH,
        "scope": SCOPE,
        "delta_within_minus_flip": delta,
        "tip_within_minus_flip": tip,
        "yearly_ret_wl": {"w": ret_w, "l": ret_l},
        "soft_keep": True,
        "broker": False,
        "live_path3_strategy_cutover": False,
        "next": next_steps,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parent: **{PARENT}** · scope `{SCOPE}`",
            "",
            "## WITHIN_DAILY − FLIP_CARVE",
            "",
            f"- held CAGR lift: **{delta['heldout_2019_plus']['cagr_lift_pp']}** pp",
            f"- full CAGR lift: **{delta['full']['cagr_lift_pp']}** pp",
            f"- sealed MDD improve: **{delta['sealed_2023_plus']['mdd_improve_pp']}** pp",
            f"- tipY / tip1y: **{(tip.get('ytd') or {}).get('cagr_lift_pp')}** / "
            f"**{(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}**",
            f"- yearly ret W–L: **{ret_w}–{ret_l}**",
            "",
            "## Disposition",
            "",
            "- Paper Soft-core carve only · live cutover flag **OFF** · broker **false**.",
            "- Soft clips + Soft 0050 Exact T+1 remain KEEP under scope intent.",
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

    # Checklist tick for paper dual line (append note, don't rewrite whole checklist casually)
    if CHECKLIST.exists() and verdict == "PAPER_WITHIN_HIT":
        text = CHECKLIST.read_text(encoding="utf-8")
        old = "- [ ] Paper dual Soft-carve vs `WITHIN_SLEEVE_PATH3` → **`PAPER_WITHIN_HIT`** (or human scope pick)"
        new = (
            f"- [x] Paper dual Soft-carve vs `WITHIN_SLEEVE_PATH3` → **`PAPER_WITHIN_HIT`** "
            f"({generated[:10]} · `{DECISION_ID}.md` · still no live flag)"
        )
        if old in text:
            CHECKLIST.write_text(text.replace(old, new), encoding="utf-8")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "yearly_ret_wl": f"{ret_w}-{ret_l}",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
