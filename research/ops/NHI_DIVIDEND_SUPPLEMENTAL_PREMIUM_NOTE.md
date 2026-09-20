# NHI dividend supplemental premium (二代健保補充保費)

Date: 2026-09-20  
Status: **OPS / RESEARCH NOTE** — Soft-Frozen **KEEP** · **not** live DEFAULT  
Human: 2026-09-20「股利超過20000會需要繳補充保費」  
Related: `CASHFLOW_THREE_VIEWS.md` · ballot A `E22_V3_WITHHOLDING_RESIDENT_NOTE.md` (#267) · Stage-E TAX0  
Helper: `scripts/nhi_dividend_supplemental_premium.py`

## Why this matters for 現金流

Ballot **A KEEP TAX0** parked **所得稅** outside daily NAV（年終申報）.  

**補充保費 is a different clock:** when a single dividend payment **達 NT$20,000**, the payer **withholds at source** on pay day. Custody cash received can be **gross − 2.11%**, while Stage-E TAX0 books still credit **gross**. That gap is a real cashflow-fidelity item — not an income-tax promote.

## Rule (research snapshot)

| Item | Value | Source |
|---|---|---|
| Trigger | 單次股利給付 **達** NT$20,000（含現金＋股票股利計費基數） | 健保署補充保險費 |
| Rate | **2.11%** | 自 110-01-01；114 宣導仍用此率 |
| Base | 達門檻 → **全額** × 費率（不是只算超過 2 萬的部分） | 同左 |
| Cap | 單次計費上限 **NT$10,000,000** | 同左 |
| Timing | 發放／給付時 **就源扣繳** | ≠ 五月綜所稅 |

Example: cash div **20,000** → premium **422** → net cash **19,578**.  
Example: cash div **19,999** → premium **0**.

Stock-div portion for NHI is typically valued at **par** in withholder practice; cash path is what hits View C bank cash. Employer/自營業主「已列入投保金額」扣除 — **not** modeled here (retail / non-employer path).

## Live posture (this cycle)

| Surface | Posture |
|---|---|
| Stage-E DEFAULT `E22_v3_recv_pay_effdelay` | **TAX0 gross** — **no** NHI haircut wired |
| Sandbox `tax10`/`tax20` | Unrelated flat research haircuts — **do not** reuse as NHI |
| Promote NHI into live books | **CLOSED** until dedicated human ballot + PR |
| Cashflow ops | Treat NHI as **known custody vs books delta** on large single pays |

## Research helper

```bash
python3 - <<'PY'
from nhi_dividend_supplemental_premium import nhi_dividend_premium
for g in (19999, 20000, 100_000, 10_000_000, 10_000_001):
    r = nhi_dividend_premium(g)
    print(g, "→ premium", round(r.premium_twd, 2), "net", round(r.net_cash_twd, 2), "applies", r.applies)
PY
```

## Path to wire (future ballot only)

1. Confirm withholder base (cash-only vs cash+stock-par) against a real custody statement / 扣繳憑單.  
2. Sandbox books version e.g. `E22_v3_recv_pay_nhi211` (receivable gross or net — decide explicitly).  
3. Gap6 / dual-book compare vs TAX0 Stage-E.  
4. Dedicated ACCEPT — **not** auto from this note; **not** conflated with ballot A.

## Non-actions

- No Soft-Frozen flip · no tip history rewrite  
- No silent 2.11% haircut on live tip  
- Do not treat this as reopening after-tax `tax10`/`tax20` DEFAULT  
- Do not merge NHI into R4 T+2 trade settlement

## Label

`NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE__2026-09-20`
