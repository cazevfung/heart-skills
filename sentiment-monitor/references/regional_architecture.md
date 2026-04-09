# 区域化配置架构

## 设计原则

- **方案A**：区域适配器模式
- **分析粒度**：文化圈（东亚、欧美、东南亚等）
- **词典演化**：全自动，AI驱动
- **数据隔离**：逻辑隔离（同一数据库+区域标签）

---

## 文化圈定义

```python
CULTURAL_CLUSTERS = {
    "east_asia": {
        "regions": ["zh-CN", "zh-TW", "zh-HK", "ja-JP", "ko-KR"],
        "characteristics": ["集体主义", "面子文化", "等级敏感"],
        "default_language": "zh"
    },
    "western": {
        "regions": ["en-US", "en-GB", "en-CA", "en-AU", "de-DE", "fr-FR"],
        "characteristics": ["个人主义", "直接表达", "契约精神"],
        "default_language": "en"
    },
    "southeast_asia": {
        "regions": ["th-TH", "vi-VN", "id-ID", "ms-MY", "tl-PH"],
        "characteristics": ["社群导向", "KOL影响力", "情绪化表达"],
        "default_language": "en"  # 多数用英语交流
    },
    "latam": {
        "regions": ["es-MX", "es-AR", "es-CL", "pt-BR"],
        "characteristics": ["热情表达", "家庭观念", "价格敏感"],
        "default_language": "es"
    }
}
```

---

## 区域词典结构

```
references/regional_dictionaries/
├── east_asia/
│   ├── zh-CN/
│   │   ├── narrative_motifs.json      # 叙事母词
│   │   ├── emotion_markers.json       # 情绪标记
│   │   ├── weaponized_patterns.json   # 武器化语言
│   │   └── trust_signals.json         # 信任信号
│   ├── ja-JP/
│   │   └── ... (相同结构)
│   └── ko-KR/
│       └── ...
├── western/
│   ├── en-US/
│   │   └── ...
│   └── de-DE/
│       └── ...
└── _evolution_log/                     # 词典演化日志
    ├── 2026-03-12_zh-CN_add.json
    ├── 2026-03-12_ja-JP_update.json
    └── ...
```

---

## 词典文件格式

### narrative_motifs.json

```json
{
  "version": "2026-03-12",
  "cluster": "east_asia",
  "region": "zh-CN",
  "motifs": [
    {
      "id": "nationalism",
      "name": "民族主义",
      "keywords": ["亲日", "汉奸", "罕见", "崇洋", "区别对待"],
      "weight": 0.9,
      "emotion_polarity": "negative",
      "escalation_pattern": "identity_attack",
      "cross_cluster_equivalents": {
        "western": "favoritism",
        "east_asia_ja": "差別"
      }
    },
    {
      "id": "betrayal_core_players",
      "name": "背叛核心玩家",
      "keywords": ["背刺", "辜负", "心寒", "老玩家", "氪金"],
      "weight": 0.85,
      "emotion_polarity": "negative",
      "escalation_pattern": "moral_judgment",
      "cross_cluster_equivalents": {
        "western": "betrayal",
        "east_asia_ja": "裏切り"
      }
    }
  ],
  "metadata": {
    "last_evolved": "2026-03-12T10:00:00Z",
    "evolution_method": "auto_llm",
    "confidence_threshold": 0.7
  }
}
```

### emotion_markers.json

```json
{
  "version": "2026-03-12",
  "cluster": "east_asia",
  "region": "zh-CN",
  "markers": {
    "direct_anger": {
      "patterns": ["傻逼", "垃圾", "死", "滚"],
      "intensity": 0.9,
      "context": "explicit_insult"
    },
    "sarcasm": {
      "patterns": ["呵呵", "真棒", "666", "[表情_微笑]"],
      "intensity": 0.6,
      "context": "passive_aggressive"
    },
    "disappointment": {
      "patterns": ["失望", "心寒", "退游", "卸载"],
      "intensity": 0.7,
      "context": "withdrawal_threat"
    }
  }
}
```

### weaponized_patterns.json

```json
{
  "version": "2026-03-12",
  "cluster": "east_asia",
  "region": "zh-CN",
  "categories": {
    "identity_attack": {
      "patterns": ["汉奸", "精日", "走狗", "罕见"],
      "severity": "critical",
      "escalation_speed": "fast"
    },
    "moral_judgment": {
      "patterns": ["又当又立", "装死", "傲慢", "恶心"],
      "severity": "high",
      "escalation_speed": "medium"
    },
    "conspiracy": {
      "patterns": ["暗改", "偷偷", "试探", "资本"],
      "severity": "medium",
      "escalation_speed": "slow"
    }
  }
}
```

### trust_signals.json

