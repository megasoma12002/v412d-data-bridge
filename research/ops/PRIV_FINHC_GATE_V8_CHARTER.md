# 民股金控 — Gate V8 AND-confirm stack (max CAGR × min MDD) Paper Charter

Date: 2026-09-25  
Status: **CHARTER OPEN · Stage A READY** · Soft-Frozen live **KEEP** · live wire **false**  
Human binding (exact intent):

```
Maximize CAGR（held / sealed 分窗）
Minimize MDD（尤其 sealed）
宇宙：公股 R1 KEEP + 民股金控 新增機制（何時開、開多少、與公股如何共存）
Soft-Frozen live 不動直到明確 ACCEPT
```

Class: **A. Research / EXPERIMENTAL** · Soft-Frozen / live e21 flip = **Class D** later only  
Parent live: Soft-Frozen **F[0.60, 0.80] T[0.03, 0.35] E[0.00, 0.50]** + `KD_OPT` + `TEL_EQUAL` + `FUSE_ADDITIVE` + `COOL_c8_f50_d21`  
Capital **500M** · lot **1000** · Exact T+1 · E22 on extended pub+priv panel  
Baseline: **`BASE_LIVE_FUSE_COOL`** (Soft+Sleeve+COOL live twin)

Label: `PRIV_FINHC_GATE_V8_CHARTER_2026-09-25__STAGE_A_OPEN`

**Passing ≠ Soft-Frozen flip ≠ live e21 universe expand ≠ tip history rewrite.**

---

## Why V8 (not retune V7)

| Prior track | Verdict | Binding |
|---|---|---|
| Dollar-split / SF4 / 0b2 | **STOP** | sealed MDD 全軍覆沒 |
| 民股新機制 N1→V6 | **STOP** | 0 sealed coexist |
| Gate V7 single OR-family | **SOFT** · observe OPEN | 0 HIT · Bull+Side F05 near-flat · **do not expand V7 grid after sealed peek** |
| β densify clip flip | **LIVE** | 明確 **No 公+民** |

V8 is a **new mechanism**: FinPriv carve-out only when **ALL active confirms** are on (AND stack), not V7’s single-gate OR-family.

## Universe (research)

| Sleeve | Members | Live role |
|---|---|---|
| **FinPub** | `2880 2886 2892 5880` | **KEEP** live Financial R1 |
| **FinPriv（民股金控）** | `2884 2885 2890 2891 2881 2882` | research-only until Class D |
| Telecom | `2412 3045 4904` | live KEEP |
| 0050 | `0050` | live KEEP |

## Mechanism V8 — AND-confirm carve-out

Live Soft-Frozen stays a **3-sleeve** router. FinPriv is **not** a permanent 4th clip box.

Daily:

1. Compute Soft-Frozen Financial sleeve weight `w_fin` (live clips + FUSE/COOL on baseline twin).  
2. Evaluate **AND gate** = product of active confirms ∈ {0,1}.  
3. If gate=0 → Financial dollars **100% FinPub** (`KD_OPT`) — live twin.  
4. If gate=1 → carve `priv_frac` of Financial dollars to **FinPriv**; remainder FinPub.  
   - FinPriv within-sleeve ∈ `{EQUAL, PRIV_KD_MAY_Klt25_T15}` (same as V7).  
   - FinPub within-sleeve = live `KD_OPT`.

So: **何時開** = AND stack · **開多少** = `priv_frac` · **與公股共存** = carve-out of FIN sleeve only (TEL/0050 untouched).

### Confirm components (predeclared — do not expand after peek)

| Confirm | Opens when |
|---|---|
| Regime ∈ {`REG_BULL`, `REG_BULL_SIDE`} | Soft-Frozen regime == `Bull` / ∈ {`Bull`,`Sideways`} |
| Trend ∈ {`MA60_0050`, `MA120_0050`} | `0050` adj_close > MA60 / MA120 (causal) |
| Optional cool-full | COOL exposure == **1.0** (not defending) |

AND gate = **elementwise product** of selected component gates (regime × trend [× cool_full]).

### Grid (predeclared)

| Axis | Values |
|---|---|
| Regime × trend AND pairs | `BULL∧MA60`, `BULL∧MA120`, `BSIDE∧MA60`, `BSIDE∧MA120` (4) |
| `cool_full` | `{false, true}` → tag `_COOL1` when true |
| `priv_frac` | `{0.05, 0.08, 0.10}` |
| FinPriv within | `{EQUAL, PRIV_KD_MAY}` |

Hard cap: **≤ 48 challengers** + `BASE_LIVE_FUSE_COOL` control (= 4 × 2 × 3 × 2).

**Do not** retune / expand the V7 single-gate grid from this screen.

## Objective (binding — same as V7 HIT)

Windows: **heldout_2019_plus** + **sealed_2023_plus** (both gate) · tip YTD/1y observe.

1. **Minimize MDD first (especially sealed)**  
   - Hard: `sealed_mdd_improve_pp ≥ 0`  
   - Hard: `heldout_mdd_improve_pp ≥ −0.25`  
2. **Then maximize CAGR**  
   - HIT floor: held CAGR lift **≥ +0.20 pp**

Score (ranking among gate-clear books only):

```
score = 0.50 × (CAGR↑_held + CAGR↑_sealed)
      + 0.50 × (MDD↑_held + MDD↑_sealed)
      − 0.25 × max(0, −CAGR↑_held)
```

**HIT / coexist** (all required):

1. `tip_clean` — YTD + trailing_1y CAGR tip PASS  
2. `tip_mdd_ok` — YTD and 1y MDD↑ ≥ **−0.5 pp**  
3. `sealed_mdd_improve_pp ≥ 0`  
4. `heldout_mdd_improve_pp ≥ −0.25`  
5. `heldout_cagr_lift_pp ≥ +0.20`  
6. Soft-Frozen live constants untouched in this Stage A

| Verdict | Meaning |
|---|---|
| `PRIV_FINHC_V8_HIT` | ≥1 coexist book |
| `PRIV_FINHC_V8_SOFT` | sealed MDD OK + tip OK + held MDD near-flat, but CAGR floor fail |
| `MDD_BLOCK` | tip OK but sealed or held MDD gate fail |
| `NO_LIFT` | no tip-clean offense |

Even HIT → **paper observe ballot only**; live universe expand = separate Class D ACCEPT.

## Out of scope / WON’T

- Edit `e16_soft_frozen_base` live clips / tip membership  
- Retune / expand V7 single-gate grid after sealed peek  
- Retune exhausted N1–V6 / SF4 / dollar-split  
- Bundle Class D Soft-Frozen or e21 expand with Stage A  
- Broker live-write · Gate H auto-fuse · DH re-enable  
- Replace 公股 with 民股 (`#257` style)

## Stage plan

| Stage | Action | Exit |
|---|---|---|
| **A** | Run predeclared V8 AND grid · screen + decision pack | HIT → observe candidates; else SOFT / MDD_BLOCK / NO_LIFT |
| **B** | Dual-paper observe on winners only | Separate ballot |
| **D** | Live FinPriv membership / Soft-Frozen topology | Human **ACCEPT** only |

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/priv_finhc_gate_v8_stagea.py
```

Artifacts: `research/ops/PRIV_FINHC_GATE_V8_*` · `repro/priv-finhc-gate-v8-stagea/`

## Label

`PRIV_FINHC_GATE_V8_CHARTER_2026-09-25__STAGE_A_OPEN`
