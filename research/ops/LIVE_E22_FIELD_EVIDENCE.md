# Live E22 Field Evidence — Readiness Note


> **HISTORICAL / SSOT:** Soft-Frozen FIN was **[0.50, 0.95]** when this note was written.
> **Live today (2026-09-13+):** FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE_ADDITIVE** · **DH_dd06** · **500M**.
> See `research/ops/OPS_STATUS.md`. Do not treat `[0.50, 0.95]` below as current live.

Date: 2026-09-07  
Status: **EVIDENCE PRESENT**  
Soft-Frozen (at writing): **[0.50, 0.95]** · **live today [0.60, 0.90]** — no history rewrite.

## Evidence landed

| Field | Value |
|---|---|
| Forward commit | `61f188c` — `forward: update frozen E16 E18 E21 real-open ledgers` (2026-09-07T14:23:36Z) |
| GHA | schedule run started 2026-09-07T14:19:54Z (`v412f-forward-paper`) |
| Live asof | **2026-09-07** |
| `e22_books_version` | **`E22_v2s_tw`** |
| `e22_manifest` | present |
| `nav.csv` `e22_version` | **present** |
| `dividends_applied.csv` | absent (n=0 — no cash/stock apply this session; optional for Gap6 clear) |
| Gap6 KPI | **`kpi_ok=true`** · flags **[]** |

## Runbook (post-forward)

| Step | Result |
|---|---|
| `e21_qc.py` | **PASS** · Exact T+1 ok |
| `e22_gap6_fidelity_kpi.py` | **PASS** (exit 0) |
| `e22_data_quality_kpi.py` | **PASS** |
| `ops_alert_scan.py --report-only` | overall HIGH · CRITICAL **0** · **no** Gap6 HIGH codes |

Detail: `research/ops/E22_GAP6_VERIFY_2026-09-07_POST_FORWARD.md`

## Non-actions

Soft-Frozen KEEP · no stitch · no cutover · no history rewrite.  
Evidence ≠ L4 / FIN50 / BLEND / E45 promote license.

## History

- 2026-09-05: CODE READY / LIVE EVIDENCE PENDING  
- 2026-09-06: Sunday — still pending  
- 2026-09-07 pre-forward: still blocked on `nav.e22_version` (`E22_GAP6_VERIFY_2026-09-07.md`)  
- 2026-09-07 post-forward: **EVIDENCE PRESENT** (this note)
