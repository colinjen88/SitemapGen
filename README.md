
# SitemapGen 是一款自動產生網站 Sitemap.xml 的工具，支援自訂規則與批次處理，適用於網站管理與 SEO。

SitemapGen is a tool for automated generation of website Sitemap.xml, supporting custom rules and batch processing for site management and SEO.


# 最新專案狀態（2025/10/28）

- 已完成 sitemap 產生與主程式（sitemap_gui.py）測試，運作正常。
- 專案目前未包含自動化測試檔案（如 test_*.py 或 *_test.py）。
- 已新增 `.gitattributes`，強制 Python 與 Markdown 檔案使用 LF 換行格式，避免 Git 換行警告。

# Sitemap 生成器專案 (SEO工具)

## 專案簡介
((這是寫給現在公司用的, 專屬客製化爬蟲工具))
這是一個自動化網站爬蟲工具，專門用於生成符合 SEO 標準的 sitemap_YYYYmmdd_HHMMSS.xml 檔案。程式會自動爬取指定網站，依據預設規則篩選有效網址，並產生結構化的 sitemap 檔案。


## 主要功能

- **自動網站爬取**：從指定起始網址開始，自動發現並爬取所有相關頁面
- **智能網址篩選**：依據預設規則自動排除不需要的網址（如登入頁面、會員頁面等）
- **權重設定**：根據頁面類型自動設定適當的 priority 值
- **進度保存**：支援中斷後續爬取，避免重複工作
- **GUI 介面**：提供友善的圖形化操作介面
- **robots.txt 狀態顯示**：啟動爬蟲時即時檢查 robots.txt，顯示「已排除收錄robots.txt阻擋清單」，可點擊開啟 robots.txt 原始檔
- **進度條動畫**：進度條以 Canvas 呈現，根據執行緒數顯示多個色塊，每個色塊獨立循環移動，動態反映多執行緒狀態
- **批次處理**：支援大量網址的高效處理

## 檔案結構

