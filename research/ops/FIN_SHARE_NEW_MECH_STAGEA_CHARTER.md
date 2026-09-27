# FIN-share new-mechanism Stage A — all remaining levers (paper)

Date: 2026-09-27  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · L1=0.05 **KEEP** · no live wire  
Human: 金融比例滿高 → 還能研究怎麼調比例嗎 → **請研究全部新機制**

Label: `FIN_SHARE_NEW_MECH_STAGEA_CHARTER_2026-09-27__OPEN__NO_LIVE_WIRE`

## Context

Live Soft-Frozen keeps FIN in **[0.60, 0.80]** (β densify already LIVE). Tip drifts ~87% FIN vs ~75% sleeve target.  
**Exhausted / closed for retune-after-peek:** Asymm CAGR_SOFT · β Stage B tip-fail · within-sleeve micro NO_FLAT · 公+民 STOP · E16/PRIV next-mech miss.  
**Still open (this Stage A):** genuinely new actuators to **lower FIN share** or trade it for CAGR/MDD — not densify the same clip grid.

## Tracks (finite)

| Track | ID pattern | Mechanism |
|---|---|---|
| **CLIP** | `CLIP_F070/072/075` | Static Soft flip candidate: FIN hi → **0.70 / 0.72 / 0.75** (ETF hi KEEP 0.50) |
| **COND** | `COND_BULL_F070/072` · `COND_BSIDE_F070` | Regime-conditional **FIN cap** (Bull or Bull+Side): on-gate FIN hi lowered; else live clips |
| **SKEW** | `SKEW_FIN_ONLY` · `SKEW_FIN_HEAVY` | COOL cut **skewed to FIN** (TEL/0050 cut less or not at all) |
| **CASH** | `CASH_F05` · `CASH_F10` | Permanent cash floor **5% / 10%** (scales Soft sleeves) |
| **SAT_REF** | `SAT_A20_H5` | Parent next-mech **MECH_HIT** reference (CONF densify — not a FIN-share lever) |

## Base

| ID | Construction |
|---|---|
| `BASE_LIVE_CONF` | Soft-Frozen + L1=0.05 + SELL_a75 + COOL_c8 + CONF_RET3_A10_H5 |

## Non-actions

- Exact T+1 · tip rewrite · live clip flip from Stage A · broker  
- Densify Asymm / β Stage B cells after peek · reopen 公+民 coexist grid · α densify beyond SAT_A20  

## Gates (vs `BASE_LIVE_CONF`)

| Gate | Pass |
|---|---|
| CAGR | heldout lift ≥ **+0.20pp** |
| MDD | heldout MDD improve ≥ **−0.50pp** |

Diagnostics (not gates): mean FIN weight · FIN↓ vs base.

## Verdicts

`MECH_HIT` · `CAGR_SOFT` · `FIN_DOWN_NO_LIFT` · `NO_LIFT` · `CLOSE_OBSERVE_RECOMMENDED`

Even HIT → paper only; **at most one** track for ACCEPT discussion. CLIP HIT → Soft-Frozen flip ballot only (not silent live).

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_share_new_mech_stagea.py
```

Artifacts: `research/ops/FIN_SHARE_NEW_MECH_STAGEA_*` · `repro/fin-share-new-mech-stagea/`
