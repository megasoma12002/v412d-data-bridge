#!/usr/bin/env python3
"""DD_SWITCH soak gate — post-stabilize cadence (0kbf).

Order (human 請按照順序修):
  1. Stabilize merged (0kbe) — prerequisite
  2. Soak via daily tip + DD_SWITCH month-end monitor
  3. Soft FIN/TEL · Path4 · broker stay CLOSED until SOAK_PASS
  4. Only then separate ballots (Soft carve / broker EXECUTE / 2020 research)

Does not flip live flags. Soft-Frozen KEEP. Year-switch FORBIDDEN.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "research" / "ops"
REGISTER = "0kbf"
DAY = date.today().isoformat()
ACCEPT_DAY = date(2026, 10, 1)
STABILIZE_ID = "TIPSOFT_LIVE_STABILIZE_2026-10-02"
MONITOR_JSON = OPS / "TIPSOFT_IP3_TRAIL42_L4_SWITCH_MONTH_END_MONITOR.json"
QC_JSON = ROOT / "forward/e21/qc_status.json"
STATE_JSON = ROOT / "forward/e21/portfolio_state.json"
NAV_CSV = ROOT / "forward/e21/nav.csv"
RECON_JSON = OPS / "LIVE_PAPER_RECON.json"
ALERTS_JSON = OPS / "OPS_ALERTS.json"
OUT_STEM = "TIPSOFT_DD_SWITCH_SOAK_GATE"

# Soak PASS floors (ops cadence — not Soft-Frozen gates)
MIN_TIP_DAYS_SINCE_ACCEPT = 20
MIN_CAL_DAYS_SINCE_ACCEPT = 28  # ~1 month-end window
MIN_LIVE_PAPER_OVERLAP = 60
REQUIRE_NO_DD_SWITCH_PAUSE = True


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def collect() -> dict:
    from live_config import LIVE

    tip = None
    if STATE_JSON.exists():
        tip = _load_json(STATE_JSON).get("last_date")
    tip_d = date.fromisoformat(str(tip)) if tip else None
    qc = _load_json(QC_JSON)
    mon = _load_json(MONITOR_JSON)
    recon = _load_json(RECON_JSON)
    alerts_doc = _load_json(ALERTS_JSON)

    nav_days: list[str] = []
    if NAV_CSV.exists():
        nav = pd.read_csv(NAV_CSV, parse_dates=["date"])
        post = nav[nav["date"] >= pd.Timestamp(ACCEPT_DAY)]
        nav_days = [d.date().isoformat() for d in post["date"]]

    cal_days = (tip_d - ACCEPT_DAY).days if tip_d else None
    tip_days = len(nav_days)

    mon_alerts = list(mon.get("alerts") or [])
    mon_pause = [a for a in mon_alerts if "PAUSE" in str(a).upper()]
    # also scan OPS_ALERTS for tipsoft dd_switch PAUSE
    ops_pause = []
    for a in alerts_doc.get("alerts") or []:
        src = str(a.get("source") or "")
        if "tipsoft_ip3_trail42_l4_switch" in src and a.get("severity") == "HIGH":
            ops_pause.append(a)

    overlap_n = None
    for key in ("overlap_n", "n_overlap", "overlap_days"):
        if key in recon:
            overlap_n = recon.get(key)
            break
    if overlap_n is None:
        # parse from alerts message if present
        for a in alerts_doc.get("alerts") or []:
            msg = str(a.get("message") or "")
            if "overlap_n=" in msg:
                try:
                    overlap_n = int(msg.split("overlap_n=")[1].split()[0].split("(")[0])
                except (IndexError, ValueError):
                    pass

    checks = {
        "stabilize_ballot_present": (OPS / f"{STABILIZE_ID}.md").exists(),
        "dd_switch_live": bool(getattr(LIVE, "live_tipsoft_dd_switch", False)),
        "path3_within_live": bool(getattr(LIVE, "live_path3_strategy_cutover", False)),
        "soft_fin_tel_stay_off": bool(getattr(LIVE, "live_path3_strategy_cutover", False)),
        "path4_live_off": not bool(getattr(LIVE, "live_path4", False)),
        "broker_false": not bool(getattr(LIVE, "broker_live_write_accepted", False)),
        "fill_port_paper": str(getattr(LIVE, "fill_port", "")) == "paper",
        "qc_pass": qc.get("status") == "PASS",
        "tip_days_since_accept_ge": tip_days >= MIN_TIP_DAYS_SINCE_ACCEPT,
        "cal_days_since_accept_ge": (cal_days or -1) >= MIN_CAL_DAYS_SINCE_ACCEPT,
        "live_paper_overlap_ge": (overlap_n or -1) >= MIN_LIVE_PAPER_OVERLAP,
        "dd_switch_monitor_no_pause": (not mon_pause) and (not ops_pause)
        if REQUIRE_NO_DD_SWITCH_PAUSE
        else True,
        "dd_switch_monitor_present": MONITOR_JSON.exists(),
    }

    soak_pass = all(
        [
            checks["stabilize_ballot_present"],
            checks["dd_switch_live"],
            checks["qc_pass"],
            checks["tip_days_since_accept_ge"],
            checks["cal_days_since_accept_ge"],
            checks["live_paper_overlap_ge"],
            checks["dd_switch_monitor_no_pause"],
            checks["dd_switch_monitor_present"],
            checks["broker_false"],
            checks["path4_live_off"],
        ]
    )

    status = "SOAK_PASS" if soak_pass else "SOAK_OPEN"

    return {
        "generated_at_utc": _utc(),
        "label": f"{OUT_STEM}_{DAY}__{status}",
        "register": REGISTER,
        "status": status,
        "human_order": [
            "1 Merge stabilize (0kbe) — DONE on main",
            "2 Soak daily tip + DD_SWITCH month-end",
            "3 Soft FIN/TEL · Path4 · broker CLOSED until SOAK_PASS",
            "4 Separate ballots only after SOAK_PASS",
        ],
        "accept_day": ACCEPT_DAY.isoformat(),
        "live_tip": tip,
        "calendar_days_since_accept": cal_days,
        "nav_tip_days_since_accept": tip_days,
        "nav_tip_dates_since_accept": nav_days,
        "floors": {
            "min_tip_days_since_accept": MIN_TIP_DAYS_SINCE_ACCEPT,
            "min_cal_days_since_accept": MIN_CAL_DAYS_SINCE_ACCEPT,
            "min_live_paper_overlap": MIN_LIVE_PAPER_OVERLAP,
            "require_no_dd_switch_pause": REQUIRE_NO_DD_SWITCH_PAUSE,
        },
        "live_locks": {
            "live_tipsoft_dd_switch": bool(LIVE.live_tipsoft_dd_switch),
            "live_path3_strategy_cutover": bool(LIVE.live_path3_strategy_cutover),
            "live_tipsoft_live_override": bool(LIVE.live_tipsoft_live_override),
            "broker_live_write_accepted": bool(LIVE.broker_live_write_accepted),
            "fill_port": str(LIVE.fill_port),
            "path4_live": bool(getattr(LIVE, "live_path4", False)),
        },
        "monitor": {
            "asof": mon.get("asof"),
            "alerts": mon_alerts,
            "pause_lines": mon_pause,
            "ops_high_alerts": ops_pause,
            "cutover_blocked": mon.get("cutover_blocked"),
        },
        "recon_overlap_n": overlap_n,
        "qc_status": qc.get("status"),
        "checks": checks,
        "freeze_until_soak_pass": [
            "No Soft FIN/TEL Exact T+1 refill ACCEPT",
            "No Path4 live",
            "No broker EXECUTE / live-write",
            "No new tip Soft mechanism Stage A / tip apply",
            "No year-switch / year-oracle",
        ],
        "after_soak_pass_ballots": [
            "Optional: Soft FIN/TEL Exact T+1 carve on Path3 OFF days (separate ACCEPT)",
            "Optional: broker EXECUTE (separate ACCEPT; PREP already filed)",
            "Optional: 2020 MDD research only if held+ ∧ y2020 improve (else KEEP residual)",
        ],
        "parents": ["0kbe", "0kbd", "0kac"],
        "non_actions": [
            "Does not flip Soft-Frozen",
            "Does not enable broker",
            "Does not reopen Soft FIN/TEL",
            "Does not promote Path4",
            "Does not rewrite forward/e21 history",
        ],
    }


def write_artifacts(payload: dict) -> None:
    OPS.mkdir(parents=True, exist_ok=True)
    checks = payload["checks"]
    rows = "\n".join(
        f"| `{k}` | {'PASS' if v else 'OPEN'} |" for k, v in checks.items()
    )
    md = "\n".join(
        [
            f"# {OUT_STEM}",
            "",
            f"Date: {DAY} · Status: **{payload['status']}** · register **{REGISTER}**",
            f"Parents: stabilize `{STABILIZE_ID}` · DD_SWITCH tip apply 0kbd",
            "",
            "## Human order",
            "",
            *[f"{i}" for i in payload["human_order"]],
            "",
            "## Snapshot",
            "",
            f"- Live tip: **{payload['live_tip']}** · QC **{payload['qc_status']}**",
            f"- Days since ACCEPT tip apply (2026-10-01): cal **{payload['calendar_days_since_accept']}** · "
            f"nav tip days **{payload['nav_tip_days_since_accept']}**",
            f"- Live↔paper overlap_n: **{payload['recon_overlap_n']}** "
            f"(floor {MIN_LIVE_PAPER_OVERLAP})",
            f"- DD_SWITCH month-end asof: **{payload['monitor']['asof']}** · "
            f"alerts `{payload['monitor']['alerts']}`",
            "",
            "## Floors",
            "",
            f"- tip days ≥ **{MIN_TIP_DAYS_SINCE_ACCEPT}**",
            f"- calendar days ≥ **{MIN_CAL_DAYS_SINCE_ACCEPT}** (~1 month-end)",
            f"- live↔paper overlap ≥ **{MIN_LIVE_PAPER_OVERLAP}**",
            "- DD_SWITCH monitor: no PAUSE_REVIEW",
            "",
            "## Checks",
            "",
            "| Check | State |",
            "|---|---|",
            rows,
            "",
            "## Freeze until SOAK_PASS",
            "",
            *[f"- {x}" for x in payload["freeze_until_soak_pass"]],
            "",
            "## After SOAK_PASS (separate ballots only)",
            "",
            *[f"- {x}" for x in payload["after_soak_pass_ballots"]],
            "",
            "## Cadence",
            "",
            "```bash",
            "PYTHONPATH=scripts python3 scripts/tipsoft_ip3_trail42_l4_switch_dual_paper_ledgers.py",
            "PYTHONPATH=scripts python3 scripts/tipsoft_ip3_trail42_l4_switch_month_end_monitor.py",
            "PYTHONPATH=scripts python3 scripts/ops_alert_scan.py --report-only",
            "PYTHONPATH=scripts python3 scripts/tipsoft_dd_switch_soak_gate.py",
            "```",
            "",
            "Formal month-end: `python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers --fail-on-stale`",
            "",
            f"Label: `{payload['label']}`",
            "",
        ]
    )
    (OPS / f"{OUT_STEM}.md").write_text(md + "\n", encoding="utf-8")
    (OPS / f"{OUT_STEM}.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def patch_ops_status(payload: dict) -> None:
    path = OPS / "OPS_STATUS.md"
    text = path.read_text(encoding="utf-8")
    line = (
        f"**DD_SWITCH soak gate (2026-10-02):** register **{REGISTER}** · status **{payload['status']}** · "
        f"tip days since ACCEPT **{payload['nav_tip_days_since_accept']}** · "
        f"overlap_n **{payload['recon_overlap_n']}** · Soft FIN/TEL/Path4/broker **CLOSED until SOAK_PASS** · "
        f"`{OUT_STEM}.md`  \n"
    )
    if "DD_SWITCH soak gate" not in text:
        anchor = "**tip Soft LIVE STABILIZE (2026-10-02):**"
        if anchor in text:
            text = text.replace(anchor, line + anchor)
        else:
            text = line + text
    else:
        text = re.sub(
            r"\*\*DD_SWITCH soak gate \(2026-10-02\):\*\*[^\n]*\n",
            line,
            text,
            count=1,
        )
    path.write_text(text, encoding="utf-8")


def patch_register(payload: dict) -> None:
    path = OPS / "HUMAN_DECISION_REGISTER.md"
    text = path.read_text(encoding="utf-8")
    row = (
        f"| {REGISTER} | DD_SWITCH soak gate (post-stabilize cadence) | "
        f"**{payload['status']}** (2026-10-02) | Human `請按照順序修` · tip days "
        f"**{payload['nav_tip_days_since_accept']}** · cal **{payload['calendar_days_since_accept']}** · "
        f"overlap_n **{payload['recon_overlap_n']}** · Soft FIN/TEL/Path4/broker CLOSED until SOAK_PASS · "
        f"2020 residual KEEP · `{OUT_STEM}.md` |\n"
    )
    if f"| {REGISTER} |" not in text:
        text = text.replace(
            "| 0kbe | tip Soft LIVE STABILIZE / freeze stack |",
            row + "| 0kbe | tip Soft LIVE STABILIZE / freeze stack |",
        )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    payload = collect()
    write_artifacts(payload)
    patch_ops_status(payload)
    patch_register(payload)
    print(json.dumps({"ok": True, "status": payload["status"], "checks": payload["checks"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
