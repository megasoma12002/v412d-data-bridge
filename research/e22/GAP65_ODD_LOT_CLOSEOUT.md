# Gap 6.5 Odd-Lot Closeout

Date: 2026-09-04  
Branch: `cursor/e22-v2s-cil-d049`  
Status: **CLOSED as research** — named TW books landed; default unchanged until explicit promote.

## Decision (locked for this workstream)

| Item | Decision |
|---|---|
| Formal float books | Keep **`E22_v2s`** as current default |
| Taiwan practice apply | Named **`E22_v2s_tw`**: floor + **par NT$10** CIL, 元以下捨去 |
| Market-mark CIL | **`E22_v2s_cil`** = research sensitivity only (overstates cash when P≫par) |
| Board-lot 1000 | **Not** formal books (TW 零股 allows 1–999) |
| 拼湊 / 劃撥費充抵 | Deferred optional haircut |
| Live history | **Do not rewrite** |
| Exact T+1 | Unchanged |

## Evidence

| Variant | CAGR vs v2s | CIL cash | End dust |
|---|---:|---:|---:|
| `E22_v2s` | — | 0 | 2.20 |
| `E22_v2s_cil` (close) | ≈ −0.0005 pp | ~392 | 0 |
| `E22_v2s_tw` (par) | ≈ −0.0005 pp | **153** | **0** |

Legal/practice: 公司法 §240 + issuer 面額折現；證交所零股辦法 ≠ 強制整張持倉.

## Promote path (separate, not this closeout)

To make TW practice the live default:

1. Explicit governance approval to set `DEFAULT_BOOKS_VERSION = E22_v2s_tw`
2. Forward cutover only (idempotent keys); no historical NAV rewrite
3. One-line ops note in E21 / formal-books doc

## Artifacts

- `research/e22/TW_ODD_LOT_APPLY.md`
- `research/e22/E22_V2S_CIL_FORMAL.md`
- `scripts/e22_dividend_accounting.py` (`E22_v2s_tw`, `E22_v2s_cil`)
- `repro/e22-tw-odd-lot-apply/`, `repro/e22-v2s-cil-historical-recompute/`

## Gap #6 remainder (out of scope here)

6.1–6.3 receivable / pay-date / div tax → still sandbox.  
6.6 board-lot live → challenger only.
