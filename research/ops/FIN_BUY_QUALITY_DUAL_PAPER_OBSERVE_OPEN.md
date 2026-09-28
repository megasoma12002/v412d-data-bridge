# FIN buy-quality A/B/C multi-paper observe — OPEN

Human: `請上observe` → `OPEN paper observe: FIN buy-quality A/B/C`  
Status: **OPEN → OPERATING** · paper only · Soft-Frozen KEEP · cutover **BLOCKED**

## Books

| Book | Construction |
|---|---|
| `BASE_LIVE_FUSE_COOL` | Live twin Soft+Sleeve+SELL_a75+FUSE+COOL |
| `A_SEED_MA120` | Base + FIN buy_ok AND BELOW_MA120 |
| `B_MA120_OR_K9` | Base + FIN buy_ok AND (BELOW_MA120 OR K9_LT30) |
| `C_OR_K9_AND_BELOW_MA60` | Base + FIN buy_ok AND (BELOW_MA120 OR (K9_LT30 AND BELOW_MA60)) |

## Ops

- Ledgers: `scripts/fin_buy_quality_dual_paper_ledgers.py`
- Monitor: `scripts/fin_buy_quality_month_end_monitor.py`
- Ballot: `FIN_BUY_QUALITY_OBSERVE_BALLOT_EXECUTED_OPEN.md`

Label: `FIN_BUY_QUALITY_DUAL_PAPER_OBSERVE_OPEN_2026-09-28`
