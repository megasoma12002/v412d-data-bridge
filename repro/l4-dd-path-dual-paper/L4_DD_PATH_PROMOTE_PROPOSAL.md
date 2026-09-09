# L4_DD_PATH_08_50 Promote Proposal — Dual Paper Ledgers

Generated: `2026-09-09T12:52:26.366426+00:00`
Status: **PROPOSAL ONLY** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`).

## Why this exists

Held-out research (`PASS_HELDOUT_L4`) unlocked an *optional* dual-paper observation path.
This PR materializes **dual Exact T+1 paper books** (BASE vs path-dependent L4)
without flipping live clips.

## Locked challenger

- **L4_DD_PATH_08_50**: apply FIN_CAP **[0.35, 0.50]** only while TAIEX active drawdown
  from 252d peak **≤ −8%**; else Soft-Frozen BASE
- Priors / regime router unchanged vs live E16

## Dual paper metrics

| Book | Window | CAGR | MDD | Fin mean | Fin max | DD-path on | Exact T+1 |
|---|---|---:|---:|---:|---:|---:|---|
| BASE_E16 | full | 13.97% | -22.39% | 79.8% | 89.4% | — | True |
| BASE_E16 | oof_2011_2018 | 8.98% | -17.57% | 80.3% | 88.8% | — | True |
| BASE_E16 | validation_2019_2022 | 12.25% | -22.39% | 79.7% | 89.4% | — | True |
| BASE_E16 | sealed_2023_plus | 25.54% | -13.95% | 79.1% | 87.9% | — | True |
| BASE_E16 | heldout_2019_plus | 18.47% | -22.39% | 79.4% | 89.4% | — | True |
| L4_DD_PATH_08_50 | full | 13.27% | -20.76% | 74.2% | 89.4% | 26.3% | True |
| L4_DD_PATH_08_50 | oof_2011_2018 | 9.63% | -15.12% | 74.6% | 88.8% | 25.0% | True |
| L4_DD_PATH_08_50 | validation_2019_2022 | 11.12% | -20.76% | 73.8% | 89.4% | 31.1% | True |
| L4_DD_PATH_08_50 | sealed_2023_plus | 22.86% | -12.85% | 73.8% | 87.9% | 23.6% | True |
| L4_DD_PATH_08_50 | heldout_2019_plus | 16.64% | -20.76% | 73.8% | 89.4% | 27.6% | True |

Validation vs BASE: MDD improve **1.63 pp**; CAGR giveback **1.14 pp**.
Sealed vs BASE: MDD improve **1.10 pp**; CAGR giveback **2.68 pp**.

## Cutover checklist (future human PR only)

1. Keep Soft-Frozen default = BASE_E16 until human-approved cutover PR
2. Run dual paper ledgers in parallel for ≥1 month-end review
3. Cutover would wire path-dependent DD-path logic (not a static clip swap)
4. Preserve BASE_E16 paper ledger indefinitely for regression
5. Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history
6. FIN_CAP_50 static promote remains separately NOT_READY_SEALED_CAGR — do not conflate

## Explicit non-goals

- Auto live-wire from this proposal
- Soft-Frozen flip
- L4 lock retune / reopen L1–L3 / FIN50 static promote
- Claim CAGR≥20% / MDD≤15% as live results

## Label

`L4_DD_PATH_DUAL_PAPER_PROMOTE_PROPOSAL`

Artifacts:
- `/workspace/repro/l4-dd-path-dual-paper/reports/l4_dd_path_dual_paper_proposal.json`
- `/workspace/repro/l4-dd-path-dual-paper/outputs/dual_paper_nav_compare.csv`
