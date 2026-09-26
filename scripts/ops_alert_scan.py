#!/usr/bin/env python3
"""Ops alert scan — RESEARCH / OPS only.

Reads live QC + latest month-end monitor JSONs and emits:
  research/ops/OPS_ALERTS.json
  research/ops/OPS_ALERTS.md

Severity:
  CRITICAL — live QC FAIL / Exact T+1 fail
  HIGH     — month-end PAUSE_REVIEW / R4 estimate missing (cutover talk blocked; Soft-Frozen unchanged)
  INFO     — ALERT lines without PAUSE / thin recon / tip lag / R4 present (liquidity ≠ NAV)

Exit codes (when not ``--report-only``):
  default ``--fail-on critical`` → exit 2 on CRITICAL; exit 0 when only HIGH
  ``--fail-on high`` → exit 1 on HIGH (and exit 2 still on CRITICAL)
  ``--fail-on never`` / ``--report-only`` → always exit 0 after writing

Never flips Soft-Frozen. Never cutover.
Phase 3: R4 continuous observe + TIP_LAG_BOOKS INFO.
Phase 5: optional DIV_APPLIED_MISSING_IN_RECV_WINDOW /
DIV_APPLIED_EMPTY_IN_RECV_WINDOW (Stage-E tip only).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research/ops"
QC_PATH = ROOT / "forward/e21/qc_status.json"
L4_JSON = ROOT / "research/gaps/L4_DD_PATH_MONTH_END_MONITOR.json"
FIN_JSON = ROOT / "research/gaps/FIN_CAP_50_MONTH_END_MONITOR.json"
BLEND_JSON = ROOT / "research/gaps/BLEND_025_MONTH_END_MONITOR.json"
E45_JSON = ROOT / "research/gaps/E45_MONTH_END_MONITOR.json"
# E45_BLEND025 observe ARCHIVED 2026-09-13 — retained path for evidence only (not scanned).
E45_BLEND025_JSON = ROOT / "research/gaps/E45_BLEND025_MONTH_END_MONITOR.json"
E45_BLEND025_ALERT_SCAN = False
SOFT_ASSIST_JSON = ROOT / "research/ops/SOFT_ASSIST_MONTH_END_MONITOR.json"
SLEEVE_TILT_JSON = ROOT / "research/ops/SLEEVE_LAYER_TILT_MONTH_END_MONITOR.json"
FUSE_ADDITIVE_JSON = ROOT / "research/ops/FUSE_ADDITIVE_MONTH_END_MONITOR.json"
E45_DEFEND_HANDOFF_JSON = ROOT / "research/ops/E45_DEFEND_HANDOFF_MONTH_END_MONITOR.json"
COOL_C8_PROXY_JSON = ROOT / "research/ops/COOL_C8_PROXY_MONTH_END_MONITOR.json"
BETA_0050_DENSIFY_JSON = ROOT / "research/ops/BETA_0050_DENSIFY_MONTH_END_MONITOR.json"
PRIV_FINHC_V7_F05_JSON = ROOT / "research/ops/PRIV_FINHC_V7_BULL_SIDE_F05_MONTH_END_MONITOR.json"
RECON_JSON = ROOT / "research/ops/LIVE_PAPER_RECON.json"
GAP6_JSON = ROOT / "research/ops/E22_GAP6_FIDELITY_KPI.json"
E22_KPI_JSON = ROOT / "research/ops/E22_DATA_QUALITY_KPI.json"
RESILIENCE_JSON = ROOT / "research/ops/DATA_SOURCE_RESILIENCE_KPI.json"
SHADOW_JSON = ROOT / "research/ops/DATA_SOURCE_SHADOW_RECONCILE.json"
PHASE_C_JSON = ROOT / "research/ops/DATA_SOURCE_PHASE_C_PROBES.json"
R4_CSV = ROOT / "forward/e21/settlement_cash_estimate.csv"
R4_JSON = ROOT / "forward/e21/settlement_cash_estimate.json"
SESSION_SKIP = ROOT / "forward/session_skip.json"
TIP_STATE = ROOT / "forward/e21/portfolio_state.json"
SIGNALS_CSV = ROOT / "forward/e21/signals.csv"
PRIVATE_FIN_ADJ = ROOT / "data/market/private_fin_adjusted.csv"

# Soft-Frozen clip — single source (never hardcode drift).
from e16_soft_frozen_base import SOFT_FROZEN_FIN_CLIP
from ops_observe_helpers import (
    R4_SUMMARY_KEYS,
    STAGE_E_DEFAULT,
    r4_artifacts_present,
    r4_summary as observe_r4_summary,
)


def _class_d_finpriv_alerts() -> list[dict]:
    """Surface Class D FinPriv stale/missing priv px (fail-closed gate off).

    HIGH when live Class D is on and private_fin_adjusted lags tip asof > 5d,
    or tip signal stamped fin_priv_skipped_missing_px. Soft-Frozen unchanged.
    """
    out: list[dict] = []
    try:
        from live_config import LIVE_FIN_PRIV_V7_F05
    except Exception:
        return out
    if not LIVE_FIN_PRIV_V7_F05:
        return out
    try:
        import live_finhc_v7_f05_cutover as finpriv
        import pandas as pd
    except Exception as exc:  # noqa: BLE001
        out.append(
            {
                "severity": "HIGH",
                "source": "fin_priv_v7_f05",
                "code": "FINPRIV_IMPORT_FAIL",
                "message": f"Class D live but cutover import failed: {exc}",
            }
        )
        return out

    asof = None
    tip = _load(TIP_STATE)
    if tip and tip.get("last_date"):
        asof = pd.Timestamp(str(tip["last_date"])[:10]).normalize()
    if asof is None and SIGNALS_CSV.exists():
        try:
            sig = pd.read_csv(SIGNALS_CSV, usecols=["date"])
            if not sig.empty:
                asof = pd.to_datetime(sig["date"]).max().normalize()
        except Exception:
            asof = None
    if asof is None:
        out.append(
            {
                "severity": "INFO",
                "source": "fin_priv_v7_f05",
                "code": "FINPRIV_ASOF_UNKNOWN",
                "message": "Class D live but tip asof unknown — skip freshness check",
            }
        )
        return out

    fresh, meta = finpriv.priv_prices_fresh_enough(asof)
    if not fresh:
        out.append(
            {
                "severity": "HIGH",
                "source": "fin_priv_v7_f05",
                "code": "FINPRIV_PX_STALE_OR_MISSING",
                "message": (
                    f"Class D live · priv panel stale/missing vs tip asof {asof.date()} "
                    f"reason={meta.get('reason')!r} stale={meta.get('stale_or_missing')!r} "
                    f"lags={meta.get('lags')!r} — gate fail-closed OFF (Soft-Frozen KEEP)"
                ),
            }
        )
    else:
        out.append(
            {
                "severity": "INFO",
                "source": "fin_priv_v7_f05",
                "code": "FINPRIV_PX_FRESH",
                "message": f"Class D priv panel fresh vs tip asof {asof.date()} (lag≤5d)",
            }
        )

    if SIGNALS_CSV.exists():
        try:
            sig = pd.read_csv(SIGNALS_CSV)
            if "fin_priv_skipped_missing_px" in sig.columns and not sig.empty:
                tip_row = sig.iloc[-1]
                skipped = tip_row.get("fin_priv_skipped_missing_px")
                if skipped is True or str(skipped).lower() in ("true", "1"):
                    out.append(
                        {
                            "severity": "HIGH",
                            "source": "fin_priv_v7_f05",
                            "code": "FINPRIV_SKIPPED_MISSING_PX_TIP",
                            "message": (
                                f"tip signal {tip_row.get('date')} fin_priv_skipped_missing_px=true "
                                f"regime={tip_row.get('regime')!r} gate_on={tip_row.get('fin_priv_gate_on')!r}"
                            ),
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            out.append(
                {
                    "severity": "INFO",
                    "source": "fin_priv_v7_f05",
                    "code": "FINPRIV_SIGNAL_SCAN_FAIL",
                    "message": f"could not scan signals for Class D skip flag: {exc}",
                }
            )
    if not PRIVATE_FIN_ADJ.exists():
        out.append(
            {
                "severity": "HIGH",
                "source": "fin_priv_v7_f05",
                "code": "FINPRIV_ADJ_FILE_MISSING",
                "message": f"missing {PRIVATE_FIN_ADJ} — Class D gate cannot turn on",
            }
        )
    return out


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument(
        "--report-only",
        action="store_true",
        help="Always exit 0 after writing OPS_ALERTS.* (month-end pack mode).",
    )
    ap.add_argument(
        "--fail-on",
        choices=("never", "critical", "high"),
        default="critical",
        help="Exit non-zero threshold when not --report-only (default: critical).",
    )
    args = ap.parse_args()

    alerts: list[dict] = []

    qc = _load(QC_PATH)
    if qc is None:
        alerts.append(
            {
                "severity": "CRITICAL",
                "source": "live_qc",
                "code": "QC_MISSING",
                "message": f"missing {QC_PATH}",
            }
        )
    else:
        status = str(qc.get("status", "")).upper()
        exact = qc.get("exact_t1_ok")
        if status != "PASS":
            alerts.append(
                {
                    "severity": "CRITICAL",
                    "source": "live_qc",
                    "code": "QC_FAIL",
                    "message": f"forward/e21 qc_status status={status!r}",
                }
            )
        if exact is False:
            alerts.append(
                {
                    "severity": "CRITICAL",
                    "source": "live_qc",
                    "code": "EXACT_T1_FAIL",
                    "message": "exact_t1_ok is false",
                }
            )
        elif exact is None:
            alerts.append(
                {
                    "severity": "CRITICAL",
                    "source": "live_qc",
                    "code": "EXACT_T1_MISSING",
                    "message": "exact_t1_ok missing from qc_status (fail closed)",
                }
            )
        if status == "PASS" and exact is True:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "live_qc",
                    "code": "QC_PASS",
                    "message": "live QC PASS; Exact T+1 ok",
                }
            )

    alerts.extend(_class_d_finpriv_alerts())

    monitor_sources = [
        ("l4_month_end", L4_JSON),
        ("fincap50_month_end", FIN_JSON),
        ("blend025_month_end", BLEND_JSON),  # FINCAP BLEND_025 KEEP
        ("e45_month_end", E45_JSON),
        # Operating paper observes — PAUSE_REVIEW must surface in OPS_ALERTS.
        ("soft_assist_month_end", SOFT_ASSIST_JSON),
        ("sleeve_tilt_month_end", SLEEVE_TILT_JSON),
        ("fuse_additive_month_end", FUSE_ADDITIVE_JSON),
        ("e45_defend_handoff_month_end", E45_DEFEND_HANDOFF_JSON),
        ("cool_c8_proxy_month_end", COOL_C8_PROXY_JSON),
        ("beta_0050_densify_month_end", BETA_0050_DENSIFY_JSON),
        ("priv_finhc_v7_bull_side_f05_month_end", PRIV_FINHC_V7_F05_JSON),
    ]
    if E45_BLEND025_ALERT_SCAN:
        monitor_sources.insert(4, ("e45_blend025_month_end", E45_BLEND025_JSON))
    for label, path in monitor_sources:
        doc = _load(path)
        if doc is None:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": label,
                    "code": "MONITOR_MISSING",
                    "message": f"missing {path} (run month-end pack)",
                }
            )
            continue
        for line in doc.get("alerts") or []:
            sev = "HIGH" if "PAUSE_REVIEW" in str(line) else "INFO"
            if str(line).startswith("ALERT"):
                sev = "HIGH" if "PAUSE_REVIEW" in str(line) else "INFO"
            if "PAUSE_REVIEW" in str(line):
                sev = "HIGH"
            alerts.append(
                {
                    "severity": sev,
                    "source": label,
                    "code": "PAUSE_REVIEW" if "PAUSE_REVIEW" in str(line) else "MONITOR_ALERT",
                    "message": str(line),
                }
            )
        if doc.get("cutover_blocked"):
            alerts.append(
                {
                    "severity": "INFO",
                    "source": label,
                    "code": "CUTOVER_BLOCKED_FLAG",
                    "message": "cutover_blocked=true (expected while Soft-Frozen KEEP)",
                }
            )

    recon = _load(RECON_JSON)
    if recon:
        for a in recon.get("alerts") or []:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "live_paper_recon",
                    "code": "RECON_NOTE",
                    "message": str(a),
                }
            )
        n = recon.get("overlap_n") or recon.get("overlap_sessions")
        if n is not None and int(n) < 60:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "live_paper_recon",
                    "code": "THIN_LIVE_HISTORY",
                    "message": f"overlap_n={n} (<60) — not decision-grade for cutover",
                }
            )

    e22_kpi = _load(E22_KPI_JSON)
    if e22_kpi is not None and e22_kpi.get("kpi_ok") is False:
        alerts.append(
            {
                "severity": "INFO",
                "source": "e22_data_quality_kpi",
                "code": "E22_DQ_FLAGS",
                "message": f"flags={e22_kpi.get('flags')}",
            }
        )

    gap6 = _load(GAP6_JSON)
    if gap6 is None:
        alerts.append(
            {
                "severity": "INFO",
                "source": "e22_gap6_fidelity_kpi",
                "code": "GAP6_KPI_MISSING",
                "message": f"missing {GAP6_JSON} (run month-end pack / e22_gap6_fidelity_kpi)",
            }
        )
    else:
        if gap6.get("code_ok") is False:
            alerts.append(
                {
                    "severity": "HIGH",
                    "source": "e22_gap6_fidelity_kpi",
                    "code": "E22_CODE_WIRE_FAIL",
                    "message": f"E22 code wire not OK; flags={gap6.get('flags')}",
                }
            )
        if gap6.get("kpi_ok") is False and gap6.get("code_ok") is True:
            alerts.append(
                {
                    "severity": "HIGH",
                    "source": "e22_gap6_fidelity_kpi",
                    "code": "GAP6_KPI_BLOCKED_LIVE_EVIDENCE",
                    "message": (
                        "kpi_ok=false with code_ok=true — live e22_* fields missing; "
                        "next forward run must persist fields (no history rewrite)"
                    ),
                }
            )
        for flag in gap6.get("flags") or []:
            sev = "HIGH" if str(flag).startswith("DEFAULT_BOOKS") or "unexpectedly" in str(flag) else "INFO"
            if flag in (
                "LIVE_LEDGER_E22_FIELDS_MISSING",
                "KPI_BLOCKED_LIVE_EVIDENCE_MISSING",
            ):
                sev = "HIGH"
            alerts.append(
                {
                    "severity": sev,
                    "source": "e22_gap6_fidelity_kpi",
                    "code": str(flag),
                    "message": str(flag),
                }
            )
        # Phase 3 — tip lag (INFO; never CRITICAL; not a second DEFAULT).
        live = gap6.get("live_ledger") or {}
        code = gap6.get("code_wire") or {}
        observed = live.get("observed_books_version")
        default = code.get("default_books_version") or STAGE_E_DEFAULT
        if observed and default and observed != default:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "e22_gap6_fidelity_kpi",
                    "code": "TIP_LAG_BOOKS",
                    "message": (
                        f"tip books {observed!r} lag Stage-E DEFAULT {default!r} — "
                        "authorized until next weekday forward (ACCEPT_TIP_BOOKS_ALIGN_V3); "
                        "tip lag ≠ second DEFAULT; Soft-Frozen KEEP"
                    ),
                }
            )
        # Phase 5 optional — apply rows missing / empty while receivable window open (Stage-E tip only).
        if observed == STAGE_E_DEFAULT:
            recv = gap6.get("receivable_stub") or {}
            n_recv = int(recv.get("n_cash_events_in_receivable_window") or 0)
            if n_recv > 0 and not live.get("dividends_applied_exists"):
                alerts.append(
                    {
                        "severity": "INFO",
                        "source": "e22_gap6_fidelity_kpi",
                        "code": "DIV_APPLIED_MISSING_IN_RECV_WINDOW",
                        "message": (
                            f"Stage-E tip with {n_recv} cash events in receivable window but "
                            "dividends_applied.csv absent — report-only; no history backfill"
                        ),
                    }
                )
            elif (
                n_recv > 0
                and live.get("dividends_applied_exists")
                and int(live.get("dividends_applied_n") or 0) == 0
            ):
                alerts.append(
                    {
                        "severity": "INFO",
                        "source": "e22_gap6_fidelity_kpi",
                        "code": "DIV_APPLIED_EMPTY_IN_RECV_WINDOW",
                        "message": (
                            f"Stage-E tip with {n_recv} cash events in receivable window but "
                            "dividends_applied.csv exists with n=0 (empty) — report-only; "
                            "no history backfill"
                        ),
                    }
                )

    # Phase 3 — R4 T+2 settlement estimate continuous observe (liquidity ≠ NAV).
    session = _load(SESSION_SKIP) or {}
    is_session = bool(session.get("is_session")) if session else None
    state_dir = ROOT / "forward/e21"
    if not r4_artifacts_present(state_dir):
        # On closed board, prior R4 should still exist; missing is HIGH either way.
        alerts.append(
            {
                "severity": "HIGH",
                "source": "r4_settlement_estimate",
                "code": "R4_ESTIMATE_MISSING",
                "message": (
                    "settlement_cash_estimate.csv/json missing or empty under forward/e21 — "
                    "liquidity observe only (NOT NAV); Soft-Frozen KEEP"
                ),
            }
        )
    else:
        r4_obs = observe_r4_summary(state_dir)
        missing = list(r4_obs.get("missing_summary_keys") or [])
        if missing:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "r4_settlement_estimate",
                    "code": "R4_SUMMARY_SCHEMA",
                    "message": (
                        f"R4 summary missing keys {missing} — liquidity view not NAV "
                        f"(session_is_session={is_session})"
                    ),
                }
            )
        else:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "r4_settlement_estimate",
                    "code": "R4_ESTIMATE_PRESENT",
                    "message": (
                        "R4 settlement_cash_estimate present — "
                        f"settled_cash_estimate={r4_obs.get('settled_cash_estimate')} "
                        "is liquidity view NOT portfolio NAV / Soft-Frozen cash"
                    ),
                }
            )

    resilience = _load(RESILIENCE_JSON)
    if resilience is None:
        alerts.append(
            {
                "severity": "INFO",
                "source": "data_source_resilience_kpi",
                "code": "RESILIENCE_KPI_MISSING",
                "message": f"missing {RESILIENCE_JSON} (run data_source_resilience_kpi)",
            }
        )
    else:
        n_sp = int(resilience.get("n_critical_without_backup") or 0)
        if n_sp > 0:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "data_source_resilience_kpi",
                    "code": "SINGLE_POINT_STREAMS",
                    "message": (
                        f"n_critical_without_backup={n_sp}; "
                        f"flags={resilience.get('flags')}"
                    ),
                }
            )
        if resilience.get("kpi_ok") is False:
            alerts.append(
                {
                    "severity": "HIGH",
                    "source": "data_source_resilience_kpi",
                    "code": "PAYMENT_DATE_BACKUP_REGRESSION",
                    "message": "dividend payment-date backup path regressed",
                }
            )

    shadow = _load(SHADOW_JSON)
    if shadow is None:
        alerts.append(
            {
                "severity": "INFO",
                "source": "data_source_shadow_reconcile",
                "code": "SHADOW_RECONCILE_MISSING",
                "message": f"missing {SHADOW_JSON} (run data_source_shadow_reconcile)",
            }
        )
    else:
        for c in shadow.get("checks") or []:
            st = str(c.get("status") or "")
            if st == "DRIFT":
                alerts.append(
                    {
                        "severity": "INFO",
                        "source": "data_source_shadow_reconcile",
                        "code": f"SHADOW_DRIFT_{c.get('id')}".upper(),
                        "message": f"{c.get('id')}: {st} detail={c.get('detail_csv') or c.get('note')}",
                    }
                )
            elif st in {"NO_OVERLAP", "YAHOO_EMPTY", "MISSING_LEDGER"}:
                alerts.append(
                    {
                        "severity": "INFO",
                        "source": "data_source_shadow_reconcile",
                        "code": f"SHADOW_FAIL_{c.get('id')}".upper(),
                        "message": f"{c.get('id')}: {st}",
                    }
                )

    phase_c = _load(PHASE_C_JSON)
    if phase_c is None:
        alerts.append(
            {
                "severity": "INFO",
                "source": "data_source_phase_c_probes",
                "code": "PHASE_C_PROBES_MISSING",
                "message": f"missing {PHASE_C_JSON} (run data_source_phase_c_probes)",
            }
        )
    else:
        overall_pc = str(phase_c.get("overall_status") or "")
        if overall_pc != "PASS":
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "data_source_phase_c_probes",
                    "code": "PHASE_C_PROBES_FAIL",
                    "message": f"overall={overall_pc}",
                }
            )
        for key, block in (phase_c.get("probes") or {}).items():
            g = (block or {}).get("gate") or {}
            if g.get("status") != "PASS":
                alerts.append(
                    {
                        "severity": "INFO",
                        "source": "data_source_phase_c_probes",
                        "code": f"PHASE_C_{key}_FAIL".upper(),
                        "message": g.get("reason") or (block or {}).get("note") or key,
                    }
                )
            elif (block or {}).get("note"):
                alerts.append(
                    {
                        "severity": "INFO",
                        "source": "data_source_phase_c_probes",
                        "code": f"PHASE_C_{key}_NOTE".upper(),
                        "message": str(block.get("note")),
                    }
                )

    # Rank
    rank = {"CRITICAL": 0, "HIGH": 1, "INFO": 2}
    alerts.sort(key=lambda x: rank.get(x["severity"], 9))

    has_crit = any(a["severity"] == "CRITICAL" for a in alerts)
    has_high = any(a["severity"] == "HIGH" for a in alerts)
    overall = "CRITICAL" if has_crit else ("HIGH" if has_high else "CLEAR")

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "OPS_ALERT_SCAN",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "soft_frozen_clip": list(SOFT_FROZEN_FIN_CLIP),
        "overall": overall,
        "n_critical": sum(1 for a in alerts if a["severity"] == "CRITICAL"),
        "n_high": sum(1 for a in alerts if a["severity"] == "HIGH"),
        "n_info": sum(1 for a in alerts if a["severity"] == "INFO"),
        "alerts": alerts,
        "routing_note": (
            "Annotate CI job summary / upload OPS_ALERTS.* as artifact. "
            "HIGH=PAUSE_REVIEW / R4 missing blocks cutover talk only (not Soft-Frozen flip). "
            "CRITICAL fails live QC smoke. "
            "R4 settled_cash_estimate is liquidity view NOT NAV. "
            "TIP_LAG_BOOKS is INFO only while tip ≠ Stage-E DEFAULT (cleared after Phase 2 catch-up)."
        ),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "OPS_ALERTS.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Ops Alerts",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Overall: **{overall}**",
        f"Soft-Frozen **[{SOFT_FROZEN_FIN_CLIP[0]:.2f}, {SOFT_FROZEN_FIN_CLIP[1]:.2f}] unchanged**. No auto cutover.",
        "",
        f"- CRITICAL: {payload['n_critical']}",
        f"- HIGH (PAUSE_REVIEW etc.): {payload['n_high']}",
        f"- INFO: {payload['n_info']}",
        "",
        "| Severity | Source | Code | Message |",
        "|---|---|---|---|",
    ]
    for a in alerts:
        msg = a["message"].replace("|", "\\|")
        lines.append(f"| {a['severity']} | `{a['source']}` | `{a['code']}` | {msg} |")
    lines += [
        "",
        "## Routing",
        "",
        "- CRITICAL → fail `e21-live-qc-smoke` / block live confidence",
        "- HIGH → month-end pack annotates PAUSE; R4 missing; cutover checklists stay blocked",
        "- INFO → tip lag / R4 present (liquidity ≠ NAV) / recorded only",
        "",
        "Re-run: `python3 scripts/ops_alert_scan.py`",
        "",
    ]
    (args.out_dir / "OPS_ALERTS.md").write_text("\n".join(lines))
    print(json.dumps(payload, indent=2))

    if args.report_only:
        return 0
    if args.fail_on == "never":
        return 0
    if has_crit:
        return 2
    if args.fail_on == "high" and has_high:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
