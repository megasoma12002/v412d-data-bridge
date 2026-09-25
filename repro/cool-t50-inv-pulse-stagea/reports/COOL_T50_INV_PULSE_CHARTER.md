# COOL → 台50反1 極短期脈衝 — Paper Charter (Stage A)

Date: 2026-09-25  
Status: **CHARTER OPEN → Stage A** · Soft-Frozen live **KEEP** · live wire **false**  
Parent: `COOL_T50_INV_SATELLITE`（全段防守持有）→ **SOFT / CAGR↓**  
Human follow-up: **「或者極短期的買入賣出00632R呢」**

## Mechanism (binding)

Daily `COOL_c8` unchanged. Detect **defend entry** = first day of a defending streak (`cool` drops from 1 → FLOOR).

| Step | Rule |
|---|---|
| Entry day `t0` | Start pulse: hold **`00632R`** for **H** sessions |
| Days `t0 … t0+H−1` | `DEF = α × (1 − FLOOR) = α × 0.50`（固定脈衝尺寸） |
| After pulse / non-entry | `DEF = 0`（賣出）— **即使仍在 defending** |
| Equity sleeves | 仍乘 `cool_exposure`（live twin） |

Contrast vs parent satellite: parent holds 反1 **整段** defending；pulse = **極短固定持有**後強制賣。

## Grid (finite — do not expand after peek)

| Axis | Values |
|---|---|
| `H` (sessions) | `{1, 2, 3, 5}` |
| `α` | `{0.50, 1.00}` |

Controls: `BASE_LIVE_FUSE_COOL` · parent ref `COOL_INV_A25` (report-only, not re-tuned).

## Objective

Same gates as parent: tip OK · held MDD↑ ≥ −0.25 · sealed MDD↑ ≥ 0 · held CAGR↑ ≥ +0.20.

| Verdict | Meaning |
|---|---|
| `COOL_INV_PULSE_HIT` | ≥1 coexist |
| `COOL_INV_PULSE_SOFT` | MDD/tip OK, CAGR short |
| `MDD_BLOCK` / `NO_LIFT` | as named |

Even HIT → paper observe only; live `00632R` = Class D ACCEPT.

## Non-actions

No COOL retune · Soft-Frozen KEEP · no tip rewrite · no intraday (Exact T+1 daily only).

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/cool_t50_inv_pulse_stagea.py
```

Label: `COOL_T50_INV_PULSE_CHARTER_2026-09-25__STAGE_A_OPEN`
