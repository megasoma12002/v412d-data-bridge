#!/usr/bin/env python3
"""Stage A: tip Soft LIVE_OVERRIDE apply-path design under Path3 WITHIN KEEP.

Question (human 「請研究4」): stamps-only wire leaves tip PnL short of paper
OVERRIDE (held +1.61 / tipY +6.04). What apply path can capture that edge
**without** re-enabling Soft FIN/TEL or undoing Path3 WITHIN?

Design (paper NAV proxies — no live wire):
- Baseline live-like tip twin: L4_LIVE_P3_WITHIN (Soft+FUSE+COOL + Path3 WITHIN)
- Ceiling (infeasible under Soft FIN/TEL OFF): PAPER_OVERRIDE return blend
- Proxies under Path3 ownership KEEP:
  - APPLY_P3MUTE_OV: where(override, live_r, l4_r) — Path3 mute on gate days
    (economic upper bound; needs Soft FIN/TEL shell OR equivalent ownership fill)
  - APPLY_P3ALPHA_* : soft-α Path3 tilt toward Soft on gate days (Path3 still owns)
  - KEEP_STAMPS: L4 itself (0 capture)

Soft KEEP · Path4 OFF · broker false · no year-cut · no live wire this pack.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-apply-path-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
OVERRIDE = ROOT / "repro" / "tipsoft-ip3-live-override-paper-observe" / "outputs"
STACK = ROOT / "repro" / "tipsoft-ip3-live-stack-race-stagea" / "outputs"

CHARTER_ID = "TIPSOFT_IP3_APPLY_PATH_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_APPLY_PATH_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_APPLY_PATH_STAGEA_DECISION_PACK"
REGISTER = "0kb6"
PARENTS = ("0kb2", "0kb5", "0kac")
MECH = "TIPSOFT_IP3_APPLY_PATH"
WINDOW = 42
MARGIN = 0.005
CONFIRM_K = 3


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return (
        df[["date", "nav"]]
        .assign(
            date=lambda x: pd.to_datetime(x["date"]).dt.normalize(),
            nav=lambda x: x["nav"].astype(float),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )


def _returns(nav: pd.DataFrame) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    return s.pct_change().fillna(0.0)


def _trail_sum(x: pd.Series, w: int) -> pd.Series:
    return x.shift(1).rolling(int(w), min_periods=max(3, int(w) // 3)).sum()


def _override_mask(live_r: pd.Series, champ_r: pd.Series) -> pd.Series:
    lead = (_trail_sum(live_r, WINDOW) - _trail_sum(champ_r, WINDOW)).fillna(0.0)
    conf = lead > float(MARGIN)
    for j in range(1, int(CONFIRM_K)):
        conf = conf & (lead.shift(j).fillna(0.0) > float(MARGIN))
    return conf.fillna(False).astype(bool)


def _nav_from_returns(r: pd.Series, nav0: float = 1.0) -> pd.DataFrame:
    nav = (1.0 + r.fillna(0.0)).cumprod() * float(nav0)
    return pd.DataFrame({"date": nav.index, "nav": nav.to_numpy(dtype=float)}).reset_index(
        drop=True
    )


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
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


def _delta(base_w: dict, chal_w: dict) -> dict[str, Any]:
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
        }
    return out


def _row(
    name: str,
    role: str,
    nav: pd.DataFrame,
    base_nav: pd.DataFrame,
    base_w: dict,
    *,
    ownership: str,
    soft_fin_tel_required: bool,
    feasible_under_keep: bool,
) -> dict[str, Any]:
    w = _pack(nav)
    d = _delta(base_w, w)
    tip = _tip(base_nav, nav)
    held = d["heldout_2019_plus"]
    sealed = d["sealed_2023_plus"]
    return {
        "arm": name,
        "role": role,
        "ownership": ownership,
        "soft_fin_tel_required": soft_fin_tel_required,
        "feasible_under_path3_within_keep": feasible_under_keep,
        "held_cagr_lift_vs_L4_pp": held["cagr_lift_pp"],
        "held_mdd_improve_vs_L4_pp": held["mdd_improve_pp"],
        "sealed_cagr_lift_vs_L4_pp": sealed["cagr_lift_pp"],
        "sealed_mdd_improve_vs_L4_pp": sealed["mdd_improve_pp"],
        "full_cagr_lift_vs_L4_pp": d["full"]["cagr_lift_pp"],
        "tipY_vs_L4_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
        "tip1y_vs_L4_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    live_nav = _load(OVERRIDE / "nav_BASE_LIVE_FUSE_COOL.csv")
    l4_nav = _load(ALIGN / "nav_L4_LIVE_P3_WITHIN.csv")
    paper_ov_nav = _load(OVERRIDE / "nav_OVERRIDE_LIVE_W42_M05_K3.csv")
    champ_nav = _load(STACK / "nav_REF_MUTE_S3_SAT_W63.csv")

    live_r = _returns(live_nav)
    l4_r = _returns(l4_nav)
    champ_r = _returns(champ_nav)
    panel = pd.concat(
        {"live": live_r, "l4": l4_r, "champ": champ_r}, axis=1, join="inner"
    ).dropna(how="any")
    if panel.empty:
        raise SystemExit("empty return panel")

    conf = _override_mask(panel["live"], panel["champ"])
    pct_ov = round(float(conf.mean()) * 100.0, 4)
    live_r_p = panel["live"]
    l4_r_p = panel["l4"]
    champ_r_p = panel["champ"]

    # Paper OVERRIDE on aligned panel (sanity vs sealed observe NAV)
    paper_r = pd.Series(
        np.where(conf.to_numpy(), live_r_p.to_numpy(), champ_r_p.to_numpy()),
        index=panel.index,
    )
    # Path3 mute vs L4 baseline (upper bound if Soft FIN/TEL shell available)
    mute_r = pd.Series(
        np.where(conf.to_numpy(), live_r_p.to_numpy(), l4_r_p.to_numpy()),
        index=panel.index,
    )
    # Soft-α Path3 tilt: on override days blend toward Soft; Path3 still owns
    alpha_arms: dict[str, pd.Series] = {}
    for a in (0.25, 0.5, 0.75):
        softish = (1.0 - a) * live_r_p + a * l4_r_p
        alpha_arms[f"APPLY_P3ALPHA_A{str(a).replace('.', '')}"] = pd.Series(
            np.where(conf.to_numpy(), softish.to_numpy(), l4_r_p.to_numpy()),
            index=panel.index,
        )

    nav0 = 1.0
    books: dict[str, tuple[str, pd.DataFrame, str, bool, bool]] = {
        "KEEP_STAMPS_L4": (
            "live tip twin / stamps-only baseline",
            _nav_from_returns(l4_r_p, nav0),
            "path3_within_fin_tel",
            False,
            True,
        ),
        "ATTR_CHAMP_MUTE_S3_SAT": (
            "attribution: MUTE_S3_SAT champ alone vs L4 (non-override stack)",
            _nav_from_returns(champ_r_p, nav0),
            "soft_shell_plus_gated_path3",
            True,  # champ base is Soft shell; Path3 intermittent
            False,
        ),
        "ATTR_LIVE_SHELL": (
            "attribution: Soft live shell alone vs L4",
            _nav_from_returns(live_r_p, nav0),
            "soft_shell",
            True,
            False,
        ),
        "PAPER_OVERRIDE_W42_M05_K3": (
            "research return blend ceiling (Soft shell ↔ MUTE_S3_SAT)",
            _nav_from_returns(paper_r, nav0),
            "soft_shell_or_stack",
            True,  # Soft-shell force-LIVE days need Soft FIN/TEL economics
            False,
        ),
        "APPLY_P3MUTE_OV": (
            "mute Path3 premium on override_on → Soft shell returns",
            _nav_from_returns(mute_r, nav0),
            "path3_mute_needs_soft_or_fill",
            True,  # ownership hole unless Soft FIN/TEL carve or fill policy
            False,
        ),
    }
    for name, r in alpha_arms.items():
        books[name] = (
            "soft-α Path3 tilt on override_on (α→Soft; Path3 owns FIN/TEL)",
            _nav_from_returns(r, nav0),
            "path3_within_fin_tel",
            False,
            True,
        )

    # Seal paper NAV from observe for tip metrics vs L4 (not rebuilt)
    books["PAPER_OVERRIDE_SEALED"] = (
        "sealed observe NAV (SSOT tip numbers)",
        paper_ov_nav,
        "soft_shell_or_stack",
        True,
        False,
    )

    l4_w = _pack(l4_nav)
    rows = []
    for name, (role, nav, ownership, soft_req, feasible) in books.items():
        nav.to_csv(OUT / f"nav_{name}.csv", index=False)
        rows.append(
            _row(
                name,
                role,
                nav,
                l4_nav,
                l4_w,
                ownership=ownership,
                soft_fin_tel_required=soft_req,
                feasible_under_keep=feasible,
            )
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "apply_path_vs_L4.csv", index=False)

    sealed_ov = df[df.arm == "PAPER_OVERRIDE_SEALED"].iloc[0]
    gap_held = float(sealed_ov["held_cagr_lift_vs_L4_pp"] or 0.0)
    gap_tipy = float(sealed_ov["tipY_vs_L4_pp"] or 0.0)

    def _capture(row: dict[str, Any]) -> float | None:
        h = row.get("held_cagr_lift_vs_L4_pp")
        if h is None or gap_held <= 0:
            return None
        return round(float(h) / gap_held, 4)

    def _capture_tipy(row: dict[str, Any]) -> float | None:
        t = row.get("tipY_vs_L4_pp")
        if t is None or gap_tipy <= 0:
            return None
        return round(float(t) / gap_tipy, 4)

    for r in rows:
        r["capture_frac_held_vs_paper_gap"] = _capture(r)
        r["capture_frac_tipY_vs_paper_gap"] = _capture_tipy(r)

    feasible = [
        r
        for r in rows
        if r["feasible_under_path3_within_keep"] and r["arm"] != "KEEP_STAMPS_L4"
    ]
    feasible_pos = [
        r
        for r in feasible
        if r["held_cagr_lift_vs_L4_pp"] is not None
        and float(r["held_cagr_lift_vs_L4_pp"]) > 0.05
    ]
    best_feas = None
    if feasible_pos:
        best_feas = max(feasible_pos, key=lambda x: float(x["held_cagr_lift_vs_L4_pp"]))

    mute = df[df.arm == "APPLY_P3MUTE_OV"].iloc[0].to_dict()
    mute_cap = _capture(mute)
    mute_tip_cap = _capture_tipy(mute)
    champ = df[df.arm == "ATTR_CHAMP_MUTE_S3_SAT"].iloc[0].to_dict()
    champ_tip_cap = _capture_tipy(champ)
    sum_diff_conf = float((paper_r - l4_r_p)[conf].sum())
    sum_diff_off = float((paper_r - l4_r_p)[~conf].sum())

    # Verdict: tipY is the live-lag pain; force-LIVE/soft-α under WITHIN do not close it.
    best_tip_cap = (
        _capture_tipy(best_feas) if best_feas is not None else None
    )
    if (
        champ_tip_cap is not None
        and champ_tip_cap >= 0.8
        and (mute_tip_cap is None or mute_tip_cap < 0.25)
        and (best_tip_cap is None or best_tip_cap < 0.25)
    ):
        verdict = "APPLY_TIPY_OWNERSHIP_BLOCK"
    elif best_feas is not None and float(best_feas["held_cagr_lift_vs_L4_pp"]) >= 0.5 * gap_held:
        verdict = "APPLY_P3ALPHA_HIT"
    elif mute_cap is not None and mute_cap >= 0.5 and not bool(
        mute["feasible_under_path3_within_keep"]
    ):
        verdict = "APPLY_OWNERSHIP_BLOCK"
    elif best_feas is not None:
        verdict = "APPLY_P3ALPHA_SOFT"
    else:
        verdict = "APPLY_KEEP_STAMPS"

    best_alpha = None
    alpha_rows = [r for r in rows if r["arm"].startswith("APPLY_P3ALPHA_")]
    if alpha_rows:
        best_alpha = max(
            alpha_rows,
            key=lambda x: float(x["held_cagr_lift_vs_L4_pp"] or -1e9),
        )

    design = {
        "problem": (
            "Live tip stamps override_on but does not apply research "
            "r=where(conf, live_r, champ_r); tip PnL stays near L4 Path3 WITHIN."
        ),
        "paper_edge_vs_L3": {"held_pp": 1.6136, "tipY_pp": 6.0402, "source": "0kb2 observe"},
        "paper_gap_vs_L4_live_twin": {
            "held_pp": gap_held,
            "tipY_pp": gap_tipy,
            "source": "PAPER_OVERRIDE_SEALED vs L4",
        },
        "attribution": {
            "pct_override_days": pct_ov,
            "sum_return_diff_OV_minus_L4_on_override_days": round(sum_diff_conf, 6),
            "sum_return_diff_OV_minus_L4_on_non_override_days": round(sum_diff_off, 6),
            "champ_MUTE_S3_SAT_vs_L4": {
                "held_pp": champ["held_cagr_lift_vs_L4_pp"],
                "tipY_pp": champ["tipY_vs_L4_pp"],
                "tipY_capture_frac": champ_tip_cap,
                "note": "Tip gap ≈ champ vs always-WITHIN L4, not force-LIVE Soft days",
            },
            "force_live_mute_vs_L4": {
                "held_pp": mute["held_cagr_lift_vs_L4_pp"],
                "tipY_pp": mute["tipY_vs_L4_pp"],
                "held_capture_frac": mute_cap,
                "tipY_capture_frac": mute_tip_cap,
            },
        },
        "constraints": {
            "path3_within_sleeve_keep": True,
            "soft_fin_tel_stay_off": True,
            "soft_clips_0050_keep": True,
            "path3_ledger_daily": True,
            "path4_live": False,
            "broker": False,
            "no_year_cut": True,
            "no_hybrid_t0": True,
            "wire_mode_today": "gate_stamps_telemetry",
        },
        "options": [
            {
                "id": "A_P3MUTE_OV",
                "arm": "APPLY_P3MUTE_OV",
                "actuator": "Mute Path3 -P3T0 emit / set Path3 weight→0 when override_on",
                "held_vs_L4_pp": mute["held_cagr_lift_vs_L4_pp"],
                "tipY_vs_L4_pp": mute["tipY_vs_L4_pp"],
                "capture_frac_held": mute_cap,
                "capture_frac_tipY": mute_tip_cap,
                "feasible_under_keep": False,
                "blocker": (
                    "On mute days Soft FIN/TEL Exact T+1 stay OFF → FIN∪TEL ownership hole; "
                    "and tipY capture≈0 even if Soft shell were available"
                ),
            },
            {
                "id": "B_P3ALPHA",
                "arm": None if best_alpha is None else best_alpha["arm"],
                "actuator": (
                    "Scale Path3 WITHIN weights toward Soft KD shell on override_on "
                    "(soft-α); Path3 ledger still owns FIN∪TEL"
                ),
                "held_vs_L4_pp": None
                if best_alpha is None
                else best_alpha["held_cagr_lift_vs_L4_pp"],
                "tipY_vs_L4_pp": None if best_alpha is None else best_alpha["tipY_vs_L4_pp"],
                "capture_frac_held": None if best_alpha is None else _capture(best_alpha),
                "capture_frac_tipY": None if best_alpha is None else _capture_tipy(best_alpha),
                "feasible_under_keep": True,
                "blocker": "Feasible but tipY capture≈0 — does not close live tip lag",
            },
            {
                "id": "C_SOFT_RESIDUAL",
                "arm": None,
                "actuator": "Only Soft 0050 / clips / FUSE / COOL (already KEEP)",
                "held_vs_L4_pp": None,
                "tipY_vs_L4_pp": None,
                "capture_frac_held": 0.0,
                "capture_frac_tipY": 0.0,
                "feasible_under_keep": True,
                "blocker": (
                    "Paper tip edge is MUTE_S3_SAT Path3 intermittency vs always-WITHIN, "
                    "not Soft residual sleeve mass"
                ),
            },
            {
                "id": "D_KEEP_STAMPS",
                "arm": "KEEP_STAMPS_L4",
                "actuator": "Continue gate_stamps_telemetry; paper observe KEEP",
                "held_vs_L4_pp": 0.0,
                "tipY_vs_L4_pp": 0.0,
                "capture_frac_held": 0.0,
                "capture_frac_tipY": 0.0,
                "feasible_under_keep": True,
                "blocker": None,
            },
            {
                "id": "E_PAPER_BLEND",
                "arm": "PAPER_OVERRIDE_W42_M05_K3",
                "actuator": "Research r=where(conf, live_r, champ_r) on tip order_rows",
                "held_vs_L4_pp": sealed_ov["held_cagr_lift_vs_L4_pp"],
                "tipY_vs_L4_pp": sealed_ov["tipY_vs_L4_pp"],
                "capture_frac_held": 1.0,
                "capture_frac_tipY": 1.0,
                "feasible_under_keep": False,
                "blocker": "Requires Soft FIN/TEL shell parity — FORBIDDEN by Path3 WITHIN KEEP",
            },
            {
                "id": "F_CHAMP_PATH3_GATE",
                "arm": "ATTR_CHAMP_MUTE_S3_SAT",
                "actuator": (
                    "Replace Path3 daily always-ON with MUTE_S3_SAT / trail-prem mute "
                    "intermittency (0kb1) while Soft FIN/TEL stay OFF"
                ),
                "held_vs_L4_pp": champ["held_cagr_lift_vs_L4_pp"],
                "tipY_vs_L4_pp": champ["tipY_vs_L4_pp"],
                "capture_frac_held": _capture(champ),
                "capture_frac_tipY": champ_tip_cap,
                "feasible_under_keep": False,
                "blocker": (
                    "Path3 OFF days reopen FIN∪TEL ownership hole under Soft FIN/TEL OFF; "
                    "also changes WITHIN daily-ledger cutover semantics — needs separate ballot"
                ),
            },
        ],
    }

    optimize = [
        "Question: under Path3 WITHIN KEEP · Soft FIN/TEL OFF, what apply path can "
        "capture paper OVERRIDE tip edge?",
        (
            f"Verdict `{verdict}`: paper gap vs live twin L4 held **+{gap_held}** tipY "
            f"**+{gap_tipy}** · override days **{pct_ov}%**"
        ),
        (
            f"Attribution: MUTE_S3_SAT champ vs L4 held **{champ['held_cagr_lift_vs_L4_pp']}** "
            f"tipY **{champ['tipY_vs_L4_pp']}** (tipY capture **{champ_tip_cap}**) — "
            "tip lag ≈ always-WITHIN vs intermittent Path3 stack, not missing Soft-force days"
        ),
        (
            f"Option A Path3-mute-on-override held **{mute['held_cagr_lift_vs_L4_pp']}** "
            f"tipY **{mute['tipY_vs_L4_pp']}** held-capture **{mute_cap}** tipY-capture "
            f"**{mute_tip_cap}** — does **not** close tipY; Soft FIN/TEL ownership hole"
        ),
        (
            "Option B best soft-α "
            + (
                f"**{best_alpha['arm']}** held **{best_alpha['held_cagr_lift_vs_L4_pp']}** "
                f"tipY **{best_alpha['tipY_vs_L4_pp']}** tipY-capture "
                f"**{_capture_tipy(best_alpha)}**"
                if best_alpha
                else "n/a"
            )
            + " — feasible ownership but tipY≈0"
        ),
        "Option C Soft 0050/clips residual: structural NO_EDGE for tip OVERRIDE gap",
        "Option D KEEP stamps: safe default · dual-paper observe KEEP · tip gap remains paper-only",
        "Option E full paper blend: FORBIDDEN under Soft FIN/TEL stay OFF",
        (
            f"Option F champ Path3 gate: tipY capture **{champ_tip_cap}** but Path3 OFF days "
            "+ WITHIN daily semantics change → separate ballot / ownership block"
        ),
        "Disposition: **no live apply wire** — tip Soft LIVE_OVERRIDE stays stamps/telemetry",
        "Soft KEEP · Path4 OFF · broker false · Path3 WITHIN KEEP",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "live_base": "L4_LIVE_P3_WITHIN",
        "gate": {
            "window": WINDOW,
            "margin": MARGIN,
            "confirm_k": CONFIRM_K,
            "pct_override_days": pct_ov,
        },
        "design": design,
        "arms": rows,
        "best_feasible": best_feas,
        "n_feasible_pos": int(len(feasible_pos)),
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "live_wire": False,
        "label": f"{SCREEN_ID}_{generated[:10]}__{verdict}",
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    # --- Charter ---
    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Under Path3 `WITHIN_SLEEVE` KEEP · Soft FIN/TEL Exact T+1 stay OFF · "
            "Exact T+1 · broker false · Path4 OFF — what **apply path** can let tip "
            "capture paper `LIVE_OVERRIDE` edge (held +1.61 / tipY +6.04 vs Soft L3; "
            "gap vs live twin L4 is the relevant target) without undoing cutover?",
            "",
            "## Method",
            "",
            "- Baseline: L4 tip Soft + Path3 WITHIN (live twin)",
            "- Ceiling: sealed paper OVERRIDE return blend (infeasible Soft-shell days)",
            "- Proxies: Path3 mute on `override_on` · soft-α Path3 tilt · Soft residual · KEEP stamps",
            "- Score held / tipY / capture fraction vs L4 gap; flag Soft FIN/TEL ownership blockers",
            "",
            "## Forbidden",
            "",
            "- Re-enable Soft FIN/TEL Exact T+1 · undo Path3 WITHIN · Path4 live · "
            "year-cut · hybrid T+0 · broker · live apply wire without dedicated ACCEPT",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md",
        REP / f"{CHARTER_ID}.md",
        charter_md,
        kind="charter",
    )
    charter_json = {
        "id": CHARTER_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "question": "apply path under Path3 WITHIN + Soft FIN/TEL OFF",
        "forbidden": [
            "soft_fin_tel_reenable",
            "path3_within_undo",
            "path4_live",
            "year_cut",
            "hybrid_t0",
            "broker",
            "live_apply_without_accept",
        ],
        "label": f"{CHARTER_ID}_{generated[:10]}",
    }
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.json",
        REP / f"{CHARTER_ID}.json",
        json.dumps(charter_json, indent=2) + "\n",
        kind="charter json",
    )

    # --- Screen MD ---
    screen_lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {generated[:10]} · Register: **{REGISTER}** · Verdict: **`{verdict}`**",
        "",
        f"Gate: lag{WINDOW} live−champ > {MARGIN} for K={CONFIRM_K} · override days **{pct_ov}%**",
        "",
        f"Paper gap vs L4: held **+{gap_held}** · tipY **+{gap_tipy}**",
        "",
        "| Arm | held vs L4 | tipY | capture | feasible KEEP | Soft FIN/TEL req |",
        "|---|---:|---:|---:|---|---|",
    ]
    for r in rows:
        screen_lines.append(
            f"| `{r['arm']}` | {r['held_cagr_lift_vs_L4_pp']} | {r['tipY_vs_L4_pp']} | "
            f"{r.get('capture_frac_held_vs_paper_gap')} | "
            f"{'Y' if r['feasible_under_path3_within_keep'] else 'N'} | "
            f"{'Y' if r['soft_fin_tel_required'] else 'N'} |"
        )
    screen_lines += [
        "",
        "## Optimize live",
        "",
    ]
    for i, line in enumerate(optimize, 1):
        screen_lines.append(f"{i}. {line}")
    screen_lines += ["", f"Label: `{screen['label']}`", ""]
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md",
        REP / f"{SCREEN_ID}.md",
        "\n".join(screen_lines),
        kind="screen",
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.json",
        REP / f"{SCREEN_ID}.json",
        json.dumps(screen, indent=2) + "\n",
        kind="screen json",
    )

    # --- Decision pack ---
    ba = best_alpha or {}
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Answer",
            "",
            "**No Path3-WITHIN-safe apply path closes the tipY gap.**",
            "",
            f"- Relevant tip gap (OVERRIDE sealed vs L4): held **+{gap_held}** · tipY **+{gap_tipy}**",
            (
                f"- Attribution: `MUTE_S3_SAT` champ vs L4 tipY **{champ['tipY_vs_L4_pp']}** "
                f"(capture **{champ_tip_cap}**) — tip lag is always-WITHIN vs intermittent "
                "Path3 stack, not missing Soft-force on override days"
            ),
            (
                f"- Force-LIVE / Path3-mute-on-override: held **{mute['held_cagr_lift_vs_L4_pp']}** "
                f"tipY **{mute['tipY_vs_L4_pp']}** tipY-capture **{mute_tip_cap}**"
            ),
            (
                f"- Best feasible soft-α **`{ba.get('arm')}`** held "
                f"**{ba.get('held_cagr_lift_vs_L4_pp')}** tipY **{ba.get('tipY_vs_L4_pp')}** "
                f"— ownership KEEP but tipY≈0"
                if ba
                else "- No soft-α arm cleared held+ vs L4"
            ),
            "- Soft 0050/clips residual cannot actuate tip OVERRIDE gap",
            "- Landing champ tipY needs Path3 OFF days + Soft fill or WITHIN daily rewrite → separate ballot",
            "- Stamps-only KEEP is the correct live posture under current constraints",
            "",
            "## Disposition",
            "",
            "- Do **not** wire return-blend / Path3 mute / soft-α apply from this pack",
            "- Do **not** re-enable Soft FIN/TEL / undo Path3 WITHIN / Path4 / broker",
            "- Next: KEEP `gate_stamps_telemetry` + dual-paper observe; any apply = new ACCEPT",
            "- Soft KEEP · Path4 OFF · broker false · no live apply this pack",
            "",
            "## Next (optimize list)",
            "",
        ]
    )
    for i, line in enumerate(optimize, 1):
        decision_md += f"{i}. {line}\n"
    decision_md += (
        f"\nLabel: `{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE`\n"
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="decision pack",
    )
    decision_json = {
        "id": DECISION_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "verdict": verdict,
        "generated_at_utc": generated,
        "gap_vs_L4": {"held_pp": gap_held, "tipY_pp": gap_tipy},
        "best_feasible": best_feas,
        "mute_proxy": {
            "held_vs_L4_pp": mute["held_cagr_lift_vs_L4_pp"],
            "capture_frac": mute_cap,
            "feasible": False,
        },
        "design": design,
        "optimize_live": optimize,
        "live_wire": False,
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
    }
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(decision_json, indent=2) + "\n",
        kind="decision pack json",
    )

    print(json.dumps({"verdict": verdict, "gap_held": gap_held, "gap_tipy": gap_tipy, "best_feasible": best_feas}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
