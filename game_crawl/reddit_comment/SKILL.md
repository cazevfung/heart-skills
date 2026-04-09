---
name: reddit_comment
description: "Reddit 帖子评论抓取。读取 reddit_metadata 输出，获取每个帖子的评论。"
metadata:
  {
    "copaw":
      {
        "emoji": "💬",
        "requires": {}
      }
  }
---

# Reddit Comment Skill

## 职责
- 读取 reddit_metadata 输出的帖子链接
- 获取每个帖子的评论

## 输入
- `--input`: reddit_metadata 输出文件（必填）
- `--output`: 输出文件

## 输出格式
```json
{
  "platform": "reddit",
  "phase": "comment",
  "posts": [
    {
      "id": "帖子ID",
      "title": "标题",
      "comments": [
        {"author": "评论者", "body": "评论内容", "score": 10}
      ]
    }
  ]
}
```

## 执行
```bash
python scripts/reddit_comment.py --input reddit_metadata.json --output reddit_comments.json
```
