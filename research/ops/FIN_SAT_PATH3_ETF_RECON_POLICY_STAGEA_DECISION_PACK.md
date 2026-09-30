# FIN_SAT_PATH3_ETF_RECON_POLICY_STAGEA_DECISION_PACK

Date: 2026-09-30 · Verdict: **`ETF_POLICY_LEDGER_RATIO_HIT`**
Register: **0kae** · Parent: **0kad**

## Finding

- COMP/SAT Soft **schedules are identical** → `SCHEDULE_W` **cannot** be Path3-book-sensitive.
- `KEEP` trades 0050 on **0** / 199 flips.
- `LEDGER_SOFT_RATIO` trades 0050 on **199** / 199 flips (median |Δ| 165000).

## Disposition

- Champion paper policy: **`LEDGER_SOFT_RATIO`**
- Full NAV dual = Stage B (not this pack).

## Next

1. Stage B paper dual NAV: Path3 flip+FIN∪TEL ledger KEEP-0050 vs +LEDGER_SOFT_RATIO (tipY/held/sealed + 0050 turnover) — Soft KEEP / no live
2. Do not live-wire ETF policy until paper dual HIT
3. 0kac PAPER_WITHIN_HIT remains primary roadmap

Label: `FIN_SAT_PATH3_ETF_RECON_POLICY_STAGEA_DECISION_PACK_2026-09-30__ETF_POLICY_LEDGER_RATIO_HIT__NO_LIVE`
