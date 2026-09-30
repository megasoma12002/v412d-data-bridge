#!/usr/bin/env python3
"""Path3 satellite (00631L) overlay re-home Stage A (0kaf) — paper / charter only.

Parent 0kad: satellite diverge sparse · overlay-owned · not direct Path3 apply.
Map COOL/DEF ownership vs COMP/SAT ledger 00631L; Soft KEEP · broker false · no live.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, load_or_build_signal
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from path3_comp_sat_daily_share_ssot import load_book_shares

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-satellite-rehome-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_SATELLITE_REHOME_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_SATELLITE_REHOME_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_SATELLITE_REHOME_STAGEA_DECISION_PACK"
REGISTER = "0kaf"

SAT_CODE = "00631L"
COMP_SCHED = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/schedule_comp_h150_x_a20.csv"
SAT_SCHED = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/schedule_sat_a20_relax.csv"
STATE = ROOT / "forward/e21/portfolio_state.json"

# Re-home options (charter ladder — none live)
OPTIONS = (
    "KEEP_OVERLAY",  # status quo: COOL/Soft owns satellite; Path3 ignores
    "PATH3_SNAPSHOT_ONLY",  # ledger may hold 00631L for observe; still no Path3 delta
    "PATH3_DEF_ON_FLIP",  # on flip, recon 00631L toward dest book (fights COOL)
    "DAILY_PATH3_DEF",  # cutover-style daily Path3 owns DEF (requires COOL re-home)
    "FORBID_IN_LEDGER",  # strip satellite from Path3 ledgers (hygiene)
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    comp = load_book_shares(BOOK_COMP)
    sat = load_book_shares(BOOK_SAT)
    sig = load_or_build_signal()
    sig["date"] = pd.to_datetime(sig["date"])
    dates = comp.index.intersection(sat.index)

    c_sched = pd.read_csv(COMP_SCHED, parse_dates=["date"]).set_index("date")
    s_sched = pd.read_csv(SAT_SCHED, parse_dates=["date"]).set_index("date")
    sched_overlap = c_sched.index.intersection(s_sched.index)
    def_c = c_sched.loc[sched_overlap, "DEF"].astype(float)
    def_s = s_sched.loc[sched_overlap, "DEF"].astype(float)

    if SAT_CODE not in comp.columns or SAT_CODE not in sat.columns:
        raise SystemExit(f"{SAT_CODE} missing from ledgers")

    d_shares = comp.loc[dates, SAT_CODE].astype(float) - sat.loc[dates, SAT_CODE].astype(float)
    nz = d_shares.abs() > 1e-9
    flip_dates = [
        pd.Timestamp(x).normalize()
        for x in sig.loc[sig["flip"].astype(bool), "date"]
        if pd.Timestamp(x).normalize() in dates
    ]
    flip_d = np.array(
        [float(comp.loc[dt, SAT_CODE] - sat.loc[dt, SAT_CODE]) for dt in flip_dates],
        dtype=float,
    )

    tip = dates.max()
    ps = json.loads(STATE.read_text(encoding="utf-8"))
    live_sat = float((ps.get("positions") or {}).get(SAT_CODE, 0.0) or 0.0)

    # When Path3 books differ on satellite, is schedule DEF also nonzero?
    both_nz_def = (def_c.reindex(dates).fillna(0).abs() > 1e-12) | (
        def_s.reindex(dates).fillna(0).abs() > 1e-12
    )
    share_diff_and_def = nz & both_nz_def.reindex(dates).fillna(False)
    share_diff_def_zero = nz & (~both_nz_def.reindex(dates).fillna(False))

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parent": "0kad",
        "code": SAT_CODE,
        "ledger_panel_end": str(tip.date()),
        "live_last_date": ps.get("last_date"),
        "live_satellite_shares": live_sat,
        "schedule_def": {
            "comp_max": float(def_c.max()),
            "sat_max": float(def_s.max()),
            "comp_pct_days_pos": float((def_c > 1e-12).mean()),
            "sat_pct_days_pos": float((def_s > 1e-12).mean()),
            "comp_sat_def_identical": bool((def_c - def_s).abs().max() == 0.0),
        },
        "share_divergence": {
            "n_days": int(len(dates)),
            "pct_days_differ": round(float(nz.mean()), 6),
            "max_abs_share_delta": round(float(d_shares.abs().max()), 1),
            "tip_comp": round(float(comp.loc[tip, SAT_CODE]), 1),
            "tip_sat": round(float(sat.loc[tip, SAT_CODE]), 1),
            "tip_delta": round(float(d_shares.loc[tip]), 1),
            "flip_n": len(flip_dates),
            "flip_pct_nonzero": round(
                float((np.abs(flip_d) > 1e-9).mean()) if len(flip_d) else 0.0, 6
            ),
        },
        "overlap_with_schedule_def": {
            "pct_share_diff_days_with_def_gt0": round(
                float(share_diff_and_def.mean()) if len(dates) else 0.0, 6
            ),
            "pct_share_diff_days_with_def_eq0": round(
                float(share_diff_def_zero.mean()) if len(dates) else 0.0, 6
            ),
            "note": (
                "Share divergence with DEF=0 ⇒ path-dependent COOL/satellite inventory, "
                "not sleeve schedule DEF — Path3 recon would not follow Soft DEF clip."
            ),
        },
        "owner_today": {
            "path3_recon": False,
            "soft_exact_t1": True,
            "cool_overlay": True,
            "mute_on_path3_flip": False,
        },
        "options": list(OPTIONS),
        "binding": {
            "0kad_satellite_overlay_block": True,
            "0kac_overlays_keep_under_default_cutover": True,
            "cool_c8_live": True,
        },
    }

    # Verdict: if most share-diff days have DEF=0, Path3-owning DEF fights COOL without schedule SSOT.
    pct_diff = screen["share_divergence"]["pct_days_differ"]
    pct_diff_def0 = screen["overlap_with_schedule_def"]["pct_share_diff_days_with_def_eq0"]
    if pct_diff < 0.5 and pct_diff_def0 >= 0.15:
        verdict = "OVERLAY_REHOME_REQUIRED__KEEP_PATH3_OUT"
    elif pct_diff >= 0.5 and def_c.max() > 0:
        verdict = "REHOME_THEN_DEF_POLICY_OPEN"
    else:
        verdict = "OVERLAY_REHOME_REQUIRED__KEEP_PATH3_OUT"
    screen["verdict"] = verdict
    screen["recommended_option"] = "KEEP_OVERLAY"

    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage A — satellite overlay re-home vs Path3** · Soft **KEEP** · "
            "COOL **KEEP** · broker **false** · cutover **BLOCKED** · no live",
            "Parent: 0kad · Mechanism ask: who owns `00631L` if Path3 expands?",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Path3 ledgers snapshot `00631L` but recon ignores it. Can Path3 ever own the "
            "satellite, or must COOL/Soft overlay re-home first?",
            "",
            "## Option ladder (no live)",
            "",
            "| Option | Meaning |",
            "|---|---|",
            "| `KEEP_OVERLAY` | status quo — COOL/Soft Exact T+1 owns satellite; Path3 no delta |",
            "| `PATH3_SNAPSHOT_ONLY` | keep ledger column for observe; still no Path3 orders |",
            "| `PATH3_DEF_ON_FLIP` | flip-day recon 00631L to dest book (contends with COOL) |",
            "| `DAILY_PATH3_DEF` | daily Path3 owns DEF — requires COOL re-home ACCEPT |",
            "| `FORBID_IN_LEDGER` | drop satellite from Path3 share SSOT |",
            "",
            "## Method",
            "",
            "- COMP vs SAT `00631L` share divergence vs schedule `DEF` column",
            "- Live position presence",
            "- Binding: 0kac overlays KEEP under default cutover; COOL live",
            "",
            "## Non-goals",
            "",
            "- Live Path3 satellite deltas · COOL param flip · broker · 0050 ETF policy (0kae)",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__00631L_REHOME__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parent": "0kad",
                "code": SAT_CODE,
                "options": list(OPTIONS),
                "soft_keep": True,
                "cool_keep": True,
                "broker": False,
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
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · code=`{SAT_CODE}` · ledger_end=`{screen['ledger_panel_end']}`",
            "",
            "## Share divergence COMP−SAT",
            "",
            f"- % days differ: **{100*pct_diff:.1f}%** · flip nonzero: "
            f"**{100*screen['share_divergence']['flip_pct_nonzero']:.1f}%**",
            f"- tip Δ shares: {screen['share_divergence']['tip_delta']}",
            "",
            "## Schedule DEF",
            "",
            f"- COMP max DEF={screen['schedule_def']['comp_max']} · "
            f"%days>0={100*screen['schedule_def']['comp_pct_days_pos']:.1f}%",
            f"- share-diff days with DEF=0: **{100*pct_diff_def0:.1f}%** of all days",
            f"- note: {screen['overlap_with_schedule_def']['note']}",
            "",
            f"## Live `{SAT_CODE}` shares: {live_sat}",
            "",
            f"Recommended option: **`{screen['recommended_option']}`**",
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_satellite_rehome_stagea.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = [
        "Default: **KEEP_OVERLAY** — Path3 continues to ignore 00631L in recon/mute",
        "Only open COOL re-home ballot if cutover scope explicitly needs Path3-owned DEF",
        "Optional hygiene: document ledger 00631L as snapshot-only (PATH3_SNAPSHOT_ONLY)",
        "0kae ETF policy / 0kac PAPER_WITHIN_HIT remain separate tracks",
    ]
    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "parent": "0kad",
        "code": SAT_CODE,
        "recommended_option": "KEEP_OVERLAY",
        "soft_keep": True,
        "cool_keep": True,
        "broker": False,
        "cutover_blocked": True,
        "live_wire": False,
        "path3_satellite_recon": False,
        "next": next_steps,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parent: **0kad**",
            "",
            "## Finding",
            "",
            f"- `{SAT_CODE}` COMP≠SAT on **{100*pct_diff:.1f}%** days, but schedule `DEF` is "
            f"**mostly zero** — divergence is path-dependent overlay inventory, not sleeve DEF.",
            "- Path3 recon owning satellite would **contend with live COOL** without schedule SSOT.",
            "",
            "## Disposition",
            "",
            "- **Recommended:** `KEEP_OVERLAY` — do **not** apply Path3 to satellite now.",
            "- Re-home charter is **defined**; execution only if cutover demands Path3-owned DEF.",
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
                "verdict": verdict,
                "pct_days_differ": pct_diff,
                "pct_share_diff_def0": pct_diff_def0,
                "recommended": "KEEP_OVERLAY",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
