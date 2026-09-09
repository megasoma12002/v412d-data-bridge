# Telecom Within-Sleeve Async — Decision Pack (FIN-parallel)

Date: 2026-09-09  
Human: **「電信三檔也做跟金融股一樣拆開的研究」**  
Status: **STOP (async / KD path)** — keep live **`TEL_EQUAL`**  
Soft-Frozen **FINBAND KEEP** · FIN **KD_OPT KEEP** · live wire **false**

## What was run (FIN-parallel)

| Step | Artifact | Result |
|---|---|---|
| Stage D timing | `TELECOM_WITHIN_SLEEVE_ASYNC_STAGE_D.md` | **STOP** — all held-out ≤ 0 (best MIX_L75-analogue **−0.045**, tip PASS) |
| PRE_EXDIV_KD summer grid (54) | `TELECOM_PRE_EXDIV_KD_OPTIMIZE.md` | **STOP** — **0 coexist**; best `TEL_KD_MAY15_AUG15_Klt25_T10` held-out **−0.376**, tip PASS |

Context: Financial held at live **KD_OPT**; capital **500M**; Telecom cash-ex mostly **Jun–Aug**.

## Contrast — prior pack Stage C (not this ballot)

@ 500M pack policies still show lift vs EQUAL (`TEL_DIVERSIFY_PACK` ~+0.33) under older FIN=`EQUAL` isolate.  
That is **lot-packing**, not FIN-style async timing. Not auto-promoted; optional later ballot only.

## Binding

1. Live Telecom within-sleeve stays **`TEL_EQUAL`**.  
2. Do **not** open Telecom KD / RS_EXDIV live cutover from this evidence.  
3. Soft-Frozen / FIN KD_OPT unchanged.  
4. Optional later: reopen **pack** cutover (`TEL_DIVERSIFY_PACK`) as a **separate** ballot — not this async line.

## Human replies (optional)

```
KEEP live TEL_EQUAL
```

```
OPEN telecom pack cutover ballot: TEL_DIVERSIFY_PACK
```

(Async/KD line needs new positive evidence before any ACCEPT.)

## Label

`TELECOM_WITHIN_SLEEVE_ASYNC_DECISION_2026-09-09__STOP__KEEP_TEL_EQUAL`
