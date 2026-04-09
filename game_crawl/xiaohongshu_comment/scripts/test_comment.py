#!/usr/bin/env python3
"""小红书Comment提取测试"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from playwright.sync_api import sync_playwright

test_url = "https://www.xiaohongshu.com/explore/69bb655000000000230118be?xsec_token=AB8nZooQXCI2LFKMEVROqhxroaYSOD78KF7P3p1HQSV8s=&xsec_source=pc_search"

print("[test] 启动浏览器访问帖子详情页...")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(test_url)
    time.sleep(5)
    
    print("[test] 页面标题:", page.title())
    
    # 查找评论相关元素
    print("[test] 查找评论容器...")
    comment_container = page.query_selector('[class*="comment"]')
    if comment_container:
        print("[test] 找到评论容器！HTML片段:")
        html = comment_container.inner_html()
        print(html[:800])
    else:
        print("[test] 未找到评论区域")
        # 尝试查找所有包含comment的元素
        all_elements = page.query_selector_all('[class*="comment"], [id*="comment"]')
        print(f"[test] 找到 {len(all_elements)} 个可能相关的元素")
        
        if all_elements:
            for i, el in enumerate(all_elements[:3]):
                print(f"[test] 元素{i}: tag={el.evaluate('node => node.tagName')}, class={el.get_attribute('class') or '无'}")
    
    browser.close()
    print("[test] 浏览器已关闭")