```json
{
  "version": "2026-03-12",
  "cluster": "east_asia",
  "region": "zh-CN",
  "signals": {
    "skepticism": {
      "patterns": ["谁信", "呵呵", "骗鬼", "画饼"],
      "trust_impact": -0.3
    },
    "promise_distrust": {
      "patterns": ["上次也说", "承诺", "保证", "没兑现"],
      "trust_impact": -0.4
    },
    "intent_attribution": {
      "patterns": ["就是想", "故意", "为了逼氪", "试探底线"],
      "trust_impact": -0.5
    }
  }
}
```

---

## 词典自动演化流程

```python
class DictionaryEvolver:
    """词典自动演化器 - 全自动AI驱动"""
    
    def __init__(self, cluster: str, region: str):
        self.cluster = cluster
        self.region = region
        self.dictionary_path = f"references/regional_dictionaries/{cluster}/{region}/"
    
    def evolve(self, recent_comments: List[Comment], high_interaction_threshold: int = 50):
        """
        自动演化词典
        """
        # 1. 筛选高互动评论
        high_interaction = [
            c for c in recent_comments 
            if c.likes + len(c.replies) > high_interaction_threshold
        ]
        
        # 2. LLM提取候选词
        candidates = self._extract_candidates_with_llm(high_interaction)
        
        # 3. 向量聚类去重
        clustered_candidates = self._cluster_candidates(candidates)
        
        # 4. 与现有词典对比
        new_candidates = self._filter_existing(clustered_candidates)
        
        # 5. 自动入库（无人工审核）
        for candidate in new_candidates:
            self._add_to_dictionary(candidate)
        
        # 6. 记录演化日志
        self._log_evolution(new_candidates)
        
        return {
            "added_count": len(new_candidates),
            "added_items": new_candidates,
            "evolution_timestamp": datetime.now().isoformat()
        }
    
    def _extract_candidates_with_llm(self, comments: List[Comment]) -> List[Dict]:
        """
        使用LLM从评论中提取候选词
        """
        prompt = f"""
分析以下{self.region}区域游戏评论，提取该社区特有的表达方式：

[评论样本]
{self._format_comments_for_llm(comments)}

请识别：
1. 新兴的叙事母题（玩家讨论的核心议题类型）
2. 新出现的情绪表达方式
3. 新出现的攻击性/武器化语言模式
4. 新出现的信任崩溃信号

对每项给出：
- 关键词/模式
- 置信度（0-1）
- 示例句子
- 建议权重

只返回置信度>0.7的项。
"""
        
        response = call_llm(prompt)
        return parse_llm_response(response)
    
    def _cluster_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """
        向量聚类去重
        """
        embeddings = [embed(c["keyword"]) for c in candidates]
        
        # 使用HDBSCAN或KMeans聚类
        clusters = hdbscan_cluster(embeddings, min_cluster_size=2)
        
        # 每个聚类选置信度最高的代表
        representatives = []
        for cluster_id in set(clusters):
            if cluster_id == -1:  # 噪声点
                continue
            cluster_members = [c for i, c in enumerate(candidates) if clusters[i] == cluster_id]
            best = max(cluster_members, key=lambda x: x["confidence"])
            representatives.append(best)
        
        return representatives
    
    def _add_to_dictionary(self, candidate: Dict):
        """
        自动添加到词典
        """
        dictionary_file = f"{self.dictionary_path}{candidate['category']}.json"
        
        with open(dictionary_file, 'r', encoding='utf-8') as f:
            dictionary = json.load(f)
        
        # 添加新项
        if candidate["category"] == "narrative_motifs":
            dictionary["motifs"].append({
                "id": generate_id(candidate["keyword"]),
                "name": candidate["description"],
                "keywords": [candidate["keyword"]] + candidate.get("variants", []),
                "weight": candidate["suggested_weight"],
                "emotion_polarity": candidate["emotion"],
                "auto_added": True,
                "added_at": datetime.now().isoformat()
            })
        
        # 保存
        dictionary["metadata"]["last_evolved"] = datetime.now().isoformat()
        
        with open(dictionary_file, 'w', encoding='utf-8') as f:
            json.dump(dictionary, f, ensure_ascii=False, indent=2)
```

---

## CIE数据模型更新（加入区域维度）

