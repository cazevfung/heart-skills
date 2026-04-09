---
name: version_update_video_script
description: "当用户需要根据游戏版本更新、patch notes 生成视频口播稿时使用本 skill。支持不同口吻（正式、轻松、搞笑、专业评测、玩家向）、不同写作风格和不同视频结构（标准、快剪、故事线等）。从 game_crawl 的 changelogs 读取版本内容；数据缺失或过期时委托 game_crawl 收集。通过风格注册表与结构注册表可扩展，新增风格或结构只需加注册表行与可选 reference 文件。"
metadata:
  {
    "copaw": {
      "emoji": "🎬",
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

# Version Update Video Script Skill

本 skill 根据游戏版本更新内容（changelog）生成**视频口播稿**。通过**风格注册表**与**结构注册表**实现可扩展：新增口吻、写作风格或视频结构时，只需在对应注册表加一行（及可选的 `references/style_<id>.md`、`references/structure_<id>.md`），无需修改本 SKILL.md 主流程。

## 参数提取

从用户消息中提取以下参数。未提及的参数使用默认值。**执行前先 Echo 所有已解析参数。**

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **game** | 游戏名称（中文或英文均可） | 从用户消息推断，无法推断时询问用户 |
| **version** | 版本号（指定某版本） | 最新版本（changelog 中 release_date 最新的一条） |
| **style** | 风格 id（口吻+写作风格），见风格注册表 | 从用户消息用触发词推断；否则用 game_overrides 的 default_style_id 或询问 |
| **structure** | 视频结构 id，见结构注册表 | 从用户消息推断；否则用 game_overrides 的 default_structure_id 或询问 |
| **script_language** | 稿子语言 | 与用户提问语言一致 |
| **duration_target** | 目标时长（如「3–5 分钟」），用于约束篇幅 | 可选 |
| **output_path** | 输出目录路径 | `user/documents/视频稿/` |
| **output_destination** | `file` 仅写文件，`chat` 仅在对话中输出完整稿子 | `file` |

## 风格注册表

所有可用风格在 `references/style_registry.md` 中定义。Phase 1 的 style 推断、Phase 3 的风格加载均从该表读取。**新增风格 = 在 style_registry 加一行 + 可选新建 `references/style_<id>.md`。**

执行前从 `references/style_registry.md` 读取完整表格；若用户未指定 style，用触发关键词匹配或读取 `config/game_overrides.json` 中该游戏的 `default_style_id` 补全；仍无法确定则询问用户。

## 结构注册表

所有可用视频结构在 `references/structure_registry.md` 中定义。Phase 1 的 structure 推断、Phase 3 的结构加载、Phase 4 的逐段生成均从该表读取。**新增结构 = 在 structure_registry 加一行 + 可选新建 `references/structure_<id>.md`。**

执行前从 `references/structure_registry.md` 读取完整表格；若用户未指定 structure，用触发关键词匹配或读取 game_overrides 的 `default_structure_id`；仍无法确定则询问用户。

## 意图推断规则

- **game**：若用户消息中无法识别任何游戏名称，立即询问「你想为哪款游戏写版本更新视频稿？」。
- **style**：用风格注册表的「触发关键词」列匹配（如「正式」「轻松」「搞笑」「专业」「玩家」）；若存在 `config/game_overrides.json` 且该游戏有 `default_style_id`，未指定时使用该默认值。
- **structure**：用结构注册表的「触发关键词」列匹配（如「标准」「快剪」「故事」）；若存在 game_overrides 的 `default_structure_id`，未指定时使用该默认值。
- **output_destination**：用户明确说「在对话框看」「直接发聊天」「发到对话」等时设为 `chat`，否则 `file`。

## 执行流程：5 个阶段

### Phase 1 — 参数解析

1. 解析用户消息，填写参数表。
2. 推断 `game`（不明确时询问）。
3. 读取 `references/style_registry.md` 与 `references/structure_registry.md`；推断 `style`、`structure`（不明确时用 game_overrides 或询问）。
4. 若存在 `config/game_overrides.json`，检查该游戏是否有 `default_style_id` / `default_structure_id`，用于补全未指定项。
5. Echo 所有已解析参数（含将使用的风格名、结构名）。

### Phase 2 — 版本数据就绪

**数据根目录：** 与 game_report 一致，固定为项目根目录下的 `data/game_data`。

1. 调用 **read_game_registry**，从返回的注册表解析该游戏的各平台（与 game_report 相同方式）；确定该游戏在哪些平台有 changelogs 配置（如 taptap、official_site）。
2. 对每个可能提供 changelogs 的平台检查：`merged/<平台>/<game_id>/changelogs/data.json` 是否存在，且 `last_updated` 在 **24 小时内**。
3. 若任一所需平台数据不存在或过期：**委托 game_crawl skill**，传入 `game`、`data_types: ["changelogs"]`、`platforms: auto`。等待完成后继续。
4. 用户明确说「用现有数据」「不爬取」时，跳过爬取，即使数据过期也继续。
5. 加载所有相关平台的 changelogs 合并结果；按 `version` 字符串去重（同版本取 body 更详的条目），按 `release_date` 降序。若用户指定了 `version`，筛选出该版本；否则取 **最新一条** 作为本次生成的目标版本。将目标版本的 `version`、`release_date`、`title`、`body` 作为 Phase 4 的输入。

### Phase 3 — 加载风格与结构

1. 从风格注册表取当前 `style_id` 对应行；若有 `references/style_<style_id>.md` 则读取，作为口吻与写作约束。
2. 从结构注册表取当前 `structure_id` 对应行；若有 `references/structure_<structure_id>.md` 则读取，得到段落顺序与每段要求（字数/时长建议、是否带时间戳等）。
3. 若存在 `config/game_overrides.json` 且该游戏有 `brand_voice`、`avoid_topics`，一并纳入生成约束（在 Phase 4 中遵循）。

### Phase 4 — 生成视频稿

1. 按**结构**的段落顺序逐段生成。每段内容须符合**风格**的口吻与写作要求，并基于 Phase 2 得到的目标版本 changelog 提炼要点（新角色、平衡调整、系统改动、Bug 修复等）。
2. 若结构的详细说明要求带时间戳（如 `[0:00]`），在稿子中相应位置插入占位。
3. 若用户指定了 `duration_target`，在生成说明中约束总字数/句数以匹配目标时长（例如中文约 200–250 字/分钟）。
4. 输出为连贯的口播稿 Markdown，可含段落标题与时间戳占位。

### Phase 5 — 输出

- **output_destination=file**（默认）：
  - 文件名：`{YYYY-MM-DD}_{游戏名}_v{版本号}_视频稿_{structure_id}.md`（版本号中的特殊字符可替换为下划线）。
  - 写入 `output_path` 目录。
  - 对话中输出：完整文件路径 + 简短摘要（游戏、版本、风格、结构）；并附带链接：`[在应用中打开](/user-docs?file=<relative_path>)`，其中 `<relative_path>` 为相对于 `user` 的路径（如 `documents/视频稿/2026-03-06_守望先锋_v2026.02.25_视频稿_standard.md`）。

- **output_destination=chat**：
  - 不写本地文件，在回复中直接输出完整视频稿正文（Markdown）。

## 失败处理

- 若 read_game_registry 返回的注册表中无该游戏：委托 game_crawl 自动发现并注册后继续。
- 若 changelogs 数据不可用且 game_crawl 也失败：告知用户先运行 game_crawl 收集 changelogs，或提供 patch notes 原文/链接由用户粘贴后重试。
- 若指定 version 在合并后的 versions 中不存在：告知用户「未找到该版本」，并列出当前已有的版本号供选择。

## Token 节省规则

- 仅加载目标版本对应的 changelog 内容，不加载其他 data_type。
- Phase 3 仅读取当前 style_id / structure_id 对应的 reference 文件（若存在），不预读全部 style_*.md / structure_*.md。
