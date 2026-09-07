# RESEARCH / OPS Hygiene Code Review — 2026-09-07

Status: **REVIEW ONLY**  
Soft-Frozen Financial **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · E45 stitch **FORBIDDEN** · retired MDD narrative **`RETIRED_HISTORICAL_NARRATIVE`** (do not invent a replacement)

Baseline: workspace tip after prior naming / debt-sweep / landmine PRs.  
Canon: `research/ops/CODING_STANDARDS.md` · prior `*CODEREVIEW*` under `research/ops/` · `scripts/e45_paper_harness.py` · `scripts/e16_soft_frozen_base.py` · `scripts/claim_labels.py`

Hygiene gates at review time: **`check_e45_paper_hygiene` PASS** · **`check_project_coding_hygiene` PASS**.  
This review finds **ban-gap / half-migration** issues those gates still miss.

Label: `RESEARCH_OPS_HYGIENE_CODEREVIEW_2026-09-07__STITCH_FORBIDDEN__NO_INVENT_MDD`

---

## Verdict

| Theme | Live emitters | Artifacts / prose | Action |
|---|---|---|---|
| Book ID aliases (`CONST_`/`REF_BLEND_`/`ALL_A05`) | Cleared in scripts (hygiene PASS) | Residual roadmap / deep-dive MD+JSON | P1 regenerate / patch operator MDs |
| Metric `mdd` vs `max_drawdown` | **Half-migrated in stage3 + v4v5** | Old CSVs still `mdd` | **P0 fix emitters** |
| `mdd_help_pp` vs `mdd_improve_pp` | Harness deltas OK; year keys still `help_YYYY_pp` | mostly cleared | P1 rename emit keys |
| `sealed_2023_latest` writers | Cleared | only intentional read fallback | OK (keep dual-read) |
| Claim `NOT_VERIFIED` vs `RETIRED_*` | Script emitters OK | normalizer still `NOT_VERIFIED_*` sibling | P1 fix normalizer |
| `e45_paper_harness` adoption | Most paper regenerators OK | stage3 / v4v5 outside regenerator detector | P1 extend hygiene + migrate |
| Soft-Frozen import | Const import OK | JSON key still `soft_frozen_clip` / `*_keep` / `*_live_clip` | P1 unify JSON key |
| HIGH_BETA OPEN / month-end wire | **NOT OPEN · not wired** | HOLD DRAFT hygiene present | OK |
| Gap6 / ops fail-closed | Gap6 exit 1/2 fail-closed | month-end can `--continue-on-error` | OK (documented) |

No Soft-Frozen / DEFAULT / stitch ballot is implied.

---

## P0 — actionable now (live emitters wrong)

### P0-1. `max_drawdown` write / `mdd` read half-migration (stage3 + V4/V5)

**Why P0:** Regenerating these packs KeyErrors or emits broken deltas. Checked-in CSVs still use column `mdd`; scripts now write `max_drawdown` but still index `["mdd"]`.

| File | Write key | Read / MD key |
|---|---|---|
| `scripts/e45_stage3_dual_paper_windows.py` | `max_drawdown` (~L78) | `_get(..., "mdd")` (~L96–97); MD `r['mdd']` (~L163) |
| `scripts/e45_v4v5_named_packs.py` | `max_drawdown` in cost + crisis rows | `c["mdd"]` / `b["mdd"]` (~L143–148, ~L219–224); MD `r['mdd']` (~L308) |

Evidence on tip:

- `repro/e45-v4v5-named-packs/outputs/e45_named_cost_multiples.csv` header still `...,cagr,mdd,...`
- `repro/e45-dual-paper-observe-design/outputs/dual_paper_window_metrics.csv` header still `...,cagr,mdd,...`
- Script bodies already append `max_drawdown`

**Fix:** Use `max_drawdown` consistently in writers, readers, and markdown; regenerate packs. Prefer harness `window_stats` / `deltas_vs_base` where possible.

**Hygiene gap:** Neither script matches `_is_paper_regenerator` (`*_paper.py` / `*_ledgers.py` / `*_batch.py`), so dual-alias family `(max_drawdown, mdd, …)` does **not** fail closed on them.

**Actionable now:** Yes.

---

## P1 — actionable now (join / operator risk)

### P1-1. Soft-Frozen JSON key still forked in live ops emitters

Canon preference (debt-sweep): `soft_frozen_fin_clip`.  
Live writers still emit other keys (values correctly from `SOFT_FROZEN_FIN_CLIP` import — const OK, key drift remains):

| Emitter | JSON key |
|---|---|
| `scripts/ops_month_end_paper_pack.py` | `soft_frozen_clip` |
| `scripts/ops_alert_scan.py` | `soft_frozen_clip` |
| `scripts/e21_live_vs_paper_recon.py` | `soft_frozen_clip` |
| `scripts/fincap50_sealed_cagr_charter_screen.py` | `soft_frozen_clip` |
| Paper packs (v4v5, stage3, next-batch, pause-refresh, …) | `soft_frozen_keep` |
| MDD L3/L4 heldout / OOF / adv | `soft_frozen_live_clip` |

