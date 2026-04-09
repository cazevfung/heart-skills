---
name: youtube_transcript
description: "YouTube 视频转录专用 skill。仅使用 Supadata API 按视频链接获取转录文本。不搜索，不抓取评论。输入来自 youtube_metadata 的输出。"
metadata:
  {
    "copaw":
      {
        "emoji": "📝",
        "requires": {}
      }
  }
---

# YouTube Transcript Skill

## 职责
仅获取 YouTube 视频转录：
- 读取视频链接
- 使用 Supadata 获取转录
- 输出纯文本

## 禁止
- ❌ 不搜索视频
- ❌ 不抓取评论
- ❌ 不使用 browser

## 输入
- `--input`: youtube_metadata 的输出文件（必填）
- `--output`: 转录结果文件

## 输出格式
```json
{
  "platform": "youtube",
  "phase": "transcript",
  "videos": [
    {
      "id": "视频ID",
      "title": "标题",
      "url": "https://youtube.com/watch?v=xxx",
      "transcript": "转录文本内容...",
      "transcript_length": 1234
    }
  ]
}
```

## 执行
```bash
# 先执行 metadata
python ../youtube_metadata/scripts/youtube_metadata.py --query "Tolan app review" --limit 30

# 再执行 transcript
python scripts/youtube_transcript.py --input ../youtube_metadata/output.json
```

## 依赖
- Supadata API key
