---
name: attribution_ops
description: "当需要对负面问题或复盘场景运行「运营归因四分法」（策划/运营/商业化/技术）时使用本 skill。输入为问题描述与可选的已有报告（舆情/留存/付费），输出归因表（责任方、建议解法类型、周期）。不替代 game_report，而是消费其输出做归因拆解。"
metadata:
  {
    "copaw": {
      "emoji": "🎯",
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

# 运营归因专家 Skill

本 skill 对「问题描述 + 可选已有报告」运行**归因四分法**，输出归因表与建议（责任方、解法类型、周期）。不直接爬取数据；可读取用户提供的报告摘要、报告文件路径或 merged 数据摘要。

## 何时使用

- 用户提到：**归因**、责任归属、问题是谁的锅、策划/运营/商业化/技术谁负责、复盘归因
- 用户问：某负面问题属于哪一层、该怎么分责、建议谁来解决、周期多长
- 用户提供了舆情/留存/付费报告或摘要，希望得到结构化归因表

若用户仅要舆情或留存/付费分析，使用 **game_report** / **game_retention** / **game_monetization**；若在已有报告基础上做归因拆解，使用本 skill。

## 参数提取

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **problem_description** | 要归因的问题描述（或指向已有报告的说明） | 从用户消息提取，缺失时询问 |
| **report_source** | 已有报告来源：`none` / `path` / `paste` / `game_report_sentiment` 等 | `none` |
| **report_path_or_content** | 报告文件路径或粘贴内容（当 report_source 非 none 时） | 用户提供 |
| **game** | 游戏名称（可选，用于上下文） | 从用户消息推断 |
| **output_format** | `markdown` / `feishu` | `markdown` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |
| **output_path** | 输出目录（输出到文件时） | `user/documents/游戏分析报告/` |

执行前 Echo 已解析参数。

## 归因框架来源

本 skill 的归因逻辑与 **game_report** 的 [references/ops_knowledge.md](../game_report/references/ops_knowledge.md) 一致：

- **技术层**：Bug、崩溃、性能、匹配质量等 → 责任方技术组，解法周期短（热修/优化）。
- **商业化层**：定价、付费强迫感、抽卡、资产贬值等 → 责任方商业化组，解法周期中。
- **运营层**：活动设计、沟通方式、版本节奏、预期管理等 → 责任方运营组，解法周期短到中。
- **策划层**：玩法设计、平衡性、内容深度、成长曲线等 → 责任方策划组，解法周期长。

执行时**必读** game_report 的 `references/ops_knowledge.md` 中「问题归因决策树」与四层定义；本 skill 的 **references/attribution_framework.md** 可做精简速查，避免重复维护时以 ops_knowledge 为准。

## 执行流程

### Phase 1 — 理解与输入

1. 解析用户消息，填写参数表；明确要归因的**问题列表**（可从用户描述或已有报告中抽取）。
2. 若用户提供了报告路径或粘贴内容，通过 **file_reader** 或直接读取获取摘要；抽取「核心负面问题」列表（建议 Top 5–10）。
3. Echo 已解析参数与待归因问题列表。

### Phase 2 — 归因分析

1. 阅读 **references/attribution_framework.md**（及必要时 [ops_knowledge.md](../game_report/references/ops_knowledge.md)），对每个问题运行归因决策树。
2. 为每个问题标注：归因层（可多层）、责任方、建议解法类型、建议处理周期（立即/本版本内/下版本前/长期）。
3. 若问题涉及多层面，分别列出并注明主次。

### Phase 3 — 输出归因报告

1. 按 **references/template_attribution.md** 生成归因报告（归因表 + 建议汇总）。
2. 若 `output_format=markdown`：按 `output_destination` 写文件或仅在对话中输出；若 `output_format=feishu`：调用 **feishu_create_doc** 工具，返回后打印飞书文档 URL。

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| 对已有问题/报告做归因拆解、分责、解法周期 | **attribution_ops**（本 skill） |
| 产出舆情/留存/付费报告 | **game_report** / **game_retention** / **game_monetization** |
| 归因框架定义 | 以 **game_report/references/ops_knowledge.md** 为准 |

## 参考文件

- 归因速查（可选）：[references/attribution_framework.md](references/attribution_framework.md)
- 归因报告模板：[references/template_attribution.md](references/template_attribution.md)
- 完整归因决策树：[game_report/references/ops_knowledge.md](../game_report/references/ops_knowledge.md)
