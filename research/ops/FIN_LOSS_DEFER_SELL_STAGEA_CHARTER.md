# FIN loss-defer sell Stage A — Paper Charter

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · no live wire  
Parent live: Soft-Frozen F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] + FUSE + `SELL_a75` + `COOL_c8_f50_d21` + L1=0.05  
Human intent (normalized):

```
OPEN Stage A charter: FIN 浮虧延後賣（等回本）· COOL 強制減碼仍優先 · paper only
```

Motivation: tip fills show **11/24** realized SELL losses under FIFO all-in cost, and **12** open BUY lots underwater vs tip — hypothesis that **穩健金融股** can wait for cost recovery before rebalance sells.  
**Important:** this is **not** an accounting FIFO rewrite; it is a **sell-eligibility / sell-priority** overlay on rebalance SELLs.

Label: `FIN_LOSS_DEFER_SELL_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Philosophy

| Regime | Job |
|---|---|
| **Normal rebalance** (COOL exposure = 1) | Optionally **defer** FIN (and optionally TEL) SELL when mark-to-market vs FIFO all-in cost is still a loss, up to a finite wait |
| **COOL defense** (exposure &lt; 1) | **Never** defer — forced de-risk / cash raise **always wins** |
| **Accounting** | FIFO / tax-lot math stays research-report only; live tip books untouched |

Belief to test (may be false): “穩健標的等一陣子一定會回本” improves CAGR without harming held MDD.  
Risk to reject: deferred losers **amplify MDD** and fight `COOL_c8`.

## Question

On `BASE_LIVE_FUSE_COOL` (Exact T+1 · Soft-Frozen KEEP), does any **finite** loss-defer sell challenger vs base:

1. lift held-out CAGR by **≥ +0.15 pp**,  
2. keep held MDD↑ **≥ −0.25 pp** (near-flat; prefer ≥ 0),  
3. keep held |MDD| **≤ 15%**,  
4. clear tip YTD + trailing_1y MDD↑ **≥ 0** (tip-safe),  
5. **never** suppress sells while COOL exposure &lt; 1?

## Non-actions

- Soft-Frozen live clip / L1 / Exact T+1 / tip rewrite  
- Live wire · broker · SendAlgo  
- Re-enable DH · weaken COOL trigger/floor/dwell  
- Change FIFO **accounting** SSOT or tax books  
- Defer sells on `0050` / `00631L` / FinPriv carve in Stage A v1 (FIN-pub first; optional TEL track only)  
- “Wait forever until green” — max wait is finite or COOL overrides

## Base

| ID | Construction |
|---|---|
| `BASE_LIVE_FUSE_COOL` | Live Soft-Frozen + FUSE `SELL_a75` + Sleeve α=0.225 + KD_OPT + TEL policy live + `COOL_c8_f50_d21` · Exact T+1 · L1=0.05 |

## Cost / loss definition (paper)

| Field | Spec |
|---|---|
| Lot cost | FIFO all-in: `fill_price + fees_tax/qty` on BUY |
| Mark | Session `adj_close` (or live market close used by paper harness) |
| Unrealized loss | `mark < lot_unit_cost` on the lots that would be consumed by a proposed SELL |
| Defer unit | Per **name** (code) on proposed Soft-Frozen rebalance SELL quantity |

## Stage A grid (finite — do not expand after peek)

Soft/Sleeve/FUSE/COOL/clip/L1/T+1 frozen except the defer overlay.

| Track | ID | Spec |
|---|---|---|
| Control | `CTRL_NO_DEFER` | Base (no overlay) |
| FIN only | `D_FIN_LOSS0_W5` | Defer FIN SELL while unrealized loss; max wait **5** sessions; COOL&lt;1 → sell now |
| FIN only | `D_FIN_LOSS0_W10` | max wait **10** |
| FIN only | `D_FIN_LOSS0_W21` | max wait **21** (align COOL dwell scale) |
| FIN band | `D_FIN_LOSS2_W10` | Defer only if loss **≤ −2%** vs cost; max wait 10; else sell |
| FIN band | `D_FIN_LOSS5_W10` | Defer only if loss **≤ −5%**; max wait 10 |
| Priority | `D_FIN_WORST_FIRST_W10` | When selling is allowed, consume **worst** (most underwater) lots first (anti-FIFO priority); still COOL-forced |
| TEL opt | `D_TEL_LOSS0_W10` | Same as FIN W10 but **TEL names only** (separate book) |
| Stress | `D_FIN_LOSS0_W10_NOCOOLGATE` | **Negative control** — defer even under COOL (expect `MDD_BLOCK`; proves gate needed) |

Script (to land with screen): `scripts/fin_loss_defer_sell_stagea.py`  
Repro: `repro/fin-loss-defer-sell-stagea/`

## Gates

| Gate | Pass |
|---|---|
| CAGR | held CAGR↑ ≥ **+0.15 pp** vs base |
| MDD near-flat | held MDD↑ ≥ **−0.25 pp** |
| MDD band | held \|MDD\| ≤ **15%** |
| Tip-safe | tip YTD + 1y MDD↑ ≥ **0** |
| COOL integrity | books with defer-under-COOL must **FAIL** or be tagged `COOL_GATE_VIOLATION` (only `*_NOCOOLGATE` may show this) |

## Verdicts

| Verdict | Meaning |
|---|---|
| `LOSS_DEFER_HIT` | ≥1 legal book clears CAGR + MDD near-flat + tip-safe + COOL integrity |
| `CAGR_SOFT` | MDD/tip OK; CAGR short of +0.15 |
| `MDD_BLOCK` | any material held/tip MDD worsen (incl. NOCOOLGATE as expected fail) |
| `NO_LIFT` | no CAGR story; MDD not better |
| `COOL_GATE_REQUIRED` | only NOCOOLGATE “works” on CAGR → defer-without-COOL forbidden |

Even `LOSS_DEFER_HIT` → **paper observe ballot only**; live sell overlay = separate ACCEPT.

## Binding reminders

1. Soft-Frozen / tip / Exact T+1 **KEEP** this charter.  
2. COOL forced de-risk is **lexically prior** to loss-defer.  
3. Tip 11 losing sells are **evidence for the question**, not authorization to change live.  
4. Do not confuse lot accounting FIFO with this sell overlay.

## Label

`FIN_LOSS_DEFER_SELL_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`
