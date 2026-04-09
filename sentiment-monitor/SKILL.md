---
name: sentiment-monitor
description: 游戏舆情监控系统，用于检测评论区叙事跃迁、评估场域毒性、识别干预窗口。从"文本考古�?转向"场域现象�?，超越传统情感分析，捕捉议题质变的临界时刻。当需要分析游戏社区舆情、识别危机爆发前兆、评估玩家情绪场域状态时触发。支持多平台数据聚合，提供叙事地层学视角的长期演化追踪�?---

# 舆情监控 (Sentiment Monitor)

## 核心理念

传统舆情监控�?温度计测量海�?——统计好评率差评率毫无意义。真正危险的不是某条具体差评，而是**评论区形成的自我强化负面共振�?*�?
本系统采�?*场域现象�?*方法�?- 不分析单条评论情感极�?- 关注**叙事跃迁**（议题性质质变的时刻）
- 评估**场域毒�?*（负面共振腔强度�?- 识别**干预窗口**（叙事尚未闭环的脆弱时刻�?
## 核心输出格式（简化版�?
基于运营决策需求，系统输出三个核心模块�?
### 1. 早期预警指标 (Early Warning Metrics)

| 指标 | 定义 | 触发阈�?| 用�?|
|------|------|---------|------|
| **毒性动�?* (Toxicity Momentum) | 场域毒性变化的加速度 | 连续 2 周期上升 | 在毒性爆发前预警 |
| **叙事凝聚�?* (Narrative Cohesion) | 分散抱怨汇聚成单一叙事的程�?| <0.3 �?>0.6 的跳�?| 检测议题质变临界点 |
| **情绪极化速度** (Polarization Velocity) | 中立声音消失的速度 | 一周期内下�?>30% | 判断场域是否正在封闭 |

**输出示例**�?```json
{
  "early_warning": {
    "toxicity_momentum": 0.18,
    "momentum_trend": "rising",
    "periods_rising": 2,
    "alert_level": "yellow",
    "narrative_cohesion": {
      "current": 0.58,
      "previous": 0.34,
      "jump_detected": true
    },
    "ai_assessment": "玩家�?版本延期'的不满正在从分散吐槽转向'官方不守承诺'的统一叙事",
    "recommended_action": "6 小时内官方回应，避免叙事闭环"
  }
}
```

### 2. 去情绪玩家诉�?(De-escalated Player Insights)

**不是�?* "玩家很生�?  
**而是�?* 表面情绪 �?底层诉求 �?隐藏 nuance

| 表面情绪 | 底层诉求 | 隐藏 nuance | 建议回应方向 |
|---------|---------|------------|------------|
| "又延期，垃圾运营" | 需要可预期的时间表 | 不是反对延期，是反对"临时通知" | 提前沟�?+ 明确里程�?|
| "日服福利更好" | 要求公平对待 | 核心玩家感到被背�?| 强调全球统一规划 |
| "bug 修了一个月还没�? | 需要进度透明 | 不知�?在修�?是真在修还是敷衍 | 定期进度更新 |

**AI 提取逻辑�?*
- 识别高互动评论中的建设性内�?- 过滤纯情绪表�?- 聚类相似诉求
- 标注每个诉求的影响范�?
### 3. 影响力分�?(Signal Prioritization)

```
🔴 高影响力信号（必须回应）
   - 核心玩家群体中的建设性批�?   - 被大量引用的"总结�?作�?   - 跨平台传播的关键节点
   �?建议：官方直接回应或私信沟�?
🟡 中影响力信号（观察）
   - 有具体建议但情绪较重的玩�?   - 新兴 KOL 的试探性发�?   �?建议：监控趋势，准备回应素材

🟢 低影响力信号（忽略）
   - 纯情绪发�?   - 重复已有观点的附�?   �?建议：不回应，避免放�?```

**影响力计算公式（可配置权重）�?*
```
impact_score = (followers_count * 0.3) + 
               (engagement_rate * 0.4) + 
               (historical_accuracy * 0.2) + 
               (cross_platform_presence * 0.1)
```

## 工作流程

