# 金融公 / 金融民 Dual-Sleeve — Decision Pack

Date: 2026-09-09  
Human: **「應該策略要把金融分成 金融公 金融民」**  
Status: **STOP (Stage A dollar-split)** — 0 coexist vs **`LIVE_PUB_KD`**  
Soft-Frozen **FINBAND KEEP** · live 公股 KD_OPT **KEEP** · live wire **false**

## Structure vs prior STOP

| Design | Result |
|---|---|
| PRIV-**replace** Financial names | STOP (MDD) — `PRIVATE_FIN_HOLDINGS` |
| **Dual** 公+民 dollar-split (this pack) | Still **STOP** — tip-clean but held-out score &lt; 0 |

Mechanism: Soft-Frozen Financial **weight** unchanged; dollars split `pub_share` → 公股 KD_OPT, rest → 民營 EQUAL/KD.

## Stage A grid (best → worst held-out)

| book | pub_share | heldout score | MDD↑pp | CAGR Δpp | tip |
|---|---:|---:|---:|---:|---|
| `DUAL_P85_KD` | 0.85 | −2.54 | −1.55 | −1.99 | clean |
| `DUAL_P75_KD` | 0.75 | −3.61 | −2.37 | −2.49 | clean |
| `DUAL_P50_KD` | 0.50 | −4.19 | −2.72 | −2.94 | clean |

Pattern: adding 民營 **raises** held-out CAGR but **worsens** MDD enough that score = MDD↑ − 0.5·|CAGR| stays negative. More 民 → worse score.

## Binding

1. Live Soft-Frozen Financial membership stays **公股 R1 only**.  
2. Do **not** live-wire `FIN_DUAL_PUB_PRIV` or expand e21 to 民營 from this screen.  
3. Do **not** open Soft-Frozen **4-sleeve** cutover (needs new charter + independent clip evidence).  
4. Policy machinery `FIN_DUAL_PUB_PRIV` remains available for paper research.

## Strategic reading

「分成 金融公／金融民」is the right **research structure** (coexist, not replace).  
Under current Soft-Frozen **single Financial band + MDD-first score**, Stage A dollar-split does **not** beat live 公股 KD.

Re-open only with: tip-clean **and** held-out score &gt; 0, or a dedicated Soft-Frozen multi-sleeve clip charter.

## Label

`FIN_PUB_PRIV_DUAL_SLEEVE_DECISION_2026-09-09__STOP__KEEP_PUB_R1`
