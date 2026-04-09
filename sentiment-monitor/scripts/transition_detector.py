"""
叙事跃迁检测脚本
用于识别评论区议题性质的质变时刻
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
    parent_id: str = None
    likes: int = 0
    replies: List['Comment'] = None
    
    def __post_init__(self):
        if self.replies is None:
            self.replies = []


class NarrativeTransitionDetector:
    """叙事跃迁检测器"""
    
    # 技术问题关键词
    TECHNICAL_KEYWORDS = [
        "bug", "卡顿", "闪退", "穿模", "修复", "优化", 
        "更新", "问题", "错误", "故障", "崩溃"
    ]
    
    # 价值冲突关键词
    VALUE_KEYWORDS = [
        "亲日", "汉奸", "罕见", "区别对待", "傲慢", "背叛",
        "崇洋", "歧视", "不公", "偏心", "装死", "又当又立"
    ]
    
    # 情绪升级关键词
    EMOTION_KEYWORDS = [
        "愤怒", "恶心", "失望", "心寒", "退游", "退款",
        "垃圾", "烂", "死", "滚", "贱"
    ]
    
    # 嫁接模式
    GRAFTING_PATTERNS = [
        r".*不改.*一句话.*改.*",
        r".*不修.*马上.*修.*",
        r"国内.*国外.*",
        r"玩家.*官方.*",
        r"我们.*你们.*"
    ]
    
    def __init__(self, comments: List[Dict]):
        self.comments = [Comment(**c) for c in comments]
        self.comments.sort(key=lambda x: x.timestamp)
    
    def detect_keyword_mutation(self, window_size: int = 10) -> Dict[str, Any]:
        """检测关键词分布突变"""
        if len(self.comments) < window_size * 2:
            return {"mutation_score": 0, "is_transition": False}
        
        early_window = self.comments[:window_size]
        late_window = self.comments[-window_size:]
        
        early_keywords = self._extract_keywords(early_window)
        late_keywords = self._extract_keywords(late_window)
        
        # 检测新出现的价值关键词
        early_value_count = sum(1 for k in early_keywords if k in self.VALUE_KEYWORDS)
        late_value_count = sum(1 for k in late_keywords if k in self.VALUE_KEYWORDS)
        
        mutation_score = (late_value_count - early_value_count) / max(len(late_keywords), 1)
        
        return {
            "mutation_score": min(mutation_score, 1.0),
            "early_value_ratio": early_value_count / max(len(early_keywords), 1),
            "late_value_ratio": late_value_count / max(len(late_keywords), 1),
            "is_transition": mutation_score > 0.2
        }
    
    def detect_narrative_grafting(self) -> Dict[str, Any]:
        """检测叙事嫁接"""
        for comment in self.comments:
            has_technical = any(kw in comment.text for kw in self.TECHNICAL_KEYWORDS)
            has_value = any(kw in comment.text for kw in self.VALUE_KEYWORDS)
            
            if has_technical and has_value:
                # 检查嫁接模式
                for pattern in self.GRAFTING_PATTERNS:
                    if re.search(pattern, comment.text):
                        return {
                            "is_grafting_point": True,
                            "grafting_comment": {
                                "id": comment.id,
                                "author": comment.author,
                                "text": comment.text[:100] + "..." if len(comment.text) > 100 else comment.text
                            },
                            "pattern_matched": pattern,
                            "technical_elements": [kw for kw in self.TECHNICAL_KEYWORDS if kw in comment.text],
                            "value_elements": [kw for kw in self.VALUE_KEYWORDS if kw in comment.text]
                        }
        
        return {"is_grafting_point": False}
    
    def detect_emotion_escalation(self) -> Dict[str, Any]:
        """检测情绪升级"""
        emotion_curve = []
        for comment in self.comments:
            score = self._calculate_emotion_intensity(comment.text)
            emotion_curve.append(score)
        
        if len(emotion_curve) < 5:
            return {"has_escalation": False}
        
        # 检测情绪跳变点
        early_avg = sum(emotion_curve[:5]) / 5
        late_avg = sum(emotion_curve[-5:]) / 5
        
        escalation = late_avg - early_avg
        
        # 找到情绪最高的评论
        max_emotion_idx = emotion_curve.index(max(emotion_curve))
        max_emotion_comment = self.comments[max_emotion_idx]
        
        return {
            "has_escalation": escalation > 0.3,
            "escalation_score": escalation,
            "early_avg": early_avg,
            "late_avg": late_avg,
            "peak_emotion_comment": {
                "id": max_emotion_comment.id,
                "author": max_emotion_comment.author,
                "text": max_emotion_comment.text[:100] + "..."
            }
        }
    
    def detect_key_nodes(self) -> List[Dict[str, Any]]:
        """检测关键节点（高互动、引发连锁反应的评论）"""
        key_nodes = []
        
        for comment in self.comments:
            # 计算互动分数
            reply_count = len(comment.replies)
            like_count = comment.likes
            
            # 检查是否包含叙事嫁接
            has_grafting = any(
                re.search(pattern, comment.text) 
                for pattern in self.GRAFTING_PATTERNS
            )
            
            influence_score = reply_count * 2 + like_count
            if has_grafting:
                influence_score *= 1.5
            
            if influence_score > 10:  # 阈值可调整
                key_nodes.append({
                    "comment_id": comment.id,
                    "author": comment.author,
                    "influence_score": influence_score,
                    "reply_count": reply_count,
                    "like_count": like_count,
                    "has_grafting": has_grafting,
                    "text_preview": comment.text[:80] + "..." if len(comment.text) > 80 else comment.text
                })
        
        # 按影响力排序
        key_nodes.sort(key=lambda x: x["influence_score"], reverse=True)
        return key_nodes[:5]  # 返回前5个关键节点
    
    def analyze_transition(self) -> Dict[str, Any]:
        """综合分析叙事跃迁"""
        keyword_mutation = self.detect_keyword_mutation()
        narrative_grafting = self.detect_narrative_grafting()
        emotion_escalation = self.detect_emotion_escalation()
        key_nodes = self.detect_key_nodes()
        
        # 综合评分
        transition_score = (
            0.3 * keyword_mutation.get("mutation_score", 0) +
            0.3 * (1.0 if narrative_grafting.get("is_grafting_point") else 0) +
            0.25 * (emotion_escalation.get("escalation_score", 0) / 2) +
            0.15 * min(len(key_nodes) / 3, 1.0)
        )
        
        # 确定跃迁阶段
        if transition_score < 0.3:
            stage = "pre_emergence"
            description = "议题处于正常技术讨论阶段"
        elif transition_score < 0.5:
            stage = "emergence"
            description = "议题开始出现价值化苗头"
        elif transition_score < 0.7:
            stage = "consolidation"
            description = "叙事跃迁正在发生，议题性质转变中"
        else:
            stage = "saturation"
            description = "叙事跃迁完成，议题已完全价值化"
        
        # 干预窗口判断
        if stage == "pre_emergence":
            intervention_window = "open"
            intervention_urgency = "low"
        elif stage == "emergence":
            intervention_window = "open"
            intervention_urgency = "medium"
        elif stage == "consolidation":
            intervention_window = "closing"
            intervention_urgency = "high"
        else:
            intervention_window = "closed"
            intervention_urgency = "critical"
        
        return {
            "transition_detected": transition_score > 0.5,
            "transition_score": round(transition_score, 2),
            "stage": stage,
            "description": description,
            "keyword_mutation": keyword_mutation,
            "narrative_grafting": narrative_grafting,
            "emotion_escalation": emotion_escalation,
            "key_nodes": key_nodes,
            "intervention_window": intervention_window,
            "intervention_urgency": intervention_urgency,
            "recommended_action": self._recommend_action(stage)
        }
    
    def _extract_keywords(self, comments: List[Comment]) -> List[str]:
        """提取关键词"""
        all_text = " ".join([c.text for c in comments])
        # 简单分词（实际应用可使用jieba等分词工具）
        words = re.findall(r'[\u4e00-\u9fff]+', all_text)
        return words
    
    def _calculate_emotion_intensity(self, text: str) -> float:
        """计算情绪强度（0-1）"""
        score = 0.0
        
        # 情绪词计数
        emotion_count = sum(1 for kw in self.EMOTION_KEYWORDS if kw in text)
        score += emotion_count * 0.1
        
        # 标点符号（感叹号、问号）
        score += text.count('！') * 0.05
        score += text.count('？') * 0.03
        
        # 大写/重复字符（模拟）
        score += len(re.findall(r'(.)\1{2,}', text)) * 0.1
        
        return min(score, 1.0)
    
    def _recommend_action(self, stage: str) -> str:
        """根据阶段推荐行动"""
        actions = {
            "pre_emergence": "持续监控，准备技术解释材料",
            "emergence": "立即发布透明技术说明，主动沟通",
            "consolidation": "发布详细数据对比，打断叙事嫁接",
            "saturation": "暂停公开回应，通过侧翼渠道沟通"
        }
        return actions.get(stage, "继续监控")


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python transition_detector.py <comments.json>")
        print("JSON format: [{id, author, text, timestamp, parent_id, likes}]")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        comments = json.load(f)
    
    detector = NarrativeTransitionDetector(comments)
    result = detector.analyze_transition()
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
