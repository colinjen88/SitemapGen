# Sitemap 生成器專案

## 專案簡介

這是一個自動化網站爬蟲工具，專門用於生成符合 SEO 標準的 sitemap.xml 檔案。程式會自動爬取指定網站，依據預設規則篩選有效網址，並產生結構化的 sitemap 檔案。

## 主要功能

- **自動網站爬取**：從指定起始網址開始，自動發現並爬取所有相關頁面
- **智能網址篩選**：依據預設規則自動排除不需要的網址（如登入頁面、會員頁面等）
- **權重設定**：根據頁面類型自動設定適當的 priority 值
- **進度保存**：支援中斷後續爬取，避免重複工作
- **GUI 介面**：提供友善的圖形化操作介面
- **批次處理**：支援大量網址的高效處理

## 檔案結構

```
sitemap_progress/
├── sitemap_gui.py              # 主程式（GUI 介面）
├── src/
│   └── sitemap_generator.py   # 核心爬蟲引擎
├── scripts/
│   ├── convert_progress_to_sitemap.py      # 進度轉換腳本
│   └── convert_progress_to_sitemap_ok.py   # 進度轉換腳本（已驗證）
├── tools/
│   ├── remove_page1.py         # 移除 page=1 參數的工具
│   ├── sitemap_gui.spec        # PyInstaller 打包設定檔
│   ├── SITEMAP_RULES.md        # 詳細規則說明
│   ├── build/                  # 編譯輸出目錄
│   └── dist/                   # 分發目錄
├── output/
│   └── here_you_are/           # 生成的 sitemap 檔案存放處
│       └── sitemap_20250912_094425.xml
├── sitemap_progress.pkl         # 主要進度檔案（保留在外層）
├── progress.pkl                # 備用進度檔案
└── README.md                   # 本說明文件
```

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

## 詳細使用說明

### GUI 介面操作

1. **啟動程式**：執行 `python sitemap_gui.py`
2. **設定參數**：
   - 起始網址：預設為 `https://pm.shiny.com.tw/`
   - 輸出檔名：預設為 `sitemap_py.xml`
3. **開始爬取**：點擊「開始爬取」按鈕
4. **監控進度**：觀察爬取進度和統計資訊
5. **自動保存**：程式會自動保存進度到 `sitemap_progress.pkl`
6. **生成 Sitemap**：爬取完成後自動生成 sitemap.xml

### 進度檔案說明

- `sitemap_progress.pkl`：主要進度檔案，包含：
  - `crawled_urls`：已爬取的網址集合
  - `valid_sitemap_urls`：有效的 sitemap 網址集合
  - `to_crawl`：待爬取的網址佇列
- `progress.pkl`：備用進度檔案

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

- **convert_progress_to_sitemap.py**：將進度檔案轉換為 sitemap.xml
- **convert_progress_to_sitemap_ok.py**：已驗證的轉換腳本

### tools/ 目錄

- **remove_page1.py**：移除 sitemap 中 `page=1` 參數的工具
- **sitemap_gui.spec**：PyInstaller 打包設定檔
- **SITEMAP_RULES.md**：詳細的規則說明文件
- **build/**：編譯過程產生的臨時檔案
- **dist/**：最終的可執行檔案

### output/ 目錄

- **here_you_are/**：存放生成的 sitemap 檔案
  - `sitemap_20250912_094425.xml`：包含 4,001 筆 URL 資料的 sitemap 檔案

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

## 授權資訊

本專案僅供學習和研究使用，請遵守相關網站的 robots.txt 和使用條款。

## 聯絡方式

如有問題或建議，請聯絡專案維護者。

---

**注意**：使用本工具時請確保遵守目標網站的使用條款，避免對伺服器造成過大負擔。
