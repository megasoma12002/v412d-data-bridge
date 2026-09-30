#!/usr/bin/env python3
"""Path4 Soft-0050 mutex Stage A (0kak) — paper only · T+0 Soft-core carve.

**Intent:** Mirror Path3's COMP↔SAT *mutual exclusion* for Soft ``0050`` —
an independent two-book switch, **not** hitchhiking Path3 flip dates
(0kae–0kaj).

Path3 analogy
-------------
- Path3 books: COMP vs SAT (FIN∪TEL composition)
- Path4 books: ``SOFT_ON`` (Soft-core incl. 0050) vs ``SOFT_OFF`` (0050=0,
  FIN∪TEL renormalized)
- Feature: ``trail_rel_on_off_63`` = 63d trail of ``r_ON − r_OFF``
- ``OFF_LEAD`` iff ``trail_rel_on_off_63 ≤ −θ`` (mirror SAT_LEAD)

Base weights from COMP Soft-core daily share ledger × close (same Soft-core
universe as 0kag carve packs). Soft KEEP · broker false · cutover BLOCKED ·
no live · **forbid Path3 ``trail_rel_63`` / P3 flip calendar as inputs**.
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
from live_path3_t0_switch_emitter import BOOK_COMP, load_or_build_signal
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from path3_comp_sat_daily_share_ssot import load_book_shares
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path4-soft-0050-mutex-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
TIPGAP_PANEL = ROOT / "repro/fin-sat-tipgap-pred-stagea/outputs/feature_panel.csv"
MARKET = ROOT / "forward/e21/live_market.csv"

CHARTER_ID = "FIN_SAT_PATH4_SOFT_0050_MUTEX_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH4_SOFT_0050_MUTEX_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH4_SOFT_0050_MUTEX_STAGEA_DECISION_PACK"
REGISTER = "0kak"

ETF = "0050"
SOFT_CORE = list(FIN) + list(TEL) + [ETF]
TRAIL = 63
THETAS = (0.005, 0.01, 0.02, 0.05)

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


def _off_weights(w_on: pd.DataFrame) -> pd.DataFrame:
    """SOFT_OFF: zero 0050, renormalize FIN∪TEL mass."""
    w = w_on.copy()
    w[ETF] = 0.0
    ft = list(FIN) + list(TEL)
    s = w[ft].sum(axis=1)
    for c in ft:
        w[c] = np.where(s.to_numpy() > 1e-12, w[c] / s, 0.0)
    # if no FIN/TEL, stay zero (degenerate)
    return w


def _port_rets(w: pd.DataFrame, px: pd.DataFrame) -> pd.Series:
    dates = w.index.intersection(px.index)
    rets = px.pct_change().reindex(dates).fillna(0.0)
    ww = w.reindex(dates).fillna(0.0)
    # T+0 same-bar: today's weights earn today's close-to-close
    pr = (ww * rets.reindex(columns=SOFT_CORE).fillna(0.0)).sum(axis=1)
    return pr.astype(float)


def _trail_rel(r_on: pd.Series, r_off: pd.Series, window: int = TRAIL) -> pd.Series:
    rel = (r_on - r_off).astype(float)
    # product trail of (1+rel) - 1 over trailing window
    x = np.log1p(rel.clip(lower=-0.999999))
    s = x.rolling(window, min_periods=window).sum()
    return np.expm1(s)


def _nav_from_rets(rets: pd.Series) -> pd.DataFrame:
    r = rets.dropna()
    nav = (1.0 + r).cumprod()
    nav = nav / float(nav.iloc[0])
    return pd.DataFrame({"date": r.index.to_numpy(), "nav": nav.to_numpy(dtype=float)})


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


def _arm_verdict(delta: dict[str, Any], tip: dict[str, Any]) -> str:
    held = delta["heldout_2019_plus"]
    sealed = delta["sealed_2023_plus"]
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    if held.get("cagr_lift_pp") is None or sealed.get("mdd_improve_pp") is None:
        return "INCOMPLETE"
    held_ok = float(held["cagr_lift_pp"]) >= HELD_CAGR_FLOOR_PP
    sealed_ok = float(sealed["mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
    tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
    full_ok = float(delta["full"].get("cagr_lift_pp") or 0) > 0
    if held_ok and sealed_ok and tip_ok and full_ok:
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


def _switch_rets(
    r_on: pd.Series,
    r_off: pd.Series,
    off_lead: pd.Series,
) -> pd.Series:
    """T+0: today's OFF_LEAD chooses today's book return."""
    lead = off_lead.reindex(r_on.index).fillna(False).astype(bool)
    return pd.Series(
        np.where(lead.to_numpy(), r_off.to_numpy(), r_on.to_numpy()),
        index=r_on.index,
        dtype=float,
    )


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


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    px = _close_panel(SOFT_CORE)
    w_on = _book_soft_weights(load_book_shares(BOOK_COMP), px)
    w_off = _off_weights(w_on)
    r_on = _port_rets(w_on, px)
    r_off = _port_rets(w_off, px)
    # Align
    idx = r_on.index.intersection(r_off.index)
    r_on, r_off = r_on.reindex(idx), r_off.reindex(idx)
    trail = _trail_rel(r_on, r_off)

    # Optional tipgap overlays (causal l1) — Soft-own, not Path3 trail
    feat = None
    if TIPGAP_PANEL.exists():
        fp = pd.read_csv(TIPGAP_PANEL, parse_dates=["date"])
        fp["date"] = pd.to_datetime(fp["date"]).dt.normalize()
        feat = fp.set_index("date")[
            [c for c in ("r0050_63_l1", "zz08_bear_l1", "trail_drag_l1") if c in fp.columns]
        ]

    # Sanity: Path3 signal present but must NOT feed arms
    _ = load_or_build_signal()

    panel = pd.DataFrame(
        {
            "date": idx,
            "r_on": r_on.to_numpy(),
            "r_off": r_off.to_numpy(),
            "trail_rel_on_off_63": trail.reindex(idx).to_numpy(),
            "w_etf_on": w_on.reindex(idx)[ETF].to_numpy(),
        }
    )
    panel.to_csv(OUT / "mutex_panel.csv", index=False)

    arms: dict[str, pd.Series] = {
        "REF_SOFT_ON": r_on,
        "REF_SOFT_OFF": r_off,
    }
    meta_arms: dict[str, dict[str, Any]] = {
        "REF_SOFT_ON": {"kind": "sticky_on", "n_off_days": 0},
        "REF_SOFT_OFF": {"kind": "sticky_off", "n_off_days": int(len(r_off))},
    }

    for th in THETAS:
        off_lead = trail.reindex(idx) <= -float(th)
        # require trail available
        off_lead = off_lead & trail.reindex(idx).notna()
        name = f"SW_TRAIL_{str(th).replace('.', '')}"
        arms[name] = _switch_rets(r_on, r_off, off_lead)
        meta_arms[name] = {
            "kind": "trail_mutex",
            "theta": th,
            "n_off_days": int(off_lead.fillna(False).sum()),
            "pct_off": round(float(off_lead.fillna(False).mean()), 4),
            "n_flips": int((off_lead.fillna(False) != off_lead.fillna(False).shift(1).fillna(False)).sum()),
        }

    if feat is not None and "r0050_63_l1" in feat.columns:
        lead = feat["r0050_63_l1"].reindex(idx) < 0
        arms["SW_R50NEG"] = _switch_rets(r_on, r_off, lead.fillna(False))
        meta_arms["SW_R50NEG"] = {
            "kind": "r0050_neg",
            "n_off_days": int(lead.fillna(False).sum()),
            "pct_off": round(float(lead.fillna(False).mean()), 4),
        }
    if feat is not None and "zz08_bear_l1" in feat.columns:
        lead = feat["zz08_bear_l1"].reindex(idx).fillna(0).astype(float) > 0.5
        arms["SW_ZZ08"] = _switch_rets(r_on, r_off, lead)
        meta_arms["SW_ZZ08"] = {
            "kind": "zz08_bear",
            "n_off_days": int(lead.sum()),
            "pct_off": round(float(lead.mean()), 4),
        }

    navs = {k: _nav_from_rets(v) for k, v in arms.items()}
    for k, nav in navs.items():
        nav.to_csv(OUT / f"nav_{k}.csv", index=False)

    base = navs["REF_SOFT_ON"]
    bw = _pack(base)
    rows = []
    for arm, nav in navs.items():
        if arm == "REF_SOFT_ON":
            continue
        delta = _delta_windows(bw, _pack(nav))
        tip = _tip(base, nav)
        yearly = yearly_compare(base, nav)
        ret_w = int(sum(1 for r in yearly if r["ret_win"]))
        ret_l = int(sum(1 for r in yearly if not r["ret_win"]))
        v = _arm_verdict(delta, tip)
        rows.append(
            {
                "arm": arm,
                "verdict_vs_on": v,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "yearly_ret_wl": f"{ret_w}-{ret_l}",
                "meta": meta_arms.get(arm, {}),
                "delta": delta,
                "tip": tip,
                "yearly": yearly,
            }
        )

    hit = [r for r in rows if r["verdict_vs_on"] in {"HIT", "HELD_HIT"}]
    if hit:
        champion = max(
            hit,
            key=lambda r: (
                float(r["held_cagr_lift_pp"] or -999),
                float(r["tip_ytd_cagr_lift_pp"] or -999),
                float(r["sealed_mdd_improve_pp"] or -999),
            ),
        )
        pack_verdict = "PATH4_MUTEX_HIT"
    else:
        soft = [r for r in rows if r["verdict_vs_on"] == "SOFT"]
        if soft:
            champion = max(soft, key=lambda r: float(r["held_cagr_lift_pp"] or -999))
            pack_verdict = "PATH4_MUTEX_SOFT"
        else:
            champion = max(rows, key=lambda r: float(r["held_cagr_lift_pp"] or -999))
            pack_verdict = f"PATH4_MUTEX_{champion['verdict_vs_on']}"

    # Correlation check: Path3 trail vs Path4 trail (diagnostic only)
    p3 = load_or_build_signal()
    p3["date"] = pd.to_datetime(p3["date"]).dt.normalize()
    p3i = p3.set_index("date")["trail_rel_63"]
    both = pd.concat(
        [trail.rename("p4"), p3i.rename("p3")], axis=1, join="inner"
    ).dropna()
    corr = float(both["p4"].corr(both["p3"])) if len(both) > 50 else None

    summary = [
        {
            "arm": r["arm"],
            "verdict_vs_on": r["verdict_vs_on"],
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
    pd.DataFrame(summary).to_csv(OUT / "arms_vs_soft_on.csv", index=False)
    pd.DataFrame(champion["yearly"]).to_csv(OUT / "yearly_champion_vs_on.csv", index=False)

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "mech": "PATH4_SOFT_0050_MUTEX",
        "verdict": pack_verdict,
        "fill_timing": "t0",
        "champion_arm": champion["arm"],
        "books": {"on": "SOFT_ON", "off": "SOFT_OFF"},
        "feature_primary": "trail_rel_on_off_63",
        "forbid_path3_inputs": True,
        "corr_p4_trail_vs_p3_trail_rel_63": None if corr is None else round(corr, 4),
        "arms_vs_soft_on": summary,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_on": champion["verdict_vs_on"],
            "delta": champion["delta"],
            "tip": champion["tip"],
            "meta": champion["meta"],
        },
        "note_vs_0kae_0kaj": (
            "0kae–0kaj hitchhiked Path3 flips to move Soft 0050; "
            "this pack is Soft-own ON↔OFF mutex mirroring Path3 structure"
        ),
        "gates": {
            "held_cagr_floor_pp": HELD_CAGR_FLOOR_PP,
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
            "Status: **Stage A — Path4 Soft-0050 mutex** · Soft **KEEP** · "
            "broker **false** · cutover **BLOCKED** · no live",
            f"Register: **{REGISTER}** · mech `PATH4_SOFT_0050_MUTEX`",
            "",
            "## Question",
            "",
            "Can a **Soft-own** mutual-exclusion between Soft-core ``0050 ON`` vs "
            "``0050 OFF`` (causal ``trail_rel_on_off_63``, mirror Path3 SAT_LEAD) "
            "beat sticky Soft-core ON on tip/held — without Path3 flip hitchhiking?",
            "",
            "## Path3 → Path4 map",
            "",
            "| | Path3 | Path4 |",
            "|---|---|---|",
            "| Books | COMP ↔ SAT | SOFT_ON ↔ SOFT_OFF |",
            "| Feature | trail_rel_63 (COMP−SAT) | trail_rel_on_off_63 (ON−OFF) |",
            "| Lead | SAT_LEAD ≤ −θ | OFF_LEAD ≤ −θ |",
            "| Fill | T+0 same-bar | T+0 Soft-core carve paper |",
            "",
            "## Non-goals",
            "",
            "- Path3 flip calendar / P3 ``trail_rel_63`` as inputs · live wire · "
            "0kae–0kaj recon promote · Soft Exact T+1 Soft-wide · broker",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__PATH4_MUTEX__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "mech": "PATH4_SOFT_0050_MUTEX",
                "soft_keep": True,
                "broker": False,
                "cutover_blocked": True,
                "forbid_path3_inputs": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    def _fmt(r: dict) -> str:
        return (
            f"| {r['arm']} | {r['verdict_vs_on']} | {r['held_cagr_lift_pp']} | "
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
            f"Register: **{REGISTER}** · corr(P4 trail, P3 trail)=**{None if corr is None else round(corr, 3)}**",
            "",
            "## Arms vs sticky SOFT_ON (T+0 Soft-core carve)",
            "",
            "| Arm | vs ON | held | full | sealed MDD↑ | tipY | tip1y | ret W–L |",
            "|---|---|---:|---:|---:|---:|---:|---|",
            *[_fmt(r) for r in summary],
            "",
            f"## Champion `{champion['arm']}` yearly vs SOFT_ON",
            "",
            "| Year | ON ret% | Chal ret% | Ret lift pp |",
            "|---:|---:|---:|---:|",
            *[
                f"| {y['year']} | {y['ret_keep_pct']:.2f} | {y['ret_chal_pct']:.2f} | "
                f"{y['ret_lift_pp']:+.2f} |"
                for y in champion["yearly"]
            ],
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path4_soft_0050_mutex_stagea.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{pack_verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = []
    if pack_verdict == "PATH4_MUTEX_HIT":
        next_steps.append(
            f"Stage B: Soft Exact T+1 / e16 clip-book dual for `{champion['arm']}` — still no live"
        )
        next_steps.append("Optional θ densify / OFF book = DEF sleeve (not zero-0050 only)")
    elif pack_verdict == "PATH4_MUTEX_SOFT":
        next_steps.append("Borderline — tip/held disposition before any Stage B")
    else:
        next_steps.append(
            "ON↔OFF Soft-core mutex no promote; try richer Path4 books (DEF sleeve / HI-LO ETF clips)"
        )
    next_steps.append("0kae–0kaj remain Path3-hitchhike track — separate from Path4 mutex")
    next_steps.append("Soft KEEP · Path3 keep_0050=True · no live")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{pack_verdict}__NO_LIVE",
        "verdict": pack_verdict,
        "register": REGISTER,
        "mech": "PATH4_SOFT_0050_MUTEX",
        "champion_arm": champion["arm"],
        "corr_p4_vs_p3_trail": None if corr is None else round(corr, 4),
        "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
        "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
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
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · mech **PATH4_SOFT_0050_MUTEX**",
            "",
            "## Champion vs sticky SOFT_ON",
            "",
            f"- held CAGR lift: **{champion['held_cagr_lift_pp']}** pp",
            f"- full CAGR lift: **{champion['full_cagr_lift_pp']}** pp",
            f"- sealed MDD improve: **{champion['sealed_mdd_improve_pp']}** pp",
            f"- tipY / tip1y: **{champion['tip_ytd_cagr_lift_pp']}** / "
            f"**{champion['tip_1y_cagr_lift_pp']}**",
            f"- corr(P4 trail, P3 trail): **{None if corr is None else round(corr, 3)}**",
            "",
            "## Disposition",
            "",
            "- Soft-own ON↔OFF mutex (not Path3 flip hitchhike).",
            "- Live Soft / Path3 unchanged · no wire.",
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
                "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
                "corr_p4_vs_p3_trail": None if corr is None else round(corr, 4),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
