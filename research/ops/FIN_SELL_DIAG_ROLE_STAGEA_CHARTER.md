# FIN sell diagnostic-role Stage A — Paper Charter

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · **`fin_sell_ok` OFF** · no live wire  
Parent live: Soft-Frozen F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] + FUSE + `SELL_a75` + `COOL_c8_f50_d21` + L1=0.05  
Prior: sell-quality `MDD_BLOCK`/`NO_EDGE` · sell new-mech `MDD_BLOCK` (hard gates starve exits)  
Human intent (normalized):

```
OPEN Stage A: FIN 賣側全新角色 · 只診斷／標註 live 賣出 · 不閘 fin_sell_ok · paper only
```

Motivation: 硬閘 `fin_sell_ok` 兩條梯子（quality／timing-confirm）都把賣 WR↑ 換成 MDD/tip↓。改成 **診斷角色**：在 **不改成交、不加閘** 的 live `SELL_a75` 賣出上，標註屬性並量條件勝率——找「哪個情境賣得比較對」，**不**據此自動閘賣。

Label: `FIN_SELL_DIAG_ROLE_STAGEA_CHARTER_2026-09-28__OPEN__NO_GATE__NO_LIVE`

## Role (binding)

| Item | Rule |
|---|---|
| Simulation | **One** `CTRL_BASE` book only |
| `fin_sell_ok` | **Never passed** to `simulate_core` |
| NAV / fills | Identical to live Soft+FUSE+SELL_a75+COOL path |
| Output | Per-attribute conditional sell WR vs unconditional |
| Observe / live | **Not authorized** by DIAG_* alone |
| Hard-gate reopen | **Forbidden** from this charter |

## KEEP / REJECT

| Item | Status |
|---|---|
| Soft-Frozen + Exact T+1 + COOL + SELL_a75 | **KEEP** |
| Sell loss-defer | **REJECTED** |
| Prior hard-gate densify | **STOP** (do not reopen here) |

## Question

On live FIN SELL fills (fwd H=21, win = price down), does any predeclared attribute show:

1. **DIAG_SIGNAL**: WR↑ ≥ **+3.0pp** vs unconditional · n ≥ **80** · coverage ∈ **[5%, 70%]**  
2. else **DIAG_WEAK**: WR↑ ≥ **+1.5pp** · n ≥ **50** · same coverage  
3. else **NO_SIGNAL**

## Attributes (finite)

`A_PERSIST2/3` · `A_DN1/2` · `A_BREAK5/10` · `A_VOL1P5/2` · `A_ATR_UP` · `A_MACD_NEG/FLIP` · `A_BB_UPPER` · `A_MFI80` · `A_RSI6_GT80` · `A_UP1` (NEG expect)

## Non-actions

- Apply / densify `fin_sell_ok`  
- Soft-dampen sell scores from this pack  
- Open paper observe or live from DIAG_*  
- Soft-Frozen / tip / FIFO rewrite  

## Follow-up if SIGNAL

Allowed next ask: **paper monitor/log** attribute flags on live sells (still no gate).  
Any gate/soft-tilt needs a **new** charter + human OPEN.

## Run

```bash
PYTHONPATH=scripts python3 scripts/fin_sell_diag_role_stagea.py
```

Artifacts: `research/ops/FIN_SELL_DIAG_ROLE_STAGEA_*` · `repro/fin-sell-diag-role-stagea/`
