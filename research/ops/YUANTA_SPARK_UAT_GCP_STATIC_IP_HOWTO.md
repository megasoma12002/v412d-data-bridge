# 元大 SPARK UAT — 最小 GCP 固定 IP 教學

Status: **OPS / HOWTO** — UAT 連線用；**不是** Soft-Frozen 日批 cutover  
Audience: 本機無固定 IP、需申請元大測試環境防火牆白名單  

Related: `ARCH_LIVE_MODULARIZE.md` · `broker_safety.py` · 元大 [SPARK API 入口](https://www.yuanta.com.tw/file-repository/content/API/page/index.html) · [說明文件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/index.html)

---

## 0. 這份教學在做什麼／不做什麼

| 做 | 不做 |
|---|---|
| 開一台 **有靜態外部 IP** 的小 VM | 不把 Soft-Frozen `forward/e21` 搬上這台 |
| 把該 IP 給營業員做 **UAT 防火牆** | 不取代 GHA `v412f-forward-paper` 日批 writer |
| 在 VM 上測 SPARK Login／查詢／之後 shadow 下單 | 不把帳密／憑證 commit 進 git／Docker image |
| 測完可 **停止 VM** 省錢 | 不開啟 `broker_live_write_accepted`（仍要另開 ACCEPT） |

**一句話：** 這台機器 =「元大 UAT 的固定出口 IP + 測 API」，不是 live 帳本主機。

---

## 1. 前置

1. 已有 Google Cloud 專案（帳單已開）
2. 已是元大證券客戶；準備跟營業員申請 **SPARK API 測試環境**
3. 本機可執行 `gcloud`（或用 Cloud Console 網頁操作同等步驟）
4. 建議區域：**`asia-east1`（台灣）** — 延遲較低，與架構文件候選一致

登入與選專案：

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud config set compute/region asia-east1
gcloud config set compute/zone asia-east1-b
```

---

## 2. 建立靜態外部 IP

```bash
gcloud compute addresses create yuanta-uat-ip \
  --region=asia-east1
```

查 IP（之後要給營業員）：

```bash
gcloud compute addresses describe yuanta-uat-ip \
  --region=asia-east1 \
  --format='get(address)'
```

記下這個 IPv4，例如 `34.x.x.x`。

---

## 3. 開最小 VM 並綁定該 IP

建議規格（夠測 API 即可）：

- 機器：`e2-small` 或 `e2-medium`
- 映像：Ubuntu 22.04 LTS
- 磁碟：20–40 GB
- 外部 IP：上面建的靜態 IP

```bash
gcloud compute instances create yuanta-uat-vm \
  --zone=asia-east1-b \
  --machine-type=e2-small \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --address=yuanta-uat-ip \
  --tags=yuanta-uat \
  --metadata=enable-oslogin=TRUE
```

### 防火牆（你這側）

- **入站：** 只開 SSH（22）給**你自己的**來源 IP；不要 `0.0.0.0/0` 長期開著
- **出站：** 預設通常已允許；元大 UAT 是他們擋你，不是你擋元大

範例（把 `YOUR.HOME.IP/32` 換成自己的公網 IP）：

```bash
gcloud compute firewall-rules create yuanta-uat-ssh \
  --allow=tcp:22 \
  --source-ranges=YOUR.HOME.IP/32 \
  --target-tags=yuanta-uat \
  --description="SSH to Yuanta UAT jump VM only from home"
```

SSH：

```bash
gcloud compute ssh yuanta-uat-vm --zone=asia-east1-b
```

---

## 4. 跟營業員怎麼說

寄給所屬營業員（可複製改）：

> 您好，我想申請元大 **SPARK API 測試環境（UAT）** 防火牆開通。  
> 固定來源 IP：`34.x.x.x`（GCP 靜態外部 IP）  
> 用途：本機／雲端開發機串接測試（Login、查詢；之後再測下單流程）  
> 請協助開通，並告知測試憑證／元件下載方式。謝謝。

開通前用 UAT 常會看到「無法連接至遠端伺服器」——屬預期，不是程式先壞。

正式環境（PROD）一般**不必**固定 IP；但開發請先走 UAT。  
若營業員只開了 PROD：見 `YUANTA_SPARK_PROD_READONLY_HOWTO.md`（逐步教學）與 `YUANTA_SPARK_PROD_READONLY_CHECKLIST.md`（只讀上限）。

---

## 5. VM 內軟體安裝（Ubuntu）

在 VM 上：

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv wget curl unzip

# .NET 8 SDK（SPARK 元件需要）
wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --channel 8.0
echo 'export DOTNET_ROOT=$HOME/.dotnet' >> ~/.bashrc
echo 'export PATH=$PATH:$HOME/.dotnet:$HOME/.dotnet/tools' >> ~/.bashrc
source ~/.bashrc
dotnet --version

python3 -m venv ~/venv-spark
source ~/venv-spark/bin/activate
pip install -U pip pythonnet
```

### SPARK 元件

1. 至元大 SPARK 入口下載 **Python Linux x64** zip + **測試憑證 `.pfx`**（本機瀏覽器）
2. 本機 `scp` 到 VM（勿 commit）：

```bash
gcloud compute scp ~/Downloads/YuantaSparkAPI*.zip yuanta-uat-vm:~/YuantaSparkAPI/ --zone=asia-east1-b
gcloud compute scp ~/Downloads/*.pfx yuanta-uat-vm:~/certs/ --zone=asia-east1-b
```

3. VM 解壓，找到 DLL 同層目錄：

```bash
cd ~/YuantaSparkAPI && unzip -o YuantaSparkAPI*.zip
find ~/YuantaSparkAPI -name YuantaSparkAPI.dll
# 之後所有 python 指令都在「dll 所在目錄」執行
```

4. **測試憑證**路徑與密碼**只放 VM 本機**，勿進 git

Linux 登入（四參數）：

```text
Login(Pfx絕對路徑, Pfx密碼, 帳號, 登入密碼)
帳號格式例：S + 分公司(4) + 帳號(7)
```

最小連線順序（觀念）：

```text
Open(UAT) → Login(pfx, pfxPass, account, pass) → 等 OnResponse Login 成功 → 再查庫存／帳務
（禁止 SendStockOrder；下單另開 ACCEPT）
```

詳細欄位見官方「國內證券下單」：`BasketNo`（自訂 ≤32 英數字）適合之後對我們的 `client_order_id`／dedupe；`OrderQty` 單位是**張**（1 張 = 1000 股）。

### 官方 UAT 測試帳（公開文件）

來源：[測試環境＆正式環境說明](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/1.前言/2.測試環境%26正式環境說明/index.html)

| 欄位 | 值 |
|---|---|
| 環境 | `Open(UAT)` |
| 帳號 | `S98875005091` |
| 登入密碼 | `1234` |
| 憑證密碼 | `yuanta` |
| 固定出口 IP（本專案） | `35.206.200.31`（`yuanta-uat-vm`） |

---

## 5b. UAT 只讀腳本（存 VM，勿 commit）

骨架對齊 `YUANTA_SPARK_PROD_READONLY_HOWTO.md`；差異只有 **`Open(UAT)`** + Linux **四參數 Login**。  
在 **`YuantaSparkAPI.dll` 同層** 寫 `uat_readonly_login.py`（可用 `nano`／`cat >`）：

```python
"""UAT read-only: Open(UAT) + Login(pfx,...) + inventory/balance. NO orders."""
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

clr.AddReference("System.Collections")
clr.AddReference("YuantaSparkAPI")

from YuantaOneAPI import (  # noqa: E402
    YuantaSparkAPITrader,
    enumEnvironmentMode,
    enumLangType,
    enumLogType,
)

# Defaults = official UAT test account (public Yuanta docs). Override via env.
ACCOUNT = os.environ.get("YUANTA_ACCOUNT", "S98875005091")
PASSWORD = os.environ.get("YUANTA_PASSWORD", "1234")
PFX_PATH = os.environ.get(
    "YUANTA_PFX_PATH",
    str(Path.home() / "certs" / "REPLACE_ME.pfx"),
)
PFX_PASSWORD = os.environ.get("YUANTA_PFX_PASSWORD", "yuanta")

state = {
    "login_done": False,
    "msg_code": "",
    "store_done": False,
    "bank_done": False,
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
    pfx = Path(PFX_PATH)
    if not pfx.is_file():
        raise SystemExit("PFX missing: {} (set YUANTA_PFX_PATH)".format(pfx))

    api = YuantaSparkAPITrader()
    api.SetLogType(enumLogType.COMMON)
    api.OnResponse += on_response

    print("Open(UAT)...")
    api.Open(enumEnvironmentMode.UAT)
    time.sleep(2)

    print("Login(pfx, ...)...")
    api.Login(str(pfx.resolve()), PFX_PASSWORD, ACCOUNT, PASSWORD)
    if not _wait("login_done") or state["msg_code"] not in ("0001", "00001"):
        print("STOP: login failed MsgCode={}".format(state["msg_code"]))
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

    print(
        "READ-ONLY DONE store={} bank={}".format(
            state["store_done"], state["bank_done"]
        )
    )
    # NO SendStockOrder / amend / cancel. NO Soft-Frozen forward/e21 writes.

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

VM 跑測（手機 SSH 可貼）：

```bash
source ~/venv-spark/bin/activate
export YUANTA_PFX_PATH="$HOME/certs/你的憑證.pfx"
cd "$(dirname "$(find ~/YuantaSparkAPI -name YuantaSparkAPI.dll | head -1)")"
# 把上面腳本存成同層 uat_readonly_login.py 後：
python uat_readonly_login.py
```

**通過：** `MsgCode` = `0001`／`00001`；結尾 `READ-ONLY DONE store=True bank=True`（筆數可為 0）。  
**回報（打碼）：** MsgCode、兩段查詢是否 True、庫存筆數。勿貼完整帳號／銀行帳號／pfx 路徑以外的秘密。

常見失敗：

| 現象 | 怎麼辦 |
|---|---|
| 無法連接至遠端伺服器 | 防火牆／IP：`curl -4 ifconfig.me` 應為 `35.206.200.31` |
| PFX missing | `ls ~/certs/*.pfx`；設 `YUANTA_PFX_PATH` |
| MsgCode `0000` | 核對 pfx 密碼 `yuanta`、帳密、元件是否 Linux x64 |
| `cannot import enumLangType` | 查詢改只傳 `ACCOUNT`（腳本已 try/except） |

---

## 6. 建議驗證清單（由淺到深）

1. VM 對外 IP 與給營業員的一致：`curl -4 ifconfig.me` → **`35.206.200.31`**
2. UAT 防火牆開通後：`Open(UAT)` 不再連線失敗
3. `Login` → `OnResponse` MsgCode **`0001`／`00001`**
4. `GetStoreSummary`／`GetBankBalance` **查詢**（只讀；筆數可 0）
5. （可選、另 ACCEPT）極小額／可取消的測試單 — 仍在 UAT；對齊 `BasketNo`
6. **不要**在此 VM 寫 repo 的 `forward/e21`；shadow 產物可留在 VM 本地目錄

對接本 repo 防呆（之後才做）：`scripts/broker_safety.py` 的 process lock／confirm／dedupe；`LIVE.broker_live_write_accepted` 維持 `False` 直到 ACCEPT。

離線欄位映射（BasketNo／張／ack→broker_acks）已在 `scripts/yuanta_spark_adapter.py`（見 `YUANTA_SPARK_ADAPTER_SKELETON.md`）；**不含** DLL 連線。

---

## 7. 省錢與安全習慣

```bash
# 不測時停機（靜態 IP 通常仍會留著，有少量位址費）
gcloud compute instances stop yuanta-uat-vm --zone=asia-east1-b

# 要測再開
gcloud compute instances start yuanta-uat-vm --zone=asia-east1-b
```

- OS Login／SSH key；勿開全世界 SSH  
- 憑證、密碼、`.pfx` 只在 VM；用 Secret Manager 更佳（進階）  
- Public GitHub repo：**禁止** push 真帳號／憑證／IP 白名單以外的秘密  

刪除（確定不要時）：

```bash
gcloud compute instances delete yuanta-uat-vm --zone=asia-east1-b
gcloud compute addresses delete yuanta-uat-ip --region=asia-east1
```

---

## 8. 之後何時才「整包上 GCP」

| 階段 | Writer of `forward/e21` |
|---|---|
| 現在 | **GHA** `v412f-forward-paper` |
| 本教學 | VM **不寫** Soft-Frozen |
| 日後 cutover | 另開 ACCEPT：日批改 GCP **且** GHA 停寫（禁止雙寫） |

---

## 9. 常見問題

**Q. Cursor Cloud Agent 能不能當 UAT 機器？**  
不能穩定當。Agent／臨時環境 IP 會變，元大 UAT 要固定 IP。

**Q. 一定要用 GCP 嗎？**  
不一定。任何雲（AWS／Azure）的**靜態公網 IP** 都行；文件以 GCP 為例是因為專案已有 GCP 候選區域。

**Q. PROD 要不要也綁這台？**  
開發先 UAT。PROD 通常不必固定 IP；真交易另走 ACCEPT + 防呆，不要用同一套「隨意測」習慣。

**Q. `gsutil` 汰換信跟這有關嗎？**  
無關。本教學只用 `gcloud compute`；之後若用 GCS 請直接寫 `gcloud storage`。

---

Label: `YUANTA_SPARK_UAT__GCP_STATIC_IP_HOWTO`
