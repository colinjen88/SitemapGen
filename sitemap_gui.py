import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from sitemap_generator import create_sitemap
import threading
import time
from tkinter import ttk, messagebox
import tkinter as tk
import os
import pickle

CRAWLED_FILE = "crawled_urls.pkl"
VALID_FILE = "valid_sitemap_urls.pkl"
TOCRAWL_FILE = "urls_to_crawl.pkl"

class SitemapApp:
    def autosave_progress(self):
        # 只在爬蟲運行時才執行自動儲存
        if not self.is_running:
            # 如果爬蟲未運行，延長檢查間隔到 30 秒
            self.root.after(30000, self.autosave_progress)
            return
            
        # 簡化日誌輸出，只在有變化時才輸出詳細資訊
        progress_file = "sitemap_progress.pkl"
        has_changes = False
        
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "rb") as f:
                    old = pickle.load(f)
                old_crawled = set(old.get("crawled_urls", set()))
                new_crawled = set(self.crawled_urls) - old_crawled
                old_valid = set(old.get("valid_sitemap_urls", set()))
                new_valid = set(self.valid_sitemap_urls) - old_valid
                
                # 只有當有新資料時才輸出詳細日誌
                if new_crawled or new_valid:
                    has_changes = True
                    print(f"[autosave_progress] 新增 crawled_urls: {len(new_crawled)} 筆")
                    print(f"[autosave_progress] 新增 valid_sitemap_urls: {len(new_valid)} 筆")
            except Exception:
                pass
        
        self.save_progress(self.crawled_urls, self.valid_sitemap_urls, self.to_crawl, self.rule1_count, self.rule2_count, self.rule3_count)
        
        if has_changes:
            print("[autosave_progress] 已儲存進度到 sitemap_progress.pkl")
        
        # 爬蟲運行時每 5 秒檢查一次，未運行時每 30 秒檢查一次
        interval = 5000 if self.is_running else 30000
        self._autosave_id = self.root.after(interval, self.autosave_progress)
    def update_gui_periodically(self):
        # 更新進度條
        self.progress.config(value=len(self.crawled_urls))
        
        # 讀取累積進度檔
        progress_file = "sitemap_progress.pkl"
        accumulated_crawled = set()
        accumulated_valid = set()
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "rb") as f:
                    data = pickle.load(f)
                    accumulated_crawled = set(data.get("crawled_urls", set()))
                    accumulated_valid = set(data.get("valid_sitemap_urls", set()))
            except Exception:
                pass
        
        # 計算統計數字
        acc_total = len(accumulated_crawled)
        acc_valid = len(accumulated_valid)
        
        # 計算本次新增的數據
        session_new_crawled = self.crawled_urls - self.session_start_crawled
        session_new_valid = self.valid_sitemap_urls - self.session_start_valid
        session_new_total = len(session_new_crawled)
        session_new_valid_count = len(session_new_valid)
        cur_to_crawl = len(self.to_crawl)
        
        # 計算分類統計
        acc_rule1 = len([url for url in accumulated_crawled if '/product-detail.php' in url])
        acc_rule2 = len([url for url in accumulated_crawled if '/menu.php' in url])
        acc_rule3 = acc_total - acc_rule1 - acc_rule2
        
        # 計算本次新增的分類統計
        session_new_rule1 = len([url for url in session_new_crawled if '/product-detail.php' in url])
        session_new_rule2 = len([url for url in session_new_crawled if '/menu.php' in url])
        session_new_rule3 = session_new_total - session_new_rule1 - session_new_rule2
        
        # 更新顯示
        self.label_stats.config(text=f"本次已爬：{session_new_total}　有效：{session_new_valid_count}　待爬：{cur_to_crawl}\n累積已爬：{acc_total}　有效：{acc_valid}")
        self.label_rule_count.config(text=f"本次 商品頁: {session_new_rule1}　清單頁: {session_new_rule2}　其他頁: {session_new_rule3} ｜ 累積 商品頁: {acc_rule1}　清單頁: {acc_rule2}　其他頁: {acc_rule3}")
    def __init__(self, root):
        self.root = root
        self.root.title("Sitemap Generator GUI")
        self.root.geometry("640x560")
        self.root.configure(bg="#f8f8f8")
        self.is_running = False
        self.thread = None
        self.threads = []
        self.num_threads = tk.IntVar(value=3)
        # 新增爬蟲進度資料結構
        self.crawled_urls = set()
        self.valid_sitemap_urls = set()
        self.to_crawl = set()
        self._gui_updater_id = None
        self._autosave_id = None  # 用於追蹤自動儲存的定時器 ID
        
        # 本次 session 的起始數據（用於計算本次新增）
        self.session_start_crawled = set()
        self.session_start_valid = set()

        # 三種規則頁面計數
        self.rule1_count = 0
        self.rule2_count = 0
        self.rule3_count = 0

        # 標題
        title = ttk.Label(root, text="Sitemap Generator", font=("Segoe UI", 20, "bold"))
        title.pack(pady=(18, 8))

        # 起始網址
        frm_url = ttk.Frame(root)
        frm_url.pack(pady=5)
        ttk.Label(frm_url, text="起始網址：", font=("Segoe UI", 12)).pack(side=tk.LEFT)
        self.entry_url = ttk.Entry(frm_url, width=52, font=("Segoe UI", 12))
        self.entry_url.pack(side=tk.LEFT, padx=5)
        self.entry_url.insert(0, "https://pm.shiny.com.tw/")

        # 執行緒數量選擇
        frm_threads = ttk.Frame(root)
        frm_threads.pack(pady=5)
        ttk.Label(frm_threads, text="執行緒數量：", font=("Segoe UI", 12)).pack(side=tk.LEFT)
        self.combo_threads = ttk.Combobox(frm_threads, textvariable=self.num_threads, values=[1,2,3,4,5,6,7,8,9,10], width=5, state="readonly")
        self.combo_threads.pack(side=tk.LEFT, padx=5)

        # 狀態
        self.label_status = ttk.Label(root, text="狀態：等待啟動", font=("Segoe UI", 14), background="#f8f8f8")
        self.label_status.pack(pady=(12, 6))

        # 進度條
        self.progress = ttk.Progressbar(root, orient="horizontal", length=540, mode="determinate")
        self.progress.pack(pady=6)

        # 進度統計（本次/累積）
        self.label_stats = ttk.Label(root, text="本次已爬：0　有效：0　待爬：0\n累積已爬：0　累積有效：0", font=("Segoe UI", 13, "bold"), background="#f8f8f8", foreground="#2a4d8f")
        self.label_stats.pack(pady=8)

        # 三種規則頁面數量顯示
        frm_rule = ttk.Frame(root)
        frm_rule.pack(pady=3)
        self.label_rule_count = ttk.Label(frm_rule, text="商品頁: 0　清單頁: 0　其他頁: 0", font=("Segoe UI", 12), foreground="blue", width=60, anchor="w")
        self.label_rule_count.pack(side=tk.LEFT, padx=5)



        # 分散式進度
        frm_dist = ttk.Frame(root)
        frm_dist.pack(pady=3)
        ttk.Label(frm_dist, text="分散式進度：", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.label_dist = ttk.Label(frm_dist, text="--", font=("Segoe UI", 11), foreground="purple", width=60, anchor="w")
        self.label_dist.pack(side=tk.LEFT, padx=5)

        # robots.txt 狀態
        frm_robots = ttk.Frame(root)
        frm_robots.pack(pady=3)
        ttk.Label(frm_robots, text="robots.txt 狀態：", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.label_robots = ttk.Label(frm_robots, text="--", font=("Segoe UI", 11), foreground="blue", width=60, anchor="w")
        self.label_robots.pack(side=tk.LEFT, padx=5)

        # sitemap.xml 狀態
        frm_sitemap = ttk.Frame(root)
        frm_sitemap.pack(pady=3)
        ttk.Label(frm_sitemap, text="sitemap.xml 狀態：", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.label_sitemap = ttk.Label(frm_sitemap, text="--", font=("Segoe UI", 11), foreground="blue", width=60, anchor="w")
        self.label_sitemap.pack(side=tk.LEFT, padx=5)

        # 錯誤訊息
        frm_error = ttk.Frame(root)
        frm_error.pack(pady=3)
        ttk.Label(frm_error, text="錯誤：", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.label_error = ttk.Label(frm_error, text="--", font=("Segoe UI", 11), foreground="red", width=60, anchor="w")
        self.label_error.pack(side=tk.LEFT, padx=5)

        # 按鈕區
        frm_btn = ttk.Frame(root)
        frm_btn.pack(pady=(22, 10))
        self.btn_start = ttk.Button(frm_btn, text="啟動爬蟲", command=self.start_crawler, width=20)
        self.btn_start.pack(side=tk.LEFT, padx=12)
        self.btn_stop = ttk.Button(frm_btn, text="停止爬蟲", command=self.stop_crawler, state=tk.DISABLED, width=20)
        self.btn_stop.pack(side=tk.LEFT, padx=12)
        self.btn_load_progress = ttk.Button(frm_btn, text="讀取進度", command=self.load_progress, width=20)
        self.btn_load_progress.pack(side=tk.LEFT, padx=12)

        # 啟動自動儲存進度（只在爬蟲運行時才執行）
        # self.autosave_progress()  # 改為在開始爬蟲時才啟動

    def load_progress(self):
        import glob
        from tkinter import filedialog
        # 搜尋所有進度檔
        progress_files = glob.glob("*.pkl")
        if not progress_files:
            messagebox.showinfo("進度讀取", "找不到任何進度檔！")
            return
        # 彈出檔案選擇視窗
        file_path = filedialog.askopenfilename(title="選擇進度檔", filetypes=[("Pickle Files", "*.pkl")], initialdir=os.getcwd())
        if not file_path:
            return
        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
            
            # 實際載入數據到程式中
            self.crawled_urls = set(data.get("crawled_urls", set()))
            self.valid_sitemap_urls = set(data.get("valid_sitemap_urls", set()))
            self.to_crawl = set(data.get("urls_to_crawl", set()))
            self.rule1_count = data.get("rule1_count", 0)
            self.rule2_count = data.get("rule2_count", 0)
            self.rule3_count = data.get("rule3_count", 0)
            
            # 記錄本次 session 的起始數據
            self.session_start_crawled = set(self.crawled_urls)
            self.session_start_valid = set(self.valid_sitemap_urls)
            
            # 更新顯示
            crawled = len(self.crawled_urls)
            valid = len(self.valid_sitemap_urls)
            to_crawl = len(self.to_crawl)
            self.label_stats.config(text=f"讀取進度檔：{os.path.basename(file_path)}\n已爬：{crawled}　有效：{valid}　待爬：{to_crawl}")
            self.progress["value"] = crawled
            
            # 更新分類統計
            rule1 = len([url for url in self.crawled_urls if '/product-detail.php' in url])
            rule2 = len([url for url in self.crawled_urls if '/menu.php' in url])
            rule3 = crawled - rule1 - rule2
            self.label_rule_count.config(text=f"本次 商品頁: {rule1}　清單頁: {rule2}　其他頁: {rule3} ｜ 累積 商品頁: {rule1}　清單頁: {rule2}　其他頁: {rule3}")
            
            messagebox.showinfo("進度讀取成功", f"已成功載入進度檔：{os.path.basename(file_path)}\n可繼續爬取剩餘的 {to_crawl} 個網址")
            
        except Exception as e:
            messagebox.showerror("進度讀取失敗", f"讀取失敗：{e}")

        # 固定 label 寬度，避免畫面跳動
        for lbl in [self.label_seo, self.label_alert, self.label_dist, self.label_robots, self.label_sitemap, self.label_error]:
            lbl.config(width=60)


    def on_close(self):
        # 關閉視窗時，強制停止爬蟲執行緒
        self.is_running = False
        try:
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)
        except Exception:
            pass
        self.root.destroy()

    def start_crawler(self):
        self.is_running = True
        def run():
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.label_status.config(text="狀態：爬蟲執行中...")
            self.progress["value"] = 0

            start_url = self.entry_url.get().strip()
            if not start_url:
                messagebox.showwarning("警告", "請輸入起始網址！")
                self.stop_crawler()
                return

            # 只在第一次啟動時初始化本次 session 的進度
            progress_file = "sitemap_progress.pkl"
            if os.path.exists(progress_file) and not self.crawled_urls:
                try:
                    with open(progress_file, "rb") as f:
                        data = pickle.load(f)
                    self.crawled_urls = set(data.get("crawled_urls", set()))
                    self.valid_sitemap_urls = set(data.get("valid_sitemap_urls", set()))
                    self.to_crawl = set(data.get("urls_to_crawl", set()))
                    self.rule1_count = data.get("rule1_count", 0)
                    self.rule2_count = data.get("rule2_count", 0)
                    self.rule3_count = data.get("rule3_count", 0)
                    
                    # 記錄本次 session 的起始數據
                    self.session_start_crawled = set(self.crawled_urls)
                    self.session_start_valid = set(self.valid_sitemap_urls)
                except Exception:
                    pass

            # 啟動自動儲存進度
            self.autosave_progress()

            def progress_callback(data):
                self.crawled_urls = data["crawled_urls"]
                self.valid_sitemap_urls = data["valid_sitemap_urls"]
                self.to_crawl = data["urls_to_crawl"]
                self.rule1_count = data.get("rule1_count", 0)
                self.rule2_count = data.get("rule2_count", 0)
                self.rule3_count = data.get("rule3_count", 0)
                # 使用 thread-safe 的方式更新 GUI
                try:
                    self.root.after(0, self.update_gui_periodically)
                except RuntimeError:
                    # 如果主執行緒已經結束，忽略錯誤
                    pass

            from src.sitemap_generator import run_crawler, create_sitemap
            num_threads = self.num_threads.get()
            import concurrent.futures
            def run_crawler_with_threads():
                # 加入 is_running 狀態檢查
                if not self.is_running:
                    return
                # 傳遞 is_running 檢查函數
                run_crawler(start_url, progress_callback, num_threads, lambda: self.is_running)
            t = threading.Thread(target=run_crawler_with_threads)
            self.threads.append(t)
            t.start()

            # 等待所有爬蟲執行緒結束
            for t in self.threads:
                while t.is_alive():
                    if not self.is_running:
                        break
                    t.join(timeout=0.5)

            self.is_running = False
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.label_status.config(text="狀態：等待啟動")
            self.progress["value"] = 100
            self.save_progress(self.crawled_urls, self.valid_sitemap_urls, self.to_crawl, self.rule1_count, self.rule2_count, self.rule3_count)
            create_sitemap(list(self.valid_sitemap_urls), "sitemap.xml")

        self.thread = threading.Thread(target=run)
        self.thread.start()
        if self._gui_updater_id:
            self.root.after_cancel(self._gui_updater_id)
            self._gui_updater_id = None

    def stop_crawler(self):
        # 停止爬蟲
        self.is_running = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.label_status.config(text="狀態：已停止")
        if self._gui_updater_id:
            self.root.after_cancel(self._gui_updater_id)
            self._gui_updater_id = None
        # 停止自動儲存
        if self._autosave_id:
            self.root.after_cancel(self._autosave_id)
            self._autosave_id = None
        # 等待所有執行緒結束
        for t in getattr(self, 'threads', []):
            if t.is_alive():
                t.join(timeout=2)
        self.threads = []

    def crawl_url(self, url, crawled_urls, valid_sitemap_urls, to_crawl, start_url):
        from urllib.parse import urljoin
        import requests
        from bs4 import BeautifulSoup

        # 爬蟲設定
        max_depth = 3
        depth = 0

        # 網頁解析
        def parse_page(url, base_url):
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
            except Exception as e:
                return str(e)

            # 檢查 robots.txt
            if not check_robots(url):
                return "robots.txt 限制存取"

            # 儲存網頁內容
            save_page(response.text, url)

            # 解析網址
            soup = BeautifulSoup(response.text, "html.parser")
            links = set()
            for a_tag in soup.find_all("a", href=True):
                link = urljoin(url, a_tag["href"])
                if is_valid_url(link, base_url):
                    links.add(link)

            return links

        # 網址合法性檢查
        def is_valid_url(url, base_url):
            if not url.startswith(base_url):
                return False
            if url in crawled_urls:
                return False
            return True

        # 儲存網頁內容
        def save_page(content, url):
            try:
                # 取得相對網址
                rel_url = url.replace("https://", "").replace("http://", "").strip("/")
                file_name = rel_url.replace("/", "_") + ".html"

                # 儲存為 HTML 檔案
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(content)

                # 更新 sitemap.xml
                valid_sitemap_urls.add(url)
                self.update_sitemap(valid_sitemap_urls)

            except Exception as e:
                return str(e)

        # 檢查 robots.txt
        def check_robots(url):
            try:
                robots_url = urljoin(url, "/robots.txt")
                response = requests.get(robots_url, timeout=5)
                response.raise_for_status()

                # 解析 robots.txt
                disallow = False
                for line in response.text.splitlines():
                    if line.startswith("User-agent:"):
                        disallow = False
                    if disallow and line.startswith("/"):
                        disallow = True
                    if not disallow and line.startswith("Allow:"):
                        disallow = False

                return not disallow

            except Exception:
                return True  # 無法取得 robots.txt 時，預設允許存取

        # 爬蟲主程式
        while depth < max_depth and self.is_running:
            links = parse_page(url, start_url)
            if isinstance(links, str):
                self.add_error(url, links)
                break

            # 新增待爬網址
            to_crawl.update(links - crawled_urls)
            depth += 1

    def save_progress(self, crawled_urls, valid_sitemap_urls, to_crawl, rule1_count=0, rule2_count=0, rule3_count=0):
        # 修正合併邏輯：僅在本次進度有新網址時才累積到舊進度
        progress_file = "sitemap_progress.pkl"
        old = {}
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "rb") as f:
                    old = pickle.load(f)
            except Exception:
                old = {}
        old_crawled = set(old.get("crawled_urls", set()))
        old_valid = set(old.get("valid_sitemap_urls", set()))
        old_to_crawl = set(old.get("urls_to_crawl", set()))
        new_crawled = set(crawled_urls)
        new_valid = set(valid_sitemap_urls)
        new_to_crawl = set(to_crawl)
        # 直接 union 舊進度與本次 session 的所有資料
        merged_crawled = old_crawled | new_crawled
        merged_valid = old_valid | new_valid
        merged_to_crawl = old_to_crawl | new_to_crawl
        merged = {
            "crawled_urls": merged_crawled,
            "valid_sitemap_urls": merged_valid,
            "urls_to_crawl": merged_to_crawl,
            "rule1_count": old.get("rule1_count", 0) + rule1_count,
            "rule2_count": old.get("rule2_count", 0) + rule2_count,
            "rule3_count": old.get("rule3_count", 0) + rule3_count
        }
        
        # 計算新增的網址
        new_crawled_diff = new_crawled - old_crawled
        new_valid_diff = new_valid - old_valid
        
        # 只在有實際變化時才輸出日誌
        if new_crawled_diff or new_valid_diff:
            print(f"[save_progress] 合併結果: 已爬={len(merged_crawled)} 有效={len(merged_valid)} 待爬={len(merged_to_crawl)}")
            if new_crawled_diff:
                print(f"[save_progress] 新增 crawled_urls: {len(new_crawled_diff)} 筆")
            if new_valid_diff:
                print(f"[save_progress] 新增 valid_sitemap_urls: {len(new_valid_diff)} 筆")
        try:
            with open(progress_file, "wb") as f:
                pickle.dump(merged, f)
            # 只在有變化時才輸出寫入成功訊息
            if new_crawled_diff or new_valid_diff:
                print(f"[save_progress] 寫入成功: 已爬:{len(merged['crawled_urls'])} 有效:{len(merged['valid_sitemap_urls'])} 待爬:{len(merged['urls_to_crawl'])}")
        except Exception as e:
            print(f"[save_progress] 寫入失敗: {e}")

    def add_error(self, url, error):
        # 記錄錯誤到日誌檔案
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("error_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {url} - {error}\n")
        except Exception as e:
            print(f"無法寫入錯誤日誌: {e}")

    def update_sitemap(self, valid_sitemap_urls):
        # 更新 sitemap.xml 檔案
        try:
            create_sitemap(list(valid_sitemap_urls), "sitemap.xml")
            self.label_sitemap.config(text="sitemap.xml 更新成功", foreground="green")
        except Exception as e:
            self.label_sitemap.config(text=f"sitemap.xml 更新失敗：{e}", foreground="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = SitemapApp(root)

    def on_closing():
        try:
            app.is_running = False
            # 嘗試終止所有執行緒
            for t in getattr(app, 'threads', []):
                if t.is_alive():
                    t.join(timeout=2)
        except Exception:
            pass
        root.destroy()
        import sys
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
