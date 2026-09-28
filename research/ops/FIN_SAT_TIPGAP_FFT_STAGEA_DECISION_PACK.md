# FIN_SAT_TIPGAP_FFT_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T13:35:42Z`
Status: **FFT_SIGNAL** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_TIPGAP_FFT_STAGEA_CHARTER.md`
Screen: `FIN_SAT_TIPGAP_FFT_STAGEA_SCREEN.md`
Parents: 0k9i tip-gap · register **0k9j**

## Verdict

**`FFT_SIGNAL`**

## Reading

- **日頻 `rel`：近白噪音**（最大功率占比 ~0.5%，峰在 2–4 日）→ 對原始 tip-gap 做 FFT **挖不出**交易用振盪器。
- **平滑後** `trail_rel_21/63`／`trail_drag`：能量在 **~85／128／256 交易日**（約 4–6／6／12 個月）。部分來自平滑低頻偏置，但 bandpass lag-1 IC 過 gate：
  - 256d IC **+0.13**
  - 128d IC **−0.21**
  - 85d IC **−0.38**
- **月聚合**：~2.5 月／~11 月弱峰（~4%）。
- **Tip 窗** `trail_rel_63` ~121d 占比很高 → 短窗+平滑偽強，勿單信。

**實務：** FFT 對 raw gap 沒用；對平滑相對軌跡可提示 **四季～半年** 帶通相位作輔助。  
**不能取代** 0k9i 時域領先（`r0050_63`／Crisis／SELL）。若用頻域，預註冊 85–128td 帶通與時域 AND，禁止再對日頻 rel 掃峰。

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. FFT_SIGNAL ≠ observe／live — 僅診斷；不單靠振盪器切換
4. Prefer 0k9i time-domain + optional 85–128td bandpass assist · no year-switch

Label: `FIN_SAT_TIPGAP_FFT_STAGEA_DECISION_PACK_2026-09-28__FFT_SIGNAL__NO_LIVE`
