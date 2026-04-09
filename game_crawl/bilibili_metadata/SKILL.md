---
name: bilibili_metadata
description: "Bilibili 视频搜索专用 skill。仅使用 B站 API 搜索视频，获取元数据和链接。不下载视频，不转录。输出供 bilibili_transcript 使用。"
metadata:
  {
    "copaw":
      {
        "emoji": "🔍",
        "requires": {}
      }
  }
---

# Bilibili Metadata Skill

## 职责
仅搜索 Bilibili 视频，获取：
- 视频标题
- BV号/链接
- UP主名称
- 发布时间
- 播放量
- 视频时长

## 禁止
- ❌ 不下载视频
- ❌ 不转录
- ❌ 不抓取评论

## 输入
- `--keyword`: 搜索关键词（必填）
- `--limit`: 结果数量限制（默认30）
- `--official-only`: 仅官方账号（可选）

## 输出格式
```json
{
  "platform": "bilibili",
  "phase": "metadata",
  "keyword": "搜索词",
  "videos": [
    {
      "bvid": "BV1xxx",
      "title": "标题",
      "author": "UP主",
      "url": "https://bilibili.com/video/BV1xxx",
      "pubdate": "2024-01-01",
      "duration": "10:30"
    }
  ]
}
```

## 执行
```bash
python scripts/bilibili_metadata.py --keyword "原神 前瞻" --limit 10
```

## 下一步
输出文件供 `bilibili_transcript` skill 使用。
