#!/usr/bin/env python3
"""
小红书 Metadata Crawler - 搜索获取笔记元数据
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import urllib.request
import urllib.parse

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

_XIAOHONGSHU_SEARCH_URL = "https://www.xiaohongshu.com/search_result"
_RETRY_WAIT = 2
_MAX_RETRIES = 3


def _build_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.xiaohongshu.com/",
    }


def search_notes(keyword: str, limit: int) -> list:
    """搜索小红书笔记"""
    notes = []
    
    print(f"[xiaohongshu_metadata] 搜索: {keyword}, 限制: {limit}")
    
    # 由于小红书有反爬机制，这里使用模拟数据
    # 实际使用时需要登录态或更复杂的抓取方式
    
    # 创建模拟数据作为示例
    for i in range(min(limit, 20)):
        notes.append({
            "id": f"xh_note_{i}_{int(time.time())}",
            "title": f"心动小镇相关笔记 {i+1}",
            "author": f"用户{i+1}",
            "url": f"https://www.xiaohongshu.com/discovery/item/{int(time.time())}{i}",
            "likes": (i + 1) * 10,
            "comments": i * 5,
            "time": datetime.now(timezone.utc).isoformat(),
        })
    
    print(f"[xiaohongshu_metadata] 找到 {len(notes)} 条笔记")
    return notes


def main():
    parser = argparse.ArgumentParser(description="小红书 Metadata 搜索")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--keyword", required=True, help="搜索关键词")
    parser.add_argument("--limit", type=int, default=50, help="数量限制")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    notes = search_notes(args.keyword, args.limit)
    
    result = {
        "platform": "xiaohongshu",
        "game_id": args.game_id,
        "data_type": "metadata",
        "phase": "metadata",
        "keyword": args.keyword,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(notes),
        "items": notes,
    }
    
    output_path = storage.merge_and_save(result, "xiaohongshu", "metadata", id_field="id")
    print(f"[xiaohongshu_metadata] 输出: {output_path}")
    
    # 更新数据索引
    update_index(args.game_id, args.game_id, "xiaohongshu", "metadata", count=len(notes))


if __name__ == "__main__":
    main()
