---
name: new_game_performance
description: "当用户询问刚上线新游的表现、首日/首周数据、新游口碑分析时使用本 skill。可先通过 game_discovery 确定分析对象（若用户未指定具体游戏），再委托 game_crawl 保证数据就绪，最后按新游表现模板与上线期知识库生成报告。输出格式可选 file/chat/feishu。"
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

# New Game Performance Skill（新游表现研究专家）

本 skill 专门研究**刚上线新游**的表现：从上线节点、首周指标、早期口碑到风险与建议，产出结构化新游表现报告。不直接爬取数据，数据缺失或过期时委托 **game_crawl**；若用户未指定具体游戏且问「最近上线的几款」，可先调用 **game_discovery** 得到名单后再分析。

## 参数提取

从用户消息中提取以下参数。未提及的参数使用默认值。**执行前先 Echo 所有已解析参数。**

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **game** | 游戏名称（可多款，逗号分隔） | 从用户消息推断；若问「最近上线的」且未指名，见 Phase 1 |
| **launch_window_days** | 视为「刚上线」的天数（用于筛选评价/帖子时间范围） | `30` |
| **platform** | 数据来源平台（单个或 `all`） | `all` |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **report_language** | 报告语言 | 与用户提问语言一致 |
| **output_path** | 输出目录路径 | `user/documents/游戏分析报告/` |
| **output_destination** | `file` 仅写文件，`chat` 仅在对话中输出完整报告 | `file` |
| **use_existing_data_only** | 用户明确「只用现有数据」时不触发爬取 | `no` |

若无法推断出任何游戏且用户也未说「最近上线的几款」，**立即询问**：「你想分析哪款新游的表现？可以说游戏名，或说「最近上线的几款」由我列出后再选。」

## 所需数据类型

本报告所需 data_types（与 game_report 的 merged 结构一致）：

- **必需**：`app_info`、`reviews`、`forum_posts`
- **可选**：`videos`、`changelogs`、`announcements`（若该游戏已配置对应平台则检查并尽量使用，缺失不阻塞报告）

数据根目录与 game_report 一致：固定为项目根目录下的 `data/game_data`。

## 执行流程：4 个阶段

### Phase 1 — 理解与确定分析对象

1. 解析用户消息，填写参数表。
2. **推断 game**：
   - 若用户给出具体游戏名（一款或多款）→ 使用该名单，Echo 后进入 Phase 2。
   - 若用户说「最近上线的」「刚上线的几款」「新游表现」等且**未指定游戏名** → 先调用 **game_discovery** skill，获取近期已上线游戏列表；然后询问用户「请从下列游戏中选择要分析的（可回复编号或名称）」，或按用户事先偏好取前 1～3 款作为默认分析对象。Echo 最终确定的 game 列表后进入 Phase 2。
3. Echo 所有已解析参数（含 `launch_window_days`、`report_format`、`output_destination`）。

### Phase 2 — 数据就绪检查

**平台范围**：`platform = all` 时，调用 **read_game_registry**，从返回的注册表中读取该游戏所有已配置平台；否则仅检查指定平台。

**对每款 game、每个 (平台, data_type) 组合**：根据 game_crawl 平台注册表与本 skill 所需 data_types 取交集，检查：

```
<数据根目录>/merged/<平台>/<game_id>/<data_type>/data.json
```

判断规则：

- 文件存在且 `last_updated` 在 **24 小时内** → 就绪，直接使用。
- 文件不存在或 `last_updated` 超过 24 小时 → 标记为「需要爬取」。
- **可选 data_type**：若 read_game_registry 返回的注册表中该游戏未配置对应平台（如无 youtube），则跳过，不标记为需要爬取。
- 用户明确「使用现有数据」「不爬取」→ 不触发爬取，即使数据过期。

**若有任何 (game, 平台, data_type) 需要爬取**：委托 **game_crawl** skill，传入：

- `game` = 当前游戏（多款时逐款委托或按 game_crawl 支持的批量方式）
- `data_types` = 需要更新的 data_type 列表（建议传 `auto` 或至少包含 `app_info`, `reviews`, `forum_posts`）
- `platforms` = 涉及的平台列表（建议 `auto`）

等待 game_crawl 完成后继续。若某 game 或某 data_type 爬取失败，在最终报告中该 game 或对应 section 标注「数据不足」，继续生成其余内容。

