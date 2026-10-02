# TIPSOFT_DD_SWITCH_SOAK_GATE

Date: 2026-10-02 · Status: **SOAK_OPEN** · register **0kbf**
Parents: stabilize `TIPSOFT_LIVE_STABILIZE_2026-10-02` · DD_SWITCH tip apply 0kbd

## Human order

1 Merge stabilize (0kbe) — DONE on main
2 Soak daily tip + DD_SWITCH month-end
3 Soft FIN/TEL · Path4 · broker CLOSED until SOAK_PASS
4 Separate ballots only after SOAK_PASS

## Snapshot

- Live tip: **2026-10-02** · QC **PASS**
- Days since ACCEPT tip apply (2026-10-01): cal **1** · nav tip days **2**
- Live↔paper overlap_n: **18** (floor 60)
- DD_SWITCH month-end asof: **2026-09-29** · alerts `[]`

## Floors

- tip days ≥ **20**
- calendar days ≥ **28** (~1 month-end)
- live↔paper overlap ≥ **60**
- DD_SWITCH monitor: no PAUSE_REVIEW

## Checks

| Check | State |
|---|---|
| `stabilize_ballot_present` | PASS |
| `dd_switch_live` | PASS |
| `path3_within_live` | PASS |
| `soft_fin_tel_stay_off` | PASS |
| `path4_live_off` | PASS |
| `broker_false` | PASS |
| `fill_port_paper` | PASS |
| `qc_pass` | PASS |
| `tip_days_since_accept_ge` | OPEN |
| `cal_days_since_accept_ge` | OPEN |
| `live_paper_overlap_ge` | OPEN |
| `dd_switch_monitor_no_pause` | PASS |
| `dd_switch_monitor_present` | PASS |

## Freeze until SOAK_PASS

- No Soft FIN/TEL Exact T+1 refill ACCEPT
- No Path4 live
- No broker EXECUTE / live-write
- No new tip Soft mechanism Stage A / tip apply
- No year-switch / year-oracle

## After SOAK_PASS (separate ballots only)

- Optional: Soft FIN/TEL Exact T+1 carve on Path3 OFF days (separate ACCEPT)
- Optional: broker EXECUTE (separate ACCEPT; PREP already filed)
- Optional: 2020 MDD research only if held+ ∧ y2020 improve (else KEEP residual)

## Cadence

```bash
PYTHONPATH=scripts python3 scripts/tipsoft_ip3_trail42_l4_switch_dual_paper_ledgers.py
PYTHONPATH=scripts python3 scripts/tipsoft_ip3_trail42_l4_switch_month_end_monitor.py
PYTHONPATH=scripts python3 scripts/ops_alert_scan.py --report-only
PYTHONPATH=scripts python3 scripts/tipsoft_dd_switch_soak_gate.py
```

Formal month-end: `python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers --fail-on-stale`

Label: `TIPSOFT_DD_SWITCH_SOAK_GATE_2026-10-02__SOAK_OPEN`

