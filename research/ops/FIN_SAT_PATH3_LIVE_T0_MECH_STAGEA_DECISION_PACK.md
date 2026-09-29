# FIN_SAT_PATH3_LIVE_T0_MECH_STAGEA_DECISION_PACK

Date: 2026-09-29 · Verdict: **`ORACLE_ONLY`**
Status: Soft-Frozen **KEEP** · global Exact T+1 **KEEP** · Path3 observe **KEEP** · cutover **BLOCKED** · no live · no fill-core edit

## Answer

Live 路径要吃到 Path3 tip，必须研究 **same-session fill carve-out**；
仅 T+1 open（0k9s hybrid）不够。

- Oracle same-bar: tipY↑ **2.7325** · held↑ 3.4758
- T1 open: tipY↑ **-8.4925** · tipClean=False
- Best MOC `MOC_F50`: tipY↑ **-4.7113** · held↑ 1.8244 · tipClean=False

## Live mechanism implication

1. 现役 `PaperOpenFillPort` / `_iter_pending` / QC **禁止** same-bar；carve-out 需具名例外（`T0_CARVE_FIN_SAT_SWITCH` only）。
2. MOC／盘中代理是下一研究实现方向（非整盘关 Exact T+1）。
3. Path3 observe 继续当 **上界**；勿把 observe 当 live fill 预期。
4. Soft-Frozen / CONF α / 全局 T+1 **KEEP**；本 Stage A **不改** live 代码。

## Next（需人裁）

- 若要推进：开 live fill carve-out 设计票（paper MOC port / same-bar allowlist）· 仍 BLOCKED 至 ACCEPT
- 或 DEFER：维持 observe-only，不碰 fill 时钟

Screen: `FIN_SAT_PATH3_LIVE_T0_MECH_STAGEA_SCREEN.md` · Charter: `FIN_SAT_PATH3_LIVE_T0_MECH_STAGEA_CHARTER.md` · Register **0k9t**

Label: `FIN_SAT_PATH3_LIVE_T0_MECH_STAGEA_DECISION_PACK_2026-09-29__ORACLE_ONLY__NO_LIVE`
