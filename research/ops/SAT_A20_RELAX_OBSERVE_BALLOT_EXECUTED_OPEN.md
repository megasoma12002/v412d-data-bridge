# SAT_A20_RELAX — Ballot EXECUTED (OPEN observe)

Date: 2026-09-28  
Status: **EXECUTED** · Soft-Frozen **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · live wire **false**  
Human (exact):

```
OPEN paper observe: SAT_A20_RELAX (Stage A SAT_RELAX_HIT · tip-first densify)
```

## Evidence

- Stage A **`SAT_RELAX_HIT`** · champion `SAT_A20_RELAX`
- tip CAGR↑ YTD +0.68 · 1y +0.74 · tip MDD↑ +0.02 · held CAGR↑ +0.33 · held MDD↑ −0.31
- Decision: `FIN_SAT_TIP_MECH_STAGEA_DECISION_PACK.md`
- Draft superseded: `FIN_SAT_TIP_MECH_SAT_RELAX_OBSERVE_BALLOT_DRAFT.md`

## Effect

- Dual-paper **OPERATING**: `CTRL_LIVE_A10` (α=0.10) ∥ `SAT_A20_RELAX` (α=0.20)
- Month-end + alert scan wired (alongside COMPOSITE)
- COMPOSITE `COMP_H150_x_A20` observe **KEEP OPEN** (held-first parallel)
- Cutover **BLOCKED** — do **not** flip live CONF α from this ballot

## Artifacts

- Operating: `SAT_A20_RELAX_DUAL_PAPER_OBSERVE_OPERATING.md`
- Ledgers: `scripts/sat_a20_relax_dual_paper_ledgers.py`
- Monitor: `scripts/sat_a20_relax_month_end_monitor.py`
- Repro: `repro/sat-a20-relax-dual-paper-observe/`
- Cutover: `CUTOVER_CHECKLIST_SAT_A20_RELAX.md` (**BLOCKED**)

Label: `SAT_A20_RELAX_OBSERVE_BALLOT_EXECUTED_2026-09-28__OPEN__NO_LIVE`
