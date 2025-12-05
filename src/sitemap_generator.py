import os
import sys
import pickle
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qsl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import re

# --- 設定區 ---
# 請將此處改為您網站的起始網址
START_URL = "https://pm.shiny.com.tw/" 
# 輸出檔案名稱

from datetime import datetime

# 啟動時記錄開始時間
START_TIME_STR = datetime.now().strftime("%Y%m%d_%H%M%S")

# 動態產生進度暫存檔名
def get_progress_filename():
    return f"crawl_temp_{START_TIME_STR}.pkl"

# 動態產生 sitemap 輸出檔名
def get_sitemap_filename():
    return f"sitemap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"


def create_sitemap(valid_sitemap_urls, output_filename=None):
    """
    依據有效網址集合，輸出 sitemap 檔案
    """
    if output_filename is None:
        output_filename = get_sitemap_filename()
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            from xml.sax.saxutils import escape
            for url in valid_sitemap_urls:
                url_escaped = escape(url)
                f.write(f'  <url><loc>{url_escaped}</loc></url>\n')
            f.write('</urlset>\n')
        print(f"--- Sitemap 已成功生成: {output_filename} ---")
    except Exception as e:
        print(f"Sitemap 檔案更新失敗: {e}")

def save_empty_pages_report(empty_pages_log):
    """
    將空頁面記錄儲存為 CSV 報告
    """
    if not empty_pages_log:
        return
    
    filename = f"empty_pages_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        with open(filename, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["發現時間", "頁面類型", "問題頁面 URL", "來源頁面 (Referrer)"])
            for log in empty_pages_log:
                writer.writerow([
                    log.get("timestamp", ""),
                    log.get("type", ""),
                    log.get("url", ""),
                    log.get("referrer", "")
                ])
        print(f"--- 空頁面報告已生成: {filename} ---")
    except Exception as e:
        print(f"空頁面報告生成失敗: {e}")

