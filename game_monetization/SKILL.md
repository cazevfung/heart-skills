---
name: game_monetization
description: "当用户需要游戏付费/变现深度分析时使用本 skill。可基于 game_crawl 的玩家评价与论坛数据从 UGC 中归纳付费相关洞察，也可基于用户提供的付费指标数据（CSV/JSON/Excel）做指标级分析。支持按游戏品类、用户指定的分析焦点（首充、付费结构、健康度、品类对比、趋势等）深度分析。无真实付费指标时在报告中明确说明为「基于玩家反馈的付费洞察」。可与 game_report、game_retention 并列使用。"
metadata:
  {
    "copaw": {
      "emoji": "💰",
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

# 游戏付费数据专家 Skill

本 skill 是游戏分析的**付费专项层**。从 `game_crawl` 的持久化数据（评价、论坛帖子、应用信息）和/或用户提供的付费指标文件中读取内容，按付费分析框架与用户指令进行深度分析，输出结构化付费分析报告。本 skill 不直接爬取数据；使用 merged 数据时若缺失或过期则委托 **game_crawl** 收集。

## 何时使用

- 用户提到：**付费分析**、变现、ARPU、ARPPU、**付费率**、LTV、首充、商业化分析、付费数据、付费结构、健康度、氪金、抽卡定价
- 用户问：某游戏的付费设计如何、付费率/ARPU 趋势、首充表现、与品类对比
- 用户提供了付费相关表格/文件，要求按品类或自定义维度分析

若用户仅要舆情或版本分析，使用 **game_report**；若仅要留存/流失分析，使用 **game_retention**。若用户既要综合报告又单独要付费专项，可先完成 game_report，再用本 skill 产出付费专项报告。

## 参数提取

从用户消息中提取以下参数。未提及的参数使用默认值。**执行前 Echo 所有已解析参数。**

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **game** | 游戏名称（中文或英文，可多款逗号分隔） | 从用户消息推断，无法推断时询问 |
| **genre** | 品类（用于分析视角与框架选择，见 monetization_framework.md） | 从用户指令或用户数据推断，可选 |
| **data_source** | `crawl_merged` 仅用 merged UGC / `user_file` 仅用用户提供文件 / `both` | 从用户意图推断 |
| **user_data_path** | 用户提供的付费数据文件路径（当 data_source 含 user_file 时） | 用户消息或后续询问 |
| **analysis_focus** | 分析焦点：首充分析 / 付费结构 / 健康度评估 / 品类对比 / 趋势 / 自定义 | 从用户指令解析，可多选 |
| **date_range** | 评价/帖子或指标的时间范围 | 近 3 个月 |
| **platform** | 数据来源平台（仅 merged 时有效） | `all` |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **report_language** | 报告语言 | 与用户提问语言一致 |
| **output_path** | 输出目录（仅 report_format=markdown 且输出到文件时） | `user/documents/游戏分析报告/` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |
| **use_existing_data_only** | 用户明确「只用现有数据」时不触发爬取 | `no` |

## 数据来源与就绪检查

**数据根目录：** 与 game_report 一致，固定为项目根目录下的 `data/game_data`。

**Merged 所需 data_types：** `app_info`、`reviews`、`forum_posts`。

**就绪规则（仅当 data_source 含 crawl_merged 时）：** 检查 `merged/<平台>/<game_id>/<data_type>/data.json` 是否存在且 `last_updated` 在 24 小时内。若有缺失或过期且用户未设置 `use_existing_data_only`，**委托 game_crawl** 传入对应 `game`、`data_types`（`app_info`、`reviews`、`forum_posts`）、`platforms`（建议 `auto`），待完成后再继续。

**用户提供数据：** 当 data_source 含 `user_file` 时，通过 **file_reader** 或用户给定路径读取；校验是否含可识别列（如 日期、付费率、ARPU、ARPPU、LTV、首充率、品类 等，见 references/monetization_framework.md），必要时列出首行与列名并 Echo 确认。

## 执行流程：4 个阶段

### Phase 1 — 理解与参数

1. 解析用户消息，填写参数表；推断 `game`（多款时逗号分隔）、`genre`、`data_source`、`analysis_focus`。
2. 若需用户提供文件而用户未提供路径或内容，询问后再继续。
3. Echo 所有已解析参数，确认使用「付费专项分析」。

### Phase 2 — 数据就绪

1. **若 data_source 含 crawl_merged**：按「数据来源与就绪检查」对所需 data_types、各平台做就绪检查；若有需爬取项，委托 **game_crawl**，完成后继续。
2. **若 data_source 含 user_file**：读取用户指定路径或用户粘贴/上传的文件；识别列名与样本行，确认可解析（见 monetization_framework 中的用户数据 schema 建议）；若无法解析则告知用户并列出已识别列。

### Phase 3 — 深度分析

1. **必读** 本 skill 的 **references/monetization_framework.md**（术语、品类表、付费模型、健康度三问、UGC 信号归类、用户数据 schema 建议）。
2. **若有用户提供指标数据**：按 `analysis_focus` 做指标计算、趋势与对比（按品类、时间、渠道等切片）；结合 `genre` 选用品类视角解读。
3. **若使用 merged UGC**：从 reviews、forum_posts 中抽取付费/氪金/定价/抽卡/贬值等相关表述，按归因层（技术/运营/商业化/策划）与品类视角归纳；在报告中注明「本报告基于玩家评价与讨论归纳付费相关洞察，非来自真实付费埋点数据」。
4. **引用**：若报告中引用具体评价或帖子，必须遵循 game_report 的 **references/citation_instructions.md**（正文用 [N]，报告末尾输出「引用来源」章节）。
5. 按 **references/template_monetization.md** 的 section 顺序生成报告正文。

### Phase 4 — 输出

1. **report_format=markdown**：按 `output_destination` 执行。
   - **output_destination=file**（默认）：文件名 `{YYYY-MM-DD}_{游戏名}_付费分析报告.md`，写入 `output_path`；对话中打印完整文件路径 + 报告摘要（2～3 句），并附带 `[在应用中打开报告](/user-docs?file=<relative_path>)`，其中 `<relative_path>` 为相对于 `user` 的路径。
   - **output_destination=chat**：不写本地文件，在回复中直接输出完整报告正文（完整 Markdown）。
2. **report_format=feishu**：在内存中组合完整报告内容，调用 **feishu_create_doc** 工具：title = `{游戏名} 付费分析报告 — {YYYY-MM-DD}`，content = 完整报告 Markdown 内容，folder_token = FEISHU_FOLDER_TOKEN（若已配置）；工具返回后打印飞书文档 URL 与简短确认。

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| 只做付费/变现/商业化深度分析 | **game_monetization**（本 skill） |
| 舆情、版本、综合分析 | **game_report** |
| 留存、流失、留存建议 | **game_retention** |
| 仅收集数据、不写报告 | **game_crawl** |
| 综合报告 + 付费专项 | 先 **game_report**（或 game_crawl），再用本 skill 基于同一数据产出付费报告 |

## 失败处理

- 若仅用 merged 且所有 data_type 均不可用且 game_crawl 也失败：告知用户，建议先运行 game_crawl 或提供付费数据文件。
- 若仅用 user_file 且文件无法解析：列出已识别列，请用户确认列名或提供符合 schema 建议的数据。
- 游戏未在注册表中：委托 game_crawl 时可触发自动发现并注册；若 game_crawl 未能发现，在报告中说明并建议用户确认游戏名或通过 write_game_registry / game_crawl 手动配置。

## Token 节省规则

- 只加载本报告所需 data_types（app_info、reviews、forum_posts），不读取 changelogs、videos、announcements 等无关类型。
- 仅在 Phase 4 写最终报告文件（当 output_destination=file）；不保存中间分析文件。
- 委托 game_crawl 时只传入 `app_info`、`reviews`、`forum_posts`，避免全量 data_types。

## 参考文件

- 付费分析框架（术语、品类、付费模型、健康度、UGC 信号、用户数据 schema）：[references/monetization_framework.md](references/monetization_framework.md)
- 付费分析报告模板：[references/template_monetization.md](references/template_monetization.md)
- 引用格式（与 game_report 一致）：[game_report/references/citation_instructions.md](../game_report/references/citation_instructions.md)
