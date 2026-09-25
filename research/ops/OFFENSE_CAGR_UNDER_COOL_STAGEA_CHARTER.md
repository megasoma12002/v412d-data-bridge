# Offense CAGR under live COOL — Paper Charter (Stage A)

Date: 2026-09-25  
Status: **PAPER CHARTER OPEN** · Stage A **DONE** · verdict **`OFFENSE_CAGR_SOFT`**  
Parent live: `LIVE_COOL_C8_CUTOVER_BALLOT_EXECUTED_ACCEPT` · defense **`COOL_c8_f50_d21` KEEP**  
Soft-Frozen tip / FIN clip **[0.60, 0.90]**: **KEEP** · no tip history rewrite · no live wire from this charter

Label: `OFFENSE_CAGR_UNDER_COOL_STAGEA_CHARTER_2026-09-25__PAPER_OPEN__NO_LIVE_WIRE`

## Why

Live (merge #281): **FUSE_ADDITIVE + COOL_c8** held ≈ **15.07% / −14.62%**.  
Defense is in band; vs same-window `FUSE_ONLY` (~16.33% / −24%) the COOL tax is ~**+1.3 pp** CAGR giveback.  
Human selected: improve **offense** (FUSE / Soft / Sleeve micro) **without** touching Soft-Frozen tip clip.

## Question

On Stage-E DEFAULT + frozen **`COOL_c8_f50_d21`** defense, does any **finite** Soft / Sleeve / FUSE micro-tune:

1. lift held-out CAGR vs live base `FUSE_COOL` by **≥ +0.20 pp**,  
2. keep held |MDD| **≤ 15%** (ACCEPT band floor),  
3. clear tip YTD + trailing 1y `mdd_improve_pp >= 0` vs `FUSE_COOL`?

## Non-actions

- Soft-Frozen clip / tip ledger rewrite  
- COOL / PROXY densify (separate lever)  
- Re-enable DH or stack DH+COOL  
- Broker live-write · Soft∥Sleeve ops auto-fuse (Gate H KEEP)  
- Live wire from Stage A (needs dedicated ACCEPT)

## Base / controls

| ID | Construction |
|---|---|
| `BASE_FUSE_COOL` | Live twin: Soft `…__SELL_a05` + Sleeve RSI14 α=0.225 + **COOL_c8** |
| `CTRL_FUSE_ONLY` | Same Soft+Sleeve, **no** COOL (offense ceiling) |
| `CTRL_STACK_COOL` | KD_OPT stack + COOL (no Soft/Sleeve) |

## Stage A tracks (finite)

| Track | Idea | Freeze |
|---|---|---|
| `SLEEVE_ALPHA` | Same Soft + COOL; Sleeve RSI14 α ∈ {0.15, 0.20, **0.225**, 0.25, 0.30} | α only |
| `SOFT_SELL_AMP` | Same Sleeve α=0.225 + COOL; sell soft amp ∈ {0.25, **0.50**, 0.75, 1.00} | sell boost |
| `SOFT_BUY_AMP` | Same sell a05 + Sleeve + COOL; K9 buy amp ∈ {0.08, **0.10**, 0.12, 0.15} | buy amp |
| `FUSE_SHAPE` | Under COOL: Soft-only · Sleeve-only · FUSE_HALF(α=0.1125) · BASE | construction |

Script: `scripts/offense_cagr_under_cool_stagea_screen.py`  
Repro: `repro/offense-cagr-under-cool-stagea/`

## Verdicts

| Verdict | Meaning |
|---|---|
| `OFFENSE_CAGR_HIT` | ≥1 book: held CAGR ≥ base+0.20pp · \|MDD\|≤15% · tip MDD OK |
| `OFFENSE_CAGR_SOFT` | CAGR lift ≥0.20pp · \|MDD\|≤15% · tip fail |
| `MDD_TRADEOFF` | CAGR lift but \|MDD\|>15% |
| `NO_LIFT` | no book beats base CAGR by 0.20pp in band |

Even HIT → **paper observe ballot only**; never live swap Soft/Sleeve/FUSE from Stage A.

## Artifacts

- EN: `research/ops/OFFENSE_CAGR_UNDER_COOL_STAGEA_CHARTER.md`  
- ZH: `research/ops/OFFENSE_CAGR_UNDER_COOL_STAGEA_CHARTER.zh-TW.md`  
- Screen: `research/ops/OFFENSE_CAGR_UNDER_COOL_STAGEA_SCREEN.md`

## Stage A result (2026-09-25)

Verdict: **`OFFENSE_CAGR_SOFT`** — no joint clear of ≥+0.20pp CAGR + |MDD|≤15% + tip OK.

| note | detail |
|---|---|
| Best tip-OK in-band micro | `SELL_a75` held lift **+0.17pp** (short of +0.20) · MDD −14.66% |
| Near | `SLEEVE_a0250` +0.08pp · tip OK |
| Control | `CTRL_STACK_COOL` +0.23pp in band but **tip fail** (not Soft/Sleeve lift) |
| Ceiling | `CTRL_FUSE_ONLY` +1.26pp but MDD −24% out of band |

Implication: finite Soft/Sleeve/FUSE amplitude densify under frozen COOL does **not** recover the ~1.3pp COOL tax at tip-clean ≥+0.20pp. Next levers (new ballot): loosen COOL, or new offense mechanism (not same-knob densify).

## Label

`OFFENSE_CAGR_UNDER_COOL_STAGEA_CHARTER_2026-09-25__OFFENSE_CAGR_SOFT__NO_LIVE_WIRE`
