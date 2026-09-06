# Data-Source Phase C Follow-up — Slice Drift / Adj-CA

Generated: `2026-09-06T06:54:33.219493+00:00`
Status: **OPS RESEARCH** — Soft-Frozen **KEEP** · no e21 primary rewrite · Yahoo TAIEX failover **opt-in only**

## Inputs

- C1: `repro/data-source-phase-c/c1_fin12_history_returns.csv`
- C2: `repro/data-source-phase-c/c2_adj_returns.csv`

## Sealed_2023_plus C1 (live close vs Yahoo)

| Code | N | MAD | Corr | Status |
|---|---:|---:|---:|---|
| `0050` | 878 | 0.00091 | 0.5043 | DRIFT |
| `5880` | 878 | 0.00021 | 0.9662 | PASS |
| `2892` | 878 | 0.00016 | 0.9875 | PASS |
| `2886` | 878 | 0.00009 | 0.9952 | PASS |
| `2880` | 878 | 0.00008 | 0.9982 | PASS |
| `2412` | 878 | 0.00007 | 0.9895 | PASS |
| `3045` | 878 | 0.00006 | 0.9974 | PASS |
| `4904` | 878 | 0.00005 | 0.9968 | PASS |

**C1 sealed DRIFT count:** 1 → `0050`

## Sealed_2023_plus C2 (adj returns)

| Code | N | MAD | Corr | Status |
|---|---:|---:|---:|---|
| `2892` | 878 | 0.00007 | 0.9957 | PASS |
| `2412` | 878 | 0.00007 | 0.9879 | PASS |
| `5880` | 878 | 0.00007 | 0.9943 | PASS |
| `3045` | 878 | 0.00006 | 0.9969 | PASS |
| `4904` | 878 | 0.00005 | 0.9963 | PASS |
| `0050` | 878 | 0.00005 | 0.9985 | PASS |
| `2880` | 878 | 0.00005 | 0.9988 | PASS |
| `2886` | 878 | 0.00005 | 0.9982 | PASS |

**C2 sealed WARN count:** 0 (none)

## Slice rollup (any DRIFT/WARN)

| Slice | C1 DRIFT codes | C2 WARN codes |
|---|---|---|
| `full` | 0050 | — |
| `pre_2020` | 0050, 2880, 2892, 5880 | — |
| `covid_2020` | — | — |
| `heldout_2019_plus` | 0050 | — |
| `sealed_2023_plus` | 0050 | — |

## Non-actions

- Soft-Frozen KEEP · no silent e21 primary switch · no Goodinfo/Wantgoo/CMoney reopen
- TAIEX Yahoo failover remains **opt-in helper only**

Label: `DATA_SOURCE_PHASE_C_FOLLOWUP_2026-09-06__SOFT_FROZEN_KEEP`
