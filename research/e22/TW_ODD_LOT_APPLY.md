# How to Apply Taiwan Odd-Lot Rules to E22 Books

> **Note (2026-09-05):** Live DEFAULT is now `E22_v2s_tw`. Any `default_remains: E22_v2s` / “default stays E22_v2s” language below is **historical research context**, not current live wiring.


Generated: `2026-09-04T18:26:12.109787+00:00`

**Research.** Default stays `E22_v2s`. No live history rewrite.

## Taiwan rule map → E22

| TW concept | Practice | E22 apply | Status |
|---|---|---|---|
| 不足一股畸零股（公司法 §240） | 面額折現（通常 NT$10），元以下捨去；可拼湊整股；剩餘洽特定人 | `E22_v2s_tw: floor(shares_gross); cash += floor(frac × 10)` | IMPLEMENTED_NAMED_VERSION |
| 零股交易 1–999 股（證交所零股辦法） | 可持有與買賣非整千股；股利按股數同權 | `Keep lot_size=1 fills; do NOT force board_lot_1000 in formal books` | KEEP_AS_IS |
| 整股 1000（主盤交易單位） | 主盤委託單位；非持股必須為 1000 倍數 | `E18 capacity challenger only (separate from CIL)` | CHALLENGER_ONLY |
| 拼湊整股視窗 / 劃撥費充抵 | 股務作業；未拼湊才折現；款常充抵手續費→實領可近 0 | `Optional haircut sensitivity; not default formal books` | DEFER |
| 畸零股現金入帳時點 | 股務／發放作業（近 payment），非除權當日市價結算 | `Amount fixed at par; credit on stock_ex_date for TR continuity (optional E22_v3 pay-clock later)` | EX_DATE_AMOUNT_OK |

## Legal / practice anchors

- **公司法 §240**：盈餘以發行新股分派時，**不滿一股之金額，以現金分派之**。
- **發行人公告慣例**：不足一股按**面額**折現（通常 NT$10；少數彈性面額），**計算至元、元以下捨去**；停止過戶前後可拼湊；剩餘洽特定人按面額認購。
- **證交所零股交易辦法**：零股以**1 股**為單位（1–999），與整股（1000）並行；**持股不必是 1000 倍數**。
- **現金增資／股票股利**皆可產生 <1 股畸零股；策略帳以除權（stock ex）事件套用同一 floor+CIL 規則。
- **市價落差爭議**：高價股按面額折現現金 ≪ 市值，屬制度結果；**正式帳必須跟面額慣例**，不可改用收盤市價 CIL 當 default（市價 CIL 僅 research `E22_v2s_cil`）。
- **散戶自保（股務，非策略 alpha）**：關注股代公告之拼湊整股期限；逾期未湊則強制面額現金，劃撥費充抵後實領可能近 0。
- **面額本身是資料**：不可假設全市場永遠 NT$10。彈性面額／面額變更需查表（`PAR_VALUE_LOOKUP_CHARTER.md`）；程式暫用 provisional `par=10` + `LOOKUP_NEEDED` 旗標，**未 verified 前不 promote default**。

## Named version ladder

| Version | Role |
|---|---|
| `E22_v2` | cash-only baseline |
| `E22_v2s` | formal float stock shares (current default) |
| `E22_v2s_cil` | research: floor + market-close CIL |
| `E22_v2s_tw` | TW-practice candidate: floor + par-10 CIL |

### `E22_v2s_tw` rule (recommended TW apply)

1. `shares_gross = shares × (1 + stock_dividend/10)`
2. `shares = floor(shares_gross)`
3. `cash += floor(frac × 10)`  ← par, yuan truncate

Cash dividends unchanged. Exact T+1 unchanged. `lot_size` stays 1 (零股 OK).

## Side-by-side sensitivity

| Variant | CAGR | MDD | End NAV | CIL cash | End dust |
|---|---:|---:|---:|---:|---:|
| E22_v2s | 13.7829% | -22.64% | 16,695,202 | 0.00 | 2.1956 |
| E22_v2s_cil | 13.7824% | -22.64% | 16,694,167 | 391.86 | 0.0000 |
| E22_v2s_tw | 13.7825% | -22.64% | 16,694,303 | 153.00 | 0.0000 |

### Deltas vs E22_v2s

- **E22_v2s_cil**: CAGR Δ `-0.0005` pp; end NAV Δ `-1,034.50`; CIL `391.86`; dust `0.0000`
- **E22_v2s_tw**: CAGR Δ `-0.0005` pp; end NAV Δ `-898.63`; CIL `153.00`; dust `0.0000`

## Decision

- Recommended TW apply: **`E22_v2s_tw`**
- Why: Matches Company Act §240 + issuer announcements (par cash for <1 share); clears fractional dust; does not over-constrain to board lots; NAV impact vs float v2s is negligible.
- vs market CIL: E22_v2s_cil overstates odd-lot cash vs TW practice when price >> par; keep as research sensitivity only.
- Live default: `KEEP_E22_v2s_UNTIL_EXPLICIT_PROMOTE_OF_TW`

Do not:

- Force lot_size=1000 as formal books
- Model 拼湊 window as portfolio alpha
- Use market-price CIL to “make shareholders whole” in formal books
- Silently replace E22_v2s without new version id
- Rewrite forward/e21 history

## Code

- `scripts/e22_dividend_accounting.py` — `E22_v2s_tw`, `tw_par_cil_cash()`
- `scripts/e22_tw_odd_lot_apply_research.py` — this study
- `scripts/e21_forward_pipeline.py` — `--e22-version E22_v2s_tw` selectable

## Artifacts

- `research/e22/TW_ODD_LOT_APPLY.json`
- `repro/e22-tw-odd-lot-apply/`

