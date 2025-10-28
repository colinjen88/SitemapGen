# SEO 排除收錄規則與網址列表

## 一、明確排除（強制 noindex, nofollow）

下列網址一律加上 `<meta name="robots" content="noindex, nofollow">`，不允許搜尋引擎收錄：

- recover_product_detail.php
- keeping.php
- logout.php
- login.php
- register.php
- member.php
- order_query.php
- order_detail.php
- money_transfer.php
- vip_contract.php
- member_contract.php
- wholesaler_contract.php

---

## 二、特殊情境排除

### 1. 404 頁面
- 只要 HTTP 狀態碼為 404，則一律加上 noindex, nofollow。

### 2. index.php
- 如果網址中出現 `/index.php/`（非標準路徑），或
- 偵測到「異常參數」（見下方說明），
- 則加上 noindex, nofollow。

### 3. category.php、charts.php、menu.php
- 這些頁面僅在偵測到「異常參數」時才加上 noindex, nofollow。

---

## 三、異常參數判斷規則

只要 $_GET 參數有下列情形之一，視為異常參數，該頁面會被加上 noindex, nofollow：

1. `page` 參數在網址中出現超過一次。
2. 參數名稱為下列之一，且其值有異常（見下方）：
   - type, mode, action, keywords, sa, sntz, usg, OVRAW, OVKEY, OVMTC, OVADID, OVKWID, OVCAMPGID, OVADGRPID
3. 參數值異常的判斷條件（任一符合即為異常）：
   - 值為空字串
   - 包含連續三個以上的斜線（/ 或 \）
   - 包含 http:// 或 https://
   - 參數值全部為符號（非英數字）
   - 連續重複同一字元4次以上（如 aaaa）
   - 長度超過10且完全沒有母音（aeiou，疑似亂碼）
   - 長度超過50
4. 參數名稱異常（任一符合即為異常）：
   - 名稱長度超過30
   - 名稱包含 script、http、<、>、'、"、{、}、[、] 等字串或符號

---

## 四、總結

- 只要是上述明確列出的檔案名稱，或遇到 404、異常參數、非標準 index.php 路徑，該頁面都會被加上 noindex, nofollow，不被搜尋引擎收錄。
- 其它頁面則依正常 SEO 流程處理。