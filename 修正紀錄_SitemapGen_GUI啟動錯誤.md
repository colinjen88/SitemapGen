# SitemapGen GUI 啟動錯誤與修正紀錄

## 問題描述

在執行 `python sitemap_gui.py` 啟動 GUI 主程式時，反覆出現如下錯誤：

```
UnboundLocalError: cannot access local variable 'old_crawled' where it is not associated with a value
```

錯誤發生於 `sitemap_gui.py` 的 `save_progress` 方法，於進行差集運算 `new_crawled_diff = new_crawled - old_crawled` 時，`old_crawled` 尚未被正確初始化。

## 問題原因

- `old_crawled`、`old_valid`、`old_to_crawl` 的初始化位置錯誤，導致在 try/except 或差集運算前未定義。
- Python 的區域變數賦值與作用域規則，若 try/except 內有重新賦值，外部變數會被遮蔽，造成未定義錯誤。

## 修正步驟

1. **將 `old_crawled`、`old_valid`、`old_to_crawl` 的初始化移到 `save_progress` 函式最前面**：
   ```python
   old_crawled = set()
   old_valid = set()
   old_to_crawl = set()
   ```
2. **讀取進度檔時只用 clear()/update() 覆蓋內容，不重新賦值**：
   ```python
   if os.path.exists(progress_file):
       try:
           with open(progress_file, "rb") as f:
               old = pickle.load(f)
               old_crawled.clear()
               old_crawled.update(old.get("crawled_urls", set()))
               old_valid.clear()
               old_valid.update(old.get("valid_sitemap_urls", set()))
               old_to_crawl.clear()
               old_to_crawl.update(old.get("urls_to_crawl", set()))
       except Exception:
           pass
   ```
3. **差集運算與後續合併邏輯放在初始化之後**：
   ```python
   new_crawled = set(crawled_urls)
   new_valid = set(valid_sitemap_urls)
   new_to_crawl = set(to_crawl)
   new_crawled_diff = new_crawled - old_crawled
   new_valid_diff = new_valid - old_valid
   ```

## 驗證結果

- 修正後，`python sitemap_gui.py` 可正常啟動 GUI，UnboundLocalError 完全消失。
- 進度儲存與合併功能可正常運作。

## 建議

- 任何涉及 try/except 及區域變數的初始化，務必將變數宣告於函式最前面，避免作用域遮蔽。
- 進行集合運算前，務必確保所有參與變數皆已初始化。

---

如需進一步細節或程式片段，請參考 `sitemap_gui.py` 內 `save_progress` 方法最新版本。