---
name: customer_engagement
description: "当用户需要问卷设计（按目标生成问卷结构、题目与选项建议）或用户调研分析（用户上传问卷结果/摘要产出洞察与可执行结论）时使用本 skill。支持目标类型：留存归因、付费意愿、活动满意度等。"
metadata:
  {
    "copaw": {
      "emoji": "📋",
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

# 用户调研与问卷专家 Skill

本 skill 支持两种模式：**问卷设计（survey_draft）** 按目标生成问卷结构、题目与选项建议；**调研分析（survey_analysis）** 对用户提供的问卷结果或摘要产出洞察与可执行结论。

## 何时使用

- 用户提到：**问卷**、调研、用户研究、问卷设计、问卷分析、留存归因调研、付费意愿调研、活动满意度调研
- 用户问：如何设计某类问卷、问卷题目怎么出、这份问卷结果怎么分析
- 用户提供了问卷结果（文件或粘贴），希望得到洞察报告

若用户要做舆情/留存/付费分析且数据来自 UGC（评价、论坛），使用 **game_report** / **game_retention** / **game_monetization**；若要做主动调研的问卷设计或问卷结果分析，使用本 skill。

## 参数提取

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **mode** | `survey_draft` 问卷设计 / `survey_analysis` 调研分析 | 从用户意图推断 |
| **survey_goal** | 调研目标（仅 draft）：留存归因/付费意愿/活动满意度/流失原因/NPS/自定义 | 从用户消息推断，无法推断时询问 |
| **product** | 产品/游戏名称（可选） | 从用户消息推断 |
| **data_source** | 问卷结果文件路径或粘贴内容（仅 analysis） | 用户提供 |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **output_path** | 输出目录 | `user/documents/调研报告/` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |

执行前 Echo 已解析参数。

## 执行流程

### Phase 1 — 理解与参数

1. 解析用户消息，填写参数表；推断 `mode`（设计 vs 分析）。
2. 若 mode=survey_draft：推断或询问 **survey_goal**；若 mode=survey_analysis：获取 **data_source**（路径或粘贴）。
3. Echo 已解析参数。

### Phase 2 — 按模式执行

1. **survey_draft**：阅读 **references/survey_framework.md**，按 survey_goal 选择题目类型与设计注意点；按 **references/template_survey_draft.md** 生成问卷结构、题目与选项建议。
2. **survey_analysis**：从 data_source 读取问卷结果（或用户粘贴的摘要）；识别主要问题与选项分布、开放题主题；按 **references/template_survey_analysis.md** 生成调研分析报告（洞察、可执行结论、局限）。

### Phase 3 — 输出

1. 若 mode=survey_draft：输出问卷草案（Markdown 或飞书）；若 mode=survey_analysis：输出调研分析报告（Markdown 或飞书）。
2. 按 `output_destination` 与 `report_format` 写文件或调用飞书工具。

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| 问卷设计、问卷结果分析、用户调研 | **customer_engagement**（本 skill） |
| 舆情/留存/付费（UGC 数据） | **game_report** / **game_retention** / **game_monetization** |

## 参考文件

- 调研目标与题目设计：[references/survey_framework.md](references/survey_framework.md)
- 问卷草案模板：[references/template_survey_draft.md](references/template_survey_draft.md)
- 调研分析报告模板：[references/template_survey_analysis.md](references/template_survey_analysis.md)
