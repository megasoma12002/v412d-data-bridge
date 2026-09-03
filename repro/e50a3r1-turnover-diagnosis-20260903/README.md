# E50-A3-R1 Turnover Diagnosis (2026-09-03)

Isolated EXPERIMENTAL challenger folder.

Constraints:
- Do not modify E16 / E18 / E22 / E44 / E45
- Keep pinned A0 / A1 / A2
- Keep Exact T+1 simulator unchanged
- Keep 2.5% OOF turnover and 0.70 bootstrap classified as EXPERIMENTAL
- Selection / diagnosis window: **2011-2018 OOF only**
- Do not open 2019-2022 or 2023-latest for parameter selection

## Commands

```bash
ROOT_IN=repro/e50a3r1-audit-20260903/inputs
ROOT_OUT=repro/e50a3r1-turnover-diagnosis-20260903
python3 scripts/e50a3r1_turnover_diagnosis.py \
  --panel $ROOT_IN/a2/causal_factor_panel.parquet \
  --prices $ROOT_IN/a0/point_in_time_universe.csv \
  --labels $ROOT_IN/a2/forward_labels_research_only.parquet \
  --actions $ROOT_IN/a1/corporate_action_ledger.csv.gz \
  --a2-qc $ROOT_IN/a2/qc_status.json \
  --baseline-grid $ROOT_OUT/baseline_train_repair_grid.csv \
  --out $ROOT_OUT
```

## Outputs

- `reports/root_cause_diagnostics.json`
- `outputs/oof_challenger_grid.csv`
- `reports/oof_challenger_summary.json`
- `E50-A3-R1_TURNOVER_DIAGNOSIS.md` (written after the run)
