# 元大 SPARK PROD — 只讀連線教學（Windows／Linux）

Status: **OPS / HOWTO** — 營業員已開 **正式環境** 後，逐步驗證 Login＋查詢  
Companion checklist: `YUANTA_SPARK_PROD_READONLY_CHECKLIST.md`  
Official docs: [SPARK 入口](https://www.yuanta.com.tw/file-repository/content/API/page/index.html) · [登入](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%99%BB%E5%85%A5/index.html) · [庫存](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E8%82%A1%E7%A5%A8%E5%BA%AB%E5%AD%98%E7%B6%9C%E5%90%88%E7%B8%BD%E8%A1%A8/index.html) · [銀行餘額](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E9%8A%80%E8%A1%8C%E9%A4%98%E9%A1%8D%E6%9F%A5%E8%A9%A2/index.html) · [交割款](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E4%BA%A4%E5%89%B2%E6%AC%BE%E6%9F%A5%E8%A9%A2/index.html)  
UAT（若之後有）: `YUANTA_SPARK_UAT_GCP_STATIC_IP_HOWTO.md`

---

## 0. 這份教學的安全上限

| 做 | 絕對不要 |
|---|---|
| `Open(PROD)` → `Login` → 庫存／餘額／交割**查詢** | 呼叫 `SendStockOrder`／改量／改價／刪單 |
| 測完 `LogOut` + `Close` | 把帳密、`.pfx` 貼進 Chat／commit 進 git |
| | 開 `E21_BROKER_WRITE_LIVE` 或 `broker_live_write_accepted` |
| | 用 `yuanta-uat-vm` 當 PROD 常態機 |

**Login 通過：** `MsgCode` = **`0001`／`00001`（成功）**（`0000` = 失敗）。  
**查詢通過：** 看到 `[GetStoreSummary]`／`[GetBankBalance]`／`[GetStkTransactionOutlay]`（筆數可為 0）。

---

## 1. 開始前跟營業員要齊

- [ ] 開的是 **PROD**  
- [ ] 帳號：`S` + 分公司 4 + 帳號 7  
- [ ] 登入密碼、**win-x64** 元件包  
- [ ] Linux／Mac 另要 `.pfx`

---

## 2. 機器

Windows x64 筆電優先；Python 3.11 **64-bit** + .NET 8 + `win-x64` 元件。

---

## 3. 安裝

- Python 3.11 x64（Add to PATH）  
- [.NET 8 Desktop Runtime x64](https://dotnet.microsoft.com/download/dotnet/8.0)  
- `python -m pip install -U pip pythonnet`  
- 確認：`python --version` → 3.11.x；`dotnet --version` → 8.x

---

## 4. 只讀腳本（存本機，勿 commit）

在 **x64 元件目錄**（與 `YuantaSparkAPI.dll` 同層）覆蓋 `prod_readonly_login.py`：

```python
"""PROD read-only: Open + Login + inventory/balance/settlement. NO orders."""
import os
import sys
import time
from pathlib import Path

if sys.version_info < (3, 8):
    raise SystemExit(
        "Need Python 3.8+. Now running: {}".format(sys.version.split()[0])
    )

from pythonnet import load

load("coreclr")
import clr  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE))
if sys.platform == "win32":
    os.add_dll_directory(str(HERE))

clr.AddReference("System.Collections")
clr.AddReference("YuantaSparkAPI")

from YuantaOneAPI import (  # noqa: E402
    YuantaSparkAPITrader,
    enumEnvironmentMode,
    enumLangType,
    enumLogType,
)

ACCOUNT = os.environ["YUANTA_ACCOUNT"]
PASSWORD = os.environ["YUANTA_PASSWORD"]
state = {
    "login_done": False,
    "msg_code": "",
    "store_done": False,
    "bank_done": False,
    "outlay_done": False,
}


def _mask_acct(acct):
    s = str(acct or "")
    return "***" + s[-4:] if len(s) >= 4 else "***"


def on_response(intMark, dwIndex, strIndex, objHandle, objValue):
    try:
        if intMark == 0:
            print("[sys]", objValue)
            return
        if intMark != 1:
            return

        if strIndex == "Login":
            status = objValue.LoginStatus
            code = str(status.MsgCode)
            state["login_done"] = True
            state["msg_code"] = code
            print("[Login] MsgCode={} MsgContent={} Count={}".format(
                code, status.MsgContent, status.Count
            ))
            if code in ("0001", "00001") or int(status.Count) > 0:
                for row in objValue.LoginList:
                    print("  account={} name={} seller={}".format(
                        _mask_acct(row.Account), row.Name, row.SellerNo
                    ))
            else:
                print("  LOGIN FAILED")
            return

        if strIndex == "GetStoreSummary":
            stk = objValue.StkStoreList
            n = int(stk.Count)
            print("[GetStoreSummary] 現貨筆數={}".format(n))
            for i in range(n):
                row = stk[i]
                print(
                    "  code={} name={} qty={} trading_qty={} avg={} mkt_amt={}".format(
                        row.StkCode,
                        row.StkName,
                        row.StockQty,
                        row.TradingQty,
                        row.Price,
                        row.MarketAmt,
                    )
                )
            state["store_done"] = True
            return

        if strIndex == "GetBankBalance":
            rows = objValue.BankBalanceList
            n = int(rows.Count)
            print("[GetBankBalance] 筆數={}".format(n))
            for i in range(n):
                row = rows[i]
                print(
                    "  account={} bank={} available={} msg={}".format(
                        _mask_acct(row.Account),
                        _mask_acct(row.BankAccount),
                        row.AvailableBalance,
                        row.Message,
                    )
                )
            state["bank_done"] = True
            return

        if strIndex == "GetStkTransactionOutlay":
            rows = objValue.TransactionOutlayList
            n = int(rows.Count)
            print("[GetStkTransactionOutlay] 筆數={}".format(n))
            for i in range(n):
                row = rows[i]
                print(
                    "  account={} day={} amt={}".format(
                        _mask_acct(row.Account),
                        row.SettlementDay,
                        row.SettlementAmt,
                    )
                )
            state["outlay_done"] = True
            return

        print("[other] strIndex={} dwIndex={}".format(strIndex, dwIndex))
    except Exception as exc:
        print("on_response error:", exc)


def _wait(flag, seconds=30):
    for _ in range(seconds):
        if state[flag]:
            return True
        time.sleep(1)
    return state[flag]


def main():
    api = YuantaSparkAPITrader()
    api.SetLogType(enumLogType.COMMON)
    api.OnResponse += on_response

    print("Open(PROD)...")
    api.Open(enumEnvironmentMode.PROD)
    time.sleep(2)

    print("Login...")
    api.Login(ACCOUNT, PASSWORD)
    if not _wait("login_done") or state["msg_code"] not in ("0001", "00001"):
        print("STOP: login failed")
        try:
            api.LogOut()
            api.Close()
        except Exception:
            pass
        return

    print("Query GetStoreSummary (read-only)...")
    try:
        api.GetStoreSummary(ACCOUNT, enumLangType.UTF8)
    except TypeError:
        api.GetStoreSummary(ACCOUNT)
    _wait("store_done", 20)

    print("Query GetBankBalance (read-only)...")
    try:
        api.GetBankBalance(ACCOUNT, enumLangType.UTF8)
    except TypeError:
        api.GetBankBalance(ACCOUNT)
    _wait("bank_done", 20)

    print("Query GetStkTransactionOutlay (read-only)...")
    try:
        api.GetStkTransactionOutlay(ACCOUNT, enumLangType.UTF8)
    except TypeError:
        api.GetStkTransactionOutlay(ACCOUNT)
    _wait("outlay_done", 20)

    print(
        "READ-ONLY DONE store={} bank={} outlay={}".format(
            state["store_done"], state["bank_done"], state["outlay_done"]
        )
    )
    # NO SendStockOrder / amend / cancel.

    time.sleep(2)
    try:
        api.LogOut()
    except Exception as exc:
        print("LogOut note:", exc)
    time.sleep(1)
    try:
        api.Close()
    except Exception as exc:
        print("Close note:", exc)
    time.sleep(2)
    sys.stdout.flush()
    print("done.")
    time.sleep(1)


if __name__ == "__main__":
    main()
    os._exit(0)
```

```powershell
cd C:\Users\mg922\Downloads\YuantaSparkAPI_win-x64_Python\YuantaSparkAPI_win-x64_Python
$env:YUANTA_ACCOUNT = "S你的帳號"
$env:YUANTA_PASSWORD = "你的密碼"
python prod_readonly_login.py
```

Linux／Mac：`Login` 改四參數 `Login(pfx, pfxPass, account, pass)`。

---

## 5. 與 App 核對

| 輸出 | 對照 |
|---|---|
| `GetStoreSummary` 代號／股數 | 元大 App 庫存 |
| `GetBankBalance` available | 銀行／可出金約略 |
| `GetStkTransactionOutlay` | 交割款（可為 0 筆） |

---

## 6. 常見失敗

| 現象 | 怎麼辦 |
|---|---|
| Python 3.6 / `annotations` | 裝 3.11 x64 |
| `dotnet root` | 裝 .NET 8 Desktop Runtime |
| `_enter_buffered_busy` | Login／查詢成功可忽略 |
| `cannot import enumLangType` | 查詢改只傳 `ACCOUNT` |
| MsgCode `0112` | 找營業員開帳務查詢權限 |

---

## 7. 回報（打碼）

可貼：`MsgCode`、三段查詢是否 `True`、庫存筆數、是否與 App 大致一致。  
勿貼：完整帳號、密碼、銀行帳號全文。

---

## 8. 通過後（仍不下單）

1. 可補 UAT → `YUANTA_SPARK_UAT_GCP_STATIC_IP_HOWTO.md`  
2. Repo：#246 adapter、#247 防呆；**接 DLL 自動下單要另開 ACCEPT**  
3. Soft-Frozen live write 另案

---

Label: `YUANTA_SPARK_PROD__READONLY_HOWTO`
