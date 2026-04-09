---
name: bilibili_transcript
description: "Bilibili 视频转录专用 skill。完整流程：下载视频→提取音频→上传OSS→DashScope转录。仅转录，不搜索。输入来自 bilibili_metadata 的输出。"
metadata:
  {
    "copaw":
      {
        "emoji": "📝",
        "requires": {}
      }
  }
---

# Bilibili Transcript Skill

## 职责
完整转录流程：
1. 读取视频链接（来自 bilibili_metadata 输出）
2. yt-dlp 下载视频（480p）
3. ffmpeg 提取音频（MP3）
4. 上传阿里云 OSS
5. DashScope Paraformer 转录
6. 删除临时文件
7. 输出转录文本

## 禁止
- ❌ 不搜索视频
- ❌ 不抓取评论
- ❌ 不保留临时视频/音频文件

## 输入
- `--input`: bilibili_metadata 的输出文件（必填）
- `--output`: 转录结果文件

## 输出格式
```json
{
  "platform": "bilibili",
  "phase": "transcript",
  "videos": [
    {
      "bvid": "BV1xxx",
      "title": "标题",
      "url": "https://bilibili.com/video/BV1xxx",
      "transcript": "转录文本内容...",
      "transcript_length": 1234
    }
  ]
}
```

## 执行
```bash
# 先执行 metadata
python ../bilibili_metadata/scripts/bilibili_metadata.py --keyword "原神 前瞻" --limit 10

# 再执行 transcript
python scripts/bilibili_transcript.py --input ../bilibili_metadata/output.json
```

## 环境依赖
- `BILIBILI_COOKIE` - B站登录
- `DASHSCOPE_API_KEY` - 阿里云转录
- `OSS_ACCESS_KEY_ID` - 阿里云 OSS
- `OSS_ACCESS_KEY_SECRET` - 阿里云 OSS
- `OSS_BUCKET` - Bucket 名称
- `OSS_ENDPOINT` - OSS  endpoint

## 工具依赖
- yt-dlp
- ffmpeg
