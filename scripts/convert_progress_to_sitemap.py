
import pickle
import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from src.sitemap_generator import generate_xml_file, get_sitemap_filename

# 自動尋找最新 crawl_temp_*.pkl
def find_latest_progress():
    files = [f for f in os.listdir('.') if f.startswith('crawl_temp_') and f.endswith('.pkl')]
    if not files:
        raise FileNotFoundError('找不到任何 crawl_temp_*.pkl 進度檔')
    return max(files, key=os.path.getmtime)

progress_file = find_latest_progress()
with open(progress_file, 'rb') as f:
    data = pickle.load(f)

valid_urls = list(data.get('valid_sitemap_urls', []))
print(f"共 {len(valid_urls)} 個有效網址 (來源: {progress_file})")

# 產生 sitemap_+完成時間+.xml（含權重與完整過濾規則）
output_file = get_sitemap_filename()
generate_xml_file(valid_urls, output_file)
print(f"已產生 {output_file}")
