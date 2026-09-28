# FIN sell new-mechanism Stage A — Paper Charter

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · no live wire  
Parent live: Soft-Frozen F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] + FUSE + `SELL_a75` + `COOL_c8_f50_d21` + L1=0.05  
Prior ladder: `FIN_SELL_QUALITY_*` Stage A `MDD_BLOCK` → Stage B `NO_EDGE` (MA-dampen / hard MA / RSI / K9 **exhausted**)  
Human intent (normalized):

```
OPEN Stage A: FIN 賣側新機制 · timing/confirm · 非 MA-dampen 家族 · CAGR+MDD+tip · 賣勝率診斷 · paper only
```

Motivation: 賣側 quality 格（hard MA／RSI／K9／soft-dampen）已證實「拉賣 WR → 傷 MDD」或「護 MDD → 失 CAGR」。改測 **新機制家族**：timing／確認條件（persist、下跌確認、破低、量能、ATR 擴張、MACD、BB、MFI），仍過 CAGR+MDD+tip；賣勝率為診斷加分。

Label: `FIN_SELL_NEW_MECH_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## KEEP

| Item | Status |
|---|---|
| Soft-Frozen clips + Exact T+1 | **KEEP** |
| FUSE + Soft buy assists | **KEEP** |
| Live soft-sell **`SELL_a75`** | **KEEP** |
| `COOL_c8_f50_d21` | **KEEP** |
| Sell **loss-defer** | **REJECTED — do not reopen** |
| Prior MA-dampen densify | **STOP** — do not reopen this track |

## Philosophy

| Regime | Job |
|---|---|
| **Normal rebalance sell** | Optional `fin_sell_ok` AND-gate = timing/confirm overlay on live `SELL_a75` |
| **COOL defense** | Live COOL exposure KEEP |
| **Sell win-rate** | Diagnostic: FIN SELL fill then fwd H=21 **price down** |

Belief: confirm weakness / exhaustion / liquidity before allowing FIN sells → fewer bad exits → CAGR↑ + MDD flat/↑ (+ sell WR↑).  
Risk: over-starve sells → hold losers → MDD↓ / tip fail.

## Question

On `CTRL_BASE` (= Soft + Sleeve + **SELL_a75** + FUSE + COOL), does a finite **timing/confirm** `fin_sell_ok` overlay produce ≥1 book with:

1. held **CAGR↑** ≥ **+0.15pp** (↑ = **chal − base**)  
2. held MDD near-flat (↑ ≥ **−0.25pp**) and abs MDD ≤ **15%**  
3. tip YTD / 1y MDD improve ≥ **0**  
4. FIN SELL win-rate (H=21, fwd ret **&lt; 0**) improve ≥ **+1.0pp** vs control

## Explicit exclusions

- Hard MA / NOT_BELOW_MA / ABOVE_MA  
- RSI-level / K9-level hard gates (prior Stage A)  
- Soft-dampen / boost-only (prior Stage B)  
- Loss-defer  

## Grid (finite)

| ID | `fin_sell_ok` |
|---|---|
| `CTRL_BASE` | none |
| `N_PERSIST2` | live sell-fire (`RSI6_GT80`) true 2 consecutive days |
| `N_PERSIST3` | sell-fire persist 3 days |
| `N_DN1` | today ret &lt; 0 |
| `N_DN2` | 2 consecutive down days |
| `N_BREAK5` | close &lt; prior 5d low |
| `N_BREAK10` | close &lt; prior 10d low |
| `N_VOL1P5` | volume &gt; 1.5× MA20 |
| `N_VOL2` | volume &gt; 2× MA20 |
| `N_ATR_UP` | ATR14 rising vs 5d ago |
| `N_MACD_NEG` | `MACD_HIST_NEG` |
| `N_MACD_FLIP` | MACD hist cross to neg |
| `N_BB_UPPER` | `BB_UPPER` |
| `N_MFI80` | `MFI14_GT80` |
| `N_UP1_NEG` | today ret &gt; 0 (**NEG** control) |

## Verdict ladder

| Label | Meaning |
|---|---|
| `SELL_NEW_MECH_HIT` | ≥1 challenger clears **all** gates (incl. sell WR) |
| `WIN_SOFT` | CAGR+MDD+tip clear; sell WR short |
| `CAGR_SOFT` | MDD+tip clear; CAGR short |
| `MDD_BLOCK` / `TIP_BLOCK` | structural fail |
| `NO_EDGE` | no legal economic clear |

## Run

```bash
PYTHONPATH=scripts python3 scripts/fin_sell_new_mech_stagea.py
```

Artifacts: `research/ops/FIN_SELL_NEW_MECH_STAGEA_*` · `repro/fin-sell-new-mech-stagea/`
