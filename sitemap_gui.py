import sys
import os
from datetime import datetime
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
from src.sitemap_generator import generate_xml_file, run_crawler, get_progress_filename, get_sitemap_filename
import threading
import time
from tkinter import ttk, messagebox
import tkinter as tk
import pickle


# 啟動時記錄開始時間
START_TIME_STR = datetime.now().strftime("%Y%m%d_%H%M%S")
def get_gui_progress_file():
    return f"crawl_temp_{START_TIME_STR}.pkl"

class SitemapApp:
    def __init__(self, root):
        self.generate_xml_file = generate_xml_file
        self.run_crawler = run_crawler
        self.progress_file = get_gui_progress_file()

        self.root = root
        self.root.title("Sitemap Generator GUI")
        self.root.geometry("700x640")
        self.is_running = False
        self.can_resume = False  # 新增：是否可繼續抓取
        self.threads = []
        self.num_threads = tk.IntVar(value=3)
        self.crawled_urls = set()
        self.valid_sitemap_urls = set()
        self.to_crawl = set()
        self.rule1_count = 0
        self.rule2_count = 0
        self.rule3_count = 0
        self.session_start_crawled = set()
        self.session_start_valid = set()
        self.session_start_rule1 = 0
        self.session_start_rule2 = 0
        self.session_start_rule3 = 0
        self._gui_updater_id = None
        self._autosave_id = None
        # 標題
        title = ttk.Label(self.root, text="Sitemap Generator", font=("Segoe UI", 20, "bold"))
        title.pack(pady=(18, 8))
        # 起始網址
        frm_url = ttk.Frame(self.root)
        frm_url.pack(pady=5)
        ttk.Label(frm_url, text="起始網址：", font=("Segoe UI", 12)).pack(side=tk.LEFT)
        self.entry_url = ttk.Entry(frm_url, width=52, font=("Segoe UI", 12))
        self.entry_url.pack(side=tk.LEFT, padx=5)
        self.entry_url.insert(0, "https://pm.shiny.com.tw/")
        # 執行緒數量 + 客製化設定在同一排
        frm_top = ttk.Frame(self.root)
        frm_top.pack(pady=5)
        ttk.Label(frm_top, text="執行緒數量：", font=("Segoe UI", 12)).pack(side=tk.LEFT)
        self.combo_threads = ttk.Combobox(frm_top, textvariable=self.num_threads, values=["1","2","3","4","5","6","7","8","9","10"], width=5, state="readonly")
        self.combo_threads.pack(side=tk.LEFT, padx=5)
        btn_custom = ttk.Button(frm_top, text="客製化設定", command=self.open_custom_settings)
        btn_custom.pack(side=tk.LEFT, padx=14)
        # 進度條動畫 Canvas
        self.progress_canvas = tk.Canvas(self.root, width=540, height=24, bg='#e6e6e6', highlightthickness=0)
        self.progress_canvas.pack(pady=8)
        self._scan_anim_offset = 0
        self._scan_anim_job = self.root.after(50, self._animate_scanning_bar)
        # 狀態顯示
        self.label_status = ttk.Label(self.root, text="狀態：等待啟動", font=("Segoe UI", 12), foreground="black")
        self.label_status.pack(pady=6)
        # 新增_爬取檔案即時區（約6行高度）
        frm_list = ttk.Frame(self.root)
        frm_list.pack(pady=3)
        self.crawl_file_list = tk.Text(frm_list, height=6, width=80, font=("Consolas", 10), state="disabled", bg="#f4f4f4")
        self.crawl_file_list.pack(side=tk.LEFT)
        scrollbar = ttk.Scrollbar(frm_list, orient="vertical", command=self.crawl_file_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.crawl_file_list.configure(yscrollcommand=scrollbar.set)
        # 統一累積/本次統計於一排
        self.label_stats = ttk.Label(self.root, text="【進度報告】已爬：0 | 有效：0 | 商品頁：0 | 清單頁：0 | 其他頁：0", font=("Segoe UI", 13, "bold"), background="#f8f8f8", foreground="#2a4d8f")
        self.label_stats.pack(pady=8)
        # robots.txt 狀態
        frm_robots = ttk.Frame(self.root)
        frm_robots.pack(pady=3)
        ttk.Label(frm_robots, text="robots.txt 狀態：", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.label_robots = ttk.Label(frm_robots, text="--", font=("Segoe UI", 11), foreground="blue", width=60, anchor="w", cursor="hand2")
        self.label_robots.pack(side=tk.LEFT, padx=5)
        self.label_robots.bind("<Button-1>", self.open_robots_url)
        self._robots_url = None
        self._robots_text = None
        self._robots_summary = None
        # sitemap.xml 狀態
        frm_sitemap = ttk.Frame(self.root)
        frm_sitemap.pack(pady=3)
        ttk.Label(frm_sitemap, text="sitemap.xml 狀態：", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.label_sitemap = ttk.Label(frm_sitemap, text="--", font=("Segoe UI", 11), foreground="blue", width=60, anchor="w", cursor="hand2")
        self.label_sitemap.pack(side=tk.LEFT, padx=5)
        self.label_sitemap.bind("<Button-1>", self.open_sitemap_file)
        
        # 進度檔顯示
        frm_progress = ttk.Frame(self.root)
        frm_progress.pack(pady=3)
        ttk.Label(frm_progress, text="進度檔：", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.label_progress_file = ttk.Label(frm_progress, text="--", font=("Segoe UI", 11), foreground="#888888", width=60, anchor="w")
        self.label_progress_file.pack(side=tk.LEFT, padx=5)
        self.update_progress_file_label()

        # 錯誤訊息
        frm_error = ttk.Frame(self.root)
        frm_error.pack(pady=3)
        ttk.Label(frm_error, text="錯誤：", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.label_error = ttk.Label(frm_error, text="--", font=("Segoe UI", 11), foreground="red", width=60, anchor="w")
        self.label_error.pack(side=tk.LEFT, padx=5)
        # 按鈕區
        frm_btn = ttk.Frame(self.root)
        frm_btn.pack(pady=(22, 10))
        self.btn_start = ttk.Button(frm_btn, text="啟動爬蟲", command=self.toggle_crawler, width=20)
        self.btn_start.pack(side=tk.LEFT, padx=12, pady=10, ipady=10)
        self.btn_stop = ttk.Button(frm_btn, text="停止爬蟲", command=self.stop_crawler, state=tk.DISABLED, width=20)
        self.btn_stop.pack(side=tk.LEFT, padx=12, pady=10, ipady=10)
        self.btn_load_progress = ttk.Button(frm_btn, text="讀取進度", command=self.load_progress, width=20)
        self.btn_load_progress.pack(side=tk.LEFT, padx=12, pady=10, ipady=10)
        
        # 客製化設定按鈕（移到下方）
        # btn_custom = ttk.Button(self.root, text="客製化設定", command=self.open_custom_settings)
        # btn_custom.pack(pady=10)

        # 底部小字：Sitemap.xml聰明產生器 by Colinjen88
        frm_footer = ttk.Frame(self.root)
        frm_footer.pack(side=tk.BOTTOM, pady=(8, 4))
        lbl_footer = tk.Label(frm_footer, text="Sitemap.xml聰明產生器v2.11 by ", font=("Segoe UI", 9), fg="#888888")
        lbl_footer.pack(side=tk.LEFT)
        link = tk.Label(frm_footer, text="Colinjen88", font=("Segoe UI", 9, "underline"), fg="#3366cc", cursor="hand2")
        link.pack(side=tk.LEFT)
        def open_email(event=None):
            import webbrowser
            webbrowser.open("mailto:colinjen88@gmail.com")
        link.bind("<Button-1>", open_email)

    def toggle_crawler(self):
        """統一的按鈕處理器，根據狀態決定啟動或繼續"""
        self.btn_start.config(state=tk.DISABLED)

        if self.is_running:
            return

        if self.can_resume:
            self.resume_crawler()
        else:
            self.start_crawler()
    
    def resume_crawler(self):
        """繼續抓取功能"""
        self.start_crawler()
    
    def open_sitemap_file(self, event=None):
        import os
        import webbrowser
        # 自動尋找最新 sitemap_*.xml
        files = [
            f for f in os.listdir('.')
            if f.endswith('.xml') and (f.startswith('sitemap_') or f.startswith('sitemap-'))
        ]
        if files:
            latest = max(files, key=os.path.getmtime)
            sitemap_path = os.path.abspath(latest)
            webbrowser.open(f"file://{sitemap_path}")
        else:
            from tkinter import messagebox
            messagebox.showinfo("找不到檔案", "尚未產生 sitemap_*.xml")

    def update_progress_file_label(self):
        try:
            name = os.path.basename(self.progress_file) if self.progress_file else "--"
            self.label_progress_file.config(text=name)
        except Exception:
            try:
                self.label_progress_file.config(text="--")
            except Exception:
                pass
    
    def open_custom_settings(self):
        """開啟客製化設定視窗"""
        # 創建新視窗
        settings_window = tk.Toplevel(self.root)
        settings_window.title("客製化設定")
        settings_window.geometry("800x700")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 讀取當前設定
        current_config = self._load_config()
        
        # 創建 Notebook (分頁標籤)
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === 基本設定頁面 ===
        frame_basic = ttk.Frame(notebook)
        notebook.add(frame_basic, text="基本設定")
        self._create_basic_settings(frame_basic, current_config)
        
        # === 爬蟲設定頁面 ===
        frame_crawler = ttk.Frame(notebook)
        notebook.add(frame_crawler, text="爬蟲設定")
        self._create_crawler_settings(frame_crawler, current_config)
        
        # === 權重設定頁面 ===
        frame_priority = ttk.Frame(notebook)
        notebook.add(frame_priority, text="權重設定")
        self._create_priority_settings(frame_priority, current_config)
        
        # === 排除規則頁面 ===
        frame_exclude = ttk.Frame(notebook)
        notebook.add(frame_exclude, text="排除規則")
        self._create_exclude_settings(frame_exclude, current_config)
        
        # === 自訂規則頁面 ===
        frame_custom = ttk.Frame(notebook)
        notebook.add(frame_custom, text="自訂規則")
        self._create_custom_rules(frame_custom, current_config)
        
        # 按鈕區域
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(pady=10)
        
        btn_save = ttk.Button(btn_frame, text="儲存設定", 
                             command=lambda: self._save_settings(settings_window, current_config))
        btn_save.pack(side=tk.LEFT, padx=5)
        
        btn_cancel = ttk.Button(btn_frame, text="取消", command=settings_window.destroy)
        btn_cancel.pack(side=tk.LEFT, padx=5)
        
        btn_reset = ttk.Button(btn_frame, text="還原預設", 
                              command=lambda: self._reset_to_defaults(settings_window, current_config, notebook))
        btn_reset.pack(side=tk.LEFT, padx=5)
    
    def _create_basic_settings(self, parent, config):
        """創建基本設定頁面"""
        # 起始網址
        ttk.Label(parent, text="起始網址：", font=("Segoe UI", 11)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        entry_start_url = ttk.Entry(parent, width=50, font=("Segoe UI", 10))
        entry_start_url.grid(row=0, column=1, padx=10, pady=10)
        entry_start_url.insert(0, config.get("start_url", "https://pm.shiny.com.tw/"))
        
        # 執行緒數量
        ttk.Label(parent, text="執行緒數量：", font=("Segoe UI", 11)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        entry_threads = ttk.Entry(parent, width=50, font=("Segoe UI", 10))
        entry_threads.grid(row=1, column=1, padx=10, pady=10)
        entry_threads.insert(0, str(config.get("max_workers", 3)))
        
        # 請求延遲（秒）
        ttk.Label(parent, text="請求延遲（秒）：", font=("Segoe UI", 11)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        entry_delay = ttk.Entry(parent, width=50, font=("Segoe UI", 10))
        entry_delay.grid(row=2, column=1, padx=10, pady=10)
        entry_delay.insert(0, str(config.get("request_delay", 0.1)))
        
        # 最大深度
        ttk.Label(parent, text="最大深度：", font=("Segoe UI", 11)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        entry_depth = ttk.Entry(parent, width=50, font=("Segoe UI", 10))
        entry_depth.grid(row=3, column=1, padx=10, pady=10)
        entry_depth.insert(0, str(config.get("max_depth", 10)))
        
        # 保存到配置字典
        config["_entry_start_url"] = entry_start_url
        config["_entry_threads"] = entry_threads
        config["_entry_delay"] = entry_delay
        config["_entry_depth"] = entry_depth
    
    def _create_crawler_settings(self, parent, config):
        """創建爬蟲設定頁面"""
        # 設定 User-Agent
        ttk.Label(parent, text="User-Agent：", font=("Segoe UI", 11)).grid(row=0, column=0, sticky=tk.W+tk.N, padx=10, pady=10)
        text_ua = tk.Text(parent, width=50, height=3, font=("Consolas", 9), wrap=tk.WORD)
        text_ua.grid(row=0, column=1, padx=10, pady=10)
        default_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        text_ua.insert("1.0", config.get("user_agent", default_ua))
        
        # 超時設定（秒）
        ttk.Label(parent, text="請求超時（秒）：", font=("Segoe UI", 11)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        entry_timeout = ttk.Entry(parent, width=50, font=("Segoe UI", 10))
        entry_timeout.grid(row=1, column=1, padx=10, pady=10)
        entry_timeout.insert(0, str(config.get("timeout", 10)))
        
        # 自動保存間隔（秒）
        ttk.Label(parent, text="自動保存間隔（秒）：", font=("Segoe UI", 11)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        entry_autosave = ttk.Entry(parent, width=50, font=("Segoe UI", 10))
        entry_autosave.grid(row=2, column=1, padx=10, pady=10)
        entry_autosave.insert(0, str(config.get("autosave_interval", 5)))
        
        # 保存到配置字典
        config["_text_ua"] = text_ua
        config["_entry_timeout"] = entry_timeout
        config["_entry_autosave"] = entry_autosave
    
    def _create_priority_settings(self, parent, config):
        """創建權重設定頁面"""
        priorities = config.get("priorities", {})
        
        # 創建滾動區域
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 預設權重項目
        default_priorities = config.get("_default_priorities", [
            ("首頁", "homepage", "1.0"),
            ("商品頁 (product-detail.php)", "product_detail", "0.7"),
            ("清單頁無參數 (menu.php)", "menu_no_params", "0.9"),
            ("清單頁有參數 (menu.php?)", "menu_with_params", "0.85"),
            ("清單頁有分頁 (page=)", "menu_with_page", "0.8"),
            ("新聞頁 (news.php)", "news", "0.9"),
            ("關於頁 (about.php)", "about", "0.8"),
            ("購物說明 (shopping_explanation)", "shopping_explanation", "0.8"),
            ("其他頁面", "default", "0.7")
        ])
        
        # 合併預設和自訂項目
        all_priorities = []
        for label, key, default in default_priorities:
            all_priorities.append((label, key, default, True))
        
        # 添加自訂項目
        custom_priorities = priorities.copy()
        for key in default_priorities:
            custom_priorities.pop(key[1], None)
        
        for key, value in custom_priorities.items():
            if key not in [x[1] for x in default_priorities]:
                all_priorities.append((key.replace("_", " ").title(), key, str(value), False))
        
        priority_entries = {}
        priority_rows = {}  # 儲存每一行的 frame
        
        # 創建每一行的設定
        for idx, (label, key, default, is_default) in enumerate(all_priorities):
            row_frame = ttk.Frame(scrollable_frame)
            row_frame.grid(row=idx, column=0, sticky=tk.W+tk.E, padx=5, pady=2)
            
            # 標籤
            label_widget = ttk.Label(row_frame, text=f"{label}：", font=("Segoe UI", 10), width=30)
            label_widget.grid(row=0, column=0, sticky=tk.W)
            
            # 輸入框
            entry = ttk.Entry(row_frame, width=15, font=("Segoe UI", 10))
            entry.grid(row=0, column=1, padx=5)
            value = str(priorities.get(key, default))
            entry.insert(0, value)
            priority_entries[key] = entry
            
            # 刪除按鈕（只有非預設項目才顯示）
            if not is_default:
                btn_delete = ttk.Button(row_frame, text="刪除", width=8,
                                       command=lambda k=key: self._delete_priority_item(k, priority_entries, priority_rows, scrollable_frame))
                btn_delete.grid(row=0, column=2, padx=5)
            
            priority_rows[key] = row_frame
        
        # 新增項目按鈕
        new_item_frame = ttk.Frame(scrollable_frame)
        new_item_frame.grid(row=len(all_priorities), column=0, sticky=tk.W+tk.E, padx=5, pady=10)
        
        ttk.Label(new_item_frame, text="新增項目名稱：", font=("Segoe UI", 10)).grid(row=0, column=0, padx=5)
        entry_new_name = ttk.Entry(new_item_frame, width=20, font=("Segoe UI", 10))
        entry_new_name.grid(row=0, column=1, padx=5)
        
        ttk.Label(new_item_frame, text="權重值：", font=("Segoe UI", 10)).grid(row=0, column=2, padx=5)
        entry_new_value = ttk.Entry(new_item_frame, width=10, font=("Segoe UI", 10))
        entry_new_value.grid(row=0, column=3, padx=5)
        entry_new_value.insert(0, "0.7")
        
        btn_add = ttk.Button(new_item_frame, text="新增項目",
                            command=lambda: self._add_priority_item(entry_new_name.get(), entry_new_value.get(), 
                                                                    priority_entries, priority_rows, scrollable_frame))
        btn_add.grid(row=0, column=4, padx=5)
        
        config["_priority_entries"] = priority_entries
        config["_priority_rows"] = priority_rows
        config["_scrollable_frame"] = scrollable_frame
    
    def _add_priority_item(self, name, value, priority_entries, priority_rows, scrollable_frame):
        """新增權重項目"""
        if not name or not name.strip():
            messagebox.showwarning("警告", "請輸入項目名稱！")
            return
        
        try:
            float(value)
        except ValueError:
            messagebox.showwarning("警告", "權重值必須是數字！")
            return
        
        key = name.lower().replace(" ", "_")
        if key in priority_entries:
            messagebox.showinfo("提示", "該項目已存在！")
            return
        
        row_idx = len(priority_entries)
        row_frame = ttk.Frame(scrollable_frame)
        row_frame.grid(row=row_idx, column=0, sticky=tk.W+tk.E, padx=5, pady=2)
        
        label_widget = ttk.Label(row_frame, text=f"{name}：", font=("Segoe UI", 10), width=30)
        label_widget.grid(row=0, column=0, sticky=tk.W)
        
        entry = ttk.Entry(row_frame, width=15, font=("Segoe UI", 10))
        entry.grid(row=0, column=1, padx=5)
        entry.insert(0, value)
        priority_entries[key] = entry
        
        btn_delete = ttk.Button(row_frame, text="刪除", width=8,
                               command=lambda k=key: self._delete_priority_item(k, priority_entries, priority_rows, scrollable_frame))
        btn_delete.grid(row=0, column=2, padx=5)
        
        priority_rows[key] = row_frame
        
        messagebox.showinfo("成功", f"已新增項目：{name}")
    
    def _delete_priority_item(self, key, priority_entries, priority_rows, scrollable_frame):
        """刪除權重項目"""
        if key in ["homepage", "default"]:
            messagebox.showwarning("警告", "不能刪除預設項目！")
            return
        
        if key in priority_rows:
            priority_rows[key].destroy()
            del priority_rows[key]
            del priority_entries[key]
            messagebox.showinfo("成功", "已刪除項目")
    
    def _create_exclude_settings(self, parent, config):
        """創建排除規則頁面"""
        ttk.Label(parent, text="排除路徑（每行一個）：", font=("Segoe UI", 11)).grid(row=0, column=0, sticky=tk.W+tk.N, padx=10, pady=10)
        
        # 創建多行文字框和滾動條
        frame = ttk.Frame(parent)
        frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W+tk.E)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_exclude = tk.Text(frame, width=60, height=10, font=("Consolas", 10), 
                               wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_exclude.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_exclude.yview)
        
        # 載入現有排除路徑（包含 SEO 文件列出的敏感頁面）
        excluded_paths = config.get("excluded_paths", [
            "/login.php",
            "/member.php",
            "/register.php",
            "/admin.php",
            "/recover_product_detail.php",
            "/keeping.php",
            "/logout.php",
            "/order_query.php",
            "/order_detail.php",
            "/money_transfer.php",
            "/vip_contract.php",
            "/member_contract.php",
            "/wholesaler_contract.php",
        ])
        text_exclude.insert("1.0", "\n".join(excluded_paths))
        
        config["_text_exclude"] = text_exclude
        
        # 勾選設定：排除非標準 index.php 路徑、啟用異常參數過濾
        chk_frame = ttk.Frame(parent)
        chk_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=10, pady=(5, 0))

        var_excl_index = tk.BooleanVar(value=bool(config.get("exclude_nonstandard_index_path", True)))
        var_abnormal = tk.BooleanVar(value=bool(config.get("enable_abnormal_query_filter", True)))

        cb1 = ttk.Checkbutton(chk_frame, text="排除非標準 index.php 路徑（/index.php/）", variable=var_excl_index)
        cb2 = ttk.Checkbutton(chk_frame, text="啟用異常參數過濾", variable=var_abnormal)
        cb1.pack(anchor=tk.W)
        cb2.pack(anchor=tk.W)

        config["_var_excl_index"] = var_excl_index
        config["_var_abnormal"] = var_abnormal

        # 提示說明
        ttk.Label(parent, text="提示：輸入要排除的路徑，每行一個。例如：/login.php", 
                 font=("Segoe UI", 9), foreground="gray").grid(row=3, column=0, columnspan=2, padx=10, pady=5)
    
    def _create_custom_rules(self, parent, config):
        """創建自訂規則頁面"""
        # 說明文字
        ttk.Label(parent, text="自訂 URL 過濾規則（使用正則表達式）", font=("Segoe UI", 11, "bold")).pack(pady=10)
        ttk.Label(parent, text="可設定多組規則，匹配的 URL 會被排除或包含", font=("Segoe UI", 9), foreground="gray").pack()
        
        # 滾動區域
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # 載入現有規則
        custom_rules = config.get("custom_rules", [
            {
                "name": "排除 menu.php 的 page=1",
                "pattern": r"[\?&]page=1($|&)",
                "url_contains": "/menu.php",
                "action": "exclude"
            }
        ])
        
        rule_frames = []
        for idx, rule in enumerate(custom_rules):
            frame = self._create_single_custom_rule(scrollable_frame, rule, idx)
            rule_frames.append(frame)
        
        config["_custom_rule_frames"] = rule_frames
        config["_scrollable_frame_rules"] = scrollable_frame
        
        # 新增規則按鈕
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(pady=10)
        
        btn_add = ttk.Button(btn_frame, text="+ 新增規則",
                           command=lambda: self._add_custom_rule(config, rule_frames))
        btn_add.pack()
    
    def _create_single_custom_rule(self, parent, rule, idx):
        """創建單一自訂規則行"""
        frame = ttk.LabelFrame(parent, text=f"規則 #{idx + 1}")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 規則名稱
        ttk.Label(frame, text="規則名稱：").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        entry_name = ttk.Entry(frame, width=40)
        entry_name.grid(row=0, column=1, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        entry_name.insert(0, rule.get("name", ""))
        
        # URL 包含
        ttk.Label(frame, text="URL 必須包含：").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        entry_contains = ttk.Entry(frame, width=30)
        entry_contains.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        entry_contains.insert(0, rule.get("url_contains", ""))
        
        # 正則表達式
        ttk.Label(frame, text="正則表達式：").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        entry_pattern = ttk.Entry(frame, width=30)
        entry_pattern.grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        entry_pattern.insert(0, rule.get("pattern", ""))
        
        # 動作類型
        ttk.Label(frame, text="動作：").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        action_var = tk.StringVar(value=rule.get("action", "exclude"))
        combo_action = ttk.Combobox(frame, textvariable=action_var, values=["exclude", "include"], 
                                    state="readonly", width=15)
        combo_action.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 刪除按鈕
        btn_delete = ttk.Button(frame, text="刪除", 
                                command=lambda f=frame: f.destroy())
        btn_delete.grid(row=0, column=4, rowspan=2, padx=5, pady=5)
        
        # 儲存到 frame 的屬性
        frame._entry_name = entry_name
        frame._entry_contains = entry_contains
        frame._entry_pattern = entry_pattern
        frame._action_var = action_var
        
        return frame
    
    def _add_custom_rule(self, config, rule_frames):
        """新增自訂規則"""
        scrollable_frame = config["_scrollable_frame_rules"]
        idx = len(rule_frames)
        
        new_rule = {
            "name": "新規則",
            "pattern": r"[\?&]page=1($|&)",
            "url_contains": "",
            "action": "exclude"
        }
        
        frame = self._create_single_custom_rule(scrollable_frame, new_rule, idx)
        rule_frames.append(frame)
    
    def _load_config(self):
        """載入設定"""
        config_file = "setup_rules/config.json"
        default_config = {
            "start_url": "https://pm.shiny.com.tw/",
            "max_workers": 3,
            "request_delay": 0.1,
            "max_depth": 10,
            "timeout": 10,
            "autosave_interval": 5,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "priorities": {
                "homepage": 1.0,
                "product_detail": 0.7,
                "menu_no_params": 0.9,
                "menu_with_params": 0.85,
                "menu_with_page": 0.8,
                "news": 0.9,
                "about": 0.8,
                "shopping_explanation": 0.8,
                "default": 0.7
            },
            "excluded_paths": [
                "/login.php",
                "/member.php",
                "/register.php",
                "/admin.php"
            ],
            "custom_rules": [
                {
                    "name": "排除 menu.php 的 page=1",
                    "pattern": r"[\?&]page=1($|&)",
                    "url_contains": "/menu.php",
                    "action": "exclude"
                }
            ]
        }
        
        if os.path.exists(config_file):
            try:
                import json
                with open(config_file, "r", encoding="utf-8") as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except Exception:
                pass
        
        return default_config
    
    def _save_settings(self, window, config):
        """儲存設定"""
        try:
            # 讀取所有輸入的值
            new_config = {
                "start_url": config["_entry_start_url"].get(),
                "max_workers": int(config["_entry_threads"].get()),
                "request_delay": float(config["_entry_delay"].get()),
                "max_depth": int(config["_entry_depth"].get()),
                "timeout": int(config["_entry_timeout"].get()),
                "autosave_interval": int(config["_entry_autosave"].get()),
                "user_agent": config["_text_ua"].get("1.0", tk.END).strip(),
                "priorities": {},
                "excluded_paths": [line.strip() for line in config["_text_exclude"].get("1.0", tk.END).split("\n") if line.strip()],
                "exclude_nonstandard_index_path": bool(config.get("_var_excl_index").get()) if config.get("_var_excl_index") is not None else True,
                "enable_abnormal_query_filter": bool(config.get("_var_abnormal").get()) if config.get("_var_abnormal") is not None else True,
            }
            
            # 讀取權重設定
            for key, entry in config["_priority_entries"].items():
                new_config["priorities"][key] = float(entry.get())
            
            # 讀取自訂規則
            custom_rules = []
            for frame in config.get("_custom_rule_frames", []):
                if frame.winfo_exists():
                    rule = {
                        "name": frame._entry_name.get(),
                        "url_contains": frame._entry_contains.get(),
                        "pattern": frame._entry_pattern.get(),
                        "action": frame._action_var.get()
                    }
                    if rule["name"] and rule["pattern"]:  # 只保存有效規則
                        custom_rules.append(rule)
            new_config["custom_rules"] = custom_rules
            
            # 儲存到檔案
            import json
            with open("setup_rules/config.json", "w", encoding="utf-8") as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", "設定已儲存！")
            window.destroy()
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存設定失敗：{e}")
    
    def _reset_to_defaults(self, window, config, notebook):
        """還原預設設定"""
        result = messagebox.askyesno("確認", "確定要還原為預設設定嗎？")
        if result:
            window.destroy()
            self.open_custom_settings()  # 重新開啟設定視窗
    
    def autosave_progress(self):
        progress_file = self.progress_file
        has_changes = False
        # 只在爬蟲運行時才執行自動儲存
        if not self.is_running:
            self.root.after(30000, self.autosave_progress)
            return
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "rb") as f:
                    old = pickle.load(f)
                old_crawled = set(old.get("crawled_urls", set()))
                new_crawled = set(self.crawled_urls) - old_crawled
                old_valid = set(old.get("valid_sitemap_urls", set()))
                new_valid = set(self.valid_sitemap_urls) - old_valid
                if new_crawled or new_valid:
                    has_changes = True
                    print(f"[autosave_progress] 新增 crawled_urls: {len(new_crawled)} 筆")
                    print(f"[autosave_progress] 新增 valid_sitemap_urls: {len(new_valid)} 筆")
            except Exception:
                pass
        self.save_progress(self.crawled_urls, self.valid_sitemap_urls, self.to_crawl, self.rule1_count, self.rule2_count, self.rule3_count)
        if has_changes:
            print(f"[autosave_progress] 已儲存進度到 {progress_file}")
        interval = 5000 if self.is_running else 30000
        self._autosave_id = self.root.after(interval, self.autosave_progress)
    def update_stats_label(self):
        # 只顯示累積統計，用當前資料
        self.label_stats.config(
            text=f"【進度報告】已爬：{len(self.crawled_urls)} | 有效：{len(self.valid_sitemap_urls)} | 商品頁：{self.rule1_count} | 清單頁：{self.rule2_count} | 其他頁：{self.rule3_count}")

    def update_gui_periodically(self):
        self.update_stats_label()
        if self.is_running:
            self._gui_updater_id = self.root.after(1000, self.update_gui_periodically)

    def _start_scan_animation(self):
        if not hasattr(self, '_scan_anim_job') or self._scan_anim_job is None:
            self._init_beam_states()
            self._scan_anim_job = self.root.after(33, self._animate_scanning_bar)

    def _stop_scan_animation(self):
        if hasattr(self, '_scan_anim_job') and self._scan_anim_job:
            self.root.after_cancel(self._scan_anim_job)
            self._scan_anim_job = None

    def _init_beam_states(self):
        self._scan_beam_count = max(1, self.num_threads.get() if hasattr(self, 'num_threads') else 1)
        self._scan_beam_offset = 0
        self._scan_beam_dir = 1

    def _animate_scanning_bar(self):
        if not getattr(self, 'is_running', False):
            self._scan_anim_job = None
            return
        width = 540
        height = 24
        rect_width = 18
        beam_count = getattr(self, '_scan_beam_count', 1)
        gap = 18
        total_length = beam_count * rect_width + (beam_count - 1) * gap
        speed = 10
        max_offset = width - total_length
        offset = self._scan_beam_offset
        dir = self._scan_beam_dir
        # 畫同步移動的 beams
        self.progress_canvas.delete("all")
        for i in range(beam_count):
            x0 = offset + i * (rect_width + gap)
            if 0 <= x0 < width:
                self.progress_canvas.create_rectangle(x0, 3, x0 + rect_width, height - 3, fill="#97ee7d", outline="", width=0)
        # bounce 邏輯
        offset += speed * dir
        if offset > max_offset:
            offset = max_offset
            dir = -1
        if offset < 0:
            offset = 0
            dir = 1
        self._scan_beam_offset = offset
        self._scan_beam_dir = dir
        self._scan_anim_job = self.root.after(33, self._animate_scanning_bar)


    def start_crawler(self):
        if self.is_running:
            return
        self.is_running = True

        self.btn_stop.config(state=tk.NORMAL)
        self.btn_load_progress.config(state=tk.DISABLED)
        self.combo_threads.config(state='disabled')
        self._start_scan_animation()
        self.can_resume = False  # 開始執行時重置狀態
        self.btn_start.config(text="啟動爬蟲", state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.label_status.config(text="狀態：爬蟲執行中...")
        # 進度條動畫進度值已不需要任何百分比設置或變更
        # self.progress["value"] = 0
        # self.progress["value"] = 100

        start_url = self.entry_url.get().strip()
        if not start_url:
            messagebox.showwarning("警告", "請輸入起始網址！")
            self.stop_crawler()
            return

        # 嘗試更新 robots.txt 狀態
        try:
            self.update_robots_status(start_url)
        except Exception:
            pass

        # 啟動前自動備份現有進度檔（只保留最新的 3 個備份）
        progress_file = self.progress_file
        if os.path.exists(progress_file):
            import shutil
            import glob
            # 找出所有現有的備份檔
            backup_files = sorted(glob.glob(f"{progress_file}.bak*"), key=os.path.getmtime)
            # 只保留最新的 2 個，刪除更舊的
            if len(backup_files) > 2:
                for old_backup in backup_files[:-2]:
                    try:
                        os.remove(old_backup)
                    except Exception:
                        pass
            # 創建新備份
            idx = 2
            while True:
                backup_file = f"{progress_file}.bak{idx}"
                if not os.path.exists(backup_file):
                    shutil.copyfile(progress_file, backup_file)
                    break
                idx += 1

        # 記錄本次啟動時的起始數據（用於計算本次統計）
        self.session_start_crawled = set(self.crawled_urls)
        self.session_start_valid = set(self.valid_sitemap_urls)
        self.session_start_rule1 = self.rule1_count
        self.session_start_rule2 = self.rule2_count
        self.session_start_rule3 = self.rule3_count

        # 啟動自動儲存進度
        self.autosave_progress()

        # 啟動 GUI 定期更新
        self.update_gui_periodically()

        def progress_callback(data):
            # 更新數據
            self.crawled_urls = data["crawled_urls"]
            self.valid_sitemap_urls = data["valid_sitemap_urls"]
            self.to_crawl = data["urls_to_crawl"]
            self.rule1_count = data.get("rule1_count", 0)
            self.rule2_count = data.get("rule2_count", 0)
            self.rule3_count = data.get("rule3_count", 0)

        def crawling_url_callback(url):
            self.show_crawling_url(url)

        num_threads = self.num_threads.get()
        def run_crawler_with_threads():
            if not self.is_running:
                return
            
            # 準備要傳遞給爬蟲的初始狀態
            initial_state = {
                "urls_to_crawl": self.to_crawl,
                "crawled_urls": self.crawled_urls,
                "valid_sitemap_urls": self.valid_sitemap_urls,
                "rule1_count": self.rule1_count,
                "rule2_count": self.rule2_count,
                "rule3_count": self.rule3_count,
            }
            # 修正：傳入 initial_state
            self.run_crawler(start_url, progress_callback, num_threads, lambda: self.is_running, initial_state=initial_state, crawling_url_callback=crawling_url_callback)

        t = threading.Thread(target=run_crawler_with_threads)
        self.threads = [t]
        t.start()

        # 修正：將 GUI 更新操作移回主執行緒
        def on_crawler_done():
            # 若是使用者手動停止，狀態已在 stop_crawler 設定，這裡直接 return
            if self.can_resume:
                return
            
            self.is_running = False
            self.can_resume = False
            self.combo_threads.config(state='readonly')
            self.btn_start.config(text="啟動爬蟲", state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.btn_load_progress.config(state=tk.NORMAL)
            self.label_status.config(text="狀態：爬取完成")
            # 產出一份完成時的 sitemap（用預設命名規則）
            try:
                out_name = get_sitemap_filename()
                self.generate_xml_file(list(self.valid_sitemap_urls), out_name)
                self.label_sitemap.config(text=f"開啟 {out_name}", foreground="blue")
            except Exception:
                pass
            # 顯示 sitemap 連結
            try:
                self.show_sitemap_link()
            except Exception:
                pass

        def wait_threads():
            t.join() # 等待爬蟲執行緒結束
            try:
                # 使用 after 將 GUI 更新排入主執行緒的事件佇列
                self.root.after(0, on_crawler_done)
            except tk.TclError:
                # 如果視窗已關閉，會引發 TclError，直接忽略
                print("視窗已關閉，略過完成後續的 GUI 更新。")

        wait_thread = threading.Thread(target=wait_threads)
        wait_thread.start()

    def load_progress(self):
        """讀取進度檔案"""
        import tkinter.filedialog as filedialog
        
        # 開啟檔案選擇對話框
        progress_file = filedialog.askopenfilename(
            title="選擇進度檔案",
            filetypes=[
                ("Pickle files", "*.pkl"),
                ("All files", "*.*")
            ],
            initialfile=self.progress_file
        )
        
        if not progress_file:
            return
        
        if not os.path.exists(progress_file):
            messagebox.showinfo("提示", "找不到進度檔案！")
            return
        
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
            self.session_start_rule1 = self.rule1_count
            self.session_start_rule2 = self.rule2_count
            self.session_start_rule3 = self.rule3_count
            # 更新顯示
            self.label_stats.config(
                text=f"本次已爬：0 | 有效：0"
            )
            # 讀取進度後可以繼續抓取
            self.can_resume = True
            # 將目前使用的進度檔更新為所選檔案
            self.progress_file = progress_file
            self.update_progress_file_label()
            self.btn_start.config(text="繼續抓取")
            self.is_running = False
            messagebox.showinfo("成功", f"已載入進度：\n已爬取 {len(self.crawled_urls)} 個網址\n有效網址 {len(self.valid_sitemap_urls)} 個\n待爬取 {len(self.to_crawl)} 個")
        except Exception as e:
            messagebox.showerror("錯誤", f"無法讀取進度檔案：{e}")

    def stop_crawler(self):
        if not self.is_running:
            return
        self.is_running = False

        self.combo_threads.config(state='readonly')
        self._stop_scan_animation()
        self.can_resume = True  # 停止後可以繼續
        self.btn_start.config(text="繼續抓取", state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_load_progress.config(state=tk.NORMAL)
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
        # 如果已有有效網址，產生 sitemap 並顯示連結
        try:
            if self.valid_sitemap_urls:
                # 立即產出帶時間戳的 sitemap（sitemap-YYYYmmddHHMM.xml）
                ts_name = datetime.now().strftime("sitemap-%Y%m%d%H%M.xml")
                self.generate_xml_file(list(self.valid_sitemap_urls), ts_name)
                # 在 GUI 顯示可點連結文字
                try:
                    self.label_sitemap.config(text=f"開啟 {ts_name}", foreground="blue")
                except Exception:
                    pass
        except Exception:
            pass

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

                # 只將 URL 加入集合，不立即更新 sitemap.xml（避免產生大量檔案）
                valid_sitemap_urls.add(url)
                # self.update_sitemap(valid_sitemap_urls)  # 已移除：避免每次爬取都產生新 XML

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
        progress_file = self.progress_file
        
        # 直接使用當前記憶體中的資料作為最新狀態，這才是正確的合併邏輯
        merged_data = {
            "crawled_urls": set(crawled_urls),
            "valid_sitemap_urls": set(valid_sitemap_urls),
            "urls_to_crawl": set(to_crawl),
            "rule1_count": rule1_count,
            "rule2_count": rule2_count,
            "rule3_count": rule3_count
        }

        if os.path.exists(progress_file):
            try:
                with open(progress_file, "rb") as f:
                    if pickle.load(f) == merged_data:
                        return # 如果資料沒有變化，則不執行寫入
            except Exception:
                pass

        try:
            with open(progress_file, "wb") as f:
                pickle.dump(merged_data, f)
            print(f"[save_progress] 寫入成功: 已爬:{len(merged_data['crawled_urls'])} 有效:{len(merged_data['valid_sitemap_urls'])} 待爬:{len(merged_data['urls_to_crawl'])}")
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
        # 更新 sitemap.xml 檔案（已停用頻繁更新，避免產生大量檔案）
        # 此函式保留以備將來需要，但現在不會自動頻繁呼叫
        try:
            # 使用固定檔名 sitemap_latest.xml，避免產生大量時間戳檔案
            output_file = "sitemap_latest.xml"
            self.generate_xml_file(list(valid_sitemap_urls), output_file)
            self.label_sitemap.config(text=f"{output_file} 更新成功", foreground="green")
            self.show_sitemap_link()
        except Exception as e:
            self.label_sitemap.config(text=f"sitemap 產生失敗:{e}", foreground="red")

    def show_sitemap_link(self):
        import os
        # 顯示最新 sitemap 檔（同時支援 sitemap_ 與 sitemap- 命名）
        files = [
            f for f in os.listdir('.')
            if f.endswith('.xml') and (f.startswith('sitemap_') or f.startswith('sitemap-'))
        ]
        if files:
            latest = max(files, key=os.path.getmtime)
            self.label_sitemap.config(text=f"開啟 {latest}", foreground="blue")

    def open_robots_url(self, event=None):
        try:
            import webbrowser
            if self._robots_url:
                webbrowser.open(self._robots_url)
        except Exception:
            pass

    def update_robots_status(self, base_url: str):
        from urllib.parse import urljoin
        import requests
        robots_url = urljoin(base_url, "/robots.txt")
        self._robots_url = robots_url
        try:
            timeout_sec = 5
            try:
                # 若有設定中的 timeout，沿用
                cfg = self._load_config()
                timeout_sec = int(cfg.get("timeout", timeout_sec))
            except Exception:
                pass

            resp = requests.get(robots_url, timeout=timeout_sec)
            if resp.status_code >= 400:
                self.label_robots.config(text="無法取得 (HTTP %d)" % resp.status_code, foreground="red")
                return

            text = resp.text or ""
            self._robots_text = text

            # 解析簡易摘要：記錄 user-agent 為 * 的 allow/disallow 條數
            allow_cnt = 0
            disallow_cnt = 0
            current_ua = None
            target_ua = "*"
            for line in text.splitlines():
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                prefix = s.split(':', 1)[0].lower()
                value = s.split(':', 1)[1].strip() if ':' in s else ''
                if prefix == 'user-agent':
                    current_ua = value
                elif current_ua in (target_ua, None):
                    if prefix == 'allow' and value:
                        allow_cnt += 1
                    elif prefix == 'disallow' and value:
                        disallow_cnt += 1

            self._robots_summary = {"allow": allow_cnt, "disallow": disallow_cnt}

            # 顯示固定成功訊息（點擊仍可開啟 robots.txt）
            self.label_robots.config(text="已排除收錄robots.txt阻擋清單", foreground="green")
        except Exception as e:
            self.label_robots.config(text=f"無法取得：{e}", foreground="red")

    def show_crawling_url(self, url):
        # 追加顯示目前爬網址 tip，最多保留30條
        def do_update():
            self.crawl_file_list['state'] = 'normal'
            lines = self.crawl_file_list.get('1.0','end').splitlines()
            lines.append(url)
            if len(lines)>30:
                lines = lines[-30:]
            self.crawl_file_list.delete('1.0', 'end')
            self.crawl_file_list.insert('1.0', '\n'.join(lines))
            self.crawl_file_list['state'] = 'disabled'
            self.crawl_file_list.see('end')
        self.root.after(0, do_update)

if __name__ == "__main__":
    root = tk.Tk()
    app = SitemapApp(root)

    def on_closing():
        if app.is_running:
            app.stop_crawler() # 優雅地停止爬蟲和計時器
        try:
            app.save_progress(app.crawled_urls, app.valid_sitemap_urls, app.to_crawl, app.rule1_count, app.rule2_count, app.rule3_count)
        except Exception:
            pass
        root.destroy()
        import sys
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

