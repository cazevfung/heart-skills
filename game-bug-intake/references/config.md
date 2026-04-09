# Game Bug Intake - 配置文件

## 飞书表格配置

创建飞书应用并获取以下信息：

```yaml
feishu:
  app_id: "cli_xxxxxxxxxxxxxxxx"           # 飞书应用 ID
  app_secret: "xxxxxxxxxxxxxxxxxxxxxxxx"   # 飞书应用密钥
  spreadsheet_token: "shtcnxxxxxxxxxxxx"   # 表格 Token（从 URL 中获取）
  sheet_name: "BugReports"                  # 工作表名称
```

## 表格字段设置

在飞书表格中创建以下列：

| 列名 | 类型 | 说明 |
|------|------|------|
| UID | 文本 | 玩家唯一标识 |
| 上报时间 | 日期时间 | 自动填充 |
| 问题类型 | 单选 | progression_blocker/visual_bug/data_loss/performance/functional/text_error |
| 严重程度 | 单选 | blocker/major/minor |
| 问题简述 | 文本 | 一句话描述 |
| 详细描述 | 文本 | 完整描述 |
| 发生位置 | 文本 | 游戏内位置 |
| 设备信息 | 文本 | 设备型号+系统 |
| 游戏版本 | 文本 | 版本号 |
| 复现步骤 | 文本 | 如何重现 |
| 已尝试解决 | 文本 | 玩家已尝试的方法 |
| 截图链接 | 文本 | 附件 URL |
| 处理状态 | 单选 | pending/confirmed/fixing/fixed |
| 处理人 | 文本 | 负责跟进的人 |

## 环境变量配置

将敏感信息配置为环境变量：

```bash
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
export FEISHU_SPREADSHEET_TOKEN="your_spreadsheet_token"
```

## API 权限申请

飞书应用需要申请以下权限：
- `sheet:spreadsheet:read` - 读取表格
- `sheet:spreadsheet:write` - 写入表格
