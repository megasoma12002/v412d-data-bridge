# LIVE Path Code Review — 2026-09-07

Scope: **LIVE path only** (`forward/e21` + write/QC scripts below).  
Reviewed: `scripts/e21_forward_pipeline.py`, `e21_qc.py`, `e16_soft_frozen_base.py`, `e22_dividend_accounting.py`, `e21_live_vs_paper_recon.py`, and `forward/e21/` schema expectations.

Soft-Frozen Financial **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · live stitch **FORBIDDEN** · no Soft-Frozen / stitch ballot invented.

Label: `LIVE_PATH_CODEREVIEW_2026-09-07__P0_ZERO_FILL__T1_NAT_GAP__SF_HEALTHY`

---

## Verdict

| Area | Grade | Notes |
|---|---|---|
| Soft-Frozen FIN clip `[0.50, 0.95]` | **HEALTHY** | Prior P0 renormalize fix still holds; live targets + signals in band |
| Exact T+1 (valid dates) | **Mostly HEALTHY** | Same-bar hard-fail on write; empty/missing schema fail-closed in QC |
| Exact T+1 (corrupt dates) | **P1 NEW** | NaT / blank dates fail-open as `exact_t1_ok=True` |
| append_immutable / no history rewrite | **HEALTHY** | Key hit → skip; audit date skip; state JSON rewrite is expected |
| E22 field persistence | **HEALTHY (tip)** | `nav.e22_version` tip + `portfolio_state.e22_books_version` present; history NaN rows expected |
| Live fill cash path | **P0 NEW** | BUY-before-SELL + qty=0 fills burn `order_id` (4 live hits) |
| Crash / partial-write recovery | **P1 NEW** | Fills/div CSVs append before `portfolio_state` write |
| Missing dividend file | **P1 latent** | `load_dividend_events` returns `[]` (silent) vs coding-standards fail-closed |
| Soft-Frozen / stitch governance | **KEEP / FORBIDDEN** | No flip recommended or implied |

**Overall:** Soft-Frozen envelope and happy-path Exact T+1 remain sound after earlier fixes. Live books are **not** fully healthy: zero-qty fills already present in `forward/e21/fills.csv` while `e21_qc` stays **PASS** (fail-open on that class).

Current tip: `last_date=2026-09-07`, `e21_qc` PASS, Soft-Frozen signal FIN ∈ `[0.66, 0.86]`.

---

## P0 — Live correctness (NEW — not fixed in prior reviews)

### L1 Zero-qty BUY fills permanently cancel orders (BUY-before-SELL)

- **Where:** `scripts/e21_forward_pipeline.py` ~184–213 (pending fill loop + `append_immutable` on fills)
- **Bug:** Pending fills iterate CSV order. Financial **BUY**s run before Telecom **SELL**s, so cash is depleted mid-basket; BUY qty is clamped with `max(0, int(cash / …))`. A **qty=0** fill is still written with `fill_id == order_id`, so the order never retries.
- **Live evidence (already in ledger):**

  | fill_id | order qty | fill qty | fill_date |
  |---|---:|---:|---|
  | `2026-09-01-5880-BUY` | 754 | **0** | 2026-09-02 |
  | `2026-09-02-5880-BUY` | 762 | **0** | 2026-09-03 |
  | `2026-09-03-5880-BUY` | 913 | **0** | 2026-09-04 |
  | `2026-09-04-5880-BUY` | 776 | **0** | 2026-09-07 |

  Same-day pattern: FIN buys → `5880` qty 0 → TEL sells free cash → other buys. End-of-day cash was still ~36k–63k on those sessions.
- **QC gap:** `e21_qc.py` does not check `quantity > 0`; status remains PASS.
- **FIXED already?** **No** (not in `PROJECT_CODE_REVIEW_2026-09-06` / landmine rounds).
- **Recommended action (forward-only; do not rewrite fills history):**
  1. Process **SELL before BUY** (or net cash before buys).
  2. **Never** append a fill with `quantity <= 0`; leave order pending (or write a separate reject ledger that does not consume `fill_id`).
  3. Add QC check `fills_positive_qty` → fail-closed.
  4. Do **not** stitch / Soft-Frozen-flip to “fix” underweights.

---

## P1 — Fail-closed / recovery (NEW)

### L2 Exact T+1 NaT / blank dates fail-open

- **Where:** `scripts/e21_qc.py` `exact_t1_from_fills` ~45–55; pipeline audit ~217–222 uses the same `fill_dt <= sig` predicate on in-memory rows.
- **Bug:** Prior P1 fixed **missing columns** / empty fills. **Corrupt date values** still pass: pandas `NaT <= Timestamp` is False, so blank/`NaT` signal dates yield `same_bar_fills=0`, `exact_t1_ok=True`, `schema_ok=True`.
- **Repro:** `exact_t1_from_fills` on rows with `signal_date=''` or `None` → `exact_t1_ok=True`.
- **FIXED already?** **Partial** — L2 schema/empty from 2026-09-06 review is still green; **NaT path is new residual**.
- **Recommended action:** Fail if `sig.isna().any()` or `fill_dt.isna().any()` (and treat unparseable strings as fail). Surface `reason=fills_dates_unparseable`.

### L3 Non-atomic fill/div append vs `portfolio_state`

- **Where:** `e21_forward_pipeline.py` fills append ~212–213, dividends ~258–275, state write ~347–356.
- **Bug:** If the process dies after `fills.csv` / `dividends_applied.csv` append but before `portfolio_state.json` write, rerun skips those ids/keys (immutable hit / skip set) and **does not** re-apply position/cash effects → permanent ledger desync.
- **FIXED already?** **No**.
- **Recommended action:** Fail-closed preflight: positions/cash must reconcile to fills + dividends since `last_date`, or write state before marking fills applied (transactional temp+rename). Prefer detect-and-halt over silent continue.

