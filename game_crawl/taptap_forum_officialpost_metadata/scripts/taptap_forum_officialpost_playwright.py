#!/usr/bin/env python3
"""TapTap Forum Official Post - Playwright 版本"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index


def fetch_official_posts_playwright(app_id: str, limit: int, storage: DataStorage) -> list:
    """使用 Playwright 抓取官方帖子"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[taptap_forum] 错误: 未安装 playwright", file=sys.stderr)
        return []
    
    url = f"https://www.taptap.cn/app/{app_id}/topic?type=official"
    print(f"[taptap_forum] 打开页面: {url}")
    
    posts = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(3)
            
            scroll_count = 0
            max_scrolls = (limit // 3) + 10
            last_count = 0
            no_change_count = 0
            
            while len(posts) < limit and scroll_count < max_scrolls and no_change_count < 3:
                # 提取帖子
                items = page.query_selector_all('a[href*="/moment/"], a[href*="/t/"]')
                
                for item in items:
                    try:
                        href = item.get_attribute('href') or ""
                        title = item.inner_text().strip()
                        
                        # 提取 ID
                        import re
                        match = re.search(r'/(?:moment|t)/(\d+)', href)
                        if match and title:
                            post_id = match.group(1)
                            full_url = href if href.startswith('http') else f"https://www.taptap.cn{href}"
                            
                            post = {
                                "id": post_id,
                                "title": title[:200],
                                "url": full_url
                            }
                            
                            # 去重
                            if not any(p.get('id') == post_id for p in posts):
                                posts.append(post)
                                
                                if len(posts) >= limit:
                                    break
                    except Exception as e:
                        continue
                
                if len(posts) == last_count:
                    no_change_count += 1
                else:
                    no_change_count = 0
                    last_count = len(posts)
                
                print(f"  当前已获取: {len(posts)}/{limit} 个帖子")
                
                if len(posts) < limit:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2.5)
                    scroll_count += 1
        
        except Exception as e:
            print(f"[taptap_forum] 抓取失败: {e}", file=sys.stderr)
        
        finally:
            browser.close()
    
    return posts[:limit]


def main():
    parser = argparse.ArgumentParser(description="TapTap 官方帖子 Metadata 抓取 (Playwright)")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--app-id", required=True, help="TapTap App ID")
    parser.add_argument("--limit", type=int, default=10, help="帖子数量")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    print(f"[taptap_forum] 抓取官方帖子 app_id={args.app_id}, limit={args.limit}")
    
    posts = fetch_official_posts_playwright(args.app_id, args.limit, storage)
    print(f"[taptap_forum] 获取 {len(posts)} 个帖子")
    
    result = {
        "platform": "taptap",
        "game_id": args.game_id,
        "data_type": "official_posts",
        "phase": "metadata",
        "app_id": args.app_id,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(posts),
        "items": posts,
    }
    
    output_path = storage.merge_and_save(result, "taptap", "official_posts", id_field="id")
    print(f"[taptap_forum] 输出: {output_path}")
    
    update_index(args.game_id, args.game_id, "taptap", "official_posts", count=len(posts))


if __name__ == "__main__":
    main()
