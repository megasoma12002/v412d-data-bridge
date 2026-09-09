# Private Financial Holdings (民營金控) — Decision Pack

Date: 2026-09-09  
Human: **「直接開 charter 並開跑」** → then **「民營缺完整股利／adj 資料 這些資料先補上」**  
Status: **STOP (Stage A)** — no positive held-out vs **`LIVE_PUB_KD`** · **0 coexist**  
Soft-Frozen **FINBAND KEEP** · FIN membership **公股 R1 KEEP** · FIN **KD_OPT KEEP** · Telecom **TEL_EQUAL KEEP** · live wire **false**

## What was run

| Step | Artifact | Result |
|---|---|---|
| Charter ACCEPT | `PRIVATE_FIN_HOLDINGS_CHARTER.md` | Paper-only; Soft-Frozen membership unchanged |
| Div + adj fill | `PRIVATE_FIN_DIV_ADJ_FILL.md` · `e22_fill_private_fin_div_adj.py` | E22 + adj + par for 8 private/R2 names |
| Stage A re-screen @ 500M/lot1000 (post-fill) | `PRIVATE_FIN_HOLDINGS_RESCREEN.md` | **STOP_NO_POSITIVE_HELDOUT_VS_LIVE_PUB_KD** |

Books vs baseline `LIVE_PUB_KD` (公股 R1 + `FIN_PRE_EXDIV_KD`) **after data fill**:

| book | heldout score | MDD↑pp | CAGR Δpp | tip_clean | coexist |
|---|---:|---:|---:|---|---|
| `LIVE_PUB_EQ` | −0.78 | −0.67 | −0.23 | yes | no |
| `ALL12_EQ` | −1.81 | −0.52 | +2.58 | no | no |
| `ALL12_KD` | −2.48 | −1.25 | +2.46 | no | no |
| `PRIV_KD` | −7.07 | −5.09 | −3.96 | yes | no |
| `PRIV_EQ` | −7.64 | −5.75 | −3.78 | yes | no |

Headlines (post-fill): PRIV alone has **higher** held-out CAGR (~+4pp) but **much worse** MDD (~−5pp) → score << 0. ALL12 still gives back CAGR and fails tip. **0 coexist**. Data gaps were not driving STOP.

## Data status

- Private OHLCV: TWSE-archive 12-stock build  
- Private `adj_close`: `data/market/private_fin_adjusted.csv` (FinMind factors)  
- Private dividends: merged into `e22_dividend_events.csv` (+ Yahoo payment backfill)  
- Par: all eight VERIFIED 10.0  
- Tip date coverage for private OHLCV may still lag live Soft-Frozen by a few sessions

## Binding

1. Soft-Frozen Financial membership stays **公股 R1** (`2880/2886/2892/5880`).  
2. Do **not** expand live `e21` universe to 民營 / ALL12 from this screen.  
3. Do **not** open Stage B dual-paper observe (no tip-clean + held-out>0 coexist).  
4. Live FIN **KD_OPT** / FINBAND / TEL_EQUAL unchanged.

## Re-open trigger

New positive evidence under current stack (held-out score > 0 **and** tip-clean vs `LIVE_PUB_KD`) — then new charter, not this pack.

## Label

`PRIVATE_FIN_HOLDINGS_DECISION_2026-09-09__STOP__KEEP_PUB_R1__POST_DIV_ADJ_FILL`
