---
name: market_landscape
description: "【强制入口】任何涉及分析市场上不同游戏表现、竞品对比、市场格局、本品定位的任务，必须先读本skill。本skill提供市场格局分析框架（竞品对照矩阵、品类位置评估、差异化定位建议），与单游戏分析的game_report有本质区别。禁止用game_report做市场格局分析，因缺乏多维度对照能力，易导致本品定位偏差。基于 game_crawl 的 merged 数据（多游戏的 app_info、reviews、forum_posts、changelogs）产出竞品对比表与市场格局小结；数据缺失或过期时委托 game_crawl 收集。"
metadata:
  {
    "copaw": {
      "emoji": "🗺️",
      "requires": {}
    },
    "openclaw": {
      "skillKey": "copaw-shared",
      "requires": {
        "bins": [
          "python3"
        ]
      }
    }
  }
---

# 竞品与市场格局专家 Skill

本 skill 从 `game_crawl` 的持久化数据中读取**多款游戏**的 app_info、reviews、forum_posts、changelogs，按对比维度产出竞品对比表、市场格局小结与本品定位建议。本 skill 不直接爬取数据；数据缺失或过期时委托 **game_crawl** 收集。

## 何时使用

- 用户提到：**竞品**、市场格局、竞品对比、多款对比、本品定位、赛道、品类位置
- 用户问：某几款游戏怎么对比、市场格局如何、本品在赛道中的位置
- 需要产出**竞品/市场专项报告**（与单款舆情/综合报告区分）

若用户仅要单款游戏的舆情或综合报告，使用 **game_report**；若仅要单款留存/付费，使用 **game_retention** / **game_monetization**。

## 参数提取

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **games** | 游戏名称列表（中文或英文，逗号分隔）；需包含「本品」若要做定位建议 | 从用户消息推断，无法推断时询问 |
| **focus_product** | 本品（用于定位建议段落） | 从 games 中指定或推断 |
| **platform** | 数据来源平台（单平台或 `all`） | `all` |
| **date_range** | 评价/帖子时间范围 | 近 3 个月 |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **report_language** | 报告语言 | 与用户提问语言一致 |
| **output_path** | 输出目录 | `user/documents/游戏分析报告/` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |
| **use_existing_data_only** | 用户明确「只用现有数据」时不触发爬取 | `no` |

执行前 Echo 已解析参数。

## 数据来源与就绪检查

**数据根目录：** 与 game_report 一致。对 **games** 列表中每一款，检查其 `merged/<平台>/<game_id>/<data_type>/data.json` 是否存在且 `last_updated` 在 24 小时内。所需 data_types：`app_info`、`reviews`、`forum_posts`；可选 `changelogs`。若有任一款缺失或过期且未设置 `use_existing_data_only`，**委托 game_crawl** 对缺失项进行收集，待完成后再继续。

## 执行流程

### Phase 1 — 理解与参数

1. 解析用户消息，填写参数表；推断 `games`（不明确则询问）；确定 `focus_product`（若有定位需求）。
2. Echo 已解析参数；确认使用「竞品/市场格局报告」。

### Phase 2 — 数据就绪

1. 对 games 列表中每款游戏按「数据来源与就绪检查」执行；若有需爬取项，委托 **game_crawl**（可批量或逐款），完成后继续。

### Phase 3 — 竞品与格局分析

1. 从合并存储读取各款游戏的 `app_info`、`reviews`、`forum_posts`（及可选的 `changelogs`）。
2. 阅读 **references/landscape_framework.md**，按对比维度（评分、口碑、版本节奏、付费感知、品类位置等）整理多维度对比表。
3. 归纳市场格局小结；若指定了 focus_product，给出本品定位建议。

### Phase 4 — 报告生成与输出

1. 按 **references/template_landscape.md** 生成竞品/市场格局报告正文。
2. 若 `report_format=markdown`：按 `output_destination` 写文件或仅在对话中输出；若 `report_format=feishu`：调用 **feishu_create_doc** 工具，返回后打印飞书文档 URL。

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| 竞品对比、市场格局、本品定位 | **market_landscape**（本 skill） |
| 单款舆情/版本/综合报告 | **game_report** |
| 仅收集数据、不写报告 | **game_crawl** |

## 参考文件

- 对比维度与品类用语：[references/landscape_framework.md](references/landscape_framework.md)
- 竞品/市场报告模板：[references/template_landscape.md](references/template_landscape.md)
