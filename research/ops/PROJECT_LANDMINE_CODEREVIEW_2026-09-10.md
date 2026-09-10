# Project Landmine Code Review — 2026-09-10 (post Soft-assist #185)

Scope: LIVE + shared simulation paths after Soft-assist OPEN observe (#185) and recent indicator / KD research.  
Companions: `PROJECT_CODE_REVIEW_2026-09-07.md` · `LIVE_PATH_CODEREVIEW_2026-09-07.md` · `PROJECT_LANDMINE_CODEREVIEW_2026-09-06.md`.

Soft-Frozen Financial **[0.60, 0.90] KEEP** · live **KD_OPT** KEEP · **E45 stitch OFF** · Soft-assist **paper observe only** · no Soft-Frozen / stitch / Soft-assist live flip proposed.

Label: `PROJECT_LANDMINE_CODEREVIEW_2026-09-10__SOFT_ASSIST_OBSERVE__CI_CAPITAL__SELL_SCORES`

---

## Verdict

| Area | Grade | Notes |
|---|---|---|
| Live Soft-Frozen FIN clip `[0.60, 0.90]` | **HEALTHY** | `e16_soft_frozen_base` SSOT; live signals FIN ∈ ~[0.66, 0.87]; `e21_qc` PASS |
| Live KD_OPT / TEL_EQUAL / E45 off | **HEALTHY** | `LIVE_FIN_WITHIN_SLEEVE=FIN_PRE_EXDIV_KD`; `LIVE_E45_STITCH=False`; tip state matches |
| Soft-assist live wire leak | **OK** | No soft_assist / SOFT_BOTH / fin_sell_scores in `e21_forward_pipeline` |
| Soft-assist observe ops | **FIXED this pass (ops)** | Monitor now falls back to tracked `dual_paper_nav_compare.csv` |
| CI live capital hardcode 3M | **FIXED this pass** | Workflow no longer passes `--capital 3000000` |
| Shared `sell_scores` on MIX/DUAL | **FIXED this pass** | Was silent no-op; now forwarded |
| Paper `simulate_core` SELL-before-BUY | **OPEN MEDIUM** | Live fixed; paper still append-order fills (doc-only this PR — avoid NAV churn) |
| Partial-write fills vs state | **OPEN** (prior O4 / L3) | Still non-atomic |
| Tip `nav.e22_version` QC | **OPEN P2** (prior L5) | Tip healthy today; QC still does not assert |

**Overall:** Live path after KD_OPT + FINBAND + E45 rollback is **honestly healthy** for Soft-Frozen / Exact T+1 / board-lot / Soft-assist isolation. New post-#185 landmines were **ops/CI drift** (gitignored NAV + obsolete 3M capital in the live writer) and a **shared allocator silent drop** of soft-sell scores on MIX/DUAL paths — not a Soft-Frozen or Soft-assist live wire.

---

## HIGH

### H1 — CI live writer hardcodes obsolete `--capital 3000000` (**FIXED this PR**)

- **Where:** `.github/workflows/v412f-forward-paper.yml` (was L89)
- **Bug:** Scheduled / issue-gated live forward still passed `--capital 3000000` after human **ACCEPT live capital 500M** (`portfolio_capital.DEFAULT_CAPITAL=500_000_000`). Day-to-day runs reuse `portfolio_state.json` cash (~539M NAV tip 2026-09-10), so the flag is mostly inert **until** wipe/replay / missing state — then CI would re-seed a **3M** book into `forward/e21` and commit it.
- **FIXED already?** **Yes this PR** — omit `--capital` so DEFAULT 500M applies. Guard: `tests/test_landmine_guards.py::LiveCapitalWorkflowGuard`.

### H2 — Soft-assist month-end depends on gitignored `*_daily_nav.csv` (**FIXED this PR**)

- **Where:** `scripts/e16_soft_assist_month_end_monitor.py` (was L143–146); `repro/.gitignore` L9–10; pack step `soft_assist_month_end` in `ops_month_end_paper_pack.py`
- **Bug:** #185 wires Soft-assist into the default month-end pack. Ledgers write `live_kd_opt_daily_nav.csv` / champion daily NAV, but those paths are **gitignored**. Only `dual_paper_nav_compare.csv` is tracked. Fresh clone / CI without `--refresh-ledgers` → monitor `SystemExit` → pack `all_ok=false` (fail-closed, but observe sleeve is unusable).
- **FIXED already?** **Yes this PR** — monitor prefers daily_nav, else reconstructs from tracked compare CSV (`nav_source` recorded). Still recommend `--refresh-ledgers` (or soft_assist ledger step) when market tip moves.

---

## MEDIUM

### M1 — `simulate_core` still fills pending in append order (no SELL-before-BUY)

- **Where:** `scripts/e50_early_stack_combined_nav.py` ~240–296
- **Issue:** Live e21 sorts SELL→BUY (post 2026-09-07 P0). Shared paper sim does not. Cash-starved BUYs are **dropped** (`q < 1: continue`) rather than left pending. Soft-assist / KD paper books share this path.
- **Impact:** Paper↔live fidelity gap under tight cash; at 500M less common but still a landmine for stress / small-capital screens.
- **This PR:** **Document only** (changing fill order would churn Soft-assist observe NAV without a deliberate refresh ACCEPT).
- **Next:** Separate paper engine PR + Soft-assist ledger refresh.

### M2 — `sell_scores` / `sell_ok` silently ignored on MIX + DUAL policies (**FIXED this PR**)

- **Where:** `scripts/within_sleeve_alloc.py` `allocate_mix_equal_rs_exdiv` (was sell-equal only); `allocate_dual_pub_priv` (did not forward kwargs); `allocate_sleeve_orders` MIX/DUAL call sites
- **Issue:** Soft-assist champion uses `FIN_PRE_EXDIV_KD` (sell_scores **did** apply). Any future MIX / DUAL + soft-sell research would silently equal-sell — false “no lift” / wrong observe.
- **FIXED already?** **Yes this PR** — forward + honor sell hooks on sell leg.

### M3 — KD_OPT parameter dual SSOT (copies still match today)

- **Where:** `e21_forward_pipeline.KD_OPT`; `soft_assist_helpers.LIVE_KD`; duplicated `LIVE_KD` dicts in `e16_kd_opt_indicator_assist_screen.py`, `e16_kd_soft_tel_sleeve_research.py`, `e16_indicator_*` screens
- **Issue:** Soft-assist observe asserts parity vs e21 at ledger build (this PR). Indicator research scripts still re-type the dict — drift risk for paper baselines labeled `LIVE_KD_OPT`.
- **This PR:** Comment + ledger assert + unit guard. **Document** consolidating research copies later (avoid e21 importing soft_assist).

### M4 — Soft-assist helper duplication in research screen

- **Where:** `scripts/e16_kd_soft_tel_sleeve_research.py` L125–131 redefines `soft_boost_scores` / `soft_sell_panel` instead of importing `soft_assist_helpers`
- **Issue:** Champion math can drift from OPERATING observe.
- **Recommend:** Import helpers on next research touch (doc-only here).

### M5 — Partial-write fills/divs vs `portfolio_state` (prior O4 / L3 — still open)

- **Where:** `e21_forward_pipeline.py` fills append before state write
- **Recommend:** Preflight reconcile or transactional write when next live-touched. **Doc-only** this PR.

### M6 — Ops JSON key `soft_frozen_clip` vs QC `soft_frozen_fin_clip` (prior O1 — still open)

- **Where:** `ops_month_end_paper_pack.py` payload key `soft_frozen_clip` (value from `SOFT_FROZEN_FIN_CLIP` — correct bounds)
- **Recommend:** Rename emitters on next ops touch. **Doc-only**.

---

## LOW

### L1 — Stale docstring “Live clip [0.50, 0.95]” in `e50` (**FIXED this PR**)

- **Where:** `e50_early_stack_combined_nav.e16_features` docstring — now points at `SOFT_FROZEN_FIN_CLIP`.

### L2 — Soft-assist / indicator scripts hardcode `CAPITAL = 500_000_000.0`

- Soft-assist ledgers now use `DEFAULT_CAPITAL`. Other indicator screens still literal 500M (matches today).

### L3 — Tip `nav.e22_version` not QC-asserted (prior L5)

- Tip 2026-09-10 = `E22_v2s_tw`, 0 nulls after replay. Optional QC still absent.

### L4 — Pack `cutover_note` omitted Soft-assist (**FIXED this PR**)

- Note now lists Soft-assist among paper observe sleeves.

### L5 — `LEGACY_ZERO_QTY_FILL_IDS` empty after replay

- Intentional; live fills qty>0 and board-lot 1000. OK.

---

## Already fixed / still OK (reconfirmed)

| Item | Status |
|---|---|
| Soft-Frozen box∩simplex projection | **OK** — live QC `soft_frozen_fin_clip` PASS |
| Exact T+1 NaT fail-closed | **OK** — `fills_date_nat_or_blank` |
| Live SELL-before-BUY + skip qty&lt;BOARD_LOT | **OK** — no qty≤0 fills in tip ledger |
| Live board-lot 1000 + `fills_board_lot_1000` QC | **OK** |
| Dividend load `require_exists=True` on live | **OK** |
| Pipeline does not own `qc_status.json` | **OK** |
| Canonical path gate `forward/e21` | **OK** |
| E45 live stitch | **OFF** — `LIVE_E45_STITCH=False`; rollback note in state |
| Soft-assist observe | **OPERATING** — `live_wire: false`; cutover checklist **BLOCKED** |
| Soft-assist uses `simulate_core` + `fin_sell_scores` for champion only | **OK** — live never passes sell_scores |
| `e16_soft_frozen_base` clip SSOT `[0.60, 0.90]` | **OK** — live + paper features both call `build_soft_frozen_targets` |
| Hygiene gates | **PASS** — project + E45 paper |
| `e21_qc` on tip | **PASS** |
| Research scripts not imported by live pipeline | **OK** — no soft_assist / indicator imports in e21 |

---

## Fixes shipped this pass

1. CI forward workflow: drop obsolete `--capital 3000000`.
2. Soft-assist month-end: fall back to tracked `dual_paper_nav_compare.csv`.
3. `within_sleeve_alloc`: forward/honor `sell_ok` / `sell_scores` on MIX + DUAL.
4. Soft-assist ledgers: `DEFAULT_CAPITAL` + assert `LIVE_KD` ≡ `e21.KD_OPT` + refuse if e21 mentions soft_assist or E45 stitch on.
5. Stale e50 clip docstring; pack cutover_note mentions Soft-assist.
6. Landmine unit guards for CI capital, live soft-assist absence, KD parity, monitor compare fallback.

---

## Recommended next (not this PR / needs deliberate paper refresh)

| Priority | Item |
|---|---|
| P1 | `simulate_core` SELL-before-BUY (+ optional pending retry) then refresh Soft-assist ledgers |
| P1 | Consolidate `LIVE_KD` copies into one non-soft_assist module imported by e21 + research |
| P2 | Partial-write transactional live state |
| P2 | QC assert tip `nav.e22_version == DEFAULT` |
| P2 | Rename ops `soft_frozen_clip` → `soft_frozen_fin_clip` |
| P2 | `e16_kd_soft_tel_sleeve_research` import `soft_assist_helpers` |

---

## Explicit non-actions

- No Soft-Frozen clip change
- No Soft-assist live wire / cutover
- No E45 stitch re-open
- No invented payment dates
- No rewrite of `forward/e21` history
- No paper Soft-assist NAV regeneration in this PR (monitor fallback only)

## Verification

```bash
python3 scripts/e21_qc.py --state-dir forward/e21
PYTHONPATH=scripts python3 scripts/check_project_coding_hygiene.py
PYTHONPATH=scripts python3 scripts/check_e45_paper_hygiene.py
python3 -m unittest tests.test_landmine_guards
# Soft-assist monitor without local daily_nav:
mv repro/soft-assist-dual-paper-observe/outputs/live_kd_opt_daily_nav.csv /tmp/ 2>/dev/null || true
python3 scripts/e16_soft_assist_month_end_monitor.py
```
