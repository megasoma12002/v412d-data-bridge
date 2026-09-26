# FUSE Soft-sell → 台50反1 — Paper Charter (Stage A)

Date: 2026-09-25  
Status: **CHARTER OPEN → Stage A** · Soft-Frozen live **KEEP** · live wire **false**  
Human: **「還是說有fuse條件成立時呢」**  
Parent: COOL-dwell / COOL-pulse `00632R` → both **SOFT / CAGR↓**

## Clarification (binding)

**`FUSE_ADDITIVE` is not a binary circuit** like `COOL_c8` defending.  
Live FUSE is **always on**: Soft observe softs + Sleeve RSI tilt into Soft-Frozen targets.

Interpretable “FUSE 條件成立” for this charter = **Soft-sell component active**  
(`RSI6_GT80` on Financial names — the live Soft sell soft).  
Sleeve RSI&lt;30 is a **buy-tilt** (not a hedge trigger) → out of scope here.

## Mechanism

Parent live twin: Soft+Sleeve **FUSE** + Soft-Frozen clips + **COOL_c8** (unchanged).

| Gate | `00632R` DEF |
|---|---|
| Soft-sell **off** | 0（賣出） |
| Soft-sell **on** (`any` FIN name RSI6&gt;80) | `α × 0.25` portfolio weight |
| Soft-sell **entry pulse** | same weight for H∈{1,2} sessions then 0 |

α ∈ `{0.50, 1.00}` · H ∈ `{1, 2}` for pulse track · dwell track = hold while sell on.

Equity sleeves still follow live FUSE targets × COOL exposure.

## Objective / gates

Same as COOL×反1: tip OK · held MDD↑≥−0.25 · sealed MDD↑≥0 · held CAGR↑≥+0.20.

| Verdict | Meaning |
|---|---|
| `FUSE_INV_HIT` | ≥1 coexist |
| `FUSE_INV_SOFT` | MDD/tip OK, CAGR short |
| `MDD_BLOCK` / `NO_LIFT` | as named |

## Non-actions

No FUSE retune · no Soft-Frozen flip · no tip `00632R` without Class D · no Sleeve-RSI&lt;30 as inverse trigger.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fuse_softsell_t50_inv_stagea.py
```

Label: `FUSE_SOFTSELL_T50_INV_CHARTER_2026-09-25__STAGE_A_OPEN`
