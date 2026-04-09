"""
Validator Module - 验证数据有效性
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class DataValidator:
    """验证数据内容，决定处理方式"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_dir = Path(config["paths"]["base_dir"])
    
    def validate_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证单个问题，返回建议的处理方式
        
        Returns:
            {
                "action": "delete" | "merge" | "fix" | "skip",
                "target": str,  # 目标路径（用于 merge）
                "reason": str   # 处理原因
            }
        """
        issue_type = issue["type"]
        path = issue["path"]
        
        if issue_type == "empty_file":
            return {
                "action": "delete",
                "reason": "空文件，无价值"
            }
        
        elif issue_type == "corrupted_json":
            return {
                "action": "delete",
                "reason": "JSON 损坏无法修复"
            }
        
        elif issue_type == "empty_array":
            # 检查是否是 checkpoint 文件
            if "checkpoint" in path.lower():
                return {
                    "action": "delete",
                    "reason": "checkpoint 文件数组为空"
                }
            return {
                "action": "delete",
                "reason": "数据数组为空"
            }
        
        elif issue_type == "game_id_mismatch":
            return {
                "action": "fix",
                "reason": f"修复 game_id 匹配文件夹名"
            }
        
        elif issue_type == "orphan_folder":
            # 需要进一步分析文件夹内容
            return self._analyze_orphan_folder(path)
        
        elif issue_type == "missing_folder":
            return {
                "action": "skip",
                "reason": "registry 中有记录但无数据，无需处理"
            }
        
        return {
            "action": "skip",
            "reason": "未知问题类型"
        }
    
    def _analyze_orphan_folder(self, folder_name: str) -> Dict[str, Any]:
        """分析孤儿文件夹，判断是否是重复数据"""
        folder_path = self.base_dir / folder_name
        
        # 检查文件夹大小
        total_size = sum(f.stat().st_size for f in folder_path.rglob("*") if f.is_file())
        
        if total_size == 0:
            return {
                "action": "delete",
                "reason": "空文件夹"
            }
        
        # 尝试读取样本文件判断内容
        sample_files = list(folder_path.rglob("*.json"))[:3]
        
        for sample_file in sample_files:
            try:
                with open(sample_file, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                
                # 检查 game 字段
                if isinstance(data, dict):
                    game_name = data.get("game", "")
                    
                    # 查找可能的重复
                    for registered_id, mapped_name in self.config.get("game_name_map", {}).items():
                        if game_name == mapped_name and registered_id != folder_name:
                            return {
                                "action": "merge",
                                "target": registered_id,
                                "reason": f"内容与 {registered_id} 重复"
                            }
            except:
                continue
        
        # 检查是否是测试数据
        if folder_name.startswith("test") or folder_name.startswith("g_test"):
            return {
                "action": "delete",
                "reason": "测试数据"
            }
        
        # 可能是新游戏，建议注册
        return {
            "action": "register",
            "reason": f"可能是新游戏，建议添加到 registry (大小: {total_size/1024:.1f} KB)"
        }
    
    def get_folder_size(self, folder_name: str) -> int:
        """获取文件夹总大小（字节）"""
        folder_path = self.base_dir / folder_name
        if not folder_path.exists():
            return 0
        return sum(f.stat().st_size for f in folder_path.rglob("*") if f.is_file())
    
    def read_sample(self, folder_name: str, max_lines: int = 10) -> Optional[str]:
        """读取文件夹内样本文件内容"""
        folder_path = self.base_dir / folder_name
        json_files = list(folder_path.rglob("*.json"))
        
        if not json_files:
            return None
        
        try:
            with open(json_files[0], 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            return json.dumps(data, ensure_ascii=False, indent=2)[:500]
        except:
            return None
