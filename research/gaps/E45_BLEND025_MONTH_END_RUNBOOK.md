# E45 Blend-α=0.25 Month-End Runbook

Status: **OPERATING OBSERVE / PAPER OPS** — Soft-Frozen **[0.50, 0.95] KEEP**.  
Sleeve: BASE vs **BLEND_E45_A25** (`0.75·1 + 0.25·E3_VOLTARGET_WINNER`).  
Parent: `E45_BLEND_ALPHA_PAPER_SCREEN.md` · open `E45_BLEND025_OBSERVE_OPEN.md`  
Parallel: full-E45 observe remains operating separately.

## Cadence

```bash
python3 scripts/e45_blend025_dual_paper_ledgers.py
python3 scripts/e45_blend025_month_end_monitor.py
# or via pack:
python3 scripts/ops_month_end_paper_pack.py
python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers  # slow
```

## Alert policy

Same family as full-E45 observe: YTD / trailing_1y ALERT 3pp / PAUSE 5pp.  
Structural design giveback baselines (α=0.25 screen): heldout **2.83 pp**, sealed **4.36 pp**.

## Stitch

Always blocked on this sleeve. Second human ACCEPT + full checklist still required.

## Label

`E45_BLEND025_MONTH_END_PAPER_RUNBOOK`
