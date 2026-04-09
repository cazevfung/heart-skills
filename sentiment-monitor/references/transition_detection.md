# 叙事跃迁检测方法论

## 什么是叙事跃迁

叙事跃迁是指议题性质发生**质变**的时刻——从可修复的技术债务，变成不可妥协的价值冲突。

### 心动小镇案例分析

```
技术问题（可修复）
    ↓
"卡建筑bug影响体验"
    ↓
【叙事跃迁点】某高互动评论将技术问题嫁接到民族情绪
    ↓
价值冲突（不可妥协）
    ↓
"亲日游戏区别对待中国玩家"
```

这个跃迁点比任何情感分数都重要，因为它代表了**议题性质的质变**。

---

## 跃迁检测信号

### 信号1：关键词突变

```python
def detect_keyword_mutation(thread_data, window_size=10):
    """
    检测关键词分布的突变点
    """
    # 时间窗口内关键词频率变化
    early_window = thread_data[:window_size]
    late_window = thread_data[-window_size:]
    
    early_keywords = extract_top_keywords(early_window)
    late_keywords = extract_top_keywords(late_window)
    
    # 计算关键词分布的KL散度
    kl_divergence = calculate_kl_divergence(early_keywords, late_keywords)
    
    # 检测新出现的情绪性/价值性关键词
    new_emotional_keywords = set(late_keywords) - set(early_keywords)
    value_keywords = ["亲日", "汉奸", "区别对待", "背叛", "傲慢"]
    
    mutation_score = len(new_emotional_keywords & set(value_keywords)) / len(value_keywords)
    
    return {
        "kl_divergence": kl_divergence,
        "mutation_score": mutation_score,
        "new_keywords": new_emotional_keywords,
        "is_transition": kl_divergence > 0.5 and mutation_score > 0.3
    }
```

### 信号2：情绪强度跳变

```python
def detect_emotion_spike(thread_data):
    """
    检测情绪强度的非线性跳变
    """
    emotion_curve = [comment.emotion_intensity for comment in thread_data]
    
    # 使用变点检测算法（如PELT或CUSUM）
    change_points = detect_change_points(emotion_curve, penalty=10)
    
    # 分析跳变前后的情绪类型变化
    for cp in change_points:
        before = thread_data[cp-5:cp]
        after = thread_data[cp:cp+5]
        
        emotion_shift = {
            "before_dominant": dominant_emotion(before),
            "after_dominant": dominant_emotion(after),
            "intensity_jump": mean_intensity(after) - mean_intensity(before)
        }
        
        if emotion_shift["intensity_jump"] > 0.4:
            return {
                "change_point_index": cp,
                "emotion_shift": emotion_shift,
                "is_anger_escalation": emotion_shift["after_dominant"] == "anger"
            }
```

### 信号3：叙事母题嫁接

```python
def detect_narrative_grafting(thread_data):
    """
    检测技术叙事被嫁接到价值叙事
    """
    for comment in thread_data:
        # 检测是否同时包含技术元素和价值元素
        has_technical = contains_any(comment.text, 
            ["bug", "修复", "卡顿", "穿模", "优化"])
        has_value = contains_any(comment.text,
            ["亲日", "区别对待", "傲慢", "背叛", "崇洋"])
        
        if has_technical and has_value:
            # 检查是否是嫁接句式："A不改，B一句话就改"
            grafting_patterns = [
                r".*不改.*一句话.*改.*",
                r".*不修.*马上.*修.*",
                r"国内.*国外.*",
                r"玩家.*官方.*"
            ]
            
            for pattern in grafting_patterns:
                if re.search(pattern, comment.text):
                    return {
                        "grafting_comment": comment,
                        "pattern_matched": pattern,
                        "technical_topic": extract_technical_topic(comment),
                        "value_topic": extract_value_topic(comment),
                        "is_grafting_point": True
                    }
    
    return {"is_grafting_point": False}
```

### 信号4：关键节点激活

