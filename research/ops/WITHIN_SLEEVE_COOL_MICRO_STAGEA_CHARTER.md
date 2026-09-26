# Within-sleeve FinPub/TEL micro under Soft+Sleeve+COOL — Paper Charter (Stage A)

Date: 2026-09-25  
Status: **CLOSED — `NO_FLAT_LIFT`** · Soft-Frozen tip **KEEP** · live wire **false**  
Parent live: Soft-Frozen **F[0.60,0.80] T[0.03,0.35] E[0.00,0.50]** + Soft sell + Sleeve RSI14 α=0.225 + `COOL_c8_f50_d21` + FUSE  
Live within-sleeve: FIN=`KD_OPT` (Apr15–May15 K\<30 T−15) · TEL=`TEL_EQUAL`  
Research order: after β densify LIVE clip (#284) — **micro within-sleeve** only (no clip rewrite · no 公+民)

Label: `WITHIN_SLEEVE_COOL_MICRO_STAGEA_CHARTER_2026-09-25__NO_FLAT_LIFT__NO_LIVE_WIRE`

## Philosophy

Soft-Frozen **clips** and **COOL** stay frozen. This charter asks whether a **finite** micro-retune of **within-sleeve** FinPub KD season params and/or Telecom alloc can lift held CAGR tip-clean under the live Soft+Sleeve+COOL stack — without touching tip membership.

## Question

On Stage-E DEFAULT + live Soft+Sleeve+**COOL_c8** with Soft-Frozen clips KEEP, does any finite within-sleeve micro challenger vs `BASE_LIVE_FUSE_COOL`:

1. lift held-out CAGR by **≥ +0.20 pp**,  
2. keep held MDD↑ **≥ 0** (flat or better vs base),  
3. clear tip YTD + 1y MDD↑ ≥ 0,  
4. keep held |MDD| **≤ 15%**?

## Non-actions

- Soft-Frozen live clip / tip rewrite (KEEP F[0.60,0.80] T[0.03,0.35] E[0.00,0.50])  
- Live tip membership / Soft-Frozen clip edits  
- 公＋民 dollar-split / FinPriv expand  
- COOL retune · DH re-enable · stack DH+COOL  
- Broker live-write · Gate H auto-fuse  
- Stage A live wire (even HIT → paper observe ballot only)

## Base

| ID | Construction |
|---|---|
| `BASE_LIVE_FUSE_COOL` | Soft `SELL_a05` + Sleeve RSI14 α=0.225 + Soft-Frozen clips **F[0.60,0.80] T[0.03,0.35] E[0.00,0.50]** + live FIN `KD_OPT` + TEL `EQUAL` + COOL_c8 from fuse offense |

Same Soft/Sleeve/COOL stack pattern as `scripts/beta_0050_densify_under_cool_stagea.py`; clips frozen at Soft-Frozen live (post β densify ACCEPT).

## Stage A grid (finite — locked after peek)

≤24 books · Soft/Sleeve/COOL/clips **frozen**. Vary only within-sleeve FIN KD season **or** TEL alloc.  
Helpers: `build_kd_season_tilt_scores` + `build_pre_exdiv_window_buy_ok`.

### Track `FIN_KD_MICRO` (TEL stays `TEL_EQUAL`) — 10 books

Exclude exact live `KD_OPT` (Apr15–May15 · K30 · T15):

| id | season | K | T− |
|---|---|---:|---:|
| `FIN_KD_A15M15_K25_T10` | Apr15–May15 | 25 | 10 |
| `FIN_KD_A15M15_K25_T15` | Apr15–May15 | 25 | 15 |
| `FIN_KD_A15M15_K25_T20` | Apr15–May15 | 25 | 20 |
| `FIN_KD_A15M15_K35_T10` | Apr15–May15 | 35 | 10 |
| `FIN_KD_A15M15_K35_T15` | Apr15–May15 | 35 | 15 |
| `FIN_KD_A15M15_K35_T20` | Apr15–May15 | 35 | 20 |
| `FIN_KD_MAY_K25_T15` | May1–May31 | 25 | 15 |
| `FIN_KD_MAY_K30_T15` | May1–May31 | 30 | 15 |
| `FIN_KD_A01M15_K30_T10` | Apr1–May15 | 30 | 10 |
| `FIN_KD_A01M15_K30_T15` | Apr1–May15 | 30 | 15 |

### Track `TEL_MICRO` (FIN stays live `KD_OPT`) — 3 books

Skip `TEL_EQUAL` control:

| id | telecom_alloc |
|---|---|
| `TEL_RS_SOFT_TILT` | `TEL_RS_SOFT_TILT` |
| `TEL_MIN_LOT_PACK` | `TEL_MIN_LOT_PACK` |
| `TEL_EXDIV_SKIP_BUY` | `TEL_EXDIV_SKIP_BUY` |

Total: **13** books (10 FIN + 3 TEL) ≤ 24.

Script: `scripts/within_sleeve_cool_micro_stagea.py`  
Repro: `repro/within-sleeve-cool-micro-stagea/`

## Verdicts

| Verdict | Meaning |
|---|---|
| `WITHIN_SLEEVE_MICRO_HIT` | ≥1 book: CAGR≥+0.20pp · held MDD↑≥0 · tip OK · \|MDD\|≤15% |
| `CAGR_SOFT` | MDD-flat + tip OK + band + CAGR lift >0 but \<+0.20pp |
| `HELD_FLAT_TIP_FAIL` | held MDD flat + CAGR≥+0.20 in band; tip MDD fails |
| `NO_FLAT_LIFT` | no book with MDD↑≥0 and CAGR≥+0.20 in band |

## Stage A result (2026-09-25)

Verdict: **`NO_FLAT_LIFT`** (0/13 HIT · 0 held-flat tip-fail · 0 CAGR soft).

| Best (by CAGR lift) | held CAGR lift | held MDD↑ | band | tip |
|---|---:|---:|:---:|:---:|
| `FIN_KD_A15M15_K35_T10` | **+0.14pp** | −0.50pp | N | N |

Nearest tip-clean band: `TEL_MIN_LOT_PACK` **+0.06pp** CAGR · MDD↑ **−0.06pp**.  
No joint MDD-flat + ≥+0.20pp under predeclared micro grid. Soft-Frozen / live KD_OPT / TEL_EQUAL **KEEP**.

## Artifacts

- EN/ZH charter · screen · decision pack  
- Order note: `research/ops/RESEARCH_ORDER_BETA_DEFENSE.md`  
- Register: `research/ops/HUMAN_DECISION_REGISTER.md`  
- Run log: `/opt/cursor/artifacts/within_sleeve_cool_micro_stagea_run.log`

## Label

`WITHIN_SLEEVE_COOL_MICRO_STAGEA_CHARTER_2026-09-25__NO_FLAT_LIFT__NO_LIVE_WIRE`
