"""
词典自动演化器
全自动AI驱动的词典更新
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass


@dataclass
class EvolutionCandidate:
    """演化候选词"""
    keyword: str
    category: str  # narrative_motifs, weaponized_patterns, etc.
    confidence: float
    description: str
    examples: List[str]
    suggested_weight: float
    variants: List[str]
    

def call_llm_for_extraction(comments_text: str, region: str, cluster: str) -> List[EvolutionCandidate]:
    """
    调用LLM提取候选词
    
    注意：这是一个mock实现，实际使用时需要接入真实的LLM API
    """
    prompt = f"""
你是一位专业的游戏社区舆情分析师，擅长识别{region}区域玩家社区的新兴表达方式。

请分析以下评论样本，识别该社区特有的、词典中可能尚未收录的表达方式：

[评论样本]
{comments_text[:3000]}...

请识别以下类别的候选词：

1. **新兴叙事母题**：玩家讨论的核心议题类型（如"暗改"、"区别对待"等）
2. **新情绪标记**：独特的情绪表达方式
3. **新武器化模式**：攻击性或讽刺性的语言模式
4. **新信任信号**：表达对官方不信任的特定说法

对每项候选词，请提供：
- 关键词/模式
- 置信度（0-1，基于出现频率和清晰度）
- 简要描述
- 2-3个示例句子
- 建议权重（0-1，该词在分析中的重要性）
- 变体形式（如果有）

