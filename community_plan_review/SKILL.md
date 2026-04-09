---
name: community_plan_review
description: "当需要制定产品/游戏的社区建设方案或对社区运营做复盘时使用本 skill。支持多阶段策略、多平台差异化、内容矩阵与产能规划；复盘时支持播放/完播/互动、粉丝增长、口碑等维度分析。用户提及社区方案、社区复盘、内容运营、多平台运营、公测/上线社区时自动应用。"
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

# 社区方案与复盘 Skill

本 skill 是**社区方案与复盘层**。支持两种模式：**方案模式（plan）** 产出社区建设方案（阶段、内容矩阵、平台策略、产能杠杆）；**复盘模式（review）** 基于用户提供的文档或数据产出复盘报告（内容表现、用户增长、口碑）。产品名、平台、阶段、指标均参数化或由 references 配置，不写死具体案例，横向延展性高。

## 何时使用

- 用户提到：**社区方案**、**社区复盘**、内容运营、多平台运营、公测/上线社区、内容矩阵、产能规划
- 用户问：如何做社区建设方案、如何做社区运营复盘、多平台内容怎么分配
- 用户提供飞书/本地文档或粘贴的社区相关数据，希望按模板产出方案或复盘报告

区分「做方案」与「做复盘」两种模式；若未明确则从用户意图或 `mode` 参数推断。

## 何时不使用

- 用户需要的是**玩家评价 / 口碑 / 舆情分析**（如"分析这款游戏的玩家反馈"、"生成舆情报告"）→ 使用 **game_report**（`report_type=sentiment`），本 skill 不介入
- 输入数据来自 game_crawl（Reddit 帖子、TapTap 评价、YouTube 视频）且目标是分析**玩家情感与游戏体验** → 使用 **game_report**
- 本 skill 的"复盘模式"仅针对**内容运营表现**（KOL 产出、平台发布互动数据、粉丝增长），不覆盖玩家游戏体验分析

## 参数提取

从用户消息中提取以下参数。未提及的参数使用默认值。**执行前先 Echo 所有已解析参数。**

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **product** | 产品/游戏名称 | 从用户消息或提供的文档中解析，无法推断时询问 |
| **mode** | `plan` 方案 / `review` 复盘 | 从用户意图推断；若提供复盘数据/文档多为 `review` |
| **platforms** | 覆盖平台列表（如 B站、抖音、快手） | 从文档/配置读取或用户指定 |
| **phase_dates** | 方案各阶段时间（仅 plan） | 用户指定或待补充 |
| **review_window** | 复盘时间范围（仅 review） | 用户指定或从文档解析 |
| **data_source** | 用户提供的文档链接、本地路径、粘贴内容 | 无则标注待补充 |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **report_language** | 报告语言 | 与用户提问语言一致 |
| **output_path** | 输出目录 | `user/documents/社区报告/` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |

若 `product` 无法推断且用户未提供文档可解析，询问：「请说明产品/游戏名，或提供包含产品信息的文档。」

## 执行流程

### Phase 1 — 理解与参数

1. 解析用户消息，填写参数表；推断 `mode`（做方案 vs 做复盘）。
2. 若用户提供文档（飞书链接、本地路径、粘贴内容）：解析文档，抽取产品名、阶段、平台、指标、表格/结论，作为后续填槽依据。
3. Echo 已解析参数。

### Phase 2 — 按模式加载框架与模板

- **mode=plan**：读取 [references/framework_community_plan.md](references/framework_community_plan.md) 与 [references/template_community_plan.md](references/template_community_plan.md)，按模板生成社区建设方案。
- **mode=review**：读取 [references/framework_review.md](references/framework_review.md) 与 [references/template_review.md](references/template_review.md)，按模板生成复盘报告。

若用户已提供文档，将解析出的结构化信息填入模板对应节；无法获取的项注明「待补充」或「数据不足」。

### Phase 3 — 报告生成与输出

1. 按所选模板的 section 顺序逐节生成正文。
2. **report_format=markdown**：按 `output_destination` 写文件（文件名示例：`{YYYY-MM-DD}_{产品名}_社区方案.md` 或 `_社区复盘报告.md`）或仅在对话中输出；写入 `output_path`。
3. **report_format=feishu**：调用 **feishu_create_doc** 工具（传入 title、content、folder_token）；工具返回后打印飞书文档 URL 与简短确认。

## 可扩展性

- **新产品**：仅通过参数 `product` 与（可选）配置中的阶段/平台/OKR 区分，不把产品名写死在 references 中。
- **新平台**：在 framework_community_plan 的「平台策略指引」表中追加一行（平台 → 内容侧重、核心指标）；复盘框架中指标按平台拆分处同步补充。
- **新内容类型 / 新阶段**：在 framework_community_plan 中以列表或表格维护，新增即追加一项，不改主流程。
- **新指标**：在 framework_review 的指标分类下追加，template_review 对应 section 引用「见 framework_review 第 X 类」。

## 与其他 skill 的协同

| 场景 | 使用方式 |
|------|----------|
| 需品类视角 | 与 **game_designer** 联合使用时，在方案/复盘中注入品类下的内容与社区预期（读 game_designer 对应品类文档后补充「品类设计视角」小节）。 |
| 数据来自爬取 | 复盘时若用户需要接入 game_crawl 数据，可先委托 **game_crawl** 收集，再按本 skill 的 template_review 生成复盘；本 skill 默认以「用户提供文档/数据」为输入，不强制依赖 game_crawl。 |

## 参考文件

- 社区方案框架（阶段、内容矩阵、排期、产能、平台、攻略导流、流程清单、KOC/PUGC、重点物料等）：[references/framework_community_plan.md](references/framework_community_plan.md)
- 社区方案报告模板：[references/template_community_plan.md](references/template_community_plan.md)
- 复盘分析框架（指标分类、OKR 对照、分析维度、有效 vs 需调整、复盘洞察类型）：[references/framework_review.md](references/framework_review.md)
- 复盘报告模板：[references/template_review.md](references/template_review.md)
