# 小红书Metadata获取 Skill

## 概述

本 skill 用于从小红书搜索获取帖子元数据（标题、作者、点赞数等）。

**重要：** 本 skill 使用 OpenClaw Browser Relay，需预先登录小红书。

## 前置要求

1. **Browser Relay 已登录小红书**
   - 使用 `openclaw browser open --url https://www.xiaohongshu.com --profile openclaw`
   - 确保登录状态有效（能看到"已关注"等登录态标识）

2. **依赖**
   ```bash
   pip install openclaw  # 确保 openclaw CLI 可用
   ```

## 使用方法

### 方式一：直接运行脚本

```bash
cd d:/App Dev/openclaw-main/skills/game_crawl/xiaohongshu_metadata/scripts
python xiaohongshu_metadata.py \
    --game-id g_a1b2c3d4 \
    --keyword "心动小镇" \
    --limit 50
```

### 方式二：通过 OpenClaw Agent 调用

Agent 自动执行：
1. 检查 browser relay 状态
2. 打开搜索页面
3. 提取数据
4. 保存到游戏目录

## 参数说明

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--game-id` | 是 | 游戏ID | `g_a1b2c3d4` |
| `--keyword` | 是 | 搜索关键词 | `心动小镇` |
| `--limit` | 否 | 数量限制 | 默认 100 |
| `--profile` | 否 | Browser profile | 默认 `openclaw` |

## 输出格式

```json
{
  "platform": "xiaohongshu",
  "game_id": "g_a1b2c3d4",
  "data_type": "metadata",
  "keyword": "心动小镇",
  "fetched_at": "2026-03-27T10:45:00+08:00",
  "count": 50,
  "items": [
    {
      "id": "69a94718000000001a0236c7",
      "title": "心动小镇迟早出大事",
      "author": "荔枝鸡",
      "likes": "1195",
      "url": "https://www.xiaohongshu.com/search_result/..."
    }
  ]
}
```

## 数据存储路径

```
data/game_data/games/{game_id}/xiaohongshu/metadata.json
```

## 与旧版本区别

| 特性 | 旧版本 | 新版本 |
|------|--------|--------|
| 浏览器 | 本地 Playwright | Browser Relay |
| 登录 | 每次手动扫码 | 一次登录，重复使用 |
| 依赖 | playwright | openclaw CLI |
| 速度 | 慢（需启动浏览器） | 快（直接连接） |

## 故障排查

### 问题："未登录状态"
**解决：** 先执行登录
```bash
openclaw browser open --url https://www.xiaohongshu.com --profile openclaw
# 手动登录后保持浏览器打开
```

### 问题："tab not found"
**解决：** browser relay 连接中断，重启 openclaw gateway
```bash
openclaw gateway restart
```

### 问题：数据为空
**解决：** 检查登录状态，确保搜索页面能正常加载内容
