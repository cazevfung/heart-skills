#!/usr/bin/env python3
"""
过滤 Reddit metadata 并执行评论抓取
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

# 配置
GAME_ID = "g_a1b2c3d4"
GAME_NAME = "心动小镇"
CUTOFF_TIME = "2026-04-01T09:30:37+00:00"
METADATA_PATH = Path("D:/App Dev/openclaw-main/data/game_data/games/g_a1b2c3d4/reddit/metadata.json")
OUTPUT_PATH = Path("D:/App Dev/openclaw-main/data/game_data/games/g_a1b2c3d4/reddit/filtered_metadata.json")

def parse_time(time_str):
    """解析 ISO 时间字符串"""
    return datetime.fromisoformat(time_str.replace("Z", "+00:00"))

def main():
    # 读取 metadata
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    items = data.get("items", [])
    cutoff = parse_time(CUTOFF_TIME)
    
    # 过滤新帖子
    new_posts = []
    for item in items:
        post_time = parse_time(item.get("created_utc", "1970-01-01T00:00:00+00:00"))
        if post_time > cutoff:
            new_posts.append(item)
    
    print(f"[filter] 总帖子数: {len(items)}")
    print(f"[filter] 截止时间: {CUTOFF_TIME}")
    print(f"[filter] 新帖子数: {len(new_posts)}")
    
    # 保存过滤后的 metadata
    filtered_data = {
        "platform": "reddit",
        "game_id": GAME_ID,
        "data_type": "metadata",
        "phase": "metadata",
        "subreddit": "heartopia",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(new_posts),
        "items": new_posts,
    }
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)
    
    print(f"[filter] 过滤后数据保存: {OUTPUT_PATH}")
    
    # 返回统计
    return len(new_posts)

if __name__ == "__main__":
    count = main()
    print(f"\n结果: {count} 个新帖子需要抓取评论")