```python
def detect_key_node_activation(thread_data):
    """
    检测高网络中心性节点的激活
    """
    # 构建互动网络
    G = build_interaction_graph(thread_data)
    
    # 计算节点中心性
    centrality = nx.betweenness_centrality(G)
    
    # 识别桥接节点（连接不同子群体）
    bridge_nodes = []
    for node, score in centrality.items():
        if score > 0.8:  # 高中心性阈值
            # 检查该节点是否连接不同群体
            neighbors = list(G.neighbors(node))
            groups = [get_user_group(n) for n in neighbors]
            if len(set(groups)) > 1:  # 连接多个群体
                bridge_nodes.append({
                    "node_id": node,
                    "centrality_score": score,
                    "connected_groups": list(set(groups)),
                    "comment": get_comment_by_author(node)
                })
    
    return bridge_nodes
```

---

## 跃迁点综合判定

```python
def detect_narrative_transition(thread_data):
    """
    综合多种信号判定叙事跃迁
    """
    signals = {
        "keyword_mutation": detect_keyword_mutation(thread_data),
        "emotion_spike": detect_emotion_spike(thread_data),
        "narrative_grafting": detect_narrative_grafting(thread_data),
        "key_node_activation": detect_key_node_activation(thread_data)
    }
    
    # 加权综合评分
    transition_score = (
        0.3 * signals["keyword_mutation"]["mutation_score"] +
        0.25 * (1 if signals["emotion_spike"] else 0) +
        0.3 * (1 if signals["narrative_grafting"]["is_grafting_point"] else 0) +
        0.15 * min(len(signals["key_node_activation"]) / 3, 1.0)
    )
    
    return {
        "transition_detected": transition_score > 0.6,
        "transition_score": transition_score,
        "signals": signals,
        "critical_moment": identify_critical_moment(signals),
        "from_narrative": "technical_issue",
        "to_narrative": signals["narrative_grafting"].get("value_topic", "unknown"),
        "intervention_window": "closing" if transition_score > 0.8 else "open"
    }
```

---

## 心动小镇案例的跃迁检测

```
评论时间线分析：

[早期] 技术反馈为主
- "猫狗挡路bug什么时候修"
- "卡顿问题严重"

[跃迁点] 梦泡泡的评论（62楼）
- "有勇气删氪金，那就退款，别装死又当又立试探老玩家"
- 引入"背叛核心玩家"叙事

[加速] 亲日指控出现（32楼、41楼）
- "立本人一句话就改了"
- "亲日游戏"
- 技术问题完全转化为价值冲突

[饱和] 叙事垄断形成
- 所有新评论都围绕"亲日/区别对待"
- 中性评论被淹没
- 场域毒性达到峰值
```

---

## 干预窗口识别

### 黄金干预时间

叙事尚未完成闭环的脆弱时刻：

```python
def identify_intervention_window(transition_analysis):
    """
    识别干预的最佳时机
    """
    if transition_analysis["transition_score"] < 0.3:
        return {
            "status": "pre_emergence",
            "strategy": "monitor",
            "urgency": "low"
        }
    elif transition_analysis["transition_score"] < 0.6:
        return {
            "status": "emergence",
            "strategy": "early_intervention",
            "urgency": "medium",
            "tactics": ["技术解释", "透明沟通"]
        }
    elif transition_analysis["transition_score"] < 0.8:
        return {
            "status": "consolidation",
            "strategy": "narrative_disruption",
            "urgency": "high",
            "tactics": ["提供反事实", "情感承认", "新事实注入"]
        }
    else:
        return {
            "status": "saturation",
            "strategy": "field_reset",
            "urgency": "critical",
            "tactics": ["暂停回应", "侧翼渠道", "长期信任重建"]
        }
```

---

## LLM辅助跃迁检测

对于复杂案例，使用LLM进行深度分析：

```python
LLM_TRANSITION_PROMPT = """
分析以下评论区内容，识别叙事跃迁点：

[评论内容]
{thread_content}

请回答：
1. 早期讨论的主题是什么？（技术/功能/体验）
2. 后期讨论的主题是什么？（价值/情感/立场）
3. 哪个评论标志着议题性质的质变？
4. 质变是如何发生的？（嫁接/类比/情绪升级）
5. 当前干预窗口状态？（开放/正在关闭/已关闭）

以JSON格式返回分析结果。
"""
```
