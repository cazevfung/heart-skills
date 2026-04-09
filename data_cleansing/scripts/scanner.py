"""
Scanner Module - 扫描数据问题
"""

import json
from pathlib import Path
from typing import List, Dict, Any


class DataScanner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_dir = Path(config["paths"]["base_dir"])
        self.registry_path = Path(config["paths"]["registry"])
        self.issues = []
    
    def scan_all(self) -> List[Dict[str, Any]]:
        """执行所有扫描"""
        self.issues = []
        
        # 加载 registry
        registered_games = self._load_registry()
        
        # 扫描文件夹
        if not self.base_dir.exists():
            return [{"type": "error", "path": str(self.base_dir), "detail": "数据目录不存在"}]
        
        folder_names = set()
        
        for folder in sorted(self.base_dir.iterdir()):
            if not folder.is_dir():
                continue
            
            folder_name = folder.name
            folder_names.add(folder_name)
            
            # 检查是否在 registry 中
            if self.config["rules"]["orphan_folders"]["enabled"]:
                if folder_name not in registered_games:
                    # 检查是否是测试文件夹
                    allowed_prefixes = self.config["rules"]["orphan_folders"]["allowed_prefixes"]
                    if not any(folder_name.startswith(p) for p in allowed_prefixes):
                        self.issues.append({
                            "type": "orphan_folder",
                            "path": folder_name,
                            "detail": "未在 registry 中注册"
                        })
            
            # 扫描文件夹内的 JSON 文件
            self._scan_folder(folder, folder_name)
        
        # 检查 registry 中缺失的文件夹
        for game_id in registered_games:
            if game_id not in folder_names:
                self.issues.append({
                    "type": "missing_folder",
                    "path": game_id,
                    "detail": "registry 中存在但文件夹不存在"
                })
        
        return self.issues
    
    def _load_registry(self) -> set:
        """加载 registry"""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            return set(registry.get("games", {}).keys())
        except Exception as e:
            print(f"警告: 无法加载 registry: {e}")
            return set()
    
    def _scan_folder(self, folder: Path, folder_name: str):
        """扫描单个文件夹"""
        json_files = list(folder.rglob("*.json"))
        
        for json_file in json_files:
            self._scan_json_file(json_file, folder_name)
    
    def _scan_json_file(self, file_path: Path, folder_name: str):
        """扫描单个 JSON 文件"""
        rel_path = f"{folder_name}/{file_path.name}"
        
        # 检查空文件
        if self.config["rules"]["empty_file"]["enabled"]:
            file_size = file_path.stat().st_size
            if file_size <= self.config["rules"]["empty_file"]["threshold_bytes"]:
                self.issues.append({
                    "type": "empty_file",
                    "path": rel_path,
                    "detail": f"文件大小: {file_size} bytes"
                })
                return
        
        # 尝试解析 JSON
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.issues.append({
                "type": "corrupted_json",
                "path": rel_path,
                "detail": f"JSON 解析错误: {str(e)[:50]}"
            })
            return
        except Exception as e:
            self.issues.append({
                "type": "corrupted_json",
                "path": rel_path,
                "detail": f"读取错误: {str(e)[:50]}"
            })
            return
        
        # 检查对象类型的数据
        if isinstance(data, dict):
            self._scan_dict_data(data, rel_path, folder_name)
    
    def _scan_dict_data(self, data: dict, rel_path: str, folder_name: str):
        """扫描字典类型的数据"""
        
        # 检查 game_id 匹配
        if self.config["rules"]["game_id_mismatch"]["enabled"]:
            if "game_id" in data and data["game_id"]:
                if data["game_id"] != folder_name:
                    self.issues.append({
                        "type": "game_id_mismatch",
                        "path": rel_path,
                        "detail": f"game_id='{data['game_id']}', 期望='{folder_name}'"
                    })
        
        # 检查空数组
        if self.config["rules"]["empty_arrays"]["enabled"]:
            array_fields = self.config["rules"]["empty_arrays"]["fields"]
            min_count = self.config["rules"]["empty_arrays"]["min_count"]
            
            for field in array_fields:
                if field in data and isinstance(data[field], list):
                    if len(data[field]) < min_count:
                        self.issues.append({
                            "type": "empty_array",
                            "path": rel_path,
                            "detail": f"{field} 数组为空 (count={len(data[field])})"
                        })