SitemapGen/
├── sitemap_gui.py                  # 主程式（GUI 介面）
├── src/
│   ├── __init__.py
│   └── sitemap_generator.py        # 核心爬蟲引擎
├── scripts/
│   ├── convert_progress_to_sitemap.py      # 進度轉換腳本
│   └── convert_progress_to_sitemap_ok.py   # 進度轉換腳本（已驗證）
├── tools/
│   ├── remove_page1.py             # 移除 page=1 參數的工具
│   ├── sitemap_gui.spec            # PyInstaller 打包設定檔
│   └── build/
│       └── sitemap_gui/            # 編譯產物
├── Custom-made/
│   ├── SITEMAP_RULES.md            # 規則說明與預設網址
│   └── URL_RULES.md                # 網址收錄規則細節
├── docs/
│   ├── 快速使用說明.md
│   ├── OPTIMIZATION_SUMMARY.md
│   ├── SITEMAP_RULES.md
│   ├── SEO排除收錄規則與網址列表.md
│   └── 修正紀錄_SitemapGen_GUI啟動錯誤.md
├── setup_rules/
│   ├── config.json                 # 客製化設定檔
│   └── config.py
├── autosave/
│   └── sitemap_YYYYmmdd_HHMMSS.xml # 自動產生的 sitemap 檔案
├── output/
│   └── here_you_are/
│       └── sitemap_YYYYmmdd_HHMMSS.xml     # 歷史產出檔案
├── crawl_temp_YYYYmmdd_HHMMSS.pkl         # 進度暫存檔（每次啟動自動命名）
└── README.md                       # 本說明文件
```

```
SitemapGen/
├── sitemap_gui.py                  # 主程式（GUI 介面）
├── src/
│   ├── __init__.py
│   └── sitemap_generator.py        # 核心爬蟲引擎
├── scripts/
│   ├── convert_progress_to_sitemap.py      # 進度轉換腳本
│   └── convert_progress_to_sitemap_ok.py   # 進度轉換腳本（已驗證）
├── tools/
│   ├── remove_page1.py             # 移除 page=1 參數的工具
│   ├── sitemap_gui.spec            # PyInstaller 打包設定檔
│   └── build/
│       └── sitemap_gui/            # 編譯產物
├── Custom-made/
│   ├── SITEMAP_RULES.md            # 規則說明與預設網址
│   └── URL_RULES.md                # 網址收錄規則細節
├── docs/
│   ├── 快速使用說明.md
│   ├── OPTIMIZATION_SUMMARY.md
│   ├── SITEMAP_RULES.md
│   ├── SEO排除收錄規則與網址列表.md
│   └── 修正紀錄_SitemapGen_GUI啟動錯誤.md
├── setup_rules/
│   ├── config.json                 # 客製化設定檔
│   └── config.py
├── autosave/
│   ├── sitemap_YYYYmmdd_HHMMSS.xml # 自動產生的 sitemap 檔案
│   └── sitemap.xml                 # 暫存檔案，每次爬蟲結束自動覆蓋，僅供快速檢查
├── output/
│   └── here_you_are/
│       └── sitemap_YYYYmmdd_HHMMSS.xml     # 歷史產出檔案
├── crawl_temp_YYYYmmdd_HHMMSS.pkl         # 進度暫存檔（每次啟動自動命名）
└── README.md                       # 本說明文件
```

## 檔案命名規則

### 進度檔案
- **格式**：`crawl_temp_YYYYmmdd_HHMMSS.pkl`
- **說明**：每次啟動程式時自動產生，避免覆蓋之前的進度
- **範例**：`crawl_temp_20251029_140000.pkl`


### Sitemap 檔案
- **正式檔案格式**：`sitemap_YYYYmmdd_HHMMSS.xml`
- **說明**：每次產生時自動命名，避免覆蓋之前的檔案
- **範例**：`sitemap_20251029_153000.xml`
- **暫存檔案**：`autosave/sitemap.xml`，每次爬蟲結束自動覆蓋，僅供快速檢查，不影響正式輸出

### 自動保存機制
- **進度檔案**：每5秒自動保存到 `crawl_temp_YYYYmmdd_HHMMSS.pkl`
- **Sitemap 檔案**：爬取完成後自動產生 `sitemap_YYYYmmdd_HHMMSS.xml`


## 操作流程補充
- **自動保存**：每次啟動自動產生新進度檔，並每5秒自動保存
- **生成 Sitemap**：每次產生新檔案，檔名自動帶時間戳
- **進度條動畫**：啟動爬蟲後，進度條會根據所選執行緒數顯示多個色塊，每個色塊獨立循環移動，動態顯示多執行緒運作情形
- **檔案管理**：所有檔案都採用時間戳命名，避免覆蓋，便於版本管理

## 快速開始

### 1. 環境需求

- Python 3.7+
- 必要的 Python 套件：
  ```bash
  pip install requests beautifulsoup4 tkinter
  ```

### 2. 設定起始網址

編輯 `src/sitemap_generator.py` 檔案，修改 `START_URL` 變數：

```python
START_URL = "https://your-website.com/"  # 改為您的網站首頁
```

### 3. 執行程式

#### 方法一：使用 GUI 介面（推薦）
```bash
python sitemap_gui.py
```

#### 方法二：使用命令列
```bash
python src/sitemap_generator.py
```

### 4. 從進度檔案生成 Sitemap

如果已有進度檔案，可以使用腳本直接生成 sitemap：

```bash
python scripts/convert_progress_to_sitemap.py
```

腳本會自動尋找最新的 `crawl_temp_YYYYmmdd_HHMMSS.pkl` 檔案，並產生對應的 `sitemap_YYYYmmdd_HHMMSS.xml`。

## 詳細使用說明

### GUI 介面操作

1. **啟動程式**：執行 `python sitemap_gui.py`
2. **設定參數**：
   - 起始網址：預設為 `https://pm.shiny.com.tw/`
   - 執行緒數量：可調整並發爬取數量
3. **客製化設定**：點擊「客製化設定」按鈕，可調整：
   - **基本設定**：起始網址、執行緒數量、請求延遲、最大深度
   - **爬蟲設定**：User-Agent、請求超時、自動保存間隔
   - **權重設定**：各種頁面類型的 priority 權重
   - **排除規則**：要排除的路徑列表
   - 設定會自動儲存到 `config.json` 檔案
4. **讀取進度**：點擊「讀取進度」按鈕載入之前的爬取進度
5. **開始爬取**：點擊「啟動爬蟲」按鈕
6. **監控進度**：觀察爬取進度和統計資訊
   - **本次統計**：顯示本次 session 新增的網址數量
   - **累積統計**：顯示總計的網址數量
   - **robots.txt 狀態**：啟動時自動抓取 robots.txt，GUI 會顯示「已排除收錄robots.txt阻擋清單」，點擊可直接開啟 robots.txt 網址
7. **停止爬取**：可隨時點擊「停止」按鈕中斷爬取
8. **自動保存**：程式會每5秒自動保存進度到 `crawl_temp_YYYYmmdd_HHMMSS.pkl`
9. **生成 Sitemap**：爬取完成後自動生成 `sitemap_YYYYmmdd_HHMMSS.xml`

### 客製化設定說明

點擊「客製化設定」按鈕可以開啟完整的設定視窗，分為四個標籤頁：

#### 1. 基本設定
- **起始網址**：設定要爬取的網站首頁
- **執行緒數量**：並發爬取的工作執行緒數（建議 1-10）
- **請求延遲**：每次請求之間的延遲時間（秒）
- **最大深度**：爬取的深度限制

