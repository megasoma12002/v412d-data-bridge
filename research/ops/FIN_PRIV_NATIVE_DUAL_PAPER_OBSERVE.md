# 民營 native dual-paper (OPERATING OBSERVE)

Status: `OPERATING_OBSERVE` · paper only · Soft-Frozen KEEP · live wire false
Default status: **KEEP OBSERVE** · posture `FIN_PRIV_NATIVE_OBSERVE_POSTURE.md`

Books: `PRIV_EQUAL` ∥ `PRIV_KD_MAY_Klt25_T15`
Execution: capital **500,000,000** · lot **1000**

Held-out vs `PRIV_EQUAL`:
- MDD↑pp: **-2.6404292725197176**
- CAGR giveback pp: **-2.791025974576544**
- Score: **-4.03594225980799**

Sealed vs `PRIV_EQUAL` (report-only):
- MDD↑pp: **-1.5036759761275942**
- CAGR giveback pp: **-4.726225914551163**
- Score: **-3.8667889334031758**

## Reproduce

```bash
python3 scripts/e16_fin_priv_native_dual_paper_ledgers.py
python3 scripts/e16_fin_priv_native_month_end_monitor.py
```

Runbook: `FIN_PRIV_NATIVE_MONTH_END_RUNBOOK.md` · checklist: `FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_CHECKLIST.md`
Status ballot (DRAFT): `FIN_PRIV_NATIVE_OBSERVE_STATUS_BALLOT_DRAFT.md`
Repro: `repro/fin-priv-native-dual-paper-observe/`
