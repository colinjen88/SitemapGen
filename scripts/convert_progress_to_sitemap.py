import pickle
from src.sitemap_generator import create_sitemap

# 讀取進度檔
with open('sitemap_progress.pkl', 'rb') as f:
    data = pickle.load(f)

valid_urls = list(data.get('valid_sitemap_urls', []))
print(f"共 {len(valid_urls)} 個有效網址")

# 產生 sitemap.xml
create_sitemap(valid_urls, 'sitemap.xml')
print("已產生 sitemap.xml")
