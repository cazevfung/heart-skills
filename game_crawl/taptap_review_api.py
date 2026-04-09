#!/usr/bin/env python3
"""
TapTap Review API Crawler - 直接API抓取
"""
import argparse
import json
import os
import sys
import time
import gzip
from datetime import datetime, timezone
from pathlib import Path

import urllib.request
import urllib.parse

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

_TAPTAP_API_URL = "https://www.taptap.cn/webapiv2/review/v3/by-app"
_RETRY_WAIT = 2
_MAX_RETRIES = 3


def _build_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.taptap.cn/",
        "X-Requested-With": "XMLHttpRequest",
    }


def _get(url: str, params: dict | None = None) -> dict:
    headers = _build_headers()
    if params:
        query = urllib.parse.urlencode(params, encoding='utf-8')
        full_url = url + "?" + query
    else:
        full_url = url
    
    for attempt in range(_MAX_RETRIES):
        try:
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                if resp.headers.get('Content-Encoding') == 'gzip':
                    data = gzip.decompress(data)
                return json.loads(data.decode("utf-8"))
        except Exception as e:
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_WAIT)
            else:
                raise
    return {}


def fetch_reviews(app_id: str, game_id: str, game_name: str, limit: int = 50) -> list:
    """抓取TapTap评价"""
    reviews = []
    from_cursor = "0"
    
    print(f"[taptap_review] 开始抓取 {game_name} (app_id: {app_id}) 的评价...")
    
    while len(reviews) < limit:
        params = {
            "app_id": app_id,
            "from": from_cursor,
            "limit": min(20, limit - len(reviews)),
            "sort": "new",
        }
        
        try:
            data = _get(_TAPTAP_API_URL, params)
        except Exception as e:
            print(f"[taptap_review] 请求失败: {e}", file=sys.stderr)
            break
        
        if not data or data.get("code") != 0:
            print(f"[taptap_review] API返回错误: {data.get('message', '未知错误')}", file=sys.stderr)
            break
        
        review_list = data.get("data", {}).get("list", [])
        if not review_list:
            break
        
        for item in review_list:
            review = item.get("review", {})
            author = item.get("author", {})
            
            reviews.append({
                "id": str(review.get("id", "")),
                "author": author.get("name", ""),
                "content": review.get("contents", {}).get("text", ""),
                "rating": review.get("score", 0),
                "likes": review.get("ups", 0),
                "time": review.get("created_time", ""),
                "url": f"https://www.taptap.cn/review/{review.get('id', '')}",
            })
            
            if len(reviews) >= limit:
                break
        
        # 获取下一页cursor
        next_cursor = data.get("data", {}).get("next_cursor", "")
        if not next_cursor or next_cursor == from_cursor:
            break
        from_cursor = next_cursor
        
        time.sleep(0.5)
    
    print(f"[taptap_review] 成功抓取 {len(reviews)} 条评价")
    return reviews[:limit]


def main():
    parser = argparse.ArgumentParser(description="TapTap Review API Crawler")
    parser.add_argument("--app-id", required=True, help="TapTap app ID")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--game-name", required=True, help="游戏名称")
    parser.add_argument("--limit", type=int, default=50, help="数量限制")
    args = parser.parse_args()
    
    reviews = fetch_reviews(args.app_id, args.game_id, args.game_name, args.limit)
    
    # 保存数据
    storage = DataStorage(args.game_id)
    output_data = {
        "platform": "taptap",
        "data_type": "review",
        "game_id": args.game_id,
        "game_name": args.game_name,
        "app_id": args.app_id,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(reviews),
        "items": reviews,
    }
    
    output_path = storage.merge_and_save(output_data, "taptap", "review", id_field="id")
    print(f"[taptap_review] 数据已保存到: {output_path}")
    
    # 更新索引
    update_index(args.game_id, args.game_name, "taptap", "review", count=len(reviews))


if __name__ == "__main__":
    main()