```
┌─────────────────────────────────────────────────────────────�?�? Phase 1: 数据接入                                          �?�? - 从各平台采集原始数据（TapTap/Reddit/B�?Discord...�?     �?�? - 统一转换为CIE（语境化互动事件）格�?                       �?�? - 存入多模态存储（�?向量/时序/对象存储�?                   �?└─────────────────────────────────────────────────────────────�?                              �?┌─────────────────────────────────────────────────────────────�?�? Phase 2: 叙事分析                                          �?�? - 检测叙事跃迁点（技术问题→价值冲突的质变�?                 �?�? - 识别关键节点（高影响力评论、桥接节点）                     �?�? - 追踪叙事母题演化                                         �?└─────────────────────────────────────────────────────────────�?                              �?┌─────────────────────────────────────────────────────────────�?�? Phase 3: 场域评估                                          �?�? - 计算叙事垄断指数                                         �?�? - 测量情绪共振腔强�?                                      �?�? - 评估异质声音排斥�?                                      �?�? - 检测符号武器化程度                                       �?�? - 计算信任余量                                             �?└─────────────────────────────────────────────────────────────�?                              �?┌─────────────────────────────────────────────────────────────�?�? Phase 4: 决策支持                                          �?�? - 判定干预窗口状态（开�?正在关闭/已关闭）                   �?�? - 推荐干预策略                                             �?�? - 预测叙事演化方向                                         �?└─────────────────────────────────────────────────────────────�?```

## 快速开�?
### 区域化分析（推荐�?
```python
# 加载评论数据
comments = load_comments("taptap_post_12345.json")

# 区域化场域毒性分�?from scripts.regional_toxicity_analyzer import RegionalToxicityAnalyzer

# 分析中国大陆区域
analyzer = RegionalToxicityAnalyzer(region="zh-CN", auto_evolve=True)
result = analyzer.analyze(comments)

# 分析日本区域
analyzer_jp = RegionalToxicityAnalyzer(region="ja-JP", auto_evolve=True)
result_jp = analyzer_jp.analyze(comments_jp)

# 分析欧美区域
analyzer_us = RegionalToxicityAnalyzer(region="en-US", auto_evolve=True)
result_us = analyzer_us.analyze(comments_us)
```

### 命令行使�?
```bash
# 区域化毒性分�?python scripts/regional_toxicity_analyzer.py comments.json zh-CN
python scripts/regional_toxicity_analyzer.py comments.json ja-JP
python scripts/regional_toxicity_analyzer.py comments.json en-US

# 叙事跃迁检�?python scripts/transition_detector.py comments.json

# 基础场域毒性评估（无区域化�?python scripts/toxicity_analyzer.py comments.json
```

## TapTap 数据采集（自然语言触发�?
当用户要求抓�?TapTap 帖子/评论时，**根据用户自然语言只执行一条命�?*：以 game_crawl �?crawl_runner 为统一入口，用 `exec` 工具调用 `python "d:\App Dev\openclaw-main\skills\game_crawl/scripts/crawl_runner.py"` 并传入推断出的参数�?*不要分步执行、不要多�?exec、不要先抓列表再逐条抓详�?*。爬取可能较久，请为 exec 设置足够长的超时（例�?600000 ms）。唯一消�?token 的时刻是「理解用�?+ 生成这一条命令」；执行期间不再调用模型。TapTap 遵循�?Reddit 相同的单条指令规范，详见 game_crawl �?`references/single_command_crawl_requirement.md`�?
**超时与进度（�?Agent 判断是否中断）：** 脚本会定期向 stderr 输出心跳行（`[taptap_forum] heartbeat phase=...` �?`[taptap_enhanced] heartbeat phase=...`），默认�?60 秒一次（可通过环境变量 `TAPTAP_HEARTBEAT_INTERVAL_SEC` 调整）�?*建议**：用「超�?N 分钟无任�?stderr 输出」作为超时条件，而不是固�?15 分钟总时长——只要持续有日志就说明任务未中断。若出现反爬或分�?评论嵌套卡住，脚本会输出诊断信息：`possible_antiscrape`（页面标题含验证/人机等）、`possible_stuck_or_antiscrape`（列表多轮滚动无新帖）、`possible_stuck no new comments` / `no new reply buttons`（评论或嵌套回复加载无进展）。Agent 可根据这些关键字判断是反爬、分页卡住还是评论嵌套卡住�?
**入口命令示例�?*
```bash
python "d:\App Dev\openclaw-main\skills\game_crawl/scripts/crawl_runner.py" --game <game_key> --platforms taptap --data-types forum_posts --limit <N>
```
�?`d:\App Dev\openclaw-main\skills\game_crawl` 替换�?game_crawl skill 所在目录的实际路径。结果写�?game_crawl �?data 目录（snapshots + merged）；sentiment-monitor 分析时从该目录或通过 data_manager 读取 merged �?forum_posts（含评论）�?
### 可调变量

