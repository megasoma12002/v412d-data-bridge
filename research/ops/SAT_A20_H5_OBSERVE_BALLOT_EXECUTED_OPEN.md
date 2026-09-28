# SAT_A20_H5 — Ballot EXECUTED (OPEN observe)

Date: 2026-09-28  
Status: **EXECUTED** · Soft-Frozen **KEEP** · live wire **false**  
Parent batch: `OBSERVE_UP_DOWN_BATCH_2026-09-28.md`  
Human (batch): `請把可上 與可下進行上下`

Canonical OPEN line:

```
OPEN paper observe: SAT_A20_H5 (00631L CONF densify α=0.20 H=5 under COOL)
```

## Evidence

- Stage A `MECH_HIT` · Stage B `PARENT_KEEP`
- Decision: `SAT_A20_H5_DECISION_2026-09-27.md`
- Draft superseded: `SAT_A20_H5_OBSERVE_BALLOT_DRAFT.md`

## Effect

- Dual-paper **OPERATING**: `BASE_LIVE_CONF` (α=0.10) ∥ `SAT_A20_H5` (α=0.20)
- Month-end + alert scan wired
- Cutover **BLOCKED** — do **not** flip live CONF α from this ballot

## Artifacts

- Operating: `SAT_A20_H5_DUAL_PAPER_OBSERVE_OPERATING.md`
- Ledgers: `scripts/sat_a20_h5_dual_paper_ledgers.py`
- Monitor: `scripts/sat_a20_h5_month_end_monitor.py`
- Repro: `repro/sat-a20-h5-dual-paper-observe/`
- Cutover: `CUTOVER_CHECKLIST_SAT_A20_H5.md` (**BLOCKED**)

Label: `SAT_A20_H5_OBSERVE_BALLOT_EXECUTED_2026-09-28__OPEN__NO_LIVE`