def run_crawler(start_url, progress_callback=None, num_threads=3, is_running_func=None, initial_state=None, crawling_url_callback=None, config=None):
    """
    爬取網站並即時回報進度，結束後自動產生 sitemap.xml
    """
    base_netloc = urlparse(start_url).netloc
    # 若有 initial_state 則續接進度，否則初始化
    if initial_state:
        urls_to_crawl = set(initial_state.get("urls_to_crawl", [start_url]))
        if not urls_to_crawl:
            urls_to_crawl = set([start_url])
        crawled_urls = set(initial_state.get("crawled_urls", []))
        valid_sitemap_urls = set(initial_state.get("valid_sitemap_urls", []))
        rule1_count = initial_state.get("rule1_count", 0)
        rule2_count = initial_state.get("rule2_count", 0)
        rule3_count = initial_state.get("rule3_count", 0)
        url_referrers = initial_state.get("url_referrers", {start_url: None})
        empty_pages_log = initial_state.get("empty_pages_log", [])
    else:
        urls_to_crawl = set([start_url])
        crawled_urls = set()
        valid_sitemap_urls = set()
        rule1_count = 0
        rule2_count = 0
        rule3_count = 0
        url_referrers = {start_url: None}
        empty_pages_log = []
    lock = threading.Lock()

    def crawl_url(current_url):
        # 新增：執行前檢查是否要停止
        if is_running_func and not is_running_func():
            return [], None
        nonlocal rule1_count, rule2_count, rule3_count
        with lock:
            if current_url in crawled_urls:
                return [], None
            crawled_urls.add(current_url)
            referrer = url_referrers.get(current_url, "Unknown")
        print(f"正在分析: {current_url}")
        new_links = []
        is_valid_page = False
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 SitemapGeneratorBot'
            }
            response = requests.get(current_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"  -> 狀態碼異常: {response.status_code}, 跳過此頁面")
                return [], None
            soup = BeautifulSoup(response.content, 'html.parser')
            # 讀取空頁面偵測設定
            empty_page_config = config.get('empty_page_detection', {})
            
            # 1. 商品詳細頁判斷
            p_cfg = empty_page_config.get('product_detail', {
                "url_pattern": "/product-detail.php",
                "breadcrumb_selector": ".breadcrumb",
                "container_selector": "div.row",
                "title_selector": ".product-title"
            })
            
            if p_cfg['url_pattern'] in current_url:
                # 新版判斷邏輯：從 breadcrumb 後的 row 找 .product-title
                breadcrumb = soup.select_one(p_cfg['breadcrumb_selector'])
                if not breadcrumb:
                    # 找不到 breadcrumb，預設為有效頁面
                    is_valid_page = True
                    with lock:
                        rule1_count += 1
                    print(f"  -> [規則1] 找不到 {p_cfg['breadcrumb_selector']}，預設為有效頁面")
                else:
                    # 找到 breadcrumb 後的第一個容器 (如 div.row)
                    # 從 container_selector 解析出 class 名稱 (例如 "div.row" -> "row")
                    container_cls = p_cfg['container_selector'].replace('div.', '').replace('.', '')
                    row_div = breadcrumb.find_next('div', class_=container_cls)
                    
                    if not row_div:
                        is_valid_page = True
                        with lock:
                            rule1_count += 1
                        print(f"  -> [規則1] 找不到 {p_cfg['container_selector']}，預設為有效頁面")
                    else:
                        # 在 row 內找 .product-title
                        product_title = row_div.select_one(p_cfg['title_selector'])
                        if product_title:
                            title_text = product_title.get_text(strip=True)
                            if title_text:
                                is_valid_page = True
                                with lock:
                                    rule1_count += 1
                                print(f"  -> [規則1] 商品頁驗證通過 (標題: {title_text[:30]}...)")
                            else:
                                # .product-title 存在但內容為空
                                print(f"  -> [規則1] 商品頁驗證失敗 ({p_cfg['title_selector']} 為空)")
                                with lock:
                                    empty_pages_log.append({
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "type": "空商品頁",
                                        "url": current_url,
                                        "referrer": referrer
                                    })
                        else:
                            # 找不到 .product-title，視為空商品頁
                            print(f"  -> [規則1] 商品頁驗證失敗 (找不到 {p_cfg['title_selector']})")
                            with lock:
                                empty_pages_log.append({
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "type": "空商品頁",
                                    "url": current_url,
                                    "referrer": referrer
                                })

            # 2. 商品列表頁判斷
            elif True: # 使用 elif True 配合內部判斷，避免變數 scope 問題
                l_cfg = empty_page_config.get('product_list', {
                    "url_pattern": "/menu.php",
                    "breadcrumb_selector": "nav.breadcrumb",
                    "container_selector": "div.row",
                    "product_link_selector": "a[href*='product-detail.php']",
                    "card_selector": ".card",
                    "pagination_empty_pattern": "0-0/0"
                })
                
                if l_cfg['url_pattern'] in current_url:
                    # 新版判斷邏輯：依據規格書實作
                    is_empty_list = False
                    empty_reason = ""
                    
                    # 1. 找到唯一的 breadcrumb
                    breadcrumb = soup.select_one(l_cfg['breadcrumb_selector'])
                    if not breadcrumb:
                        # 找不到 breadcrumb，預設為有效頁面
                        is_valid_page = True
                        with lock:
                            rule2_count += 1
                        print(f"  -> [規則2] 找不到 {l_cfg['breadcrumb_selector']}，預設為有效頁面")
                    else:
                        # 2. 找到 breadcrumb 後的第一個 div.row (商品列表容器)
                        container_cls = l_cfg['container_selector'].replace('div.', '').replace('.', '')
                        row_div = breadcrumb.find_next('div', class_=container_cls)
                        
                        if not row_div:
                            # 找不到商品列表容器，預設為有效頁面
                            is_valid_page = True
                            with lock:
                                rule2_count += 1
                            print(f"  -> [規則2] 找不到商品列表容器 {l_cfg['container_selector']}，預設為有效頁面")
                        else:
                            # 3. 檢查商品相關元素
                            product_links = row_div.select(l_cfg['product_link_selector'])
                            cards = row_div.select(l_cfg['card_selector'])
                            
                            if product_links or cards:
                                # 發現商品相關元素，為有效頁面
                                is_valid_page = True
                                with lock:
                                    rule2_count += 1
                                print(f"  -> [規則2] 清單頁驗證通過 (發現 {len(product_links)} 個商品連結, {len(cards)} 個卡片)")
                            else:
                                # 4. 檢查 innerText 是否為空
                                inner_text = row_div.get_text(strip=True)
                                if inner_text:
                                    # 商品列表容器有內容
                                    is_valid_page = True
                                    with lock:
                                        rule2_count += 1
                                    print(f"  -> [規則2] 清單頁驗證通過 (列表有內容: {inner_text[:30]}...)")
                                else:
                                    # 5. 檢查分頁資訊
                                    import re
                                    page_text = soup.get_text()
                                    pagination_pattern = l_cfg['pagination_empty_pattern']
                                    
                                    if re.search(pagination_pattern, page_text):
                                        is_empty_list = True
                                        empty_reason = f"分頁顯示 {pagination_pattern}，且列表為空"
                                    else:
                                        # 列表為空但無分頁確認，仍視為空列表
                                        is_empty_list = True
                                        empty_reason = "商品列表容器為空"
                                    
                                    if is_empty_list:
                                        print(f"  -> [規則2] 清單頁驗證失敗 ({empty_reason})")
                                        with lock:
                                            empty_pages_log.append({
                                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                "type": "空清單頁",
                                                "url": current_url,
                                                "referrer": referrer
                                            })
                else:
                    is_valid_page = True
                    with lock:
                        rule3_count += 1
                    print("  -> [規則3] 其他頁面，預設為有效")
            if is_valid_page:
                with lock:
                    valid_sitemap_urls.add(current_url)
                print(f"[即時統計] 商品頁: {rule1_count} 清單頁: {rule2_count} 其他頁: {rule3_count}  有效頁面總數: {rule1_count + rule2_count + rule3_count}")
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(start_url, href)
                    absolute_url = absolute_url.split('#')[0]
                    if urlparse(absolute_url).netloc == base_netloc:
                        new_links.append(absolute_url)
        except requests.exceptions.RequestException as e:
            print(f"  -> 請求錯誤: {e}, 跳過此頁面")
        time.sleep(0.1)
        return new_links, current_url

    print("--- 開始爬取網站 ---")
    max_workers = num_threads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while urls_to_crawl:
            if is_running_func and not is_running_func():
                break
            batch = list(urls_to_crawl)
            urls_to_crawl.clear()
            futures = []
            for url in batch:
                if is_running_func and not is_running_func():
                    break
                if crawling_url_callback:
                    crawling_url_callback(url)
                futures.append(executor.submit(crawl_url, url))
            for future in as_completed(futures):
                # 新增：處理結果前檢查是否要停止
                if is_running_func and not is_running_func():
                    break
                new_links, finished_url = future.result()
                for link in new_links:
                    with lock:
                        if link not in crawled_urls:
                            urls_to_crawl.add(link)
                            if link not in url_referrers:
                                url_referrers[link] = finished_url
                # 即時回報進度
                if progress_callback:
                    progress_callback({
                        "crawled_urls": set(crawled_urls),
                        "valid_sitemap_urls": set(valid_sitemap_urls),
                        "urls_to_crawl": set(urls_to_crawl),
                        "rule1_count": rule1_count,
                        "rule2_count": rule2_count,
                        "rule3_count": rule3_count,
                        "url_referrers": url_referrers,
                        "empty_pages_log": empty_pages_log
                    })
    # 最後一次回報
    if progress_callback:
        progress_callback({
            "crawled_urls": set(crawled_urls),
            "valid_sitemap_urls": set(valid_sitemap_urls),
            "urls_to_crawl": set(urls_to_crawl),
            "rule1_count": rule1_count,
            "rule2_count": rule2_count,
            "rule3_count": rule3_count,
            "url_referrers": url_referrers,
            "empty_pages_log": empty_pages_log
        })
    print("\n--- 爬取完成 ---")
    print(f"總共掃描 {len(crawled_urls)} 個網址")
    print(f"找到 {len(valid_sitemap_urls)} 個有效網址")
    print(f"商品頁: {rule1_count} 清單頁: {rule2_count} 其他頁: {rule3_count}")
    print(f"所有有效頁面總數: {rule1_count + rule2_count + rule3_count}")
    # --- 生成 sitemap.xml 檔案 ---
    generate_xml_file(valid_sitemap_urls, config=config)
    # --- 生成空頁面報告 ---
    save_empty_pages_report(empty_pages_log)
    return crawled_urls, valid_sitemap_urls, urls_to_crawl

