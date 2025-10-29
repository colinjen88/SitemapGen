# Sitemap Generator 規則說明

## 功能簡介
本程式會自動爬取指定網站，依據下列規則產生 sitemap.xml，並自動排除不需要的網址，適合 SEO 使用。

---

## 使用方式
1. 修改 `sitemap_generator.py` 中的 `START_URL` 為你的網站首頁網址。
2. 執行程式，會自動產生 sitemap.xml。
3. 也可用進度檔（sitemap_crawl_temp.pkl）匯出 sitemap。

---

## 網址收錄規則

### 首頁網址
- 只保留一個首頁網址（以 `START_URL` 為準，結尾自動補 `/`）。
- 排除以下首頁變體，只留標準首頁：
  - `https://你的網址/`
  - `https://你的網址`
  - `https://你的網址/index.php`
- 首頁網址會排在 sitemap 第一筆，priority 設為 1.0。

### 權重設定（priority）
- 首頁：`1.0`
- 商品頁（含 `/product-detail.php`）：`0.7`
- 清單頁（含 `/menu.php`）：
  - `/menu.php`（無參數）：`0.9`
  - `/menu.php?`（有參數但沒有 `page=`）：`0.85`
  - `/menu.php?`（有 `page=` 參數，如 `/menu.php?cid=3&page=2`）：`0.8`
- 新聞頁（結尾 `/news.php` 或 `/news-detail.php`）：`0.9`
- 關於頁（結尾 `/about.php`）：`0.8`
- 關於頁（如 `/about.php?paction=186`）：`0.9`
- 購物說明頁（含 `/shopping_explanation.php`）：`0.8`
- 其他頁面：`0.7`

### 排除網址
- 含以下路徑的網址不會收錄：
  - `/login.php`
  - `/member.php`
  - `/register.php`
- 只收錄同網域的網址（不會收錄外部網站連結）。
- 網址重複只保留一筆（自動去除重複）。
- 清單頁（`/menu.php`）若網址含 `page=1` 參數（如 `/menu.php?cid=3&page=1`），會被排除，只保留不含 `page=1` 的網址（如 `/menu.php?cid=3`）。

---

## 其他說明
- 商品頁會檢查商品名稱是否存在，清單頁會檢查列表內容，其餘頁面預設有效。
- sitemap.xml 產生後會自動開啟檔案。
- 進度檔可用於中斷後續產生 sitemap。
- 網址排序：首頁排第一，其餘依規則排序（如權重、網址長度等）。

---

## 檔案說明
- `sitemap.xml`：產生的 sitemap 檔案。
- `sitemap_crawl_temp.pkl`：爬蟲進度暫存檔，可用於匯出 sitemap。

---

