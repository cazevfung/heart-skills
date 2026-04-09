# 平台注册表

所有可用平台及对应 skill

## 视频平台

| 平台 | Skill | 两步流程 | 说明 |
|------|-------|---------|------|
| YouTube | `youtube_metadata` → `youtube_transcript` | 是 | 海外视频+转录 |
| Bilibili | `bilibili_metadata` → `bilibili_transcript` | 是 | 国内视频+转录 |

## 社区平台

| 平台 | Skill | 两步流程 | 说明 |
|------|-------|---------|------|
| Reddit | `reddit_metadata` → `reddit_comment` | 是 | 海外论坛帖子+评论 |
| TapTap | `taptap_review` / `taptap_forum_officialpost_metadata` → `taptap_comment` | 否/是 | 评价/官方帖子+评论 |

## 选择策略

```python
PLATFORM_STRATEGY = {
    "国内游戏": ["bilibili", "taptap"],
    "海外游戏": ["youtube", "reddit"],
    "全球热门": ["youtube", "bilibili", "reddit", "taptap"],
}
```

## 执行顺序

1. **视频平台**（耗时最长，先执行）
   - YouTube / Bilibili metadata
   - YouTube / Bilibili transcript

2. **社区平台**（可并行）
   - Reddit metadata + comment
   - TapTap review
   - TapTap forum metadata + comment

## 输出路径规范

```
data/game_data/games/{game_id}/
├── {platform}/
│   └── {data_type}.json
└── checkpoints/
    └── {platform}_{data_type}_checkpoint_{num}.json
```
