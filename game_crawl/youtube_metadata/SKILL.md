---
name: youtube_metadata
description: "YouTube 视频搜索专用 skill。使用 Supadata API 搜索视频，支持 checkpoint 和规范化存储。"
metadata:
  {
    "copaw":
      {
        "emoji": "🔍",
        "requires": {}
      }
  }
---

# YouTube Metadata Skill

## 职责
- 搜索 YouTube 视频，获取元数据
- 支持 checkpoint 断点续传
- 规范化存储到 game_id 目录

## 禁止
- ❌ 不抓取转录
- ❌ 不抓取评论
- ❌ 不使用 browser

## 输入
- `--game-id`: 游戏ID（必填，如 g_genshin）
- `--query`: 英文搜索关键词（必填）
- `--limit`: 结果数量限制（默认30）
- `--resume`: 从 checkpoint 恢复（可选）

## 输出
- 规范路径：`games/{game_id}/youtube/metadata.json`
- 自动合并，不覆盖已有数据

## 执行
```bash
# 新任务
python scripts/youtube_metadata.py --game-id g_genshin --query "Tolan app review" --limit 30

# 断点续传
python scripts/youtube_metadata.py --game-id g_genshin --query "Tolan app review" --limit 30 --resume
```

## 数据管理
- 每 10 条自动保存 checkpoint
- 最终数据自动合并到规范路径
- 保留最近 3 个 checkpoint

## 下一步
输出供 `youtube_transcript` skill 使用。
