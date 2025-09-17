import os
import sys
import pickle
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import pickle
import re

# --- 設定區 ---
# 請將此處改為您網站的起始網址
START_URL = "https://pm.shiny.com.tw/" 
# 輸出檔案名稱
OUTPUT_FILENAME = "sitemap_py.xml"

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

def run_crawler(start_url, progress_callback=None, num_threads=3, is_running_func=None):
    """
    爬取網站並即時回報進度，結束後自動產生 sitemap.xml
    """
    base_netloc = urlparse(start_url).netloc
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
            soup = BeautifulSoup(response.content, 'lxml')
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

    exclude_patterns = ['/login.php', '/member.php', '/register.php']
    urls = {u for u in urls if not any(p in u for p in exclude_patterns)}

    urls = remove_menu_page1(urls)

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
    try:
        import webbrowser
        import os
        webbrowser.open('file://' + os.path.abspath(OUTPUT_FILENAME))
    except Exception as e:
        print(f"[自動開啟失敗] {e}")

def remove_menu_page1(urls):
    """
    排除 /menu.php?cid=xxx&page=1 這種網址，只保留 page=1 參數以外的 menu.php
    """
    import re
    result = set()
    for url in urls:
        if '/menu.php' in url and re.search(r'[\?&]page=1($|&)', url):
            continue
        result.add(url)
    return result

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


