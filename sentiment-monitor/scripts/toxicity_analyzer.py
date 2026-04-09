"""
场域毒性评估脚本
用于评估评论区的负面共振腔强度
"""

import json
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from collections import Counter


@dataclass
class Comment:
    id: str
    author: str
    text: str
    timestamp: str
    sentiment: str = "neutral"  # positive, neutral, negative
    likes: int = 0
    replies: List['Comment'] = None
    
    def __post_init__(self):
        if self.replies is None:
            self.replies = []


class FieldToxicityAnalyzer:
    """场域毒性分析器"""
    
    # 叙事母题词典
    NARRATIVE_MOTIFS = {
        "betrayal": ["背叛", "背刺", "辜负", "心寒", "失望透顶"],
        "neglect": ["忽视", "不管", "不理", "装死", "冷处理"],
        "discrimination": ["区别对待", "偏心", "不公", "歧视"],
        "nationalism": ["亲日", "汉奸", "罕见", "崇洋", "日本"],
        "commercialization": ["逼氪", "圈钱", "骗氪", "割韭菜"],
        "technical": ["bug", "卡顿", "修复", "优化", "问题"]
    }
    
    # 武器化语言模式
    WEAPONIZED_PATTERNS = {
        "identity_attack": ["汉奸", "精日", "走狗", "罕见", "鬼子"],
        "moral_judgment": ["又当又立", "装死", "傲慢", "恶心", "贱"],
        "conspiracy": ["暗改", "偷偷", "试探", "资本", "内幕"],
        "us_vs_them": ["我们玩家", "你们官方", "国内", "国服", "日服"]
    }
    
    # 信任崩溃信号
    TRUST_SIGNALS = {
        "skepticism": ["谁信", "呵呵", "骗鬼", "画饼", "忽悠"],
        "promise_distrust": ["上次也说", "承诺", "保证", "没兑现", "又鸽"],
        "intent_attribution": ["就是想", "故意", "为了逼氪", "试探底线", "恶心玩家"]
    }
    
    def __init__(self, comments: List[Dict]):
        self.comments = [Comment(**c) for c in comments]
    
    def calculate_narrative_monopoly(self) -> Dict[str, Any]:
        """计算叙事垄断指数"""
        motif_counts = Counter()
        
        for comment in self.comments:
            for motif, keywords in self.NARRATIVE_MOTIFS.items():
                if any(kw in comment.text for kw in keywords):
                    motif_counts[motif] += 1
        
        total = sum(motif_counts.values())
        if total == 0:
            return {"monopoly_index": 0, "is_monopolized": False}
        
        # 赫芬达尔-赫希曼指数
        hhi = sum((count/total)**2 for count in motif_counts.values())
        
        # 主导叙事
        dominant_motif = motif_counts.most_common(1)[0] if motif_counts else ("none", 0)
        
        return {
            "monopoly_index": round(hhi, 2),
            "dominant_motif": dominant_motif[0],
            "dominant_count": dominant_motif[1],
            "dominant_ratio": round(dominant_motif[1] / total, 2) if total > 0 else 0,
            "narrative_diversity": len(motif_counts),
            "motif_distribution": dict(motif_counts),
            "is_monopolized": hhi > 0.6
        }
    
    def calculate_emotion_resonance(self) -> Dict[str, Any]:
        """计算情绪共振强度"""
        # 按情感分类
        sentiment_groups = {"positive": [], "neutral": [], "negative": []}
        for c in self.comments:
            sentiment_groups[c.sentiment].append(c)
        
        negative_ratio = len(sentiment_groups["negative"]) / len(self.comments)
        
        # 检测情绪级联（简化版：连续负面评论）
        cascades = []
        current_cascade = []
        
        for comment in self.comments:
            if comment.sentiment == "negative":
                current_cascade.append(comment)
            else:
                if len(current_cascade) >= 3:
                    cascades.append(current_cascade)
                current_cascade = []
        
        if len(current_cascade) >= 3:
            cascades.append(current_cascade)
        
        # 计算共振强度
        resonance_strength = (
            negative_ratio * 0.5 +
            min(len(cascades) / 5, 0.3) +
            min(sum(len(c) for c in cascades) / len(self.comments), 0.2)
        )
        
        return {
            "resonance_strength": round(resonance_strength, 2),
            "negative_ratio": round(negative_ratio, 2),
            "cascade_count": len(cascades),
            "max_cascade_length": max(len(c) for c in cascades) if cascades else 0,
            "is_echo_chamber": resonance_strength > 0.7
        }
    
    def calculate_heterogeneity_repulsion(self) -> Dict[str, Any]:
        """计算异质声音排斥度"""
        non_negative = [c for c in self.comments if c.sentiment != "negative"]
        
        if not non_negative:
            return {"repulsion_rate": 1.0, "is_hetero_repelled": True}
        
        repelled = 0
        for comment in non_negative:
            # 检查是否被攻击（简化：检查回复中是否有负面词）
            is_attacked = any(
                self._contains_attack_language(reply.text)
                for reply in comment.replies
            )
            
            # 检查是否被忽视（无互动）
            is_ignored = len(comment.replies) == 0 and comment.likes < 2
            
            if is_attacked or is_ignored:
                repelled += 1
        
        repulsion_rate = repelled / len(non_negative)
        
        return {
            "repulsion_rate": round(repulsion_rate, 2),
            "non_negative_count": len(non_negative),
            "repelled_count": repelled,
            "is_hetero_repelled": repulsion_rate > 0.8
        }
    
    def calculate_symbol_weaponization(self) -> Dict[str, Any]:
        """计算符号武器化程度"""
        category_scores = {}
        
        for category, patterns in self.WEAPONIZED_PATTERNS.items():
            count = sum(
                1 for c in self.comments
                if any(p in c.text for p in patterns)
            )
            category_scores[category] = round(count / len(self.comments), 2)
        
        overall = sum(category_scores.values()) / len(category_scores)
        
        return {
            "weaponization_scores": category_scores,
            "overall_weaponization": round(overall, 2),
            "is_weaponized": overall > 0.4
        }
    
    def calculate_trust_reserve(self) -> Dict[str, Any]:
        """计算信任余量"""
        trust_breakdown = {}
        
        for signal_type, patterns in self.TRUST_SIGNALS.items():
            count = sum(
                1 for c in self.comments
                if any(p in c.text for p in patterns)
            )
            trust_breakdown[signal_type] = round(count / len(self.comments), 2)
        
        # 信任余量 = 1 - 最大信任崩溃信号
        max_breakdown = max(trust_breakdown.values()) if trust_breakdown else 0
        trust_reserve = 1 - max_breakdown
        
        return {
            "trust_reserve": round(trust_reserve, 2),
            "trust_breakdown": trust_breakdown,
            "is_trust_depleted": trust_reserve < 0.3
        }
    
    def analyze_toxicity(self) -> Dict[str, Any]:
        """综合分析场域毒性"""
        narrative = self.calculate_narrative_monopoly()
        resonance = self.calculate_emotion_resonance()
        heterogeneity = self.calculate_heterogeneity_repulsion()
        weaponization = self.calculate_symbol_weaponization()
        trust = self.calculate_trust_reserve()
        
        # 综合毒性评分
        toxicity_score = (
            0.25 * narrative["monopoly_index"] +
            0.20 * resonance["resonance_strength"] +
            0.20 * heterogeneity["repulsion_rate"] +
            0.20 * weaponization["overall_weaponization"] +
            0.15 * (1 - trust["trust_reserve"])
        )
        
        # 毒性等级
        if toxicity_score < 0.3:
            level = "healthy"
            description = "场域健康，多元声音并存"
            color = "🟢"
        elif toxicity_score < 0.5:
            level = "mild"
            description = "轻度毒性，存在局部情绪聚集"
            color = "🟡"
        elif toxicity_score < 0.7:
            level = "moderate"
            description = "中度毒性，叙事开始垄断"
            color = "🟠"
        elif toxicity_score < 0.85:
            level = "severe"
            description = "重度毒性，负面共振腔形成"
            color = "🔴"
        else:
            level = "critical"
            description = "危急毒性，信任完全崩溃"
            color = "⚫"
        
        # 关键发现
        key_findings = []
        if narrative["is_monopolized"]:
            key_findings.append(f"叙事被'{narrative['dominant_motif']}'垄断")
        if resonance["is_echo_chamber"]:
            key_findings.append("情绪回声室效应显著")
        if heterogeneity["is_hetero_repelled"]:
            key_findings.append("异质声音被系统性排斥")
        if weaponization["is_weaponized"]:
            key_findings.append("语言高度武器化")
        if trust["is_trust_depleted"]:
            key_findings.append("信任储备枯竭")
        
        return {
            "toxicity_score": round(toxicity_score, 2),
            "toxicity_level": level,
            "description": description,
            "color": color,
            "dimensions": {
                "narrative_monopoly": narrative,
                "emotion_resonance": resonance,
                "heterogeneity_repulsion": heterogeneity,
                "symbol_weaponization": weaponization,
                "trust_reserve": trust
            },
            "key_findings": key_findings,
            "intervention_urgency": "immediate" if level in ["severe", "critical"] else "planned",
            "recommended_strategy": self._recommend_strategy(level)
        }
    
    def _contains_attack_language(self, text: str) -> bool:
        """检查是否包含攻击性语言"""
        attack_patterns = [
            "傻逼", "脑残", "滚", "死", "垃圾", "恶心", "贱"
        ]
        return any(p in text for p in attack_patterns)
    
    def _recommend_strategy(self, level: str) -> str:
        """根据毒性等级推荐策略"""
        strategies = {
            "healthy": "维持现状，定期监控",
            "mild": "关注情绪聚集点，准备预案",
            "moderate": "主动沟通，打断叙事垄断",
            "severe": "暂停公开回应，侧翼渠道稀释",
            "critical": "全面静默，长期信任重建计划"
        }
        return strategies.get(level, "继续监控")


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python toxicity_analyzer.py <comments.json>")
        print("JSON format: [{id, author, text, timestamp, sentiment, likes, replies}]")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        comments = json.load(f)
    
    analyzer = FieldToxicityAnalyzer(comments)
    result = analyzer.analyze_toxicity()
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
