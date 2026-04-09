---
name: game_data_pipeline
description: "游戏数据全流程管理 skill。从游戏名称到最终数据的一站式处理：自动发现游戏信息、注册到 game_registry、规划抓取任务、协调各平台爬虫执行、汇总结果。用户只需提供游戏名，系统自动完成全流程。"
metadata:
  {
    "copaw":
      {
        "emoji": "🔄",
        "requires": {}
      }
  }
---

# Game Data Pipeline Skill

## 职责

本 skill 是游戏数据抓取的**总入口**，负责协调全流程：

```
用户输入游戏名
    ↓
1. game_discovery - 发现游戏信息（英文名、关键词、上线日期）
    ↓
2. game_registry - 检查/注册游戏（生成 game_id）
    ↓
3. 规划抓取任务 - 根据游戏类型选择平台
    ↓
4. 执行抓取 - 调用各平台 skill
    ↓
5. 汇总结果 - 输出数据摘要
```

## 输入

| 参数 | 必填 | 说明 |
|------|------|------|
| game_name | 是 | 游戏中文名（如"原神"） |
| platforms | 否 | 指定平台（默认自动选择） |
| limit | 否 | 每个平台抓取数量（默认30） |

## 输出

数据保存至规范路径：
```
data/game_data/games/{game_id}/
├── reddit/posts.json
├── reddit/comments.json
├── taptap/reviews.json
├── taptap/metadata.json
├── taptap/comments.json
├── youtube/metadata.json
├── youtube/transcripts.json
├── bilibili/metadata.json
└── bilibili/transcripts.json
```

## 执行流程

### 完整流程（推荐）

```bash
# 只需游戏名，自动完成全流程
python skills/game_data_pipeline/scripts/run_pipeline.py --game-name "原神" --limit 30
```

### 分步执行

```bash
# 1. 发现游戏
python skills/game_discovery/scripts/discover.py --game "原神"

# 2. 注册游戏（如果未注册）
python scripts/registry_tool.py --add --name "原神" --en "Genshin Impact"

# 3. 执行抓取（YouTube）
python skills/game_crawl/youtube_metadata/scripts/youtube_metadata.py \
    --game-id g_genshin --query "Genshin Impact review" --limit 30
python skills/game_crawl/youtube_transcript/scripts/youtube_transcript.py \
    --game-id g_genshin --input youtube_metadata.json

# 4. 执行抓取（Reddit）
python skills/game_crawl/reddit_metadata/scripts/reddit_metadata.py \
    --game-id g_genshin --subreddit Genshin_Impact --limit 30
python skills/game_crawl/reddit_comment/scripts/reddit_comment.py \
    --game-id g_genshin --input reddit_metadata.json
```

## 平台选择策略

| 游戏类型 | 推荐平台 |
|---------|---------|
| 国内游戏 | bilibili, taptap |
| 海外游戏 | youtube, reddit |
| 全球热门 | 全部平台 |

## 依赖 Skill

- `game_discovery` - 游戏信息发现
- `youtube_metadata` / `youtube_transcript`
- `bilibili_metadata` / `bilibili_transcript`
- `reddit_metadata` / `reddit_comment`
- `taptap_review` / `taptap_forum_officialpost_metadata` / `taptap_comment`

## 注意事项

1. 所有抓取脚本需要 `--game-id` 参数
2. 支持 `--resume` 断点续传
3. 数据自动合并，不覆盖已有数据
4. 最终数据存储在规范路径

---

_一站式游戏数据抓取，从名称到数据。_
