#!/usr/bin/env python3
"""
统计本次抓取的新评论数
"""
import json
from pathlib import Path

# 读取 filtered metadata
with open("D:/App Dev/openclaw-main/data/game_data/games/g_a1b2c3d4/reddit/filtered_metadata.json", "r", encoding="utf-8") as f:
    filtered = json.load(f)

# 读取 comments
with open("D:/App Dev/openclaw-main/data/game_data/games/g_a1b2c3d4/reddit/comment.json", "r", encoding="utf-8") as f:
    comments = json.load(f)

# 统计新帖子的评论数
new_post_ids = {item["id"] for item in filtered["items"]}
new_comments_count = 0

for item in comments["items"]:
    if item["id"] in new_post_ids:
        new_comments_count += item.get("comment_count", 0)

print(f"=== 心动小镇 Reddit 抓取结果 ===")
print(f"新获取帖子数: {filtered['count']}")
print(f"新获取评论数: {new_comments_count}")
print(f"数据文件路径:")
print(f"  - Metadata: D:\\App Dev\\openclaw-main\\data\\game_data\\games\\g_a1b2c3d4\\reddit\\metadata.json")
print(f"  - Comments: D:\\App Dev\\openclaw-main\\data\\game_data\\games\\g_a1b2c3d4\\reddit\\comment.json")
print(f"状态: 成功")