```python
CIE = {
    "cie_id": "uuid",
    "timestamp": "ISO-8601",
    "platform": "taptap|reddit|twitter|...",
    
    # 新增：区域维度
    "regional_context": {
        "cluster": "east_asia",           # 文化圈
        "region": "zh-CN",                # 具体区域
        "language": "zh",                 # 语言
        "platform_regional": "taptap_cn"  # 平台+区域组合
    },
    
    # 参与体
    "participants": {
        "author": {
            "id": "...",
            "role": "player|influencer|official",
            "regional_indicators": {        # 新增
                "writing_style": "direct_confrontational",
                "cultural_markers": ["集体主义"]
            }
        },
        "respondents": ["..."],
        "amplifiers": ["..."]
    },
    
    # 叙事物
    "narrative": {
        "surface_topic": "bug_report|...",
        "narrative_motif": "betrayal|...",
        "narrative_stage": "emergence|...",
        "regional_motif_mapping": {         # 新增：跨区域母题映射
            "local_id": "nationalism",
            "cross_cluster_equivalents": {
                "western": "favoritism",
                "east_asia_ja": "差別"
            }
        }
    },
    
    # 情绪场
    "affective_field": {
        "dominant_emotion": "anger|...",
        "emotional_intensity": 0.0-1.0,
        "toxicity_level": 0.0-1.0,
        "resonance_pattern": "echo_chamber|...",
        "regional_emotion_style": "direct_confrontational"  # 新增
    },
    
    # 时间拓扑
    "temporal_topology": {
        "event_phase": "pre_announcement|...",
        "narrative_momentum": "accelerating|...",
        "intervention_window": "open|...",
        "regional_timing": {                # 新增：区域特定时机
            "local_hour": 14,               # 当地时间
            "is_work_hours": True,          # 是否工作时间
            "cultural_timing": "evening_leisure"  # 文化语境时机
        }
    }
}
```

---

## 区域化分析器改造

```python
class RegionalAnalyzer:
    """区域化分析器"""
    
    def __init__(self, cluster: str, region: str):
        self.cluster = cluster
        self.region = region
        self.dictionary_loader = RegionalDictionaryLoader(cluster, region)
        self.evolver = DictionaryEvolver(cluster, region)
    
    def analyze(self, comments: List[Comment]) -> Dict:
        """
        执行区域化分析
        """
        # 1. 加载区域词典
        dictionaries = self.dictionary_loader.load_all()
        
        # 2. 执行区域特定分析
        narrative = self._analyze_narrative(comments, dictionaries["narrative_motifs"])
        emotion = self._analyze_emotion(comments, dictionaries["emotion_markers"])
        toxicity = self._analyze_toxicity(comments, dictionaries)
        
        # 3. 触发词典演化（全自动）
        evolution_result = self.evolver.evolve(comments)
        
        return {
            "cluster": self.cluster,
            "region": self.region,
            "narrative_analysis": narrative,
            "emotion_analysis": emotion,
            "toxicity_analysis": toxicity,
            "dictionary_evolution": evolution_result
        }
    
    def _analyze_narrative(self, comments, motif_dictionary):
        """
        使用区域特定母词词典分析叙事
        """
        # 区域特定的权重调整
        if self.cluster == "east_asia":
            # 东亚：民族主义叙事权重更高
            nationalism_weight = 1.2
        elif self.cluster == "western":
            # 欧美：契约/公平叙事权重更高
            nationalism_weight = 0.6
        else:
            nationalism_weight = 1.0
        
        # ... 分析逻辑
```

---

## 实施检查清单

### Phase 1.5: 区域化基础

- [ ] 创建 `references/regional_dictionaries/` 目录结构
- [ ] 创建 `east_asia/zh-CN/` 初始词典（从现有硬编码迁移）
- [ ] 创建 `east_asia/ja-JP/` 初始词典（需要日本游戏案例填充）
- [ ] 创建 `western/en-US/` 初始词典
- [ ] 更新CIE数据模型，加入`regional_context`字段
- [ ] 改造`toxicity_analyzer.py`，支持`--region`参数
- [ ] 改造`transition_detector.py`，支持`--region`参数

### Phase 2: 自动演化

- [ ] 实现`DictionaryEvolver`类
- [ ] 实现LLM候选词提取prompt
- [ ] 实现向量聚类去重
- [ ] 实现自动入库逻辑
- [ ] 实现演化日志记录
- [ ] 添加演化效果评估（对比分析质量变化）

### Phase 3: 跨区域分析

- [ ] 实现母题跨文化圈映射
- [ ] 实现跨区域叙事传播追踪
- [ ] 实现区域对比分析（同一事件在不同区域的表现差异）

---

## 日本区域优先实施说明

**为什么先做日本**：
1. 数据可获取（TapTap有日服玩家，Reddit有英文讨论日本游戏）
2. 文化差异显著（含蓄vs直接，适合验证区域化有效性）
3. 近期案例丰富（可以找几个日本游戏的舆情事件验证）

**日本区域特定考量**：
- **敬语讽刺**：「お疲れ様です」「なるほど」在特定语境下是负面信号
- **撤回威胁**：「退坑」在日语中表达更含蓄，可能是「もうやめます」
- **集体行动**：日本玩家更倾向于组织化请愿，而非评论区爆发

**需要收集的日本游戏案例**：
- 《原神》日服特定争议
- 《明日方舟》日服运营事件
- 《雀魂》相关舆情
