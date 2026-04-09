---
name: official_site_crawl
description: "游戏官网抓取专用 skill。仅用于浏览器模式，抓取官网公告、更新日志。禁止用于其他平台。"
metadata:
  {
    "copaw":
      {
        "emoji": "🌐",
        "requires": {}
      }
  }
---

# Official Site Crawl Skill

## 职责
- 抓取游戏官网公告
- 抓取更新日志
- 需要 browser 模式

## 使用场景
- ✅ 官网公告
- ✅ 更新日志
- ✅ 需要 JavaScript 渲染的页面

## 禁止使用场景
- ❌ YouTube/Bilibili/Reddit/TapTap（都有专用 skill）

## 输入
- `--url`: 官网 URL
- `--type`: 数据类型（announcements/changelogs）

## 执行
```bash
# 需使用 browser 工具
browser open <url>
```

## 策略文档
见 `references/browser_strategies.md`
