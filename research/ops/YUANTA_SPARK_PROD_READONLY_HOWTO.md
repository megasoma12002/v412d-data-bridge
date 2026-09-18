# 元大 SPARK PROD — 只讀連線教學（Windows／Linux）

Status: **OPS / HOWTO** — 營業員已開 **正式環境** 後，逐步驗證 Login＋查詢  
Companion checklist: `YUANTA_SPARK_PROD_READONLY_CHECKLIST.md`  
Official docs: [SPARK 入口](https://www.yuanta.com.tw/file-repository/content/API/page/index.html) · [登入](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%99%BB%E5%85%A5/index.html) · [連線](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E9%80%A3%E7%B7%9A%E8%88%87%E9%9B%A2%E7%B7%9A/index.html)  
UAT（若之後有）: `YUANTA_SPARK_UAT_GCP_STATIC_IP_HOWTO.md`

---

## 0. 這份教學的安全上限

| 做 | 絕對不要 |
|---|---|
| `Open(PROD)` → `Login` → 看 `OnResponse` | 呼叫 `SendStockOrder`／改量／改價／刪單 |
| 庫存／餘額／交割**查詢**（官方範例裡的查詢函式） | 把帳密、`.pfx` 貼進 Chat／commit 進 git |
| 測完 `LogOut` + `Close` | 開 `E21_BROKER_WRITE_LIVE` 或 `broker_live_write_accepted` |
| | 用 `yuanta-uat-vm` 當 PROD 常態機 |

**通過標準：** Login 的 `MsgCode` 為 **`0001`／`00001`（成功）**。  
注意：元大文件寫 **`0000` = 失敗**、**`0001` = 成功**（與直覺相反）。

---

## 1. 開始前跟營業員要齊（缺一不可）

打勾再用：

- [ ] 確認開的是 **PROD（正式）**，不是 UAT  
- [ ] 證券帳號：`S` + 分公司 4 碼 + 帳號 7 碼（例示格式 `S98xxxxxxx`）  
- [ ] 登入密碼（API／網路下單密碼，以營業員說明為準）  
- [ ] **元件包**：Python 範例資料夾（內含 `YuantaSparkAPI.dll` 與相依檔）  
- [ ] **Windows**：通常帳密即可 Login  
- [ ] **Linux／Mac**：另要 `.pfx` 絕對路徑 + pfx 密碼  
- [ ] PROD 是否要 IP 白名單（多數不必；若要，勿與 UAT IP 混用）

下載入口：元大 SPARK API 頁（需已申請）。解壓到本機專用目錄，例如：

```text
Windows:  C:\YuantaSparkAPI\
Linux:    ~/YuantaSparkAPI/
```

該目錄**不要**放在本 git repo 裡。

---

## 2. 建議在哪台機器跑

| 環境 | 建議 |
|---|---|
| **Windows 筆電（優先）** | 最省事；官方 Python 範例以 Windows 為主 |
| Linux／Mac | 可；Login 必須帶 pfx 四參數版 |
| GCP `yuanta-uat-vm` | **不要**當 PROD 教學機（那是 UAT 白名單用途） |

---

## 3. 安裝（約 10–20 分鐘）

### 3.1 共同需求

- Python **3.8+**（建議 3.10／3.11）  
- [.NET 8](https://dotnet.microsoft.com/download)（Desktop／SDK 皆可；Linux 用 install script）  
- `pip install pythonnet`

### 3.2 Windows（PowerShell）

先確認是 **Python 3.8+**（不要用 2.7；`annotations` 錯誤＝版本太舊）：

```powershell
python --version
py -3 --version
```

若 `python` 顯示 2.x，改用 `py -3`：

```powershell
cd C:\Users\你的路徑\YuantaSparkAPI_win-x86_Python
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version   # 應為 3.8+
pip install -U pip pythonnet

dir YuantaSparkAPI.dll
```

沒裝 Python 3：到 [python.org](https://www.python.org/downloads/) 裝 3.11／3.12，安裝時勾 **Add python.exe to PATH**。

### 3.3 Linux（Ubuntu 例）

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --channel 8.0
export DOTNET_ROOT=$HOME/.dotnet
export PATH=$PATH:$HOME/.dotnet:$HOME/.dotnet/tools

mkdir -p ~/YuantaSparkAPI && cd ~/YuantaSparkAPI
# 把營業員給的元件解壓到這裡
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip pythonnet
```

---

## 4. 只讀腳本（請自己存成本機檔，勿 commit）

在元件目錄建立 `prod_readonly_login.py`（帳密用環境變數，不要寫死進檔案）。

### 4.1 Windows — 帳密 Login

```python
"""PROD read-only: Open + Login only. NO orders."""
import os
import sys
import time
from pathlib import Path

if sys.version_info < (3, 8):
    raise SystemExit(
        "Need Python 3.8+. Now running: {}. Try: py -3 prod_readonly_login.py".format(
            sys.version.split()[0]
        )
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
    enumLogType,
)

ACCOUNT = os.environ["YUANTA_ACCOUNT"]       # e.g. S98xxxxxxx
PASSWORD = os.environ["YUANTA_PASSWORD"]
login_ok = {"done": False, "msg_code": "", "msg": ""}


def on_response(intMark, dwIndex, strIndex, objHandle, objValue):
    try:
        if intMark == 0:
            print("[sys]", objValue)
            return
        if intMark == 1 and strIndex == "Login":
            status = objValue.LoginStatus
            code = str(status.MsgCode)
            content = str(status.MsgContent)
            login_ok["done"] = True
            login_ok["msg_code"] = code
            login_ok["msg"] = content
            print("[Login] MsgCode={} MsgContent={} Count={}".format(
                code, content, status.Count
            ))
            # 0001 / 00001 = 成功；0000 = 失敗（官方定義）
            if code in ("0001", "00001") or int(status.Count) > 0:
                for row in objValue.LoginList:
                    # 打碼：只印帳號後 4 碼
                    acct = str(row.Account)
                    print("  account=***{} name={} seller={}".format(
                        acct[-4:], row.Name, row.SellerNo
                    ))
            else:
                print("  LOGIN FAILED — stop here; do not query/trade")
    except Exception as exc:
        print("on_response error:", exc)


def main():
    api = YuantaSparkAPITrader()
    api.SetLogType(enumLogType.COMMON)
    api.OnResponse += on_response

    print("Open(PROD)...")
    api.Open(enumEnvironmentMode.PROD)
    time.sleep(2)

    print("Login...")
    api.Login(ACCOUNT, PASSWORD)

    # 等 OnResponse（最多 ~30s）
    for _ in range(30):
        if login_ok["done"]:
            break
        time.sleep(1)

    if login_ok["msg_code"] not in ("0001", "00001"):
        print("STOP: login not successful. Do not call order APIs.")
        api.LogOut()
        api.Close()
        return

    print("Login OK — read-only window. Add inventory query from official sample NEXT.")
    print("When done: Ctrl+C then LogOut/Close, or wait for auto close.")
    # --- 可選：在這裡呼叫官方範例的「庫存／交割」查詢函式（名稱以你下載的 sample 為準）---
    # 例如官方 YSendOrder.py / 查詢範例裡的庫存 API；不要複製 SendStockOrder。

    time.sleep(5)
    api.LogOut()
    api.Close()
    print("done.")


if __name__ == "__main__":
    main()
```

執行（務必用 Python 3）：

```powershell
cd C:\Users\你的路徑\YuantaSparkAPI_win-x86_Python
.\.venv\Scripts\Activate.ps1   # 若有建 venv
$env:YUANTA_ACCOUNT = "S你的帳號"
$env:YUANTA_PASSWORD = "你的密碼"
py -3 prod_readonly_login.py
# 或（venv 已 activate 且是 3.8+）:
# python prod_readonly_login.py
```

### 4.2 Linux／Mac — pfx 四參數 Login

把上面的 `api.Login(ACCOUNT, PASSWORD)` 改成：

```python
PFX_PATH = os.environ["YUANTA_PFX_PATH"]   # 絕對路徑
PFX_PASS = os.environ["YUANTA_PFX_PASS"]
api.Login(PFX_PATH, PFX_PASS, ACCOUNT, PASSWORD)
```

```bash
export YUANTA_ACCOUNT='S你的帳號'
export YUANTA_PASSWORD='你的密碼'
export YUANTA_PFX_PATH='/home/你/certs/xxxx.pfx'
export YUANTA_PFX_PASS='pfx密碼'
cd ~/YuantaSparkAPI && source .venv/bin/activate
python prod_readonly_login.py
```

---

## 5. 庫存／交割只讀查詢（第二步）

Login 成功後：

1. 打開營業員／官網給的 **Python 範例**（常名 `YSendOrder.py` 或查詢專用 sample）  
2. 找到**庫存、銀行餘額、交割款、損益**相關呼叫（名稱因版本而異）  
3. **只抄查詢函式**進你的 `prod_readonly_login.py`；**整段刪除／註解**所有 `SendStockOrder`、改單、刪單  
4. 在 `Login OK` 分支裡呼叫查詢；結果與元大 App／對帳單核對張數與金額（允許延遲）

查詢函式實際名稱以你手上的 SDK 為準；不要猜造 API 名。官方文件目錄：[sparkapi_docs](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/index.html)。

---

## 6. 常見失敗對照

| 現象 | 可能原因 | 怎麼辦 |
|---|---|---|
| `future feature annotations is not defined` | `python` 是 2.x 或 &lt;3.7 | `py -3 --version`；用 `py -3` 重跑；裝 Python 3.11 |
| `Error loading YuantaSparkAPI` | DLL 不在目錄／缺相依／沒裝 .NET | 元件齊全；`dir`／`ls` 核對；重裝 .NET 8 |
| `Open` 後一直 timeout | 網路／防火牆／環境選錯 | 確認 `enumEnvironmentMode.PROD`；問營業員 PROD 是否要白名單 |
| MsgCode `0000` | 登入失敗 | 帳號格式、密碼、pfx |
| MsgCode `0102` | 密碼凍結或未啟用 | 找營業員重設／啟用 |
| MsgCode `0112` | 無此權限 | 確認 SPARK／API 權限真的開在 PROD |
| Linux Login 掛掉 | 沒用四參數 pfx | 改 `Login(pfx, pfxPass, account, pass)` |

---

## 7. 測完回報（打碼）

可貼給 agent／自己存檔的安全內容：

- OS（Win／Linux）  
- `Open(PROD)` 是否成功  
- Login `MsgCode` + `MsgContent`（可原文）  
- 帳號只留後 4 碼  
- 有無成功跑庫存查詢（是／否；張數是否與 App 大致一致）  

**不要貼：** 完整帳號、密碼、pfx、未打碼身分證、委託內容。

---

## 8. 通過後下一步（仍不下單）

1. 若營業員可補 **UAT** → 改走 `YUANTA_SPARK_UAT_GCP_STATIC_IP_HOWTO.md`  
2. Repo 側：#246 offline adapter、#247 防呆已備；**接真 DLL 要另開 ACCEPT**  
3. Soft-Frozen 日批／自動下單 = 更後面的 ACCEPT，與「能 Login」分開

---

Label: `YUANTA_SPARK_PROD__READONLY_HOWTO`
