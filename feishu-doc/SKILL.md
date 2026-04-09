---
name: feishu-doc
description: 将 Markdown 内容或本地文件发布到飞书云文档。支持标题、正文、表格等格式，自动转换为飞书 docx 格式。需要在 OpenClaw 环境变量中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET。
---

# Feishu Doc Publisher

将 Markdown 内容发布到飞书云文档。

## 前置配置

在 OpenClaw 环境变量中配置：
- `FEISHU_APP_ID` - 飞书应用 ID
- `FEISHU_APP_SECRET` - 飞书应用密钥

## 使用方式

### 从 Markdown 内容创建文档

```bash
python "<skill_dir>/scripts/publish.py" --title "文档标题" --content "# 标题\n\n正文内容" [--folder-token xxx]
```

### 从本地文件创建文档

```bash
python "<skill_dir>/scripts/publish.py" --title "文档标题" --file "/path/to/file.md" [--folder-token xxx]
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` | 是 | 文档标题 |
| `--content` | 否 | Markdown 内容（与 --file 二选一） |
| `--file` | 否 | 本地 Markdown 文件路径（与 --content 二选一） |
| `--folder-token` | 否 | 目标文件夹 Token，不填则存入个人空间 |

## 输出

成功时返回 JSON：
```json
{
  "url": "https://feishu.cn/docx/xxx",
  "document_id": "xxx"
}
```

失败时返回：
```json
{
  "error": "错误信息"
}
```

## 支持的 Markdown 格式

- 标题（# ## ###）
- 段落与换行
- 加粗（**text**）
- 斜体（*text*）
- 无序列表（- item）
- 有序列表（1. item）
- 引用（> quote）
- 表格（| col1 | col2 |）—— 简单表格支持，复杂表格可能解析失败
- 代码块（```code```）
- 水平分割线（---）

## 限制与注意事项

### Markdown 表格限制

- 不支持复杂表格（嵌套、多行表头等）
- 表格列数过多时可能渲染异常
- **建议：** 复杂表格转为列表格式，确保稳定性

### 大文档处理

- 文档内容超过 1000 行时，建议分段发布
- 返回码 1 通常是格式解析失败，简化 Markdown 后重试

### 故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 返回码 1，无文档生成 | Markdown 格式错误 | 简化格式，移除复杂表格 |
| 文档生成但内容不完整 | 部分内容解析失败 | 检查是否有不支持的格式 |
| 文档在个人空间而非指定文件夹 | folder-token 无效或缺失 | 确认环境变量 FEISHU_FOLDER_TOKEN |
| 认证失败 | 凭证错误 | 检查 FEISHU_APP_ID 和 FEISHU_APP_SECRET |
