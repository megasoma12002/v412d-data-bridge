#!/usr/bin/env python3
"""Tip Soft hybrid runner Stage A (0kas) — Soft T+1 overlays + P3/P4 T+0 carve.

Default promote-gate twin from research↔live alignment (0kar P2/P3):
score Path3/Path4 as Exact T+0 carve premium on ``BASE_LIVE_FUSE_COOL``.

Arms vs ``BASE_LIVE_FUSE_COOL``:
- ``TIPSOFT_P3_WITHIN_T1`` — 0kap Exact T+1 tip Soft Path3 (clock-mismatch ref)
- ``HYBRID_P3_WITHIN_T0`` — hybrid Path3 WITHIN T+0 carve
- ``HYBRID_P3_P4_CASH_00025_T0`` — hybrid Path3+Path4 CASH T+0 carve

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
from tip_soft_hybrid_runner import RUNNER_ID, run_default_hybrids

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tip-soft-hybrid-runner-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TIP_SOFT_HYBRID_RUNNER_STAGEA_CHARTER"
SCREEN_ID = "TIP_SOFT_HYBRID_RUNNER_STAGEA_SCREEN"
DECISION_ID = "TIP_SOFT_HYBRID_RUNNER_STAGEA_DECISION_PACK"
REGISTER = "0kas"
PARENTS = ("0kar", "0kap", "0kao")

BASE_ID = "BASE_LIVE_FUSE_COOL"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10


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


def yearly_compare(nav_keep: pd.DataFrame, nav_chal: pd.DataFrame) -> list[dict[str, Any]]:
    def _yr(nav: pd.DataFrame) -> dict[int, float]:
        x = nav.copy()
        x["date"] = pd.to_datetime(x["date"])
        x["year"] = x["date"].dt.year
        out: dict[int, float] = {}
        for y, g in x.groupby("year"):
            g = g.reset_index(drop=True)
            if len(g) < 2:
                continue
            out[int(y)] = float(g["nav"].iloc[-1] / float(g["nav"].iloc[0]) - 1.0)
        return out

    a, b = _yr(nav_keep), _yr(nav_chal)
    rows = []
    for y in sorted(set(a) | set(b)):
        if y not in a or y not in b:
            continue
        rows.append(
            {
                "year": y,
                "ret_keep_pct": round(a[y] * 100, 4),
                "ret_chal_pct": round(b[y] * 100, 4),
                "ret_lift_pp": round((b[y] - a[y]) * 100, 4),
                "ret_win": bool(b[y] > a[y]),
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


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    built = run_default_hybrids()
    arms: dict[str, pd.DataFrame] = built["arms"]
    metas: dict[str, dict[str, Any]] = built["metas"]

    for arm, nav in arms.items():
        nav.to_csv(OUT / f"nav_{arm}.csv", index=False)

    base = arms[BASE_ID]
    bw = _pack(base)
    rows = []
    for arm, nav in arms.items():
        if arm == BASE_ID:
            continue
        delta = _delta(bw, _pack(nav))
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

    hybrids = [r for r in rows if (r.get("meta") or {}).get("kind") == "tip_soft_hybrid"]
    hit = [r for r in hybrids if r["verdict_vs_live"] in {"HIT", "HELD_HIT"}]
    if hit:
        champion = max(hit, key=_rank)
        pack_verdict = "HYBRID_HIT"
    else:
        soft = [r for r in hybrids if r["verdict_vs_live"] == "SOFT"]
        if soft:
            champion = max(soft, key=_rank)
            pack_verdict = "HYBRID_SOFT"
        else:
            champion = max(hybrids or rows, key=_rank)
            pack_verdict = f"HYBRID_{champion['verdict_vs_live']}"

    t1_ref = next((r for r in rows if r["arm"] == "TIPSOFT_P3_WITHIN_T1"), None)
    h_p3 = next((r for r in rows if r["arm"] == "HYBRID_P3_WITHIN_T0"), None)
    h_p3p4 = next((r for r in rows if r["arm"] == "HYBRID_P3_P4_CASH_00025_T0"), None)

    rec: list[str] = [
        f"Default twin runner = `{RUNNER_ID}` (Soft Exact T+1 overlays + P3/P4 Exact T+0 carve premium)",
    ]
    if h_p3:
        rec.append(
            f"Hybrid Path3 `{h_p3['arm']}` → {h_p3['verdict_vs_live']} "
            f"held {h_p3['held_cagr_lift_pp']} tipY {h_p3['tip_ytd_cagr_lift_pp']} "
            f"sealedMDD {h_p3['sealed_mdd_improve_pp']}"
        )
    if h_p3p4:
        rec.append(
            f"Hybrid P3+P4 `{h_p3p4['arm']}` → {h_p3p4['verdict_vs_live']} "
            f"held {h_p3p4['held_cagr_lift_pp']} tipY {h_p3p4['tip_ytd_cagr_lift_pp']} "
            f"sealedMDD {h_p3p4['sealed_mdd_improve_pp']}"
        )
    if t1_ref:
        rec.append(
            f"Contrast Exact T+1 tip Soft Path3 `{t1_ref['arm']}` was "
            f"{t1_ref['verdict_vs_live']} (clock-mismatch ref from 0kap)"
        )
    if pack_verdict == "HYBRID_HIT":
        rec.append(
            f"Champion `{champion['arm']}` clears tip Soft hybrid gates vs live — "
            "still Soft KEEP · Path4 live OFF until ACCEPT ballot"
        )
    elif "MDD_BLOCK" in pack_verdict or "TIP_BLOCK" in pack_verdict:
        rec.append(
            "Hybrid still blocked vs live Soft+FUSE+COOL — keep live stack; "
            "do not promote P3/P4 on Soft-core HIT alone"
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
        "mech": "TIP_SOFT_HYBRID_RUNNER",
        "runner_id": RUNNER_ID,
        "verdict": pack_verdict,
        "base": BASE_ID,
        "champion_arm": champion["arm"],
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
            "Status: **Stage A — tip Soft hybrid runner default twin**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            f"Runner: `{RUNNER_ID}`",
            "",
            "## Question",
            "",
            "Under Soft Exact T+1 FUSE+COOL shell, does Path3/Path4 Exact T+0 carve "
            "premium clear tip Soft promote gates vs ``BASE_LIVE_FUSE_COOL``?",
            "",
            "## Method",
            "",
            "``r_hybrid = r_shell_T1 + (r_softcore_T0 − r_softcore_T1lag)``",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__HYBRID_RUNNER`",
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
                "runner_id": RUNNER_ID,
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
            f"Register: **{REGISTER}** · runner=`{RUNNER_ID}` · base=`{BASE_ID}`",
            "",
            "## Arms vs live Soft+FUSE+COOL",
            "",
            "| Arm | vs live | held | full | sealed MDD↑ | tipY | tip1y | ret W–L |",
            "|---|---|---:|---:|---:|---:|---:|---|",
            *[_fmt(r) for r in summary],
            "",
            "## Optimize / disposition",
            "",
            *[f"{i+1}. {s}" for i, s in enumerate(rec)],
            "",
            "Repro: `PYTHONPATH=scripts python3 "
            "scripts/tip_soft_hybrid_runner_stagea.py`",
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
        "runner_id": RUNNER_ID,
        "champion_arm": champion["arm"],
        "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
        "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
        "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
        "optimize_live": rec,
        "soft_keep": True,
        "broker": False,
        "path4_live": False,
        "default_twin_template": True,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · runner **`{RUNNER_ID}`**",
            "",
            "## Champion vs live",
            "",
            f"- held CAGR lift: **{champion['held_cagr_lift_pp']}** pp",
            f"- full CAGR lift: **{champion['full_cagr_lift_pp']}** pp",
            f"- sealed MDD improve: **{champion['sealed_mdd_improve_pp']}** pp",
            f"- tipY / tip1y: **{champion['tip_ytd_cagr_lift_pp']}** / "
            f"**{champion['tip_1y_cagr_lift_pp']}**",
            "",
            "## Default twin",
            "",
            f"- Adopt `{RUNNER_ID}` as default tip Soft promote-gate twin.",
            "- Soft Exact T+1 overlays KEEP; P3/P4 scored via Exact T+0 carve premium.",
            "",
            "## Next",
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
                "runner_id": RUNNER_ID,
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
