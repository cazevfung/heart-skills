# 场域毒性评估模型

## 什么是场域毒性

场域毒性不是简单的"负面评论多"，而是指**评论区已经形成了一种自我强化的负面共振腔**——每一条新评论都在重复和强化核心叙事母题，而异质声音被瞬间淹没或排斥。

### 心动小镇案例的场域毒性特征

```
✗ 叙事垄断：所有讨论都围绕"亲日/区别对待"
✗ 情绪共振：愤怒情绪相互放大，形成回声室
✗ 异质排斥：中性/正面评论被攻击或忽视
✗ 符号武器化：语言成为身份政治的表演工具
✗ 信任崩溃：官方任何回应都被解读为"狡辩"
```

---

## 毒性评估维度

### 维度1：叙事垄断指数 (Narrative Monopoly Index)

```python
def calculate_narrative_monopoly(thread_data):
    """
    测量单一叙事母题的主导程度
    0 = 多元叙事并存
    1 = 完全垄断
    """
    # 提取所有评论的叙事母题
    narrative_distribution = {}
    for comment in thread_data:
        motifs = extract_narrative_motifs(comment.text)
        for motif in motifs:
            narrative_distribution[motif] = narrative_distribution.get(motif, 0) + 1
    
    # 计算赫芬达尔-赫希曼指数 (HHI)
    total = sum(narrative_distribution.values())
    hhi = sum((count/total)**2 for count in narrative_distribution.values())
    
    # 检测主导叙事
    dominant_motif = max(narrative_distribution, key=narrative_distribution.get)
    dominant_ratio = narrative_distribution[dominant_motif] / total
    
    return {
        "monopoly_index": hhi,  # 越接近1越垄断
        "dominant_motif": dominant_motif,
        "dominant_ratio": dominant_ratio,
        "narrative_diversity": len(narrative_distribution),
        "is_monopolized": hhi > 0.6 and dominant_ratio > 0.5
    }
```

### 维度2：情绪共振腔强度 (Emotional Resonance Cavity)

```python
def calculate_resonance_cavity(thread_data):
    """
    测量情绪相互放大的程度
    """
    # 构建情绪传播网络
    G = nx.DiGraph()
    
    for i, comment in enumerate(thread_data):
        G.add_node(i, emotion=comment.emotion, intensity=comment.emotion_intensity)
        
        # 检查情绪感染：回复是否继承/放大父评论情绪
        if comment.parent_id:
            parent_idx = find_comment_index(thread_data, comment.parent_id)
            parent_emotion = thread_data[parent_idx].emotion
            
            # 情绪一致性
            emotion_match = (comment.emotion == parent_emotion)
            # 情绪强度放大
            intensity_amplification = comment.emotion_intensity > thread_data[parent_idx].emotion_intensity
            
            if emotion_match and intensity_amplification:
                G.add_edge(parent_idx, i, weight=comment.emotion_intensity)
    
    # 计算共振强度
    resonance_strength = nx.density(G)
    
    # 检测情绪级联（情绪像波浪一样传播）
    cascades = detect_emotion_cascades(G)
    
    return {
        "resonance_strength": resonance_strength,
        "cascade_count": len(cascades),
        "max_cascade_length": max(len(c) for c in cascades) if cascades else 0,
        "is_echo_chamber": resonance_strength > 0.7 and len(cascades) > 3
    }
```

### 维度3：异质声音排斥度 (Heterogeneity Repulsion)

