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
若營業員只開了 PROD：見 `YUANTA_SPARK_PROD_READONLY_CHECKLIST.md`（只讀 Login／查詢，不下單）。

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

1. 至元大 SPARK 入口下載 **Python／C# 元件與範例**（需已申請）
2. 解壓到例如 `~/YuantaSparkAPI/`（含 `YuantaSparkAPI.dll` 與所有 `.so`）
3. **測試憑證**依文件匯入／放置；路徑與密碼**只放 VM 本機**，勿進 git

Linux／Mac 登入常需：

```text
Login(Pfx絕對路徑, Pfx密碼, 帳號, 登入密碼)
帳號格式例：S + 分公司(4) + 帳號(7)
```

最小連線順序（觀念）：

```text
Open(UAT) → Login(...) → 等 OnResponse Login 成功 → 再查庫存／帳務
（下單 SendStockOrder 等 Login／查詢都穩再說）
```

詳細欄位見官方「國內證券下單」：`BasketNo`（自訂 ≤32 英數字）適合之後對我們的 `client_order_id`／dedupe；`OrderQty` 單位是**張**（1 張 = 1000 股）。

---

## 6. 建議驗證清單（由淺到深）

1. VM 對外 IP 與給營業員的一致：`curl -4 ifconfig.me`
2. UAT 防火牆開通後：`Open(UAT)` 不再連線失敗
3. `Login` → `OnResponse` MsgCode 成功
4. 庫存／交割款／損益**查詢**（只讀）
5. （可選）極小額／可取消的測試單 — 仍在 UAT；對齊 `BasketNo`
6. **不要**在此 VM 寫 repo 的 `forward/e21`；shadow 產物可留在 VM 本地目錄

對接本 repo 防呆（之後才做）：`scripts/broker_safety.py` 的 process lock／confirm／dedupe；`LIVE.broker_live_write_accepted` 維持 `False` 直到 ACCEPT。

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
