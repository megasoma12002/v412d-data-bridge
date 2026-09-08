# E45 Novel Strategy Screen — Decision Pack

Date: 2026-09-08  
Status: **RESEARCH DONE — no tip-clean Soft_A beater**  
Ballot: 「請想新的策略」  
Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock unchanged

## Ideas tested (new, not Sideways/mix retunes)

| Strategy | One-liner |
|---|---|
| DD05_FULL_ELSE_SOFT | In ≥5% drawdown use full C35; else Soft_A |
| DD05_FULL_ELSE_OFF | Only defend in ≥5% drawdown |
| FXZ_RELOC_C35 | USDTWD stress as sole intensity |
| FXZ_GATE_SOFT_A | Soft_A only when FX confirms stress |
| FINONLY_SOFT_A | Soft_A timing, relocate FIN only |
| SOFT_A_NEST_A05 | Soft_A + mild blend-α nest |

## Result vs Soft_A (+0.83, tip PASS)

| Book | Held-out | Tip | Read |
|---|---:|---|---|
| Soft_A | **+0.83** | PASS | Still tip×score champion |
| DD05_FULL_ELSE_OFF | +0.38 | PASS | Tip-clean but weaker score |
| DD05_FULL_ELSE_SOFT | +0.17 | PASS | Weaker |
| FINONLY_SOFT_A | +0.12 | PASS | Weaker (less defense) |
| SOFT_A_NEST_A05 | +0.83 | PASS | No incremental lift vs Soft_A |
| FXZ_* | ≤0 / negative | mixed | FX-only sensor insufficient |

## Binding read

1. New ideas on available free series **did not** displace Soft_A under tip binding.  
2. Operational optimum remains **Soft_A tip twin + ungated C35 long-score twin**.  
3. Next true novelty needs **new data ingest** (rates/credit/breadth beyond proxy) or accept tradeoff.

Artifacts: `E45_NOVEL_STRATEGY_SCREEN.md` · freeze · `scripts/e45_novel_strategy_screen_paper.py`
