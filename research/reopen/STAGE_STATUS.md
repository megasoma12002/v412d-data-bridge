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
| Stage 8b | Multi-ETF screen 00713/00918/00896/00878/00927 | **Interesting sandbox** (short windows); **no promote** |

## Official posture

1. Official: **E22_v2 ex-date** (`forward/e22_v2/`) — 8 names, 3 sleeves
2. Paper: **E22_v3 payment-date** — no auto-cutover
3. E45=B; no G4 shorts; no extra ETF sleeves in live

## Stage 8 / 8b

- 0056: **STOP**
- 00713 / 00878: fail bar on longer windows
- 00918 / 00896 / 00927 SLEEVE4: clear bar only on **short** listing windows → `STAGE8B_MULTI_ETF_INTERESTING_CONTINUE_SANDBOX` (research only)
- Docs: `research/reopen/STAGE8_DECISION.md`, `research/reopen/STAGE8B_DECISION.md`
- 00981A / 00991A: **`INCONCLUSIVE_TOO_SHORT`** (00991A cannot run; 00981A only 62 post-warmup days)

## Recommended next

Ops monitoring; optional Stage 8b follow-up = dividend-adjusted ranking + cost stress on **00896/00918** only (still no live cutover). Do not retune stopped Stage 7/8 thresholds or reopen stopped 3A feature sets.

Promotion bar unchanged: challenger + evidence + explicit approval.
