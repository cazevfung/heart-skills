#!/usr/bin/env python3
"""TapTap Review Crawler - API 模式 (Debug)"""

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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': f'https://www.taptap.cn/app/{app_id}/review',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    # 先尝试获取单个评价页面
    try:
        url = f"https://www.taptap.cn/webapiv2/review/v2/by-app"
        params = {
            'app_id': app_id,
            'page': 1,
            'limit': 10,
            'order': 'default',
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        print(f"[DEBUG] Status: {response.status_code}")
        print(f"[DEBUG] Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"[DEBUG] First 500 chars: {response.text[:500]}")
        
        # 尝试解析
        try:
            data = response.json()
            print(f"[DEBUG] JSON parsed successfully")
            print(f"[DEBUG] Keys: {data.keys() if isinstance(data, dict) else 'not dict'}")
        except Exception as e:
            print(f"[DEBUG] JSON parse error: {e}")
            
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="TapTap Review - API Mode Debug")
    parser.add_argument("--app-id", required=True, help="TapTap app ID")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--game-name", required=True, help="游戏名称")
    parser.add_argument("--limit", type=int, default=100, help="数量限制")
    args = parser.parse_args()
    
    fetch_reviews_api(args.app_id, args.game_id, args.game_name, limit=args.limit)