```python
def calculate_heterogeneity_repulsion(thread_data):
    """
    测量异质声音被排斥的程度
    """
    neutral_positive_comments = [
        c for c in thread_data 
        if c.sentiment in ["neutral", "positive"]
    ]
    
    repulsion_signals = []
    for comment in neutral_positive_comments:
        # 检查是否收到负面回复
        replies = get_replies(thread_data, comment.id)
        negative_replies = [r for r in replies if r.sentiment == "negative"]
        
        # 检查是否被忽视（无互动）
        is_ignored = len(replies) == 0 and comment.likes < 2
        
        # 检查是否被攻击
        is_attacked = any(
            contains_attack_language(r.text) 
            for r in replies
        )
        
        repulsion_signals.append({
            "comment_id": comment.id,
            "is_ignored": is_ignored,
            "is_attacked": is_attacked,
            "negative_reply_ratio": len(negative_replies) / len(replies) if replies else 0
        })
    
    # 计算排斥率
    total_hetero = len(neutral_positive_comments)
    if total_hetero == 0:
        return {"repulsion_rate": 1.0, "is_hetero_repelled": True}
    
    repelled_count = sum(
        1 for s in repulsion_signals 
        if s["is_ignored"] or s["is_attacked"]
    )
    
    return {
        "repulsion_rate": repelled_count / total_hetero,
        "hetero_comment_count": total_hetero,
        "repelled_count": repelled_count,
        "is_hetero_repelled": repelled_count / total_hetero > 0.8
    }
```

### 维度4：符号武器化程度 (Symbol Weaponization)

```python
def calculate_symbol_weaponization(thread_data):
    """
    测量语言作为关系武器的程度
    """
    weaponized_patterns = {
        "identity_attack": ["汉奸", "精日", "走狗", "罕见"],
        "moral_judgment": ["又当又立", "装死", "傲慢", "背叛"],
        "conspiracy": ["暗改", "偷偷", "试探", "资本"],
        "us_vs_them": ["我们玩家", "你们官方", "国内", "日本"]
    }
    
    weaponization_scores = {}
    for category, patterns in weaponized_patterns.items():
        count = sum(
            1 for c in thread_data
            if any(p in c.text for p in patterns)
        )
        weaponization_scores[category] = count / len(thread_data)
    
    # 整体武器化程度
    overall_weaponization = sum(weaponization_scores.values()) / len(weaponization_scores)
    
    return {
        "weaponization_scores": weaponization_scores,
        "overall_weaponization": overall_weaponization,
        "is_weaponized": overall_weaponization > 0.4
    }
```

### 维度5：信任余量 (Trust Reserve)

```python
def calculate_trust_reserve(thread_data, historical_data=None):
    """
    测量社区对官方的信任余量
    基于历史互动模式计算
    """
    # 检测信任崩溃信号
    trust_signals = {
        "official_skepticism": 0,  # 对官方声明的怀疑
        "promise_distrust": 0,     # 对承诺的不信任
        "intent_attribution": 0    # 恶意意图归因
    }
    
    skepticism_patterns = ["谁信", "呵呵", "骗鬼", "画饼"]
    promise_patterns = ["上次也说", "承诺", "保证", "没兑现"]
    intent_patterns = ["就是想", "故意", "为了逼氪", "试探底线"]
    
    for comment in thread_data:
        if any(p in comment.text for p in skepticism_patterns):
            trust_signals["official_skepticism"] += 1
        if any(p in comment.text for p in promise_patterns):
            trust_signals["promise_distrust"] += 1
        if any(p in comment.text for p in intent_patterns):
            trust_signals["intent_attribution"] += 1
    
    # 归一化
    total_comments = len(thread_data)
    trust_breakdown = {
        k: v/total_comments for k, v in trust_signals.items()
    }
    
    # 信任余量 = 1 - 信任崩溃程度
    trust_reserve = 1 - max(trust_breakdown.values())
    
    return {
        "trust_reserve": trust_reserve,
        "trust_breakdown": trust_breakdown,
        "is_trust_depleted": trust_reserve < 0.3
    }
```

---

## 综合毒性评分

