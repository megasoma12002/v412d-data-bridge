# FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T13:40:20Z`
Status: **WAVE_LAP_SIGNAL** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_CHARTER.md`
Screen: `FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_SCREEN.md`
Parents: 0k9j FFT · 0k9i tip-gap · register **0k9k**

## Verdict

**`WAVE_LAP_SIGNAL`**

## Reading

- Wavelet daily top: `[{"period_tdays": 53.0, "power_frac": 0.02656}, {"period_tdays": 57.0, "power_frac": 0.0265}, {"period_tdays": 216.0, "power_frac": 0.02643}]`
- Wavelet trail top: `[{"period_tdays": 234.0, "power_frac": 0.09024}, {"period_tdays": 216.0, "power_frac": 0.08685}, {"period_tdays": 200.0, "power_frac": 0.07821}]`
- Wavelet tip-trail top: `[{"period_tdays": 320.0, "power_frac": 0.12733}, {"period_tdays": 115.0, "power_frac": 0.11008}, {"period_tdays": 107.0, "power_frac": 0.09821}]`
- Laplace trail peaks: `[{"sigma": 0.0, "omega": 0.02721, "period_tdays": 230.94, "mag": 13.201103, "mag_frac": 1.0}, {"sigma": 0.0, "omega": 0.03534, "period_tdays": 177.78, "mag": 9.028941, "mag_frac": 0.68395}, {"sigma": 0.0, "omega": 0.05466, "period_tdays": 114.95, "mag": 6.593851, "mag_frac": 0.49949}]`
- IC-gated: `[{"method": "wavelet", "series": "trail_rel_63", "feature": "ridge", "lag1_ic": -0.0558, "ic_gate": true}, {"method": "laplace", "series": "daily_rel", "feature": "osc_p230.94_s0.0", "period_tdays": 230.94, "sigma": 0.0, "lag1_ic": 0.0695, "ic_gate": true}, {"method": "laplace", "series": "daily_rel", "feature": "osc_p114.95_s0.0", "period_tdays": 114.95, "sigma": 0.0, "lag1_ic": 0.0475, "ic_gate": true}, {"method": "laplace", "series": "trail_rel_63", "feature": "osc_p230.94_s0.0", "period_tdays": 230.94, "sigma": 0.0, "lag1_ic": 0.0686, "ic_gate": true}]`

Use wavelet band 70–140td and/or Laplace damped oscillator as assist to 0k9i time-domain; do not replace r0050_63 / Crisis / SELL.

**Reading（精煉）：**
- 日頻 CWT 近乎平坦（~2.6%）→ 與 FFT 白噪音一致。
- Trail CWT／Laplace 主尺度 **~115／200–234 交易日**，與 0k9j 的 128／256 帶重疊；tip 窗另見 ~107–115d。
- Laplace 峰 **σ≈0** → 幾乎無指數衰減優勢，等價於傅立葉振盪，**沒有比 FFT 多出穩定阻尼極點**。
- IC 過門但偏弱（|IC|~0.05–0.07）≪ FFT 帶通（0k9j 曾到 −0.38）→ 小波／Laplace 作輔助確認尺度，**主預測仍用 0k9i 時域**。

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. Wavelet/Laplace = diagnosis/assist · not sole switch · not live
4. Prefer 0k9i time-domain + optional 70–140td wavelet band / damped osc · no year-switch

Label: `FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_DECISION_PACK_2026-09-28__WAVE_LAP_SIGNAL__NO_LIVE`
