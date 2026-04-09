---
name: game-bug-intake
description: 游戏 Bug 收集与上报 Skill。用于识别玩家上报的游戏问题，通过多轮对话收集详细信息，并将结构化数据存储到飞书表格。当玩家描述游戏异常、卡顿、数据丢失、功能失效等问题时触发。支持追问获取复现步骤、截图、设备信息等。
---

# Game Bug Intake - Bug 收集与上报

## 核心职责

1. **识别 Bug 上报**：从玩家对话中识别 Bug 相关描述
2. **多轮信息收集**：通过追问获取完整信息
3. **结构化存储**：将 Bug 信息写入飞书表格

## Bug 类型定义

| 类型 | 描述 | 示例 |
|------|------|------|
| progression_blocker | 进度阻断 | 卡关、任务无法完成、门打不开 |
| visual_bug | 显示异常 | 贴图错误、UI 错位、黑屏 |
| data_loss | 数据丢失 | 物品消失、进度回滚、存档损坏 |
| performance | 性能问题 | 卡顿、闪退、发热、耗电快 |
| functional | 功能异常 | 按钮无响应、功能无法使用 |
| text_error | 文本错误 | 错别字、翻译问题、文本显示不全 |

## 多轮对话流程

### 第一轮：识别与分类

**玩家输入示例**："我的商店突然不见了"

**Bot 判断**：
- 疑似 Bug：是
- 初步分类：visual_bug 或 functional
- 紧急程度：中（影响功能但非完全阻断）

**Bot 回复**：
```
听起来你遇到了显示问题。为了帮你更好地解决，我需要了解一些细节：

1. 是在哪个界面看不到商店？（主界面/农场内/其他）
2. 这个问题是突然出现的吗？之前有没有更新游戏或清理缓存？
```

### 第二轮：收集上下文

**玩家回复后**，继续追问：
- 设备型号（iOS/Android/PC）
- 游戏版本号
- 是否尝试过重启/重装

### 第三轮：收集证据

询问是否可以提供：
- 截图
- 录屏
- 具体复现步骤

### 第四轮：确认与存储

汇总信息，征得玩家同意后存储：
```
已收集以下信息：
- 问题：商店图标消失
- 设备：iPhone 14 / iOS 17
- 版本：v1.2.3
- 尝试：已重启，问题仍在

是否确认提交这个反馈？提交后我们会尽快排查。
```

## 飞书表格结构

存储字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| uid | string | 玩家UID |
| timestamp | datetime | 上报时间 |
| bug_type | enum | 问题类型 |
| severity | enum | 严重程度：blocker/major/minor |
| title | string | 问题简述 |
| description | text | 详细描述 |
| location | string | 发生位置/场景 |
| device | string | 设备信息 |
| version | string | 游戏版本 |
| reproduction_steps | text | 复现步骤 |
| workarounds_tried | text | 已尝试的解决方法 |
| screenshots | array | 截图链接 |
| status | enum | 状态：pending/confirmed/fixing/fixed |
| handler | string | 处理人 |

## 脚本使用

### 存储 Bug 到飞书

```bash
python scripts/store_bug.py \
  --title "商店图标消失" \
  --type visual_bug \
  --severity major \
  --uid "123456" \
  --description "主界面商店按钮消失..." \
  --device "iPhone 14, iOS 17" \
  --version "1.2.3"
```

### 查询 Bug 状态

```bash
python scripts/query_bug.py --uid "123456"
```

## 追问策略

### 必问字段（Minimum Viable Info）

1. **问题描述**（已在上报时获得）
2. **发生位置**（哪个界面/场景）
3. **设备信息**（型号+系统）
4. **游戏版本**

### 选问字段（根据情况追问）

- **复现步骤**：如果问题可重复出现
- **截图/录屏**：视觉类问题强烈建议
- **已尝试解决**：避免重复建议
- **发生频率**：偶发/必现

### 追问话术模板

**获取设备信息**：
"方便告诉我你的设备型号吗？比如 iPhone 14 或小米13，这有助于我们定位问题。"

**获取版本信息**：
"你的游戏版本号是多少？可以在设置-关于里查看。"

**获取复现步骤**：
"这个问题每次都会出现吗？能描述一下你做了什么之后出现的吗？"

**获取截图**：
"如果可以的话，截个图给我看看？这样我能更准确地判断问题。"

## 严重程度判断

| 级别 | 标准 | 响应话术 |
|------|------|---------|
| blocker | 完全无法游戏、数据丢失 | "这个问题很严重，我会优先反馈给技术团队" |
| major | 核心功能受损、体验严重下降 | "这个问题影响较大，我会记录并跟进" |
| minor | 视觉瑕疵、非核心功能异常 | "收到反馈，我们会安排在后续版本优化" |

## 与攻略 QA 的边界

**区分 Bug vs 攻略问题**：

| 玩家描述 | 判断 | 处理方式 |
|---------|------|---------|
| "小麦怎么获得" | 攻略问题 | 转 guide_qa |
| "我种了小麦但一直不生长" | 疑似bug | 先确认是否缺水/季节，排除后转bug_intake |
| "商店按钮点不动" | bug | 直接走bug_intake |
| "第三章怎么解锁" | 攻略问题 | 转 guide_qa |

**模糊地带处理**：
先尝试用攻略逻辑解释，如果玩家确认"不是这个问题"，再转bug收集。

## 配置说明

飞书表格配置在 `references/config.md`：

```yaml
feishu:
  app_id: ${FEISHU_APP_ID}
  app_secret: ${FEISHU_APP_SECRET}
  spreadsheet_token: "YOUR_SPREADSHEET_TOKEN"
  sheet_name: "BugReports"
```
