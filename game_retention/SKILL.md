---
name: game_retention
description: "当用户需要游戏留存分析、流失原因研究、次日/7日/30日留存影响因素或留存改进建议时使用本 skill。基于 game_crawl 的玩家评价与论坛数据，从 UGC 中归纳留存风险因素与改进方向；无真实留存指标时在报告中明确说明为「基于玩家反馈的留存洞察」。可与 game_report 并列使用：留存专项用本 skill，舆情/版本/综合报告用 game_report。"
metadata:
  {
    "copaw": {
      "emoji": "📈",
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

# 游戏留存研究专家 Skill

本 skill 是游戏分析的**留存专项层**。从 `game_crawl` 的持久化数据（评价、论坛帖子、应用信息）中读取内容，按留存分析框架归纳流失风险因素、留存影响因素与可执行建议，输出结构化留存分析报告。本 skill 不直接爬取数据；数据缺失或过期时委托 **game_crawl** 收集。

## 何时使用

- 用户提到：**留存**、次日留存、7日留存、30日留存、**流失**、掉留、留资、DAU、retention、churn
- 用户问：某游戏的流失原因、如何提升留存、哪些问题影响留存
- 需要产出**留存专项报告**（与舆情/版本/综合报告区分）

若用户仅要舆情或版本分析，使用 **game_report**；若同时要「综合报告里包含留存视角」，可先完成 game_report，再基于同一数据用本 skill 补一份留存摘要。

## 参数提取

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **game** | 游戏名称（中文或英文） | 从用户消息推断，无法推断时询问 |
| **platform** | 数据来源平台（单平台或 `all`） | `all` |
| **date_range** | 评价/帖子时间范围 | 近 3 个月 |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **report_language** | 报告语言 | 与用户提问语言一致 |
| **output_path** | 输出目录（仅 `report_format=markdown` 且输出到文件时） | `user/documents/游戏分析报告/` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |

执行前 Echo 已解析参数。

## 数据来源与就绪检查

**数据根目录：** 与 game_report 一致，固定为项目根目录下的 `data/game_data`。

**所需 data_types：** `app_info`, `reviews`, `forum_posts`。可选：`changelogs`（用于版本节奏与留存关系）。

**就绪规则：** 与 game_report Phase 2 相同——检查 `merged/<平台>/<game_id>/<data_type>/data.json` 是否存在且 `last_updated` 在 24 小时内。若有缺失或过期，**委托 game_crawl** 传入对应 `game`、`data_types`、`platforms`（建议 `auto`），待完成后再继续。

## 执行流程

### Phase 1 — 理解与参数

1. 解析用户消息，填写参数表；推断 `game`（不明确则询问）。
2. Echo 参数；确认使用「留存专项报告」。

### Phase 2 — 数据就绪

1. 按「数据来源与就绪检查」对所需 data_types 做就绪检查。
2. 若有需爬取项，委托 **game_crawl**，完成后继续。

### Phase 3 — 留存分析

1. 从合并存储读取各平台 `reviews`、`forum_posts`、`app_info`（及可选的 `changelogs`）。
2. 阅读本 skill 的 **references/retention_framework.md**，按其中维度对 UGC 做归类与归纳：
   - 流失/弃坑相关表述（显式与隐式）
   - 留存风险因素（技术、商业化、运营、策划）
   - 可转化为改进建议的结论
3. **重要**：若没有真实 D1/D7/D30 等指标，在报告中明确注明：「本报告基于玩家评价与讨论归纳留存风险与建议，非来自真实留存数据。」

### Phase 4 — 报告生成与输出

1. 按 **references/template_retention.md** 生成留存分析报告正文。
2. 若 `report_format=markdown`：按 `output_destination` 写文件或仅在对话中输出；若 `report_format=feishu`：调用 **feishu_create_doc** 工具（传入 title、content、folder_token）；工具返回后打印飞书文档 URL 与简短确认。

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| 只做留存分析 / 流失原因 / 留存建议 | **game_retention**（本 skill） |
| 舆情、版本、综合分析 | **game_report** |
| 仅收集数据、不写报告 | **game_crawl** |
| 留存 + 舆情/版本一起要 | 先 **game_report**（或 game_crawl），再用本 skill 基于同一数据产出留存报告 |

## 扩展说明

- **新增维度**：在 `references/retention_framework.md` 中扩展流失归因分类或指标定义即可，无需改 Phase 主流程。
- **输出模板**：修改 `references/template_retention.md` 即可调整报告结构与命名。

## 参考文件

- 留存分析框架（指标、归因、建议结构）：[references/retention_framework.md](references/retention_framework.md)
- 留存报告模板：[references/template_retention.md](references/template_retention.md)
