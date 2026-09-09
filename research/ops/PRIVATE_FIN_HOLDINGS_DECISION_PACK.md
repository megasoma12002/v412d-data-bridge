# Private Financial Holdings (民營金控) — Decision Pack

Date: 2026-09-09  
Human: **「直接開 charter 並開跑」**  
Status: **STOP (Stage A)** — no positive held-out vs **`LIVE_PUB_KD`** · **0 coexist**  
Soft-Frozen **FINBAND KEEP** · FIN membership **公股 R1 KEEP** · FIN **KD_OPT KEEP** · Telecom **TEL_EQUAL KEEP** · live wire **false**

## What was run

| Step | Artifact | Result |
|---|---|---|
| Charter ACCEPT | `PRIVATE_FIN_HOLDINGS_CHARTER.md` | Paper-only; Soft-Frozen membership unchanged |
| Stage A re-screen @ 500M/lot1000 | `PRIVATE_FIN_HOLDINGS_RESCREEN.md` · `scripts/e16_private_fin_holdings_rescreen.py` | **STOP_NO_POSITIVE_HELDOUT_VS_LIVE_PUB_KD** |

Books vs baseline `LIVE_PUB_KD` (公股 R1 + `FIN_PRE_EXDIV_KD`):

| book | heldout score | tip_clean | coexist |
|---|---:|---|---|
| `LIVE_PUB_EQ` | −0.78 | yes | no |
| `ALL12_KD` | −1.69 | no | no |
| `ALL12_EQ` | −1.97 | no | no |
| `PRIV_KD` | −5.85 | yes | no |
| `PRIV_EQ` | −7.04 | yes | no |

Headlines: PRIV alone is materially worse on MDD; ALL12 gives back ~2.6–2.8 pp held-out CAGR and fails tip gates; no challenger scores > 0.

## Data caveats (directional only)

- Private OHLCV from TWSE-archive 12-stock build; `adj_close` ≈ `close`.  
- Dividend events CSV lacks private names → E22 incomplete for PRIV/ALL12.  
- Tip date coverage for private names ends ~2026-09-04 vs live Soft-Frozen through 2026-09-09 → tip name counts may be < universe size.

## Binding

1. Soft-Frozen Financial membership stays **公股 R1** (`2880/2886/2892/5880`).  
2. Do **not** expand live `e21` universe to 民營 / ALL12 from this screen.  
3. Do **not** open Stage B dual-paper observe (no tip-clean + held-out>0 coexist).  
4. Live FIN **KD_OPT** / FINBAND / TEL_EQUAL unchanged.

## Re-open trigger

New positive evidence under current stack (held-out > 0 **and** tip-clean vs `LIVE_PUB_KD`), ideally with private dividend panel complete — then new charter, not this pack.

## Label

`PRIVATE_FIN_HOLDINGS_DECISION_2026-09-09__STOP__KEEP_PUB_R1`
