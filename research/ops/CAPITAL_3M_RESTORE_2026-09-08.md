# Capital restore to 3M — 2026-09-08

Human: **「先復原成原3M時的條件版本 然後再來研究電信不強制三家全買」**  
Soft-Frozen: **KEEP** · board-lot **1000 KEEP** · stitch **FORBIDDEN**

## Change

| | 15M (#118) | **Restored 3M** |
|---|---:|---:|
| `DEFAULT_CAPITAL` | 15_000_000 | **3_000_000** |
| Live tip NAV (2026-09-07) | ≈16.03M | ≈**3.16M** |
| TEL holdings | ≈8% | **0%** (equal-split + 整張) |
| cash | ≈0.04% | ≈**14.6%** |

Authorized wipe+replay `forward/e21` 2026-08-24→09-07 @ 3M + board-lot 1000.  
Dual-paper observe `--refresh-ledgers` @ 3M.

## Why TEL=0 again

Equal name-split: `sleeve_trade * nav / 3` per telecom code → each slice &lt; 1 張.  
Next research: **`TELECOM_WITHIN_SLEEVE_ALLOC_CHARTER.md`** (不強制三家全買).
