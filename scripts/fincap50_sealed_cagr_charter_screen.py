#!/usr/bin/env python3
"""FIN_CAP_50 sealed-CAGR charter gate screen — RESEARCH_ONLY.

Applies research/gaps/FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md gates to:
  1) Existing sealed-CAGR improve diagnostic candidates
  2) Operating dual-paper trailing (FIN50 / L4_DD_PATH month-end)
  3) Recomputed ytd / trailing_1y for hist-pass candidates

Never flips Soft-Frozen. Never cutover. Never retunes FIN_CAP_50 lock.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e50_early_stack_combined_nav import e16_features, simulate_core
import e22_dividend_accounting as e22div
from e16_fin_cap_oof_challenger import e16_features_fin_cap
from fincap_sealed_cagr_improve_diag import (
    blend_targets,
    load_market,
    path_conditional_target,
    score,
)

ROOT = Path(__file__).resolve().parents[1]
DIAG_JSON = ROOT / "research/gaps/FINCAP_SEALED_CAGR_IMPROVE_DIAGNOSTIC.json"
FIN_MON = ROOT / "research/gaps/FIN_CAP_50_MONTH_END_MONITOR.json"
L4_MON = ROOT / "research/gaps/L4_DD_PATH_MONTH_END_MONITOR.json"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"
OUT_DIR = ROOT / "repro/fincap50-sealed-cagr-charter-screen"
RESEARCH = ROOT / "research/gaps"

OOF_MDD_MIN = 1.0
OOF_LATE_CAGR_GB_MAX = 1.5
SEALED_CAGR_GB_MAX = 3.0
SEALED_MDD_MIN = 1.0
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0

FAMILY_MAP = {
    "L4-CRISIS-ONLY": ["CRISIS_ONLY_50"],
    "L4-FINCAP-70": ["FIN_CAP_70_STATIC"],
    "L4-BLEND-LIGHT": ["BLEND_025", "BLEND_050"],
    "L4-DD-PATH": ["DD_BEAR_CRISIS_50"],
}
BLOCKED_REF = {"FIN_CAP_50_REF", "L3_MILD_35_60_REF"}


def _f(x):
    try:
        return None if x is None else float(x)
    except (TypeError, ValueError):
        return None


def hist_gate(c: dict) -> dict:
    oof_mdd = _f(c.get("oof_mdd_improve_pp"))
    oof_gb = _f(c.get("oof_cagr_giveback_pp"))
    late_gb = _f(c.get("late_bull_cagr_giveback_pp"))
    sealed_mdd = _f(c.get("sealed_mdd_improve_pp"))
    sealed_gb = _f(c.get("sealed_cagr_giveback_pp"))
    checks = {
        "exact_t1": bool(c["exact_t1_ok"]) if "exact_t1_ok" in c else False,
        "oof_mdd_ge_1pp": oof_mdd is not None and oof_mdd >= OOF_MDD_MIN,
        "oof_cagr_gb_le_1_5pp": oof_gb is not None and oof_gb <= OOF_LATE_CAGR_GB_MAX,
        "late_bull_cagr_gb_le_1_5pp": late_gb is not None and late_gb <= OOF_LATE_CAGR_GB_MAX,
        "sealed_cagr_gb_le_3pp": sealed_gb is not None and sealed_gb <= SEALED_CAGR_GB_MAX,
        "sealed_mdd_ge_1pp": sealed_mdd is not None and sealed_mdd >= SEALED_MDD_MIN,
        "not_blocked_static_ref": c.get("id") not in BLOCKED_REF,
    }
    return {
        "checks": checks,
        "hist_pass": all(checks.values()),
        "metrics": {
            "oof_mdd_improve_pp": oof_mdd,
            "oof_cagr_giveback_pp": oof_gb,
            "late_bull_cagr_giveback_pp": late_gb,
            "sealed_mdd_improve_pp": sealed_mdd,
            "sealed_cagr_giveback_pp": sealed_gb,
        },
    }


def trail_from_monitor(path: Path, sleeve: str) -> dict:
    if not path.exists():
        return {"available": False, "sleeve": sleeve}
    doc = json.loads(path.read_text())
    alerts = [str(a) for a in (doc.get("alerts") or [])]
    pause = any("PAUSE_REVIEW" in a for a in alerts) or bool(doc.get("cutover_blocked"))
    windows = {}
    for row in doc.get("windows") or []:
        w = row.get("window")
        if w in ("ytd", "trailing_1y"):
            windows[w] = {
                "cagr_giveback_pp": row.get("cagr_giveback_pp"),
                "mdd_improve_pp": row.get("mdd_improve_pp"),
            }
    alert = any(
        (_f((windows.get(w) or {}).get("cagr_giveback_pp")) or -1e9) > TRAIL_ALERT_PP
        for w in ("ytd", "trailing_1y")
    )
    return {
        "available": True,
        "sleeve": sleeve,
        "pause_review": pause,
        "cutover_blocked": bool(doc.get("cutover_blocked")),
        "authoritative_go_live_status": doc.get("authoritative_go_live_status"),
        "alerts": alerts,
        "windows": windows,
        "trail_pass": (not pause) and (not alert),
    }


def compute_trailing(ids: list[str]) -> dict[str, dict]:
    if not ids:
        return {}
    print("loading market for trailing windows ...", flush=True)
    market = load_market()
    dividends = (
        pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()
    )
    _p, _s, base_t, base_reg = e16_features(market)
    _p50, _s50, fin50_t, _ = e16_features_fin_cap(market, 0.35, 0.50)
    _p70, _s70, fin70_t, _ = e16_features_fin_cap(market, 0.50, 0.70)
    cr50_t, _ = path_conditional_target(base_t, fin50_t, base_reg, "crisis_only")
    dd50_t, _ = path_conditional_target(base_t, fin50_t, base_reg, "dd_only")
    blend25_t = blend_targets(base_t, fin50_t, 0.25)
    blend50_t = blend_targets(base_t, fin50_t, 0.50)

    targets = {
        "BASE": base_t,
        "FIN_CAP_70_STATIC": fin70_t,
        "BLEND_025": blend25_t,
        "BLEND_050": blend50_t,
        "CRISIS_ONLY_50": cr50_t,
        "DD_BEAR_CRISIS_50": dd50_t,
    }
    need = ["BASE"] + [i for i in ids if i in targets]
    navs: dict[str, pd.DataFrame] = {}
    for cid in need:
        print(f"  trailing sim {cid} ...", flush=True)
        nav, _fills, _meta = simulate_core(
            market,
            targets[cid],
            base_reg,
            dividends,
            apply_e22=True,
            e22_version=e22div.E22_V2S,
            apply_stock_div=True,
        )
        navs[cid] = nav

    asof = pd.to_datetime(navs["BASE"]["date"]).dt.date.max()
    ytd = (date(asof.year, 1, 1), asof)
    t1_start = date.fromordinal(max(asof.toordinal() - 365, date(2000, 1, 1).toordinal()))
    out: dict[str, dict] = {}
    for cid in ids:
        if cid not in navs:
            out[cid] = {"available": False, "reason": "unknown_target_id"}
            continue
        y = score(navs["BASE"], navs[cid], ytd[0], ytd[1], "ytd")
        t = score(navs["BASE"], navs[cid], t1_start, asof, "trailing_1y")
        ygb = _f(y.get("cagr_giveback_pp"))
        tgb = _f(t.get("cagr_giveback_pp"))
        pause = (ygb is not None and ygb > TRAIL_PAUSE_PP) or (
            tgb is not None and tgb > TRAIL_PAUSE_PP
        )
        alert = (ygb is not None and ygb > TRAIL_ALERT_PP) or (
            tgb is not None and tgb > TRAIL_ALERT_PP
        )
        out[cid] = {
            "available": True,
            "asof": str(asof),
            "ytd": y,
            "trailing_1y": t,
            "pause_review": pause,
            "alert": alert,
            "trail_pass": (not pause) and (not alert),
        }
    return out


def main() -> int:
    if not DIAG_JSON.exists():
        raise SystemExit(f"missing {DIAG_JSON}")

    diag = json.loads(DIAG_JSON.read_text())
    cands = [c for c in (diag.get("candidates") or []) if c.get("id") and c["id"] != "BASE"]

    hist_rows = []
    hist_pass_ids = []
    for c in cands:
        g = hist_gate(c)
        hist_rows.append({"id": c["id"], "family": c.get("family"), **g})
        if g["hist_pass"]:
            hist_pass_ids.append(c["id"])

    trail_ids = sorted(set(hist_pass_ids) | {"DD_BEAR_CRISIS_50"})
    trailing = compute_trailing(trail_ids)

    fin_trail = trail_from_monitor(FIN_MON, "FIN_CAP_50")
    l4_trail = trail_from_monitor(L4_MON, "L4_DD_PATH_08_50")

    family_results = []
    promote_eligible = []
    for fam, ids in FAMILY_MAP.items():
        members = []
        for cid in ids:
            h = next((r for r in hist_rows if r["id"] == cid), None)
            t = trailing.get(cid) or {"available": False}
            charter_pass = bool(h and h["hist_pass"] and t.get("trail_pass"))
            members.append(
                {
                    "id": cid,
                    "hist_pass": bool(h and h["hist_pass"]),
                    "trail_pass": bool(t.get("trail_pass")),
                    "charter_pass": charter_pass,
                    "hist": h,
                    "trailing": t,
                }
            )
            if charter_pass:
                promote_eligible.append({"family": fam, "id": cid})
        family_results.append(
            {
                "family": fam,
                "any_charter_pass": any(m["charter_pass"] for m in members),
                "members": members,
                "operating_dual_paper": l4_trail if fam == "L4-DD-PATH" else None,
            }
        )

    if promote_eligible:
        decision = "PAPER_PROMOTE_PROPOSAL_ONLY"
        exit_hint = (
            "Named challenger may enter dual-paper observe + promote proposal only "
            "(not live cutover)."
        )
    elif hist_pass_ids:
        decision = "HIST_PASS_TRAIL_FAIL"
        exit_hint = (
            "STOP for promote — hist gates clear for some families but trailing FAIL; "
            "keep FIN50 dual-paper; Soft-Frozen KEEP."
        )
    else:
        decision = "NO_FAMILY_CLEARS_HIST_GATES"
        exit_hint = "STOP — no family clears hist gates; keep FIN50 dual-paper; Soft-Frozen KEEP."

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FINCAP50_SEALED_CAGR_CHARTER_SCREEN",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "soft_frozen_clip": [0.50, 0.95],
        "charter": "research/gaps/FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md",
        "diagnostic_source": str(DIAG_JSON),
        "gates": {
            "oof_mdd_min_pp": OOF_MDD_MIN,
            "oof_late_cagr_gb_max_pp": OOF_LATE_CAGR_GB_MAX,
            "sealed_cagr_gb_max_pp": SEALED_CAGR_GB_MAX,
            "sealed_mdd_min_pp": SEALED_MDD_MIN,
            "trail_alert_pp": TRAIL_ALERT_PP,
            "trail_pause_pp": TRAIL_PAUSE_PP,
        },
        "hist_pass_ids": hist_pass_ids,
        "promote_eligible": promote_eligible,
        "decision": decision,
        "charter_exit_hint": exit_hint,
        "operating_dual_paper": {"FIN_CAP_50": fin_trail, "L4_DD_PATH_08_50": l4_trail},
        "families": family_results,
        "hist_rows": hist_rows,
        "forbidden": [
            "Soft-Frozen flip",
            "retune FIN_CAP_50 lock",
            "live cutover without CUTOVER_CHECKLIST_FIN50 + human PR",
        ],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    lines = [
        "# FIN_CAP_50 Sealed-CAGR Charter Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **RESEARCH_ONLY** — Soft-Frozen **[0.50, 0.95] KEEP**; no cutover.",
        "",
        f"## Decision: **{decision}**",
        "",
        exit_hint,
        "",
        "### Hist-pass IDs (OOF / late-bull / sealed)",
        "",
    ]
    lines += [f"- `{i}`" for i in hist_pass_ids] or ["- None"]
    lines += ["", "### Promote-eligible (hist + trailing)", ""]
    lines += [f"- `{p['family']}` / `{p['id']}`" for p in promote_eligible] or ["- None"]
    lines += [
        "",
        "### Operating dual-paper trailing",
        "",
        f"- FIN_CAP_50 pause/cutover_blocked: **{fin_trail.get('pause_review')}** / **{fin_trail.get('cutover_blocked')}**",
        f"- L4_DD_PATH_08_50 pause/cutover_blocked: **{l4_trail.get('pause_review')}** / **{l4_trail.get('cutover_blocked')}**",
        "",
        "### Family table",
        "",
        "| Family | Member | Hist pass | Trail pass | Charter pass |",
        "|---|---|---|---|---|",
    ]
    for fam in family_results:
        for m in fam["members"]:
            lines.append(
                f"| `{fam['family']}` | `{m['id']}` | {m['hist_pass']} | {m['trail_pass']} | {m['charter_pass']} |"
            )
    lines += [
        "",
        "## Hard rules",
        "",
        "- Do not retune FIN_CAP_50 lock",
        "- Do not Soft-Frozen flip",
        "- Passing charter ≠ live cutover",
        "",
        "Re-run: `python3 scripts/fincap50_sealed_cagr_charter_screen.py`",
        "",
    ]
    text = "\n".join(lines)
    (OUT_DIR / "FINCAP50_SEALED_CAGR_CHARTER_SCREEN.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    (OUT_DIR / "FINCAP50_SEALED_CAGR_CHARTER_SCREEN.md").write_text(text)
    (RESEARCH / "FINCAP50_SEALED_CAGR_CHARTER_SCREEN.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    (RESEARCH / "FINCAP50_SEALED_CAGR_CHARTER_SCREEN.md").write_text(text)
    print(
        json.dumps(
            {
                "decision": decision,
                "hist_pass_ids": hist_pass_ids,
                "promote_eligible": promote_eligible,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
