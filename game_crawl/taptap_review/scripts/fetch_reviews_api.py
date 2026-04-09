#!/usr/bin/env python3
"""TapTap Review Crawler - API 模式"""

import json
import time
import sys
import requests
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage

def fetch_reviews_api(app_id, game_id, game_name, limit=100):
    """使用 TapTap API 抓取评价"""
    print(f"[taptap_review] 开始抓取 {game_name} (app_id: {app_id}) 的评价...")
    
    reviews = []
    seen_ids = set()
    page = 1
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': f'https://www.taptap.cn/app/{app_id}/review',
    }
    
    while len(reviews) < limit and page <= 20:
        try:
            # TapTap API endpoint
            url = f"https://www.taptap.cn/webapiv2/review/v2/by-app"
            params = {
                'app_id': app_id,
                'page': page,
                'limit': 50,
                'order': 'default',
                'region': 'cn',
                'X-UA': 'V=1&PN=WebApp&LANG=zh_CN&VN_CODE=102&VN=0.1.0&LOC=CN&PLT=PC&DS=Android&UID=0&OS=Windows&OSV=10'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            data = response.json()
            
            if data.get('success') and 'data' in data:
                items = data['data'].get('list', [])
                if not items:
                    break
                    
                for item in items:
                    review_id = str(item.get('id', ''))
                    if review_id in seen_ids:
                        continue
                    seen_ids.add(review_id)
                    
                    author = item.get('author', {})
                    review_data = {
                        'id': review_id,
                        'author': author.get('name', ''),
                        'author_id': author.get('id', ''),
                        'content': item.get('contents', {}).get('text', ''),
                        'score': item.get('score', 0),
                        'likes': item.get('stat', {}).get('agree', 0),
                        'replies': item.get('stat', {}).get('reply', 0),
                        'time': item.get('created_time', ''),
                        'url': f"https://www.taptap.cn/review/{review_id}"
                    }
                    reviews.append(review_data)
                    
                    if len(reviews) >= limit:
                        break
                
                print(f"[taptap_review] 第{page}页: 已收集 {len(reviews)} 条")
                page += 1
                time.sleep(1)
            else:
                break
                
        except Exception as e:
            print(f"[ERROR] 抓取失败: {e}")
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
    
    parser = argparse.ArgumentParser(description="TapTap Review - API Mode")
    parser.add_argument("--app-id", required=True, help="TapTap app ID")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--game-name", required=True, help="游戏名称")
    parser.add_argument("--limit", type=int, default=100, help="数量限制")
    args = parser.parse_args()
    
    try:
        reviews = fetch_reviews_api(
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
