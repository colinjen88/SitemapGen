# 跨專案共用設定檔 (Shared Config) 實作指南與交辦提示詞

本文件說明如何將「共用設定檔 (`config.json`)」模式應用到其他專案，以確保所有專案的環境變數、部署設定與伺服器資訊保持一致與集中管理。

---

## 1. 核心概念

所有專案不應再將伺服器 IP、路徑或專案設定寫死 (Hardcode) 在程式碼中。應統一讀取根目錄下的 `config.json`。

**標準 `config.json` 結構：**

```json
{
    "project": {
        "name": "project-name",
        "version": "1.0",
        "description": "Project Description"
    },
    "site": {
        "title": "Website Title",
        "themeColor": "#0f766e",
        "apiBaseUrl": "/api"
    },
    "server": {
        "port": 3001, // 禁止使用 3000 (Conflict prone)
        "dataFile": "data.json" // Optional: custom data file path
    },
    "remote": {
        "user": "root",
        "host": "72.62.66.151",
        "dir": "/var/www/project_name"
    },
    "deploy": {
        "files": ["dist"], // Files or Folders to upload
        "pm2Name": "project-name",
        "description": "Build local and scp to remote",
        "nginxConfig": "" // Optional: Path to nginx config if needed
    },
    "sharedConfigRepo": "https://github.com/colinjen88/dev-admin.git"
}
```

---

## 2. 實作範例

### 後端 (Node.js/Express)
```javascript
const fs = require('fs');
// 讀取設定
let config = {};
try {
    config = JSON.parse(fs.readFileSync('./config.json', 'utf8'));
} catch (e) {
    console.warn("Config not found, using defaults");
}
// 使用設定
const PORT = process.env.PORT || config.server?.port || 3000;
```

### 部署腳本 (deploy.ps1 範本)
```powershell
# deploy.ps1
$ErrorActionPreference = "Stop"

# 1. 讀取設定檔
$ConfigPath = Join-Path $PSScriptRoot "config.json"
if (-not (Test-Path $ConfigPath)) {
    Write-Error "Config not found (config.json)"
    exit 1
}
$Config = Get-Content $ConfigPath -Encoding UTF8 -Raw | ConvertFrom-Json

# 2. 建構 (Build)
if ($args -notcontains "-no-build") {
    Write-Host "Building project..." -ForegroundColor Cyan
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed"
        exit $LASTEXITCODE
    }
}

# 3. 部署 (Deploy)
$RemoteUser = $Config.remote.user
$RemoteHost = $Config.remote.host
$RemoteDir  = $Config.remote.dir
$DeployFiles = $Config.deploy.files

Write-Host "Target: $RemoteUser@$RemoteHost" -ForegroundColor Cyan
Write-Host "Dest Dir: $RemoteDir" -ForegroundColor Cyan

foreach ($Item in $DeployFiles) {
    $LocalPath = Join-Path $PSScriptRoot $Item
    
    if (Test-Path $LocalPath) {
        Write-Host "Uploading: $Item -> $RemoteDir" -ForegroundColor Yellow
        
        # scp -r 會將目錄本身上傳。
        # 例如: deploy.files=["dist"], remote.dir="/var/www/proj"
        # 結果: /var/www/proj/dist/index.html
        # 請確保 Nginx root 設定為 .../dist 或對應路徑。
        # 建議：維持此結構 (上傳完整 dist 目錄)，方便版本切換與路徑管理。
        scp -r "$LocalPath" "$RemoteUser@$RemoteHost`:$RemoteDir"
    } else {
        Write-Warning "Local file not found: $LocalPath"
    }
}

# 4. 重啟 PM2 (Optional)
if ($Config.deploy.PSObject.Properties.Match("pm2Name") -and $Config.deploy.pm2Name) {
    $Pm2Name = $Config.deploy.pm2Name
    Write-Host "Restarting PM2: $Pm2Name" -ForegroundColor Cyan
    # 假設遠端已設定 SSH Key 免密碼登入
    ssh "$RemoteUser@$RemoteHost" "pm2 restart $Pm2Name"
}

