# FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_CHARTER

Date: 2026-09-30
Status: **Stage B — Path3 0050 ETF recon paper NAV dual** · Soft **KEEP** · broker **false** · cutover **BLOCKED** · no live
Parent: 0kae `ETF_POLICY_LEDGER_RATIO_HIT`
Register: **0kag**

## Question

Does flip-day `LEDGER_SOFT_RATIO` (move Soft 0050 toward dest book Soft-core weight) **improve** Path3 Soft-core tip/held/sealed vs status-quo sticky-0050 `KEEP`?

## Method

- Soft-core = FIN∪TEL∪0050 from COMP/SAT daily share ledgers × close
- Path3 flips from `p3_t0_state` signal
- Between flips: **hold** Soft-core weights (carve-only paper)
- Arms: `KEEP` vs `LEDGER_SOFT_RATIO` (+ `FULL_DAILY` context)
- Metrics: WINDOWS_STANDARD + tip YTD/1y · lift = chal − KEEP

## Gates

- held CAGR lift > 0
- sealed MDD improve ≥ -0.25 pp
- tip YTD CAGR lift ≥ -1.0 pp (or null)

## Non-goals

- Live wire · mute expand · Soft Exact T+1 between flips · satellite · broker

Label: `FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_CHARTER_2026-09-30__NAV_DUAL__NO_LIVE`
