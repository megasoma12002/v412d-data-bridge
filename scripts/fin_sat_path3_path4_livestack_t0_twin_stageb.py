#!/usr/bin/env python3
"""Path3×Path4 live-stack T+0 overlay twin (0kaq) — Soft-core T+0 × COOL.

**Why:** P3/P4 are Exact T+0 carve mechanisms. The Exact T+1 tip Soft twin
(0kap) understates their live-intent edge. This pack overlays frozen live
``COOL_c8`` exposure on Soft-core T+0 coexist NAVs (0kao) and scores them
against ``BASE_LIVE_FUSE_COOL``.

Arms vs live Exact T+1 base:
- Soft-core T+0 ``REF_P3_WITHIN`` / ``P3_P4_CASH_{θ}`` (raw)
- Same Soft-core T+0 × frozen COOL equity scale (live overlay proxy)
- Reference: published 0kap Exact T+1 ``LIVE_P3_WITHIN`` row (no re-sim)

Soft KEEP · broker false · Path4 live OFF · no wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-path4-livestack-t0-twin-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

SOFTCORE = ROOT / "repro" / "fin-sat-path3-path4-coexist-stagea" / "outputs"
LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"

CHARTER_ID = "FIN_SAT_PATH3_PATH4_LIVESTACK_T0_TWIN_STAGEB_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_PATH4_LIVESTACK_T0_TWIN_STAGEB_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_PATH4_LIVESTACK_T0_TWIN_STAGEB_DECISION_PACK"
REGISTER = "0kaq"
PARENTS = ("0kap", "0kao")

BASE_ID = "BASE_LIVE_FUSE_COOL"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10

# Soft-core T+0 arms to overlay (from 0kao)
SOFTCORE_ARMS = (
    "REF_P3_WITHIN",
    "P3_P4_CASH_00025",
    "P3_P4_CASH_0005",
    "P3_P4_CASH_001",
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _tip(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
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
            bn = g["nav"].astype(float) / float(g["nav"].iloc[0])
            out[int(y)] = {"ret": float(bn.iloc[-1] - 1.0)}
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
                "ret_win": bool(kb["ret"] > ka["ret"]),
            }
        )
    return rows


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
    if sealed_ok and tip_ok and float(held["cagr_lift_pp"]) > 0.02:
        return "SOFT"
    if float(sealed["mdd_improve_pp"]) < SEALED_MDD_FLOOR_PP:
        return "MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "TIP_BLOCK"
    return "NO_EDGE"


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return df[["date", "nav"]].sort_values("date").reset_index(drop=True)


def _apply_cool_scale(nav: pd.DataFrame, cool: pd.Series) -> pd.DataFrame:
    """Equity-scale Soft-core T+0 returns by frozen COOL exposure (cash earns 0)."""
    x = nav.copy()
    x["date"] = pd.to_datetime(x["date"]).dt.normalize()
    x = x.set_index("date").sort_index()
    r = x["nav"].pct_change().fillna(0.0)
    c = cool.reindex(x.index).astype(float)
    # forward/back fill short gaps at edges; default full risk-on
    c = c.ffill().bfill().fillna(1.0).clip(lower=0.0, upper=1.0)
    r_eff = r * c
    out = pd.DataFrame(
        {
            "date": x.index,
            "nav": (1.0 + r_eff).cumprod().to_numpy(),
            "cool": c.to_numpy(),
            "r_raw": r.to_numpy(),
            "r_cool": r_eff.to_numpy(),
        }
    )
    return out.reset_index(drop=True)


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    base_path = LIVESTACK / f"nav_{BASE_ID}.csv"
    cool_path = LIVESTACK / "exposure_cool_from_fuse.csv"
    if not base_path.exists() or not cool_path.exists():
        raise FileNotFoundError(
            "missing 0kap live-stack outputs — run "
            "scripts/fin_sat_path3_path4_livestack_twin_stageb.py first"
        )

    base = _load_nav(base_path)
    cool_df = pd.read_csv(cool_path, parse_dates=[0])
    # exposure csv may be date-indexed without name
    if "e45_exposure" in cool_df.columns:
        cool = cool_df.set_index(cool_df.columns[0])["e45_exposure"]
    else:
        cool = cool_df.iloc[:, 0]
        if not isinstance(cool, pd.Series):
            cool = pd.Series(cool)
        cool.index = pd.to_datetime(cool_df.iloc[:, 0] if cool_df.shape[1] > 1 else cool_df.index)
    cool.index = pd.to_datetime(cool.index).normalize()
    cool = cool.astype(float).sort_index()
    cool.name = "e45_exposure"
    cool.to_frame().to_csv(OUT / "exposure_cool_from_fuse.csv")

    arms: dict[str, pd.DataFrame] = {BASE_ID: base}
    metas: dict[str, dict[str, Any]] = {
        BASE_ID: {
            "kind": "live_exact_t1_base",
            "fill_timing": "exact_t1",
            "path3": False,
            "path4": False,
            "cool_overlay": True,
        }
    }

    for arm in SOFTCORE_ARMS:
        src = SOFTCORE / f"nav_{arm}.csv"
        if not src.exists():
            raise FileNotFoundError(src)
        raw = _load_nav(src)
        raw.to_csv(OUT / f"nav_T0_{arm}.csv", index=False)
        arms[f"T0_{arm}"] = raw
        metas[f"T0_{arm}"] = {
            "kind": "softcore_t0_raw",
            "fill_timing": "t0",
            "softcore_arm": arm,
            "path3": True,
            "path4": arm.startswith("P3_P4_CASH"),
            "cool_overlay": False,
        }

        cool_nav = _apply_cool_scale(raw, cool)
        cool_nav.to_csv(OUT / f"nav_T0COOL_{arm}.csv", index=False)
        arms[f"T0COOL_{arm}"] = cool_nav[["date", "nav"]]
        metas[f"T0COOL_{arm}"] = {
            "kind": "softcore_t0_x_cool",
            "fill_timing": "t0",
            "softcore_arm": arm,
            "path3": True,
            "path4": arm.startswith("P3_P4_CASH"),
            "cool_overlay": True,
            "mean_cool": round(float(cool_nav["cool"].mean()), 4),
            "pct_cool_lt1": round(float((cool_nav["cool"] < 1.0 - 1e-12).mean()), 4),
        }

    # Reference 0kap Exact T+1 P3 WITHIN (already scored; include for clock compare)
    t1_p3 = LIVESTACK / "nav_LIVE_P3_WITHIN.csv"
    if t1_p3.exists():
        arms["T1_LIVE_P3_WITHIN"] = _load_nav(t1_p3)
        metas["T1_LIVE_P3_WITHIN"] = {
            "kind": "live_exact_t1_p3_ref",
            "fill_timing": "exact_t1",
            "path3": True,
            "path4": False,
            "cool_overlay": True,
            "note": "0kap tip Soft twin reference",
        }

    bw = _pack(base)
    rows = []
    for arm, nav in arms.items():
        if arm == BASE_ID:
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
                "verdict_vs_live": v,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "yearly_ret_wl": f"{ret_w}-{ret_l}",
                "meta": metas.get(arm, {}),
                "delta": delta,
                "tip": tip,
                "yearly": yearly,
            }
        )

    def _rank(r: dict[str, Any]) -> tuple[float, float, float]:
        return (
            float(r["held_cagr_lift_pp"] or -999),
            float(r["tip_ytd_cagr_lift_pp"] or -999),
            float(r["sealed_mdd_improve_pp"] or -999),
        )

    # Prefer T0×COOL CASH arms among HITs (live-intent P3+P4 under COOL)
    t0cool = [r for r in rows if (r.get("meta") or {}).get("kind") == "softcore_t0_x_cool"]
    t0cool_hit = [r for r in t0cool if r["verdict_vs_live"] in {"HIT", "HELD_HIT"}]
    t0_raw = [r for r in rows if (r.get("meta") or {}).get("kind") == "softcore_t0_raw"]
    t0_raw_hit = [r for r in t0_raw if r["verdict_vs_live"] in {"HIT", "HELD_HIT"}]

    if t0cool_hit:
        champion = max(t0cool_hit, key=_rank)
        pack_verdict = "LIVESTACK_T0_HIT"
    elif t0_raw_hit:
        champion = max(t0_raw_hit, key=_rank)
        pack_verdict = "LIVESTACK_T0_RAW_HIT"
    else:
        soft = [r for r in t0cool if r["verdict_vs_live"] == "SOFT"]
        if soft:
            champion = max(soft, key=_rank)
            pack_verdict = "LIVESTACK_T0_SOFT"
        else:
            pool = t0cool or rows
            champion = max(pool, key=_rank)
            pack_verdict = f"LIVESTACK_T0_{champion['verdict_vs_live']}"

    best_t0cool_p3 = next(
        (r for r in t0cool if r["arm"] == "T0COOL_REF_P3_WITHIN"), None
    )
    best_t0cool_p3p4 = max(
        [r for r in t0cool if "P3_P4_CASH" in r["arm"]],
        key=_rank,
        default=None,
    )
    t1_ref = next((r for r in rows if r["arm"] == "T1_LIVE_P3_WITHIN"), None)

    rec: list[str] = []
    rec.append(
        "P3/P4 live-intent clock is Exact T+0 — do not decide promote from Exact T+1 twin alone (0kap)"
    )
    if best_t0cool_p3:
        rec.append(
            f"T+0×COOL Path3 WITHIN `{best_t0cool_p3['arm']}` → "
            f"{best_t0cool_p3['verdict_vs_live']} held {best_t0cool_p3['held_cagr_lift_pp']} "
            f"tipY {best_t0cool_p3['tip_ytd_cagr_lift_pp']} sealedMDD "
            f"{best_t0cool_p3['sealed_mdd_improve_pp']}"
        )
    if best_t0cool_p3p4:
        rec.append(
            f"T+0×COOL best P3+P4 `{best_t0cool_p3p4['arm']}` → "
            f"{best_t0cool_p3p4['verdict_vs_live']} held {best_t0cool_p3p4['held_cagr_lift_pp']} "
            f"tipY {best_t0cool_p3p4['tip_ytd_cagr_lift_pp']}"
        )
        if best_t0cool_p3 and float(best_t0cool_p3p4["held_cagr_lift_pp"] or 0) > float(
            best_t0cool_p3["held_cagr_lift_pp"] or 0
        ) + 0.05:
            rec.append(
                "Under T+0×COOL, Path4 CASH_ETF adds held edge on Path3 — "
                "sequence: P3 T+0 cutover observe → Path4 CASH ballot (still OFF now)"
            )
        else:
            rec.append(
                "Under T+0×COOL, Path4 does not clearly beat Path3-only — "
                "Path4 live OFF; Soft sticky 0050 KEEP"
            )
    if t1_ref:
        rec.append(
            f"Contrast Exact T+1 tip Soft `T1_LIVE_P3_WITHIN` was "
            f"{t1_ref['verdict_vs_live']} (sealed MDD {t1_ref['sealed_mdd_improve_pp']}) "
            "— clock mismatch vs P3/P4 T+0"
        )
    if pack_verdict in {"LIVESTACK_T0_HIT", "LIVESTACK_T0_RAW_HIT"}:
        rec.append(
            f"Carry champion `{champion['arm']}` as live-optimize candidate — "
            "still Soft KEEP · Path4 live OFF · broker false until ACCEPT"
        )
    elif "MDD_BLOCK" in pack_verdict:
        rec.append(
            "Even T+0×COOL is MDD_BLOCK vs live Exact T+1 base — "
            "need sealed-MDD disposition or keep live Soft+COOL+FUSE unchanged"
        )
    rec.append("Soft KEEP · broker false · Path4 live flag OFF · no wire this pack")

    summary = [
        {
            "arm": r["arm"],
            "verdict_vs_live": r["verdict_vs_live"],
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
    pd.DataFrame(summary).to_csv(OUT / "arms_vs_live.csv", index=False)
    pd.DataFrame(champion["yearly"]).to_csv(
        OUT / "yearly_champion_vs_live.csv", index=False
    )

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": "PATH3_PATH4_LIVESTACK_T0_TWIN",
        "verdict": pack_verdict,
        "base": BASE_ID,
        "champion_arm": champion["arm"],
        "note": (
            "Soft-core T+0 NAVs from 0kao; COOL scale frozen from 0kap "
            "BASE_LIVE_FUSE_COOL offense. Scores vs Exact T+1 live base."
        ),
        "arms_vs_live": summary,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_live": champion["verdict_vs_live"],
            "delta": champion["delta"],
            "tip": champion["tip"],
            "meta": champion["meta"],
        },
        "optimize_live": rec,
        "gates": {
            "held_cagr_floor_pp": HELD_CAGR_FLOOR_PP,
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
            "tip_y_floor_pp": TIP_Y_FLOOR_PP,
        },
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, default=str) + "\n")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage B — live-stack T+0 overlay twin** · Soft **KEEP** · "
            "Path4 live **OFF** · broker **false**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Given P3/P4 are Exact T+0 mechanisms, does Soft-core T+0 (± frozen COOL) "
            "beat ``BASE_LIVE_FUSE_COOL`` — and how should live be optimized?",
            "",
            "## Method",
            "",
            "- Soft-core T+0 NAVs: 0kao coexist paper",
            "- COOL: frozen ``e45_exposure`` from 0kap BASE offense",
            "- Base: Exact T+1 ``BASE_LIVE_FUSE_COOL``",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__LIVESTACK_T0__NO_LIVE`",
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
                "mech": "PATH3_PATH4_LIVESTACK_T0_TWIN",
                "soft_keep": True,
                "broker": False,
                "path4_live": False,
            },
            indent=2,
        )
        + "\n"
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    def _fmt(r: dict) -> str:
        return (
            f"| {r['arm']} | {r['verdict_vs_live']} | {r['held_cagr_lift_pp']} | "
            f"{r['full_cagr_lift_pp']} | {r['sealed_mdd_improve_pp']} | "
            f"{r['tip_ytd_cagr_lift_pp']} | {r['tip_1y_cagr_lift_pp']} | "
            f"{r['yearly_ret_wl']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · base=`{BASE_ID}` · Soft-core fill=`t0` · "
            "live base fill=`exact_t1`",
            "",
            "## Arms vs live Exact T+1",
            "",
            "| Arm | vs live | held | full | sealed MDD↑ | tipY | tip1y | ret W–L |",
            "|---|---|---:|---:|---:|---:|---:|---|",
            *[_fmt(r) for r in summary],
            "",
            "## Optimize live",
            "",
            *[f"{i+1}. {s}" for i, s in enumerate(rec)],
            "",
            "Repro: `PYTHONPATH=scripts python3 "
            "scripts/fin_sat_path3_path4_livestack_t0_twin_stageb.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{pack_verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(screen, indent=2, default=str) + "\n"
    )
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{pack_verdict}__NO_LIVE",
        "verdict": pack_verdict,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": "PATH3_PATH4_LIVESTACK_T0_TWIN",
        "champion_arm": champion["arm"],
        "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
        "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
        "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
        "optimize_live": rec,
        "soft_keep": True,
        "broker": False,
        "path4_live": False,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · base **{BASE_ID}**",
            "",
            "## Champion vs live Exact T+1",
            "",
            f"- held CAGR lift: **{champion['held_cagr_lift_pp']}** pp",
            f"- full CAGR lift: **{champion['full_cagr_lift_pp']}** pp",
            f"- sealed MDD improve: **{champion['sealed_mdd_improve_pp']}** pp",
            f"- tipY / tip1y: **{champion['tip_ytd_cagr_lift_pp']}** / "
            f"**{champion['tip_1y_cagr_lift_pp']}**",
            f"- meta: `{champion.get('meta')}`",
            "",
            "## How to optimize live (T+0 clock)",
            "",
            *[f"{i+1}. {s}" for i, s in enumerate(rec)],
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
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
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
                "optimize_live": rec,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
