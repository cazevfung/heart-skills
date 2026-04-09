---
name: game-discovery
description: "查询近期新游戏上线或即将上线的资讯，涵盖国内（TapTap、游民星空、3DM）和海外（Steam、IGN）来源。当用户询问新游戏、近期上线游戏、即将发布游戏、新游推荐、游戏发布日程、内测/公测/测试资格时使用。"
metadata:
  {
    "copaw": {
      "emoji": "🎮",
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

# Game Discovery

当用户询问近期新游戏或即将上线游戏时，使用 **browser_use** 按以下来源抓取资讯并汇总回复。

## 来源表

| 优先级 | 分类 | 来源 | URL |
|--------|------|------|-----|
| P0 | 国内新游（手游/PC） | TapTap 新游上线 | https://www.taptap.cn/taptap-choices/new-game |
| P0 | 国内游戏资讯 | 游民星空 新游频道 | https://www.gamersky.com/newgame/ |
| P1 | 国内游戏资讯 | 3DM 新游 | https://www.3dmgame.com/games/xinyou/ |
| P1 | 海外 PC/主机 | Steam 新游上线 | https://store.steampowered.com/explore/new/ |
| P2 | 海外综合 | IGN Upcoming | https://www.ign.com/upcoming/games |

## 执行步骤

1. **判断用户意图**：
   - 只问国内 → 抓 P0 两个来源
   - 只问海外 → 抓 P1/P2 海外来源
   - 未指定（默认）→ 抓 P0 全部 + P1 海外来源（共3个）

2. **抓取每个来源**（逐个执行，不混用）：
   ```json
   {"action": "open", "url": "https://www.taptap.cn/taptap-choices/new-game"}
   ```
   ```json
   {"action": "snapshot"}
   ```

3. **整理回复**，分两个分组：
   - **已上线**：游戏名、上线日期、平台、一句话简介、来源链接
   - **即将上线 / 测试中**：游戏名、预计日期或状态（内测/公测/定档/待定）、平台、来源链接

4. **注册到查找库（含去重）**（为省 token：**注册表只读一次、只写回一次**；所有去重与合并均在本次读入的 `games` 上完成，不要按游戏多次读/写）：
   - **读取当前注册表**：调用 **read_game_registry** **仅一次**，得到 `games` 对象。若返回的注册表为空或无 `games`，本步可跳过写回（由 game_crawl 首次使用时初始化），仅保留整理回复即可。
   - **对每个已整理出的游戏执行去重判断**：
     - 输入：本轮发现并整理出的游戏名（及若有则带上从页面解析到的 TapTap app_id 等）。
     - **生成候选 game_key**：由游戏名生成，规则与现有注册表风格一致（如英文名转小写、空格替为下划线、去标点，得到 snake_case；仅中文名时可用拼音缩写或暂用英文/中文标识，避免与现有 key 冲突）。参见 `game_crawl` SKILL 中注册表 schema。
     - **判定是否已存在**：① 若 `games` 中已有该 `game_key` → 视为已登录，跳过。② 否则，将当前游戏名规范化（小写、去标点、trim），与 `games` 中**每个**条目的 `game_key` 及该条目下 `aliases` 逐一做**大小写不敏感**比较；若有任一匹配 → 视为同一游戏（已登录），跳过；可选：若该条目缺少当前展示名，可记录「建议将展示名加入该条目的 aliases」，在一次性写回时顺带更新该条目的 `aliases`。
     - 仅当「未匹配到任何已有 game_key 或 aliases」时，才加入待写入列表。
   - **构建最小新条目并合并**：对每个通过去重的新游戏，构造最小条目：`aliases` 至少包含本页使用的游戏名（多语言/多来源名称可一并放入）；`platforms` 可为 `{}`；若本步能从发现页直接解析到 TapTap 链接（如 `/app/<数字id>/`），可填 `taptap: { "target": "<app_id>" }`。将新条目以 `games[game_key] = { ... }` 合并进已读取的 `games`，**不覆盖**已有 key。
   - **一次性写回**：若有至少一个新增条目（或对已有条目的 aliases 补充），**仅一次**调用 **write_game_registry** 传入完整注册表写回（不要按游戏多次写回）。在回复中简要说明：本次新登录到查找库的游戏列表；已存在而跳过的游戏（可选列出）；若因注册表为空而跳过写回，也一并说明。
   - **与整理回复的关系**：先完成上述「整理回复」内容，再执行本注册步骤；最终回复中可增加「已将上述新游戏登记到查找库，重复项已跳过」及新登录数量或列表。

## 注意事项

- TapTap 页面为 JS 渲染，若 snapshot 内容为空，等待 2 秒后再次 snapshot。
- 若某来源不可访问，跳过并说明，继续下一个来源。
- 回复中标注每条信息的来源名称，方便用户溯源。
- 本 skill 只做**发现**，不做深度数据收集；如需某款游戏的详细玩家评价或版本分析，请使用 `game_crawl` + `game_report`。
- **注册表与去重**：
  - **省 token**：注册表整流程只调用一次 **read_game_registry**、一次 **write_game_registry**；先查后加均在内存中完成。
  - **去重优先**：每次写回前必须基于**当前** read_game_registry 返回的注册表做上述去重，避免同一游戏因名称变体（中英文、简繁体等）被重复登录。
  - **不覆盖**：仅新增 `games` 中不存在的 `game_key`，绝不覆盖已有条目的 `platforms`、`queries` 等。
  - **game_key 命名**：与现有注册表风格一致（如 heartopia、afk_journey、naraka_bladepoint），避免与现有 key 冲突；若无法确定可读 key，可先用保守的临时 key 并在 aliases 中写清名称，后续由 game_crawl Phase 1 发现时再补全或调整。
