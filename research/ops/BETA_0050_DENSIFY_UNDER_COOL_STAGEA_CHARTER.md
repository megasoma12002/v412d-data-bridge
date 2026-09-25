# β / 0050 densify under COOL — Paper Charter (Stage A)

Date: 2026-09-25  
Status: **PAPER CHARTER OPEN** · Stage A **RUNNING**  
Parent live: `COOL_c8_f50_d21` + `FUSE_ADDITIVE` KEEP · Soft-Frozen tip **KEEP**  
Research order (human): (1) live KEEP → (2) offense = **earn 大盤** → (3) skip 公+民 mix → (4) 民股 only with new mechanism

Label: `BETA_0050_DENSIFY_UNDER_COOL_STAGEA_CHARTER_2026-09-25__PAPER_OPEN__NO_LIVE_WIRE`

## Philosophy (binding for this charter)

| Role | Sleeve | Job |
|---|---|---|
| **Main earn** | **0050** | Capture market β |
| **Aux defense** | Telecom + 公股 Financial | Floor drawdowns |
| **Overlays** | FUSE + COOL | Exposure / cool circuit — not a fourth industry |

Prior step `#282` Soft/Sleeve/FUSE amplitude densify → **`OFFENSE_CAGR_SOFT`** (no tip-clean ≥+0.20pp).  
This charter is the **next offense lever**: raise **0050 clip mass** under frozen COOL, without touching tip membership or adding 民股.

## Question

On Stage-E DEFAULT + live Soft+Sleeve+**COOL_c8**, does any **finite** challenger clip that densifies 0050 (defense floors kept) vs `BASE_FUSE_COOL`:

1. lift held-out CAGR by **≥ +0.20 pp**,  
2. keep held |MDD| **≤ 15%**,  
3. clear tip YTD + 1y MDD↑ ≥ 0?

## Non-actions

- Soft-Frozen live clip / tip rewrite (Class D needs dedicated ACCEPT even if HIT)  
- 公＋民 dollar-split / FinPriv membership (0b / 0b2 STOP)  
- COOL retune · DH re-enable · stack DH+COOL  
- Broker live-write · Gate H auto-fuse  
- Stage A live wire

## Base

| ID | Construction |
|---|---|
| `BASE_FUSE_COOL` | Live twin: Soft `SELL_a05` + Sleeve RSI14 α=0.225 + clips **F[0.60,0.90] T[0.03,0.35] E[0.00,0.35]** + COOL |

## Stage A grid (finite — do not expand after peek)

TEL hi / Soft / Sleeve / COOL **frozen**. FIN **lo ≥ 0.60** (defense floor). Only ETF band + optional FIN hi give-room:

| Track | Idea | Clips (F / T / E) |
|---|---|---|
| `E_HI` | Raise 0050 ceiling | F live · T live · E `[0,0.40]` `[0,0.45]` `[0,0.50]` |
| `E_HI_FIN_ROOM` | Lower FIN hi to feed ETF | F `[0.60,0.85\|0.80]` · T live · E `[0,0.45\|0.50]` |
| `E_FLOOR` | Force minimum 大盤 weight | E lo ∈ `{0.05,0.10}` with matching hi |
| `E_FLOOR_TEL` | Same + slightly higher TEL lo | T lo `0.05` · E densify |

Script: `scripts/beta_0050_densify_under_cool_stagea.py`  
Repro: `repro/beta-0050-densify-under-cool-stagea/`

## Verdicts

| Verdict | Meaning |
|---|---|
| `BETA_0050_HIT` | ≥1 book: CAGR≥+0.20pp · \|MDD\|≤15% · tip OK |
| `BETA_0050_SOFT` | CAGR lift in band but tip fail / short of +0.20 |
| `MDD_TRADEOFF` | CAGR lift but \|MDD\|>15% |
| `NO_LIFT` | no ≥+0.20pp CAGR in band |

Even HIT → **paper observe ballot only**; Soft-Frozen clip flip = separate Class D ACCEPT.

## Artifacts

- EN/ZH charter · screen · decision pack  
- Order note: `research/ops/RESEARCH_ORDER_BETA_DEFENSE.md`

## Label

`BETA_0050_DENSIFY_UNDER_COOL_STAGEA_CHARTER_2026-09-25__PAPER_OPEN__NO_LIVE_WIRE`
