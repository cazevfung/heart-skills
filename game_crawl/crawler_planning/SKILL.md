---
name: crawler_planning
description: "游戏数据抓取专用任务规划。将用户的抓取需求拆解为具体的平台抓取任务序列，管理抓取策略、速率限制、数据新鲜度和 checkpoint 恢复。"
metadata:
  {
    "copaw":
      {
        "emoji": "🕷️",
        "requires": {}
      }
  }
---

# Crawler Planning Skill

## 职责

本 skill 是游戏数据抓取的**规划层**，专门处理爬虫任务的拆解与调度：

```
用户输入抓取需求
    ↓
1. 分析需求 → 确定目标平台、数据类型、数量
    ↓
2. 选择策略 → 根据游戏类型选择平台组合
    ↓
3. 生成任务序列 → 按依赖关系排序
    ↓
4. 输出执行计划 → 具体的脚本调用序列
```

## 核心原则

**先规划，再执行；先试点，再全量；有 checkpoint，能恢复。**

---

## 输入

| 参数 | 必填 | 说明 |
|------|------|------|
| game_id | 是 | 游戏ID（如 g_genshin） |
| game_name | 否 | 游戏中文名（用于搜索关键词） |
| platforms | 否 | 指定平台列表，默认自动选择 |
| data_types | 否 | 数据类型（metadata/review/comment/transcript） |
| limit | 否 | 每平台抓取数量，默认 50 |
| force | 否 | 强制重新抓取，无视现有数据 |

---

## 平台选择策略

读取 `references/platform_selection.md` 获取完整策略：

| 游戏类型 | 首选平台 | 次选平台 |
|---------|---------|---------|
| 国内手游 | taptap, bilibili | - |
| 海外手游 | youtube, reddit | - |
| 全球热门 | 全部平台 | - |
| 独立游戏 | reddit, youtube | bilibili |

---

## 数据类型依赖关系

```
comment → 依赖 → metadata (帖子列表)
transcript → 依赖 → metadata (视频列表)
review → 独立
metadata → 独立
```

**执行顺序必须满足依赖关系。**

---

## 执行流程

### Step 1 — 需求解析

从用户输入提取：
- 游戏ID
- 目标平台（显式指定 or 自动推断）
- 数据类型
- 数量限制
- 是否强制刷新

### Step 2 — 平台选择

如果没有显式指定平台：
1. 检查 game_registry.json 中的游戏信息
2. 根据游戏类型选择默认平台组合
3. 考虑数据新鲜度，跳过较新的平台（除非 force=true）

### Step 3 — 任务拆解

为每个平台生成任务列表：

```json
{
  "tasks": [
    {
      "platform": "taptap",
      "data_type": "review",
      "script": "skills/game_crawl/taptap_review/scripts/taptap_review.py",
      "args": ["--game-id", "g_genshin", "--app-id", "45213", "--limit", "50"],
      "depends_on": [],
      "estimated_time": "5min"
    },
    {
      "platform": "taptap", 
      "data_type": "comment",
      "script": "skills/game_crawl/taptap_comment/scripts/taptap_comment.py",
      "args": ["--game-id", "g_genshin", "--input", "..."],
      "depends_on": ["taptap_metadata"],
      "estimated_time": "10min"
    }
  ]
}
```

### Step 4 — 试点验证

每个平台的第一个任务先执行试点（5条）：
- 验证数据格式正确
- 验证网络连接正常
- 验证反爬机制未触发

试点失败 → 停止该平台的后续任务
试点成功 → 继续全量抓取

### Step 5 — 全量执行

按依赖顺序执行任务：
1. 独立任务并行执行
2. 依赖任务等待前置完成
3. 每任务支持 `--resume` 断点续传
4. 定期保存 checkpoint

---

## 速率限制策略

读取 `references/rate_limiting.md`：

| 平台 | 请求间隔 | 并发限制 | 备注 |
|------|---------|---------|------|
| taptap | 2-3秒 | 1 | 滚动加载，需模拟 |
| bilibili | 0.5秒 | 1 | API 调用，有频率限制 |
| reddit | 1秒 | 1 | 需要登录态 |
| youtube | 1秒 | 1 | API key 配额限制 |

---

## Checkpoint 策略

读取 `references/checkpoint_strategy.md`：

- **保存时机**: 每 10-20 条数据 or 每 60 秒
- **保存位置**: `data/game_data/games/{game_id}/checkpoints/`
- **恢复方式**: 脚本支持 `--resume` 参数
- **清理策略**: 保留最近 3 个 checkpoint

---

## 输出格式

### 执行计划

```json
{
  "plan_id": "plan_20260319_001",
  "game_id": "g_genshin",
  "created_at": "2026-03-19T15:30:00Z",
  "tasks": [
    {
      "id": "task_001",
      "platform": "taptap",
      "data_type": "review",
      "script_path": "D:/App Dev/openclaw-main/skills/game_crawl/taptap_review/scripts/taptap_review.py",
      "args": ["--game-id", "g_genshin", "--app-id", "45213", "--limit", "50"],
      "depends_on": [],
      "status": "pending",
      "estimated_time_seconds": 300
    }
  ],
  "total_estimated_time": "15min",
  "parallel_groups": [["task_001", "task_002"], ["task_003"]]
}
```

---

## 错误处理

| 错误类型 | 处理策略 |
|---------|---------|
| 网络超时 | 重试 3 次，每次间隔 5 秒 |
| 反爬拦截 | 停止该平台，记录错误，继续其他平台 |
| 数据格式错误 | 停止该任务，检查脚本是否需要更新 |
| 依赖任务失败 | 跳过依赖该任务的所有后续任务 |

---

## 使用示例

### 基本用法

```bash
# 自动规划并执行
python skills/game_crawl/crawler_planning/scripts/plan.py \
    --game-id g_genshin \
    --game-name "原神" \
    --limit 50

# 指定平台
python skills/game_crawl/crawler_planning/scripts/plan.py \
    --game-id g_genshin \
    --platforms taptap,bilibili \
    --limit 30

# 强制刷新
python skills/game_crawl/crawler_planning/scripts/plan.py \
    --game-id g_genshin \
    --force
```

### 通过 OpenClaw 调用

当 game-crawler 接到抓取任务时：

1. 读取本 skill
2. 调用规划逻辑生成任务序列
3. 按序执行每个抓取脚本
4. 汇总结果

---

## 注意事项

1. **不要并行执行同一平台的多个任务** — 容易触发反爬
2. **优先使用现有数据** — 检查数据新鲜度，避免重复抓取
3. **试点先行** — 全量抓取前先验证 5 条数据
4. **及时 checkpoint** — 长任务定期保存，支持恢复
5. **尊重平台规则** — 遵守 robots.txt 和平台使用条款

---

_爬虫规划：从需求到执行序列的桥梁。_