```python
def calculate_field_toxicity(thread_data, historical_data=None):
    """
    计算场域综合毒性评分
    """
    dimensions = {
        "narrative_monopoly": calculate_narrative_monopoly(thread_data),
        "resonance_cavity": calculate_resonance_cavity(thread_data),
        "heterogeneity_repulsion": calculate_heterogeneity_repulsion(thread_data),
        "symbol_weaponization": calculate_symbol_weaponization(thread_data),
        "trust_reserve": calculate_trust_reserve(thread_data, historical_data)
    }
    
    # 加权综合
    toxicity_score = (
        0.25 * dimensions["narrative_monopoly"]["monopoly_index"] +
        0.20 * dimensions["resonance_cavity"]["resonance_strength"] +
        0.20 * dimensions["heterogeneity_repulsion"]["repulsion_rate"] +
        0.20 * dimensions["symbol_weaponization"]["overall_weaponization"] +
        0.15 * (1 - dimensions["trust_reserve"]["trust_reserve"])
    )
    
    # 毒性等级
    if toxicity_score < 0.3:
        level = "healthy"
        description = "场域健康，多元声音并存"
    elif toxicity_score < 0.5:
        level = "mild"
        description = "轻度毒性，存在局部情绪聚集"
    elif toxicity_score < 0.7:
        level = "moderate"
        description = "中度毒性，叙事开始垄断"
    elif toxicity_score < 0.85:
        level = "severe"
        description = "重度毒性，负面共振腔形成"
    else:
        level = "critical"
        description = "危急毒性，信任完全崩溃"
    
    return {
        "toxicity_score": toxicity_score,
        "toxicity_level": level,
        "description": description,
        "dimensions": dimensions,
        "intervention_urgency": "immediate" if level in ["severe", "critical"] else "planned"
    }
```

---

## 心动小镇案例的毒性评估

```
叙事垄断指数: 0.87 (极高)
- 主导叙事: "亲日/区别对待" (占比68%)
- 次要叙事几乎被完全压制

情绪共振腔: 0.82 (极强)
- 检测到5条情绪级联链
- 最长级联: 12层愤怒情绪放大

异质声音排斥: 0.91 (极高)
- 中性/正面评论: 3条
- 被排斥: 2条被攻击，1条被忽视
- 排斥率: 100%

符号武器化: 0.76 (高)
- 身份攻击: 23% (汉奸、精日)
- 道德审判: 45% (又当又立、傲慢)
- 阴谋论: 34% (暗改、试探)
- 对立框架: 67% (我们vs你们)

信任余量: 0.12 (枯竭)
- 官方怀疑: 45%
- 承诺不信任: 34%
- 恶意归因: 56%

━━━━━━━━━━━━━━━━━━━━━
综合毒性评分: 0.84 (危急)
━━━━━━━━━━━━━━━━━━━━━

状态: 场域已充满毒素，任何官方发言都会被毒性浸染
建议: 暂停公开回应，通过侧翼渠道释放稀释剂
```

---

## 毒性演化追踪

```python
def track_toxicity_evolution(game_id, platform, time_window="7d"):
    """
    追踪场域毒性的时间演化
    """
    snapshots = fetch_field_snapshots(game_id, platform, time_window)
    
    evolution = []
    for snapshot in snapshots:
        toxicity = calculate_field_toxicity(snapshot.data)
        evolution.append({
            "timestamp": snapshot.timestamp,
            "toxicity_score": toxicity["toxicity_score"],
            "level": toxicity["toxicity_level"],
            "dominant_motif": toxicity["dimensions"]["narrative_monopoly"]["dominant_motif"]
        })
    
    # 检测毒性加速/减速
    if len(evolution) >= 2:
        recent = evolution[-1]["toxicity_score"]
        previous = evolution[-2]["toxicity_score"]
        acceleration = recent - previous
        
        return {
            "evolution_curve": evolution,
            "current_trend": "accelerating" if acceleration > 0.1 else "stable" if acceleration > -0.1 else "decelerating",
            "acceleration_rate": acceleration,
            "predicted_next": recent + acceleration
        }
```
