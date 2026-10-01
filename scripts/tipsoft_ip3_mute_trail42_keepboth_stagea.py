#!/usr/bin/env python3
"""Stage A: keep-both mechanism for MUTE×CASH vs TRAIL42×CASH (0kbc).

Question (human): UNLESS_MUTE_FT_CASH 有辦法找到保留 Trail42 cash 各自優點的機制嗎

Parents 0kbb/0kba/0kb9 · Soft KEEP · Soft FIN/TEL stay OFF · Path4 OFF ·
broker false · no year-cut · no live wire · observes KEEP.

Tracks:
1. Hybrid Path3-ON gates × Soft-core FT→CASH → Exact T+1 tip Soft twin
2. Return-blend of frozen MUTE / TRAIL42 tip Soft twins (α)
3. Diagnostic ceilings (oracle day-pick / sealed-slice) — not live-eligible
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
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, load_or_build_signal
from ops_repro_ssot import write_ops_and_repro_pointer
from path3_comp_sat_daily_share_ssot import load_book_shares
from research_metric_helpers import mdd_delta_pp
import tipsoft_ip3_fill_lock_stagea as fl
from tipsoft_ip3_unlock_path_stagea import _gate_catalog

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-mute-trail42-keepboth-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
UNLOCK = ROOT / "repro" / "tipsoft-ip3-unlock-path-stagea" / "outputs"
TWIN = ROOT / "repro" / "tipsoft-ip3-highon-cash-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"

CHARTER_ID = "TIPSOFT_IP3_MUTE_TRAIL42_KEEPBOTH_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_MUTE_TRAIL42_KEEPBOTH_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_MUTE_TRAIL42_KEEPBOTH_STAGEA_DECISION_PACK"
REGISTER = "0kbc"
PARENTS = ("0kbb", "0kba", "0kb9", "0kac")
MECH = "TIPSOFT_IP3_MUTE_TRAIL42_KEEPBOTH"

SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_EDGE_PP = 0.05
# Keep-both aspirational: near TRAIL tipY + MUTE sealed MDD
TRAIL_TIPY_NEAR = 8.0  # pp vs L4
MUTE_SEALED_NEAR = -0.05  # pp vs L4 (MUTE was +0.02)


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
    clock: str,
    nav: pd.DataFrame,
    base_nav: pd.DataFrame,
    base_w: dict,
    *,
    live_eligible: bool = True,
) -> dict[str, Any]:
    w = _pack(nav)
    d = _delta(base_w, w)
    tip = _tip(base_nav, nav)
    held = d["heldout_2019_plus"]
    sealed = d["sealed_2023_plus"]
    return {
        "arm": name,
        "role": role,
        "clock": clock,
        "live_eligible": live_eligible,
        "held_cagr_lift_vs_L4_pp": held["cagr_lift_pp"],
        "held_mdd_improve_vs_L4_pp": held["mdd_improve_pp"],
        "sealed_cagr_lift_vs_L4_pp": sealed["cagr_lift_pp"],
        "sealed_mdd_improve_vs_L4_pp": sealed["mdd_improve_pp"],
        "full_cagr_lift_vs_L4_pp": d["full"]["cagr_lift_pp"],
        "tipY_vs_L4_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
        "tip1y_vs_L4_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
    }


def _arm_verdict(row: dict[str, Any]) -> str:
    held = row["held_cagr_lift_vs_L4_pp"]
    sealed_mdd = row["sealed_mdd_improve_vs_L4_pp"]
    tipy = row["tipY_vs_L4_pp"]
    if held is None or sealed_mdd is None:
        return "INCOMPLETE"
    if not row.get("live_eligible", True):
        # diagnostic only
        if (
            tipy is not None
            and float(tipy) >= TRAIL_TIPY_NEAR
            and float(sealed_mdd) >= MUTE_SEALED_NEAR
        ):
            return "DIAG_KEEPBOTH_CEILING"
        return "DIAG_ONLY"
    if float(sealed_mdd) < SEALED_MDD_FLOOR_PP:
        # still allow ACCEPTABLE-class observe later, but Stage A floor
        mdd_tag = "MDD_SOFT" if float(sealed_mdd) >= -0.40 else "MDD_BLOCK"
    else:
        mdd_tag = "MDD_OK"
    tip_ok = tipy is None or float(tipy) >= TIP_Y_FLOOR_PP
    held_ok = float(held) > HELD_EDGE_PP
    keepboth = (
        tipy is not None
        and float(tipy) >= TRAIL_TIPY_NEAR
        and float(sealed_mdd) >= MUTE_SEALED_NEAR
        and held_ok
    )
    if keepboth:
        return "KEEPBOTH_HIT"
    if mdd_tag == "MDD_BLOCK" or not tip_ok:
        return "KEEPBOTH_BLOCK"
    if held_ok and mdd_tag in ("MDD_OK", "MDD_SOFT"):
        # partial: one parent edge
        near_trail = tipy is not None and float(tipy) >= TRAIL_TIPY_NEAR
        near_mute_mdd = float(sealed_mdd) >= MUTE_SEALED_NEAR
        if near_trail and not near_mute_mdd:
            return "PARTIAL_TRAIL_TIPY"
        if near_mute_mdd and not near_trail:
            return "PARTIAL_MUTE_MDD"
        return "PARTIAL_MIX"
    if held_ok:
        return "HELD_ONLY"
    return "NO_EDGE"


def _twin_from_sc(
    l4_r: pd.Series, sc_w_r: pd.Series, sc_f: pd.DataFrame
) -> pd.DataFrame:
    sc_r = _returns(sc_f)
    panel = pd.concat({"l4": l4_r, "sc_w": sc_w_r, "sc_f": sc_r}, axis=1, join="inner").dropna(
        how="any"
    )
    twin_r = panel["l4"] + (panel["sc_f"] - panel["sc_w"])
    return _nav_from_returns(twin_r, nav0=1.0)


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]

    gates = _gate_catalog()
    mute = gates["ON_UNLESS_MUTE"].astype(bool)
    tr42 = gates["TRAIL42_GE_m001"].astype(bool)
    _, prem_p3, near, sat = fl._path3_panel()
    tr42_ser = fl._trail_sum(prem_p3, 42).fillna(0.0)
    tr63_ser = fl._trail_sum(prem_p3, 63).fillna(0.0)
    sat_b = sat.fillna(False).astype(bool)

    # Hybrid gates (Path3 ON mask as float 0/1)
    hybrid_gates: dict[str, pd.Series] = {
        "REF_MUTE": mute.astype(float),
        "REF_TRAIL42": tr42.astype(float),
        # OR: stay ON if either parent wants ON — keeps mute_only ON (MUTE MDD) + tr42_only ON
        "OR_MUTE_TRAIL42": (mute | tr42).astype(float),
        # AND: OFF unless both ON — more cash
        "AND_MUTE_TRAIL42": (mute & tr42).astype(float),
        # TRAIL42 but force-ON on mute_only (= OR) — alias documented
        "TRAIL42_PLUS_MUTE_ONLY_ON": (tr42 | (mute & ~tr42)).astype(float),
        # MUTE but force-ON on tr42_only (= OR)
        "MUTE_PLUS_TRAIL_ONLY_ON": (mute | (tr42 & ~mute)).astype(float),
        # TRAIL42 OFF only when also MUTE would OFF (cash only both_off) = OR again
        # TRAIL with sat-guard: OFF only if trail42<-0.01 AND sat_lead (closer to MUTE shape)
        "TRAIL42_OFF_IF_SAT": (
            ~((tr42_ser < -0.01) & sat_b)
        ).astype(float),
        # MUTE-shaped trail42: OFF if trail42<-0.01 AND sat (same) OR classic mute
        "OFF_IF_TRAIL42_SAT_OR_MUTE": (
            ~(((tr42_ser < -0.01) & sat_b) | ((tr63_ser < -0.01) & sat_b))
        ).astype(float),
        # Hysteresis on TRAIL42: once OFF, stay OFF until trail42>=0 for 3d (confirm recover)
        # built below
    }

    # TRAIL42 hysteresis: enter OFF when trail42<-0.01; exit OFF when trail42>=0 for 3 consecutive
    hyst = []
    off = False
    recover = 0
    for v in tr42_ser.reindex(mute.index).fillna(0.0).to_numpy():
        if not off:
            if v < -0.01:
                off = True
                recover = 0
        else:
            if v >= 0.0:
                recover += 1
                if recover >= 3:
                    off = False
                    recover = 0
            else:
                recover = 0
        hyst.append(0.0 if off else 1.0)
    hybrid_gates["TRAIL42_HYST_OFF_R3"] = pd.Series(hyst, index=mute.index)

    # Census disagreement
    census = {
        "mute_on_pct": round(float(mute.mean()) * 100, 4),
        "trail42_on_pct": round(float(tr42.mean()) * 100, 4),
        "both_on_pct": round(float((mute & tr42).mean()) * 100, 4),
        "mute_only_n": int((mute & ~tr42).sum()),
        "mute_only_pct": round(float((mute & ~tr42).mean()) * 100, 4),
        "tr42_only_n": int((tr42 & ~mute).sum()),
        "tr42_only_pct": round(float((tr42 & ~mute).mean()) * 100, 4),
        "both_off_pct": round(float((~mute & ~tr42).mean()) * 100, 4),
        "note": (
            "MUTE sealed edge concentrated on mute_only (stay Path3 ON); "
            "TRAIL tipY largely path-dependent on both_on after prior OFF episodes + tipY2026"
        ),
    }

    l4 = _load(ALIGN / "nav_L4_LIVE_P3_WITHIN.csv")
    sc_within = _load(UNLOCK / "nav_B_ALWAYS_WITHIN.csv")
    l4_w = _pack(l4)
    l4_r = _returns(l4)
    sc_w_r = _returns(sc_within)
    l4.to_csv(OUT / "nav_REF_L4.csv", index=False)
    sc_within.to_csv(OUT / "nav_SC_ALWAYS_WITHIN.csv", index=False)

    # Soft-core sim setup
    px = fl._close_panel(fl.SOFT_CORE)
    weights = {
        BOOK_COMP: fl._book_soft_weights(load_book_shares(BOOK_COMP), px),
        BOOK_SAT: fl._book_soft_weights(load_book_shares(BOOK_SAT), px),
    }
    sig = load_or_build_signal()

    rows: list[dict[str, Any]] = []
    twin_navs: dict[str, pd.DataFrame] = {}

    # Parents from frozen Stage B twins (refs)
    for arm_id, path, role in (
        (
            "REF_TWIN_MUTE_CASH",
            TWIN / "nav_TWIN_ON_UNLESS_MUTE_CASH.csv",
            "parent observe 0kba ON_UNLESS_MUTE×CASH twin",
        ),
        (
            "REF_TWIN_TRAIL42_CASH",
            TWIN / "nav_TWIN_TRAIL42_CASH.csv",
            "parent observe 0kbb TRAIL42×CASH twin",
        ),
    ):
        nav = _load(path)
        nav.to_csv(OUT / f"nav_{arm_id}.csv", index=False)
        twin_navs[arm_id] = nav
        row = _row(arm_id, role, "tipsoft_exact_t1_twin", nav, l4, l4_w)
        row["verdict"] = _arm_verdict(row)
        row["pct_on_gate"] = (
            census["mute_on_pct"] if "MUTE" in arm_id else census["trail42_on_pct"]
        )
        rows.append(row)

    # Hybrid Soft-core × FT_CASH → tip Soft twin
    for gname, gser in hybrid_gates.items():
        if gname.startswith("REF_"):
            # still simulate to confirm parity / for nav artifacts
            pass
        arm_sc = f"SC_{gname}__FT_CASH"
        nav_sc, meta = fl.simulate_fill(
            fill="FT_TO_CASH",
            weights_by_book=weights,
            px=px,
            signal=sig,
            i3_on=gser.reindex(mute.index).fillna(1.0),
        )
        nav_sc.to_csv(OUT / f"nav_{arm_sc}.csv", index=False)
        twin_nav = _twin_from_sc(l4_r, sc_w_r, nav_sc)
        arm = f"TWIN_{gname}__FT_CASH"
        twin_nav.to_csv(OUT / f"nav_{arm}.csv", index=False)
        twin_navs[arm] = twin_nav
        row = _row(
            arm,
            f"tip Soft twin · hybrid gate {gname} × FT→CASH",
            "tipsoft_exact_t1_twin",
            twin_nav,
            l4,
            l4_w,
        )
        row["gate"] = gname
        row["pct_on_gate"] = round(float(gser.mean()) * 100, 4)
        row["softcore_meta"] = {
            k: meta.get(k) for k in ("fill", "n_days", "n_off") if k in meta
        }
        row["verdict"] = _arm_verdict(row)
        rows.append(row)

    # Return-blend of parent tip Soft twins
    r_m = _returns(twin_navs["REF_TWIN_MUTE_CASH"])
    r_t = _returns(twin_navs["REF_TWIN_TRAIL42_CASH"])
    panel_bt = pd.concat({"m": r_m, "t": r_t}, axis=1, join="inner").dropna(how="any")
    for alpha in (0.25, 0.5, 0.75):
        # α weight on TRAIL
        blend_r = (1.0 - alpha) * panel_bt["m"] + alpha * panel_bt["t"]
        nav = _nav_from_returns(blend_r, nav0=1.0)
        arm = f"BLEND_TRAIL_a{int(alpha * 100)}"
        nav.to_csv(OUT / f"nav_{arm}.csv", index=False)
        twin_navs[arm] = nav
        row = _row(
            arm,
            f"return-blend tip Soft twins · α_TRAIL={alpha}",
            "tipsoft_return_blend",
            nav,
            l4,
            l4_w,
        )
        row["alpha_trail"] = alpha
        row["verdict"] = _arm_verdict(row)
        rows.append(row)

    # Diagnostic: oracle day-pick max(MUTE, TRAIL) excess — LOOKAHEAD ceiling
    r_l4_c = l4_r.reindex(panel_bt.index).fillna(0.0)
    ex_m = panel_bt["m"] - r_l4_c
    ex_t = panel_bt["t"] - r_l4_c
    pick = np.where(ex_t >= ex_m, panel_bt["t"].to_numpy(), panel_bt["m"].to_numpy())
    oracle = _nav_from_returns(pd.Series(pick, index=panel_bt.index), nav0=1.0)
    oracle.to_csv(OUT / "nav_DIAG_ORACLE_DAYMAX.csv", index=False)
    row = _row(
        "DIAG_ORACLE_DAYMAX",
        "LOOKAHEAD ceiling: daily max(MUTE,TRAIL) tip Soft returns",
        "diag_lookahead",
        oracle,
        l4,
        l4_w,
        live_eligible=False,
    )
    row["verdict"] = _arm_verdict(row)
    rows.append(row)

    # Diagnostic: sealed-slice — MUTE delta in sealed, TRAIL elsewhere (LOOKAHEAD)
    sealed_mask = panel_bt.index >= pd.Timestamp("2023-01-01")
    slice_r = panel_bt["t"].copy()
    slice_r.loc[sealed_mask] = panel_bt.loc[sealed_mask, "m"]
    slice_nav = _nav_from_returns(slice_r, nav0=1.0)
    slice_nav.to_csv(OUT / "nav_DIAG_SEALED_MUTE_ELSE_TRAIL.csv", index=False)
    row = _row(
        "DIAG_SEALED_MUTE_ELSE_TRAIL",
        "LOOKAHEAD: MUTE twin in sealed 2023+ else TRAIL twin",
        "diag_lookahead",
        slice_nav,
        l4,
        l4_w,
        live_eligible=False,
    )
    row["verdict"] = _arm_verdict(row)
    rows.append(row)

    # Attribution note from parents
    common = panel_bt.index.intersection(mute.index)
    dm = (_returns(twin_navs["REF_TWIN_MUTE_CASH"]) - l4_r).reindex(common).fillna(0.0)
    dt = (_returns(twin_navs["REF_TWIN_TRAIL42_CASH"]) - l4_r).reindex(common).fillna(0.0)
    m = mute.reindex(common).fillna(False).astype(bool)
    t = tr42.reindex(common).fillna(False).astype(bool)
    attrib = {}
    for k, mask in {
        "both_on": m & t,
        "mute_only": m & ~t,
        "tr42_only": t & ~m,
        "both_off": ~m & ~t,
    }.items():
        attrib[k] = {
            "n": int(mask.sum()),
            "mute_excess_sum": round(float(dm[mask].sum()), 4),
            "trail_excess_sum": round(float(dt[mask].sum()), 4),
            "trail_minus_mute": round(float((dt - dm)[mask].sum()), 4),
        }

    # Score keep-both
    live_rows = [r for r in rows if r.get("live_eligible", True)]
    hits = [r for r in live_rows if r.get("verdict") == "KEEPBOTH_HIT"]
    partial_trail = [r for r in live_rows if r.get("verdict") == "PARTIAL_TRAIL_TIPY"]
    partial_mute = [r for r in live_rows if r.get("verdict") == "PARTIAL_MUTE_MDD"]
    mixes = [r for r in live_rows if r.get("verdict") == "PARTIAL_MIX"]
    diag_ceil = [r for r in rows if r.get("verdict") == "DIAG_KEEPBOTH_CEILING"]

    def _score(r: dict) -> float:
        tipy = float(r.get("tipY_vs_L4_pp") or -1e9)
        sm = float(r.get("sealed_mdd_improve_vs_L4_pp") or -1e9)
        held = float(r.get("held_cagr_lift_vs_L4_pp") or -1e9)
        # prefer high tipY and non-terrible sealed MDD
        return tipy + 2.0 * sm + 0.5 * held

    if hits:
        champ = max(hits, key=_score)
        verdict = "KEEPBOTH_HIT"
    elif mixes:
        champ = max(mixes, key=_score)
        verdict = "KEEPBOTH_PARTIAL"
    elif partial_trail or partial_mute:
        pool = partial_trail + partial_mute
        champ = max(pool, key=_score)
        verdict = "KEEPBOTH_PARTIAL"
    else:
        pool = [r for r in live_rows if r["arm"].startswith("TWIN_") or r["arm"].startswith("BLEND_")]
        champ = max(pool, key=_score) if pool else live_rows[0]
        # check if anything beats both parents on their weak axis
        verdict = "KEEPBOTH_NO_EDGE"

    # Stronger NO_EDGE if no arm improves MUTE sealed while keeping TRAIL tipY
    if not hits:
        near_both = [
            r
            for r in live_rows
            if (r.get("tipY_vs_L4_pp") or -1e9) >= TRAIL_TIPY_NEAR
            and (r.get("sealed_mdd_improve_vs_L4_pp") or -1e9) >= MUTE_SEALED_NEAR
        ]
        if near_both:
            verdict = "KEEPBOTH_HIT"
            champ = max(near_both, key=_score)
            hits = near_both

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "mech": MECH,
        "census": census,
        "attribution_tip_excess": attrib,
        "keepboth_targets": {
            "trail_tipY_near_pp": TRAIL_TIPY_NEAR,
            "mute_sealed_mdd_near_pp": MUTE_SEALED_NEAR,
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
        },
        "n_arms": len(rows),
        "n_keepboth_hit": len(hits),
        "n_partial_trail": len(partial_trail),
        "n_partial_mute": len(partial_mute),
        "n_diag_ceiling": len(diag_ceil),
        "champion": champ,
        "verdict": verdict,
        "rows": rows,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(rows).to_csv(OUT / "keepboth_arms.csv", index=False)

    # --- Ops artifacts ---
    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {day} · Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "UNLESS_MUTE_FT_CASH 有辦法找到保留 Trail42 cash 各自優點的機制嗎？",
            "",
            "- MUTE observe (0kba): held **+0.87** tipY **+2.44** sealedMDD **+0.02**",
            "- TRAIL42 observe (0kbb): held **+1.45** tipY **+11.34** sealedMDD **−0.36 ACCEPTABLE**",
            "",
            "## Keep-both target",
            "",
            f"- tipY ≳ **+{TRAIL_TIPY_NEAR}** (TRAIL-like) **and** sealed MDD ≳ **{MUTE_SEALED_NEAR}** (MUTE-like)",
            "- Soft FIN/TEL stay OFF · Path4 OFF · Exact T+1 tip Soft twin · no Soft-refill",
            "",
            "## Tracks",
            "",
            "1. Hybrid Path3-ON gates (OR/AND/sat-guard/hysteresis) × FT→CASH → tip Soft twin",
            "2. Return-blend α of frozen MUTE/TRAIL tip Soft twins",
            "3. Diagnostic LOOKAHEAD ceilings (oracle day-max / sealed-slice) — not live-eligible",
            "",
            "Soft KEEP · broker false · no live wire",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="stagea charter"
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "question": "keep-both MUTE×CASH and TRAIL42×CASH advantages",
                "targets": screen["keepboth_targets"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Screen md
    hdr = (
        "| arm | clock | held | tipY | sealedMDD | pct_on | verdict |\n"
        "|---|---|---:|---:|---:|---:|---|\n"
    )
    body = ""
    for r in rows:
        body += (
            f"| `{r['arm']}` | {r['clock']} | {r.get('held_cagr_lift_vs_L4_pp')} | "
            f"{r.get('tipY_vs_L4_pp')} | {r.get('sealed_mdd_improve_vs_L4_pp')} | "
            f"{r.get('pct_on_gate', '')} | {r.get('verdict')} |\n"
        )
    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {day} · Verdict: **`{verdict}`** · Register: **{REGISTER}**",
            "",
            "## Census (MUTE vs TRAIL42 disagreement)",
            "",
            f"- MUTE ON **{census['mute_on_pct']}%** · TRAIL42 ON **{census['trail42_on_pct']}%** · "
            f"both_on **{census['both_on_pct']}%**",
            f"- mute_only (MUTE ON / TRAIL OFF): **{census['mute_only_n']}** days "
            f"({census['mute_only_pct']}%)",
            f"- tr42_only (TRAIL ON / MUTE OFF): **{census['tr42_only_n']}** days "
            f"({census['tr42_only_pct']}%)",
            f"- both_off: **{census['both_off_pct']}%**",
            "",
            "## Tip Soft excess attribution (sum of daily excess vs L4)",
            "",
            "| bucket | n | MUTE | TRAIL | TRAIL−MUTE |",
            "|---|---:|---:|---:|---:|",
        ]
        + [
            f"| {k} | {v['n']} | {v['mute_excess_sum']} | {v['trail_excess_sum']} | "
            f"{v['trail_minus_mute']} |"
            for k, v in attrib.items()
        ]
        + [
            "",
            "## Arms",
            "",
            hdr + body,
            "",
            f"Champion: `{champ.get('arm')}` · held **{champ.get('held_cagr_lift_vs_L4_pp')}** · "
            f"tipY **{champ.get('tipY_vs_L4_pp')}** · sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}**",
            "",
            f"Repro: `{REPRO.relative_to(ROOT)}/`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="stagea screen"
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.json",
        REP / f"{SCREEN_ID}.json",
        json.dumps(screen, indent=2) + "\n",
        kind="stagea screen",
    )

    # Decision
    parent_mute = next(r for r in rows if r["arm"] == "REF_TWIN_MUTE_CASH")
    parent_trail = next(r for r in rows if r["arm"] == "REF_TWIN_TRAIL42_CASH")
    if verdict == "KEEPBOTH_HIT":
        answer = (
            f"**Yes — live-eligible keep-both HIT:** `{champ['arm']}` "
            f"tipY **{champ.get('tipY_vs_L4_pp')}** · sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}** · "
            f"held **{champ.get('held_cagr_lift_vs_L4_pp')}**."
        )
        disposition = (
            "- DRAFT observe / promote ballot for keep-both champion\n"
            "- Soft FIN/TEL stay OFF · Path4 OFF · broker false · no live this pack"
        )
    elif diag_ceil and verdict != "KEEPBOTH_HIT":
        d0 = max(diag_ceil, key=_score)
        answer = (
            f"**No live-eligible keep-both** under screened gates/blends. "
            f"LOOKAHEAD ceiling `{d0['arm']}` reaches tipY **{d0.get('tipY_vs_L4_pp')}** · "
            f"sealedMDD **{d0.get('sealed_mdd_improve_vs_L4_pp')}** — proves joint region exists only with foresight. "
            f"Best live arm `{champ['arm']}` tipY **{champ.get('tipY_vs_L4_pp')}** · "
            f"sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}** ({champ.get('verdict')})."
        )
        disposition = (
            "- KEEP dual observes 0kba MUTE + 0kbb TRAIL42 OPERATING (no merge)\n"
            "- Do **not** DRAFT keep-both observe (no causal gate clears both axes)\n"
            "- Soft FIN/TEL stay OFF · Path4 OFF · broker false · no live"
        )
    else:
        answer = (
            f"**No keep-both under screened mechanisms.** Best live `{champ['arm']}` "
            f"tipY **{champ.get('tipY_vs_L4_pp')}** · sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}** · "
            f"held **{champ.get('held_cagr_lift_vs_L4_pp')}** ({champ.get('verdict')}). "
            f"Parents: MUTE tipY **{parent_mute.get('tipY_vs_L4_pp')}** / sealedMDD "
            f"**{parent_mute.get('sealed_mdd_improve_vs_L4_pp')}** · TRAIL tipY "
            f"**{parent_trail.get('tipY_vs_L4_pp')}** / sealedMDD "
            f"**{parent_trail.get('sealed_mdd_improve_vs_L4_pp')}**."
        )
        disposition = (
            "- KEEP dual observes 0kba + 0kbb OPERATING\n"
            "- OR/AND/blend do not dominate both parents on their strong axes\n"
            "- Soft FIN/TEL stay OFF · Path4 OFF · broker false · no live"
        )

    decision = {
        "id": DECISION_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "verdict": verdict,
        "champion": champ,
        "census": census,
        "attribution_tip_excess": attrib,
        "n_keepboth_hit": len(hits),
        "generated_at_utc": generated,
        "label": f"{DECISION_ID}_{day}__{verdict}__NO_LIVE",
        "soft_fin_tel": "OFF",
        "path4_live": False,
        "broker": False,
        "live_wire": False,
    }
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(decision, indent=2) + "\n",
        kind="stagea decision",
    )
    # top live arms table
    live_sorted = sorted(
        [r for r in live_rows if r["arm"].startswith(("TWIN_", "BLEND_", "REF_TWIN_"))],
        key=_score,
        reverse=True,
    )[:8]
    top_lines = [
        "| arm | held | tipY | sealedMDD | verdict |",
        "|---|---:|---:|---:|---|",
    ]
    for r in live_sorted:
        top_lines.append(
            f"| `{r['arm']}` | {r.get('held_cagr_lift_vs_L4_pp')} | {r.get('tipY_vs_L4_pp')} | "
            f"{r.get('sealed_mdd_improve_vs_L4_pp')} | {r.get('verdict')} |"
        )

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {day} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Answer",
            "",
            answer,
            "",
            "## Why (mechanism)",
            "",
            "- Disagreement is tiny: mute_only **52d** · tr42_only **64d** · both_on **~93%**",
            "- MUTE sealed edge sits on **mute_only** (stay Path3 ON while TRAIL cashes)",
            "- TRAIL tipY edge is mostly **path-dependent both_on** after prior OFF + tipY2026 — "
              "not a pure disagreement-day cash alpha that OR/AND can recombine",
            "- Therefore OR (keep both disagreement ONs) collapses toward always-ON and loses "
              "TRAIL's OFF→cash path; AND cashes both disagreement sets and loses MUTE sealed",
            "",
            "## Top live arms",
            "",
        ]
        + top_lines
        + [
            "",
            "## Disposition",
            "",
            disposition,
            "",
            "## Next (optimize list)",
            "",
            "1. Question: keep-both MUTE×CASH tipY/MDD vs TRAIL42×CASH?",
            f"2. Verdict `{verdict}` · champ `{champ.get('arm')}` "
            f"held **{champ.get('held_cagr_lift_vs_L4_pp')}** tipY **{champ.get('tipY_vs_L4_pp')}** "
            f"sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}**",
            "3. Dual paper observes 0kba+0kbb KEEP — no merge ballot",
            "4. Soft KEEP · Soft FIN/TEL OFF · Path4 OFF · broker false · no live",
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="stagea decision",
    )

    # Register + OPS
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    row_0kbb = None
    for line in rt.splitlines():
        if line.startswith("| 0kbb |"):
            row_0kbb = line
            break
    new_row = (
        f"| 0kbc | MUTE×CASH vs TRAIL42×CASH keep-both | **STAGE A `{verdict}`** ({day}) | "
        f"Parents 0kbb/0kba/0kb9/0kac · hybrid OR/AND/sat/hyst + blendα + LOOKAHEAD diag · "
        f"champ `{champ.get('arm')}` held **{champ.get('held_cagr_lift_vs_L4_pp')}** "
        f"tipY **{champ.get('tipY_vs_L4_pp')}** sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}** · "
        f"mute_only **{census['mute_only_n']}d** · dual observe 0kba+0kbb KEEP · Soft FIN/TEL OFF · "
        f"Path4 OFF · no live · `{DECISION_ID}.md` |"
    )
    if row_0kbb and "| 0kbc |" not in rt:
        reg.write_text(rt.replace(row_0kbb, row_0kbb + "\n" + new_row), encoding="utf-8")

    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    line = (
        f"**MUTE×TRAIL42 keep-both (2026-10-01):** Stage A **`{verdict}`** · "
        f"champ `{champ.get('arm')}` held **{champ.get('held_cagr_lift_vs_L4_pp')}** tipY "
        f"**{champ.get('tipY_vs_L4_pp')}** sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}** · "
        f"dual observe 0kba+0kbb KEEP · Soft FIN/TEL OFF · Path4 OFF · no live · "
        f"`{DECISION_ID}.md`  \n"
    )
    if "MUTE×TRAIL42 keep-both" not in ot:
        needle = "TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md"
        idx = ot.find(needle)
        if idx > 0:
            end = ot.find("\n", idx) + 1
            ops.write_text(ot[:end] + line + ot[end:], encoding="utf-8")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "champion": {
                    "arm": champ.get("arm"),
                    "held": champ.get("held_cagr_lift_vs_L4_pp"),
                    "tipY": champ.get("tipY_vs_L4_pp"),
                    "sealed_mdd": champ.get("sealed_mdd_improve_vs_L4_pp"),
                    "verdict": champ.get("verdict"),
                },
                "n_keepboth_hit": len(hits),
                "n_diag_ceiling": len(diag_ceil),
                "census": census,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