Write-Host "Deployment Complete!" -ForegroundColor Green
```

---

## 3. 交辦提示詞 (Handover Prompt)

當您開啟一個新專案，或要求 AI / 工程師重構舊專案時，請直接複製貼上以下提示詞：

```markdown
### 任務：整合標準化共用設定檔 (config.json)

請依照以下規範重構或設定本專案，確保符合我們的跨專案部署標準：

1. **建立/確認 `config.json`**：
   - 在專案根目錄建立 `config.json`。
   - 抄寫標準結構 (包含 `project`, `server`, `remote`, `deploy`, `sharedConfigRepo`)。
   - `remote` 區塊需定義伺服器 IP (host)、使用者 (user) 與部署路徑 (dir)。
   - `deploy` 區塊需定義要上傳的檔案/目錄 (如 `dist`)。

2. **後端/前端整合**：
   - 移除程式碼中寫死的 Port 或 IP。
   - 前端若需變數，請透過 `import.meta.env` (Vite) 或由後端 API 讀取 config。
   - 後端請在啟動時讀取 `config.json`。

3. **建立部署腳本 (`deploy.ps1`)**：
   - 建立 PowerShell 腳本，**必須讀取 `config.json`** 的 `remote` 與 `deploy` 設定。
   - 執行 `npm run build`。
   - 使用 `scp` 自動將 `deploy.files` 定義的內容上傳至 `remote.dir`。
   - 禁止在 ps1 檔案中寫死 IP 位址，一切以 config.json 為準。

**目標**：確保我只要修改 `config.json`，就能改變部署目標與專案基本設定，而無須修改程式碼。
```

---

## 4. 中央管理與衝突預防 (Google Sheets)

為了避免 `admin.md` 或 `registry.md` 檔案散亂，我們改用 **Google Sheets** 作為中央註冊表。

### 管理目標
為避免多個專案在同一台伺服器上發生 **Port 衝突** (如都用 3000) 或 **部署路徑覆蓋**，必須在共用試算表中記錄所有專案的配置。

### Google Sheets 註冊表連結
> **[Google Sheets Project Registry](https://docs.google.com/spreadsheets/d/1SnDbdIS6R9gTtpQY6ugNuSvRfHfG659jHpRO6-9gUlY/edit?usp=sharing)**

試算表欄位建議：
| Project Name | Type | Port | Remote Host | Remote Dir | Description |
|---|---|---|---|---|---|
| daily-intel | VPS | 3001 | 72.62.66.151 | /var/www/dailyintel | 智能情報儀表板 |
| taiwan-trip | VPS | 3002 | 72.62.66.151 | /var/www/taiwan_trip | 台灣家庭跨年旅遊行程 App |
| seo-keyword-ranking-portfolio | VPS | 3003 | 72.62.66.151 | /var/www/seo_portfolio | SEO Content Marketing Portfolio |
| SitemapGen | Desktop | N/A | N/A | N/A | 網站 Sitemap 產生器工具 (GUI) |

### 新專案 SOP
1. **檢查佔用**：開啟 Google Sheet，確認哪個 Port 與 Path 是空閒的。
2. **分配資源**：
   - 決定新專案的 Port。
   - 決定獨立的部署路徑。
3. **回寫記錄**：
   - **手動**將新專案設定填入 Google Sheet。
   - 專案本身的 `config.json` 仍需建立，但「註冊」動作改為填寫試算表。

   這樣可確保團隊清楚知道 Port 3001 是 `daily-intel`。**嚴格禁止使用預設的 Port 3000**，因為極易與其他服務或開發環境衝突。請務必分配 3000 以外的 Port (如 3001, 3002, 8080 等)。

---

## 5. 版本紀錄 (Change Log)

| Date | Author | Description |
|---|---|---|
| 2026-01-05 | Antigravity | Initial creation and standardization of deployment flow. |
| 2026-01-05 | Antigravity | Updated registry link to Google Sheets and clarified Nginx/Directory structure. |
| 2026-01-05 | Antigravity | Registered seo-keyword-ranking-portfolio (Port 3003) and created config files. |
| 2026-01-05 | Antigravity | Added PM2 restart logic to deploy.ps1 template and registered SitemapGen. |