#### 2. 爬蟲設定
- **User-Agent**：設定請求標頭，模擬瀏覽器行為
- **請求超時**：每個網頁請求的超時時間（秒）
- **自動保存間隔**：自動保存進度的時間間隔（秒）
 - （資訊）robots.txt 檢查：啟動時自動請求 `起始網址/robots.txt`，若可取得則狀態顯示為綠色並支援點擊開啟

#### 3. 權重設定
可調整各種頁面類型在 sitemap 中的 priority 權重（0.0 到 1.0）：
- 首頁（1.0）
- 商品頁（0.7）
- 清單頁（0.7-0.9）
- 新聞頁（0.9）
- 關於頁（0.8）
- 其他頁面（0.7）

#### 4. 排除規則
可設定要排除的路徑，每行一個，例如：
```
/login.php
/member.php
/register.php
/admin.php
```

#### 5. 自訂規則（正則表達式）
可設定多組自訂 URL 過濾規則：
- **規則名稱**：自訂規則的顯示名稱
- **URL 必須包含**：URL 必須包含的文字（可選）
- **正則表達式**：匹配 URL 的正則表達式
- **動作**：
  - `exclude`：排除匹配的 URL
  - `include`：只保留匹配的 URL

範例：
- 排除 menu.php 的 page=1 參數：
  - URL 必須包含：`/menu.php`
  - 正則表達式：`[\\?&]page=1($|&)`
  - 動作：`exclude`

設定完成後點擊「儲存設定」按鈕即可保存，設定會儲存在 `config.json` 檔案中。

---

## 補充說明

### 專案目標與適用對象
本工具適合網站管理者、SEO 工程師，或有大量自動化 sitemap 產生需求的團隊。可快速產生結構化 sitemap，提升搜尋引擎收錄效率。

### 常見問題 Q&A

**Q1: GUI 無法啟動怎麼辦？**
A: 請確認已安裝 tkinter，並使用 Python 3.7 以上版本。

**Q2: 進度檔損毀怎麼辦？**
A: 建議先備份進度檔，刪除損毀檔案後重新開始，或聯絡維護者協助。

**Q3: 產生的 sitemap 沒有預期網址？**
A: 請檢查 SitemapGen/Custom-made/URL_RULES.md，確認網址是否被排除規則過濾。

### 進階設定

- **自訂排除規則**：可編輯 `SitemapGen/Custom-made/URL_RULES.md`，調整收錄與排除條件。
- **priority 權重調整**：同樣於 SitemapGen/Custom-made/URL_RULES.md 內調整各類型頁面權重。
- **批次處理**：可多次執行、續爬，適合大型網站。

### 聯絡方式
如有問題請聯絡程式維護者，或於 GitHub 提出 issue。

1. **啟動程式**：執行 `python sitemap_gui.py`
2. **設定參數**：
   - 起始網址：預設為 `https://pm.shiny.com.tw/`
   - 輸出檔名：自動產生 `sitemap_YYYYmmdd_HHMMSS.xml`
   - 執行緒數量：可調整並發爬取數量
3. **讀取進度**：點擊「讀取進度」按鈕載入之前的爬取進度
4. **開始爬取**：點擊「開始爬蟲」按鈕
5. **監控進度**：觀察爬取進度和統計資訊
   - **本次統計**：顯示本次 session 新增的網址數量
   - **累積統計**：顯示總計的網址數量
6. **停止爬取**：可隨時點擊「停止」按鈕中斷爬取
7. **自動保存**：程式會每5秒自動保存進度到 `crawl_temp_YYYYmmdd_HHMMSS.pkl`
8. **生成 Sitemap**：爬取完成後自動生成 `sitemap_YYYYmmdd_HHMMSS.xml`

### 進度檔案說明

- `crawl_temp_YYYYmmdd_HHMMSS.pkl`：主要進度暫存檔，包含：
  - `crawled_urls`：已爬取的網址集合
  - `valid_sitemap_urls`：有效的 sitemap 網址集合
  - `urls_to_crawl`：待爬取的網址佇列
  - `rule1_count`、`rule2_count`、`rule3_count`：規則計數
  - **自動命名**：每次啟動程式時自動產生，避免覆蓋之前的進度

### 網址收錄規則

#### 權重設定（Priority）
- **首頁**：`1.0`
- **商品頁**（含 `/product-detail.php`）：`0.7`
- **清單頁**（含 `/menu.php`）：
  - 無參數：`0.9`
  - 有參數但無 `page=`：`0.85`
  - 有 `page=` 參數：`0.8`
- **新聞頁**（結尾 `/news.php` 或 `/news-detail.php`）：`0.9`
- **關於頁**（結尾 `/about.php`）：`0.8`
- **購物說明頁**（含 `/shopping_explanation.php`）：`0.8`
- **其他頁面**：`0.7`

