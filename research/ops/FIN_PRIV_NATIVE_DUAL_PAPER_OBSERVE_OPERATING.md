# 民營 native dual-paper (OPERATING OBSERVE)

Status: `OPERATING_OBSERVE` · paper only · Soft-Frozen KEEP · live wire false
Default status: **KEEP OBSERVE** · posture `FIN_PRIV_NATIVE_OBSERVE_POSTURE.md`

Books: `PRIV_EQUAL` ∥ `PRIV_KD_MAY_Klt25_T15`
Execution: capital **500,000,000** · lot **1000**

Held-out vs `PRIV_EQUAL`:
- MDD↑pp: **0.7314742099901905**
- CAGR giveback pp: **-0.2126480490775684**
- Score: **0.6251501854514063**

Sealed vs `PRIV_EQUAL` (report-only):
- MDD↑pp: **0.14075545096390307**
- CAGR giveback pp: **-0.13119453154086802**
- Score: **0.07515818519346906**

## Reproduce

```bash
python3 scripts/e16_fin_priv_native_dual_paper_ledgers.py
python3 scripts/e16_fin_priv_native_month_end_monitor.py
```

Runbook: `FIN_PRIV_NATIVE_MONTH_END_RUNBOOK.md` · checklist: `FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_CHECKLIST.md`
Status ballot (DRAFT): `FIN_PRIV_NATIVE_OBSERVE_STATUS_BALLOT_DRAFT.md`
Repro: `repro/fin-priv-native-dual-paper-observe/`
