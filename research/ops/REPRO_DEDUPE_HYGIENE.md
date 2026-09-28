# Repro / ops dedupe hygiene

Date: 2026-09-28  
Soft-Frozen **KEEP** · Exact T+1 **KEEP** · live tip **untouched**

## Rules

1. **Decision packs SSOT** = `research/ops/*DECISION_PACK*` (and sibling ACCEPT / cutover notes).
2. `repro/*/reports/*DECISION_PACK*` must be a **pointer** (see `scripts/ops_repro_ssot.py`), not a byte clone.
3. Do **not** commit `repro/*/reports/nav_*.csv` when the same bytes already live under `outputs/` (gitignore + hygiene test).
4. Prefer regenerating NAV from the stage script over copying `BASE_LIVE*` / `LIVE_COOL*` across stages.
5. Local `.worktrees/` is gitignored — prune with `git worktree remove` / `git worktree prune` (do not leave multi-hundred-MB checkouts).

## Helper

```bash
# From stage scripts after writing ops SSOT:
from ops_repro_ssot import write_ops_and_repro_pointer
write_ops_and_repro_pointer(OPS / "FOO_DECISION_PACK.md", REP / "FOO_DECISION_PACK.md", body)
```

## Intentional non-dedupe

- `OPS_STATUS.md` ↔ `HUMAN_DECISION_REGISTER.md` ↔ `ACCEPT_*` (governance map vs binding verdicts)
- Live tip path `forward/e21/`
- Thin `*_month_end_monitor.py` / `*_dual_paper_ledgers.py` entrypoints (shared drivers already exist)

Label: `REPRO_DEDUPE_HYGIENE_2026-09-28`
