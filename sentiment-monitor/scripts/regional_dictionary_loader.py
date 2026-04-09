"""
区域化词典加载器
支持多文化圈的词典管理
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class RegionalDictionaryLoader:
    """区域词典加载器"""
    
    # 文化圈定义
    CULTURAL_CLUSTERS = {
        "east_asia": ["zh-CN", "zh-TW", "zh-HK", "ja-JP", "ko-KR"],
        "western": ["en-US", "en-GB", "en-CA", "en-AU", "de-DE", "fr-FR"],
        "southeast_asia": ["th-TH", "vi-VN", "id-ID", "ms-MY", "tl-PH"],
        "latam": ["es-MX", "es-AR", "es-CL", "pt-BR"]
    }
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            # 默认路径：相对于脚本位置
            script_dir = Path(__file__).parent.parent
            self.base_path = script_dir / "references" / "regional_dictionaries"
        else:
            self.base_path = Path(base_path)
    
    def get_cluster_for_region(self, region: str) -> Optional[str]:
        """获取区域所属的文化圈"""
        for cluster, regions in self.CULTURAL_CLUSTERS.items():
            if region in regions:
                return cluster
        return None
    
    def load_dictionary(self, cluster: str, region: str, dict_type: str) -> Optional[Dict]:
        """
        加载特定词典
        
        Args:
            cluster: 文化圈 (east_asia, western, etc.)
            region: 区域代码 (zh-CN, ja-JP, etc.)
            dict_type: 词典类型 (narrative_motifs, weaponized_patterns, trust_signals)
        """
        file_path = self.base_path / cluster / region / f"{dict_type}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_all_for_region(self, region: str) -> Dict[str, Dict]:
        """加载某个区域的所有词典"""
        cluster = self.get_cluster_for_region(region)
        if not cluster:
            raise ValueError(f"Unknown region: {region}")
        
        dictionaries = {}
        dict_types = ["narrative_motifs", "weaponized_patterns", "trust_signals", "emotion_markers"]
        
        for dict_type in dict_types:
            data = self.load_dictionary(cluster, region, dict_type)
            if data:
                dictionaries[dict_type] = data
        
        return dictionaries
    
    def get_cross_cluster_equivalent(self, motif_id: str, from_region: str, to_region: str) -> Optional[str]:
        """
        获取跨区域母题等价映射
        
        Example:
            get_cross_cluster_equivalent("nationalism", "zh-CN", "en-US")
            -> "favoritism"
        """
        from_cluster = self.get_cluster_for_region(from_region)
        dictionary = self.load_dictionary(from_cluster, from_region, "narrative_motifs")
        
        if not dictionary:
            return None
        
        for motif in dictionary.get("motifs", []):
            if motif["id"] == motif_id:
                equivalents = motif.get("cross_cluster_equivalents", {})
                
                # 先尝试精确匹配区域
                if to_region in equivalents:
                    return equivalents[to_region]
                
                # 再尝试匹配文化圈
                to_cluster = self.get_cluster_for_region(to_region)
                if to_cluster in equivalents:
                    return equivalents[to_cluster]
                
                # 特殊处理东亚内部映射
                if from_cluster == "east_asia" and to_cluster == "east_asia":
                    if to_region.startswith("zh"):
                        return equivalents.get("east_asia_zh")
                    elif to_region.startswith("ja"):
                        return equivalents.get("east_asia_ja")
                    elif to_region.startswith("ko"):
                        return equivalents.get("east_asia_ko")
        
        return None
    
    def list_available_regions(self) -> List[str]:
        """列出所有可用区域"""
        regions = []
        for cluster_dir in self.base_path.iterdir():
            if cluster_dir.is_dir() and not cluster_dir.name.startswith("_"):
                for region_dir in cluster_dir.iterdir():
                    if region_dir.is_dir():
                        regions.append(region_dir.name)
        return regions
    
    def get_dictionary_metadata(self, cluster: str, region: str, dict_type: str) -> Optional[Dict]:
        """获取词典元数据"""
        dictionary = self.load_dictionary(cluster, region, dict_type)
        if dictionary:
            return dictionary.get("metadata", {})
        return None


# 便捷函数
def load_regional_dictionaries(region: str) -> Dict[str, Dict]:
    """便捷函数：加载指定区域的所有词典"""
    loader = RegionalDictionaryLoader()
    return loader.load_all_for_region(region)


def get_cluster(region: str) -> Optional[str]:
    """便捷函数：获取区域所属文化圈"""
    loader = RegionalDictionaryLoader()
    return loader.get_cluster_for_region(region)


if __name__ == "__main__":
    # 测试
    loader = RegionalDictionaryLoader()
    
    print("Available regions:", loader.list_available_regions())
    print()
    
    # 加载中文词典
    zh_dicts = loader.load_all_for_region("zh-CN")
    print(f"Loaded {len(zh_dicts)} dictionaries for zh-CN")
    
    if "narrative_motifs" in zh_dicts:
        motifs = zh_dicts["narrative_motifs"]["motifs"]
        print(f"  - Narrative motifs: {len(motifs)}")
        for motif in motifs:
            print(f"    - {motif['id']}: {motif['name']}")
    
    print()
    
    # 测试跨区域映射
    equivalent = loader.get_cross_cluster_equivalent("nationalism", "zh-CN", "en-US")
    print(f"'nationalism' (zh-CN) -> '{equivalent}' (en-US)")