`e21_qc.py` check name is `soft_frozen_fin_clip` (boolean), a fourth spelling surface.

**Actionable now:** Yes (rename emitters + dual-read consumers if any).

### P1-2. `claim_labels.normalize_claim_label` → wrong sibling

`scripts/claim_labels.py` maps deprecated aliases → `NOT_VERIFIED_HISTORICAL_NARRATIVE`, not canon `RETIRED_HISTORICAL_NARRATIVE`. Live claim emitters use `e45.CLAIMED_MDD_STATUS` / harness `CLAIM_STATUS` (good). Landmine if anything adopts `normalize_claim_label` for E45 claim status.

**Actionable now:** Yes (map to `RETIRED_HISTORICAL_NARRATIVE`; keep legacy const for vocabulary only).

### P1-3. Verify book IDs still non-canonical

`scripts/e45_verify_mdd_1316.py` still labels variants `E16_E18_E22_v2s` / `E16_E18_E22_v2s_E45_E3` (and mirrors in `research/e45/E45_MDD_1316_VERIFICATION.json`). Cross-pack joins against dual-paper `BASE_E16_E18_E22_v2s` / `CHAL_E45_E3` break.

**Actionable now:** Yes (alias table + emit canonical; do not invent MDD).

### P1-4. Year MDD help keys / local M1 fork chain

Harness / five-batch use `mdd_improve_*`. New M1–M3 papers still emit:

- function `year_mdd_help_pp` defined in `scripts/e45_m1_state_signal_paper.py`
- imported by M2/M3 relocate / BIL_FX / three-state papers
- JSON keys `help_2015_pp` … `help_2022_pp` (not `mdd_improve_2015_pp`)

Hygiene bans `\bmdd_help_pp\b` and a few `mdd_help_*` spellings — **does not** catch `help_YYYY_pp` or `year_mdd_help_pp`.

**Actionable now:** Yes (rename emit keys; optionally hoist helper into harness / `research_metric_helpers`).

### P1-5. Harness adoption gap for stage3 / v4v5

| Script | Harness? | Regenerator detector? |
|---|---|---|
| `scripts/e45_stage3_dual_paper_windows.py` | only `WINDOWS_STANDARD` | No |
| `scripts/e45_v4v5_named_packs.py` | **none** | No |

These still fork local market load / `nav_stats` paths and hardcode `"E3_VOLTARGET_WINNER"`. Related: `e45_crisis_triggered_alpha_paper.py` keeps local `blend_const` (≈ harness `blend_exposure`) plus experiment-specific `blend_gate` / `blend_e1bin` (those experiment forks are OK).

**Actionable now:** Yes (extend `_is_paper_regenerator` for `*_named_packs.py` / `*_dual_paper_windows.py`; migrate load/stats).

### P1-6. Stale deep-dive book IDs (`ALL_A05_C*`)

- Generator `scripts/e45_sleeve_local_deep_dive.py` now emits `BLEND_E45_A05_C1x` via `book_id_for_alpha`.
- Published `research/e45/E45_SLEEVE_LOCAL_DEEP_DIVE.md` + `.json` still list `ALL_A05_C1x` / `ALL_A08_C2x`.

**Actionable now:** Yes (regenerate; leave CODEREVIEW historical mentions).

### P1-7. Operator roadmap / P1–P7 prose aliases

Still teach banned display IDs:

- `research/ops/E45_PAPER_RESEARCH_ROADMAP.md` — `ALL_A05` in five-batch row
- `research/ops/E45_PAPER_P1_P7_INTEGRATED_ANALYSIS.md` — `REF_BLEND_A05`

**Actionable now:** Yes (prose → `BLEND_E45_A05`). Historical `*CODEREVIEW*` / landmine docs that *describe* the bug: leave.

### P1-8. Dual-paper JSON claim key lag

Live ledger scripts emit `claim_status`. Some research mirrors still have `claimed_mdd_status` (value correctly `RETIRED_HISTORICAL_NARRATIVE`), e.g.:

- `research/e45/E45_DUAL_PAPER_OBSERVE.json`
- `research/e45/E45_BLEND005_DUAL_PAPER_OBSERVE.json`
- `research/e45/E45_BLEND025_DUAL_PAPER_OBSERVE.json`
- `research/e45/E45_BLEND_ALPHA_*.json`
- `research/e45/E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE.json`
- `research/e45/E45_SLEEVE_LOCAL_DEEP_DIVE.json`

**Actionable now:** Yes on next ledger regenerate (not a blind JSON rewrite).

### P1-9. `BASE_ID = "BASE_…"` string beside harness import

Still hardcode in `e45_dual_paper_ledgers.py`, `e45_blend005_dual_paper_ledgers.py`, `e45_blend025_dual_paper_ledgers.py`. Prefer `BASE_ID = BOOK_BASE` (sleeve-local / M2 bil-fx already do).

