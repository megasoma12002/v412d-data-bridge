# FIN_SAT_PATH3_ETF_RECON_HARDEN_STAGEA_CHARTER

Date: 2026-09-30
Status: **Stage A — Path3 0050 ETF recon harden** · Soft **KEEP** · broker **false** · cutover **BLOCKED** · no live
Parent: 0kag `ETF_NAV_DUAL_HIT` (T+0 full RATIO)
Register: **0kah**

## Question

Can flip-day **clip / slew / deadband** on Soft `0050` weight change improve Soft-core tip/held/sealed vs sticky `KEEP`, and beat or match parent full `LEDGER_SOFT_RATIO` on held CAGR or yearly ret W–L?

## Method

- Soft-core = FIN∪TEL∪0050 · Path3 flips · **fill `t0`**
- Arms: KEEP · RATIO · CLIP_{05,10,15} · SLEW_{50,75} · DEAD_{02,05}
- Between flips: hold Soft-core weights (carve-only)

## Gates (vs KEEP)

- held CAGR lift > 0 · sealed MDD improve ≥ -0.25 pp · tip YTD ≥ -1.0 pp
- Champion: HIT arm maximizing held; prefer harden if beats RATIO held or W–L

## Non-goals

- Live `keep_0050=False` · mute expand · Soft Exact T+1 between flips · satellite · broker · cutover ACCEPT

Label: `FIN_SAT_PATH3_ETF_RECON_HARDEN_STAGEA_CHARTER_2026-09-30__HARDEN__NO_LIVE`
