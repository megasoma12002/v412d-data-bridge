# Archive Sentinel Hygiene (`or 0` / `or 9`)

Date: 2026-09-05  
Status: **POLICY LANDED** — Layer 5 hygiene; no Soft-Frozen change.

## Problem

Archive / research scripts sometimes coerce missing metrics with:

```python
(cagr or 0.0) - 0.5 * abs(mdd or 0.0)
(turn or 9) <= TURNOVER_CEILING
key=lambda r: abs(r["max_drawdown"] or 9)
```

`or 0` can hide legitimate 0.0 vs missing; `or 9` is a sort/gate sentinel that can silently pass/fail when the field is `None`.

## Policy (going forward)

| Context | Rule |
|---|---|
| Live / Soft-Frozen / cutover path | **Forbidden** — use explicit `None` checks; fail closed |
| Month-end / ops monitors | **Forbidden** for decision gates; `mtd` CAGR already display-only |
| Active research screens (OOF/held-out) | Prefer `math.inf` / `None` + explicit skip; avoid `or 9` in gate predicates |
| Frozen archive scripts under `scripts/e50a3*` / old stage grids | **Accepted debt** — do not mass-rewrite; label RESEARCH_ONLY |

## This round

1. Documented the rule (this file).  
2. Ops emitters now pull Soft-Frozen clip from `e16_soft_frozen_base` (no literal drift).  
3. No bulk rewrite of archived `or 9` stage scripts (risk > value).

## Re-check

```bash
rg -n "or 9" scripts/ops_*.py scripts/e16_*month_end*.py scripts/e21_*.py
# expect: no gate sentinels on live/ops paths
```
