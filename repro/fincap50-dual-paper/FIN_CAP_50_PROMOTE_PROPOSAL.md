# FIN_CAP_50 Promote Proposal — Dual Paper Ledgers

Generated: `2026-09-05T01:33:13.170662+00:00`
Status: **PROPOSAL ONLY** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`).

> **CUTOVER BLOCKED — read this first**  
> Authoritative go-live decision: **`NOT_READY_SEALED_CAGR`**  
> (`research/gaps/FIN_CAP_50_GO_LIVE_VERIFY.md`).  
> Held-out PASS (`PASS_HELDOUT_FIN_CAP`) does **not** authorize cutover.  
> Sealed CAGR giveback failed (+4.33pp) and month-end Gate E is PAUSE (YTD/1y).  
> This document is a **paper dual-ledger proposal**, not a promote license.

## Why this exists

Prior research (`PASS_HELDOUT_FIN_CAP`) unlocked an *optional* dual-paper observation path.
This materializes **dual Exact T+1 paper books** so ops can review BASE vs FIN_CAP_50
without flipping live clips. Go-live verify later **blocked** sealed cutover.

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
Sealed (go-live): MDD +4.41 pp; CAGR giveback **+4.33 pp** → **FAIL** sealed gate.

## Status stack (do not collapse)

| Layer | Label |
|---|---|
| Held-out research | `PASS_HELDOUT_FIN_CAP` |
| Dual-paper books | `OPERATING (paper)` |
| Go-live verify | **`NOT_READY_SEALED_CAGR`** |
| Live Soft-Frozen clip | **[0.50, 0.95] KEEP** |
| Cutover | **FROZEN** |

## Cutover checklist (future human PR only — currently blocked)

1. Keep Soft-Frozen default = BASE_E16 until human-approved cutover PR
2. Re-clear go-live gates (sealed CAGR ≤3pp + no YTD/1y PAUSE)
3. Run dual paper ledgers in parallel for ≥1 clean month-end review
4. Cutover-only: change E16 Financial clip to [0.35,0.50] with named ledger FIN_CAP_50
5. Preserve BASE_E16 paper ledger indefinitely for regression
6. Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history
7. MDD target ≤15% still NOT claimed — FIN_CAP_50 held MDD ~-19.6%

## Explicit non-goals

- Auto live-wire from this proposal
- Treating held-out PASS as cutover-ready
- FIN_CAP cut retune
- L1 loss-engine reattach
- Claim CAGR≥20% / MDD≤15% as live results
- Conflating with L4_DD_PATH (path-dependent; separate promote path)

## Label

`FIN_CAP_50_DUAL_PAPER_PROMOTE_PROPOSAL__CUTOVER_BLOCKED`

Artifacts:
- `repro/fincap50-dual-paper/reports/fincap50_dual_paper_proposal.json`
- `repro/fincap50-dual-paper/outputs/dual_paper_nav_compare.csv`
