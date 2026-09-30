# FIN_SAT_PATH3_ETF_SAT_SCOPE_STAGEA_CHARTER

Date: 2026-09-30
Status: **Stage A — can Path3 own Soft 0050 / satellite?** · Soft-Frozen **KEEP** · broker **false** · cutover **BLOCKED** · no live
Parents: 0kab ledger · 0kaa mute · 0kac `WITHIN_SLEEVE_PATH3` (0050 KEEP)
Register: **0kad**

## Question

Today Path3 ledger-scaled recon moves **FIN∪TEL only** (`keep_0050=True`). Mute keeps Soft **0050** and **satellites** (e.g. `00631L`). Should Stage B+ research extend Path3 to those codes?

## Split (do not bundle)

| Code | Role today | Path3 today | Research ask |
|---|---|---|---|
| `0050` | Soft sleeve ETF clip Exact T+1 | KEEP | Optional recon when COMP/SAT ETF shares diverge? |
| `00631L` | COOL/Soft satellite overlay | out of recon | Can Path3 book own satellite, or must overlay re-home first? |

## Method

- Measure COMP vs SAT daily share divergence for 0050 / 00631L (vs FIN/TEL baselines)
- Flip-day subset stats
- Paper probe: `plan_delta_shares_ledger(..., keep_0050=False)` on last COMP→SAT / SAT→COMP
- Satellite: charter gap only (no silent wire into FIN∪TEL engine)

## Non-goals

- Live `keep_0050=False` · mute scope expand · cutover ACCEPT · broker
- Soft clip densify / CONF α flip
- Treating FinPriv names (2881/…) as Path3 Soft universe
- Auto-folding COOL into Path3 without overlay re-home charter

## Verdict ladder

| Verdict | Meaning |
|---|---|
| `ETF_DIVERGES__PROBE_OPEN` | 0050 COMP≠SAT material · paper `keep_0050=False` probe next |
| `ETF_DIVERGES__SATELLITE_OVERLAY_BLOCK` | 0050 material · satellite remains overlay-blocked |
| `ETF_DIVERGES__KEEP_DEFAULT` | 0050 diverges but default KEEP still preferred |
| `NO_ETF_EDGE__SATELLITE_OVERLAY_BLOCK` | 0050 near-identical · satellite not direct P3 |
| `SCOPE_AMBIGUOUS` | need human pick |

Label: `FIN_SAT_PATH3_ETF_SAT_SCOPE_STAGEA_CHARTER_2026-09-30__0050_00631L__NO_LIVE`
