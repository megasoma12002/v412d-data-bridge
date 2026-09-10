# Project Code Review — 2026-09-10 (full repo)

Scope: whole-repo landmine + live-path review after Soft-assist OPEN observe (#185) and indicator / KD research arc.  
Soft-Frozen Financial **[0.60, 0.90] KEEP** · live **KD_OPT** KEEP · E45 stitch **OFF** · Soft-assist **paper observe only** · DEFAULT **`E22_v2s_tw` KEEP**

Companion detail: `PROJECT_LANDMINE_CODEREVIEW_2026-09-10.md`  
Priors: `PROJECT_CODE_REVIEW_2026-09-07.md` · `LIVE_PATH_CODEREVIEW_2026-09-07.md` · `PROJECT_LANDMINE_CODEREVIEW_2026-09-06.md`

Label: `PROJECT_CODEREVIEW_2026-09-10__CI_CAPITAL_500M__SOFT_ASSIST_NAV_FALLBACK__SELL_SCORES_MIX`

---

## Verdict

| Area | Grade | Notes |
|---|---|---|
| Soft-Frozen FIN clip `[0.60, 0.90]` | **HEALTHY** | SSOT `e16_soft_frozen_base`; `e21_qc` PASS |
| Exact T+1 / board-lot / zero-qty | **HEALTHY** | Prior P0/P1 fixes still green |
| Live KD_OPT + TEL_EQUAL + E45 OFF | **HEALTHY** | Tip state matches; Soft-assist **not** in e21 |
| Soft-assist observe isolation | **HEALTHY** | `live_wire: false`; cutover **BLOCKED** |
| Soft-assist month-end on fresh clone | **FIXED this pass** | Fallback to tracked `dual_paper_nav_compare.csv` |
| CI live capital (wipe/recovery) | **FIXED this pass** | Dropped obsolete `--capital 3000000` → DEFAULT 500M |
| Paper MIX/DUAL soft-sell hooks | **FIXED this pass** | Was silent no-op |
| Paper `simulate_core` SELL-before-BUY | **OPEN MEDIUM** | Live fixed; paper still append-order (doc-only — avoid Soft-assist NAV churn) |
| Hygiene gates | **PASS** | project + E45 paper |
| Landmine unit guards | **PASS** | `tests/test_landmine_guards.py` (9) |

**Overall:** Live path remains healthy. Post-#185 issues were **ops/CI drift** (gitignored Soft-assist NAV; obsolete 3M capital in the live writer workflow) and a **shared allocator** silent drop of `sell_scores` on MIX/DUAL — not a Soft-Frozen flip or Soft-assist live wire.

---

## Fixed this pass

### H1 — CI live writer hardcoded `--capital 3000000`
- **Where:** `.github/workflows/v412f-forward-paper.yml`
- **Bug:** After ACCEPT capital 500M, wipe/missing-state recovery would re-seed **3M** into `forward/e21`
- **Fix:** Omit `--capital` → `portfolio_capital.DEFAULT_CAPITAL` (500M)
- **Guard:** `LiveCapitalWorkflowGuard`

### H2 — Soft-assist month-end required gitignored `*_daily_nav.csv`
- **Where:** `scripts/e16_soft_assist_month_end_monitor.py`
- **Bug:** Pack step failed on fresh clone without `--refresh-ledgers`
- **Fix:** Prefer daily_nav; else reconstruct from tracked `dual_paper_nav_compare.csv` (`nav_source` recorded)

### M2 — `sell_scores` / `sell_ok` dropped on MIX + DUAL
- **Where:** `scripts/within_sleeve_alloc.py`
- **Bug:** Future MIX/DUAL + soft-sell research would silently equal-sell
- **Fix:** Forward + honor sell hooks on sell leg

### Other
- Soft-assist ledgers: `DEFAULT_CAPITAL` + assert `LIVE_KD` ≡ `e21.KD_OPT`
- Stale e50 clip docstring; pack cutover_note lists Soft-assist
- Landmine unit guards expanded

---

## Still open (not Soft-Frozen / Soft-assist live)

| ID | Sev | Finding | Action |
|---|---|---|---|
| M1 | P1 | `simulate_core` no SELL-before-BUY (live has it) | Separate paper-engine PR + Soft-assist ledger refresh |
| M3 | P1 | `LIVE_KD` / `KD_OPT` copied in many research scripts | Consolidate into shared non-soft_assist module |
| M4 | P2 | `e16_kd_soft_tel_sleeve_research` duplicates soft helpers | Import `soft_assist_helpers` on next touch |
| M5 | P2 | Partial-write fills vs `portfolio_state` (prior O4) | Transactional write when next live-touched |
| M6 | P2 | Ops JSON key `soft_frozen_clip` vs QC `soft_frozen_fin_clip` | Rename on next ops touch |
| L3 | P2 | Tip `nav.e22_version` not QC-asserted | Optional QC assert == DEFAULT |

---

## Already healthy (reconfirmed)

- Soft-Frozen box∩simplex + live QC `soft_frozen_fin_clip`
- Exact T+1 NaT fail-closed; `fills_positive_qty`; board-lot 1000
- Live KD_OPT / TEL_EQUAL; `LIVE_E45_STITCH=False`
- Soft-assist observe OPERATING; no soft_assist imports in e21
- Dividend `require_exists=True` on live; Gap6 / hygiene PASS

---

## Verification run this pass

```bash
python3 scripts/e21_qc.py --state-dir forward/e21
PYTHONPATH=scripts python3 scripts/check_project_coding_hygiene.py
PYTHONPATH=scripts python3 scripts/check_e45_paper_hygiene.py
python3 -m unittest tests.test_landmine_guards
python3 scripts/e16_soft_assist_month_end_monitor.py
```

All PASS · Soft-assist monitor alerts **none** (asof 2026-09-10).

---

## Non-actions

- No Soft-Frozen / DEFAULT / Soft-assist live / E45 stitch flip
- No rewrite of `forward/e21` history
- No Soft-assist NAV regeneration in this PR (monitor fallback only)
- No invented payment dates
