---
name: game_announcement_copy
description: "当用户需要为某款游戏生成公告文案（维护、活动、版本预告等）时使用本 skill。通过风格注册表与每风格独立 Markdown 定义，支持无限扩展写作风格与口吻；可为每款游戏配置默认风格，或单次指定风格。本 skill 不爬取数据，游戏未注册时委托 game_crawl 发现并注册。"
metadata:
  {
    "copaw": {
      "emoji": "📢",
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

# Game Announcement Copy Skill（游戏公告文案生成）

本 skill 根据用户提供的要点与所选风格，生成符合该游戏口吻的公告文案。**扩展方式**：新增风格 = 新建 `references/styles/<style_id>.md` + 在下方风格注册表加一行；为游戏设默认风格 = 通过 **write_game_registry** 在该游戏下增加可选字段 `announcement_style_id`。

## 何时使用

- 用户说：为某游戏**写公告**、**写维护通知**、**写活动文案**、**写版本预告**、**生成公告文案**
- 用户希望指定或使用某款游戏的**口吻/写作风格**产出可直接使用的公告正文

## 风格注册表

所有可用风格在此表定义。Phase 1 的风格解析、Phase 2 的文件加载均依赖此表。

**新增风格 = 新建 `references/styles/<style_id>.md` + 在本表加一行，无需修改其他代码。**

| style_id | name_zh | name_en | 适用场景 | 定义文件 |
|----------|---------|---------|----------|----------|
| warm_casual | 温暖口语 | Warm & Casual | 社区向、治愈系、生活模拟 | styles/warm_casual.md |
| official_formal | 正式简洁 | Official Formal | 版本/维护公告、海外向 | styles/official_formal.md |
| playful_emoji | 活泼表情 | Playful+Emoji | 活动、福利、节日公告 | styles/playful_emoji.md |

## 参数提取

从用户消息中提取以下参数。未提及的参数使用默认值。**执行前先 Echo 所有已解析参数。**

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **game** | 游戏名称（中文或英文均可） | 从用户消息推断，无法推断时询问用户 |
| **announcement_type** | 公告类型：maintenance / event / version / general | 从用户意图推断，否则 general |
| **style** | 风格 override（style_id）；不填则用该游戏默认或询问 | 见「style 解析顺序」 |
| **raw_content** | 要传达的要点（列表或段落） | 用户消息中提取，缺失时询问 |
| **language** | 输出语言 zh / en | 与用户消息一致 |
| **length** | 篇幅：short / medium / long | medium |

### style 解析顺序

1. 用户明确指定风格（如「用正式口吻」「用 warm_casual」「活泼一点」）→ 匹配注册表中的 style_id 或 name_zh/name_en，使用对应 style_id。
2. 未指定则调用 **read_game_registry**，从返回的注册表中取 `games[game_key].announcement_style_id`；若存在则使用。
3. 若仍无，列出风格注册表中的 name_zh / name_en 让用户选择，或使用注册表第一行作为默认。

## 执行流程：4 个阶段

### Phase 1 — 解析与风格确定

1. 从用户消息解析 game、announcement_type、raw_content、language、length。
2. **解析 game**：调用 **read_game_registry**，根据 game 匹配返回的 `games` 下的 game_key（如 heartopia、afk_journey）。若游戏未注册，先委托 **game_crawl** skill 执行 Phase 1 发现并注册，再继续。
3. **解析 style**：按「style 解析顺序」得到 style_id；若需询问，列出风格注册表中的 name_zh/name_en 供用户选择。
4. **raw_content**：若用户未提供要传达的要点，询问：「请简单列出这条公告要写的内容要点（例如：维护时间、补偿内容、活动名称等）。」
5. Echo 已解析参数：game、game_key、announcement_type、style_id、language、length、raw_content 摘要。

### Phase 2 — 加载风格定义

1. 根据风格注册表找到 style_id 对应的定义文件路径：`<本 skill 目录>/references/styles/<style_id>.md`。
2. 读取该文件全文。
3. 若文件不存在，报错并提示：「风格 \<style_id\> 未找到，请检查风格注册表与 references/styles/ 下是否存在对应 md 文件。」

### Phase 3 — 生成文案

1. 组装生成请求（prompt 或等价多轮消息）：
   - **角色**：你是该游戏的公告文案撰写者，需严格遵循下方「风格定义」。
   - **风格定义**：Phase 2 读取的 md 全文。
   - **本次任务**：公告类型 = announcement_type；要传达的要点 = raw_content；输出语言 = language；篇幅 = length。
   - **输出要求**：只输出最终公告正文（可含标题），不要输出思考过程；若风格定义中有结构建议，按建议组织段落。
2. 调用 LLM 生成公告文案。
3. 可选：若生成结果明显偏离风格或遗漏要点，在返回时附带一句简短提示（如「已按 XX 风格生成，若需更正式/更短可说明」）。

### Phase 4 — 输出

1. 将生成的公告文案返回用户（对话内展示）。
2. 若用户之前指定了输出到文件或 Feishu，可调用 **feishu_create_doc** 工具或写入指定路径；未指定则默认仅在对话中输出。
3. 附带使用的 style_id 与 game，便于用户复现或切换风格再生成。

## 错误处理

| 问题 | 处理 |
|------|------|
| 游戏未在 game_registry 注册 | 委托 game_crawl Phase 1 发现并注册后继续；若 game_crawl 无法发现，提示用户可通过 write_game_registry 或 game_crawl 手动配置注册表 |
| 风格文件不存在 | 提示「风格 \<style_id\> 定义文件缺失」，列出注册表中已有 style_id，请用户选择或联系维护者添加 |
| raw_content 缺失 | Phase 1 中询问用户补充要点后再继续 |
| 用户未指定风格且游戏无 announcement_style_id | 列出风格注册表（name_zh / name_en），请用户选择或使用注册表第一行 |

## 为游戏配置默认风格

在注册表（通过 **read_game_registry** / **write_game_registry** 读写）的对应游戏对象下增加**可选**字段即可：

```json
"heartopia": {
  "aliases": ["心动小镇", "Heartopia"],
  "announcement_style_id": "warm_casual",
  "platforms": { ... }
}
```

新增游戏只需在 game_registry 存在（可由 game_crawl 发现）；若希望该游戏默认使用某风格，加 `announcement_style_id` 即可。

## 新增一种写作风格

1. 在 `references/styles/` 下新建 `<style_id>.md`（如 `tech_minimal.md`）。
2. 在文件中按「风格定义文件内容结构」填写：风格名称、语气/口吻、称呼与署名、用词偏好与禁忌、结构建议、示例片段、公告类型差异（可选）。
3. 在本 SKILL.md 的「风格注册表」表格中增加一行：style_id | name_zh | name_en | 适用场景 | 定义文件。

无需修改任何其它代码或配置即可生效。
