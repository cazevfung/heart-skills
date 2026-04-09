#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏公告图配置加载器
支持多游戏、主题继承、风格扩展
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class ConfigLoader:
    """配置加载器 - 处理配置继承和合并"""
    
    def __init__(self, config_base_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_base_path: 配置根目录，默认从当前文件向上找config目录
        """
        if config_base_path:
            self.config_base = Path(config_base_path)
        else:
            # 从当前文件位置推断: scripts/ -> parent -> config/
            self.config_base = Path(__file__).parent.parent / "config"
        
        self._cache = {}  # 缓存已加载的配置
    
    def _load_json(self, relative_path: str) -> dict:
        """加载JSON文件"""
        full_path = self.config_base / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_game_config(self, game_key: str) -> Dict[str, Any]:
        """
        加载游戏完整配置（包含继承和合并）
        
        Args:
            game_key: 游戏标识符，如 "heartopia"
            
        Returns:
            合并后的完整配置字典
        """
        # 检查缓存
        cache_key = f"game_{game_key}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 1. 加载游戏专属配置
        game_config = self._load_json(f"games/{game_key}.json")
        
        # 验证 game_key 匹配
        if game_config.get("game_key") != game_key:
            raise ValueError(f"配置文件 game_key 不匹配: {game_config.get('game_key')} != {game_key}")
        
        # 2. 获取默认风格
        style_id = game_config.get("visual", {}).get("default_style", "announcement_cover")
        style_config = self.load_style_config(style_id)
        
        # 3. 合并主题配置
        themes = self._merge_themes(game_config)
        
        # 4. 合并角色模式配置
        character_modes = self._merge_character_modes(game_config, style_config)
        
        # 5. 处理参考图
        reference_images = self._resolve_reference_images(game_config)
        
        # 6. 组装完整配置
        full_config = {
            "game_key": game_key,
            "game_name": game_config.get("game_name", game_key),
            "game_name_en": game_config.get("game_name_en", game_key),
            "reference_images": reference_images,
            "themes": themes,
            "character_modes": character_modes,
            "visual": game_config.get("visual", {}),
            "output": game_config.get("output", {}),
            "prompt_template": game_config.get("prompt_template", {}),
            "style_config": style_config
        }
        
        # 缓存
        self._cache[cache_key] = full_config
        return full_config
    
    def load_style_config(self, style_id: str) -> Dict[str, Any]:
        """
        加载风格配置
        
        Args:
            style_id: 风格标识符，如 "announcement_cover"
            
        Returns:
            风格配置字典
        """
        cache_key = f"style_{style_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        style_config = self._load_json(f"styles/{style_id}.json")
        
        # 验证 style_id 匹配
        if style_config.get("style_id") != style_id:
            raise ValueError(f"风格文件 style_id 不匹配: {style_config.get('style_id')} != {style_id}")
        
        self._cache[cache_key] = style_config
        return style_config
    
    def load_default_themes(self) -> Dict[str, Any]:
        """加载默认主题库"""
        cache_key = "default_themes"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        themes_config = self._load_json("themes/_default_themes.json")
        self._cache[cache_key] = themes_config.get("themes", {})
        return self._cache[cache_key]
    
    def _merge_themes(self, game_config: dict) -> Dict[str, Any]:
        """
        合并主题配置
        优先级: 游戏自定义 > 游戏覆盖 > 默认主题库
        """
        themes = {}
        
        # 是否继承默认主题库
        if game_config.get("themes", {}).get("inherit_default", True):
            themes.update(self.load_default_themes())
        
        # 游戏覆盖
        themes.update(game_config.get("themes", {}).get("overrides", {}))
        
        # 游戏自定义（新增）
        themes.update(game_config.get("themes", {}).get("custom", {}))
        
        return themes
    
    def _merge_character_modes(self, game_config: dict, style_config: dict) -> Dict[str, Any]:
        """
        合并角色模式配置
        优先级: 游戏自定义 > 游戏覆盖 > 风格默认
        """
        character_modes = {}
        
        # 是否继承风格默认
        if game_config.get("character_modes", {}).get("inherit_default", True):
            character_modes.update(style_config.get("character_modes", {}))
        
        # 游戏覆盖
        character_modes.update(game_config.get("character_modes", {}).get("overrides", {}))
        
        # 游戏自定义（新增）
        character_modes.update(game_config.get("character_modes", {}).get("custom", {}))
        
        return character_modes
    
    def _resolve_reference_images(self, game_config: dict) -> List[str]:
        """
        解析参考图配置
        从 ref_file 指定的 .txt 文件读取URL列表
        """
        ref_config = game_config.get("reference_images", {})
        ref_file = ref_config.get("ref_file")
        
        if not ref_file:
            return []
        
        return self._load_ref_urls(ref_file)
    
    def _load_ref_urls(self, ref_file: str) -> List[str]:
        """
        从 .txt 文件加载参考图URL列表
        支持 # 注释和空行
        """
        file_path = self.config_base / ref_file
        if not file_path.exists():
            raise FileNotFoundError(f"参考图链接文件不存在: {file_path}")
        
        urls = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释行
                if not line or line.startswith('#'):
                    continue
                urls.append(line)
        
        return urls
    
    def list_games(self) -> List[str]:
        """列出所有已配置的游戏"""
        games_dir = self.config_base / "games"
        if not games_dir.exists():
            return []
        
        games = []
        for f in games_dir.glob("*.json"):
            if f.stem.startswith("_"):  # 跳过模板文件
                continue
            games.append(f.stem)
        return sorted(games)
    
    def list_styles(self) -> List[str]:
        """列出所有可用风格"""
        styles_dir = self.config_base / "styles"
        if not styles_dir.exists():
            return []
        
        return sorted([f.stem for f in styles_dir.glob("*.json")])
    
    def list_themes(self, game_key: Optional[str] = None) -> List[str]:
        """
        列出所有可用主题
        
        Args:
            game_key: 如果提供，返回该游戏可用的主题（含自定义）
        """
        themes = set(self.load_default_themes().keys())
        
        if game_key:
            try:
                game_config = self._load_json(f"games/{game_key}.json")
                themes.update(game_config.get("themes", {}).get("custom", {}).keys())
            except FileNotFoundError:
                pass
        
        return sorted(list(themes))
    
    def clear_cache(self):
        """清除配置缓存"""
        self._cache.clear()


# 便捷函数
def get_loader(config_base_path: Optional[str] = None) -> ConfigLoader:
    """获取配置加载器实例"""
    return ConfigLoader(config_base_path)


def load_game(game_key: str, config_base_path: Optional[str] = None) -> Dict[str, Any]:
    """快捷函数：加载游戏配置"""
    loader = ConfigLoader(config_base_path)
    return loader.load_game_config(game_key)


if __name__ == "__main__":
    # 测试
    loader = ConfigLoader()
    
    print("=== 已配置游戏 ===")
    for game in loader.list_games():
        print(f"  - {game}")
    
    print("\n=== 可用风格 ===")
    for style in loader.list_styles():
        print(f"  - {style}")
    
    print("\n=== 默认主题 ===")
    for theme in loader.list_themes():
        print(f"  - {theme}")
    
    print("\n=== 心动小镇配置 ===")
    config = loader.load_game_config("heartopia")
    print(f"游戏名: {config['game_name']}")
    print(f"参考图数量: {len(config['reference_images'])}")
    print(f"可用主题数: {len(config['themes'])}")
    print(f"角色模式: {list(config['character_modes'].keys())}")
