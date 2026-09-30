# FIN_SAT_PATH3_ETF_RECON_YEARMIT_STAGEA_CHARTER

Date: 2026-09-30
Status: **Stage A — Path3 0050 ETF recon year-mitigation** · Soft **KEEP** · broker **false** · cutover **BLOCKED** · no live
Parent: 0kah `ETF_HARDEN_HIT` / `DEAD_05`
Register: **0kai**

## Question

Can **asymmetric** or **larger deadband** rules on flip-day Soft `0050` shrink calendar-loser drag (esp. 2024) vs parent `DEAD_05` while still HITting sticky `KEEP` on held/sealed/tip?

## Diagnosis (0kah)

- Loser years under DEAD_05: 2016 / 2020 / 2023 / **2024 (~−5pp)**
- 2024 large *cut* of 0050 hurt; 2025 large cut helped → no look-ahead block-all-cuts (MDD_BLOCK in probe)

## Method

- Soft-core carve-only · Path3 flips · **fill `t0`**
- Arms: KEEP · RATIO · DEAD_{05,07,08} · ADD_FULL_CUT_D{05,07} · CUT_FULL_ADD_D05 · CLIP_08
- Champion among HIT: maximize sum ret-lift on loser years, then held

## Non-goals

- Look-ahead year labels · live wire · mute expand · Soft Exact T+1 · satellite · broker

Label: `FIN_SAT_PATH3_ETF_RECON_YEARMIT_STAGEA_CHARTER_2026-09-30__YEARMIT__NO_LIVE`
