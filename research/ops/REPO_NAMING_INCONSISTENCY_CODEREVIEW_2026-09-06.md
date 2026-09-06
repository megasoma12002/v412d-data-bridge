# Repo Naming Inconsistency — Code Review (2026-09-06)

Status: **REVIEW ONLY** — Soft-Frozen **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · E45 stitch **FORBIDDEN** · claimed −13.16% **`RETIRED_HISTORICAL_NARRATIVE`** (do not invent a replacement)

**Baseline:** `main` @ review time  
**Related open fix:** [PR #87](https://github.com/megasoma12002/v412d-data-bridge/pull/87) (`cursor/e45-naming-consistency-d049`) — clears primary E45 *script emitter* forks in §A  
**Canon source:** `scripts/e45_paper_harness.py`, `scripts/e16_soft_frozen_base.py`, `scripts/claim_labels.py`

Label: `REPO_NAMING_CODEREVIEW_2026-09-06__STITCH_FORBIDDEN`

---

## Verdict

Across `scripts/` (~122 py), `research/`, and `repro/`, there are **~16 dual-name concept families**.

| Bucket | Count | Action |
|---|---|---|
| High — runtime / operator join risk | **5** | Fix emitters + regenerate decision / ballot packs |
| Medium — hygiene dual emit / prose drift | **7** | Fix or regenerate |
| Low / intentional keep | **4+** | Document; do not blind-rewrite |

On **`main` today:** profile / MDD-key / sealed-window writers / observe-sleeve prose / claim-value packs are still forked.  
**PR #87** clears those script emitters and adds hygiene bans.  
**After #87:** residual risk is mostly **stale research/repro teaching old schema**, plus hygiene duals (claim JSON keys, local `WINDOWS=`, Soft-Frozen aliases, verify book IDs).

No Soft-Frozen / DEFAULT / stitch ballot is implied by this review.

---

## Canon table

| Concept | Canonical | Banned / fork |
|---|---|---|
| Claim const (paper) | `CLAIM_STATUS` ← harness | local paper `CLAIMED_MDD_STATUS = …` |
| Claim source attr | `e45.CLAIMED_MDD_STATUS` | (ownership — keep in `e45_crisis_core.py`) |
| Claim value | `RETIRED_HISTORICAL_NARRATIVE` | emitting `NOT_VERIFIED` as *claim status* |
| Profile const | `E45_PROFILE_DEFAULT` | local `E45_PROFILE = "E3_VOLTARGET_WINNER"` |
| MDD delta key | `mdd_improve_pp` | `mdd_help_pp` |
| Sealed window key | `sealed_2023_plus` | `sealed_2023_latest` (**writers**) |
| Observe FIN sleeve | `SLEEVE_FIN_ONLY_A10` | calling *observe* `FIN_ONLY_A10` |
| Paper FIN densify | `FIN_ONLY_A10` | (keep — different ID) |
| E45 windows map | `WINDOWS_STANDARD` | silent local `WINDOWS = {…}` copies |
| Book base / full / blend | `BOOK_BASE`=`BASE_E16_E18_E22_v2s` · `BOOK_FULL`=`CHAL_E45_E3` · `BLEND_E45_A##` | bare `BLEND_A##`, `FULL_E45`, verify ids without `BASE_`/`CHAL_` |
| Soft-Frozen clip | `SOFT_FROZEN_FIN_CLIP` | local `SOFT_FROZEN_CLIP` / mixed JSON keys |
| OOF (E45) | `oof_2011_2018` | do **not** rewrite MDD-L1 `oof_2012_2018` |
| Validation window | `validation_2019_2022` | `val_2019_2022` |

---

## A. High findings (live on `main`)

### A1. Local `E45_PROFILE =` fork

**Why High:** Paper regenerators redefine the frozen profile string beside harness `E45_PROFILE_DEFAULT` — future retune/rename drifts silently.

**Evidence:** `scripts/e45_dual_paper_ledgers.py`, `e45_blend005_dual_paper_ledgers.py`, `e45_blend025_dual_paper_ledgers.py`, `e45_blend_alpha_paper_screen.py`, `e45_blend_alpha_grid_fine.py`, `e45_crisis_triggered_alpha_paper.py`, `e45_crisis_year_attribution_paper.py`, `e45_alpha_cost_turnover_paper.py`, `e45_low_alpha_deep_dive_paper.py`, `e45_sleeve_local_paper.py`, …

**Fix:** Import/use `E45_PROFILE_DEFAULT` only.  
**PR #87:** Cleared in emitters + hygiene ban on `^E45_PROFILE\s*=`.

### A2. `mdd_help_pp` vs `mdd_improve_pp`

**Why High:** Harness / dual-paper delta keys use `mdd_improve_pp`; five-research batch still emits `mdd_help_pp` on `main` → cross-pack joins break.

**Evidence:** `scripts/e45_five_research_batch.py` (emit + markdown cells).  
Filename `crisis_year_mdd_help_vs_base.csv` is cosmetic only.

**Fix:** Emit/read `mdd_improve_pp`.  
**PR #87:** Cleared emitters + CSV column.

### A3. `sealed_2023_latest` writers vs `sealed_2023_plus`

**Why High:** Decision consumers keyed on `sealed_2023_plus` miss rows still written as `sealed_2023_latest`.

**Evidence (`main` writers, ~8 scripts):**  
`scripts/mdd_l1_loss_engine_heldout.py`, `mdd_l2_loss_engine_heldout.py`, `mdd_l3_loss_engine_heldout.py`,  
`e50a3r1_stage8b_s8b1_heldout.py`, `e50a3r1_stage8c_s8c1_heldout.py`, `e50a3r1_stage9a_s9a1_heldout.py`,  
`gap56_continuation_research.py`, `e50a_dual_track_s9a1_monitor.py`.

**Stale artifacts (~18+ files), including:**  
`research/gaps/MDD_L1_HELDOUT_DECISION.json`,  
`research/gaps/MDD_L2_HELDOUT_DECISION.json`,  
`research/gaps/MDD_L3_HELDOUT_DECISION.json`,  
`research/e50a/E50A_S1_HELDOUT_DECISION.json`,  
`research/gaps/GAP5_6_CONTINUATION.json`,  
`research/e50a/TRACK_A_S9A1_MONITOR_STATUS.md`,  
mirrors under `repro/`.

**Fix:** Writers → `sealed_2023_plus`; monitor may keep `plus or latest` **read** fallback; regenerate research decision packs.  
**PR #87:** Writers + dual-read fallback; **checked-in artifacts stay stale until regenerate**.

### A4. Observe sleeve called `FIN_ONLY_A10`

**Why High:** Operator ballots can lock/displace the wrong book. Observe OPERATING id is `SLEEVE_FIN_ONLY_A10`; paper densify remains `FIN_ONLY_A10`.

**Evidence:**  
- `scripts/e45_five_research_batch.py` — still emits observe prose with `FIN_ONLY_A10` (mixed with one `SLEEVE_FIN_ONLY_A10` book field)  
- `research/ops/E45_HIGH_BETA_SLEEVE_LOCAL_PAPER.md` — “FIN_ONLY_A10 observe stays OPERATING”  
- `research/ops/E45_HIGH_BETA_OBSERVE_OPEN_BALLOT_DRAFT.md` (+ `.zh-TW.md`)  
- `research/ops/E45_FIVE_RESEARCH_BATCH_INTEGRATED.md` + `research/e45/` / `repro/` mirrors

**Fix:** Re-publish five-batch / HIGH_BETA docs from fixed generator; ballot text must say `SLEEVE_FIN_ONLY_A10` for observe.  
**PR #87:** Script prose partially fixed; **published MD still wrong until regenerate**.

### A5. Claim status still taught as `NOT_VERIFIED`

**Why High:** Active packs present `NOT_VERIFIED` as the −13.16% *claim status*, contradicting `RETIRED_HISTORICAL_NARRATIVE`.

**Evidence:**  
- `research/ops/E45_V4_COST_STRESS_PACK.md`, `E45_V5_MULTI_WINDOW_PACK.md`  
- `repro/e45-v4v5-named-packs/summary.json`, `repro/e45-dual-paper-observe-design/summary.json`, `repro/e45-mdd-verify/summary.json`  
- Register / debt / gap briefs still say claim “remains NOT_VERIFIED” in places

**Note:** A verification *scan* may still report “no artifact matched −13.16%”. That is not the same as the claim-status const. Prefer: scan unmatched + policy `RETIRED_HISTORICAL_NARRATIVE`.

**Fix:** Regenerate V4/V5/stage3/verify summaries; patch operator briefs.

---

## B. Medium findings

### B1. Claim JSON key triple

Same concept emitted as `claimed_mdd_status` | `claim_mdd_status` | `claim_status` (~17 script files; more in artifacts).

**Prefer:** `claimed_mdd_status` for new emitters; dual-read old keys.

### B2. Local `WINDOWS =` copies (~15 scripts)

E45 paper scripts often import harness but still define local `WINDOWS` (sometimes string dates vs harness `date` — e.g. `e45_stage3_dual_paper_windows.py`). Drift risk if `WINDOWS_STANDARD` bounds change.

**Prefer:** use `WINDOWS_STANDARD` (or an explicit documented subset alias).

### B3. Soft-Frozen const / JSON aliases

- Const: `SOFT_FROZEN_CLIP` in `ops_alert_scan.py`, `ops_month_end_paper_pack.py`, `e21_live_vs_paper_recon.py` vs canon `SOFT_FROZEN_FIN_CLIP`
- JSON: `soft_frozen_keep` | `soft_frozen_clip` | `soft_frozen_live_clip`

**Prefer:** import `SOFT_FROZEN_FIN_CLIP`; one JSON key (suggest `soft_frozen_fin_clip`).

### B4. `claim_labels.normalize_claim_label` → `NOT_VERIFIED_HISTORICAL_NARRATIVE`

Canon retirement label is `RETIRED_HISTORICAL_NARRATIVE`. Normalizer still returns the `NOT_VERIFIED_*` sibling for deprecated aliases — landmine if callers adopt normalize for E45 claim.

**Prefer:** normalize deprecated aliases → `RETIRED_HISTORICAL_NARRATIVE` (or map both + document).

### B5. Roadmap book-ID prose: `CONST_A05` / `ALL_A05`

Still taught in `E45_PAPER_RESEARCH_ROADMAP.md`, `E45_PAPER_P1_P7_INTEGRATED_ANALYSIS.md`, `E45_STAGE12_STATUS.md` while harness emitters use `BLEND_E45_A05`.

**Prefer:** update operator roadmaps; leave landmine-review docs that describe the bug as historical.

### B6. `val_2019_2022` vs `validation_2019_2022`

`scripts/mdd_l1_sealed_attribution.py` emits `val_2019_2022` (+ research/repro mirrors) while E45 `WINDOWS_STANDARD` uses `validation_2019_2022`.

**Prefer:** `validation_2019_2022` (or document MDD-L1 ownership if intentional).

### B7. Function forks outside E45 paper harness

`load_market` / `window_stats` copies in e16 / fincap / MDD scripts; local `blend_const` in `e45_crisis_triggered_alpha_paper.py` vs harness `blend_exposure`.

E45 paper regenerators are (after #87) hygiene-gated; non-E45 copies remain Medium hygiene.

---

## C. High residual beyond PR #87 script scope

### C1. `e45_verify_mdd_1316.py` book IDs

Emits `E16_E18_E22_v2s` / `E16_E18_E22_v2s_E45_E3` instead of harness `BASE_E16_E18_E22_v2s` / `CHAL_E45_E3`.

**Severity:** High for cross-pack joins against dual-paper ledgers.  
**Not fixed by PR #87.**

### C2. Hardcoded `"E3_VOLTARGET_WINNER"` in non-harness scripts

Runtime-equal today; hygiene Medium once profile const is the only write path.

### C3. `BASE_ID = "BASE_…"` hardcode while importing `BOOK_BASE`

`e45_dual_paper_ledgers.py`, `e45_blend005_dual_paper_ledgers.py`, `e45_blend025_dual_paper_ledgers.py` still hardcode the string beside harness import. Prefer `BASE_ID = BOOK_BASE` (sleeve-local already does).

---

## D. Intentional keep (do not “fix”)

| Dual | Why keep |
|---|---|
| `CLAIM_STATUS` ↔ `e45.CLAIMED_MDD_STATUS` | Harness alias vs crisis_core source attr |
| `SLEEVE_FIN_ONLY_A10` ↔ `FIN_ONLY_A10` | Observe sleeve vs paper densify — **different IDs** |
| `oof_2011_2018` ↔ `oof_2012_2018` | E45 `WINDOWS_STANDARD` vs MDD-L1 window ownership |
| `sealed_2023_latest` **read** fallback | Compat for pre-rename decision JSON |
| `BLEND_025` (E16 fin-cap) ↔ `BLEND_E45_A25` | Different products |
| E22 version matrix (`E22_v2` / `v2s` / `v2s_tw` / `cil`) | Intentional research versions; do not infer from `BOOK_BASE` ledger id |
| Filename `crisis_year_mdd_help_vs_base.csv` | Cosmetic “help”; column should be `mdd_improve_pp` |

---

## E. Scorecard

### On `main` (pre-#87)

| Family | Scripts | Research/repro | Severity |
|---|---|---|---|
| `E45_PROFILE =` | live (~11) | n/a | High |
| `mdd_help_pp` | live (five-batch) | mostly cleared column-wise | High |
| `sealed_2023_latest` writers | live (~8) | decision JSON still keyed latest (~18) | High |
| Observe=`FIN_ONLY_A10` prose | live (five-batch) | live HIGH_BETA / five-batch MD | High |
| Claim=`NOT_VERIFIED` | mixed | V4/V5 + stale repro | High |
| Claim JSON key triple | live | live | Medium |
| Local `WINDOWS=` | ~15 | n/a | Medium |
| Soft-Frozen aliases | 3 ops scripts | mixed JSON keys | Medium |
| Roadmap `CONST_A05`/`ALL_A05` | — | 3 ops MDs | Medium |
| Verify book IDs | live | mirrors | High |
| Intentional duals (§D) | — | — | Keep |

### After PR #87 merges (scripts only)

| Cleared | Still open |
|---|---|
| Profile / `mdd_help_pp` / sealed writers / observe script prose / hygiene bans | Stale research decision JSON + HIGH_BETA/V4/V5 publishes; claim JSON keys; local `WINDOWS`; Soft-Frozen aliases; verify book IDs; `claim_labels.normalize_claim_label`; roadmap CONST/ALL prose |

---

## F. Recommended fix batches (no governance ballot)

1. **Merge PR #87** (script emitter canon).  
2. **Regenerate** MDD L1–L3 / E50A / Gap5–6 decision packs + Track-A monitor status → `sealed_2023_plus`.  
3. **Re-publish** five-research + HIGH_BETA ballot/status MD from fixed generator (`SLEEVE_FIN_ONLY_A10`).  
4. **Regenerate** V4/V5 + dual-paper design + MDD verify summaries → `RETIRED_HISTORICAL_NARRATIVE` + harness book IDs.  
5. **Script hygiene follow-up:** verify book IDs; collapse claim JSON key; delete dead local `WINDOWS`; Soft-Frozen import alias; `normalize_claim_label` → retired; roadmap CONST/ALL → `BLEND_E45_A05`.

---

## G. Non-actions

- No Soft-Frozen / DEFAULT / stitch change.  
- No −13.16% reinvention or claim reinstatement.  
- Do not rewrite `oof_2012_2018` or paper densify `FIN_ONLY_A10` IDs.  
- Do not treat dated landmine reviews that *describe* old bugs as active schema.

---

## H. Method

- Harness canon read: `scripts/e45_paper_harness.py` (`CLAIM_STATUS`, `E45_PROFILE_DEFAULT`, `BOOK_BASE`/`BOOK_FULL`, `WINDOWS_STANDARD`, `blend_exposure`)  
- Soft-Frozen canon: `scripts/e16_soft_frozen_base.py` (`SOFT_FROZEN_FIN_CLIP` = `[0.50, 0.95]`)  
- Full pass: `scripts/`, `research/`, `repro/` for dual-name patterns  
- Spot counts on `main`: `sealed_2023_latest` (~24 files / ~8 script writers), `mdd_help_pp` (1 script), local `WINDOWS=` (~15), Soft-Frozen CLIP aliases (3), CONST/ALL roadmap (3), `SLEEVE_FIN_ONLY_A10` present in 24 files but observe prose still often says `FIN_ONLY_A10`  
- Cross-check open PR #87 scope vs residual artifact drift
