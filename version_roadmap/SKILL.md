---
name: version_roadmap
description: "当用户需要版本节奏建议、排期建议、大版本间隔与小活动填充时使用本 skill。基于 changelog 历史与可选舆情/留存结论，给出版本节奏建议（蜜月期/空档期）、排期注意事项。与 game_report 的 version 报告区分：version 报告是单版本内容分析，本 skill 是多版本节奏与规划。"
metadata:
  {
    "copaw": {
      "emoji": "📅",
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

# 版本节奏与排期专家 Skill

本 skill 基于 `game_crawl` 的 changelog 历史与可选的舆情/留存结论（或报告摘要），给出版本节奏建议（大版本间隔、小活动填充、蜜月期/空档期）与排期注意事项。本 skill 不直接爬取数据；数据缺失或过期时委托 **game_crawl** 收集。

## 何时使用

- 用户提到：**版本节奏**、排期、大版本间隔、小活动填充、蜜月期、空档期、更新频率、下版本什么时候
- 用户问：某游戏版本节奏是否健康、排期建议、如何避免空档期
- 需要产出**版本节奏/排期建议报告**

若用户仅要单版本内容分析，使用 **game_report**（report_type=version）；若要做多版本节奏与规划建议，使用本 skill。

## 参数提取

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **game** | 游戏名称（中文或英文） | 从用户消息推断，无法推断时询问 |
| **platform** | 数据来源平台（单平台或 `all`） | `all` |
| **date_range** | 分析的时间范围（用于 changelog 与可选 UGC） | 近 6 个月 |
| **report_context** | 可选已有报告摘要或路径（舆情/留存结论，用于「当前阶段」判断） | 无 |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **report_language** | 报告语言 | 与用户提问语言一致 |
| **output_path** | 输出目录 | `user/documents/游戏分析报告/` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |
| **use_existing_data_only** | 用户明确「只用现有数据」时不触发爬取 | `no` |

执行前 Echo 已解析参数。

## 数据来源与就绪检查

**数据根目录：** 与 game_report 一致。**必选 data_types：** `changelogs`。**可选：** `reviews`、`forum_posts`（用于当前运营阶段判断）。就绪规则同 game_report；若有缺失或过期且未设置 `use_existing_data_only`，**委托 game_crawl**，待完成后再继续。

## 执行流程

### Phase 1 — 理解与参数

1. 解析用户消息，填写参数表；推断 `game`（不明确则询问）。
2. 若有 report_context（报告摘要或路径），读取后抽取「当前阶段」「核心问题」等，供 Phase 3 使用。
3. Echo 已解析参数；确认使用「版本节奏/排期建议报告」。

### Phase 2 — 数据就绪

1. 对 changelogs（及可选的 reviews、forum_posts）做就绪检查；若有需爬取项，委托 **game_crawl**，完成后继续。

### Phase 3 — 节奏与排期分析

1. 从合并存储读取 `changelogs`（及可选的 reviews、forum_posts）。
2. 阅读 **references/roadmap_framework.md**，完成：
   - 历史版本间隔统计（大版本/小更新频率）；
   - 当前运营阶段判断（可与 game_report 的 ops_knowledge 阶段衔接：买量冲刺期/版本发布期/内容消化期/版本末尾疲劳期/版本空档期/危机响应期）；
   - 蜜月期/空档期定义与建议（大版本后蜜月期活动密度、空档期填充建议）；
   - 排期注意事项（与品类正常更新间隔对比、风险点）。
3. 若存在 report_context，将其中「当前阶段」「核心问题」融入节奏建议。

### Phase 4 — 报告生成与输出

1. 按 **references/template_roadmap.md** 生成版本节奏与排期建议报告正文。
2. 若 `report_format=markdown`：按 `output_destination` 写文件或仅在对话中输出；若 `report_format=feishu`：调用 **feishu_create_doc** 工具，返回后打印飞书文档 URL。

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| 版本节奏、排期、蜜月期/空档期建议 | **version_roadmap**（本 skill） |
| 单版本内容分析、更新日志解读 | **game_report**（report_type=version） |
| 归因与责任划分 | **attribution_ops** |

## 参考文件

- 节奏原则与阶段定义：[references/roadmap_framework.md](references/roadmap_framework.md)
- 版本节奏报告模板：[references/template_roadmap.md](references/template_roadmap.md)
- 运营阶段定义（可衔接）：[game_report/references/ops_knowledge.md](../game_report/references/ops_knowledge.md)
