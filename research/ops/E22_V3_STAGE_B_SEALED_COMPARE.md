# E22_v3 Stage B — Sealed-Window Dual-Book Compare

Generated: `2026-09-06T10:04:47.356207+00:00`
Status: **SANDBOX RESEARCH** — Soft-Frozen **KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · no promote

## Method

- Window: `sealed_2023_plus` from `2023-01-01`
- Constant holdings: 1000 shares × Soft-Frozen FIN `2880, 2886, 2892, 5880`
- Wealth = cash + receivable + marked equity
- Formal path: `E22_v2s_tw`
- Sandbox paths: `E22_v3_recv_pay` / `E22_v3_tax10` / `E22_v3_tax20`

## Results vs DEFAULT

| Version | Sandbox? | End wealth | CAGR | MDD | ΔCAGR pp | ΔMDD improve pp | End recv |
|---|:---:|---:|---:|---:|---:|---:|---:|
| `E22_v2s_tw` | N | 185405.15 | 17.58% | -10.85% | +nan | +nan | 0.00 |
| `E22_v3_recv_pay` | Y | 185405.15 | 17.58% | -10.85% | +0.00 | +0.00 | 894.40 |
| `E22_v3_recv_pay_tax10` | Y | 183646.13 | 17.26% | -11.19% | -0.32 | -0.34 | 804.96 |
| `E22_v3_recv_pay_tax20` | Y | 181887.11 | 16.93% | -11.54% | -0.64 | -0.69 | 715.52 |
| `E22_v3_tax10` | Y | 183646.13 | 17.26% | -11.19% | -0.32 | -0.34 | 0.00 |
| `E22_v3_tax20` | Y | 181887.11 | 16.93% | -11.54% | -0.64 | -0.69 | 0.00 |

## Governance

- Live DEFAULT remains **`E22_v2s_tw`** (untouched).
- Soft-Frozen FIN clip **[0.50, 0.95] KEEP**.
- Combined `recv_pay_taxW` still **NOT STARTED** (needs each axis alone first).
- No E45 stitch; no Soft-Frozen / DEFAULT flip; no retired-narrative reinvention.

## Withholding note

Tax sandboxes use a **flat haircut** (10%/20%) — resident/non-resident rule must be written before any promote ballot.

Label: `E22_V3_STAGE_B_SEALED_2026-09-06__DEFAULT_KEEP`
