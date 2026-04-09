---
name: game_crawl
description: "游戏数据抓取统一入口。协调多平台数据抓取：TapTap、Bilibili、Reddit、YouTube。自动规划、执行、汇总，一站式完成游戏数据收集。"
metadata:
  {
    "copaw":
      {
        "emoji": "🎮",
        "requires": {}
      }
  }
---

# Game Crawl Skill

## 职责

本 skill 是游戏数据抓取的**统一入口**，负责协调全流程：

```
用户输入需求
    ↓
1. 需求解析 → 确定游戏、平台、数据类型
    ↓
2. 调用 crawler_planning → 生成抓取计划
    ↓
3. 执行任务序列 → 逐个平台抓取
    ↓
4. 汇总结果 → 输出数据摘要
```

**核心原则：用户只需提供游戏名，系统自动完成剩余工作。**

---

## 输入

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| game_id | 是 | 游戏ID | `g_genshin` |
| game_name | 否 | 游戏中文名（用于搜索） | `原神` |
| platforms | 否 | 指定平台，逗号分隔 | `taptap,bilibili` |
| data_types | 否 | 数据类型，逗号分隔 | `review,comment` |
| limit | 否 | 每平台数量限制 | `50` |
| force | 否 | 强制重新抓取 | `false` |
| resume | 否 | 从 checkpoint 恢复 | `false` |

---

## 支持的平台

| 平台 | 数据类型 | 说明 |
|------|---------|------|
| **taptap** | review, comment | 评价、帖子评论 |
| **bilibili** | metadata, transcript | 视频元数据、字幕 |
| **reddit** | metadata, comment | 帖子、评论 |
| **youtube** | metadata, transcript | 视频元数据、字幕 |

---

## 执行流程

### Step 1 — 需求解析

从用户输入提取关键信息：
- 游戏ID（必须）
- 游戏名称（用于搜索关键词）
- 目标平台（默认自动选择）
- 数据类型（默认全部）
- 数量限制（默认 50）

### Step 2 — 规划任务

调用 `crawler_planning` 生成抓取计划：

```
读取 crawler_planning/SKILL.md
    ↓
分析游戏类型、平台选择策略
    ↓
生成任务序列（含依赖关系）
    ↓
输出执行计划
```

### Step 3 — 执行抓取

按任务序列逐个执行：

```
for task in plan.tasks:
    # 检查依赖
    if task.depends_on:
        等待依赖任务完成
    
    # 试点验证（5条）
    执行试点抓取
    if 试点失败:
        跳过该平台，记录错误
        continue
    
    # 全量抓取
    执行完整抓取
    
    # 保存 checkpoint
    定期保存进度
```

### Step 4 — 汇总结果

所有任务完成后：
- 统计各平台数据量
- 更新数据索引
- 生成执行报告
- 返回数据路径

---

## 使用方式

### 方式一：完整抓取（推荐）

```bash
# 自动选择平台，抓取全部数据类型
python skills/game_crawl/scripts/crawl.py --game-id g_genshin --game-name "原神"

# 指定平台和数量
python skills/game_crawl/scripts/crawl.py \
    --game-id g_genshin \
    --game-name "原神" \
    --platforms taptap,bilibili \
    --limit 50

# 强制重新抓取
python skills/game_crawl/scripts/crawl.py \
    --game-id g_genshin \
    --force
```

### 方式二：分步执行

```bash
# 1. 规划任务
python skills/game_crawl/crawler_planning/scripts/plan.py \
    --game-id g_genshin \
    --output plan.json

# 2. 执行单个任务
python skills/game_crawl/taptap_review/scripts/taptap_review.py \
    --game-id g_genshin \
    --app-id 45213 \
    --limit 50

# 3. 查看结果
python scripts/data_query.py --game-id g_genshin --list
```

### 方式三：通过 OpenClaw 调用

用户发送消息：
> "抓取原神的最新数据"

Agent 执行：
1. 识别游戏ID：`g_genshin`
2. 读取本 skill
3. 调用规划 → 执行 → 汇总
4. 返回结果摘要

---

## 子 Skill 说明

### crawler_planning

**职责**：任务规划与拆解
**输入**：游戏信息、抓取需求
**输出**：任务执行计划
**文档**：`crawler_planning/SKILL.md`

### 平台抓取 Skills

| Skill | 职责 | 脚本路径 |
|-------|------|---------|
| taptap_review | TapTap 评价抓取 | `taptap_review/scripts/taptap_review.py` |
| taptap_comment | TapTap 评论抓取 | `taptap_comment/scripts/taptap_comment.py` |
| taptap_forum_officialpost_metadata | TapTap 帖子元数据 | `taptap_forum_officialpost_metadata/scripts/...` |
| bilibili_metadata | B站视频搜索 | `bilibili_metadata/scripts/bilibili_metadata.py` |
| bilibili_transcript | B站字幕抓取 | `bilibili_transcript/scripts/bilibili_transcript.py` |
| reddit_metadata | Reddit 帖子搜索 | `reddit_metadata/scripts/reddit_metadata.py` |
| reddit_comment | Reddit 评论抓取 | `reddit_comment/scripts/reddit_comment.py` |
| youtube_metadata | YouTube 视频搜索 | `youtube_metadata/scripts/youtube_metadata.py` |
| youtube_transcript | YouTube 字幕抓取 | `youtube_transcript/scripts/youtube_transcript.py` |
| official_site_crawl | 官网公告抓取 | `official_site_crawl/SKILL.md` |

---

## 数据输出

抓取结果保存至：

```
data/game_data/games/{game_id}/
├── taptap/
│   ├── review.json
│   └── comment.json
├── bilibili/
│   ├── metadata.json
│   └── transcript.json
├── reddit/
│   ├── metadata.json
│   └── comment.json
├── youtube/
│   ├── metadata.json
│   └── transcript.json
└── checkpoints/          # checkpoint 文件
```

---

## 错误处理

| 错误场景 | 处理策略 |
|---------|---------|
| 游戏未注册 | 提示用户先注册游戏 |
| 平台不支持 | 跳过该平台，继续其他平台 |
| 网络超时 | 重试 3 次，失败后跳过 |
| 反爬拦截 | 停止该平台，记录错误 |
| 数据格式错误 | 停止该任务，检查脚本 |

---

## 最佳实践

1. **优先使用自动规划** — 让系统选择最佳平台组合
2. **设置合理 limit** — 首次抓取建议 30-50 条试点
3. **使用 resume 恢复** — 长任务中断后从 checkpoint 恢复
4. **定期更新数据** — 热门游戏建议每周更新一次
5. **监控数据质量** — 检查抓取结果是否完整、格式是否正确

---

## 注意事项

- 所有脚本需要 `--game-id` 参数
- 支持 `--resume` 断点续传
- 数据自动合并，不覆盖已有数据
- 遵守各平台的使用条款和速率限制
- 频繁抓取可能触发反爬机制，请合理设置间隔

---

_一站式游戏数据抓取，从需求到数据。_
