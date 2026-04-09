---
name: game_marketing
description: "当用户需要地区市场营销方案（含竞品、STP、用户画像、卖点、分地区方案模板及联动规划）时使用本 skill；可调用 game_designer、market_landscape、new_game_performance；联动相关认知见 references/collaboration_framework.md。当用户需要获客/买量分析、素材与真实体验一致性、渠道或首日流失洞察时也使用本 skill；基于 game_crawl 的 UGC 归纳买量素材与体验是否一致、首日流失相关表述；无 CPI/渠道数据时在报告中注明「基于玩家反馈的获客洞察」。"
metadata:
  {
    "copaw": {
      "emoji": "📣",
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

# 游戏营销专家 Skill

本 skill 覆盖两类场景：**地区市场营销方案**（主场景）与**获客/买量分析**（子场景）。地区营销方案时，串联竞品列表→了解竞品→STP 用户画像与卖点→按模板产出分地区方案，并按需使用 **market_landscape**、**game_designer**、**new_game_performance**。获客分析时，从 `game_crawl` 的持久化数据中按获客框架归纳素材与体验一致性、首日流失，输出获客报告。本 skill 不直接爬取数据；数据缺失或过期时委托 **game_crawl** 收集。

## 何时使用

**地区营销方案（task_focus = marketing_plan）：**
- 用户提到：**营销方案**、上市方案、地区发行、**STP**、**用户画像**、**游戏卖点**、**竞品**、**联动**（IP 联动/品牌联名/跨界合作），以及某地区/多地区（如日本、东南亚）
- 用户问：某游戏在某某地区怎么推、怎么做发行方案、竞品是谁然后怎么定卖点、适合做什么联动

**获客分析（task_focus = acquisition）：**
- 用户提到：**获客**、买量、素材、**首日流失**、CPI、渠道、下载后删、广告与实机不符
- 用户问：某游戏买量素材和体验是否一致、为什么装完就删、获客健康度如何
- 需要产出**获客专项报告**（与舆情/留存/付费报告区分）

若用户仅要舆情或版本分析，使用 **game_report**；若仅要留存或付费分析，使用 **game_retention** / **game_monetization**。若仅要竞品对比或市场格局，使用 **market_landscape**。

## 参数提取

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **game** | 游戏名称（中文或英文）；做方案时即本品 | 从用户消息推断，无法推断时询问 |
| **task_focus** | `marketing_plan`（地区营销方案）/ `acquisition`（获客分析） | 从用户消息推断 |
| **regions** | 需出方案的地区列表（如 中国大陆、日本、东南亚） | 从用户消息推断或询问（仅 marketing_plan） |
| **focus_product** | 本品（做方案的游戏） | 同 game |
| **include_competitors** | 是否先列竞品并了解竞品（会用到 market_landscape） | 做方案时推断为 true |
| **platform** | 数据来源平台（单平台或 `all`） | `all` |
| **date_range** | 评价/帖子时间范围 | 近 3 个月 |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **report_language** | 报告语言 | 与用户提问语言一致 |
| **output_path** | 输出目录 | `user/documents/游戏分析报告/` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |
| **use_existing_data_only** | 用户明确「只用现有数据」时不触发爬取 | `no` |

执行前 Echo 已解析参数。

## 数据来源与就绪检查

**数据根目录：** 与 game_report 一致，固定为项目根目录下的 `data/game_data`。

**获客分析所需 data_types：** `app_info`、`reviews`、`forum_posts`；可选 `videos`。

**地区营销方案所需数据：** 本品 + 竞品列表中各款的 `app_info`、`reviews`、`forum_posts`（与 market_landscape 一致）；缺数据时委托 **game_crawl** 对缺失项收集。

**就绪规则：** 检查 `merged/<平台>/<game_id>/<data_type>/data.json` 是否存在且 `last_updated` 在 24 小时内。若有缺失或过期且未设置 `use_existing_data_only`，委托 **game_crawl** 传入对应 `game`/`games`、`data_types`、`platforms`（建议 `auto`），待完成后再继续。

---

## 执行流程 A：地区市场营销方案（task_focus = marketing_plan）

### Phase 1 — 理解与参数

1. 解析用户消息，填写参数表；确定本品（game）、regions、是否要竞品（include_competitors）。
2. Echo 参数；确认使用「地区市场营销方案」。

### Phase 2 — 竞品列表与了解竞品

1. **使用 market_landscape**：若用户未给竞品名单，先按本品品类/赛道推断竞品并列出；再按 **market_landscape** 的流程与数据（merged 多款 app_info、reviews、forum_posts）产出「竞品列表 + 多维度对比 + 市场格局小结」。若用户已给竞品名单，直接以该名单执行 market_landscape 的分析逻辑。
2. **数据就绪**：对本品及竞品按 market_landscape 的数据就绪规则检查；若有缺失或过期且未设置 use_existing_data_only，**委托 game_crawl** 对缺失项收集，完成后继续。

### Phase 3 — STP：用户画像与卖点

1. **用户画像**：基于竞品与市场格局，用 STP（细分→目标→定位）归纳本品核心玩家群体；输出核心用户占比、兴趣标签、触媒习惯。需要时读取 **game_designer** 的 references/_index.md 并仅加载相关品类文档，注入品类视角。
2. **卖点**：基于 STP 与竞品对比，归纳应对市场竞争的差异化点，提炼 3–5 条游戏卖点；可再参考 game_designer 的品类动机与设计基线。
3. 若涉及「刚上线」或首周表现基准，可引用 **new_game_performance** 的结论或指标口径。

阅读 **references/stp_marketing_framework.md** 以统一用户画像与卖点的输出结构。

### Phase 4 — 分地区营销方案

1. 对 **regions** 中每个地区，按 **references/template_regional_marketing.md** 填写。
2. 各区块填写要求：
   - 【目标】：首月下载量/收入目标/品类排名目标（可写区间或「待定」）。
   - 【用户画像】：与 Phase 3 一致，可按地区微调（当地兴趣标签、触媒习惯）。
   - 【渠道策略】：主力渠道（TikTok/YouTube/本地渠道等）、预算占比、内容形式（短视频/直播/图文等）；可参考 **references/marketing_tactics_library.md**（预告片、微电影、跨界、话题、前瞻直播、KOL/明星等）。
   - 【本地化重点】：文化适配、支付方式、KOL 合作层级与数量。
   - 【里程碑】：D-30（预注册）、D-Day（冲榜/买量峰值）、D+30（首版本活动/留存优化）等。
   - 【联动规划】：按 **references/collaboration_framework.md**（联动认知体系）填写建议联动类型、优先方向与档期、风险或前提；**须包含用户群体匹配**（与本品该地区用户画像的匹配度或匹配理由）；与用户画像及渠道策略一致。

### Phase 5 — 输出

1. 按 report_format（markdown/feishu）、output_destination（file/chat）写文件或创建飞书文档。
2. 若 markdown + file：文件名建议 `{YYYY-MM-DD}_{游戏名}_地区营销方案.md`，写入 output_path；对话中打印完整文件路径与报告摘要，并附带 Markdown 链接 `[在应用中打开报告](/user-docs?file=<relative_path>)`。
3. 若 report_format=feishu：调用 **feishu_create_doc** 工具，返回后打印飞书文档 URL 与简短确认。

---

## 执行流程 B：获客分析（task_focus = acquisition）

### Phase 1 — 理解与参数

1. 解析用户消息，填写参数表；推断 game（不明确则询问）。
2. Echo 参数；确认使用「获客专项报告」。

### Phase 2 — 数据就绪

1. 按「数据来源与就绪检查」对本品所需 data_types 做就绪检查。
2. 若有需爬取项，委托 **game_crawl**，完成后继续。

### Phase 3 — 获客分析

1. 从合并存储读取各平台 `reviews`、`forum_posts`、`app_info`（及可选的 `videos`）。
2. 阅读 **references/acquisition_framework.md**，按其中维度对 UGC 做归类与归纳：素材与体验一致性、首日/安装后短期流失相关表述、渠道或来源相关提及（若有）。
3. **重要**：若无 CPI/渠道埋点数据，在报告中明确注明：「本报告基于玩家评价与讨论归纳获客相关洞察，非来自真实 CPI 或渠道数据。」

### Phase 4 — 报告生成与输出

1. 按 **references/template_acquisition.md** 生成获客分析报告正文。
2. 若 report_format=markdown：按 output_destination 写文件或仅在对话中输出；若 report_format=feishu：调用 **feishu_create_doc** 工具，返回后打印飞书文档 URL 与简短确认。

---

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| 地区营销方案（竞品→STP→分地区方案） | **game_marketing**（本 skill），其中竞品/格局用 **market_landscape**，品类设计视角用 **game_designer**，新游表现基准用 **new_game_performance** |
| 获客/买量/素材-体验一致性/首日流失分析 | **game_marketing**（本 skill） |
| 仅竞品对比、市场格局、本品定位（不产出营销方案） | **market_landscape** |
| 舆情、版本、综合分析 | **game_report** |
| 留存、流失、留存建议 | **game_retention** |
| 仅收集数据、不写报告 | **game_crawl** |

---

## 参考文件

**地区营销方案：**
- STP 与营销框架：[references/stp_marketing_framework.md](references/stp_marketing_framework.md)
- 地区营销方案模板：[references/template_regional_marketing.md](references/template_regional_marketing.md)
- 营销手段参考库：[references/marketing_tactics_library.md](references/marketing_tactics_library.md)
- 联动认知体系：[references/collaboration_framework.md](references/collaboration_framework.md)

**获客分析：**
- 获客分析框架：[references/acquisition_framework.md](references/acquisition_framework.md)
- 获客报告模板：[references/template_acquisition.md](references/template_acquisition.md)
