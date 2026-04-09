"""
区域化毒性分析器
支持多文化圈的场域毒性评估
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass
from collections import Counter

from regional_dictionary_loader import RegionalDictionaryLoader, load_regional_dictionaries
from dictionary_evolver import DictionaryEvolver


@dataclass
class Comment:
    id: str
    author: str
    text: str
    timestamp: str
    sentiment: str = "neutral"
    likes: int = 0
    replies: List['Comment'] = None
    
    def __post_init__(self):
        if self.replies is None:
            self.replies = []


class RegionalToxicityAnalyzer:
    """区域化场域毒性分析器"""
    
    def __init__(self, region: str, auto_evolve: bool = True):
        """
        Args:
            region: 区域代码 (zh-CN, ja-JP, en-US, etc.)
            auto_evolve: 是否自动演化词典
        """
        self.region = region
        self.loader = RegionalDictionaryLoader()
        self.cluster = self.loader.get_cluster_for_region(region)
        self.dictionaries = load_regional_dictionaries(region)
        self.auto_evolve = auto_evolve
        
        if auto_evolve:
            self.evolver = DictionaryEvolver(self.cluster, region)
    
    def analyze(self, comments: List[Dict]) -> Dict[str, Any]:
        """
        执行区域化毒性分析
        
        Args:
            comments: 评论数据列表
        
        Returns:
            包含区域特定分析结果的字典
        """
        comment_objects = [Comment(**c) for c in comments]
        
        # 1. 执行区域特定的分析
        narrative = self._analyze_narrative(comment_objects)
        toxicity = self._analyze_toxicity(comment_objects)
        emotion = self._analyze_emotion(comment_objects)
        trust = self._analyze_trust(comment_objects)
        
        # 2. 计算综合毒性评分
        toxicity_score = self._calculate_regional_toxicity_score(narrative, toxicity, emotion, trust)
        
        # 3. 判定毒性等级（区域特定阈值）
        level = self._determine_regional_level(toxicity_score)
        
        # 4. 触发词典演化（全自动）
        evolution_result = None
        if self.auto_evolve:
            evolution_result = self.evolver.evolve(comments)
        
        return {
            "region": self.region,
            "cluster": self.cluster,
            "toxicity_score": round(toxicity_score, 2),
            "toxicity_level": level,
            "level_description": self._get_level_description(level),
            "narrative_analysis": narrative,
            "toxicity_dimensions": toxicity,
            "emotion_analysis": emotion,
            "trust_analysis": trust,
            "regional_characteristics": self._get_regional_characteristics(),
            "intervention_recommendation": self._get_regional_intervention(level),
            "dictionary_evolution": evolution_result
        }
    
    def _analyze_narrative(self, comments: List[Comment]) -> Dict:
        """使用区域特定母词分析叙事"""
        if "narrative_motifs" not in self.dictionaries:
            return {"error": "No narrative motifs dictionary found"}
        
        motif_dict = self.dictionaries["narrative_motifs"]
        motifs = motif_dict.get("motifs", [])
        
        # 统计各母词出现频率
        motif_counts = Counter()
        for comment in comments:
            for motif in motifs:
                if any(kw in comment.text for kw in motif.get("keywords", [])):
                    # 区域特定的权重调整
                    weight = self._adjust_weight_for_region(motif)
                    motif_counts[motif["id"]] += weight
        
        # 找出主导叙事
        total = sum(motif_counts.values())
        if total == 0:
            return {
                "dominant_motif": None,
                "monopoly_index": 0,
                "is_monopolized": False
            }
        
        dominant = motif_counts.most_common(1)[0]
        hhi = sum((count/total)**2 for count in motif_counts.values())
        
        return {
            "dominant_motif": {
                "id": dominant[0],
                "name": next(m["name"] for m in motifs if m["id"] == dominant[0]),
                "score": round(dominant[1], 2)
            },
            "monopoly_index": round(hhi, 2),
            "is_monopolized": hhi > 0.6,
            "all_motifs": dict(motif_counts)
        }
    
    def _adjust_weight_for_region(self, motif: Dict) -> float:
        """根据区域调整权重"""
        base_weight = motif.get("weight", 0.5)
        
        # 区域特定调整
        if self.cluster == "east_asia":
            if self.region.startswith("zh"):
                # 中国大陆：民族主义叙事权重更高
                if motif["id"] in ["nationalism", "betrayal_core_players"]:
                    return base_weight * 1.2
            elif self.region.startswith("ja"):
                # 日本：服务态度叙事权重更高
                if motif["id"] in ["service_attitude", "promise_breach"]:
                    return base_weight * 1.2
        
        elif self.cluster == "western":
            # 欧美：商业化/公平性叙事权重更高
            if motif["id"] in ["predatory_monetization", "broken_promises"]:
                return base_weight * 1.1
        
        return base_weight
    
    def _analyze_toxicity(self, comments: List[Comment]) -> Dict:
        """使用区域特定武器化模式分析毒性"""
        if "weaponized_patterns" not in self.dictionaries:
            return {"error": "No weaponized patterns dictionary found"}
        
        weapon_dict = self.dictionaries["weaponized_patterns"]
        categories = weapon_dict.get("categories", {})
        
        category_scores = {}
        for cat_name, cat_data in categories.items():
            count = sum(
                1 for c in comments
                if any(p in c.text for p in cat_data.get("patterns", []))
            )
            category_scores[cat_name] = {
                "ratio": round(count / len(comments), 2),
                "severity": cat_data.get("severity", "medium"),
                "escalation_speed": cat_data.get("escalation_speed", "medium")
            }
        
        overall = sum(s["ratio"] for s in category_scores.values()) / len(category_scores) if category_scores else 0
        
        return {
            "category_scores": category_scores,
            "overall_weaponization": round(overall, 2),
            "is_weaponized": overall > 0.4
        }
    
    def _analyze_emotion(self, comments: List[Comment]) -> Dict:
        """分析情绪（区域特定）"""
        # 按情感分类
        sentiment_groups = {"positive": [], "neutral": [], "negative": []}
        for c in comments:
            sentiment_groups[c.sentiment].append(c)
        
        negative_ratio = len(sentiment_groups["negative"]) / len(comments)
        
        # 检测情绪级联
        cascades = []
        current_cascade = []
        
        for comment in comments:
            if comment.sentiment == "negative":
                current_cascade.append(comment)
            else:
                if len(current_cascade) >= 3:
                    cascades.append(current_cascade)
                current_cascade = []
        
        if len(current_cascade) >= 3:
            cascades.append(current_cascade)
        
        # 区域特定的共振计算
        resonance = self._calculate_regional_resonance(negative_ratio, cascades, len(comments))
        
        return {
            "negative_ratio": round(negative_ratio, 2),
            "cascade_count": len(cascades),
            "max_cascade_length": max(len(c) for c in cascades) if cascades else 0,
            "resonance_strength": round(resonance, 2),
            "is_echo_chamber": resonance > 0.7
        }
    
    def _calculate_regional_resonance(self, negative_ratio: float, cascades: List, total: int) -> float:
        """区域特定的情绪共振计算"""
        base_resonance = negative_ratio * 0.5
        
        # 东亚：级联效应更显著（集体主义文化）
        if self.cluster == "east_asia":
            cascade_factor = min(len(cascades) / 3, 0.3) * 1.2
        else:
            cascade_factor = min(len(cascades) / 5, 0.3)
        
        # 欧美：个体表达权重更高
        if self.cluster == "western":
            individual_factor = negative_ratio * 0.2
        else:
            individual_factor = negative_ratio * 0.1
        
        return min(base_resonance + cascade_factor + individual_factor, 1.0)
    
    def _analyze_trust(self, comments: List[Comment]) -> Dict:
        """使用区域特定信任信号分析"""
        if "trust_signals" not in self.dictionaries:
            return {"error": "No trust signals dictionary found"}
        
        trust_dict = self.dictionaries["trust_signals"]
        signals = trust_dict.get("signals", {})
        
        trust_breakdown = {}
        for signal_name, signal_data in signals.items():
            patterns = signal_data.get("patterns", [])
            count = sum(
                1 for c in comments
                if any(p in c.text for p in patterns)
            )
            trust_breakdown[signal_name] = {
                "ratio": round(count / len(comments), 2),
                "impact": signal_data.get("trust_impact", -0.3),
                "count": count
            }
        
        # 计算信任余量 - 基于加权影响
        total_negative_impact = sum(
            s["ratio"] * abs(s["impact"]) for s in trust_breakdown.values()
        )
        trust_reserve = max(0, 1 - total_negative_impact)
        
        return {
            "trust_reserve": round(trust_reserve, 2),
            "trust_breakdown": trust_breakdown,
            "is_trust_depleted": trust_reserve < 0.3
        }
    
    def _calculate_regional_toxicity_score(self, narrative: Dict, toxicity: Dict, emotion: Dict, trust: Dict) -> float:
        """计算区域特定的综合毒性评分"""
        # 基础权重 - 提高情绪和武器化的权重
        weights = {
            "narrative": 0.20,
            "weaponization": 0.25,
            "resonance": 0.30,
            "trust": 0.25
        }
        
        # 区域特定权重调整
        if self.cluster == "east_asia":
            # 东亚：叙事垄断和情绪共振权重更高
            weights["narrative"] = 0.25
            weights["resonance"] = 0.35
            weights["trust"] = 0.20
        elif self.cluster == "western":
            # 欧美：信任权重更高
            weights["trust"] = 0.35
            weights["weaponization"] = 0.20
        
        # 计算各项得分
        narrative_score = narrative.get("monopoly_index", 0)
        weaponization_score = toxicity.get("overall_weaponization", 0)
        resonance_score = emotion.get("resonance_strength", 0)
        trust_loss = 1 - trust.get("trust_reserve", 1)
        
        # 如果情绪共振极高，整体毒性应该更高
        if emotion.get("is_echo_chamber"):
            resonance_score = min(resonance_score * 1.2, 1.0)
        
        # 如果身份攻击比例高，整体毒性应该更高
        identity_attack = toxicity.get("category_scores", {}).get("identity_attack", {})
        if identity_attack.get("ratio", 0) > 0.3:
            weaponization_score = min(weaponization_score * 1.3, 1.0)
        
        score = (
            weights["narrative"] * narrative_score +
            weights["weaponization"] * weaponization_score +
            weights["resonance"] * resonance_score +
            weights["trust"] * trust_loss
        )
        
        return min(score, 1.0)
    
    def _determine_regional_level(self, score: float) -> str:
        """区域特定的毒性等级判定"""
        # 基础阈值
        if score < 0.3:
            return "healthy"
        elif score < 0.5:
            return "mild"
        elif score < 0.7:
            return "moderate"
        elif score < 0.85:
            return "severe"
        else:
            return "critical"
    
    def _get_level_description(self, level: str) -> str:
        """获取等级描述"""
        descriptions = {
            "healthy": "场域健康，多元声音并存",
            "mild": "轻度毒性，存在局部情绪聚集",
            "moderate": "中度毒性，叙事开始垄断",
            "severe": "重度毒性，负面共振腔形成",
            "critical": "危急毒性，信任完全崩溃"
        }
        return descriptions.get(level, "未知状态")
    
    def _get_regional_characteristics(self) -> Dict:
        """获取区域特征"""
        characteristics = {
            "east_asia": {
                "expression_style": "含蓄到直接（因国家而异）",
                "collective_behavior": "高（集体行动倾向）",
                "key_triggers": ["民族主义", "核心玩家背叛", "服务态度"]
            },
            "western": {
                "expression_style": "直接",
                "collective_behavior": "中（个体表达为主）",
                "key_triggers": ["公平性", "透明度", "契约履行"]
            }
        }
        return characteristics.get(self.cluster, {})
    
    def _get_regional_intervention(self, level: str) -> str:
        """获取区域特定的干预建议"""
        # 基础建议
        base_recommendations = {
            "healthy": "维持现状，定期监控",
            "mild": "关注情绪聚集点，准备预案",
            "moderate": "主动沟通，打断叙事垄断",
            "severe": "暂停公开回应，侧翼渠道稀释",
            "critical": "全面静默，长期信任重建计划"
        }
        
        recommendation = base_recommendations.get(level, "继续监控")
        
        # 区域特定补充
        if self.cluster == "east_asia" and level in ["severe", "critical"]:
            recommendation += " | 东亚特别建议：避免直接对抗，通过KOL/社群领袖间接沟通"
        elif self.cluster == "western" and level in ["severe", "critical"]:
            recommendation += " | 欧美特别建议：提供详细数据和时间线，透明沟通"
        
        return recommendation


def main():
    """命令行入口"""
    import sys
    import io
    
    # 设置UTF-8编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if len(sys.argv) < 3:
        print("Usage: python regional_toxicity_analyzer.py <comments.json> <region>")
        print("Regions: zh-CN, ja-JP, en-US, etc.")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        comments = json.load(f)
    
    region = sys.argv[2]
    
    analyzer = RegionalToxicityAnalyzer(region, auto_evolve=False)
    result = analyzer.analyze(comments)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
