# Data-Source Phase C — `0050` C1 Quarantine / adj_close Probe

Generated: `2026-09-06T10:05:38.175958+00:00`
Status: **OPS PATCH RESEARCH** — Soft-Frozen **KEEP** · no e21 primary rewrite
Soft-Frozen clip: `[0.5, 0.95]` (import only)

## Quarantine list (C1 builder)

Drop these dates from raw-close C1 correlation probes (spike days):

- `2014-01-02`
- `2025-06-18`

## Sealed C1 before / after quarantine

| Slice | N | MAD | Corr |
|---|---:|---:|---:|
| sealed before | 878 | 0.0009117654967668204 | 0.5042695477228695 |
| sealed after quarantine | 877 | 5.022785126495416e-05 | 0.9984951247004171 |

## adj_close probe

| Probe | N | MAD | Corr |
|---|---:|---:|---:|
| sealed raw close vs Yahoo | 878 | 0.0009117654967668239 | 0.5042695477228701 |
| sealed adj_close vs Yahoo | 878 | 0.0001711011494605587 | 0.9943004147398405 |

Read: prefer **adj_close / C2** for history QC; raw-close C1 remains spike-sensitive.

## Non-actions

- No Soft-Frozen / DEFAULT flip · no e21 primary rewrite · no stitch · no vendor reopen

Label: `DATA_SOURCE_PHASE_C_0050_QUARANTINE_2026-09-06__SOFT_FROZEN_KEEP`
