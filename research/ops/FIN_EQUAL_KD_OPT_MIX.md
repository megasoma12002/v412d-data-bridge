# FIN EQUAL × KD_OPT λ-mix — coexistence probe

Generated: `2026-09-09T03:09:17.995465+00:00`
Soft-Frozen **KEEP** · live wire **false**
Status: **COEXIST_CANDIDATE_FOUND**

Definition: `λ·FIN_EQUAL + (1−λ)·FIN_PRE_EXDIV_KD` (`KD_APR15_MAY15_Klt30_T15`)
Coexist rule: held-out score > 0 **and** tip YTD+1y both PASS (giveback ≤ 3pp)

## Grid vs `FIN_EQUAL`

| id | λ(EQUAL) | heldout score | MDD↑pp | CAGR giveback | YTD gate | 1y gate | coexist? |
|---|---:|---:|---:|---:|---|---|---|
| `FIN_EQUAL` | 1.00 | — | — | — | PASS | PASS | — |
| `KD_OPT` | 0.00 | 0.647 | 0.807 | 0.319 | PASS | PASS | True |
| `KD_MIX_L25` | 0.25 | 0.453 | 0.610 | 0.315 | PASS | PASS | True |
| `KD_MIX_L50` | 0.50 | 0.280 | 0.409 | 0.259 | PASS | PASS | True |
| `KD_MIX_L75` | 0.75 | 0.153 | 0.204 | 0.102 | PASS | PASS | True |

## Verdict

Coexist candidate `KD_OPT` (λ=0.00): held-out +0.647 and tip YTD/1y PASS. Soft-Frozen KEEP · no live wire.

**Reading:** EQUAL×KD λ-grid **interpolates** — all mid-λ tip PASS + held>0, but **none beat pure `KD_OPT` on held-out**. Mixing EQUAL only softens KD (smaller MDD lift, smaller tip giveback at high λ). Does **not** create a new Pareto winner vs pure KD_OPT.

Compare: `MIX_L75` (EQUAL×RS) held ~+0.13 tip PASS; `KD_MIX_L75` held ~+0.15 tip PASS — similar “soft” mix tier; pure KD still dominates held-out among tip-clean books.

## Hard rules

- Soft-Frozen KEEP · no live wire · no cutover from this probe
- Does not stack MIX_L75×KD (EQUAL×KD only)
- Dual-paper OPERATING observe unchanged until dedicated ballot

Repro: `repro/fin-equal-kd-mix-20260909/`

```bash
python3 scripts/e16_fin_equal_kd_mix_paper.py
```
