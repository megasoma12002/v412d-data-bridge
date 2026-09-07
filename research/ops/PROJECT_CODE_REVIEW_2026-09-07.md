# Project Code Review — 2026-09-07 (full repo)

Scope: live `forward/e21` path + research/ops hygiene across `scripts/` / `research/`.  
Soft-Frozen Financial **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · live stitch **FORBIDDEN** · retired MDD narrative **`RETIRED_HISTORICAL_NARRATIVE`** (do not invent a replacement).

Companion detail:
- `LIVE_PATH_CODEREVIEW_2026-09-07.md`
- `RESEARCH_OPS_HYGIENE_CODEREVIEW_2026-09-07.md`

Label: `PROJECT_CODEREVIEW_2026-09-07__P0_ZERO_FILL_FIXED__T1_NAT__MDD_KEY__GAP6_GREEN`

---

## Verdict

| Area | Grade | Notes |
|---|---|---|
| Soft-Frozen FIN clip | **HEALTHY** | Prior renormalize + QC band checks still green |
| Exact T+1 (happy path) | **HEALTHY** | Same-bar hard-fail on write; empty/missing schema fail-closed |
| Exact T+1 (NaT/blank dates) | **FIXED this pass** | Was fail-open → now fail-closed |
| Live zero-qty fills | **FIXED this pass (forward-only)** | SELL-before-BUY; skip qty&lt;1; QC `fills_positive_qty` + frozen legacy allowlist |
| E22 / Gap6 live evidence | **HEALTHY** | Post-Monday forward PASS (`61f188c`); EVIDENCE PRESENT |
| Hygiene gates | **PASS** | `check_project_coding_hygiene` · `check_e45_paper_hygiene` |
| Research metric key half-migration | **FIXED this pass** | stage3 / v4v5 read `max_drawdown` |
| Research residual debt | **OPEN P1/P2** | Soft-Frozen JSON key rename, claim normalizer sibling, book-ID hardcodes — tracked below |
| HIGH_BETA / stitch | **HOLD / FORBIDDEN** | Not wired into month-end pack |

**Overall:** Live path had a real P0 (qty=0 BUY fills burning order ids) that QC previously missed. Fixes are **forward-only** (no history rewrite). Soft-Frozen / DEFAULT / stitch unchanged. Research debt remains mostly naming/hygiene, not live cutover risk.

---

## Fixed this pass (P0 / P1)

### L1 Zero-qty BUY fills (P0)
- **Where:** `scripts/e21_forward_pipeline.py` pending fill loop
- **Bug:** CSV order BUY-before-SELL depleted cash; `qty=0` fills still appended → order never retries (4 live `5880` hits)
- **Fix:** sort SELL→BUY; **skip** `q < 1` (leave order pending). Do not rewrite historical fills.
- **QC:** `fills_positive_qty` fail-closed except frozen `LEGACY_ZERO_QTY_FILL_IDS` (4 ids)

### L2 Exact T+1 NaT/blank dates (P1)
- **Where:** `scripts/e21_qc.py` `exact_t1_from_fills`
- **Bug:** blank/`NaT` dates compared as non-same-bar → `exact_t1_ok=True`
- **Fix:** coerce + fail with `fills_date_nat_or_blank`

### L4 Missing dividend file silent (P1 latent)
- **Where:** `scripts/e22_dividend_accounting.py` `load_dividend_events`
- **Fix:** `require_exists=` opt-in; live pipeline passes `require_exists=True`

### R1 `max_drawdown` / `mdd` half-migration (P0 research regenerators)
- **Where:** `scripts/e45_stage3_dual_paper_windows.py`, `scripts/e45_v4v5_named_packs.py`
- **Bug:** writers emit `max_drawdown`; deltas/MD still read `mdd` → KeyError on regenerate
- **Fix:** read/display `max_drawdown` consistently

---

## Still open (not Soft-Frozen / stitch)

| ID | Sev | Finding | Action |
|---|---|---|---|
| O1 | P1 | Ops JSON still uses key `soft_frozen_clip` (const import OK) | Rename emitters to `soft_frozen_fin_clip` on next ops touch |
| O2 | P1 | `normalize_claim_label` sibling `NOT_VERIFIED_HISTORICAL_NARRATIVE` | Prefer retired const only |
| O3 | P1 | Dual-paper ledgers hardcode `BASE_ID` string | Prefer `BOOK_BASE` |
| O4 | P2 | Partial-write: fills append before `portfolio_state` | Preflight / transactional write when next touched |
| O5 | P2 | Tip `nav.e22_version` not QC-asserted (tip healthy today) | Optional QC latest non-null == DEFAULT |
| O6 | P2 | Deep-dive / roadmap prose `ALL_A05` residue | Doc regenerators |
| O7 | P2 | `year_mdd_help_pp` / `help_YYYY_pp` in M1–M3 forks | Ban or migrate on next paper run |

---

## Already healthy (reconfirmed)

- Soft-Frozen box∩simplex + live QC `soft_frozen_fin_clip`
- Gap6 code wire + live evidence after 2026-09-07 forward
- HIGH_BETA HOLD DRAFT; not in `ops_month_end_paper_pack`
- `sealed_2023_latest` writers cleared
- Classic banned emitters cleared (hygiene PASS)
- Month-end pack correctly marks `all_ok=false` when Gap6 blocked (pre-evidence)

---

## Verification run this pass

```bash
python3 scripts/e21_qc.py --state-dir forward/e21   # PASS incl. fills_positive_qty
PYTHONPATH=scripts python3 scripts/check_project_coding_hygiene.py
PYTHONPATH=scripts python3 scripts/check_e45_paper_hygiene.py
```

NaT unit assert in review session: `exact_t1_from_fills` blank date → FAIL.

---

## Non-actions

- No Soft-Frozen / DEFAULT / stitch flip
- No rewrite of historical `forward/e21` fills/NAV rows
- No HIGH_BETA OPEN
- No invent MDD replacement
