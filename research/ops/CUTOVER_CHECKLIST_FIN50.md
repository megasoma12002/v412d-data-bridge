# Cutover checklist — FIN_CAP_50

Status: **PREP ONLY** — Soft-Frozen **[0.50, 0.95] stays**.  
Authoritative go-live today: **`NOT_READY_SEALED_CAGR`**.

## What cutover would change

- Static live Financial clip **[0.50, 0.95] → [0.35, 0.50]** (named FIN_CAP_50).
- Different from L4 (L4 is path-dependent logic, not this static swap).

## Gates (all required)

| # | Gate | Current | Pass? |
|---|---|---|---|
| 1 | Exact T+1 (Gate A) | PASS on verify artifact | YES |
| 2 | Held-out 2019+ (Gate B) | PASS (MDD improve; CAGR gb ≤3 pp) | YES |
| 3 | Sealed 2023+ (Gate C) | **FAIL** — CAGR giveback ~4.33 pp | **NO** |
| 4 | Soft-Frozen unchanged until PR (Gate D) | [0.50, 0.95] | YES |
| 5 | Month-end Gate E (no YTD/1y PAUSE) | YTD/1y **PAUSE_REVIEW** | **NO** |
| 6 | Re-run go-live verify → not `NOT_READY_SEALED_CAGR` | Still NOT_READY | **NO** |
| 7 | Explicit human cutover PR | Not opened | **NO** |

## Blockers now

1. **Sealed CAGR giveback** above gate — needs **new research charter** (do not retune locked FIN_CAP_50).  
2. **YTD / 1y PAUSE_REVIEW** on month-end.  
3. No human PR.

## When gates clear — PR shape

1. Title: `Cutover: Soft-Frozen Financial clip → FIN_CAP_50 [0.35, 0.50]`  
2. Must attach fresh `FIN_CAP_50_GO_LIVE_VERIFY` with all gates PASS  
3. Single-source edit only via approved path (`e16_soft_frozen_base` or explicit cutover module) — **no silent edit**  
4. Forbidden: bundling L4 DD-path, E45, E50-A overlay in the same PR  

## Operator loop until then

```bash
python3 scripts/ops_month_end_paper_pack.py
# review research/gaps/FIN_CAP_50_MONTH_END_MONITOR.md
# sealed path still blocked by FIN_CAP_50_GO_LIVE_VERIFY.md
```

Label: `CUTOVER_CHECKLIST_FIN50__NOT_AUTHORIZED`
