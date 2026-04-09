---
name: game-cs-agent
description: 游戏客服+攻略 Agent 的中央协调 Skill。负责接收玩家消息，进行意图识别和路由分发，协调 guide_qa 和 bug_intake 两个子 Skill。管理对话上下文，处理 Skill 切换，整合回答并返回给玩家。当玩家与游戏客服 Bot 对话时触发。
---

# Game CS Agent - 客服 Agent 中央协调

## 架构定位

```
┌─────────────────────────────────────────┐
│         玩家对话界面                      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Game CS Agent (本 Skill)           │
│  - 意图识别                              │
│  - 上下文管理                            │
│  - Skill 路由                            │
│  - 回答整合                              │
└───────┬───────────────┬─────────────────┘
        │               │
┌───────▼──────┐  ┌────▼────────┐
│ game-guide-qa │  │ game-bug-  │
│   攻略问答    │  │   intake   │
│              │  │  Bug收集    │
└──────────────┘  └─────────────┘
```

## 意图识别矩阵

| 玩家输入特征 | 意图分类 | 路由目标 | 置信度判断 |
|-------------|---------|---------|-----------|
| "怎么获得"、"在哪里"、"怎么做" | 攻略查询 | guide_qa | 高 |
| "为什么XX不XX" + 异常描述 | 疑似 Bug | 需澄清 | 中 |
| "消失了"、"不见了"、"点不动" | Bug 上报 | bug_intake | 高 |
| "卡顿"、"闪退"、"黑屏" | Bug 上报 | bug_intake | 高 |
| "谢谢"、"好的"、"明白了" | 对话结束 | 直接回复 | 高 |
| 模糊描述 | 需澄清 | 追问 | 低 |

## 上下文状态机

```
[初始状态]
    │
    ▼
[意图识别] ──► 攻略查询 ──► [guide_qa 状态]
    │              │
    │              ▼
    │         [回答玩家]
    │              │
    │              ▼
    │         [追问/结束]
    │
    ├──► Bug 上报 ──► [bug_intake 状态]
    │       │
    │       ▼
    │  [信息收集轮1]
    │       │
    │       ▼
    │  [信息收集轮2]
    │       │
    │       ▼
    │  [信息收集轮3]
    │       │
    │       ▼
    │  [确认存储]
    │
    └──► 模糊/需澄清 ──► [追问状态] ──► 回到意图识别
```

## 关键决策逻辑

### 1. 攻略 vs Bug 的边界判断

**明确攻略问题**（直接路由 guide_qa）：
- 询问获取方式、位置、解锁条件
- 询问游戏机制、规则说明
- 询问任务完成方法

**明确 Bug 问题**（直接路由 bug_intake）：
- 描述异常现象（消失、无法点击、显示错误）
- 性能问题（卡顿、闪退、发热）
- 数据异常（物品消失、进度回滚）

**模糊地带**（先澄清）：
- "XX 不工作" → 先问："是不知道怎么操作，还是操作了没反应？"
- "拿不到 XX" → 先问："是不知道获取方式，还是完成了条件但没收到？"

### 2. 状态保持与切换

**同一会话内状态保持**：
```
玩家: "小麦怎么获得" → guide_qa 回答
玩家: "那玉米呢" → 保持 guide_qa 上下文，理解"那"指代同类问题
玩家: "我的商店不见了" → 切换至 bug_intake，重置上下文
```

**多轮对话管理**：
- Bug 收集过程中，玩家突然问攻略问题 → 保存 Bug 进度，回答攻略，然后回到 Bug 收集
- 记录每个意图的完成度，支持断点恢复

## 协作流程示例

### 场景 1：纯攻略咨询

```
玩家: "小麦怎么获得"
    │
    ▼
CS Agent: 意图识别 = 攻略查询 (置信度: 高)
    │
    ▼
guide_qa: 检索知识库 → 生成回答
    │
    ▼
CS Agent: 整合回答 → 返回玩家

玩家: "玉米呢"
    │
    ▼
CS Agent: 上下文识别 = 同类攻略问题
    │
    ▼
guide_qa: 检索"玉米获取"
    │
    ▼
CS Agent: 返回回答
```

### 场景 2：纯 Bug 上报

