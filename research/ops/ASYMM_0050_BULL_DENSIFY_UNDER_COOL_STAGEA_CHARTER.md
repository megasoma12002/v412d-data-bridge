# Asymmetric 0050 Bull densify under COOL — Paper Charter (Stage A)

Date: 2026-09-25  
Status: **OPEN · Stage A** · Soft-Frozen tip **KEEP** · live wire **false**  
Parent live: Soft-Frozen **F[0.60,0.80] T[0.03,0.35] E[0.00,0.50]** + Soft+Sleeve+**COOL_c8** + FUSE  
Human (exact):

```
OPEN charter: 非對稱0050 Bull加碼 / MDD持平 under COOL
```

Prior: Stage A always-on densify → **`BETA_0050_HIT`** (near-flat MDD −0.06pp) → Class D live flip.  
Stage B always-on fine grid → **`HELD_FLAT_TIP_FAIL`** (held MDD↑≥0 + CAGR≥+0.20 available; tip MDD fails).  
This charter is the **next offense lever**: densify **0050 only in Bull (or Bull+Sideways)**; non-offense regimes keep live (or restore prior FINBAND) so MDD can stay flat while tip stays clean.

Label: `ASYMM_0050_BULL_DENSIFY_UNDER_COOL_STAGEA_CHARTER_2026-09-25__OPEN__NO_LIVE_WIRE`

## Philosophy

| Regime | Job |
|---|---|
| **Bull** (offense) | Raise 0050 clip mass beyond live Soft-Frozen |
| **Non-Bull** | Keep live clips, or optionally restore prior FINBAND defense |

Overlays FUSE+COOL frozen. No 民股. No tip rewrite.

## Question

On live Soft-Frozen + COOL twin, does any **finite** regime-conditional clip challenger vs `BASE_LIVE_FUSE_COOL`:

1. lift held-out CAGR by **≥ +0.20 pp**,  
2. keep held MDD↑ **≥ 0** (flat or better),  
3. clear tip YTD + 1y MDD↑ ≥ 0,  
4. keep held |MDD| **≤ 15%**?

## Non-actions

- Soft-Frozen live clip / tip rewrite (even HIT → paper observe ballot only)  
- 公＋民 / FinPriv membership  
- COOL retune · DH re-enable · Stage A live wire  
- Broker live-write · Gate H auto-fuse  
- Retune exhausted Stage B always-on FIN hi∈[0.80,0.85] grid after peek

## Base

| ID | Construction |
|---|---|
| `BASE_LIVE_FUSE_COOL` | Live Soft-Frozen clips + Soft `SELL_a05` + Sleeve RSI14 α=0.225 + COOL_c8 |

## Stage A grid (finite — do not expand after peek)

TEL live frozen. Soft/Sleeve/COOL frozen. Live clips = rest-regime default unless `DEF_REST`.

| Track | Gate | Bull densify | Rest |
|---|---|---|---|
| `BULL_E_HI` | Bull | F live · E hi ∈ `{0.55,0.60,0.65}` | live |
| `BULL_FIN_ROOM` | Bull | F hi ∈ `{0.75,0.78}` · E hi ∈ `{0.55,0.60,0.65}` | live |
| `BULL_SIDE_FIN_ROOM` | Bull+Sideways | same as `BULL_FIN_ROOM` | live |
| `BULL_OFF_DEF_REST` | Bull | F hi ∈ `{0.75,0.78}` · E hi ∈ `{0.55,0.60}` | prior FINBAND F[0.60,0.90] E[0.00,0.35] |

Script: `scripts/asymm_0050_bull_densify_under_cool_stagea.py`  
Repro: `repro/asymm-0050-bull-densify-under-cool-stagea/`

## Verdicts

| Verdict | Meaning |
|---|---|
| `ASYMM_MDD_FLAT_HIT` | ≥1 book clears all four gates |
| `HELD_FLAT_TIP_FAIL` | held MDD flat + CAGR OK; tip fails |
| `CAGR_SOFT` | MDD flat + tip OK; CAGR short of +0.20 |
| `NO_FLAT_LIFT` | no book with MDD↑≥0 and CAGR≥+0.20 in band |

Even HIT → **paper observe ballot only**; Soft-Frozen flip = separate Class D ACCEPT.

## Label

`ASYMM_0050_BULL_DENSIFY_UNDER_COOL_STAGEA_CHARTER_2026-09-25__OPEN__NO_LIVE_WIRE`
