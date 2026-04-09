---
name: official_persona
description: "当用户需要研究某款游戏的官方人设、官方口吻、官方文案风格时使用本skill。通过聚合 game_crawl 已收集的官方渠道内容（官网公告与更新日志、Reddit/TapTap 官方账号或 flair 帖子），经 LLM 分析产出「官方人设」研究报告（语气、用词、称呼、典型句式、拟人化设定等），供运营/文案对齐官方口吻使用。本 skill 不直接爬取数据，数据缺失或过期时委托 game_crawl 收集。"
metadata:
  {
    "copaw": {
      "emoji": "📝",
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

# Official Persona Skill（官方人设研究）

本 skill 从游戏**官方发布内容**中聚合文本，经 LLM 分析产出该游戏的「官方人设」研究报告，用于指导运营/文案与官方口吻对齐。数据来自 `game_crawl` 的持久化 merged 存储，本 skill 仅做筛选、聚合与分析。

## 何时使用

- 用户说：研究/分析某游戏的**官方人设**、**官方口吻**、**官方文案风格**、**官方怎么说话**
- 用户希望得到一份可复用的**人设说明**或**话术参考**，用于写公告、回复玩家等

## 参数提取

从用户消息中提取以下参数。未提及的参数使用默认值。**执行前先 Echo 所有已解析参数。**

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **game** | 游戏名称（中文或英文均可） | 从用户消息推断，无法推断时询问用户 |
| **platforms** | 参与聚合的平台（子集或「全部」） | 该游戏在 game_registry 中已配置的、能提供官方内容的平台 |
| **date_range** | 官方内容时间范围 | 近 6 个月（人设研究需要一定样本量） |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **output_path** | 输出目录路径 | `user/documents/游戏分析报告/` |
| **output_destination** | 报告输出位置：`file` 仅写文件，`chat` 仅在对话中输出完整报告 md | `file` |

## 官方内容定义

与 `game_registry.json` 一致，本 skill 只聚合以下「官方」内容：

| 平台 | 数据类型 | 官方判定方式 |
|------|----------|--------------|
| official_site | announcements, changelogs | 全部视为官方 |
| reddit | forum_posts | 仅保留 `post.flair` 属于该游戏 `platforms.reddit.official_flairs` 的帖子 |
| taptap | forum_posts | 仅保留 `post.author` 属于该游戏 `platforms.taptap.official_accounts` 的帖子 |

**merged 路径说明：** 数据根目录固定为项目根目录下的 `data/game_data`。合并数据路径为 `merged/<平台>/<game_key>/<data_type>/data.json`，其中 `game_key` 为注册表（**read_game_registry** 返回）中 `games` 下的游戏键名（如 heartopia、afk_journey）。

## 执行流程：4 个阶段

### Phase 1 — 理解

1. 解析用户消息，填写参数表。
2. 推断 `game`（不明确时询问）：
   > "你想研究哪款游戏的官方人设？"
3. 调用 **read_game_registry**，根据 `game` 匹配游戏键名（`game_key`）及各平台配置；若游戏未注册，先委托 **game_crawl** 执行 Phase 1 发现并注册，再继续。
4. 确定参与聚合的平台：若 `platforms` 为「全部」，取该游戏已配置的 `official_site`、`reddit`、`taptap`（仅包含能提供官方内容的平台）；若用户指定子集，则只使用指定平台。
5. 确定需检查的 (platform, data_type)：
   - official_site：announcements、changelogs
   - reddit：forum_posts
   - taptap：forum_posts
6. Echo 所有已解析参数（game、game_key、platforms、date_range、report_format、output_path、output_destination）。

### Phase 2 — 数据就绪检查

**数据根目录：** 与 game_crawl 一致，固定为项目根目录下的 `data/game_data`。

对 Phase 1 确定的每个 (platform, data_type) 组合进行检查（仅检查该游戏已配置的平台）：

- 调用 `read_game_data(platform, game_key, data_type)`（或等价读取 merged 文件）；若返回空或文件不存在，标记为「需爬取」。
- 调用 `check_game_data_freshness(platform, game_key, data_type, hours=24)`；若 `fresh` 为 false，标记为「需爬取」。

**若有任何组合被标记为需爬取：** 委托 **game_crawl** skill，传入：
- `game` = 当前游戏名/键
- `data_types` = 本次需要的 data_type 列表（announcements、changelogs、forum_posts）
- `platforms` = 涉及的平台列表（或 `auto`）

等待 game_crawl 完成后继续。

若某平台未配置（如无 official_site），跳过该平台，在最终报告中对应章节注明「暂无该渠道数据」。

### Phase 3 — 聚合官方内容

1. **读取 merged 数据**  
   对每个 (platform, data_type) 使用 `read_game_data(platform, game_key, data_type)` 读取合并数据。

2. **过滤为「仅官方」**
   - **official_site**：announcements、changelogs 全量保留；按 `date_range` 过滤（announcements 用 `published_at`，changelogs 用 `release_date`）。
   - **reddit**：从 `game_registry.games[game_key].platforms.reddit.official_flairs` 读取 flair 列表；只保留 `post.flair` 在该列表中的帖子；再按 `date_range` 过滤 `created_at`。
   - **taptap**：从 `game_registry.games[game_key].platforms.taptap.official_accounts` 读取官方账号列表；只保留 `post.author` 在该列表中的帖子；再按 `date_range` 过滤 `created_at`。

3. **构建官方语料**  
   将上述过滤后的条目整理为「官方语料」：每条包含来源（平台、数据类型）、标题、正文、日期等，便于 Phase 4 分析。若总文本过长，可对长正文截断或按条采样，在模板中说明「分析基于所提供语料，已做截断/采样」。

### Phase 4 — 分析与输出

1. **加载人设模板**  
   读取 `references/template_persona.md`，按其中章节与写作要求构造 LLM 提示。

2. **生成人设报告**  
   将 Phase 3 的官方语料与模板要求一并提交给 LLM，生成结构化人设报告。分析须严格基于提供的语料，不得臆造；若某渠道无数据，在对应章节注明「暂无该渠道数据」。

3. **引用与来源**  
   报告中可引用若干条原文并标注来源（平台、日期）；引用格式可采用数字标注 `[1]`、`[2]` 等，并在报告末尾列出「引用来源」清单（可参考 game_report 的 `citation_instructions.md` 简化版）。

4. **输出**
   - **report_format=markdown 且 output_destination=file**：  
     文件名格式 `{YYYY-MM-DD}_{游戏名}_官方人设研究.md`，写入 `output_path`。对话中打印完整文件路径、报告摘要（3 句话），并附带 Markdown 链接：`[在应用中打开报告](/user-docs?file=<relative_path>)`，其中 `<relative_path>` 为相对于 `user` 目录的路径。
   - **output_destination=chat**：  
     不写文件，在回复中直接输出完整报告正文（完整 Markdown）。
   - **report_format=feishu**：  
     在内存中组合完整报告内容，调用 **feishu_create_doc** 工具：title = `{游戏名} 官方人设研究 — {YYYY-MM-DD}`，content = 完整报告 Markdown 内容，folder_token = FEISHU_FOLDER_TOKEN（若已配置）；工具返回后打印飞书文档 URL 与简短确认。

## 失败处理

| 情况 | 处理 |
|------|------|
| 游戏未在 game_registry 注册 | 委托 game_crawl Phase 1 发现并注册后继续 |
| 某平台数据缺失且 game_crawl 失败 | 报告中该渠道章节注明「数据不足（爬取失败）」，继续生成其他部分 |
| 所有官方渠道均无数据 | 告知用户，建议先运行 game_crawl 收集相关 data_types 与平台 |
| 官方过滤后无任何帖子（如 reddit 无 official_flairs 帖子） | 在报告中说明该平台「暂无符合条件的官方帖子」，其他平台照常分析 |

## 依赖与工具

- **注册表**：通过 **read_game_registry** / **write_game_registry** 读写，结构见 game_crawl SKILL.md。
- **game_data 工具**：`read_game_data`、`check_game_data_freshness`、`get_data_root_path`、`read_game_registry`、`write_game_registry`。
- **委托**：通过 run_skill 或等价方式调用 **game_crawl**（数据就绪）；report_format=feishu 时调用 **feishu_create_doc** 工具。

## Token 节省规则

- 只读取本 skill 所需的 (platform, data_type)，不加载多余数据。
- 聚合语料时若条数或总字数过多，可对长正文截断、或按时间/热度采样，在模板中说明即可。
- 仅在 Phase 4 写最终报告文件（output_destination=file 时）；不保存中间语料文件。
