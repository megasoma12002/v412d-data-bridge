#!/usr/bin/env python3
"""Stage B: tip Soft Exact T+1 twin of Soft-core high-ON × FT→CASH (0kb9).

Parent 0kb9 ``UNLOCK_HIGHON_FILL_HIT`` Soft-core champion
``TRAIL42_GE_m001 × FT_TO_CASH`` (+ ``ON_UNLESS_MUTE × CASH``).

Twin stitch (Exact T+1 tip Soft clock):
  tip_r = L4_r + (softcore_fill_r − softcore_ALWAYS_WITHIN_r)

L4 = tip Soft Soft+FUSE+COOL + Path3 WITHIN (live tip twin).
Soft-core delta carries high-ON Path3 + FIN∪TEL→cash on OFF days without
re-enabling Soft Exact T+1 FIN/TEL.

Refs: MUTE Soft-refill ceiling · raw Soft-core fill (wrong-clock diagnostic).

Soft KEEP · Path4 OFF · broker false · no year-cut · no live wire.
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
REPRO = ROOT / "repro" / "tipsoft-ip3-highon-cash-twin-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
UNLOCK = ROOT / "repro" / "tipsoft-ip3-unlock-path-stagea" / "outputs"
STACK = ROOT / "repro" / "tipsoft-ip3-live-stack-race-stagea" / "outputs"

CHARTER_ID = "TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_SCREEN"
DECISION_ID = "TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_DECISION_PACK"
REGISTER = "0kba"
PARENTS = ("0kb9", "0kb8", "0kb7", "0kac")
MECH = "TIPSOFT_IP3_HIGHON_CASH_TWIN"

SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_EDGE_PP = 0.05

CHALLENGERS = (
    ("TWIN_TRAIL42_CASH", "nav_B_TRAIL42_GE_m001__FT_TO_CASH.csv", "TRAIL42_GE_m001"),
    ("TWIN_ON_UNLESS_MUTE_CASH", "nav_B_ON_UNLESS_MUTE__FT_TO_CASH.csv", "ON_UNLESS_MUTE"),
)


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
    if float(sealed_mdd) < SEALED_MDD_FLOOR_PP:
        return "TWIN_MDD_BLOCK"
    if tipy is not None and float(tipy) < TIP_Y_FLOOR_PP:
        return "TWIN_TIP_BLOCK"
    if float(held) > HELD_EDGE_PP:
        return "TWIN_HIT"
    if float(held) > -0.5:
        return "TWIN_SOFT"
    return "TWIN_NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    l4 = _load(ALIGN / "nav_L4_LIVE_P3_WITHIN.csv")
    sc_within = _load(UNLOCK / "nav_B_ALWAYS_WITHIN.csv")
    mute = _load(STACK / "nav_REF_MUTE_S3_SAT_W63.csv")
    l4_w = _pack(l4)
    l4_r = _returns(l4)
    sc_w_r = _returns(sc_within)

    rows: list[dict[str, Any]] = []
    # baseline
    l4.to_csv(OUT / "nav_REF_L4.csv", index=False)
    rows.append(
        _row("REF_L4", "live tip twin / always Path3 WITHIN", "tipsoft_exact_t1", l4, l4, l4_w)
    )

    # Soft-refill ceiling (Track A)
    mute.to_csv(OUT / "nav_REF_SOFT_REFILL_MUTE.csv", index=False)
    rows.append(
        _row(
            "REF_SOFT_REFILL_MUTE",
            "tip Soft Soft-refill ceiling (WITHIN-loosen)",
            "tipsoft_exact_t1",
            mute,
            l4,
            l4_w,
        )
    )

    twin_rows = []
    for arm_id, sc_file, gate in CHALLENGERS:
        sc = _load(UNLOCK / sc_file)
        sc_r = _returns(sc)
        panel = pd.concat(
            {"l4": l4_r, "sc_w": sc_w_r, "sc_f": sc_r}, axis=1, join="inner"
        ).dropna(how="any")
        if panel.empty:
            raise RuntimeError(f"empty panel for {arm_id}")
        twin_r = panel["l4"] + (panel["sc_f"] - panel["sc_w"])
        twin_nav = _nav_from_returns(twin_r, nav0=1.0)
        twin_nav.to_csv(OUT / f"nav_{arm_id}.csv", index=False)
        sc.to_csv(OUT / f"nav_SC_{arm_id}.csv", index=False)
        row = _row(
            arm_id,
            f"tip Soft Exact T+1 twin · Soft-core {gate}×FT→CASH delta on L4",
            "tipsoft_exact_t1_twin",
            twin_nav,
            l4,
            l4_w,
        )
        row["gate"] = gate
        row["softcore_parent"] = sc_file
        row["verdict"] = _arm_verdict(row)
        rows.append(row)
        twin_rows.append(row)

        # wrong-clock diagnostic: raw Soft-core vs L4
        diag = _row(
            f"DIAG_SC_{arm_id}",
            f"raw Soft-core {gate}×CASH vs L4 (wrong clock)",
            "softcore_t0_diag",
            sc,
            l4,
            l4_w,
        )
        diag["verdict"] = _arm_verdict(diag)
        rows.append(diag)

    sc_within.to_csv(OUT / "nav_SC_ALWAYS_WITHIN.csv", index=False)

    hits = [r for r in twin_rows if r["verdict"] == "TWIN_HIT"]
    softs = [r for r in twin_rows if r["verdict"] == "TWIN_SOFT"]
    blocks = [r for r in twin_rows if r["verdict"] in ("TWIN_MDD_BLOCK", "TWIN_TIP_BLOCK")]

    if hits:
        champ = max(hits, key=lambda x: float(x["held_cagr_lift_vs_L4_pp"]))
        verdict = "TWIN_HIT"
    elif softs and not blocks:
        champ = max(softs, key=lambda x: float(x["held_cagr_lift_vs_L4_pp"]))
        verdict = "TWIN_SOFT"
    elif blocks and not hits:
        # pick least-bad blocked or soft
        pool = twin_rows
        champ = max(pool, key=lambda x: float(x["held_cagr_lift_vs_L4_pp"] or -1e9))
        if any(r["verdict"] == "TWIN_MDD_BLOCK" for r in twin_rows):
            verdict = "TWIN_MDD_BLOCK"
        else:
            verdict = "TWIN_TIP_BLOCK"
    else:
        champ = max(twin_rows, key=lambda x: float(x["held_cagr_lift_vs_L4_pp"] or -1e9))
        verdict = champ["verdict"] if twin_rows else "INCOMPLETE"

    refill = next(r for r in rows if r["arm"] == "REF_SOFT_REFILL_MUTE")

    flat = [{k: v for k, v in r.items()} for r in rows]
    pd.DataFrame(flat).to_csv(OUT / "twin_arms.csv", index=False)

    optimize = [
        "Question: does tip Soft Exact T+1 twin of Soft-core high-ON×CASH clear vs L4?",
        (
            f"Verdict `{verdict}`: champion **`{champ['arm']}`** held "
            f"**{champ['held_cagr_lift_vs_L4_pp']}** tipY **{champ['tipY_vs_L4_pp']}** "
            f"sealedMDD **{champ['sealed_mdd_improve_vs_L4_pp']}**"
        ),
        (
            f"Soft-refill ceiling (Track A) held **{refill['held_cagr_lift_vs_L4_pp']}** "
            f"tipY **{refill['tipY_vs_L4_pp']}** — still needs WITHIN-loosen ACCEPT"
        ),
        (
            "Disposition: "
            + (
                "DRAFT dual-paper observe / ACCEPT −P3T0 apply ballot (cash fill · Soft FIN/TEL stay OFF)"
                if verdict == "TWIN_HIT"
                else "KEEP stamps · Soft-core HIT does not traverse tip Soft twin · no ACCEPT apply"
                if verdict in ("TWIN_MDD_BLOCK", "TWIN_TIP_BLOCK", "TWIN_NO_EDGE")
                else "SOFT only — no ACCEPT; optional observe draft / harden"
            )
        ),
        "Soft KEEP · Path4 OFF · broker false · Soft FIN/TEL stay OFF · no live wire",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "base": "L4_LIVE_P3_WITHIN",
        "stitch": "tip_r = L4_r + (softcore_fill_r - softcore_ALWAYS_WITHIN_r)",
        "floors": {
            "held_edge_pp": HELD_EDGE_PP,
            "sealed_mdd_pp": SEALED_MDD_FLOOR_PP,
            "tipY_pp": TIP_Y_FLOOR_PP,
        },
        "champion": champ,
        "arms": rows,
        "n_twin_hit": int(len(hits)),
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
            "Does the tip Soft Exact T+1 twin of Soft-core high-ON × FT→CASH "
            "(`TRAIL42≥−0.01` / `ON_UNLESS_MUTE`) clear held / tipY / sealed MDD vs "
            "L4 live tip twin — without Soft FIN/TEL Exact T+1 re-enable?",
            "",
            "## Method",
            "",
            "- Stitch: `tip_r = L4_r + (softcore_fill_r − softcore_ALWAYS_WITHIN_r)`",
            "- Challengers: TRAIL42×CASH · ON_UNLESS_MUTE×CASH",
            "- Floors: held > +0.05 · sealed MDD ≥ −0.25 · tipY ≥ −1.0",
            "- Ref: Soft-refill MUTE ceiling (Track A)",
            "",
            "## Forbidden",
            "",
            "- Soft FIN/TEL re-enable · Path4 · broker · year-cut · live wire without ACCEPT",
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
                "question": "tip Soft twin of high-ON×CASH",
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
        f"Stitch: `tip_r = L4_r + (SC_fill − SC_WITHIN)` · champion **`{champ['arm']}`**",
        "",
        "| Arm | clock | held | tipY | sealedMDD | verdict |",
        "|---|---|---:|---:|---:|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['arm']}` | {r['clock']} | {r.get('held_cagr_lift_vs_L4_pp')} | "
            f"{r.get('tipY_vs_L4_pp')} | {r.get('sealed_mdd_improve_vs_L4_pp')} | "
            f"{r.get('verdict', '—')} |"
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
                f"**Tip Soft Exact T+1 twin clears — champion `{champ['arm']}`.**"
                if verdict == "TWIN_HIT"
                else f"**Tip Soft twin does not clear (`{verdict}`) — Soft-core HIT ≠ tip Soft promote.**"
            ),
            "",
            f"- Champion vs L4: held **{champ['held_cagr_lift_vs_L4_pp']}** tipY "
            f"**{champ['tipY_vs_L4_pp']}** sealedMDD **{champ['sealed_mdd_improve_vs_L4_pp']}**",
            f"- Soft-refill ceiling tipY **{refill['tipY_vs_L4_pp']}** (WITHIN-loosen only)",
            "",
            "## Disposition",
            "",
            (
                "- DRAFT dual-paper observe ballot for high-ON×CASH −P3T0 apply · Soft FIN/TEL stay OFF"
                if verdict == "TWIN_HIT"
                else "- KEEP `gate_stamps_telemetry` · no ACCEPT apply · ladder step 2 stays closed on tip Soft"
            ),
            "- Soft KEEP · Path4 OFF · broker false · no live wire this pack",
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
                "champion": champ,
                "generated_at_utc": generated,
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
                "champion": {
                    "arm": champ["arm"],
                    "held": champ["held_cagr_lift_vs_L4_pp"],
                    "tipY": champ["tipY_vs_L4_pp"],
                    "sealed_mdd": champ["sealed_mdd_improve_vs_L4_pp"],
                    "verdict": champ.get("verdict"),
                },
                "twins": [
                    {
                        "arm": r["arm"],
                        "held": r["held_cagr_lift_vs_L4_pp"],
                        "tipY": r["tipY_vs_L4_pp"],
                        "sealed_mdd": r["sealed_mdd_improve_vs_L4_pp"],
                        "verdict": r.get("verdict"),
                    }
                    for r in twin_rows
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
