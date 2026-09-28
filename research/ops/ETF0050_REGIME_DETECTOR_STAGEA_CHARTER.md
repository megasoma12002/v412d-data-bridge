# ETF 0050 regime × local detector Stage A — paper

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · β clip **KEEP** · no live wire  
Parents: `1d` hard quality **`TIP_BLOCK`** · `1e` soft×extreme **`TIP_BLOCK`** · `1c` ASYMM Bull densify **`CAGR_SOFT`** (do **not** reopen clip densify)

Human intent (normalized):

```
OPEN Stage A: 0050 多空都做 · (A) live regime 閘 Δw · (B) 新 0050 多空偵測器閘 Δw · tip-safe + CAGR↑ · KEEP clip · paper only
```

Label: `ETF0050_REGIME_DETECTOR_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why

Prior Δw quality / soft / extreme grids tip-blocked. Live already has Bull/Bear/Crisis/Sideways priors (clip mass path). Untested: use that regime — or a **new 0050-local** bull/bear detector — as **Δw allow gates** (not raising `E` hi).

| Track | Mechanism |
|---|---|
| **REG** | Live Soft-Frozen regime string gates 0050 adds/cuts |
| **DET** | New detector on 0050 adj close (MA60 trend / MACD) gates Δw |

Belief: regime- or detector-conditional timing can buy lower / sell higher without densify.  
Risk: repeats ASYMM (Bull mass) or tip wall; MR vs trend cancel.

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen β clip · Exact T+1 · COOL · SELL_a75 | **KEEP** |
| ASYMM Bull **clip densify** | **CLOSED** |
| `1d`/`1e` identical MA/RET/soft/extreme grids | **CLOSED** — do not reopen |
| Live wire | **forbidden** |

## Mechanism

Hard allow/deny on intended 0050 Δw (residual → FIN+TEL). `damp=0` when fail.

**REG** uses live `regime` from Soft-Frozen twin (`Bull`/`Bear`/`Crisis`/`Sideways`).  
**DET** uses 0050-only features (independent of live regime label).

## Gates (HIT)

1. held CAGR↑ ≥ **+0.15pp** (chal − base)  
2. held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**  
3. tip YTD & 1y MDD↑ ≥ **0**  
4. 0050 BUY or SELL WR↑ H=21 ≥ **+0.5pp**

## Grid (finite ≤14)

| ID | Track | Buy allow | Sell allow |
|---|---|---|---|
| `CTRL_BASE` | ctrl | always | always |
| `REG_BUY_BULL` | reg | Bull | — |
| `REG_BUY_BULL_SIDE` | reg | Bull∨Sideways | — |
| `REG_SELL_BEAR_CRISIS` | reg | — | Bear∨Crisis |
| `REG_BOTH_TREND` | reg | Bull | Bear∨Crisis |
| `REG_BOTH_MR` | reg | Bear∨Crisis | Bull |
| `DET_BUY_MA60_UP` | det | close&gt;MA60 | — |
| `DET_BUY_MA60_DN` | det | close&lt;MA60 | — |
| `DET_SELL_MA60_DN` | det | — | close&lt;MA60 |
| `DET_SELL_MA60_UP` | det | — | close&gt;MA60 |
| `DET_BOTH_TREND` | det | &gt;MA60 | &lt;MA60 |
| `DET_BOTH_MR` | det | &lt;MA60 | &gt;MA60 |
| `DET_BUY_MACD_POS` | det | MACD hist&gt;0 | — |
| `DET_BOTH_MACD` | det | hist&gt;0 | hist&lt;0 |

## Verdicts

`REGIME_DETECTOR_HIT` · `WIN_SOFT` · `CAGR_SOFT` · `TIP_BLOCK` · `MDD_BLOCK` · `NO_EDGE`  
Even HIT → paper observe ballot only.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/etf0050_regime_detector_stagea.py
```

Artifacts: `research/ops/ETF0050_REGIME_DETECTOR_STAGEA_*` · `repro/etf0050-regime-detector-stagea/`
