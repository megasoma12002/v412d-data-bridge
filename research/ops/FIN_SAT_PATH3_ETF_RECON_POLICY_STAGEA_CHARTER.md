# FIN_SAT_PATH3_ETF_RECON_POLICY_STAGEA_CHARTER

Date: 2026-09-30
Status: **Stage A — Path3 0050 ETF recon policy** · Soft **KEEP** · broker **false** · cutover **BLOCKED** · no live
Parent: 0kad `ETF_DIVERGES__SATELLITE_OVERLAY_BLOCK`
Register: **0kae**

## Question

Which paper policy can make Path3 move Soft `0050` when COMP≠SAT, given `keep_0050=False` freeze-sleeve-$ is a no-op?

## Candidates

| ID | Rule |
|---|---|
| `KEEP` | status quo — never touch 0050 |
| `SCHEDULE_W` | paper Soft schedule `0050` weight × live Soft-core $ |
| `LEDGER_SOFT_RATIO` | paper ledger $ weight 0050/(FIN+TEL+0050) × live Soft-core $ |

## Method

- Prove COMP vs SAT sleeve schedules identical or not
- On each Path3 flip: compute 0050 target/delta under each policy (live tip capital proxy)
- Champion = material flip-day 0050 trades + book-sensitive (not schedule-identical dead)

## Non-goals

- Live wire · mute expand · cutover ACCEPT · broker · satellite 00631L
- Full NAV paper dual (Stage B after policy HIT)

Label: `FIN_SAT_PATH3_ETF_RECON_POLICY_STAGEA_CHARTER_2026-09-30__0050_POLICY__NO_LIVE`
