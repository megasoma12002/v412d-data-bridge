# E22_v3 withholding — resident / non-resident note (sandbox)

Date: 2026-09-06 · **amended 2026-09-20**  
Status: **SANDBOX RESEARCH NOTE** — Soft-Frozen **KEEP** · live DEFAULT **`E22_v3_recv_pay_effdelay` (TAX0)** · **no tax promote**  
Related: `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · `E22_V3_TAX_RECV_STAGE_B_STATUS.md` · register #6b

## Purpose

Stage B has sealed evidence for **flat** sandbox haircuts (`tax10` / `tax20`).  
Those flats are **sensitivity probes**, not Taiwan resident law. This note records human decisions and the **statutory resident convention** before any tax DEFAULT promote.

## Human decisions recorded

| Topic | Decision | When | Source |
|---|---|---|---|
| Holder residency | **本國居住者（本國人）** | 2026-09-20 | Human ops message |
| Modeling principle | **參考本國人慣例計算** — use TW **domestic resident** dividend-income rules; do **not** treat non-resident withholding / treaty tables / sandbox `tax10`/`tax20` as the resident rule | 2026-09-20 | Human ops message |

## TW domestic resident convention (statutory — for modeling reference)

For **personal** Taiwan-resident holders, cash dividends from domestic companies follow **所得稅法** dividend regime since 107 年度（二擇一）:

| 方式 | 慣例規則（摘要） | 法源／說明 |
|---|---|---|
| **合併計稅** | 股利併入綜合所得；另按股利×**8.5%** 計可抵減稅額（每申報戶上限 **8 萬**） | 所得稅法股利所得規定；財政部／Invest Taiwan 說明 |
| **分開計稅** | 股利不併入綜合所得，按全戶股利合計 **28%** 單一稅率分開計算稅額後併報 | 同上（法定 28%） |

重要（跟帳本怎麼寫有關）：

1. 這是 **年度結算申報** 的個人所得稅選擇，**不是** 券商在除息當日固定扣 10%/20% 那種非居住者扣繳模型。  
2. 因此 live **TAX0**（組合 NAV 先記稅前現金）本身也是常見研究／簿記慣例：稅在年終申報層處理，不進日頻 NAV。  
3. Sandbox `E22_v3_tax10` / `tax20` = flat haircut **≠** 上表本國人慣例；**不可**因「本國人」直接把 tax10/20 推成 DEFAULT。

Cite pointers (ops, not legal advice): 所得稅法股利條文 · [Invest Taiwan 個人綜所稅／股利](https://investtaiwan.nat.gov.tw/showPage?lang=cht&menuNum=9&search=56) · 財政部優化說明（合併 8.5% 抵減／分開 28%）。

## What the sandbox does today (unchanged)

| Version | Cash timing | Withholding model |
|---|---|---|
| `E22_v3_tax10` / `tax20` | Cash on ex | Flat 10% / 20% of gross (**not** resident law) |
| `E22_v3_recv_pay_tax10` / `tax20` | Receivable on ex (net); cash on pay | Same flat net |

## Promote gate checklist

| Topic | Status | Promote gate |
|---|---|---|
| Holder residency | **DECIDED** — 本國人 | ✓ |
| Modeling principle | **DECIDED** — 參考本國人慣例（二擇一框架；非 tax10/20） | ✓ |
| Treaty overlays | **N/A** for resident-only v1 | Confirm waive line |
| **Which resident method to encode in books** | **OPEN** — see ballot below | Must pick one named rule |
| Timing in ledger | **OPEN** — tax outside NAV (TAX0) vs accrue on pay/ex vs annual stub | Match chosen method |
| Refunds / credits | **OPEN** if modeling 8.5% 抵減 / 溢繳 | Yes/No + fields |
| Issuer exceptions | **OPEN** — ETF／特殊配息是否同一規則 | Include/exclude |

**`promote_ready=false`** until the **books method** ballot below is chosen (and timing/refunds/exceptions filled).

## Next human ballot (pick one — tax books only)

| Ballot | Meaning for Soft-Frozen books | Notes |
|---|---|---|
| **A. KEEP TAX0** | Live stays tax-pre; resident tax stays **outside** daily NAV (慣例：年終申報) | Matches current Stage-E; **recommended default** unless after-tax NAV is required |
| **B. Named `…_div28`** | Model **分開計稅 28%** haircut on cash dividends (conservative large-holder proxy) | New sandbox id; **not** tax10/20; needs timing (ex vs pay vs year-end stub) |
| **C. Named merge-credit** | Model **合併計稅** + 8.5% credit (cap 8 萬／戶) | Needs household / other-income assumptions — usually **too heavy** for single strategy NAV |

This residency／慣例 note **alone** does **not** ACCEPT B or C.

## Non-actions

- No tax DEFAULT flip · no Soft-Frozen flip · no `forward/e21` rewrite  
- Do **not** map「本國人慣例」→ `tax10` / `tax20` DEFAULT

## Label

`E22_V3_WITHHOLDING_RESIDENT_NOTE__DOMESTIC_CONVENTION_2026-09-20__PROMOTE_READY_FALSE`