| 变量 | 来源/命令�?| 含义 | 默认/说明 |
|------|-------------|------|-----------|
| **game_key** | crawl_runner `--game` | 游戏�?game_registry 中的 key | 需在游戏注册表中配�?`platforms.taptap.target`（app_id），�?heartopia 对应 45213 |
| **limit** | crawl_runner `--limit` | 最多抓取的帖子数（含评论） | 默认 30；用户说「最�?100 条」→ 100 |

### 游戏�?�?app_id 对照（便于从用户话中推断 game 与注册表�?
| 游戏�?| app_id（taptap.target�?|
|--------|-------------------------|
| 心动小镇 | 45213 |

用户说游戏名时优先查上表；若用户直接给出数字�?URL 中的 ID，则用该 ID。游戏注册表中需存在对应 game_key �?`platforms.taptap.target` 为该 app_id�?
### 单次执行示例

- 用户：「抓取心动小�?TapTap 论坛帖最�?50 条�? 
  �?一条命令：`python "d:\App Dev\openclaw-main\skills\game_crawl/scripts/crawl_runner.py" --game heartopia --platforms taptap --data-types forum_posts --limit 50`

- 用户：「抓�?45213 �?TapTap 帖子最�?30 条�? 
  �?一条命令：`python "d:\App Dev\openclaw-main\skills\game_crawl/scripts/crawl_runner.py" --game heartopia --platforms taptap --data-types forum_posts --limit 30`  
  （limit 未指定时用默�?30；game_key 需在注册表中配�?taptap.target=45213。）

## Reddit 数据采集（自然语言触发�?
当用户要求抓�?Reddit 帖子/评论时，**根据用户自然语言只执行一条命�?*：以 game_crawl �?crawl_runner 为统一入口，用 `exec` 工具调用 `python "d:\App Dev\openclaw-main\skills\game_crawl/scripts/crawl_runner.py"` 并传入推断出的参数�?*不要分步执行、不要多�?exec、不要先抓列表再逐条抓详�?*。爬取可能较久，请为 exec 设置足够长的超时（例�?600000 ms）。唯一消�?token 的时刻是「理解用�?+ 生成这一条命令」；执行期间不再调用模型。Reddit 遵循�?TapTap 相同的单条指令规范，详见 game_crawl �?`references/single_command_crawl_requirement.md`�?
**入口命令示例�?*
```bash
python "d:\App Dev\openclaw-main\skills\game_crawl/scripts/crawl_runner.py" --game <game_id> --platforms reddit --data-types forum_posts --limit <N>
```
�?`d:\App Dev\openclaw-main\skills\game_crawl` 替换�?game_crawl skill 所在目录的实际路径�?
### 可调变量

| 变量 | 来源/命令�?| 含义 | 默认/说明 |
|------|-------------|------|-----------|
| **subreddit** | game_registry `platforms.reddit.target` | 子版名称 | 需在游戏注册表中先配置，不可由用户自然语言覆盖 |
| **limit** | crawl_runner `--limit` | 最多抓取的帖子�?| 默认 30；用户说「最�?100 条」→ 100 |
| **days** | 当前 crawl_runner 不传 | 仅保留最�?N 天的帖子 | 若用户说「过去一年」等，可提示：直接调�?reddit.py 时可�?`--days 365`；后�?crawl_runner 支持后可在此�?`--days` |

### 单次执行示例

- 用户：「抓 heartopia �?Reddit 最�?50 条�? 
  �?一条命令：`python "d:\App Dev\openclaw-main\skills\game_crawl/scripts/crawl_runner.py" --game heartopia --platforms reddit --data-types forum_posts --limit 50`

- 用户：「抓取心动小�?Reddit 论坛帖�? 
  �?一条命令：`python "d:\App Dev\openclaw-main\skills\game_crawl/scripts/crawl_runner.py" --game heartopia --platforms reddit --data-types forum_posts --limit 30`  
  （limit 未指定时用默�?30。）

## 核心概念

### 语境化互动事�?(CIE)

系统的原子数据单元，包含四个维度�?- **参与�?*：谁参与了互�?- **叙事�?*：讨论的核心是什�?- **情绪�?*：在什么情感氛围内
- **时间拓扑**：在叙事演化的哪个阶�?
详见 [references/data_architecture.md](references/data_architecture.md)

### 叙事跃迁

