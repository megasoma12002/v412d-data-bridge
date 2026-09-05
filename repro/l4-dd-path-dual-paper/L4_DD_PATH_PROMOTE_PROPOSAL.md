# L4_DD_PATH_08_50 Promote Proposal — Dual Paper Ledgers

Generated: `2026-09-05T04:47:21.524806+00:00`
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
| BASE_E16 | full | 13.78% | -22.64% | 79.8% | 91.9% | — | True |
| BASE_E16 | oof_2011_2018 | 8.85% | -17.41% | 80.2% | 91.1% | — | True |
| BASE_E16 | validation_2019_2022 | 12.33% | -22.64% | 79.9% | 91.9% | — | True |
| BASE_E16 | sealed_2023_plus | 24.93% | -14.46% | 78.9% | 88.5% | — | True |
| BASE_E16 | heldout_2019_plus | 18.24% | -22.64% | 79.4% | 91.9% | — | True |
| L4_DD_PATH_08_50 | full | 13.12% | -21.01% | 74.4% | 91.9% | 26.3% | True |
| L4_DD_PATH_08_50 | oof_2011_2018 | 9.62% | -15.17% | 74.9% | 91.1% | 25.0% | True |
| L4_DD_PATH_08_50 | validation_2019_2022 | 11.13% | -21.01% | 74.2% | 91.9% | 31.1% | True |
| L4_DD_PATH_08_50 | sealed_2023_plus | 22.27% | -12.99% | 73.7% | 88.5% | 23.7% | True |
| L4_DD_PATH_08_50 | heldout_2019_plus | 16.37% | -21.01% | 74.0% | 91.9% | 27.6% | True |

Validation vs BASE: MDD improve **1.63 pp**; CAGR giveback **1.20 pp**.
Sealed vs BASE: MDD improve **1.47 pp**; CAGR giveback **2.66 pp**.

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
