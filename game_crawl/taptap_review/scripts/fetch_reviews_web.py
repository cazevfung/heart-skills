#!/usr/bin/env python3
"""TapTap Review Crawler - Web Scraping Mode"""

import json
import time
import sys
import requests
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage

def fetch_reviews_web(app_id, game_id, game_name, limit=100):
    """使用网页抓取 TapTap 评价"""
    print(f"[taptap_review] 开始抓取 {game_name} (app_id: {app_id}) 的评价...")
    
    reviews = []
    seen_ids = set()
    page = 1
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    while len(reviews) < limit and page <= 10:
        try:
            # 直接访问评价页面
            url = f"https://www.taptap.cn/app/{app_id}/review"
            params = {'page': page}
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            html = response.text
            
            # 尝试从 HTML 中提取 JSON 数据
            # TapTap 通常会将数据嵌入到 window.__INITIAL_STATE__ 或类似变量中
            import re
            
            # 查找评价数据
            # 尝试多种可能的模式
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.__DATA__\s*=\s*({.+?});',
                r'<script[^>]*>[^<]*"review"[^<]*({.+?})[^<]*</script>',
            ]
            
            data = None
            for pattern in patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        print(f"[DEBUG] Found data with pattern: {pattern[:50]}...")
                        break
                    except:
                        continue
            
            if not data:
                # 尝试直接正则提取评价列表
                review_pattern = r'data-review-id="(\d+)"[^>]*>[\s\S]*?<div[^>]*class="[^"]*review-content[^"]*"[^>]*>([\s\S]*?)</div>'
                matches = re.findall(review_pattern, html)
                if matches:
                    print(f"[DEBUG] Found {len(matches)} reviews via regex")
                else:
                    print(f"[DEBUG] No data found on page {page}")
                    # 保存 HTML 用于调试
                    debug_path = Path(f"taptap_debug_page_{page}.html")
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(html[:5000])
                    print(f"[DEBUG] Saved debug HTML to {debug_path}")
                    break
            
            # 提取评价列表
            items = []
            if data and isinstance(data, dict):
                # 尝试多种可能的路径
                if 'reviews' in data:
                    items = data['reviews']
                elif 'review' in data:
                    items = data['review']
                elif 'data' in data and 'list' in data['data']:
                    items = data['data']['list']
                elif 'list' in data:
                    items = data['list']
            
            if not items:
                print(f"[DEBUG] No items found on page {page}")
                break
            
            print(f"[DEBUG] Found {len(items)} items on page {page}")
            
            for item in items:
                review_id = str(item.get('id', ''))
                if not review_id or review_id in seen_ids:
                    continue
                seen_ids.add(review_id)
                
                author = item.get('author', {}) if isinstance(item.get('author'), dict) else {}
                review_data = {
                    'id': review_id,
                    'author': author.get('name', '') if isinstance(author, dict) else str(author),
                    'content': item.get('contents', {}).get('text', '') if isinstance(item.get('contents'), dict) else str(item.get('content', '')),
                    'score': item.get('score', 0),
                    'likes': item.get('stat', {}).get('agree', 0) if isinstance(item.get('stat'), dict) else 0,
                    'time': item.get('created_time', ''),
                    'url': f"https://www.taptap.cn/review/{review_id}"
                }
                reviews.append(review_data)
                
                if len(reviews) >= limit:
                    break
            
            print(f"[taptap_review] 第{page}页: 已收集 {len(reviews)} 条")
            page += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"[ERROR] 抓取失败: {e}")
            import traceback
            traceback.print_exc()
            break
    
    # 截取前 limit 条
    reviews = reviews[:limit]
    
    # 保存数据
    storage = DataStorage(game_id)
    output_data = {
        'platform': 'taptap',
        'data_type': 'review',
        'game_id': game_id,
        'game_name': game_name,
        'app_id': app_id,
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'count': len(reviews),
        'items': reviews
    }
    
    output_path = storage.get_output_path('taptap', 'reviews')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"[taptap_review] 数据已保存到: {output_path}")
    
    return reviews

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="TapTap Review - Web Scraping")
    parser.add_argument("--app-id", required=True, help="TapTap app ID")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--game-name", required=True, help="游戏名称")
    parser.add_argument("--limit", type=int, default=100, help="数量限制")
    args = parser.parse_args()
    
    try:
        reviews = fetch_reviews_web(
            args.app_id, 
            args.game_id, 
            args.game_name,
            limit=args.limit
        )
        print(f"[taptap_review] {args.game_name}: 成功抓取 {len(reviews)} 条评价")
    except Exception as e:
        print(f"[taptap_review] {args.game_name}: 抓取失败 - {e}")
        import traceback
        traceback.print_exc()
