---
name: taptap_review
description: "TapTap 游戏评价抓取。使用 browser 模式抓取评价页面，支持滚动加载。"
metadata:
  {
    "copaw":
      {
        "emoji": "⭐",
        "requires": {}
      }
  }
---

# TapTap Review Skill

## 职责
- 使用 browser 抓取 TapTap 游戏评价
- URL: `https://www.taptap.cn/app/{app_id}/review?os=pc`
- 支持滚动加载更多

## 输入
- `--app-id`: TapTap app ID（必填）
- `--limit`: 评价数量限制（默认50）
- `--output`: 输出文件

## 输出格式
```json
{
  "platform": "taptap",
  "data_type": "review",
  "app_id": "12345",
  "reviews": [
    {
      "author": "用户名",
      "content": "评价内容",
      "likes": 10
    }
  ]
}
```

## 执行
```bash
python scripts/taptap_review.py --app-id "45213" --limit 50
```

## 抓取字段
- 用户名: `.review-item__user-wrap a span` 或 `.review-item__user-wrap span`
- 评价内容: `.review-item__body .collapse-text-emoji__content span`
- 点赞数: `.review-vote-up span`