只返回置信度>0.7的项。以JSON格式返回。
"""
    
    # Mock实现：返回空列表
    # 实际实现应调用LLM API
    return []


class DictionaryEvolver:
    """词典自动演化器"""
    
    def __init__(self, cluster: str, region: str, base_path: str = None):
        self.cluster = cluster
        self.region = region
        
        if base_path is None:
            script_dir = Path(__file__).parent.parent
            self.base_path = script_dir / "references" / "regional_dictionaries"
        else:
            self.base_path = Path(base_path)
        
        self.region_path = self.base_path / cluster / region
        self.evolution_log_path = self.base_path / "_evolution_log"
        
        # 确保目录存在
        self.region_path.mkdir(parents=True, exist_ok=True)
        self.evolution_log_path.mkdir(parents=True, exist_ok=True)
    
    def evolve(self, comments: List[Dict], high_interaction_threshold: int = 50) -> Dict:
        """
        执行词典演化
        
        Args:
            comments: 评论数据列表
            high_interaction_threshold: 高互动阈值（点赞+回复数）
        
        Returns:
            演化结果报告
        """
        # 1. 筛选高互动评论
        high_interaction = [
            c for c in comments
            if c.get("likes", 0) + len(c.get("replies", [])) > high_interaction_threshold
        ]
        
        if len(high_interaction) < 10:
            return {
                "evolved": False,
                "reason": "Insufficient high-interaction comments",
                "comments_analyzed": len(comments),
                "high_interaction_count": len(high_interaction)
            }
        
        # 2. 准备评论文本
        comments_text = self._prepare_comments_text(high_interaction)
        
        # 3. LLM提取候选词
        candidates = call_llm_for_extraction(comments_text, self.region, self.cluster)
        
        # 4. 过滤已存在的词
        new_candidates = self._filter_existing(candidates)
        
        # 5. 自动入库
        added_items = []
        for candidate in new_candidates:
            success = self._add_to_dictionary(candidate)
            if success:
                added_items.append({
                    "keyword": candidate.keyword,
                    "category": candidate.category,
                    "confidence": candidate.confidence
                })
        
        # 6. 记录演化日志
        self._log_evolution(added_items, len(comments), len(high_interaction))
        
        return {
            "evolved": True,
            "region": self.region,
            "cluster": self.cluster,
            "comments_analyzed": len(comments),
            "high_interaction_analyzed": len(high_interaction),
            "candidates_found": len(candidates),
            "new_candidates": len(new_candidates),
            "added_items": added_items,
            "timestamp": datetime.now().isoformat()
        }
    
    def _prepare_comments_text(self, comments: List[Dict]) -> str:
        """准备评论文本供LLM分析"""
        texts = []
        for c in comments[:50]:  # 最多取50条
            text = c.get("text", "")
            likes = c.get("likes", 0)
            replies = len(c.get("replies", []))
            texts.append(f"[点赞:{likes} 回复:{replies}] {text}")
        return "\n\n".join(texts)
    
    def _filter_existing(self, candidates: List[EvolutionCandidate]) -> List[EvolutionCandidate]:
        """过滤已存在的词"""
        new_candidates = []
        
        for candidate in candidates:
            if not self._keyword_exists(candidate.keyword, candidate.category):
                new_candidates.append(candidate)
        
        return new_candidates
    
    def _keyword_exists(self, keyword: str, category: str) -> bool:
        """检查关键词是否已存在"""
        dict_file = self.region_path / f"{category}.json"
        
        if not dict_file.exists():
            return False
        
        try:
            with open(dict_file, 'r', encoding='utf-8') as f:
                dictionary = json.load(f)
            
            if category == "narrative_motifs":
                for motif in dictionary.get("motifs", []):
                    if keyword in motif.get("keywords", []):
                        return True
            elif category == "weaponized_patterns":
                for cat_data in dictionary.get("categories", {}).values():
                    if keyword in cat_data.get("patterns", []):
                        return True
            elif category == "trust_signals":
                for signal_data in dictionary.get("signals", {}).values():
                    if keyword in signal_data.get("patterns", []):
                        return True
            
            return False
        except Exception:
            return False
    
    def _add_to_dictionary(self, candidate: EvolutionCandidate) -> bool:
        """添加候选词到词典"""
        dict_file = self.region_path / f"{candidate.category}.json"
        
        # 读取现有词典或创建新词典
        if dict_file.exists():
            with open(dict_file, 'r', encoding='utf-8') as f:
                dictionary = json.load(f)
        else:
            dictionary = {
                "version": datetime.now().strftime("%Y-%m-%d"),
                "cluster": self.cluster,
                "region": self.region,
                "metadata": {
                    "last_evolved": datetime.now().isoformat(),
                    "evolution_method": "auto_llm",
                    "confidence_threshold": 0.7
                }
            }
        
        # 根据类别添加
        if candidate.category == "narrative_motifs":
            if "motifs" not in dictionary:
                dictionary["motifs"] = []
            
            motif_id = self._generate_id(candidate.keyword)
            dictionary["motifs"].append({
                "id": motif_id,
                "name": candidate.description,
                "keywords": [candidate.keyword] + candidate.variants,
                "weight": candidate.suggested_weight,
                "emotion_polarity": "negative",
                "escalation_pattern": "auto_detected",
                "auto_added": True,
                "added_at": datetime.now().isoformat(),
                "confidence": candidate.confidence,
                "examples": candidate.examples[:3]
            })
        
        elif candidate.category == "weaponized_patterns":
            if "categories" not in dictionary:
                dictionary["categories"] = {}
            
            # 自动分类（简化版）
            subcategory = "auto_detected"
            dictionary["categories"][subcategory] = {
                "patterns": [candidate.keyword] + candidate.variants,
                "severity": "medium",
                "escalation_speed": "medium",
                "context": candidate.description,
                "auto_added": True,
                "added_at": datetime.now().isoformat()
            }
        
        # 更新元数据
        dictionary["metadata"]["last_evolved"] = datetime.now().isoformat()
        
        # 保存
        try:
            with open(dict_file, 'w', encoding='utf-8') as f:
                json.dump(dictionary, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving dictionary: {e}")
            return False
    
    def _generate_id(self, keyword: str) -> str:
        """生成ID"""
        # 简化实现：直接使用关键词的拼音/英文
        import re
        # 移除非字母数字字符，转为小写
        id_str = re.sub(r'[^\w]', '_', keyword.lower())
        return f"auto_{id_str}_{datetime.now().strftime('%m%d')}"
    
    def _log_evolution(self, added_items: List[Dict], total_comments: int, high_interaction: int):
        """记录演化日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "cluster": self.cluster,
            "region": self.region,
            "comments_analyzed": total_comments,
            "high_interaction_comments": high_interaction,
            "items_added": added_items,
            "method": "auto_llm"
        }
        
        log_file = self.evolution_log_path / f"{datetime.now().strftime('%Y-%m-%d')}_{self.region}_evolution.json"
        
        # 追加到日志文件
        logs = []
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        
        logs.append(log_entry)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 测试
    evolver = DictionaryEvolver("east_asia", "zh-CN")
    
    # Mock评论数据
    mock_comments = [
        {"text": "这游戏真的垃圾", "likes": 100, "replies": [{}, {}]},
        {"text": "官方又在暗改", "likes": 50, "replies": [{}]},
    ]
    
    result = evolver.evolve(mock_comments)
    print(json.dumps(result, ensure_ascii=False, indent=2))
