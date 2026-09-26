# TEL within-sleeve — 名目高低／結構／防守聯動 — Paper Charter (Stage A)

Date: 2026-09-26  
Status: **Stage A `TEL_WITHIN_SOFT`** · Soft-Frozen live **KEEP** · live wire **false**  
Human: **三軌都做**（TEL within-sleeve Stage A）

Priors (do not reopen as this charter):

| Prior | Verdict |
|---|---|
| TEL async / `PRE_EXDIV_KD` (FIN-parallel) | **STOP** |
| Telecom pack cutover | **KEEP `TEL_EQUAL`** |
| Within-sleeve COOL micro (old TEL pack cells) | **`NO_FLAT_LIFT`** |

Class: **A. Research / EXPERIMENTAL** · no Soft-Frozen flip · no tip rewrite · no live wire from Stage A  

Live twin baseline (offense path, no `00631L` satellite in this paper twin — CONF_RET3 orthogonal KEEP):  
Soft-Frozen clips + Soft+Sleeve + **`SELL_a75`** + `FUSE_ADDITIVE` + **`COOL_c8`** + FIN **`KD_OPT`** + TEL base **`TEL_EQUAL`**

Label: `TEL_WITHIN_SLEEVE_STAGEA_CHARTER_2026-09-26__OPEN`

**Passing ≠ live · ≠ `TEL_EQUAL` flip · ≠ reopen STOP KD grid.**

---

## Question

Vs `BASE_LIVE_FUSE_COOL` (`TEL_EQUAL`): does any **new** TEL within-sleeve mechanism clear held CAGR≥**+0.20pp** and MDD/tip gates?

## Tracks (finite · FIN stays `KD_OPT`)

Challengers use `TEL_RS_SOFT_TILT` with **custom `tel_name_scores`** (not seasonal KD).

### T1 — 名目高低／技術（≠ KD season）

| id | Score |
|---|---|
| `T1_DIST60` | Soft-tilt by distance below 60d high |
| `T1_RSI14_INV` | Soft-tilt by inverted RSI14 |
| `T1_BELOW_MA60` | Soft-tilt boost when close &lt; MA60 |
| `T1_DIST60_RSI` | 0.5·DIST60 + 0.5·RSI14_INV |

### T2 — 結構／流動性（≠ 舊 pack lot 劇本）

| id | Score |
|---|---|
| `T2_INV_VOL20` | Soft-tilt inverse 20d return vol |
| `T2_ADV20` | Soft-tilt relative 20d ADV |
| `T2_INV_BETA0050` | Soft-tilt inverse \|β\| vs 0050 (60d) |
| `T2_ADV_INVVOL` | 0.5·ADV20 + 0.5·INV_VOL20 |

### T3 — 防守聯動（只在 COOL 窗改權重）

Same score families, but **when `cool_exposure=1` force equal scores** (TEL behaves EQUAL off-defense):

| id | Active score when defending |
|---|---|
| `T3_COOL_DIST60` | DIST60 |
| `T3_COOL_RSI14` | RSI14_INV |
| `T3_COOL_INV_VOL20` | INV_VOL20 |
| `T3_COOL_ADV20` | ADV20 |

### Controls

- `BASE_LIVE_FUSE_COOL` — `TEL_EQUAL`

Total challengers: **12** (+ base).

## Gates / verdicts

| Gate | Rule |
|---|---|
| tip_clean / tip_mdd_ok | YTD+1y PASS · MDD↑ ≥ −0.5pp |
| held_mdd / sealed_mdd | ≥ −0.25pp / ≥ 0 |
| cagr_floor | held CAGR↑ ≥ +0.20pp |

| Verdict | Meaning |
|---|---|
| `TEL_WITHIN_HIT` | ≥1 book clears all |
| `TEL_WITHIN_SOFT` | MDD/tip OK · CAGR short |
| `MDD_BLOCK` | tip OK · MDD fail |
| `NO_LIFT` | no tip-clean offense |

Even HIT → paper observe only.

## Out of scope

- Soft-Frozen clip / tip rewrite / broker  
- Reopen `TEL_PRE_EXDIV_KD` summer grid / async STOP path  
- Promote old `TEL_DIVERSIFY_PACK` without new evidence  
- Retune COOL / FUSE / SELL_a75 / live `00631L`  

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/tel_within_sleeve_stagea.py
```

Artifacts: `research/ops/TEL_WITHIN_SLEEVE_*` · `repro/tel-within-sleeve-stagea/`

## Label

`TEL_WITHIN_SLEEVE_STAGEA_CHARTER_2026-09-26__OPEN`
