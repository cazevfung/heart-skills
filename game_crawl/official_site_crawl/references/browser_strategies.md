# Official Site Browser Strategies

官网抓取浏览器策略

## 通用流程

```
browser open <url> → 等待加载 → 抓取内容 → 保存
```

## 公告抓取

**目标：** 游戏官网公告/新闻页面

**步骤：**
1. 打开官网公告页面
2. 等待 JavaScript 渲染
3. 提取公告列表
4. 逐条进入详情页抓取内容

**示例：**
```python
# 使用 browser 工具
browser open "https://game.com/news"
browser snapshot
# 提取公告标题、链接、时间
```

## 更新日志抓取

**目标：** 版本更新/Patch Notes 页面

**步骤：**
1. 打开更新日志页面
2. 等待加载
3. 提取版本号、更新内容

**常见 URL 模式：**
- `/news`
- `/patch-notes`
- `/updates`
- `/announcements`

## 注意事项

- 官网结构各异，需要针对性处理
- 可能需要处理分页
- 注意反爬机制，控制频率
