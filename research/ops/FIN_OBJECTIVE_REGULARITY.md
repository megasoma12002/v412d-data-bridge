# FIN objective regularity discovery

Generated: `2026-09-09T00:36:53.571598+00:00`
Status: **DISCOVERY_SCREEN** · Soft-Frozen **KEEP** · live wire **false**
Split: train ≤2019 · test ≥2020 · Yahoo K9/D9 · FIN `2880, 2886, 2892, 5880`

## What this is

Data-driven scan **without** presupposing May–Jun. Your observation is checked against survivors.

## A) Ex-div local high (most robust)

| bin | share | expected |
|---|---:|---:|
| `[-40,-21]` | 5.0% | 43.5% |
| `[-20,-11]` | 15.0% | 21.7% |
| `[-10,-1]` | 80.0% | 21.7% |
| `[0,0]` | 0.0% | 2.2% |
| `[1,5]` | 0.0% | 10.9% |

## B) Calendar half-months (40d, train&test >0)

| bucket | train med | test med |
|---|---:|---:|
| `04-H2` | 2.76% | 5.13% |
| `05-H1` | 2.69% | 5.05% |
| `05-H2` | 4.80% | 4.42% |
| `01-H2` | 3.84% | 4.11% |
| `06-H1` | 3.32% | 3.38% |
| `11-H1` | 1.46% | 3.07% |

## C) Holding-constrained KD×month survivors (20–90d to ex)

Discards Oct/Nov “winners” that only look good because they hold ~200d to next August ex.

| month | K< | exit | train med | test med | med days |
|---:|---:|---:|---:|---:|---:|
| 4 | 20 | T-10 | 9.9% | 15.0% | 81 |
| 4 | 20 | T-15 | 9.9% | 15.0% | 81 |
| 4 | 25 | T-15 | 10.8% | 13.0% | 79 |
| 4 | 25 | T-5 | 9.9% | 13.0% | 79 |
| 4 | 25 | T-10 | 9.9% | 13.0% | 79 |
| 4 | 30 | T-15 | 11.7% | 12.8% | 80 |
| 4 | 30 | T-10 | 10.8% | 12.8% | 80 |
| 4 | 30 | T-5 | 10.5% | 12.8% | 80 |
| 4 | 20 | T-5 | 9.2% | 12.8% | 81 |
| 5 | 20 | T-10 | 8.8% | 11.0% | 62 |
| 5 | 20 | T-15 | 8.8% | 11.0% | 62 |
| 5 | 20 | T-5 | 8.8% | 10.9% | 62 |

## vs your observation

- **Supports:** pre-ex T−10…T−1 high clustering (objective, strong)
- **Supports directionally:** late-spring KD oversold → ride into pre-ex (May survives OOS under constraint)
- **Sharpens:** April entries objectively beat May/Jun on constrained grid; Jun is weaker
- **Rejects as top:** unconstrained Oct/Nov KD “survivors” (path-length bias)

## Verdict

- OBJECTIVE (robust): cash-ex local highs cluster in T-10..T-1 — keep pre-ex skip window
- OBJECTIVE (calendar): Apr H2 / May half-months have consistent positive 40d fwd returns train∩test
- OBJECTIVE (KD, hold 20-90d): April K<20..30 survivors strongest; May K<25 still survives OOS; June weaker
- Your May–Jun K story is directionally right for the FIN dividend cycle, but April entry + T-10 exit is the cleaner objective framing
- Oct/Nov grid winners were mostly holding-period artifacts — discard without constraint
- Caution: still multiple-testing; paper hypotheses only · Soft-Frozen KEEP

## Hard rules

- Soft-Frozen KEEP · no live wire · discovery ≠ observe OPEN

Repro: `repro/fin-objective-regularity-20260909/`
