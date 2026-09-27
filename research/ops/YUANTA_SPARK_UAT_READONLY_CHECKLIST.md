# 元大 SPARK UAT — 只讀驗證清單（PREP）

Status: **OPS / PREP** — UAT Login＋查詢 only · Soft-Frozen **KEEP** · **EXECUTE BLOCKED**  
Parent: `ACCEPT_PREP_BROKER_LIVE_WRITE_2026-09-25.md` · VM howto: `YUANTA_SPARK_UAT_GCP_STATIC_IP_HOWTO.md`  
Repo PREP pack: `BROKER_R5_OCO_PREP_NOT_OPEN.md`

---

## 0. 硬規則

| 做 | 不做 |
|---|---|
| `Open(UAT)` → `Login` → **只讀**庫存／餘額／交割 | **不下單**（`SendStockOrder`／`SendAlgo`／改刪單） |
| 固定出口 IP 白名單（例：`35.206.200.31`） | 不把 `.pfx`／密碼 commit 進 git |
| 記錄 MsgCode `0001`／`00001`（打碼後） | 不設 `E21_BROKER_WRITE_LIVE=1` |
| | 不開 `broker_live_write_accepted` |
| | 不改 Soft-Frozen `fill_port` |

**一句話：** UAT 只讀過關 = EXECUTE 前置證據；≠ 可以自動交易。

---

## 1. 本機／VM 前置（打勾）

- [ ] GCP 靜態 IP 已給營業員（howto §2–3）
- [ ] `ystest.yuanta.com.tw:443` 從該 IP 可通
- [ ] .NET + pythonnet + UAT SPARK 元件已裝在 **UAT VM**（非 tip writer）
- [ ] 憑證只在 Secret Manager／VM env

---

## 2. 只讀步驟

| # | 步驟 | 通過標準 |
|---|---|---|
| 1 | 元件載入 | DLL 無缺檔 |
| 2 | `Open(UAT)` | 連線成功 |
| 3 | `Login` | OnResponse MsgCode **`0001` 或 `00001`** |
| 4 | GetStoreSummary／庫存 | 張數合理 |
| 5 | GetBankBalance／交割 | 數字合理 |
| 6 | Logout | **零**下單痕跡 |

可接受紀錄（打碼）：Login 時間、MsgCode、查詢種類。  
**禁止**貼：完整帳號、密碼、pfx。

---

## 3. Repo 對照（agent 可跑、無憑證）

```bash
python3 scripts/ops_uat_readonly_prep_status.py --fail-if-gates-open
# Expect: PREP_OK_WAITING_OPERATOR · API_WIRED=false · send paths blocked
```

Optional evidence drop（**打碼** JSON，永不含密碼）：

`fixtures/uat_readonly_evidence.example.json` → 複製為本機 `fixtures/uat_readonly_evidence.json`（gitignored）

---

## 4. 通過後仍不做

- 不接 Soft-Frozen tip 下單  
- 不 `API_WIRED=True` 直到獨立 wire PR + EXECUTE ballot  
- 條件單 OCO SendAlgo 另開 ACCEPT  

Label: `YUANTA_SPARK_UAT_READONLY_CHECKLIST_2026-09-27__PREP`
