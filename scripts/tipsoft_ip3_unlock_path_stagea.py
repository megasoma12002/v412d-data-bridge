#!/usr/bin/env python3
"""Stage A: unlock paths for perfection ladder step 2 (0kb8 reopen_if).

Two tracks:
A. Soft FIN/TEL refill — loosen Path3 WITHIN (re-enable Soft Exact T+1 FIN∪TEL
   on Path3 OFF / as stack). Tip Soft ceiling = MUTE_S3_SAT / OVERRIDE.
B. High-ON% Path3 gate + non-Soft fill (FREEZE / FT→0050 / FT→CASH) under Soft
   FIN/TEL stay OFF — Soft-core T+0 carve sim vs ALWAYS_WITHIN.

Parents 0kb8/0kb7/0kb6/0kac · Soft KEEP · Path4 OFF · broker false · no live.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, load_or_build_signal
from ops_repro_ssot import write_ops_and_repro_pointer
from path3_comp_sat_daily_share_ssot import load_book_shares
import tipsoft_ip3_fill_lock_stagea as fl

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-unlock-path-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TIPSOFT_IP3_UNLOCK_PATH_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_UNLOCK_PATH_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_UNLOCK_PATH_STAGEA_DECISION_PACK"
REGISTER = "0kb9"
PARENTS = ("0kb8", "0kb7", "0kb6", "0kac")
MECH = "TIPSOFT_IP3_UNLOCK_PATH"

SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_EDGE_PP = 0.05
# High-ON gates must be meaningfully intermittent but not ~10% MUTE
MIN_ON_PCT = 50.0
MAX_ON_PCT = 98.0


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gate_catalog() -> dict[str, pd.Series]:
    live_r, prem_p3, near, sat = fl._path3_panel()
    tr63 = fl._trail_sum(prem_p3, 63).fillna(0.0)
    tr42 = fl._trail_sum(prem_p3, 42).fillna(0.0)
    tr21 = fl._trail_sum(prem_p3, 21).fillna(0.0)
    mute_only = (tr63 < -0.01) & sat.fillna(False)
    i3_mute = fl._three_state_mute_sat(near, sat, prem_p3)
    return {
        "MUTE_S3_SAT": i3_mute.astype(float),
        "NEARPEAK3": near.astype(float),
        "ON_UNLESS_MUTE": (~mute_only).astype(float),
        "TRAIL63_GE_m001": (tr63 >= -0.01).astype(float),
        "TRAIL63_GE_0": (tr63 >= 0.0).astype(float),
        "TRAIL42_GE_m001": (tr42 >= -0.01).astype(float),
        "TRAIL21_GE_m001": (tr21 >= -0.01).astype(float),
        "ALWAYS": pd.Series(1.0, index=live_r.index),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    # --- Track A: Soft FIN/TEL refill (loosen WITHIN) ---
    l4 = fl._load_nav(fl.ALIGN / "nav_L4_LIVE_P3_WITHIN.csv")
    mute_nav = fl._load_nav(fl.STACK / "nav_REF_MUTE_S3_SAT_W63.csv")
    ov_nav = fl._load_nav(
        ROOT
        / "repro/tipsoft-ip3-live-override-paper-observe/outputs/nav_OVERRIDE_LIVE_W42_M05_K3.csv"
    )
    l3 = fl._load_nav(fl.LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    l4_w = fl._pack(l4)
    track_a = [
        fl._row(
            "A_SOFT_REFILL_MUTE",
            "Soft FIN/TEL refill = MUTE_S3_SAT vs L4 (loosen WITHIN)",
            "tipsoft_exact_t1",
            mute_nav,
            l4,
            l4_w,
            feasible=False,
            soft_fin_tel_required=True,
        ),
        fl._row(
            "A_SOFT_REFILL_OVERRIDE",
            "Soft refill + LIVE_OVERRIDE blend vs L4",
            "tipsoft_exact_t1",
            ov_nav,
            l4,
            l4_w,
            feasible=False,
            soft_fin_tel_required=True,
        ),
        fl._row(
            "A_COST_ALWAYS_SOFT_L3",
            "diagnostic: always Soft shell (no Path3) vs L4",
            "tipsoft_exact_t1",
            l3,
            l4,
            l4_w,
            feasible=False,
            soft_fin_tel_required=True,
        ),
    ]
    for r in track_a:
        # nav already on disk from priors; copy tip refs
        pass
    mute_nav.to_csv(OUT / "nav_A_SOFT_REFILL_MUTE.csv", index=False)
    ov_nav.to_csv(OUT / "nav_A_SOFT_REFILL_OVERRIDE.csv", index=False)
    l3.to_csv(OUT / "nav_A_COST_ALWAYS_SOFT_L3.csv", index=False)
    l4.to_csv(OUT / "nav_REF_L4.csv", index=False)

    # --- Track B: high-ON% gates × Soft-core fills ---
    gates = _gate_catalog()
    gate_info = {
        k: {"pct_on": round(float(v.mean()) * 100.0, 4), "n": int(len(v))}
        for k, v in gates.items()
    }
    high_on = {
        k: v
        for k, v in gates.items()
        if MIN_ON_PCT <= gate_info[k]["pct_on"] <= MAX_ON_PCT
    }

    px = fl._close_panel(fl.SOFT_CORE)
    weights = {
        BOOK_COMP: fl._book_soft_weights(load_book_shares(BOOK_COMP), px),
        BOOK_SAT: fl._book_soft_weights(load_book_shares(BOOK_SAT), px),
    }
    sig = load_or_build_signal()

    # baseline ALWAYS_WITHIN under dummy always-on gate
    base_nav, base_meta = fl.simulate_fill(
        fill="ALWAYS_WITHIN",
        weights_by_book=weights,
        px=px,
        signal=sig,
        i3_on=gates["ALWAYS"],
    )
    base_nav.to_csv(OUT / "nav_B_ALWAYS_WITHIN.csv", index=False)
    base_w = fl._pack(base_nav)

    fills = ("FREEZE", "FT_TO_0050", "FT_TO_CASH")
    track_b: list[dict[str, Any]] = []
    track_b.append(
        fl._row(
            "B_ALWAYS_WITHIN",
            "Soft-core daily Path3 baseline",
            "softcore_t0",
            base_nav,
            base_nav,
            base_w,
            feasible=True,
            soft_fin_tel_required=False,
            meta=base_meta,
        )
    )

    for gname, gser in high_on.items():
        for fill in fills:
            arm = f"B_{gname}__{fill}"
            nav, meta = fl.simulate_fill(
                fill=fill,
                weights_by_book=weights,
                px=px,
                signal=sig,
                i3_on=gser,
            )
            meta = dict(meta)
            meta["gate"] = gname
            meta["pct_on_gate"] = gate_info[gname]["pct_on"]
            nav.to_csv(OUT / f"nav_{arm}.csv", index=False)
            track_b.append(
                fl._row(
                    arm,
                    f"high-ON {gname} × {fill}",
                    "softcore_t0",
                    nav,
                    base_nav,
                    base_w,
                    feasible=True,
                    soft_fin_tel_required=False,
                    meta=meta,
                )
            )

    # Also report MUTE low-ON fills as negative controls (already known blocked)
    for fill in fills:
        arm = f"B_MUTE_S3_SAT__{fill}"
        nav, meta = fl.simulate_fill(
            fill=fill,
            weights_by_book=weights,
            px=px,
            signal=sig,
            i3_on=gates["MUTE_S3_SAT"],
        )
        meta = dict(meta)
        meta["gate"] = "MUTE_S3_SAT"
        meta["pct_on_gate"] = gate_info["MUTE_S3_SAT"]["pct_on"]
        meta["control"] = True
        nav.to_csv(OUT / f"nav_{arm}.csv", index=False)
        track_b.append(
            fl._row(
                arm,
                f"control low-ON MUTE × {fill}",
                "softcore_t0",
                nav,
                base_nav,
                base_w,
                feasible=True,
                soft_fin_tel_required=False,
                meta=meta,
            )
        )

    clears = []
    for r in track_b:
        if r["arm"] == "B_ALWAYS_WITHIN":
            continue
        if r.get("meta", {}).get("control"):
            continue
        held = r["held_cagr_lift_pp"]
        if held is None or float(held) <= HELD_EDGE_PP:
            continue
        sealed = r["sealed_mdd_improve_pp"]
        tipy = r["tipY_pp"]
        sealed_ok = sealed is None or float(sealed) >= SEALED_MDD_FLOOR_PP
        tip_ok = tipy is None or float(tipy) >= TIP_Y_FLOOR_PP
        if sealed_ok and tip_ok:
            clears.append(r)

    best_b = None
    if clears:
        best_b = max(clears, key=lambda x: float(x["held_cagr_lift_pp"]))

    a_mute = next(r for r in track_a if r["arm"] == "A_SOFT_REFILL_MUTE")
    a_ov = next(r for r in track_a if r["arm"] == "A_SOFT_REFILL_OVERRIDE")

    if clears:
        verdict = "UNLOCK_HIGHON_FILL_HIT"
    elif float(a_mute["held_cagr_lift_pp"] or 0) > HELD_EDGE_PP:
        verdict = "UNLOCK_SOFT_REFILL_ONLY"
    else:
        verdict = "UNLOCK_NO_PATH"

    rows = track_a + [{k: v for k, v in r.items()} for r in track_b]
    flat = []
    for r in rows:
        d = {k: v for k, v in r.items() if k != "meta"}
        meta = r.get("meta") or {}
        d["gate"] = meta.get("gate")
        d["pct_on_gate"] = meta.get("pct_on_gate")
        d["pct_off"] = meta.get("pct_off")
        flat.append(d)
    pd.DataFrame(flat).to_csv(OUT / "unlock_arms.csv", index=False)

    optimize = [
        "Question: Soft FIN/TEL refill (loosen WITHIN) vs high-ON% gate + new fill?",
        (
            f"Verdict `{verdict}`: Soft-refill MUTE tipY **+{a_mute['tipY_pp']}** held "
            f"**+{a_mute['held_cagr_lift_pp']}** · OVERRIDE tipY **+{a_ov['tipY_pp']}** "
            f"(requires Soft FIN/TEL Exact T+1 carve / WITHIN loosen ACCEPT)"
        ),
        (
            f"High-ON gate catalog: "
            + ", ".join(f"{k}={gate_info[k]['pct_on']}%" for k in sorted(high_on))
        ),
        (
            "Track B Soft-core clears (held>+0.05 · sealedMDD≥−0.25 · tipY≥−1): "
            + (
                f"**{best_b['arm']}** held **{best_b['held_cagr_lift_pp']}** tipY "
                f"**{best_b['tipY_pp']}** sealedMDD **{best_b['sealed_mdd_improve_pp']}**"
                if best_b
                else f"**0** / {len(high_on)*len(fills)} high-ON arms"
            )
        ),
        (
            "Disposition: "
            + (
                "promote high-ON fill champion → tip Soft twin Stage B / observe draft"
                if verdict == "UNLOCK_HIGHON_FILL_HIT"
                else "only Soft-refill unlocks tip Soft tipY — needs explicit WITHIN-loosen ACCEPT; "
                "high-ON+non-Soft fill does not clear Soft-core floors"
                if verdict == "UNLOCK_SOFT_REFILL_ONLY"
                else "no unlock path"
            )
        ),
        "Soft KEEP · Path4 OFF · broker false · no live wire this pack",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "track_a_soft_refill": {
            "mute_vs_L4": {
                "held_pp": a_mute["held_cagr_lift_pp"],
                "tipY_pp": a_mute["tipY_pp"],
                "sealed_mdd_pp": a_mute["sealed_mdd_improve_pp"],
            },
            "override_vs_L4": {
                "held_pp": a_ov["held_cagr_lift_pp"],
                "tipY_pp": a_ov["tipY_pp"],
                "sealed_mdd_pp": a_ov["sealed_mdd_improve_pp"],
            },
            "requires": "ACCEPT loosen WITHIN / Soft FIN/TEL Exact T+1 carve",
            "ballot_cost": "Undo or carve 0kac WITHIN Soft FIN/TEL OFF daily",
        },
        "track_b_highon_fill": {
            "gates": {k: gate_info[k] for k in high_on},
            "all_gates": gate_info,
            "n_arms": len(high_on) * len(fills),
            "n_clears": int(len(clears)),
            "best": best_b,
            "floors": {
                "held_edge_pp": HELD_EDGE_PP,
                "sealed_mdd_pp": SEALED_MDD_FLOOR_PP,
                "tipY_pp": TIP_Y_FLOOR_PP,
                "on_pct_band": [MIN_ON_PCT, MAX_ON_PCT],
            },
        },
        "arms": rows,
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "live_wire": False,
        "label": f"{SCREEN_ID}_{generated[:10]}__{verdict}",
    }
    (OUT / "screen.json").write_text(
        json.dumps(screen, indent=2, default=str) + "\n", encoding="utf-8"
    )

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Which unlock reopens ladder step 2: **(A)** Soft FIN/TEL refill "
            "(loosen WITHIN), or **(B)** high-ON% Path3 gate + freeze/0050/cash fill "
            "while Soft FIN/TEL stay OFF?",
            "",
            "## Method",
            "",
            "- Track A: tip Soft Exact T+1 MUTE_S3_SAT / OVERRIDE vs L4 (Soft-refill ceiling)",
            "- Track B: Soft-core T+0 · gates with ON% in [50,98] · fills FREEZE/0050/CASH "
            "vs ALWAYS_WITHIN",
            "- Floors: held > +0.05 · sealed MDD ≥ −0.25 · tipY ≥ −1.0",
            "",
            "## Forbidden",
            "",
            "- Silent WITHIN undo · Path4 live · broker · year-cut · live apply without ACCEPT",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.json",
        REP / f"{CHARTER_ID}.json",
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "question": "Soft refill vs high-ON fill unlock",
                "label": f"{CHARTER_ID}_{generated[:10]}",
            },
            indent=2,
        )
        + "\n",
        kind="charter json",
    )

    lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {generated[:10]} · Register: **{REGISTER}** · Verdict: **`{verdict}`**",
        "",
        "## Track A — Soft FIN/TEL refill (loosen WITHIN)",
        "",
        f"- MUTE vs L4: held **+{a_mute['held_cagr_lift_pp']}** tipY **+{a_mute['tipY_pp']}** "
        f"sealedMDD **{a_mute['sealed_mdd_improve_pp']}**",
        f"- OVERRIDE vs L4: held **+{a_ov['held_cagr_lift_pp']}** tipY **+{a_ov['tipY_pp']}**",
        "- Requires explicit ACCEPT to carve/undo Soft FIN/TEL OFF under 0kac WITHIN",
        "",
        "## Track B — high-ON% × fill (Soft FIN/TEL OFF)",
        "",
        f"Gates in band: {', '.join(f'`{k}` {gate_info[k]['pct_on']}%' for k in sorted(high_on))}",
        f"Clears: **{len(clears)}** / {len(high_on)*len(fills)}",
        "",
        "| Arm | held | tipY | sealedMDD | ON% |",
        "|---|---:|---:|---:|---:|",
    ]
    show = [r for r in track_b if r["arm"] != "B_ALWAYS_WITHIN"]
    show = sorted(
        show,
        key=lambda x: float(x["held_cagr_lift_pp"] or -1e9),
        reverse=True,
    )[:12]
    for r in show:
        lines.append(
            f"| `{r['arm']}` | {r['held_cagr_lift_pp']} | {r['tipY_pp']} | "
            f"{r['sealed_mdd_improve_pp']} | {(r.get('meta') or {}).get('pct_on_gate')} |"
        )
    lines += ["", "## Optimize live", ""]
    for i, line in enumerate(optimize, 1):
        lines.append(f"{i}. {line}")
    lines += ["", f"Label: `{screen['label']}`", ""]
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md",
        REP / f"{SCREEN_ID}.md",
        "\n".join(lines),
        kind="screen",
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.json",
        REP / f"{SCREEN_ID}.json",
        json.dumps(screen, indent=2, default=str) + "\n",
        kind="screen json",
    )

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Answer",
            "",
            (
                "**High-ON% + non-Soft fill clears Soft-core floors — candidate unlock without Soft FIN/TEL.**"
                if verdict == "UNLOCK_HIGHON_FILL_HIT"
                else "**Only Soft FIN/TEL refill unlocks tip Soft tipY; high-ON% + freeze/0050/cash does not.**"
                if verdict == "UNLOCK_SOFT_REFILL_ONLY"
                else "**No unlock path cleared.**"
            ),
            "",
            "### Track A (loosen WITHIN)",
            f"- MUTE Soft-refill vs L4: held **+{a_mute['held_cagr_lift_pp']}** tipY **+{a_mute['tipY_pp']}**",
            f"- OVERRIDE vs L4: held **+{a_ov['held_cagr_lift_pp']}** tipY **+{a_ov['tipY_pp']}**",
            "- Ballot cost: carve/undo 0kac Soft FIN/TEL Exact T+1 OFF — **not** silent",
            "",
            "### Track B (Soft FIN/TEL stay OFF)",
            (
                f"- Best clear: **`{best_b['arm']}`** held **{best_b['held_cagr_lift_pp']}** "
                f"tipY **{best_b['tipY_pp']}**"
                if best_b
                else f"- Clears: **0** / {len(high_on)*len(fills)} high-ON arms"
            ),
            "",
            "## Disposition",
            "",
            (
                "- Next: tip Soft Exact T+1 twin of high-ON fill champion → Stage B / observe"
                if verdict == "UNLOCK_HIGHON_FILL_HIT"
                else "- Next: KEEP ladder step 1 · Soft-refill only via **explicit** WITHIN-loosen ACCEPT ballot "
                "(human) · do not promote high-ON fill"
                if verdict == "UNLOCK_SOFT_REFILL_ONLY"
                else "- Next: KEEP step 1"
            ),
            "- Path4 OFF · broker false · no live wire this pack",
            "",
            "## Next (optimize list)",
            "",
        ]
    )
    for i, line in enumerate(optimize, 1):
        decision_md += f"{i}. {line}\n"
    decision_md += f"\nLabel: `{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE`\n"
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="decision pack",
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(
            {
                "id": DECISION_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "verdict": verdict,
                "generated_at_utc": generated,
                "track_a": screen["track_a_soft_refill"],
                "track_b": {
                    "n_clears": int(len(clears)),
                    "best": best_b,
                    "gates": {k: gate_info[k] for k in high_on},
                },
                "optimize_live": optimize,
                "live_wire": False,
                "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
            },
            indent=2,
            default=str,
        )
        + "\n",
        kind="decision pack json",
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "track_a_mute_tipY": a_mute["tipY_pp"],
                "track_a_mute_held": a_mute["held_cagr_lift_pp"],
                "high_on_gates": {k: gate_info[k]["pct_on"] for k in high_on},
                "n_clears": len(clears),
                "best_b": None
                if best_b is None
                else {
                    "arm": best_b["arm"],
                    "held": best_b["held_cagr_lift_pp"],
                    "tipY": best_b["tipY_pp"],
                    "sealed_mdd": best_b["sealed_mdd_improve_pp"],
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