### L4 Missing dividend events file is silent empty

- **Where:** `scripts/e22_dividend_accounting.py` `load_dividend_events` ~115–116 (`if not path.exists(): return []`); live call `e21_forward_pipeline.py` ~244.
- **Bug:** Coding standards §1: missing live data → hard fail. Missing path currently applies **no** dividends with no error.
- **FIXED already?** **No** (latent; `data/dividend_events/e22_dividend_events.csv` exists today).
- **Recommended action:** Live pipeline: missing/unreadable dividends path → `SystemExit`. Keep research opt-in only behind an explicit flag if needed.

---

## P2 — Persistence / QC coverage gaps

### L5 `nav.e22_version` historical NaNs; QC does not assert tip field

- **Where:** live `forward/e21/nav.csv` (10/11 rows NaN `e22_version`, tip `2026-09-07` = `E22_v2s_tw`); `e21_qc.py` has **no** `e22_version` / `e22_books_version` check; state has `e22_books_version` + `e22_manifest`.
- **Notes:** Expected under `append_immutable` (no history rewrite). Gap6 “column present” is satisfied; tip persistence works.
- **FIXED already?** Field write path fixed earlier; **QC assertion still absent**.
- **Recommended action:** QC: require column present and **latest** `nav.e22_version` non-null and equal to `DEFAULT_BOOKS_VERSION` (or state `e22_books_version`). Do not backfill old rows.

### L6 Partial cash fills burn residual size

- **Where:** same fill loop as L1 (`q = max(0, int(cash/…))` then fill_id consume).
- **Notes:** Related to L1; non-zero partials also prevent remainder retry. Live has additional partials beyond the four zeros.
- **Recommended action:** After sell-first cash path, either leave residual quantity pending under a new order id policy or document intentional “fill-what-you-can-and-cancel” as Soft-Frozen E18 semantics (today it is silent).

### L7 Provisional par fallback vs “missing par → hard fail”

- **Where:** `e22_dividend_accounting.py` `par_for_code` ~82–86.
- **Notes:** `E22_v2s_tw` design uses provisional 10 when table miss; DEFAULT live books depend on this. Tension with coding-standards wording, not a Soft-Frozen clip issue.
- **Recommended action:** Document as intentional DEFAULT exception, or fail-closed when live code lacks `verified_par_twd`.

### L8 Recon `drop_duplicates(..., keep="last")`

- **Where:** `e21_live_vs_paper_recon.py` ~37 (research/ops only, `live_wire: false`).
- **Notes:** Could mask duplicate live dates if QC bypassed; does not rewrite `forward/e21`.
- **Recommended action:** Prefer fail if live nav dates duplicate; keep Soft-Frozen untouched.

---

## Already fixed in prior reviews (still green)

| ID | Sev (then) | Item | Status now |
|---|---|---|---|
| Prior L1 | P0 | Soft-Frozen clip-then-`/sum` FIN breach → box∩simplex projection | **Still fixed** — `apply_soft_frozen_clips`; 5k random vectors 0 breaches; live targets FIN≥0.58 |
| Prior L2 | P1 | Empty fills / missing date **columns** Exact T+1 fail-open | **Still fixed** for those cases; see NEW L2 for NaT values |
| Prior L3 | P1 | Ops alert silent when `exact_t1_ok` missing | Out of this file set; not re-broken by live scripts reviewed |
| QC ownership | P1 | Pipeline stomped `qc_status.json` | **Still fixed** — pipeline writes `pipeline_t1_audit.json` only |
| Path gate | P2→closed | Canonical `forward/e21` resolve equality | **Still fixed** |
| Universe | P2→closed | `FIN`/`TEL` import from soft-frozen base | **Still fixed** |
| E22 override | — | `--confirm-e22-version-override` | **Still fixed** |

---

## Schema expectations (`forward/e21`)

| Artifact | Expectation | Observed 2026-09-07 |
|---|---|---|
| `signals.csv` | Unique monotonic dates; `e16_*` sum≈1; FIN ∈ `[0.50,0.95]` | OK (QC PASS) |
| `nav.csv` | Unique monotonic dates; positive NAV; tip `e22_version` | OK tip; 10 legacy NaN version cells |
| `orders.csv` / `fills.csv` | Unique ids; fills ⊆ orders; Exact T+1 dates | Dates OK; **qty=0 fills present** |
| `portfolio_state.json` | `cash`, `positions`, `last_date`, `e22_books_version`, `e22_applied_keys`, `e22_manifest` | Present (`E22_v2s_tw`) |
| `qc_status.json` | Owned by `e21_qc.py` | PASS (misses L1/L2) |
| `pipeline_t1_audit.json` | Pipeline-only T+1 audit | Present; `owns_qc_status: false` |
| `audit_chain.jsonl` | Unique dates; hash links | OK |

---

## Explicit non-goals / honesty

- No Soft-Frozen clip change, DEFAULT change, or stitch recommendation.
- No invented remediation that rewrites `forward/e21` history.
- Soft-Frozen + valid-date Exact T+1 paths are **honestly healthy** post prior P0/P1 fixes.
- Live execution path is **not** honestly healthy until L1 (zero-fill / sell-first) is fixed forward-only and QC fail-closes on it.

## Suggested verification after fix

```bash
PYTHONPATH=scripts python3 scripts/e21_qc.py
# after patch: assert no new quantity<=0 fills; NaT dates → FAIL
python3 -c "import pandas as pd; f=pd.read_csv('forward/e21/fills.csv'); assert (f.quantity>0).all()"
```
