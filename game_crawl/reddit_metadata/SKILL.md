---
name: reddit_metadata
description: "Reddit 帖子元数据抓取。搜索 subreddit，获取帖子标题、内容、链接。不抓取评论。输出供 reddit_comment 使用。"
metadata:
  {
    "copaw":
      {
        "emoji": "🔴",
        "requires": {}
      }
  }
---

# Reddit Metadata Skill

## 职责
- 搜索指定 subreddit
- 获取帖子标题、作者、内容、链接
- 不抓取评论

## 禁止
- ❌ 不抓取评论（由 reddit_comment 处理）

## 输入
- `--subreddit`: subreddit 名称（必填）
- `--limit`: 帖子数量限制
- `--output`: 输出文件

## 输出格式
```json
{
  "platform": "reddit",
  "phase": "metadata",
  "subreddit": "subreddit名",
  "posts": [
    {
      "id": "帖子ID",
      "title": "标题",
      "author": "作者",
      "content": "内容",
      "url": "https://reddit.com/r/xxx/comments/xxx",
      "created_utc": "2024-01-01T00:00:00"
    }
  ]
}
```

## 执行
```bash
python scripts/reddit_metadata.py --subreddit "Genshin_Impact" --limit 30
```

## 下一步
输出文件供 `reddit_comment` skill 使用。