**游戏未在注册表中**：委托 game_crawl 时 game_crawl 会执行自动发现并注册，本 skill 无需单独写注册表。

### Phase 3 — 分析与报告生成

#### Phase 3.0 — 上线期上下文（强制，在所有 section 生成前执行）

1. 读取本 skill 的 **references/launch_knowledge.md**，掌握「刚上线」界定、首周指标解读、早期差评归因与风险建议输出要求。
2. 若需与通用运营阶段对照，可参考 game_report 的 **references/ops_knowledge.md** 中买量冲刺期/版本发布期等描述。
3. 根据数据中的评价/帖子时间分布，推断「上线参考日」与当前处于上线后第几天，用于报告中的「分析时段」和趋势解读。

#### Phase 3.1 — 引用索引构建（强制，在生成正文前执行）

与 game_report 一致：

1. 阅读 game_report 的 **references/citation_instructions.md**，遵守引用格式。
2. 扫描已加载的 `reviews`、`forum_posts`、`app_info` 等，选出计划在报告中引用的条目。
3. 从 1 开始分配唯一编号，构建 citationMap（编号 → 条目元数据：标题/摘要、平台、日期、url）。
4. 撰写报告时，凡引用具体数据或引文必须在句末或引文末加上 [N]；报告末尾必须输出「引用来源」章节，仅列出正文中实际引用过的编号。

#### Phase 3.2 — 数据加载与报告正文

- **数据加载**：对每款 game，从 `merged/<平台>/<game_id>/` 下按所需 data_types 加载并合并（规则与 game_report Phase 3.1 一致：reviews 按 created_at、forum_posts 按 created_at 合并与过滤，app_info 取 info 等）。
- **时间过滤**：评价与帖子按 `launch_window_days` 过滤（仅保留上线参考日至今或最近 N 天内的数据）；若无明确上线日，则保留最近 `launch_window_days` 天的数据。
- **报告生成**：按 **references/template_new_game_performance.md** 的 section 顺序逐节生成；每个 blockquote 或典型引用必须附 [N]；风险与建议按 launch_knowledge 的归因层与时限要求书写。

多款游戏时：每款游戏单独生成一份报告（或在一份报告中分「游戏 A」「游戏 B」大节），按参数表中的 game 顺序输出。

### Phase 4 — 输出

**确定 game_id**：调用 **read_game_registry**，从返回的注册表中读取各游戏的平台配置（TapTap app_id、reddit subreddit 等），用于构建数据路径与报告中的平台标注。若某游戏尚未注册，由 Phase 2 的 game_crawl 先完成发现与注册。

**markdown 格式**：

- **output_destination = file**（默认）：
  - 文件名：`{YYYY-MM-DD}_{游戏名}_新游表现报告.md`
  - 写入 `output_path`
  - 对话中必须打印：完整文件路径 + 报告摘要（2～3 句话）；并附带 Markdown 链接：`[在应用中打开报告](/user-docs?file=<relative_path>)`，其中 `<relative_path>` 为相对于 `user` 的路径（如 `documents/游戏分析报告/2026-03-06_XX_新游表现报告.md`）。
- **output_destination = chat**：不写本地文件，在回复中直接输出完整报告正文（完整 Markdown）。

**report_format = feishu**：在内存中组合完整报告内容，调用 **feishu_create_doc** 工具：title = `{游戏名} 新游表现报告 — {YYYY-MM-DD}`，content = 完整报告 Markdown 内容，folder_token = FEISHU_FOLDER_TOKEN（若已配置）；工具返回后打印飞书文档 URL 与简短确认。

## 失败处理

- 某款游戏无数据且 game_crawl 也失败：该款在报告中标注「数据不足（爬取失败）」，其余游戏照常生成。
- 所有 game 均无可用数据：告知用户「暂无可用数据，建议先运行 game_crawl 收集目标游戏数据，或确认游戏名与注册表中的注册一致」。
- 游戏未在注册表：Phase 2 已通过委托 game_crawl 自动发现并注册，若 game_crawl 未能发现该游戏，在报告中说明并建议用户确认游戏名或通过 write_game_registry / game_crawl 手动配置。

## Token 节省规则

- 只加载本报告所需 data_types，不读取多余类型。
- 仅在 Phase 4 写最终报告文件（当 output_destination=file）；不保存中间分析文件。
- 委托 game_crawl 时只传入真正需要更新的 data_type 与平台，避免全量重爬。
