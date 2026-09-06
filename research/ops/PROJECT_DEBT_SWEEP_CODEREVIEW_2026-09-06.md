# Project Debt-Sweep Code Review — 2026-09-06

Status: **REVIEW + REMEDIATION**  
Soft-Frozen **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · E45 stitch **FORBIDDEN** · retired MDD narrative **`RETIRED_HISTORICAL_NARRATIVE`** (do not invent a replacement)

Label: `PROJECT_DEBT_SWEEP_CODEREVIEW_2026-09-06__STITCH_FORBIDDEN`

Baseline: `main` after #87–#91 (naming High/Medium + observe/Phase C ops).

---

## Verdict

Prior naming/hygiene PRs cleared the **classic High emitters**. This sweep closes the **ban gaps** those gates did not catch, repairs **ops/status contradictions**, and registers residual Low debt.

| Bucket | Found | This PR |
|---|---|---|
| High (join / metric / clip / observe id) | 8 families | **Fixed + hygiene widened** |
| Medium (boards / ballots / Soft-Frozen JSON keys / DIAGNOSTICS identity) | 7+ | **Fixed** |
| Low / intentional keep | regenerator overlap, v412 dtype, cosmetic CSV names, review-doc historical bans | **Documented only** |

No Soft-Frozen / DEFAULT / stitch ballot is implied.

---

## Fixed in this PR

### Scripts — High/Medium

1. **JSON claim key** `claimed_mdd_status` → `claim_status` in OPERATING/paper emitters.
2. **`_abs_or(..., 9.0)`** month-end monitors → `abs_mdd` / `mdd_delta_pp` from `research_metric_helpers`.
3. **Soft-Frozen hardcodes** → import `SOFT_FROZEN_FIN_CLIP` / LO/HI (papers + blend025 dual ledgers + go-live expected pin).
4. **Observe lock prose** `FIN_ONLY_A10` → `SLEEVE_FIN_ONLY_A10` (covid densify report).
5. **Dashboard** `operating_observe_sleeves` includes A05 + `SLEEVE_FIN_ONLY_A10`.
6. **Month-end / dashboard windows** sealed/heldout starts from `WINDOWS_STANDARD`.
7. **`mdd_help_*` keys** → `mdd_improve_*` in five-batch / covid / crisis-year emitters.
8. **Hygiene bans extended**: `claimed_mdd_status`, `_abs_or(...,9.0)`, Soft-Frozen KEEP string, `mdd_help_*` variants, observe-lock prose.

### Non-script

- Soft-Frozen JSON key `soft_frozen_clip` → `soft_frozen_fin_clip` in ops/gap packs.
- HIGH_BETA ballot locked-book id corrected (observe ≠ paper densify).
- Roadmap / STAGE12 / observe-status / P1–P7 / five-batch: `CONST_/REF_BLEND_/ALL_A05` → `BLEND_E45_A05`; sleeve-local OPERATING contradictions fixed.
- `E45_OBSERVE_PAUSE_DIAGNOSTICS.md` restored as **alias stub** pointing at REFRESH (identity collision fixed).
- `STRATEGY_DEBT_BOARD.md` snapshot updated.

---

## Residual register (do not blind-rewrite)

| Item | Why keep / defer |
|---|---|
| Paper densify book `FIN_ONLY_A10` | Different ID from observe `SLEEVE_FIN_ONLY_A10` |
| `sealed_2023_latest` **read** fallback in monitors | Intentional dual-read |
| `CLAIMED_MDD_STATUS_LEGACY` / claim_labels vocabulary | Not claim-status emitters |
| Overlapping regenerators (five-batch vs covid thicken vs next-batch) | Documented ownership — `E45_REGENERATOR_OWNERSHIP_2026-09-06.md` (no merge) |
| Cosmetic CSV filenames still containing `mdd_help` | **Closed** in eng-debt-cleanup → `mdd_improve*` |
| v412* market `read_csv` without dtype=str | **Closed** in eng-debt-cleanup (`dtype={"code": str}`) |
| Review docs mentioning banned labels | Historical findings — leave |
| FIN_CAP_50 challenger clip `[0.35,0.50]` literals | Challenger design, not Soft-Frozen |
| HIGH_BETA observe | Still **DRAFT / NOT OPEN** |

---

## Ban-gap map (before → after)

| Pattern | Before #87–#91 | After this PR |
|---|---|---|
| `E45_PROFILE=` / bare `BLEND_A##` / `mdd_help_pp` / sealed writers | Banned | Still banned |
| `claimed_mdd_status` JSON | **Gap** | **Banned** |
| `_abs_or(..., 9.0)` | **Gap** | **Banned** |
| Soft-Frozen KEEP `[0.50,0.95]` string | **Gap** | **Banned** |
| `mdd_help_2020_pp` etc. | **Gap** | **Banned** |
| Observe lock prose `FIN_ONLY_A10` | **Gap** | **Banned** |

---

## Non-actions

- No Soft-Frozen / DEFAULT flip
- No live stitch / no HIGH_BETA OPEN
- No retired-narrative reinvention
- No e21 primary rewrite / no Goodinfo·Wantgoo·CMoney reopen

## Verify

```bash
PYTHONPATH=scripts python3 scripts/check_project_coding_hygiene.py
```
