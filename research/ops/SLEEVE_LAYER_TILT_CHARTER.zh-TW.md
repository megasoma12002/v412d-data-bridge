# Sleeve 層 tilt — 研究憲章（paper）

日期：2026-09-10  
狀態：**OPEN／僅 paper**  
人類：**直接起草 sleeve-layer tilt research charter**（建議順序②；Soft-assist observe 繼續）  
先驗證種：**`SLEEVE_BELOW_MA60_a01`**（先前 soft/TEL/sleeve screen tip-clean 勝 live）  
Soft-Frozen **clips KEEP** · live **KD_OPT／TEL_EQUAL KEEP** · Soft-assist observe **不動** · E45 **OFF**

## 在問什麼

用 **sleeve NAV 指標**（如收盤 &lt; MA60）去 **加減 Soft-Frozen router score**，再 clip／blend 出新的 sleeve 權重，能否 tip-clean 勝過或共存於 **`LIVE_STACK`**？

**不做：** Soft-assist 名稱分數 · 改 KD · 改 TEL within-sleeve · 翻 Soft-Frozen 上下限 · 乾粉 · E45 stitch。

## 為何獨立憲章

- Soft-assist ballot **刻意排除** sleeve tilt。  
- 致動器不同：動的是 **sleeve 權重**，不是 FIN 內名稱分數。  
- Clips 箱體不變；只動 score → cand。

## 機制（摘要）

`score' = score + sign·α·signal` → Soft-Frozen clip + blend → 模擬時 **KD_OPT + TEL_EQUAL** 不變。  
預設：低於趨勢／超賣 **+boost**；高於趨勢／超買 **−dampen**。

## Stage A

- 對照：`LIVE_STACK`  
- 種子：`SLEEVE_BELOW_MA60_a01`（α=0.10）  
- 有限網格：訊號 ∈ {BELOW_MA60, RSI14_LT30, MOM20_NEG, 可選 MA40/MA120} × α ∈ {0.05,0.10,0.15,0.20} · ≤~24 books  
- 產出 tip／heldout／sealed；總評 `NO_LIFT` / `BEATS_LIVE` 等  
- 有 tip-clean lift → 另開 observe ballot；否則 STOP

## 非動作

不上 Soft-Frozen／KD／TEL／Soft-assist／E45；不與 Soft-assist 自動疊加。

英文全文：`SLEEVE_LAYER_TILT_CHARTER.md`
