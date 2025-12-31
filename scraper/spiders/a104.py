import scrapy
from scrapy.http import FormRequest
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# 載入.env設定檔
load_dotenv()


class A104Spider(scrapy.Spider):
    name = "104_ai_jobs"
    allowed_domains = ["www.104.com.tw"]

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-TW",
            "origin": "https://www.104.com.tw/",
            "referer": "https://www.104.com.tw/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
            "Content-Type": "application/json",
        }
    }

    start_url = "https://www.104.com.tw/jobs/search/list"
    
    def __init__(self, *args, **kwargs):
        super(A104Spider, self).__init__(*args, **kwargs)
        
        # 從.env讀取搜尋關鍵字
        keywords_str = os.getenv("SEARCH_KEYWORDS", "AI自動化,AI轉型,數位轉型,流程自動化,RPA,AI工程師")
        self.keywords = [k.strip() for k in keywords_str.split(",")]
        
        # 從.env讀取每個關鍵字要爬取的頁數
        try:
            self.pages_per_keyword = int(os.getenv("SCRAPY_PAGES_PER_KEYWORD", "5"))
            if not 1 <= self.pages_per_keyword <= 50:
                self.logger.warning(f"頁數設定異常,使用預設值5頁")
                self.pages_per_keyword = 5
        except:
            self.logger.warning("無法讀取頁數設定,使用預設值5頁")
            self.pages_per_keyword = 5
        
        self.logger.info(f"搜尋關鍵字: {', '.join(self.keywords)}")
        self.logger.info(f"每個關鍵字爬取: {self.pages_per_keyword} 頁")

    def start_requests(self):
        for keyword in self.keywords:
            self.logger.info(f'開始搜尋關鍵字: {keyword}')
            for i in range(self.pages_per_keyword):
                yield FormRequest(
                    url=self.start_url + f"?page={i+1}&keyword={keyword}&remoteWork=1,2",
                    method="GET",
                    callback=self.parse,
                    meta={'keyword': keyword, 'page': i+1}
                )

    def parse(self, response):
        try:
            body = json.loads(response.body)
            jobs = body["data"]["list"]
            keyword = response.meta.get('keyword', '')
            page = response.meta.get('page', 1)
            
            self.logger.info(f'關鍵字 "{keyword}" 第{page}頁: 找到 {len(jobs)} 筆職缺')
            
            for job in jobs:
                # 二次確認，只處理允許遠端工作的職缺 (1: 完全遠端, 2: 部分遠端)
                if job.get('remoteWorkType', 0) in [1, 2]:
                    yield {
                        'search_keyword': keyword,  # 記錄是用哪個關鍵字找到的
                        'jobName': job.get('jobName', ''),
                        'jobRole': self._get_job_role_text(job.get('jobRole', '')),
                        'jobAddrNoDesc': job.get('jobAddrNoDesc', ''),
                        'jobAddress': job.get('jobAddress', ''),
                        'description': job.get('description', ''),
                        'optionEdu': job.get('optionEdu', ''),
                        'periodDesc': job.get('periodDesc', ''),
                        'applyCnt': job.get('applyCnt', 0),
                        'custName': job.get('custName', ''),
                        'coIndustryDesc': job.get('coIndustryDesc', ''),
                        'salaryLow': job.get('salaryLow', 0),
                        'salaryHigh': job.get('salaryHigh', 0),
                        'appearDate': datetime.strptime(job['appearDate'], "%Y%m%d").strftime("%Y-%m-%d") if job.get('appearDate') else '',
                        'jobLink': "https:" + job["link"]["job"].split("?")[0] if job.get('link') and job['link'].get('job') else '',
                        'remoteWorkType': self._get_remote_work_text(job.get('remoteWorkType', 0)),
                        'major': ','.join(job.get('major', [])) if job.get('major') else '',
                        'salaryType': self._get_salary_type_text(job.get('salaryType', '')),
                    }
        except Exception as e:
            self.logger.error(f'解析錯誤: {e}')
    
    def _get_job_role_text(self, role):
        """將工作型態代碼轉為文字"""
        role_map = {1: '正職', 2: '兼職', 3: '高階'}
        return role_map.get(role, '未知')
    
    def _get_remote_work_text(self, remote_type):
        """將遠端工作代碼轉為文字"""
        remote_map = {0: '不可遠端', 1: '完全遠端', 2: '部分遠端'}
        return remote_map.get(remote_type, '未知')
    
    def _get_salary_type_text(self, salary_type):
        """將薪資型態代碼轉為文字"""
        salary_map = {'H': '時薪', 'M': '月薪', 'Y': '年薪', '': '面議'}
        return salary_map.get(salary_type, salary_type)
