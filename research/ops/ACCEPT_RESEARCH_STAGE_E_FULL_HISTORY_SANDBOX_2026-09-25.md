# ACCEPT RESEARCH — Stage-E full-history sandbox resim (no tip rewrite)

Status: **RESEARCH ACCEPTED** (2026-09-25 deferred-ops ballot)  
Soft-Frozen tip: **KEEP** — **do not** rewrite `forward/e21` history

## Ballot

> `ACCEPT RESEARCH Stage-E full-history sandbox resim under repro/; compare to tip; never overwrite Soft-Frozen nav/fills/orders.`

## Why

Method change to `E22_v3_recv_pay_effdelay` is **forward-only** on tip (`ACCEPT_TIP_BOOKS_ALIGN_V3`).  
Optional sandbox answers “what would NAV look like if Stage-E applied over the full sample?” without inventing tip.

## Rules

1. Outputs only under `repro/stage-e-full-history-sandbox/` (or dated subdir).
2. Read tip / market / dividend ledgers as inputs — **no** write to `forward/e21/`.
3. Use preserved payment dates from `e22_dividend_events.csv` (blank pay fail-closed under Stage-E).
4. Report ≠ promote; Soft-Frozen KEEP.

## Entrypoint

```bash
python3 scripts/e22_stage_e_full_history_sandbox.py --out-dir repro/stage-e-full-history-sandbox
```

Label: `ACCEPT_RESEARCH_2026-09-25_STAGE_E_FULL_HISTORY_SANDBOX`
