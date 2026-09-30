# FIN_SAT_PATH3_SATELLITE_REHOME_STAGEA_CHARTER

Date: 2026-09-30
Status: **Stage A — satellite overlay re-home vs Path3** · Soft **KEEP** · COOL **KEEP** · broker **false** · cutover **BLOCKED** · no live
Parent: 0kad · Mechanism ask: who owns `00631L` if Path3 expands?
Register: **0kaf**

## Question

Path3 ledgers snapshot `00631L` but recon ignores it. Can Path3 ever own the satellite, or must COOL/Soft overlay re-home first?

## Option ladder (no live)

| Option | Meaning |
|---|---|
| `KEEP_OVERLAY` | status quo — COOL/Soft Exact T+1 owns satellite; Path3 no delta |
| `PATH3_SNAPSHOT_ONLY` | keep ledger column for observe; still no Path3 orders |
| `PATH3_DEF_ON_FLIP` | flip-day recon 00631L to dest book (contends with COOL) |
| `DAILY_PATH3_DEF` | daily Path3 owns DEF — requires COOL re-home ACCEPT |
| `FORBID_IN_LEDGER` | drop satellite from Path3 share SSOT |

## Method

- COMP vs SAT `00631L` share divergence vs schedule `DEF` column
- Live position presence
- Binding: 0kac overlays KEEP under default cutover; COOL live

## Non-goals

- Live Path3 satellite deltas · COOL param flip · broker · 0050 ETF policy (0kae)

Label: `FIN_SAT_PATH3_SATELLITE_REHOME_STAGEA_CHARTER_2026-09-30__00631L_REHOME__NO_LIVE`
