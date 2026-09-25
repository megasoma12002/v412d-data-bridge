# 民股金控 — max CAGR × min MDD（Gate V7）Paper Charter

Date: 2026-09-25  
Status: **CHARTER OPEN · Stage A DONE → `PRIV_FINHC_SOFT`** · Soft-Frozen live **KEEP** · live wire **false**  
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

Label: `PRIV_FINHC_CAGR_MDD_GATE_V7_CHARTER_2026-09-25__STAGE_A_OPEN`

**Passing ≠ Soft-Frozen flip ≠ live e21 universe expand ≠ tip history rewrite.**

---

## Why new (not retune)

| Prior track | Verdict | Binding |
|---|---|---|
| Dollar-split dual / SF4 clips / 0b2 並存 | **STOP** | sealed MDD 全軍覆沒 |
| 民股新機制 N1→V6 | **STOP** | 0 sealed coexist |
| 民營 native observe | **KEEP OBSERVE** | cutover BLOCKED · 非本 charter 並存路徑 |
| β densify clip flip | **LIVE** | 明確 **No 公+民** |

Research order step 4 was **DEFER** → this charter **OPEN**s it with a **new gate mechanism**, not the exhausted clip/damper grids.

## Universe (research)

| Sleeve | Members | Live role |
|---|---|---|
| **FinPub** | `2880 2886 2892 5880` | **KEEP** live Financial R1 |
| **FinPriv（民股金控）** | `2884 2885 2890 2891 2881 2882` | research-only until Class D |
| Telecom | `2412 3045 4904` | live KEEP |
| 0050 | `0050` | live KEEP |

## Mechanism V7 — gated carve-out（何時開 / 開多少 / 如何共存）

Live Soft-Frozen stays a **3-sleeve** router. FinPriv is **not** a permanent 4th clip box.

Daily:

1. Compute Soft-Frozen Financial sleeve weight `w_fin` (live clips + FUSE/COOL stack on baseline twin).  
2. Evaluate **gate** ∈ {0,1} (mechanisms below).  
3. If gate=0 → Financial dollars **100% FinPub** (`KD_OPT`) — live twin.  
4. If gate=1 → carve `priv_frac` of Financial dollars to **FinPriv**; remainder FinPub.  
   - FinPriv within-sleeve ∈ `{EQUAL, PRIV_KD_MAY_Klt25_T15}` (native observe champion).  
   - FinPub within-sleeve = live `KD_OPT`.

So: **何時開** = gate · **開多少** = `priv_frac` · **與公股共存** = carve-out of FIN sleeve only (TEL/0050 untouched).

### Gate families (predeclared — do not expand after peek)

| ID | Gate opens when |
|---|---|
| `REG_BULL` | Soft-Frozen regime == `Bull` |
| `REG_BULL_SIDE` | regime ∈ {`Bull`, `Sideways`} |
| `MA60_0050` | `0050` adj_close > MA60 (causal) |
| `MA120_0050` | `0050` adj_close > MA120 |
| `RS60_PRIV_GT_PUB` | EW PRIV 60d return > EW PUB 60d return |

### Size / policy grid

| Axis | Values |
|---|---|
| `priv_frac` | `{0.05, 0.10, 0.15}` |
| FinPriv within | `{EQUAL, PRIV_KD_MAY}` |

Hard cap: `priv_frac ≤ 0.15` (small satellite; not a second Soft-Frozen Financial).

**Controls**

- `BASE_LIVE_FUSE_COOL` — live twin (gate always off / priv_frac=0)  
- `ALWAYS_F10_EQ` — gate always on, `priv_frac=0.10`, EQUAL (sanity / upper offense)

Finite book count target: **≤ 32** challengers + 2 controls.

## Objective (binding)

Windows: **heldout_2019_plus** + **sealed_2023_plus** (both gate) · tip YTD/1y observe.

Dual goal, lexicographic:

1. **Minimize MDD first (especially sealed)**  
   - Hard: `sealed_mdd_improve_pp ≥ 0`  
   - Hard: `heldout_mdd_improve_pp ≥ −0.25` (near-flat tolerance; 0 preferred)  
2. **Then maximize CAGR**  
   - Report held + sealed CAGR lift pp  
   - Offense floor for **HIT**: held CAGR lift **≥ +0.20 pp**

Score (ranking among gate-clear books only):

```
score = 0.50 × (CAGR↑_held + CAGR↑_sealed)
      + 0.50 × (MDD↑_held + MDD↑_sealed)
      − 0.25 × max(0, −CAGR↑_held)   # penalize held CAGR loss only
```

**Coexist / HIT** (all required):

1. `tip_clean` — YTD + trailing_1y CAGR tip PASS  
2. `tip_mdd_ok` — YTD and 1y MDD↑ ≥ **−0.5 pp**  
3. `sealed_mdd_improve_pp ≥ 0`  
4. `heldout_mdd_improve_pp ≥ −0.25`  
5. `heldout_cagr_lift_pp ≥ +0.20`  
6. Soft-Frozen live constants untouched in this Stage A

| Verdict | Meaning |
|---|---|
| `PRIV_FINHC_HIT` | ≥1 coexist book |
| `PRIV_FINHC_SOFT` | sealed MDD OK but CAGR floor fail / tip soft |
| `MDD_BLOCK` | tip OK but sealed or held MDD gate fail (expected prior pattern) |
| `NO_LIFT` | no tip-clean offense |

Even HIT → **paper observe ballot only**; live universe expand = separate Class D ACCEPT.

## Out of scope / WON’T

- Edit `e16_soft_frozen_base` live clips / tip membership  
- Retune exhausted N1–V6 damper / SF4 clip / dollar-split grids  
- Bundle Class D Soft-Frozen or e21 expand with Stage A  
- Broker live-write · Gate H auto-fuse · DH re-enable  
- Replace 公股 with 民股 (`#257` style)

## Stage plan

| Stage | Action | Exit |
|---|---|---|
| **A** | Run predeclared V7 gate grid · screen + decision pack | HIT → observe candidates; else STOP / SOFT / MDD_BLOCK |
| **B** | Dual-paper observe on winners only | Separate ballot |
| **D** | Live FinPriv membership / Soft-Frozen topology | Human **ACCEPT** only |

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/priv_finhc_cagr_mdd_gate_v7_stagea.py
```

Artifacts: `research/ops/PRIV_FINHC_CAGR_MDD_GATE_V7_*` · `repro/priv-finhc-cagr-mdd-gate-v7-stagea/`

## Label

`PRIV_FINHC_CAGR_MDD_GATE_V7_CHARTER_2026-09-25__STAGE_A_OPEN`