议题性质发生**质变**的时刻——从可修复的技术债务，变成不可妥协的价值冲突�?
**检测信�?*�?1. 关键词突变（技术词→价值词�?2. 情绪强度跳变
3. 叙事母题嫁接�?A不改，B一句话就改"�?4. 关键节点激�?
详见 [references/transition_detection.md](references/transition_detection.md)

### 场域毒�?
评论区形成的**自我强化负面共振�?*——每条新评论都强化核心叙事，异质声音被淹没�?
**评估维度**�?- 叙事垄断指数（单一叙事主导程度�?- 情绪共振腔强度（情绪相互放大�?- 异质声音排斥度（中�?正面评论被攻�?忽视�?- 符号武器化程度（语言成为关系武器�?- 信任余量（社区对官方的信任储备）

详见 [references/field_toxicity.md](references/field_toxicity.md)

## 区域化支�?
### 文化圈划�?
| 文化�?| 包含区域 | 特征 |
|--------|---------|------|
| **东亚** (east_asia) | zh-CN, zh-TW, ja-JP, ko-KR | 集体主义、面子文化、等级敏�?|
| **欧美** (western) | en-US, en-GB, de-DE, fr-FR | 个人主义、直接表达、契约精�?|
| **东南�?* (southeast_asia) | th-TH, vi-VN, id-ID | 社群导向、KOL影响力、情绪化 |
| **拉美** (latam) | es-MX, pt-BR | 热情表达、家庭观念、价格敏�?|

### 区域词典结构

```
references/regional_dictionaries/
├── east_asia/
�?  ├── zh-CN/              # 中国大陆
�?  �?  ├── narrative_motifs.json
�?  �?  ├── weaponized_patterns.json
�?  �?  └── trust_signals.json
�?  └── ja-JP/              # 日本
�?      └── ...
├── western/
�?  └── en-US/              # 美国/英语�?�?      └── ...
└── _evolution_log/         # 词典演化日志
```

### 词典自动演化

系统自动从数据中学习和更新词典：

```python
from scripts.dictionary_evolver import DictionaryEvolver

# 创建演化�?evolver = DictionaryEvolver(cluster="east_asia", region="zh-CN")

# 执行演化（全自动，无人工审核�?result = evolver.evolve(comments, high_interaction_threshold=50)

# 查看演化结果
print(f"新增词条: {result['added_count']}")
print(f"演化时间: {result['timestamp']}")
```

**演化流程**�?1. 筛选高互动评论（点�?回复 > 阈值）
2. LLM提取候选词（新兴叙事母题、情绪标记、武器化模式�?3. 向量聚类去重
4. 自动入库
5. 记录演化日志

详见 [references/regional_architecture.md](references/regional_architecture.md)

## 数据架构

### 多模态存储策�?
| 存储类型 | 用�?| 技术选型 |
|---------|------|---------|
| 图数据库 | 关系拓扑（回应链、情绪簇�?| Neo4j / TigerGraph |
| 向量数据�?| 语义嵌入（叙事母题向量） | Pinecone / Milvus |
| 时序数据�?| 场域状态流�?| TimescaleDB / InfluxDB |
| 对象存储 | 原始内容归档 | S3 / MinIO |

### 语境层化存储

- **L0层（地层�?*：原始数据，不可修改
- **L1层（沉积层）**：叙事提取结果，带算法版本标�?- **L2层（变质层）**：场域合成分�?- **L3层（土壤层）**：决策支持数�?
### CIE数据模型（含区域维度�?
```python
CIE = {
    "cie_id": "uuid",
    "timestamp": "ISO-8601",
    "platform": "taptap",
    
    # 区域维度
    "regional_context": {
        "cluster": "east_asia",      # 文化�?        "region": "zh-CN",           # 具体区域
        "language": "zh"             # 语言
    },
    
    # 参与体、叙事物、情绪场、时间拓�?..
}
```

详见 [references/data_architecture.md](references/data_architecture.md)

## 平台可延展�?
### 统一适配器接�?
```python
class PlatformAdapter:
    def fetch_posts(self, game_id, since): pass
    def fetch_comments(self, post_id): pass
    def normalize_to_cie(self, raw_data): pass
    def extract_relationships(self, raw_data): pass
```

### 已支�?计划支持平台

- [x] TapTap（优先实现）
- [x] Reddit
- [ ] Bilibili
- [ ] Discord
- [ ] 小红�?- [ ] YouTube
- [ ] QQ频道

## 典型应用场景

