# Research Stages — Status Through Stage 8

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
| Stage 8 | Defensive ETF sleeve (0056) | **STOP** |

## Official posture

1. Official: **E22_v2 ex-date** (`forward/e22_v2/`) — 8 names, 3 sleeves
2. Paper: **E22_v3 payment-date** — no auto-cutover
3. E45=B; no G4 shorts; no extra ETF sleeves

## Stage 8 result

- Probe: `SLEEVE4_0056` / `RISKOFF_0056` vs BASE
- Decision: **`STOP_STAGE8_DEFENSIVE_ETF_SLEEVE`**
- Docs: `research/reopen/STAGE8_DECISION.md`, `repro/stage8-defensive-etf-20260904/`

## Recommended next

Ops monitoring only unless a **new** info source arrives (TWT58U industry PIT, equity tick, true board-proposal dates). Do not retune stopped Stage 7/8 thresholds or reopen stopped 3A feature sets.

Promotion bar unchanged: challenger + evidence + explicit approval.
