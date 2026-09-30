#!/usr/bin/env python3
"""Path4 Soft-0050 extreme OFF second book (0kan) — paper only · T+0 Soft-core carve.

Parent 0kak: Soft-own ON↔OFF renorm ``PATH4_MUTEX_HIT`` / ``SW_TRAIL_001`` held+0.40.

**Question:** Does a more extreme OFF book beat sticky Soft-core ON (and Stage A
renorm parent) under the same trail-mutex structure?

Extreme OFF books (vs Stage A zero-0050 + FIN∪TEL renormalize)
--------------------------------------------------------------
- ``OFF_CASH_ETF`` — park 0050 mass in cash (earn 0); FIN∪TEL keep ON absolute
  weights (no renorm → cash drag = former ETF share)
- ``OFF_FULL_CASH`` — Soft-core fully in cash (earn 0) when OFF_LEAD
- ``OFF_RENORM`` — Stage A control (0050=0, renorm FIN∪TEL)

θ densify grid vs Stage A. Soft KEEP · broker false · cutover BLOCKED · no live ·
**forbid Path3 ``trail_rel_63`` / P3 flip calendar as inputs**.
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
REPRO = ROOT / "repro" / "fin-sat-path4-soft-0050-mutex-extreme-off"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
PARENT_A = ROOT / "repro/fin-sat-path4-soft-0050-mutex-stagea/outputs"
TIPGAP_PANEL = ROOT / "repro/fin-sat-tipgap-pred-stagea/outputs/feature_panel.csv"
MARKET = ROOT / "forward/e21/live_market.csv"

CHARTER_ID = "FIN_SAT_PATH4_SOFT_0050_MUTEX_EXTREME_OFF_CHARTER"
SCREEN_ID = "FIN_SAT_PATH4_SOFT_0050_MUTEX_EXTREME_OFF_SCREEN"
DECISION_ID = "FIN_SAT_PATH4_SOFT_0050_MUTEX_EXTREME_OFF_DECISION_PACK"
REGISTER = "0kan"
PARENT_REGISTER = "0kak"

ETF = "0050"
SOFT_CORE = list(FIN) + list(TEL) + [ETF]
TRAIL = 63
# densify vs Stage A (0.005, 0.01, 0.02, 0.05)
THETAS = (0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02, 0.05)

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


def _off_renorm_weights(w_on: pd.DataFrame) -> pd.DataFrame:
    """Stage A OFF: zero 0050, renormalize FIN∪TEL mass."""
    w = w_on.copy()
    w[ETF] = 0.0
    ft = list(FIN) + list(TEL)
    s = w[ft].sum(axis=1)
    for c in ft:
        w[c] = np.where(s.to_numpy() > 1e-12, w[c] / s, 0.0)
    return w


def _off_cash_etf_weights(w_on: pd.DataFrame) -> pd.DataFrame:
    """Extreme OFF: park 0050 in cash (earn 0); keep FIN∪TEL absolute ON weights."""
    w = w_on.copy()
    w[ETF] = 0.0
    return w


def _port_rets(w: pd.DataFrame, px: pd.DataFrame) -> pd.Series:
    dates = w.index.intersection(px.index)
    rets = px.pct_change().reindex(dates).fillna(0.0)
    ww = w.reindex(dates).fillna(0.0)
    # T+0 same-bar: today's weights earn today's close-to-close
    # Cash residual (1 - sum(w)) earns 0 implicitly.
    pr = (ww * rets.reindex(columns=SOFT_CORE).fillna(0.0)).sum(axis=1)
    return pr.astype(float)


def _trail_rel(r_on: pd.Series, r_off: pd.Series, window: int = TRAIL) -> pd.Series:
    rel = (r_on - r_off).astype(float)
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


def _switch_rets(r_on: pd.Series, r_off: pd.Series, off_lead: pd.Series) -> pd.Series:
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


def _theta_tag(th: float) -> str:
    s = f"{th:.4f}".rstrip("0").rstrip(".")
    return s.replace(".", "")


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    parent_held = None
    parent_arm = None
    parent_path = PARENT_A / "screen.json"
    if parent_path.exists():
        ps = json.loads(parent_path.read_text(encoding="utf-8"))
        parent_arm = ps.get("champion_arm")
        parent_held = (
            ((ps.get("champion") or {}).get("delta") or {})
            .get("heldout_2019_plus", {})
            .get("cagr_lift_pp")
        )

    px = _close_panel(SOFT_CORE)
    w_on = _book_soft_weights(load_book_shares(BOOK_COMP), px)
    w_renorm = _off_renorm_weights(w_on)
    w_cash_etf = _off_cash_etf_weights(w_on)

    r_on = _port_rets(w_on, px)
    r_renorm = _port_rets(w_renorm, px)
    r_cash_etf = _port_rets(w_cash_etf, px)
    idx = r_on.index.intersection(r_renorm.index).intersection(r_cash_etf.index)
    r_on = r_on.reindex(idx)
    r_renorm = r_renorm.reindex(idx)
    r_cash_etf = r_cash_etf.reindex(idx)
    r_full_cash = pd.Series(0.0, index=idx, dtype=float)

    trail_renorm = _trail_rel(r_on, r_renorm)
    trail_cash_etf = _trail_rel(r_on, r_cash_etf)
    trail_full_cash = _trail_rel(r_on, r_full_cash)

    feat = None
    if TIPGAP_PANEL.exists():
        fp = pd.read_csv(TIPGAP_PANEL, parse_dates=["date"])
        fp["date"] = pd.to_datetime(fp["date"]).dt.normalize()
        feat = fp.set_index("date")[
            [c for c in ("r0050_63_l1", "zz08_bear_l1", "trail_drag_l1") if c in fp.columns]
        ]

    _ = load_or_build_signal()  # present but must NOT feed arms

    panel = pd.DataFrame(
        {
            "date": idx,
            "r_on": r_on.to_numpy(),
            "r_off_renorm": r_renorm.to_numpy(),
            "r_off_cash_etf": r_cash_etf.to_numpy(),
            "r_off_full_cash": r_full_cash.to_numpy(),
            "trail_rel_on_renorm_63": trail_renorm.reindex(idx).to_numpy(),
            "trail_rel_on_cash_etf_63": trail_cash_etf.reindex(idx).to_numpy(),
            "trail_rel_on_full_cash_63": trail_full_cash.reindex(idx).to_numpy(),
            "w_etf_on": w_on.reindex(idx)[ETF].to_numpy(),
            "w_sum_cash_etf": w_cash_etf.reindex(idx).sum(axis=1).to_numpy(),
        }
    )
    panel.to_csv(OUT / "mutex_panel.csv", index=False)

    arms: dict[str, pd.Series] = {
        "REF_SOFT_ON": r_on,
        "REF_OFF_RENORM": r_renorm,
        "REF_OFF_CASH_ETF": r_cash_etf,
        "REF_OFF_FULL_CASH": r_full_cash,
    }
    meta_arms: dict[str, dict[str, Any]] = {
        "REF_SOFT_ON": {"kind": "sticky_on", "off_book": None, "n_off_days": 0},
        "REF_OFF_RENORM": {
            "kind": "sticky_off",
            "off_book": "OFF_RENORM",
            "n_off_days": int(len(r_renorm)),
        },
        "REF_OFF_CASH_ETF": {
            "kind": "sticky_off",
            "off_book": "OFF_CASH_ETF",
            "n_off_days": int(len(r_cash_etf)),
        },
        "REF_OFF_FULL_CASH": {
            "kind": "sticky_off",
            "off_book": "OFF_FULL_CASH",
            "n_off_days": int(len(r_full_cash)),
        },
    }

    book_specs = (
        ("RENORM", r_renorm, trail_renorm),
        ("CASH_ETF", r_cash_etf, trail_cash_etf),
        ("FULL_CASH", r_full_cash, trail_full_cash),
    )
    for book_name, r_off, trail in book_specs:
        for th in THETAS:
            off_lead = trail.reindex(idx) <= -float(th)
            off_lead = off_lead & trail.reindex(idx).notna()
            name = f"SW_{book_name}_{_theta_tag(th)}"
            arms[name] = _switch_rets(r_on, r_off, off_lead)
            meta_arms[name] = {
                "kind": "trail_mutex",
                "off_book": f"OFF_{book_name}",
                "theta": th,
                "n_off_days": int(off_lead.fillna(False).sum()),
                "pct_off": round(float(off_lead.fillna(False).mean()), 4),
                "n_flips": int(
                    (
                        off_lead.fillna(False)
                        != off_lead.fillna(False).shift(1).fillna(False)
                    ).sum()
                ),
            }

    if feat is not None and "r0050_63_l1" in feat.columns:
        lead = feat["r0050_63_l1"].reindex(idx) < 0
        for book_name, r_off, _trail in (
            ("CASH_ETF", r_cash_etf, trail_cash_etf),
            ("FULL_CASH", r_full_cash, trail_full_cash),
        ):
            name = f"SW_{book_name}_R50NEG"
            arms[name] = _switch_rets(r_on, r_off, lead.fillna(False))
            meta_arms[name] = {
                "kind": "r0050_neg",
                "off_book": f"OFF_{book_name}",
                "n_off_days": int(lead.fillna(False).sum()),
                "pct_off": round(float(lead.fillna(False).mean()), 4),
            }
    if feat is not None and "zz08_bear_l1" in feat.columns:
        lead = feat["zz08_bear_l1"].reindex(idx).fillna(0).astype(float) > 0.5
        for book_name, r_off, _trail in (
            ("CASH_ETF", r_cash_etf, trail_cash_etf),
            ("FULL_CASH", r_full_cash, trail_full_cash),
        ):
            name = f"SW_{book_name}_ZZ08"
            arms[name] = _switch_rets(r_on, r_off, lead)
            meta_arms[name] = {
                "kind": "zz08_bear",
                "off_book": f"OFF_{book_name}",
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
        held_pp = delta["heldout_2019_plus"]["cagr_lift_pp"]
        beats_parent = (
            None
            if parent_held is None or held_pp is None
            else bool(float(held_pp) > float(parent_held))
        )
        rows.append(
            {
                "arm": arm,
                "verdict_vs_on": v,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": held_pp,
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "yearly_ret_wl": f"{ret_w}-{ret_l}",
                "beats_parent_held": beats_parent,
                "meta": meta_arms.get(arm, {}),
                "delta": delta,
                "tip": tip,
                "yearly": yearly,
            }
        )

    # Prefer extreme OFF books (CASH_ETF / FULL_CASH) among HITs; else any HIT
    extreme_hit = [
        r
        for r in rows
        if r["verdict_vs_on"] in {"HIT", "HELD_HIT"}
        and (r.get("meta") or {}).get("off_book") in {"OFF_CASH_ETF", "OFF_FULL_CASH"}
        and (r.get("meta") or {}).get("kind") == "trail_mutex"
    ]
    any_hit = [r for r in rows if r["verdict_vs_on"] in {"HIT", "HELD_HIT"}]

    def _rank_key(r: dict) -> tuple:
        return (
            float(r["held_cagr_lift_pp"] or -999),
            float(r["tip_ytd_cagr_lift_pp"] or -999),
            float(r["sealed_mdd_improve_pp"] or -999),
        )

    if extreme_hit:
        champion = max(extreme_hit, key=_rank_key)
        pack_verdict = "PATH4_EXTREME_HIT"
    elif any_hit:
        champion = max(any_hit, key=_rank_key)
        # HIT only via renorm control → not extreme promote
        pack_verdict = "PATH4_EXTREME_RENORM_ONLY"
    else:
        soft = [r for r in rows if r["verdict_vs_on"] == "SOFT"]
        if soft:
            champion = max(soft, key=lambda r: float(r["held_cagr_lift_pp"] or -999))
            pack_verdict = "PATH4_EXTREME_SOFT"
        else:
            champion = max(rows, key=lambda r: float(r["held_cagr_lift_pp"] or -999))
            pack_verdict = f"PATH4_EXTREME_{champion['verdict_vs_on']}"

    # Diagnostic: Path3 trail vs cash-etf trail
    p3 = load_or_build_signal()
    p3["date"] = pd.to_datetime(p3["date"]).dt.normalize()
    p3i = p3.set_index("date")["trail_rel_63"]
    both = pd.concat(
        [trail_cash_etf.rename("p4"), p3i.rename("p3")], axis=1, join="inner"
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
            "beats_parent_held": r["beats_parent_held"],
            **{f"meta_{k}": v for k, v in (r["meta"] or {}).items()},
        }
        for r in rows
    ]
    pd.DataFrame(summary).to_csv(OUT / "arms_vs_soft_on.csv", index=False)
    pd.DataFrame(champion["yearly"]).to_csv(OUT / "yearly_champion_vs_on.csv", index=False)

    beats_parent = champion.get("beats_parent_held")
    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parent_register": PARENT_REGISTER,
        "parent_champion_arm": parent_arm,
        "parent_held_cagr_lift_pp": parent_held,
        "mech": "PATH4_SOFT_0050_MUTEX_EXTREME_OFF",
        "verdict": pack_verdict,
        "fill_timing": "t0",
        "champion_arm": champion["arm"],
        "books": {
            "on": "SOFT_ON",
            "off_extreme": ["OFF_CASH_ETF", "OFF_FULL_CASH"],
            "off_control": "OFF_RENORM",
        },
        "feature_primary": "trail_rel_on_<off>_63",
        "forbid_path3_inputs": True,
        "corr_p4_cash_etf_trail_vs_p3_trail_rel_63": None
        if corr is None
        else round(corr, 4),
        "arms_vs_soft_on": summary,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_on": champion["verdict_vs_on"],
            "beats_parent_held": beats_parent,
            "delta": champion["delta"],
            "tip": champion["tip"],
            "meta": champion["meta"],
        },
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
            "Status: **Path4 Soft-0050 extreme OFF second book** · Soft **KEEP** · "
            "broker **false** · cutover **BLOCKED** · no live",
            f"Register: **{REGISTER}** · Parent: **{PARENT_REGISTER}** "
            f"`PATH4_MUTEX_HIT` / `{parent_arm or 'SW_TRAIL_001'}`",
            "",
            "## Question",
            "",
            "Does an **extreme OFF** book (cash-park 0050 mass, or Soft-core full cash) "
            "under Soft-own trail-mutex beat sticky Soft-core ON — and improve on Stage A "
            "renorm OFF — without Path3 flip hitchhiking?",
            "",
            "## Books",
            "",
            "- ``SOFT_ON`` — Soft-core incl. 0050 (sticky baseline)",
            "- ``OFF_CASH_ETF`` — 0050→cash (earn 0); FIN∪TEL keep ON absolute weights",
            "- ``OFF_FULL_CASH`` — Soft-core fully cash (earn 0)",
            "- ``OFF_RENORM`` — Stage A control (0050=0, renorm FIN∪TEL)",
            "",
            "## Non-goals",
            "",
            "- Path3 flip / P3 trail inputs · live wire · Soft Exact T+1 Soft-wide · "
            "broker · Stage B HI/DEF clip promote",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__PATH4_EXTREME__NO_LIVE`",
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
                "parent_register": PARENT_REGISTER,
                "mech": "PATH4_SOFT_0050_MUTEX_EXTREME_OFF",
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
            f"{r['yearly_ret_wl']} | {r['beats_parent_held']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`** · fill=`t0`",
            f"Register: **{REGISTER}** · Parent held=**{parent_held}** "
            f"(`{parent_arm}`) · corr(P4 cash-etf, P3)=**"
            f"{None if corr is None else round(corr, 3)}**",
            "",
            "## Arms vs sticky SOFT_ON (T+0 Soft-core carve)",
            "",
            "| Arm | vs ON | held | full | sealed MDD↑ | tipY | tip1y | ret W–L | >parent |",
            "|---|---|---:|---:|---:|---:|---:|---|---|",
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
            "Repro: `PYTHONPATH=scripts python3 "
            "scripts/fin_sat_path4_soft_0050_mutex_extreme_off.py`",
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
    if pack_verdict == "PATH4_EXTREME_HIT":
        off_book = (champion.get("meta") or {}).get("off_book")
        if off_book == "OFF_FULL_CASH":
            next_steps.append(
                f"Human disposition: `{champion['arm']}` is Soft-core full-cash "
                "risk-off (broader than 0050-only) vs keep Stage A renorm primary "
                "— still no live"
            )
            next_steps.append(
                "If carry FULL_CASH: optional Stage C coexist / e21 smoke + "
                "lag-1 sensitivity (same-bar T+0 pack)"
            )
        elif beats_parent:
            next_steps.append(
                f"Carry `{champion['arm']}` — extreme OFF beats Stage A parent held; "
                "optional Stage C coexist / e21 smoke — still no live"
            )
        else:
            next_steps.append(
                f"HIT via extreme OFF but held ≤ Stage A parent (`{parent_arm}` "
                f"held={parent_held}) — keep Stage A renorm as primary; "
                "use extreme only if tip/MDD dominate"
            )
    elif pack_verdict == "PATH4_EXTREME_RENORM_ONLY":
        next_steps.append(
            "Extreme cash books no HIT; Stage A renorm OFF remains best Soft-own OFF"
        )
    elif pack_verdict == "PATH4_EXTREME_SOFT":
        next_steps.append("Borderline — tip/held disposition before any promote")
    else:
        next_steps.append(
            "Extreme OFF mutex no promote; Soft-core ON sticky / Stage A renorm KEEP"
        )
    next_steps.append("0kal HI/DEF clip Stage B remains separate Path4 richer-book track")
    next_steps.append("Soft KEEP · Path3 keep_0050=True · no live")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{pack_verdict}__NO_LIVE",
        "verdict": pack_verdict,
        "register": REGISTER,
        "parent_register": PARENT_REGISTER,
        "parent_champion_arm": parent_arm,
        "parent_held_cagr_lift_pp": parent_held,
        "mech": "PATH4_SOFT_0050_MUTEX_EXTREME_OFF",
        "champion_arm": champion["arm"],
        "beats_parent_held": beats_parent,
        "corr_p4_cash_etf_vs_p3_trail": None if corr is None else round(corr, 4),
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
            f"Register: **{REGISTER}** · Parent: **{PARENT_REGISTER}**",
            "",
            "## Champion vs sticky SOFT_ON",
            "",
            f"- held CAGR lift: **{champion['held_cagr_lift_pp']}** pp",
            f"- full CAGR lift: **{champion['full_cagr_lift_pp']}** pp",
            f"- sealed MDD improve: **{champion['sealed_mdd_improve_pp']}** pp",
            f"- tipY / tip1y: **{champion['tip_ytd_cagr_lift_pp']}** / "
            f"**{champion['tip_1y_cagr_lift_pp']}**",
            f"- beats Stage A parent held: **{beats_parent}** "
            f"(parent `{parent_arm}` held={parent_held})",
            f"- corr(P4 cash-etf trail, P3 trail): **"
            f"{None if corr is None else round(corr, 3)}**",
            "",
            "## Disposition",
            "",
            "- Soft-own extreme OFF second book (cash-park 0050 / full cash) · "
            "not Path3 hitchhike.",
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
                "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
                "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
                "beats_parent_held": beats_parent,
                "parent_held_cagr_lift_pp": parent_held,
                "corr_p4_cash_etf_vs_p3_trail": None if corr is None else round(corr, 4),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