**Actionable now:** Yes (trivial).

---

## P2 — hygiene / residual (fix when touched)

| ID | Finding | Actionable now? |
|---|---|---|
| P2-1 | `REF_BLEND_E45_A05` / `REF_FIN_ONLY_A10` / `REF_CHAL_E3` in `e45_next_research_batch.py` (ref-tagged experiment books) | Prefer display-only or `book_id_for_alpha`; not observe IDs |
| P2-2 | `mdd_l1_sealed_attribution.py` emits `val_2019_2022` vs E45 `validation_2019_2022` | Document MDD-L1 ownership or rename |
| P2-3 | Soft-Frozen KEEP prose `[0.50, 0.95]` in monitor MD strings | Allowed by standards; optional `CLIP_TXT` from import |
| P2-4 | Pre-E45 `v412*` trainers use internal metrics key `mdd` | Leave (not E45 NAV schema) |
| P2-5 | Month-end default `--report-only` on alert scan; CRITICAL only fails with `--fail-on-critical` | Intentional; document in runbooks |
| P2-6 | Observe status table row says “Sleeve-local FIN_ONLY @ α=0.10” without id `SLEEVE_FIN_ONLY_A10` (`E45_OBSERVE_SLEEVES_STATUS.md`) | Cosmetic; body already correct |

---

## Themes checked — healthy / intentional keep

### Book ID aliases (scripts)

Banned `CONST_A##` / `REF_BLEND_A##` / bare `BLEND_A##` / `FULL_E45` / `CHAL_E45_E3_FULL` **not** present as emitters under `scripts/` (only in hygiene ban lists). Canonical `BLEND_E45_A##`, `SLEEVE_FIN_ONLY_A10`, `BASE_E16_E18_E22_v2s` used by live observe / paper packs.

**Keep:** paper densify `FIN_ONLY_A10` ≠ observe `SLEEVE_FIN_ONLY_A10`.

### `sealed_2023_latest`

No live writers remain. Only intentional dual-read:

- `scripts/e50a_dual_track_s9a1_monitor.py` — `sealed_2023_plus or sealed_2023_latest`
- hygiene allow for that fallback pattern

Decision JSONs under `research/gaps/` already use `sealed_2023_plus`.

### Claim status emitters

New/active paper + ops scripts emit `CLAIM_STATUS` / `e45.CLAIMED_MDD_STATUS` → `RETIRED_HISTORICAL_NARRATIVE`. V4/V5 ops MDs and verify JSON already retired. Historical CODEREVIEW / landmine text mentioning `NOT_VERIFIED`: **leave**.

### HIGH_BETA

- Ballot / hygiene: **HOLD DRAFT / NOT OPEN** (`E45_HIGH_BETA_HOLD_DRAFT_HYGIENE.md`)
- `scripts/ops_month_end_paper_pack.py`: **no HIGH_BETA step**
- Observe status lists HIGH_BETA under Draft / HOLD only

### Gap6 / ops fail-closed

- `scripts/e22_gap6_fidelity_kpi.py`: `kpi_ok = code_ok AND live_evidence_ok`; exit `1` code fail / `2` live evidence missing / `0` ok — **fail-closed**
- Latest `research/ops/E22_GAP6_FIDELITY_KPI.json`: `kpi_ok: true`
- `MONTH_END_PAPER_PACK.json` (2026-09-07): ran with `continue_on_error: true`; Gap6 then exited `2` → `all_ok: false` / `partial_pack: true` — pack surfaces failure correctly when continue-on-error is used

### Soft-Frozen const single-source

Machine fields import `SOFT_FROZEN_FIN_CLIP` (no `SOFT_FROZEN_CLIP =` alias left). Prose KEEP mentions of the band remain allowed.

---

## Explicit non-actions

- No Soft-Frozen flip / DEFAULT rewrite / live stitch
- No HIGH_BETA OPEN / no month-end HIGH_BETA wire
- No inventing a replacement for the retired handoff MDD narrative
- No blind rewrite of historical CODEREVIEW / dated snapshots that document old bans
- Do not collapse `FIN_ONLY_A10` (paper densify) into `SLEEVE_FIN_ONLY_A10` (observe)

## Suggested fix order

1. **P0-1** stage3 + v4v5 `mdd`↔`max_drawdown` + regenerate  
2. Widen regenerator detector so those scripts fail closed on dual metric/book aliases  
3. **P1-2** claim normalizer · **P1-1** Soft-Frozen JSON key · **P1-3** verify book IDs  
4. **P1-4** year help keys · regenerate deep-dive + dual-paper claim-key mirrors · roadmap prose

## Verify after fixes

```bash
PYTHONPATH=scripts python3 scripts/check_e45_paper_hygiene.py
PYTHONPATH=scripts python3 scripts/check_project_coding_hygiene.py
# after emitter fixes:
python3 scripts/e45_stage3_dual_paper_windows.py
python3 scripts/e45_v4v5_named_packs.py
python3 scripts/e22_gap6_fidelity_kpi.py
```