```
玩家: "我的商店图标不见了"
    │
    ▼
CS Agent: 意图识别 = Bug 上报 (置信度: 高)
    │
    ▼
bug_intake: 开始收集流程
    │
    ▼
CS Agent: "是在哪个界面看不到商店？"

玩家: "主界面"
    │
    ▼
bug_intake: 记录位置，进入轮2
    │
    ▼
CS Agent: "你的设备型号是？"

玩家: "iPhone 14"
    │
    ▼
bug_intake: 记录设备，进入轮3
    │
    ▼
CS Agent: "方便截图看看吗？"

玩家: [上传截图]
    │
    ▼
bug_intake: 存储截图链接，信息完整
    │
    ▼
CS Agent: "已记录，我们会尽快排查"
    │
    ▼
bug_intake: 调用 store_bug.py → 飞书表格
```

### 场景 3：模糊地带处理

```
玩家: "我种的小麦不生长"
    │
    ▼
CS Agent: 意图模糊（攻略？Bug？）
    │
    ▼
CS Agent: "小麦不生长通常是因为缺水，你检查过是否需要浇水吗？"

玩家: "浇过了，还是不生长"
    │
    ▼
CS Agent: 排除攻略原因 → 确认为 Bug
    │
    ▼
切换到 bug_intake 流程
```

### 场景 4：中途切换

```
玩家: "我的任务完成不了" → 进入 bug_intake
    │
    ▼
CS Agent: "是哪个任务？"

玩家: "哦对了，小麦怎么获得来着" → 攻略问题插入
    │
    ▼
CS Agent: 保存 bug_intake 进度
    │
    ▼
guide_qa: 回答小麦获取
    │
    ▼
CS Agent: "回到刚才的任务问题，你遇到的是...？"
    │
    ▼
恢复 bug_intake 进度
```

## 上下文数据结构

```json
{
  "session_id": "uuid",
  "current_intent": "guide_qa|bug_intake|clarifying",
  "intent_history": [
    {"intent": "guide_qa", "query": "小麦获取", "completed": true},
    {"intent": "bug_intake", "stage": 2, "data": {...}, "completed": false}
  ],
  "guide_qa_context": {
    "last_topic": "crops",
    "last_item": "小麦"
  },
  "bug_intake_context": {
    "stage": 2,
    "collected": {
      "title": "任务无法完成",
      "type": "progression_blocker",
      "location": "第三章"
    },
    "pending_questions": ["device", "version"]
  }
}
```

## 回答整合规则

### 从子 Skill 获取原始回答后：

1. **添加语气包装**：根据游戏官方人设调整口吻
2. **补充上下文**：如果使用了指代（"那个"、"它"），展开说明
3. **添加过渡**：在 Skill 切换时说明"回到刚才的问题..."
4. **结束语**：适当添加"还有其他问题吗？"

### 示例：

guide_qa 原始回答：
```
小麦获取方式：1.种植 2.商店购买 3.好友赠送
```

CS Agent 整合后：
```
小麦可以通过以下方式获得：

1. **种植**（推荐）：在农场耕地播种...
2. **商店购买**：杂货店每日限购...
3. **好友赠送**：可向好友请求...

还有什么想了解的吗？😊
```

## 异常处理

### 知识库未找到
```
guide_qa: 返回 "信息不足"
CS Agent: "这个问题我暂时不确定，你可以尝试... 或者我可以帮你记录反馈"
```

### Bug 存储失败
```
bug_intake: store_bug.py 返回错误
CS Agent: "信息已记录，稍后会有专人跟进。如果紧急，也可以联系客服邮箱..."
```

### 玩家长时间无响应
```
CS Agent: 检测会话超时
       → 保存当前进度
       → "我暂时离开了，有问题随时叫我"
```

## 配置项

```yaml
# config.yml
cs_agent:
  # 意图识别阈值
  intent_confidence_threshold: 0.7
  
  # 会话超时时间（分钟）
  session_timeout: 30
  
  # 最大追问次数
  max_clarify_rounds: 3
  
  # 官方人设配置
  persona:
    tone: "friendly"  # friendly/professional/casual
    emoji: true
    signature: "农场小助手"
  
  # Skill 调用配置
  skills:
    guide_qa:
      knowledge_base_path: "./knowledge_base"
    bug_intake:
      feishu_config: "./feishu_config.yml"
```
