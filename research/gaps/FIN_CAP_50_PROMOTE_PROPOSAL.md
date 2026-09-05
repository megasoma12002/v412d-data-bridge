# FIN_CAP_50 Promote Proposal — Dual Paper Ledgers

Generated: `2026-09-05T01:33:13.170662+00:00`
Status: **PROPOSAL ONLY** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`).

## Why this exists

Prior research (`PASS_HELDOUT_FIN_CAP`) unlocked an *optional* promote path.
This PR materializes **dual Exact T+1 paper books** so ops can review BASE vs FIN_CAP_50
without flipping live clips.

## Locked challenger

- **FIN_CAP_50**: Financial clip **[0.35, 0.50]**; residual → Telecom/0050
- Priors / regime router unchanged vs live E16

## Dual paper metrics

| Book | Window | CAGR | MDD | Fin mean | Fin max | Exact T+1 |
|---|---|---:|---:|---:|---:|---|
| BASE_E16 | full | 13.78% | -22.64% | 79.8% | 91.9% | True |
| BASE_E16 | oof_2011_2018 | 8.85% | -17.41% | 80.2% | 91.1% | True |
| BASE_E16 | heldout_2019_plus | 18.24% | -22.64% | 79.4% | 91.9% | True |
| FIN_CAP_50 | full | 12.70% | -19.58% | 50.0% | 50.0% | True |
| FIN_CAP_50 | oof_2011_2018 | 8.50% | -12.84% | 50.0% | 50.0% | True |
| FIN_CAP_50 | heldout_2019_plus | 16.60% | -19.58% | 50.0% | 50.0% | True |

Held-out vs BASE: MDD improve **3.06 pp**; CAGR giveback **1.63 pp**.

## Cutover checklist (future human PR only)

1. Keep Soft-Frozen default = BASE_E16 until human-approved cutover PR
2. Run dual paper ledgers in parallel for ≥1 month-end review
3. Cutover-only: change E16 Financial clip to [0.35,0.50] with named ledger FIN_CAP_50
4. Preserve BASE_E16 paper ledger indefinitely for regression
5. Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history
6. MDD target ≤15% still NOT claimed — FIN_CAP_50 held MDD ~-19.6%

## Explicit non-goals

- Auto live-wire from this proposal
- FIN_CAP cut retune
- L1 loss-engine reattach
- Claim CAGR≥20% / MDD≤15% as live results

## Label

`FIN_CAP_50_DUAL_PAPER_PROMOTE_PROPOSAL`

Artifacts:
- `/workspace/repro/fincap50-dual-paper/reports/fincap50_dual_paper_proposal.json`
- `/workspace/repro/fincap50-dual-paper/outputs/dual_paper_nav_compare.csv`
