# 舆情监控数据架构设计

## 核心设计理念

从"文本考古学"转向"场域现象学"。数据不是被采集的客体，而是被培育的生态。

### 范式转移

| 传统舆情监控 | 新范式：场域感知 |
|------------|----------------|
| 实体表：用户、帖子、评论 | 关系事件：语境化互动事件(CIE) |
| 情感极性分析 | 叙事拓扑测绘 |
| 统计报告 | 场域状态演化追踪 |
| 抓取-分析-丢弃 | 叙事地层学（长期培育） |

---

## 核心数据单元：语境化互动事件 (CIE)

CIE是系统的原子数据单元，包含四个不可还原的维度：

```
CIE = {
  "cie_id": "uuid",
  "timestamp": "ISO-8601",
  "platform": "taptap|reddit|bilibili|discord|...",
  
  // 维度1：参与体 (Who)
  "participants": {
    "author": {"id": "...", "role": "player|influencer|official|..."},
    "respondents": ["..."],  // 回复链中的参与者
    "amplifiers": ["..."]    // 高互动、高传播节点
  },
  
  // 维度2：叙事物 (What)
  "narrative": {
    "surface_topic": "bug_report|feature_request|complaint|...",
    "narrative_motif": "betrayal|neglect|discrimination|...",
    "narrative_stage": "emergence|consolidation|saturation|closure"
  },
  
  // 维度3：情绪场 (Emotional Field)
  "affective_field": {
    "dominant_emotion": "anger|disappointment|sarcasm|...",
    "emotional_intensity": 0.0-1.0,
    "toxicity_level": 0.0-1.0,
    "resonance_pattern": "echo_chamber|debate|fragmented"
  },
  
  // 维度4：时间拓扑 (When in Narrative Evolution)
  "temporal_topology": {
    "event_phase": "pre_announcement|announcement|peak|aftermath",
    "narrative_momentum": "accelerating|stable|decelerating",
    "intervention_window": "open|closing|closed"
  }
}
```

---

## 存储策略：多模态持久化

### 1. 图数据库（关系拓扑）

存储：玩家之间的回应链、话题汇聚与分流、情绪簇的边界渗透

```cypher
// 节点类型
(:Player {id, role, influence_score})
(:Post {id, platform, timestamp})
(:NarrativeMotif {name, category})
(:EmotionCluster {type, intensity})

// 关系类型
(:Player)-[:AUTHORS]->(:Post)
(:Post)-[:REPLIES_TO]->(:Post)
(:Post)-[:EXPRESSES]->(:NarrativeMotif)
(:Player)-[:AMPLIFIES]->(:Post)
(:EmotionCluster)-[:INFORMS]->(:Post)
```

### 2. 向量数据库（语义嵌入）

存储：叙事母题的向量表示、语境快照的向量指纹

```python
# 叙事母题向量
narrative_vectors = {
  "betrayal_narrative": [0.23, -0.87, 0.12, ...],  # 背叛叙事语义中心
  "neglect_narrative": [0.45, -0.32, 0.78, ...],   # 忽视叙事语义中心
  "discrimination_narrative": [0.91, -0.15, 0.33, ...]  # 歧视叙事语义中心
}

# 语境快照指纹
snapshot_fingerprint = embedding("整个评论区的集体情绪氛围描述")
```

### 3. 时序数据库（场域状态流变）

存储：叙事垄断指数、情绪共振腔谐波、信任余量衰减轨迹

```
measurement: field_state
  tags: platform, game_id, topic_id
  fields:
    - narrative_monopoly_index (0-1)
    - resonance_cavity_frequency
    - trust_reserve_level (0-1)
    - toxicity_saturation (0-1)
    - intervention_window_status
```

### 4. 对象存储（数字民族志档案）

存储：原始内容、截图、完整评论文本、修订历史

```
s3://sentiment-archive/
  {platform}/{game_id}/{date}/{post_id}/
    - raw_content.json
    - screenshot.png
    - revision_history.json
    - full_thread.html
```

---

## 叙事DNA与谱系追踪

### 叙事原型图谱 (Narrative Archetype Graph)

```
元节点：抽象叙事原型
  ├─ :NarrativeArchetype {name: "暗改指控"}
  ├─ :NarrativeArchetype {name: "区别对待"}
  ├─ :NarrativeArchetype {name: "亲日/崇洋"}
  └─ :NarrativeArchetype {name: "背叛核心玩家"}

具体事件实例链接到原型：
  (:CIE {event_id: "heartopia_march_2025"})-[:INSTANTIATES]->(:NarrativeArchetype {name: "亲日/崇洋"})
```

