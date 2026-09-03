# Isolated E50-A3-R1 reproduction (2026-09-03)

This folder is an audit sandbox. Frozen baselines were not modified.
Existing `forward/` and `research/` outputs were not overwritten.

## What was reproduced

1. **E50-A0 / A1 / A2**: downloaded pinned frozen GitHub Actions artifacts and hash-verified. Not rebuilt.
2. **E50-A3 / E50-A3-R1**: rerun locally from those frozen inputs into `outputs/`.

Pinned artifact sources:

| Stage | Run | Artifact |
|---|---|---|
| A0 | 33532322856 | `v412-e50a0-point-in-time` |
| A1 | 33637154310 | `v412-e50a1-full-causal-database` |
| A2 | 33645002188 | `v412-e50a2-causal-alpha-factors` |

## Commands (do not write into existing output dirs)

```bash
ROOT=repro/e50a3r1-audit-20260903
python3 scripts/e50a3_train_exact_open.py --self-test
python3 scripts/e50a3_train_exact_open.py \
  --panel $ROOT/inputs/a2/causal_factor_panel.parquet \
  --prices $ROOT/inputs/a0/point_in_time_universe.csv \
  --labels $ROOT/inputs/a2/forward_labels_research_only.parquet \
  --actions $ROOT/inputs/a1/corporate_action_ledger.csv.gz \
  --a2-qc $ROOT/inputs/a2/qc_status.json \
  --out $ROOT/outputs/a3
python3 scripts/e50a3r1_repair.py \
  --panel $ROOT/inputs/a2/causal_factor_panel.parquet \
  --prices $ROOT/inputs/a0/point_in_time_universe.csv \
  --labels $ROOT/inputs/a2/forward_labels_research_only.parquet \
  --actions $ROOT/inputs/a1/corporate_action_ledger.csv.gz \
  --a2-qc $ROOT/inputs/a2/qc_status.json \
  --out $ROOT/outputs/a3r1
```

Large input datasets are gitignored. Re-download with `gh run download` using the run IDs above.
