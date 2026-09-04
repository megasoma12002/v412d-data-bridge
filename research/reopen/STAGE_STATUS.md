# Research Stages — Status Through Stage 7

| Stage | Content | Outcome |
|---|---|---|
| Gap-fill P0–P2 | E45-C1, e50_stack, E22_v2, hedge/3B close | Done |
| Reopen R1–R2 | E22/E16/G4/E45 challengers | No upgrades |
| Stage 3 | 3A OI+Amihud adversarial | **STOP** |
| Stage 4 | 3A Rev YoY+CFO YoY adversarial | **STOP** |
| Stage 5 | Ops + payment-date fill + E22_v3 H1 | H1 interesting, **no promote** |
| Stage 5b | Paper `forward/e22_v3_challenger/` payment-date | **Seeded** (EXPERIMENTAL) |
| Stage 6 | 3A lend-fee stress (`-z(fee)`) | **STOP** |
| Stage 7 | Dual QC + TX front-month OI timing overlay | Dual QC **PASS**; TX OI **STOP** |

## Stage 5/5b/7 ops posture

1. Official: **E22_v2 ex-date** daily (`forward/e22_v2/`)
2. Paper parallel: **E22_v3 payment-date** (`forward/e22_v3_challenger/`) — no auto-cutover
3. E45=B; no G4 shorts; no E16 micro-grids
4. Dual QC script: `scripts/stage7_dual_qc.py`

## Stage 7 result

- Dual QC (v2 + v3): **PASS** — see `repro/stage7-tx-oi-timing-20260904/dual_qc.json`
- TX OI timing: **`STOP_STAGE7_TX_OI_TIMING_OVERLAY`** — neither UP nor DOWN delever clears util/MDD bar vs BASE
- Artifacts: `repro/stage7-tx-oi-timing-20260904/`, `research/reopen/STAGE7_DECISION.md`

## Recommended next (Stage 8+)

Ops monitoring only unless a **new** info source arrives (e.g. paid TWT58U industry PIT, equity tick, true board-proposal dates). Do **not** retune stopped TX-OI thresholds or reopen stopped 3A/Stage4/Stage6 feature sets.

Promotion bar unchanged: challenger + evidence + explicit approval.
