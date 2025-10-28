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
OUTPUT_FILENAME = "sitemap.xml"

def create_sitemap(valid_sitemap_urls, output_filename):
    """
    依據有效網址集合，輸出 sitemap.xml
    """
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for url in valid_sitemap_urls:
                f.write(f'  <url><loc>{url}</loc></url>\n')
            f.write('</urlset>\n')
        print(f"--- Sitemap 已成功生成: {output_filename} ---")
    except Exception as e:
        print(f"sitemap.xml 更新失敗: {e}")

def run_crawler(start_url, progress_callback=None, num_threads=3, is_running_func=None, initial_state=None):
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
    else:
        urls_to_crawl = set([start_url])
        crawled_urls = set()
        valid_sitemap_urls = set()
        rule1_count = 0
        rule2_count = 0
        rule3_count = 0
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
            if '/product-detail.php' in current_url:
                product_name_element = soup.find(id="product_name")
                if product_name_element and product_name_element.get('value', '').strip():
                    is_valid_page = True
                    with lock:
                        rule1_count += 1
                    print("  -> [規則1] 商品頁驗證通過 (商品名稱存在)")
                elif product_name_element and product_name_element.get_text(strip=True):
                    is_valid_page = True
                    with lock:
                        rule1_count += 1
                    print("  -> [規則1] 商品頁驗證通過 (商品名稱存在)")
                else:
                    print("  -> [規則1] 商品頁驗證失敗 (商品名稱為空)")
            elif '/menu.php' in current_url:
                breadcrumb = soup.find('nav', class_='breadcrumb')
                if breadcrumb:
                    row_div = breadcrumb.find_next_sibling('div', class_='row')
                    if row_div:
                        if row_div.get_text(strip=True):
                            is_valid_page = True
                            with lock:
                                rule2_count += 1
                            print("  -> [規則2] 清單頁驗證通過 (列表有內容)")
                        else:
                            print("  -> [規則2] 清單頁驗證失敗 (列表為空)")
                    else:
                        is_valid_page = True
                        with lock:
                            rule2_count += 1
                        print("  -> [規則2] 找不到 div.row，預設為有效頁面")
                else:
                    is_valid_page = True
                    with lock:
                        rule2_count += 1
                    print("  -> [規則2] 找不到 breadcrumb，預設為有效頁面")
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
                # 新增：分派前檢查是否要停止
                if is_running_func and not is_running_func():
                    break
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
                # 即時回報進度
                if progress_callback:
                    progress_callback({
                        "crawled_urls": set(crawled_urls),
                        "valid_sitemap_urls": set(valid_sitemap_urls),
                        "urls_to_crawl": set(urls_to_crawl),
                        "rule1_count": rule1_count,
                        "rule2_count": rule2_count,
                        "rule3_count": rule3_count
                    })
    # 最後一次回報
    if progress_callback:
        progress_callback({
            "crawled_urls": set(crawled_urls),
            "valid_sitemap_urls": set(valid_sitemap_urls),
            "urls_to_crawl": set(urls_to_crawl),
            "rule1_count": rule1_count,
            "rule2_count": rule2_count,
            "rule3_count": rule3_count
        })
    print("\n--- 爬取完成 ---")
    print(f"總共掃描 {len(crawled_urls)} 個網址")
    print(f"找到 {len(valid_sitemap_urls)} 個有效網址")
    print(f"商品頁: {rule1_count} 清單頁: {rule2_count} 其他頁: {rule3_count}")
    print(f"所有有效頁面總數: {rule1_count + rule2_count + rule3_count}")
    # --- 生成 sitemap.xml 檔案 ---
    generate_xml_file(valid_sitemap_urls)
    return crawled_urls, valid_sitemap_urls, urls_to_crawl

def generate_xml_file(urls):
    """
    根據收集到的有效 URL 生成 sitemap.xml 檔案
    """
    if not urls:
        print("沒有找到任何有效的 URL，無法生成 sitemap.xml")
        return

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

    # 明確排除頁面（根據 SEO 規則）
    explicit_exclude = [
        '/recover_product_detail.php',
        '/keeping.php',
        '/logout.php',
        '/login.php',
        '/register.php',
        '/member.php',
        '/order_query.php',
        '/order_detail.php',
        '/money_transfer.php',
        '/vip_contract.php',
        '/member_contract.php',
        '/wholesaler_contract.php',
    ]
    urls = {u for u in urls if not any(p in u for p in explicit_exclude)}

    urls = apply_custom_rules(urls)

    # 讀取可選的 GUI 設定
    exclude_nonstandard_index = True
    enable_abnormal_filter = True
    try:
        import json
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                exclude_nonstandard_index = cfg.get('exclude_nonstandard_index_path', True)
                enable_abnormal_filter = cfg.get('enable_abnormal_query_filter', True)
                # 合併 GUI 中自訂的 excluded_paths
                extra_excluded = cfg.get('excluded_paths', []) or []
                if extra_excluded:
                    urls = {u for u in urls if not any(p in u for p in extra_excluded)}
    except Exception:
        pass

    # 依 SEO 規則進一步過濾：/index.php/ 與異常參數（可透過 GUI 開關）
    if exclude_nonstandard_index:
        urls = {u for u in urls if not is_nonstandard_index_path(u)}
    if enable_abnormal_filter:
        urls = {u for u in urls if not has_abnormal_query(u)}

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    url_list = sorted(list(urls), key=lambda x: (0 if x == homepage else 1, x))
    for url in url_list:
        # 權重規則
        if url == homepage:
            priority = '1.0'
        elif '/product-detail.php' in url:
            priority = '0.7'
        elif url.endswith('/menu.php'):
            priority = '0.9'
        elif '/menu.php?' in url:
            if 'page=' in url:
                priority = '0.8'
            else:
                priority = '0.85'
        elif url.endswith('/news.php') or url.endswith('/news-detail.php'):
            priority = '0.9'
        elif url.endswith('/about.php'):
            priority = '0.8'
        elif '/about.php?paction=186' in url:
            priority = '0.9'
        elif '/shopping_explanation.php' in url:
            priority = '0.8'
        else:
            priority = '0.7'

        xml_content += '  <url>\n'
        xml_content += f'    <loc>{url}</loc>\n'
        xml_content += f'    <priority>{priority}</priority>\n'
        xml_content += '  </url>\n'

    xml_content += '</urlset>'

    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    print(f"\n--- Sitemap 已成功生成: {OUTPUT_FILENAME} ---")
    # 已產生 sitemap.xml，無自動開啟

def apply_custom_rules(urls):
    """
    套用自訂規則過濾 URL
    """
    import re
    import os
    
    # 讀取 config.json
    config_file = "config.json"
    if not os.path.exists(config_file):
        # 如果沒有 config.json，使用舊的邏輯
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
    export_sitemap_with_priority_from_progress("sitemap_progress.pkl", output_dir="here_you_are")


