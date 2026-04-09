"""
Cleaner Module - 执行清理操作
"""

import json
import shutil
from pathlib import Path
from typing import List, Dict, Any

from validator import DataValidator


class DataCleaner:
    def __init__(self, config: Dict[str, Any], interactive: bool = False):
        self.config = config
        self.interactive = interactive
        self.base_dir = Path(config["paths"]["base_dir"])
        self.registry_path = Path(config["paths"]["registry"])
        self.validator = DataValidator(config)
        self.actions = []
    
    def clean(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行清理操作"""
        self.actions = []
        
        for issue in issues:
            recommendation = self.validator.validate_issue(issue)
            action = recommendation["action"]
            
            if action == "skip":
                continue
            
            # 交互式确认
            if self.interactive:
                print(f"\n[{issue['type']}] {issue['path']}")
                print(f"  建议: {action} - {recommendation['reason']}")
                confirm = input("  确认执行? (y/n/skip all): ").lower()
                
                if confirm == "skip all":
                    self.interactive = False
                    continue
                elif confirm != "y":
                    print("  跳过")
                    continue
            
            # 执行操作
            result = self._execute_action(issue, recommendation)
            self.actions.append(result)
        
        return self.actions
    
    def _execute_action(self, issue: Dict[str, Any], recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个操作"""
        action = recommendation["action"]
        path = issue["path"]
        
        result = {
            "issue_type": issue["type"],
            "path": path,
            "action": action,
            "success": False,
            "detail": ""
        }
        
        try:
            if action == "delete":
                result["success"] = self._delete_path(path)
                result["detail"] = "已删除"
            
            elif action == "fix":
                result["success"] = self._fix_game_id(path)
                result["detail"] = "已修复 game_id"
            
            elif action == "merge":
                target = recommendation.get("target", "")
                result["success"] = self._merge_folders(path, target)
                result["detail"] = f"已合并到 {target}"
            
            elif action == "register":
                result["success"] = self._register_game(path)
                result["detail"] = "已添加到 registry"
            
        except Exception as e:
            result["detail"] = f"错误: {str(e)}"
        
        return result
    
    def _delete_path(self, path: str) -> bool:
        """删除文件或文件夹"""
        full_path = self.base_dir / path
        
        if full_path.is_file():
            full_path.unlink()
            return True
        elif full_path.is_dir():
            shutil.rmtree(full_path)
            return True
        
        return False
    
    def _fix_game_id(self, path: str) -> bool:
        """修复文件中的 game_id"""
        # 解析路径
        if "/" in path:
            folder_name, file_path = path.split("/", 1)
        else:
            return False
        
        full_path = self.base_dir / folder_name / file_path
        
        with open(full_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            # 修复顶层 game_id
            if "game_id" in data:
                data["game_id"] = folder_name
            
            # 修复数组中的 game_id
            for key in ["items", "videos", "transcripts", "posts"]:
                if key in data and isinstance(data[key], list):
                    for item in data[key]:
                        if isinstance(item, dict) and "game_id" in item:
                            item["game_id"] = folder_name
        
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    
    def _merge_folders(self, source: str, target: str) -> bool:
        """合并文件夹"""
        source_path = self.base_dir / source
        target_path = self.base_dir / target
        
        if not source_path.exists() or not target_path.exists():
            return False
        
        # 复制所有文件到目标文件夹
        for src_file in source_path.rglob("*"):
            if src_file.is_file():
                # 计算相对路径
                rel_path = src_file.relative_to(source_path)
                dst_file = target_path / rel_path
                
                # 创建目标目录
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件
                shutil.copy2(src_file, dst_file)
        
        # 删除源文件夹
        shutil.rmtree(source_path)
        
        return True
    
    def _register_game(self, folder_name: str) -> bool:
        """将游戏添加到 registry"""
        # 读取现有 registry
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        # 获取游戏名映射
        game_name = self.config.get("game_name_map", {}).get(folder_name, folder_name)
        
        # 添加到 registry
        if "games" not in registry:
            registry["games"] = {}
        
        registry["games"][folder_name] = {
            "name": folder_name,
            "english_name": game_name,
            "queries": [folder_name],
            "platforms": {}
        }
        
        # 保存 registry
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
        
        return True
