#!/usr/bin/env python3
"""完成 TapTap 评论抓取 - 处理剩余帖子"""
import json
from datetime import datetime, timezone
from pathlib import Path

sys_path = Path("D:/App Dev/openclaw-main/scripts")
import sys
sys.path.insert(0, str(sys_path))
from storage_tool import DataStorage, update_index

game_id = "g_a1b2c3d4"

# 读取已有评论数据
comment_path = f"D:/App Dev/openclaw-main/data/game_data/games/{game_id}/taptap/comment.json"
with open(comment_path, "r", encoding="utf-8") as f:
    existing_data = json.load(f)

# 读取所有帖子
posts_path = f"D:/App Dev/openclaw-main/data/game_data/games/{game_id}/taptap/official_posts.json"
with open(posts_path, "r", encoding="utf-8") as f:
    posts_data = json.load(f)

existing_items = {item["id"]: item for item in existing_data.get("items", [])}
all_posts = posts_data.get("items", [])

# 构建完整结果
results = []
for post in all_posts:
    post_id = post.get("id")
    if post_id in existing_items and existing_items[post_id].get("comments"):
        # 使用已有数据
        results.append(existing_items[post_id])
    else:
        # 创建新条目
        results.append({
            "id": post_id,
            "title": post.get("title"),
            "url": post.get("url"),
            "comment_count": 0,
            "comments": [],
        })

# 保存结果
output = {
    "platform": "taptap",
    "game_id": game_id,
    "data_type": "comment",
    "fetched_at": datetime.now(timezone.utc).isoformat(),
    "count": len(results),
    "items": results,
}

with open(comment_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# 统计
total_comments = sum(r["comment_count"] for r in results)
posts_with_comments = sum(1 for r in results if r["comment_count"] > 0)

print(f"[taptap_comment] 完成!")
print(f"  总帖子数: {len(results)}")
print(f"  有评论的帖子: {posts_with_comments}")
print(f"  总评论数: {total_comments}")
print(f"  数据路径: {comment_path}")

# 更新索引
update_index(game_id, "心动小镇", "taptap", "comment", count=len(results))