#### 排除規則
- 含以下路徑的網址不會收錄：
  - `/login.php`
  - `/member.php`
  - `/register.php`
- 只收錄同網域的網址
- 自動去除重複網址
- 清單頁若含 `page=1` 參數會被排除

## 工具說明

### scripts/ 目錄

- **convert_progress_to_sitemap.py**：將進度檔案轉換為 sitemap_YYYYmmdd_HHMMSS.xml
- **convert_progress_to_sitemap_ok.py**：已驗證的轉換腳本

### tools/ 目錄

- **remove_page1.py**：移除 sitemap 中 `page=1` 參數的工具
- **sitemap_gui.spec**：PyInstaller 打包設定檔
- **docs/SITEMAP_RULES.md**：詳細的規則說明文件
- **build/**：編譯過程產生的臨時檔案
- **dist/**：最終的可執行檔案

### autosave/ 目錄

- **自動保存目錄**：存放生成的 sitemap 檔案
  - `sitemap_YYYYmmdd_HHMMSS.xml`：自動產生的 sitemap 檔案，包含完整的 URL 資料

## 進階功能

### 自訂規則

您可以修改 `src/sitemap_generator.py` 中的函數來自訂：

1. **網址篩選規則**：修改 `is_valid_url()` 函數
2. **權重設定**：修改 `get_priority()` 函數
3. **內容驗證**：修改 `is_valid_content()` 函數

### 批次處理

對於大型網站，建議：

1. 分段爬取：設定較小的爬取範圍
2. 定期保存：利用自動保存功能
3. 合併結果：使用腳本合併多個進度檔案

### 效能優化

- 調整 `MAX_WORKERS` 參數控制並發數
- 設定適當的 `REQUEST_DELAY` 避免過度請求
- 使用 `HEAD` 請求進行初步篩選

## 故障排除

### 常見問題

1. **爬取中斷**：
   - 檢查網路連線
   - 確認目標網站可正常訪問
   - 檢查防火牆設定

2. **記憶體不足**：
   - 減少 `MAX_WORKERS` 數量
   - 定期清理快取
   - 分段處理大型網站

3. **生成檔案錯誤**：
   - 檢查進度檔案是否完整
   - 確認輸出目錄權限
   - 驗證網址格式

4. **GUI 功能問題**：
   - **讀取進度功能**：v1.5 已修復，現在可完整載入進度並繼續爬取
   - **統計數字不一致**：v1.5 已修復，現在「本次」和「累積」統計會正確對應
   - **停止按鈕無效**：v1.5 已修復，現在可正常停止爬取
   - **Threading 錯誤**：v1.5 已修復，避免主執行緒結束後的錯誤

### 日誌分析

程式會輸出詳細的日誌資訊，包括：
- 爬取進度
- 錯誤訊息
- 統計資訊
- 效能指標

## 技術規格

- **語言**：Python 3.7+
- **GUI 框架**：Tkinter
- **HTTP 請求**：requests
- **HTML 解析**：BeautifulSoup4
- **並發處理**：ThreadPoolExecutor
- **資料序列化**：pickle

## 版本歷史

- **v1.0**：基本爬蟲功能
- **v1.1**：新增 GUI 介面
- **v1.2**：優化權重設定規則
- **v1.3**：新增進度保存功能
- **v1.4**：重構檔案結構，提升可維護性
- **v1.5**：修復功能問題，完善 GUI 功能實現
- **v1.6**：實作時間戳檔案命名，避免檔案覆蓋，提升版本管理

## 授權資訊

本專案僅供學習和研究使用，請遵守相關網站的 robots.txt 和使用條款。

## 聯絡方式

如有問題或建議，請聯絡專案維護者。

---

**注意**：使用本工具時請確保遵守目標網站的使用條款，避免對伺服器造成過大負擔。

## 快速使用說明

### 主要工具（一般用戶）
1. 啟動 `sitemap_gui.py`（雙擊或命令列執行）。
2. 輸入起始網址，選擇執行緒數量。
3. 按下「開始」自動爬取，完成後自動產生 `sitemap_YYYYmmdd_HHMMSS.xml`。
4. 所有網址去重、首頁唯一化、分頁排除、常見無效頁面排除都自動完成。
5. 產生的 `sitemap_YYYYmmdd_HHMMSS.xml` 可直接上傳給搜尋引擎。

### 進階批次處理（選用）
- 適合需合併多次進度、或自訂規則的技術用戶。
- 執行 `src/sitemap_generator.py` 內的 `export_sitemap_with_priority_from_progress`，可從進度檔（`crawl_temp_YYYYmmdd_HHMMSS.pkl`）批次產生 `sitemap_YYYYmmdd_HHMMSS.xml`。
- 可自訂 `config.json` 進行更細緻的網址過濾。

---

一般用戶只需用主要工具即可，進階批次處理為選用功能。
