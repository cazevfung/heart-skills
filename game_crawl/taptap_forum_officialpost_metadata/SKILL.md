---
name: taptap_forum_officialpost_metadata
description: "TapTap 官方帖子元数据抓取。使用 browser 模式抓取官方帖子列表，获取标题、链接。不抓取评论。"
metadata:
  {
    "copaw":
      {
        "emoji": "📋",
        "requires": {}
      }
  }
---

# TapTap Forum Official Post Metadata Skill

## 职责
- 使用 browser 抓取 TapTap 官方帖子列表
- URL: `https://www.taptap.cn/app/{app_id}/topic?type=official`
- 获取帖子标题、链接
- 不抓取评论

## 禁止
- ❌ 不抓取评论（由 taptap_comment 处理）

## 输入
- `--app-id`: TapTap app ID（必填）
- `--limit`: 帖子数量限制
- `--output`: 输出文件

## 输出格式
```json
{
  "platform": "taptap",
  "phase": "metadata",
  "data_type": "forum_officialpost",
  "app_id": "12345",
  "posts": [
    {
      "id": "帖子ID",
      "title": "标题",
      "url": "https://..."
    }
  ]
}
```

## 执行
```bash
python scripts/taptap_forum_officialpost_metadata.py --app-id "45213" --limit 30
```

## 下一步
输出文件供 `taptap_comment` skill 使用。
