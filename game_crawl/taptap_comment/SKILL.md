---
name: taptap_comment
description: "TapTap 帖子评论抓取。使用 browser 模式读取帖子页面，获取评论。"
metadata:
  {
    "copaw":
      {
        "emoji": "💬",
        "requires": {}
      }
  }
---

# TapTap Comment Skill

## 职责
- 使用 browser 打开帖子页面
- 获取帖子评论

## 输入
- `--input`: taptap_forum_officialpost_metadata 输出文件（必填）
- `--output`: 输出文件
- `--comment-limit`: 每帖子评论数（默认50）

## 输出格式
```json
{
  "platform": "taptap",
  "phase": "comment",
  "posts": [
    {
      "id": "帖子ID",
      "title": "标题",
      "comments": [
        {"author": "评论者", "content": "评论内容", "likes": 10}
      ]
    }
  ]
}
```

## 执行
```bash
python scripts/taptap_comment.py --input taptap_posts.json --output taptap_comments.json
```
