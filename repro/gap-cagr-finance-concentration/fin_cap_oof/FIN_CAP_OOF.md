# E16 FIN_CAP Weight-Budget OOF Challenger

Generated: `2026-09-05T00:54:11.288016+00:00`

**RESEARCH_ONLY.** No live-wire. Selection = 2011–2018 OOF only.

## Decision: `OOF_FIN_CAP_PASS_READY_FOR_HELDOUT`

### Predeclared pass rule

- Finance mean & max weight ≤ cap_hi
- OOF MDD improve ≥ **1 pp** vs BASE_E16
- OOF CAGR giveback ≤ **2 pp**

### Baseline (OOF)

- CAGR `0.08846959052336945` MDD `-0.1741290000386425` util `0.0014050905040481898`
- Mean Financial weight `0.802`

| name | fin_hi | fin_mean | OOF CAGR | OOF MDD | MDDΔ pp | CAGR giveback pp | pass |
|---|---:|---:|---:|---:|---:|---:|---|
| FIN_CAP_60 | 0.6 | 0.597 | 0.087488148875698 | -0.14537386469498248 | 2.88 | 0.10 | True |
| FIN_CAP_50 | 0.5 | 0.500 | 0.08498439286806181 | -0.12842313719649323 | 4.57 | 0.35 | True |

## Recommended (OOF only)

- `FIN_CAP_50` fin_hi=0.5
- MDD improve `4.57` pp; CAGR giveback `0.35` pp

Held-out numbers below are **informational only** (not used to pick).

- Held-out CAGR `0.16601509541261028` MDD `-0.19575705858876424`

Next: one held-out gate. Only `PASS_HELDOUT` may propose changing live E16 clips.

### Informational held-out (2019+)

| name | held CAGR | held MDD |
|---|---:|---:|
| BASE_E16 | 0.18235031521908462 | -0.22639131293777315 |
| FIN_CAP_60 | 0.1664249621074141 | -0.20729237733142059 |
| FIN_CAP_50 | 0.16601509541261028 | -0.19575705858876424 |

Artifacts:
- `repro/gap-cagr-finance-concentration/fin_cap_oof/reports/fin_cap_oof_summary.json`
- `repro/gap-cagr-finance-concentration/fin_cap_oof/outputs/fin_cap_oof_candidates.csv`

Label: `RESEARCH_FIN_CAP_OOF__NO_LIVE_WIRE`
