#!/usr/bin/env python3
"""TapTap Review Crawler - Alternative API"""

import json
import time
import sys
import requests
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage

def fetch_reviews_alt(app_id, game_id, game_name, limit=100):
    """使用替代方式抓取 TapTap 评价"""
    print(f"[taptap_review] 开始抓取 {game_name} (app_id: {app_id}) 的评价...")
    
    reviews = []
    seen_ids = set()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': f'https://www.taptap.cn/app/{app_id}',
        'Origin': 'https://www.taptap.cn',
    }
    
    # 尝试不同的 API 端点
    endpoints = [
        f"https://www.taptap.cn/webapiv2/review/v2/by-app?app_id={app_id}&limit=50&page=1",
        f"https://api.taptapdada.com/review/v2/by-app?app_id={app_id}&limit=50&page=1",
        f"https://www.taptap.cn/ajax/search/review?app_id={app_id}&limit=50",
    ]
    
    for url in endpoints:
        try:
            print(f"[DEBUG] Trying: {url[:80]}...")
            response = requests.get(url, headers=headers, timeout=30)
            print(f"[DEBUG] Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[DEBUG] Success! Keys: {list(data.keys())[:5] if isinstance(data, dict) else 'N/A'}")
                    
                    # 解析数据
                    items = []
                    if isinstance(data, dict):
                        if data.get('success') and 'data' in data:
                            items = data['data'].get('list', [])
                        elif 'list' in data:
                            items = data['list']
                        elif 'reviews' in data:
                            items = data['reviews']
                    
                    print(f"[DEBUG] Found {len(items)} items")
                    
                    for item in items:
                        review_id = str(item.get('id', ''))
                        if not review_id or review_id in seen_ids:
                            continue
                        seen_ids.add(review_id)
                        
                        author = item.get('author', {}) if isinstance(item.get('author'), dict) else {}
                        stat = item.get('stat', {}) if isinstance(item.get('stat'), dict) else {}
                        contents = item.get('contents', {}) if isinstance(item.get('contents'), dict) else {}
                        
                        review_data = {
                            'id': review_id,
                            'author': author.get('name', '') if isinstance(author, dict) else str(author),
                            'author_id': author.get('id', '') if isinstance(author, dict) else '',
                            'content': contents.get('text', '') if isinstance(contents, dict) else str(contents),
                            'score': item.get('score', 0),
                            'likes': stat.get('agree', 0) if isinstance(stat, dict) else 0,
                            'replies': stat.get('reply', 0) if isinstance(stat, dict) else 0,
                            'time': item.get('created_time', ''),
                            'url': f"https://www.taptap.cn/review/{review_id}"
                        }
                        reviews.append(review_data)
                        
                        if len(reviews) >= limit:
                            break
                    
                    if reviews:
                        print(f"[taptap_review] 成功获取 {len(reviews)} 条评价")
                        break
                        
                except Exception as e:
                    print(f"[DEBUG] Parse error: {e}")
                    continue
            
        except Exception as e:
            print(f"[DEBUG] Request error: {e}")
            continue
    
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"[taptap_review] 数据已保存到: {output_path}")
    
    return reviews

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="TapTap Review - Alternative API")
    parser.add_argument("--app-id", required=True, help="TapTap app ID")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--game-name", required=True, help="游戏名称")
    parser.add_argument("--limit", type=int, default=100, help="数量限制")
    args = parser.parse_args()
    
    try:
        reviews = fetch_reviews_alt(
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
