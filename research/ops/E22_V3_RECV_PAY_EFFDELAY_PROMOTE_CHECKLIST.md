# E22_v3 Receivable / Effdelay — Stage-E Promote Checklist

Date: 2026-09-16  
Ballot: **ACCEPT Stage-E promote** — live DEFAULT → `E22_v3_recv_pay_effdelay`  
Soft-Frozen FIN clip / Exact T+1 / FUSE+DH: **KEEP**  
Preserved cash-on-ex: `E22_v2s_tw_effex` (CLI override + confirm)

Authority: `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · Stage B sealed compare · Gap #6.1/6.2

## Gates

| Gate | Status |
|---|---|
| Charter ACCEPT (Stage A/B unlock) | ✅ 2026-09-05 |
| Sandbox sealed compare (TAX0 recv_pay wealth ≈ formal) | ✅ `E22_V3_STAGE_B_SEALED_COMPARE.md` |
| Timing axis only (TAX0) — no flat tax promote | ✅ (tax10/20 stay sandbox) |
| Receivable identity: accrue on effective ex; clear on effective pay | ✅ `e22_v3_sandbox_books` |
| Typhoon / 封關 snaps (effdelay) | ✅ + MOPS overlay on pay |
| Forward-only; no `forward/e21` history rewrite | ✅ |
| Soft-Frozen clip / E45 stitch / broker live | **KEEP / not this PR** |
| Dedicated promote PR | **this PR** |

## Live wiring

| Piece | Change |
|---|---|
| `e22_dividend_accounting.DEFAULT_BOOKS_VERSION` | `E22_v3_recv_pay_effdelay` |
| `e22_books_apply.apply_books_for_date` | Router formal ↔ sandbox |
| `e21_forward_pipeline` | Persist `e22_receivables`; NAV = cash + recv + equity |
| `live_ledger.holdings` | Include receivable in NAV |

## Explicit non-actions

- Broker live write / `fill_port` flip  
- Dividend tax DEFAULT (resident note still DRAFTED)  
- Soft-Frozen FIN band flip  
- E45 stitch  

Label: `E22_V3_RECV_PAY_EFFDELAY_STAGE_E_PROMOTE_2026-09-16__ACCEPT`
