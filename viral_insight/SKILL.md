---
name: viral_insight
description: "当用户需要传播/推荐洞察、玩家为何安利或吐槽传播、哪些内容易引发讨论或二创时使用本 skill。基于 game_crawl 的 UGC 归纳「值得分享的时刻」与传播风险点；无 K 因子数据时在报告中注明「基于玩家反馈的传播洞察」。可与 game_report、community_plan_review 并列使用。"
metadata:
  {
    "copaw": {
      "emoji": "🔄",
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

# 传播洞察专家 Skill

本 skill 是游戏分析的**传播/推荐专项层**。从 `game_crawl` 的持久化数据（评价、论坛帖子，可选视频标题/评论）中读取内容，按传播分析框架归纳玩家在什么情境下会安利或吐槽传播、哪些内容易引发讨论或二创，输出传播洞察报告。本 skill 不直接爬取数据；数据缺失或过期时委托 **game_crawl** 收集。

## 何时使用

- 用户提到：**传播**、推荐、安利、口碑、K 因子、二创、讨论度、玩家自发分享、值得分享
- 用户问：玩家为什么会安利/吐槽这款游戏、哪些内容容易传播、传播风险点
- 需要产出**传播专项报告**（与舆情/社区方案区分）

若用户仅要舆情分析，使用 **game_report**；若要做社区方案或复盘，使用 **community_plan_review**。

## 参数提取

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **game** | 游戏名称（中文或英文） | 从用户消息推断，无法推断时询问 |
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

**所需 data_types：** `reviews`、`forum_posts`。可选：`videos`（标题/评论中的推荐、安利、二创等）。

**就绪规则：** 与 game_report Phase 2 相同。若有缺失或过期且未设置 `use_existing_data_only`，**委托 game_crawl**，待完成后再继续。

## 执行流程

### Phase 1 — 理解与参数

1. 解析用户消息，填写参数表；推断 `game`（不明确则询问）。
2. Echo 参数；确认使用「传播洞察报告」。

### Phase 2 — 数据就绪

1. 按「数据来源与就绪检查」对所需 data_types 做就绪检查。
2. 若有需爬取项，委托 **game_crawl**，完成后继续。

### Phase 3 — 传播分析

1. 从合并存储读取各平台 `reviews`、`forum_posts`（及可选的 `videos`）。
2. 阅读本 skill 的 **references/referral_framework.md**，按其中维度对 UGC 做归类与归纳：
   - 正面传播情境（安利、推荐、拉人、二创、自发讨论）
   - 负面传播情境（吐槽扩散、差评传播、舆情爆发）
   - 易传播内容类型与「值得分享的时刻」
3. **重要**：若无 K 因子或分享率等数据，在报告中明确注明：「本报告基于玩家评价与讨论归纳传播相关洞察，非来自真实 K 因子或分享率数据。」

### Phase 4 — 报告生成与输出

1. 按 **references/template_viral.md** 生成传播洞察报告正文。
2. 若 `report_format=markdown`：按 `output_destination` 写文件或仅在对话中输出；若 `report_format=feishu`：调用 **feishu_create_doc** 工具，返回后打印飞书文档 URL 与简短确认。

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| 传播/推荐/安利/二创/讨论度分析 | **viral_insight**（本 skill） |
| 舆情、版本、综合分析 | **game_report** |
| 社区方案、社区复盘 | **community_plan_review** |
| 仅收集数据、不写报告 | **game_crawl** |

## 参考文件

- 传播分析框架：[references/referral_framework.md](references/referral_framework.md)
- 传播报告模板：[references/template_viral.md](references/template_viral.md)
