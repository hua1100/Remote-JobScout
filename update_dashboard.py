import os
import glob
import subprocess
import shutil
import sys

def run_spider():
    print("🚀 Starting Scrapy Spider...")
    try:
        # 執行 Scrapy 爬蟲
        subprocess.run([sys.executable, "-m", "scrapy", "crawl", "104_ai_jobs"], check=True)
        print("✅ Spider finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running spider: {e}")
        sys.exit(1)

def update_data_file():
    # 尋找最新的 ai_jobs_*.csv
    list_of_files = glob.glob('ai_jobs_*.csv') 
    
    if not list_of_files:
        print("❌ No CSV file found!")
        sys.exit(1)
        
    # 找出最新的檔案
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"📄 Found latest data file: {latest_file}")
    
    target_file = 'data.csv'
    
    # 複製並重新命名為 data.csv
    try:
        shutil.copy(latest_file, target_file)
        print(f"✅ Updated {target_file}")
        
        # 清理舊檔案 (選用)
        # for f in list_of_files:
        #     if f != latest_file:
        #         os.remove(f)
        
    except Exception as e:
        print(f"❌ Error updating data file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_spider()
    update_data_file()
