"""
Sitemap Generator 設定檔
包含程式的各種設定參數
"""

import os

# 預設設定
DEFAULT_CONFIG = {
    # 爬蟲設定
    "START_URL": "https://pm.shiny.com.tw/",
    "MAX_WORKERS": 3,
    "REQUEST_DELAY": 0.1,
    "MAX_DEPTH": 10,
    
    # 檔案設定
    "PROGRESS_FILE": "sitemap_crawl_temp.pkl",
    "OUTPUT_FILE": "sitemap.xml",
    "ERROR_LOG_FILE": "error_log.txt",
    
    # GUI 設定
    "AUTOSAVE_INTERVAL": 5000,  # 毫秒
    "GUI_UPDATE_INTERVAL": 1000,  # 毫秒
    "WINDOW_SIZE": "640x560",
    
    # 網址篩選規則
    "EXCLUDED_PATHS": [
        "/login.php",
        "/member.php", 
        "/register.php",
        "/admin.php"
    ],
    
    # Priority 設定
    "PRIORITIES": {
        "homepage": 1.0,
        "product_detail": 0.7,
        "menu_no_params": 0.9,
        "menu_with_params": 0.85,
        "menu_with_page": 0.8,
        "news": 0.9,
        "about": 0.8,
        "shopping_explanation": 0.8,
        "default": 0.7
    }
}

class Config:
    """設定管理類別"""
    
    def __init__(self, config_file="setup_rules/config.json"):
        self.config_file = config_file
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self):
        """從檔案載入設定"""
        if os.path.exists(self.config_file):
            try:
                import json
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except Exception as e:
                print(f"載入設定檔失敗: {e}")
    
    def save_config(self):
        """儲存設定到檔案"""
        try:
            import json
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存設定檔失敗: {e}")
    
    def get(self, key, default=None):
        """取得設定值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """設定值"""
        self.config[key] = value
    
    def get_all(self):
        """取得所有設定"""
        return self.config.copy()

# 全域設定實例
config = Config()
