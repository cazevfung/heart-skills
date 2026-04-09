---
name: event_ops
description: "当用户需要活动方案（按类型给结构模板与节奏/风险提示）或活动复盘（用户提供活动数据/文档产出表现复盘）时使用本 skill。支持类型：限时冲刺、养成长线、裂变、消耗清库、限定皮肤、节日主题。与 community_plan_review 区分：本 skill 侧重游戏内/游戏外活动机制与节奏。"
metadata:
  {
    "copaw": {
      "emoji": "🎪",
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

# 活动运营专家 Skill

本 skill 支持两种模式：**方案模式（plan）** 产出活动方案（类型、结构、节奏、风险提示）；**复盘模式（review）** 基于用户提供的活动数据/文档产出活动复盘报告（目标、指标、参与率、负面反馈、建议）。

## 何时使用

- 用户提到：**活动方案**、活动设计、限时活动、养成活动、裂变活动、消耗清库、限定皮肤活动、节日活动、活动复盘、活动效果
- 用户问：如何设计某类活动、活动节奏怎么排、某活动复盘结论
- 用户提供了活动数据或文档，希望按模板产出复盘报告

若用户要做社区内容方案或社区复盘，使用 **community_plan_review**；若要做公告文案，使用 **game_announcement_copy**。

## 参数提取

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **mode** | `plan` 方案 / `review` 复盘 | 从用户意图推断 |
| **product** | 产品/游戏名称 | 从用户消息或文档解析，无法推断时询问 |
| **event_type** | 活动类型（仅 plan）：限时冲刺/养成长线/裂变/消耗清库/限定皮肤/节日主题 | 从用户意图推断，可多选或通用 |
| **data_source** | 用户提供的复盘文档链接、本地路径、粘贴内容（仅 review） | 用户提供 |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **report_language** | 报告语言 | 与用户提问语言一致 |
| **output_path** | 输出目录 | `user/documents/社区报告/` 或 `user/documents/活动报告/` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |

执行前 Echo 已解析参数。

## 执行流程

### Phase 1 — 理解与参数

1. 解析用户消息，填写参数表；推断 `mode`（做方案 vs 做复盘）。
2. 若 mode=review 且用户提供文档：解析文档，抽取活动名、目标、指标、时间、表格/结论，作为后续填槽依据。
3. Echo 已解析参数。

### Phase 2 — 按模式加载框架与模板

1. **plan**：阅读 **references/event_types_framework.md**，确定活动类型对应的机制、效果、常见副作用、节奏注意点；按 **references/template_event_plan.md** 生成活动方案。
2. **review**：从用户提供的数据/文档中抽取目标、实际指标、参与率、负面反馈等；按 **references/template_event_review.md** 生成复盘报告。

### Phase 3 — 生成与输出

1. 按所选模板生成完整正文。
2. 若 `report_format=markdown`：按 `output_destination` 写文件或仅在对话中输出；若 `report_format=feishu`：调用 **feishu_create_doc** 工具，返回后打印飞书文档 URL。

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| 活动方案、活动复盘、活动类型与节奏 | **event_ops**（本 skill） |
| 社区方案、社区复盘、内容矩阵、多平台 | **community_plan_review** |
| 活动公告文案 | **game_announcement_copy** |

## 参考文件

- 活动类型框架：[references/event_types_framework.md](references/event_types_framework.md)
- 活动方案模板：[references/template_event_plan.md](references/template_event_plan.md)
- 活动复盘模板：[references/template_event_review.md](references/template_event_review.md)