### 跨时间链接 (Cross-Temporal Links)

```cypher
// 当新事件与历史事件相似度超过阈值时自动建立
(:CIE {event_id: "current"})-[:RESEMBLES {similarity: 0.87}]->(:CIE {event_id: "historical_2022"})
```

---

## 语境层化存储 (Stratified Context Storage)

### L0层：地层（原始数据）
- 原始帖子、评论、截图
- **不可修改**
- 存储：对象存储

### L1层：沉积层（叙事提取）
- 识别出的母题、情绪簇、关键节点
- 带处理算法版本标记
- 存储：图数据库 + 向量数据库

### L2层：变质层（场域合成）
- 叙事拓扑图、共振腔分析
- L1数据的聚合与解释
- 存储：图数据库

### L3层：土壤层（决策支持）
- 干预建议、脆弱性评估
- 与具体业务逻辑绑定
- 存储：关系型数据库 / 文档数据库

---

## 干预-反馈数据孪生

每次介入尝试生成**干预事件记录 (IER)**：

```
IER = {
  "ier_id": "uuid",
  "cie_id": "链接到原始场域状态",
  "intervention_type": "micro_test|context_reconstruction|...",
  "intervention_content": "...",
  "timestamp": "...",
  "field_state_before": {...},  // 干预前场域状态快照
  "field_state_after": {...},   // 干预后场域状态快照
  "narrative_entropy_change": 0.0,  // 叙事熵变
  "effectiveness_score": 0.0-1.0
}
```

---

## 双时态数据库结构

所有核心数据带两个时间戳：

- **Valid Time (有效时间)**：数据描述的现实世界时间
- **Transaction Time (事务时间)**：数据被记录到系统的时间

支持**时间旅行查询**：重建"事件发生当天14:30的场域状态"

---

## 平台可延展性设计

### 统一平台接口

```python
class PlatformAdapter:
    def fetch_posts(self, game_id, since):
        """获取帖子列表"""
        pass
    
    def fetch_comments(self, post_id):
        """获取评论树"""
        pass
    
    def normalize_to_cie(self, raw_data):
        """转换为CIE格式"""
        pass
    
    def extract_relationships(self, raw_data):
        """提取关系拓扑"""
        pass
```

### 平台特定字段映射

每个平台有独特的数据结构，通过映射层统一：

```yaml
# taptap_mapping.yaml
post:
  id: "post_id"
  author: "user.name"
  content: "content"
  timestamp: "created_at"
  
comment:
  id: "comment_id"
  parent_id: "reply_to"
  author: "user.name"
  content: "content"
  likes: "like_count"
  
relationships:
  reply_chain: "reply_to"
  like_interaction: "liked_by"
```

---

## 数据血缘与溯源

任何高层分析都可以溯源到原始语境：

```
L3决策建议 
  → 追溯到 L2场域合成 
    → 追溯到 L1叙事提取 
      → 追溯到 L0原始数据
```

每个CIE都带有完整的**数据血缘链**，确保可审计、可复现。

---

## 冷数据的热关联

历史数据不是静态归档，而是定期被**叙事相似度引擎**扫描：

```python
def async_reactivation():
    """
    定期扫描历史数据，当新事件与旧事件在向量空间距离小于阈值时，
    自动建立跨时间链接，提醒运营者参考历史干预记录
    """
    new_event_vector = embed(current_event)
    historical_events = query_all_historical()
    
    for hist in historical_events:
        similarity = cosine_similarity(new_event_vector, hist.vector)
        if similarity > THRESHOLD:
            create_cross_temporal_link(current_event, hist, similarity)
            alert_ops(f"当前事件与{hist.date}的{hist.title}相似度{similarity}")
```

---

## 实施路线图

### Phase 1: 核心架构（当前）
- [x] 数据架构设计文档
- [ ] CIE数据模型实现
- [ ] 平台适配器接口（TapTap先行）

### Phase 2: 单平台验证
- [ ] TapTap数据接入
- [ ] 叙事跃迁检测算法
- [ ] 场域毒性评估

### Phase 3: 多平台扩展
- [ ] Reddit/B站/Discord适配器
- [ ] 跨平台叙事追踪
- [ ] 实时场域监控仪表盘

### Phase 4: 智能化升级
- [ ] 预测性叙事演化模型
- [ ] 自动干预建议生成
- [ ] 反事实模拟引擎
