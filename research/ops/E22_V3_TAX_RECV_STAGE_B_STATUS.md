# E22_v3 Tax / Receivable — Stage B Status

Date: 2026-09-05  
Ballot: **ACCEPT charter** (human 2026-09-05)  
Live DEFAULT: **`E22_v2s_tw`** (untouched)  
Soft-Frozen: **[0.50, 0.95] KEEP**

## Authorized by charter ACCEPT

| Version | Role | Status |
|---|---|---|
| `E22_v3_recv_pay` | Receivable on ex; cash on pay; TAX0; stock=TW | **SANDBOX OPEN** |
| `E22_v3_tax10` | Ex cash × 0.90; stock=TW | **SANDBOX OPEN** |
| `E22_v3_tax20` | Ex cash × 0.80; stock=TW | **SANDBOX OPEN** |
| `E22_v3_recv_pay_taxW` | Combined | **NOT STARTED** (needs each axis alone first) |

Code: `scripts/e22_v3_sandbox_books.py`  
Smoke: `research/ops/E22_V3_SANDBOX_SMOKE.md` (ok=true)

## Explicit non-actions

- No `DEFAULT_BOOKS_VERSION` flip  
- No Soft-Frozen flip  
- No `forward/e21` history rewrite  
- No E45 stitch (Item 3 still queued)  

## Next (still Item 2 research — not Item 3)

1. Broader sealed-window dual-book NAV compare vs `E22_v2s_tw`  
2. Write one withholding assumption (resident / non-resident) before any tax promote  
3. Human **promote** ballot later (second vote) if evidence warrants  

## Label

`E22_V3_TAX_RECV_STAGE_B_2026-09-05__OPEN`
