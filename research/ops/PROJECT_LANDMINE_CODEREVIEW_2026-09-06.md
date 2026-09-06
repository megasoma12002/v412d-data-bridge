# Project Code Review — Landmines from E45 five-research batch (2026-09-06)

Scope: whole-repo engineering hygiene after the five-item paper batch.  
Soft-Frozen Financial **[0.50, 0.95] KEEP** · DEFAULT KEEP · live stitch **FORBIDDEN** · −13.16% **RETIRED**.

## Verdict

| Area | Grade | Notes |
|---|---|---|
| Live QC / Soft-Frozen / Exact T+1 | **PASS** | Prior P0/P1 fixes still green; `e21_qc` PASS |
| Month-end observe monitors | **PASS** | FULL / A05 / A25 / sleeve-local EXIT 0, `stitch_blocked=true` |
| E45 paper harness truthfulness | **FIXED this pass** | `__all__` consistency now fail-closed in hygiene |
| Five-research batch book IDs | **FIXED this pass** | Non-canonical `FULL_E45` / `BLEND_A##` / `ALL_A##` → canonical |
| Hygiene coverage of `*_batch.py` | **FIXED this pass** | Regenerator detector now includes research batches |
| Soft-Frozen / stitch governance | **KEEP / FORBIDDEN** | No flips |

## Landmines stepped on (this arc)

### L1 — Agent / tooling name confusion
- **Symptom:** Repeated broken drafts of `e45_five_research_batch.py` importing names that “looked right” in stale views (`load_market` vs aliases, window key drift).
- **Root:** Harness is the single source of truth; any advertised export that does not exist is a landmine.
- **Fix:** `check_e45_paper_hygiene.py` now exec-checks `__all__` against defined names (fail-closed).

### L2 — Non-canonical book IDs in new research
- **Symptom:** Batch emitted observe keys / sim labels `FULL_E45`, `BLEND_A05`, `BLEND_A25`, `ALL_A05`.
- **Impact:** Cross-run joins with OPERATING observe sleeves (`CHAL_E45_E3`, `BLEND_E45_A05`, …) break; humans misread packs.
- **Fix:** `scripts/e45_five_research_batch.py` rewritten to canonical IDs; artifacts regenerated.

### L3 — Hygiene blind spot for research batches
- **Symptom:** `e45_five_research_batch.py` was **not** classified as a paper regenerator, so missing-harness would not fail closed.
- **Fix:** `_is_paper_regenerator` now matches `research_batch` / `*_batch.py`.

### L4 — Tip PAUSE ≠ paper failure (governance landmine)
- **Symptom:** Tip YTD/1y PAUSE_REVIEW across observe sleeves looks like “batch broken”.
- **Rule:** Observe PAUSE is expected and does **not** revoke held-out paper scores; stitch stays forbidden until clean trailing + second human ACCEPT.


### L5 — `FEE_KEYS` NameError in α cost/turnover regenerator
- **Symptom:** `e45_alpha_cost_turnover_paper.py` completed all sims then crashed on undefined `FEE_KEYS`, leaving **stale** report JSON with `FULL_E45` / bare `BLEND_A##`.
- **Impact:** Research mirrors disagreed with harness; next agents trusted broken artifacts.
- **Fix:** Define `FEE_KEYS` to match `simulate_core` scaled fee constants; regenerate reports; hygiene now scans regenerator JSON for retired book IDs.

### L6 — Sleeve-local scope labels colliding with observe IDs
- **Symptom:** `ALL_A05` / `FIN_A05` / `HIGHBETA_A05` looked like observe books.
- **Fix:** ALL-scope uses `BOOK_BLEND_A##` / `BOOK_FULL` / `BOOK_BASE`; sleeve overlays use `FIN_ONLY_*` / `FIN_0050_*` / `HIGH_BETA_*`. Deep-dive `book_tag("ALL", …)` emits `BLEND_E45_A##_C#x`.

## Fixes shipped this pass

1. Canonicalize five-batch book / observe sleeve IDs; regenerate `repro/e45-five-research-batch/` + ops/research MD.
2. Hygiene: batch regenerator detection + harness `__all__` truth check.
3. Fix `FEE_KEYS`; regenerate α-cost + crisis-year + sleeve-local artifacts to canonical IDs.
4. Hygiene scans regenerator report JSON for stale `FULL_E45` / `BLEND_A##`.
5. Smoke: `check_e45_paper_hygiene` PASS · `check_project_coding_hygiene` PASS · month-end monitors EXIT 0 · `e21_qc` PASS.

## Still deferred (not blocking)

| ID | Item | Why deferred |
|---|---|---|
| D1 | Split oversized OOF / adversarial monoliths | Touch-when-needed (prior O7) |
| D2 | Historical MD mentioning `NOT_VERIFIED` | Dated snapshots; regenerators already emit retired status |
| D3 | HIGH_BETA observe OPEN | Ballot remains **DRAFT**; held-out still prefers FIN_ONLY_A10 |

## Verification

```bash
PYTHONPATH=scripts python3 scripts/check_e45_paper_hygiene.py
PYTHONPATH=scripts python3 scripts/check_project_coding_hygiene.py
python3 scripts/e45_five_research_batch.py
python3 scripts/e45_blend005_month_end_monitor.py
python3 scripts/e21_qc.py
```

## Explicit non-goals

- Soft-Frozen flip / DEFAULT rewrite / live stitch
- Auto-OPEN HIGH_BETA
- Invent −13.16% replacement

## Label

`PROJECT_LANDMINE_CODEREVIEW_2026-09-06__BATCH_IDS_FIXED__HYGIENE_EXTENDED__STITCH_FORBIDDEN`

## Round 3 — whole-repo review hardening (no behavior change to live)

| Fix | Effect |
|---|---|
| `fetch_telecom_0050_ohlcv.py` `__main__` guard | Import no longer hits network / writes |
| `v412f-forward-paper.yml` / `complete-telecom-0050-ohlcv.yml` issue title gates | Only `RUN_E21_FORWARD` / `RUN_TELECOM_0050` issues can write |
| Regenerated crisis / blend-grid / blend-screen / maxcut artifacts | Retired `CONST_A*` / `REF_BLEND_A*` / `CHAL_E45_E3_FULL` cleared |
| Hygiene `ARTIFACT_GLOBS` expanded | Fail-closed on those JSON paths |
| `BOOK_BASE_RUNTIME_NOTE` | Label honesty without renaming ledger ids |
| `tests/test_landmine_guards.py` | Minimal fail-closed unit guards |

Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · −13.16% RETIRED.

## Round 4 — High leftovers + Medium claim drift

| Fix | Effect |
|---|---|
| `e21_forward_pipeline` → `pipeline_t1_audit.json` | Stops stomping `qc_status.json` (owned by `e21_qc.py`) |
| `--confirm-e22-version-override` | Non-DEFAULT E22 books require explicit confirm |
| E45 month-end monitors regenerated at NAV tip `2026-09-04` | Tip-aligned PAUSE (stitch still blocked) |
| fills/orders `dtype={"code": str}` + hygiene guard | Blocks 0050→50 landmine |
| dual-paper `current_live_clip` from Soft-Frozen constants | No hardcoded 0.50/0.95 literals |
| Frozen governance/spec claim label | `NOT_VERIFIED` → `RETIRED_HISTORICAL_NARRATIVE` |
| Month-end pack workflow | Skip git commit when `continue_on_error` |

Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · −13.16% RETIRED.
