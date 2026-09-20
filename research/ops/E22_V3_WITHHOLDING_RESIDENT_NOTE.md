# E22_v3 withholding — resident / non-resident note (sandbox)

Date: 2026-09-06 · **amended 2026-09-20**  
Status: **RESIDENT PATH CLOSED FOR TAX PROMOTE** — Soft-Frozen **KEEP** · live DEFAULT **`E22_v3_recv_pay_effdelay` (TAX0)**  
Related: `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · `E22_V3_TAX_RECV_STAGE_B_STATUS.md` · register #6b

## Purpose

Record human decisions for Taiwan **domestic resident** dividend-income modeling vs Stage B flat sandboxes (`tax10` / `tax20`).

## Human decisions recorded

| Topic | Decision | When | Source |
|---|---|---|---|
| Holder residency | **本國居住者（本國人）** | 2026-09-20 | Human |
| Modeling principle | **參考本國人慣例**（所得稅法股利二擇一框架；≠ sandbox tax10/20） | 2026-09-20 | Human |
| **Books method** | **A. KEEP TAX0** — dividend personal tax stays **outside** daily Soft-Frozen NAV（年終申報慣例） | 2026-09-20 | Human「A」 |

### Effect of ballot **A. KEEP TAX0**

- Live Stage-E **TAX0** is the **accepted** books tax posture for this cycle.  
- **No** DEFAULT promote of `E22_v3_tax10` / `tax20` / `recv_pay_tax*` from residency／慣例 notes.  
- Sandbox flat haircuts remain **research sensitivity only**.  
- Timing receivable path (`E22_v3_recv_pay_effdelay`) **unchanged**.  
- Re-open after-tax NAV books only with a **new** human ballot (would be former B/C or successor) + dedicated PR.

**`promote_ready` for after-tax tax\* DEFAULT = false / path not taken** (ballot A = keep TAX0).

## TW domestic resident convention (reference only under ballot A)

Statutory 二擇一（合併 8.5% 抵減／分開 28%）仍是納稅人年終選擇；在 ballot A 下 **不編碼進日頻帳本**。  
Cite: 所得稅法股利規定 · Invest Taiwan 綜所稅說明.

## Sandbox table (still open for research, not live)

| Version | Role | Live? |
|---|---|---|
| `E22_v3_tax10` / `tax20` | Flat sensitivity | **No** |
| `E22_v3_recv_pay_tax*` | Combined sensitivity | **No** |

## Non-actions

- No Soft-Frozen flip · no `forward/e21` rewrite · no silent tax haircut on tip  
- Do not interpret A as ACCEPT of tax10/20

## Label

`E22_V3_WITHHOLDING_RESIDENT_NOTE__BALLOT_A_KEEP_TAX0_2026-09-20`
