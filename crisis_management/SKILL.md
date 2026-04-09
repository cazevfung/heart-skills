---
name: crisis_management
description: "当用户需要危机/舆情应对建议、对外话术原则或预案结构时使用本 skill。输入为舆情结论（或 game_report sentiment 摘要）/ 事件类型，输出应对策略要点、话术原则、可选预案结构。不替代真人决策，仅提供框架与话术参考。"
metadata:
  {
    "copaw": {
      "emoji": "🆘",
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

# 危机与舆情应对专家 Skill

本 skill 根据舆情结论（或 game_report sentiment 报告摘要）与事件类型，产出**危机应对建议文档**：应对策略要点、对外话术原则、预案结构。不替代真人决策，仅提供可操作的框架与话术参考。

## 何时使用

- 用户提到：**危机应对**、舆情应对、公关话术、对外回应、预案、危机公关、负面舆情怎么回应
- 用户问：某负面事件该怎么回应、话术怎么写、预案结构如何
- 用户提供了舆情报告或 sentiment 摘要，希望得到应对策略与话术

若用户仅要舆情分析（发生了什么），使用 **game_report**（report_type=sentiment）；若在已有舆情结论基础上要「怎么回应」，使用本 skill。

## 参数提取

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **event_summary** | 舆情/事件摘要（或指向已有报告的说明） | 从用户消息或报告提取，缺失时询问 |
| **event_type** | 事件类型（可选）：技术事故/商业化争议/运营沟通/策划内容/多因素 | 从摘要推断或用户指定 |
| **report_source** | 已有报告路径或粘贴内容（sentiment 报告等） | 用户提供 |
| **product** | 产品/游戏名称 | 从用户消息推断 |
| **output_format** | `markdown` / `feishu` | `markdown` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |
| **output_path** | 输出目录 | `user/documents/游戏分析报告/` 或 `user/documents/危机应对/` |

执行前 Echo 已解析参数。

## 执行流程

### Phase 1 — 理解与输入

1. 解析用户消息，填写参数表；获取**事件/舆情摘要**（用户描述或从报告路径/粘贴内容中抽取）。
2. 推断或确认 **event_type**（技术/商业化/运营/策划/多因素），便于选用对应话术原则。
3. Echo 已解析参数与事件摘要要点。

### Phase 2 — 应对分析

1. 阅读 **references/crisis_framework.md**（事件类型、响应节奏、话术原则、与归因层对应）。
2. 根据 event_summary 与 event_type，归纳：核心诉求、情绪焦点、责任归属（可参考 attribution_ops 四层）。
3. 产出策略要点（先回应什么、后做什么、谁出面、时间线）；话术原则（诚恳/不推责/具体补偿或改进承诺等）；预案结构（公告模板、FAQ、升级路径等）。

### Phase 3 — 输出应对文档

1. 按 **references/template_crisis.md** 生成危机应对建议文档。
2. 若 `output_format=markdown`：按 `output_destination` 写文件或仅在对话中输出；若 `output_format=feishu`：调用 **feishu_create_doc** 工具，返回后打印飞书文档 URL。

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| 危机应对策略、话术、预案 | **crisis_management**（本 skill） |
| 舆情分析（发生了什么） | **game_report**（report_type=sentiment） |
| 归因分责 | **attribution_ops** |

## 参考文件

- 危机类型与话术原则：[references/crisis_framework.md](references/crisis_framework.md)
- 应对文档模板：[references/template_crisis.md](references/template_crisis.md)