def generate_xml_file(urls, output_filename=None, config=None):
    """
    根據收集到的有效 URL 生成 sitemap.xml 檔案
    """
    if not urls:
        print("沒有找到任何有效的 URL，無法生成 sitemap.xml")
        return

    if output_filename is None:
        # 預設存到 autosave/sitemap.xml
        os.makedirs("autosave", exist_ok=True)
        output_filename = os.path.join("autosave", "sitemap.xml")

    homepage = START_URL if START_URL.endswith('/') else START_URL + '/'
    homepage_variants = {
        homepage,
        homepage.rstrip('/'),
        homepage.rstrip('/') + '/index.php'
    }
    urls = set(urls)
    if any(u in urls for u in homepage_variants):
        urls -= homepage_variants
        urls.add(homepage)

    # 讀取設定檔
    cfg = config if config else {}
    if not cfg:
        try:
            import json
            if os.path.exists('setup_rules/config.json'):
                with open('setup_rules/config.json', 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
        except Exception:
            pass

    # 讀取排除路徑 (不再使用 hardcoded explicit_exclude)
    explicit_exclude = cfg.get('excluded_paths', []) or []
    urls = {u for u in urls if not any(p in u for p in explicit_exclude)}

    urls = apply_custom_rules(urls)

    # 讀取可選的 GUI 設定
    exclude_nonstandard_index = cfg.get('exclude_nonstandard_index_path', True)
    enable_abnormal_filter = cfg.get('enable_abnormal_query_filter', True)

    # 依 SEO 規則進一步過濾：/index.php/ 與異常參數（可透過 GUI 開關）
    if exclude_nonstandard_index:
        urls = {u for u in urls if not is_nonstandard_index_path(u)}
    if enable_abnormal_filter:
        urls = {u for u in urls if not has_abnormal_query(u)}

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    url_list = sorted(list(urls), key=lambda x: (0 if x == homepage else 1, x))
    
    # 讀取權重設定
    priorities = cfg.get('priorities', {})
    
    from xml.sax.saxutils import escape
    for url in url_list:
        priority = '0.5' # 預設值
        
        if url == homepage:
            priority = str(priorities.get('homepage', 1.0))
        else:
            # 嘗試匹配路徑關鍵字
            matched = False
            # 這裡需要一個靈活的匹配機制，目前先支援 config 中的 key 作為路徑部分匹配
            # 例如: "product_detail": 0.7 -> if "product_detail" in url: priority = 0.7
            # 但 config key 可能是 "product" 或 "product_detail"，需要一種對應方式
            # 簡單實作：遍歷 priorities keys，若 key 在 url 中則使用該 priority
            # 注意：這可能會誤判，例如 "news" 匹配 "newsletter"
            
            # 為了相容舊版 PM 站邏輯與新版通用邏輯，我們保留一些特定判斷，但優先使用 config
            
            # 1. 直接匹配 config 中的 key (如果 key 是路徑的一部分)
            # 排序 keys 以確保長度長的先匹配 (避免 "news" 蓋過 "news-detail")
            sorted_keys = sorted(priorities.keys(), key=len, reverse=True)
            for key in sorted_keys:
                if key == "homepage" or key == "default": continue
                
                # 特殊處理：PM 站的 key 是功能名稱而非路徑，需映射
                # 但新版 config_default.json 的 key 是 "product", "category" 等，可直接當關鍵字
                # 舊版 config_custom.json 的 key 是 "product_detail", "menu_no_params" 等
                
                # 嘗試直接匹配 key
                if key in url:
                    priority = str(priorities[key])
                    matched = True
                    break
                
                # 舊版 PM 站特定映射 (為了相容性)
                if key == "product_detail" and "/product-detail.php" in url:
                    priority = str(priorities[key])
                    matched = True
                    break
                if key == "menu_no_params" and "/menu.php" in url and "?" not in url:
                    priority = str(priorities[key])
                    matched = True
                    break
                if key == "menu_with_params" and "/menu.php" in url and "?" in url and "page=" not in url:
                    priority = str(priorities[key])
                    matched = True
                    break
                if key == "menu_with_page" and "/menu.php" in url and "page=" in url:
                    priority = str(priorities[key])
                    matched = True
                    break
                if key == "news" and ("/news.php" in url or "/news-detail.php" in url):
                    priority = str(priorities[key])
                    matched = True
                    break
                if key == "about" and "/about.php" in url:
                    priority = str(priorities[key])
                    matched = True
                    break
                if key == "shopping_explanation" and "/shopping_explanation.php" in url:
                    priority = str(priorities[key])
                    matched = True
                    break
            
            if not matched:
                priority = str(priorities.get('default', 0.7))

        url_escaped = escape(url)
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{url_escaped}</loc>\n'
        xml_content += f'    <priority>{priority}</priority>\n'
        xml_content += '  </url>\n'

    xml_content += '</urlset>'

    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    print(f"\n--- Sitemap 已成功生成: {output_filename} ---")
    # 已產生 sitemap.xml，無自動開啟

def apply_custom_rules(urls):
    """
    套用自訂規則過濾 URL
    """
    import re
    import os
    
    # 讀取 config.json
    config_file = "setup_rules/config.json"
    if not os.path.exists(config_file):
        # 如果沒有 setup_rules/config.json，使用舊的邏輯
        return remove_menu_page1(urls)
    
    try:
        import json
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        custom_rules = config.get("custom_rules", [])
    except Exception:
        # 讀取失敗時使用舊的邏輯
        return remove_menu_page1(urls)
    
    if not custom_rules:
        # 沒有自訂規則時使用舊的邏輯
        return remove_menu_page1(urls)
    
    result = set()
    for url in urls:
        should_exclude = False
        should_include = False
        
        # 檢查所有規則
        for rule in custom_rules:
            pattern = rule.get("pattern", "")
            url_contains = rule.get("url_contains", "")
            action = rule.get("action", "exclude")
            
            # 檢查 URL 是否包含指定字串
            if url_contains and url_contains not in url:
                continue
            
            # 檢查是否匹配正則表達式
            if pattern and re.search(pattern, url):
                if action == "exclude":
                    should_exclude = True
                elif action == "include":
                    should_include = True
        
        # 包含規則優先於排除規則，如果都沒匹配則預設包含
        if should_include or (not should_exclude and not should_include):
            result.add(url)
    
    return result

def remove_menu_page1(urls):
    """
    排除 /menu.php?cid=xxx&page=1 這種網址，只保留 page=1 參數以外的 menu.php（舊版邏輯）
    """
    import re
    result = set()
    for url in urls:
        if '/menu.php' in url and re.search(r'[\?&]page=1($|&)', url):
            continue
        result.add(url)
    return result

def is_nonstandard_index_path(url: str) -> bool:
    """/index.php/ 非標準路徑需排除"""
    return '/index.php/' in url

def has_abnormal_query(url: str) -> bool:
    """依 SEO 文件定義偵測異常參數，任一條件成立即視為異常。"""
    parsed = urlparse(url)
    if not parsed.query:
        return False

    # 拆解參數（允許重複鍵）
    params = parse_qsl(parsed.query, keep_blank_values=True)
    name_to_values = {}
    for k, v in params:
        name_to_values.setdefault(k, []).append(v)

    # 規則 1: page 參數重複
    if 'page' in name_to_values and len(name_to_values['page']) > 1:
        return True

    # 規則 4: 參數名稱異常
    dangerous_substrings = ['script', 'http', '<', '>', "'", '"', '{', '}', '[', ']']
    for name in name_to_values.keys():
        if len(name) > 30:
            return True
        lname = name.lower()
        if any(s in lname for s in dangerous_substrings):
            return True

    # 規則 2/3: 指定名稱且值異常；值異常的通用檢查也對所有參數套用
    special_names = {
        'type','mode','action','keywords','sa','sntz','usg',
        'ovraw','ovkey','ovmtc','ovadid','ovkwid','ovcampgid','ovadgrpid'
    }

    def value_is_abnormal(value: str) -> bool:
        if value is None:
            return True
        v = value
        if v == '':
            return True
        if '///' in v or 'http://' in v or 'https://' in v:
            return True
        # 全部為非英數
        import re
        if not re.search(r'[A-Za-z0-9]', v):
            return True
        # 連續重複同一字元4次以上
        if re.search(r'(.)\1{3,}', v):
            return True
        # 長度 > 10 且無母音（疑似亂碼）
        if len(v) > 10 and not re.search(r'[AEIOUaeiou]', v):
            return True
        # 長度 > 50
        if len(v) > 50:
            return True
        return False

    for name, values in name_to_values.items():
        # 指定名稱需要值正常，否則異常
        if name.lower() in special_names:
            for val in values:
                if value_is_abnormal(val):
                    return True
        # 對所有參數值做通用異常檢查
        for val in values:
            if value_is_abnormal(val):
                return True

    return False

def export_sitemap_with_priority_from_progress(progress_pkl_path, output_dir="."):
    import pickle
    from datetime import datetime
    # 讀取進度檔
    with open(progress_pkl_path, "rb") as f:
        d = pickle.load(f)
    urls = d.get("valid_sitemap_urls", set())
    if not urls:
        print("進度檔無有效網址，無法輸出 sitemap")
        return
    # 處理首頁網址，只保留 https://pm.shiny.com.tw/
    homepage = "https://pm.shiny.com.tw/"
    homepage_variants = {
        "https://pm.shiny.com.tw/",
        "https://pm.shiny.com.tw",
        "https://pm.shiny.com.tw/index.php"
    }
    urls = set(urls)
    if any(u in urls for u in homepage_variants):
        urls -= homepage_variants
        urls.add(homepage)
    # 產生檔名
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"sitemap_{now_str}.xml")
    print(f"將 {len(urls)} 筆網址輸出到 {out_path}")
    # 依原本權重規則產生 XML
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    from xml.sax.saxutils import escape
    url_priority_list = []
    for url in urls:
        if url == homepage:
            priority = 1.0
        elif '/product-detail.php' in url:
            priority = 0.7
        elif '/menu.php' in url:
            priority = 0.9
        elif '/news-detail.php' in url:
            priority = 0.8
        elif '/news.php' in url:
            priority = 0.85
        elif '/about.php' in url:
            priority = 0.85
        elif '/shopping_explanation.php' in url:
            priority = 0.8
        else:
            priority = 0.7
        url_priority_list.append((priority, url))
    # 首頁放第一筆，其餘依 priority 由大到小，網址長度由小到大排序
    url_priority_list.sort(key=lambda x: (0 if x[1] == homepage else 1, -x[0], len(x[1]), x[1]))
    for priority, url in url_priority_list:
        url_escaped = escape(url)
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{url_escaped}</loc>\n'
        xml_content += f'    <priority>{priority:.1f}</priority>\n'
        xml_content += '  </url>\n'
    xml_content += '</urlset>'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    print(f"已輸出 sitemap: {out_path}")

if __name__ == "__main__":
    # 預設直接匯出進度檔內容
    export_sitemap_with_priority_from_progress("sitemap_crawl_temp.pkl", output_dir="autosave")


