# Next-mechanism Stage A — satellite densify / E16 score / FinPriv reopen (paper)

Date: 2026-09-27  
Status: **Stage A OPEN** · Soft-Frozen clips **KEEP** · Exact T+1 **KEEP** · L1=0.05 **KEEP** · no live wire  
Parent: earn-beta menu `CLOSE_OBSERVE_RECOMMENDED`; remaining space = **new mechanism**, not old-grid retune  
Human: 是不是還有空間 → **請研究**

Label: `NEXT_MECH_STAGEA_CHARTER_2026-09-27__OPEN__NO_LIVE_WIRE`

## Context

Exhausted: fill levers · residual L1 (LIVE) · earn-beta BETA/COOL/FIN_DYN/VOL.  
Live still loses TAIEX/0050 CAGR while winning MDD.  
This Stage A probes **three new-mechanism directions** (finite):

1. **SAT** — densify live `CONF_RET3` 00631L short-assist (α / H)  
2. **E16** — rewrite Bull prior / score mix (router signal source)  
3. **PRIV** — reopen FinPriv with **one new AND cell densify** off V8 best SOFT (not full V8 grid)  
4. **CLOSE** — meta if all miss CAGR gate  

## Question

Vs base = live twin **FUSE+COOL+L1=0.05+CONF_RET3 α=0.10 H=5**:

1. Does thicker/longer CONF pulse clear held CAGR ≥ **+0.20pp** with MDD near-flat?  
2. Does Bull-prior→0050 or m20-heavier score clear the same?  
3. Does V8-best densify (`BSIDE_MA120_COOL1` F08/F10 KD_MAY) clear the same?  

## Non-actions

- Exact T+1 · tip rewrite · live clip / L1 flip · broker  
- Full V8 48-book retune · COOL off · Soft-Frozen membership expand to live from Stage A  

## Base

| ID | Construction |
|---|---|
| `BASE_LIVE_CONF` | Soft-Frozen + L1=0.05 + SELL_a75 + COOL_c8 + **CONF_RET3_A10_H5** OFF=00631L |

## Grid (finite)

| Track | ID | Spec |
|---|---|---|
| SAT | `SAT_A15_H5` | CONF RET3 · α=**0.15** · H=5 |
| SAT | `SAT_A20_H5` | α=**0.20** · H=5 |
| SAT | `SAT_A10_H8` | α=0.10 · H=**8** |
| E16 | `E16_BULL_E20` | Bull prior FIN/TEL/0050 = **[0.70,0.10,0.20]** |
| E16 | `E16_M20_050` | score weights m20=**0.50**, m60=0.25, −vol=0.15, d60=0.10 |
| PRIV | `PRIV_V8BEST_F08` | V8 tag `BSIDE_MA120_COOL1` · frac=**0.08** · PRIV_KD_MAY |
| PRIV | `PRIV_V8BEST_F10` | same · frac=**0.10** |
| CLOSE | *(meta)* | no CAGR gate → `CLOSE_OBSERVE_RECOMMENDED` |

## Gates

| Gate | Pass |
|---|---|
| CAGR | heldout lift ≥ **+0.20pp** vs `BASE_LIVE_CONF` |
| MDD | heldout MDD improve ≥ **−0.50pp** |

## Verdicts

`MECH_HIT` · `CAGR_SOFT` · `NO_LIFT` · `CLOSE_OBSERVE_RECOMMENDED`

Even HIT → paper only; **at most one** track for ACCEPT discussion.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/next_mech_stagea.py
```

Artifacts: `research/ops/NEXT_MECH_STAGEA_*` · `repro/next-mech-stagea/`