### 场景1：实时监控预�?
**输入**：过�?30 分钟的新评论  
**输出**�?```
🟡 预警：毒性动量连�?2 周期上升 (+0.18)
   叙事凝聚度：0.34 �?0.58（快速汇聚中�?   
   AI 判断：玩家对"版本延期"的不满正在从分散吐槽
   转向"官方不守承诺"的统一叙事
   
   建议�? 小时内回应，避免窗口关闭
   
   高影响力信号�?   - @小镇老玩家：提出具体改进建议�?56�?34回复�?   - @HeartopiaFan：跨平台发帖（Reddit 42 upvotes�?```

### 场景2：版本更新舆情追�?
**输入**：版本更新前后多周期数据  
**输出**�?- 毒性动量趋势图
- 叙事演化路径
- 干预措施效果评估

### 场景3：长期态势感知

**输入**：历史舆情数�? 
**分析**�?- 建立叙事原型图谱
- 识别 recurring cultural patterns
- 预测未来危机风险�?
## 与现有Skill的协�?
```
game_crawl ──�?原始数据采集
     �?     �?sentiment_monitor ──�?叙事分析/场域评估
     �?     �?game_report ──�?结构化报告生�?     �?     �?crisis_management ──�?应对策略建议
```

## 实施路线�?
### Phase 1: 核心架构（当前）
- [x] 数据架构设计文档
- [x] CIE数据模型定义
- [x] 叙事跃迁检测算�?- [x] 场域毒性评估模�?
### Phase 1.5: 区域化基础（当前）
- [x] 区域化架构设�?- [x] 文化圈定义（东亚/欧美/东南�?拉美�?- [x] 区域词典框架
- [x] 中国大陆词典 (zh-CN)
- [x] 日本词典 (ja-JP)
- [x] 美国词典 (en-US)
- [x] 区域化分析器
- [x] 词典自动演化�?
### Phase 2: 单平台验�?- [x] 接入game_crawl的TapTap数据
- [ ] 验证心动小镇案例（中国大陆）
- [ ] 收集日本游戏案例验证
- [ ] 输出分析报告模板

### Phase 3: 多平台扩�?- [ ] Reddit/B�?Discord适配�?- [ ] 跨平台叙事追�?- [ ] 跨区域叙事映�?- [ ] 实时场域监控仪表�?
### Phase 4: 智能化升�?- [ ] 预测性叙事演化模�?- [ ] 自动干预建议生成
- [ ] 反事实模拟引�?
## 注意事项

### 关于数据质量

- 本系统依赖高质量的评论数据（包含回复链、点赞数、时间戳�?- 数据缺失会影响关系拓扑分析准确�?- 建议�?game_crawl 配合，确保数据完整性。TapTap 论坛数据（含评论）现统一�?game_crawl �?`taptap_forum.py` 产出，请通过 crawl_runner 拉取�?
### 关于分析局�?
- 当前实现基于规则+统计方法，复杂案例需LLM辅助
- 叙事母词词典需要针对具体游�?社区持续更新
- 跨文化语境（如中日韩玩家社区）需要本地化调整

### 关于伦理边界

- 本系统用�?*理解**社区情绪，而非**操控**舆论
- 干预建议聚焦�?*修复信任**，而非**压制批评**
- 所有分析应透明可审计，避免黑箱操作

## 参考资�?
- [数据架构设计](references/data_architecture.md)
- [叙事跃迁检测方法论](references/transition_detection.md)
- [场域毒性评估模型](references/field_toxicity.md)
- [区域化架构设计](references/regional_architecture.md)

## 区域词典参�?
### 已配置区�?
| 区域 | 文化�?| 状�?| 特色考量 |
|------|--------|------|---------|
| zh-CN | 东亚 | �?已配�?| 民族主义叙事权重高、直接对抗表�?|
| ja-JP | 东亚 | �?已配�?| 敬语讽刺、含蓄表达、服务态度敏感 |
| en-US | 欧美 | �?已配�?| 直接批评、契约精神、公平性敏�?|

### 词典内容

- **叙事母词** (narrative_motifs): 各区域特有的核心议题类型
- **武器化模�?* (weaponized_patterns): 攻击�?讽刺性语言模式
- **信任信号** (trust_signals): 表达对官方不信任的特定说�?- **情绪标记** (emotion_markers): 区域特定的情绪表达方�?
### 跨区域母题映�?
示例�?- 中国大陆 "民族主义" �?日本 "差別" �?欧美 "favoritism"
- 中国大陆 "背叛核心玩家" �?日本 "裏切�? �?欧美 "betrayal"
