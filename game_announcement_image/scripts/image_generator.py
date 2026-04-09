#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏公告图生成器 v2.0
支持多游戏、配置驱动、主题化生成
"""

import json
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from config_loader import ConfigLoader, load_game


class ImageGenerator:
    """游戏公告图生成器"""
    
    def __init__(self, game_key: str, config_base_path: Optional[str] = None):
        """
        初始化生成器
        
        Args:
            game_key: 游戏标识符，如 "heartopia"
            config_base_path: 配置根目录路径
        """
        self.game_key = game_key
        self.config = load_game(game_key, config_base_path)
        self.loader = ConfigLoader(config_base_path)
        
        # 加载API配置
        self.api_config = self._load_api_config()
    
    def _load_api_config(self) -> dict:
        """加载火山引擎API配置"""
        config_path = Path(__file__).parent.parent / "config" / "volcengine_api.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate(
        self,
        main_title: str,
        sub_title: str = "",
        theme: Optional[str] = None,
        character_mode: Optional[str] = None,
        character_desc: str = "穿着休闲服装",
        character_action: str = "开心地展示新物品",
        expression: str = "开心",
        scene_elements: str = "小镇街景——小房子、绿树",
        dynamic_pose: Optional[str] = None,
        game_name: Optional[str] = None,
        output_path: Optional[str] = None,
        n: int = 2
    ) -> Dict[str, Any]:
        """
        生成公告图
        
        Args:
            main_title: 主标题
            sub_title: 副标题
            theme: 主题ID，默认使用游戏配置的 default_theme
            character_mode: 角色模式 single/double/multiple，默认使用游戏配置
            character_desc: 角色服装描述
            character_action: 角色动作描述
            expression: 角色表情
            scene_elements: 场景元素描述
            dynamic_pose: 动态动作描述（皮肤类可用夸张动作）
            game_name: 游戏名，默认使用配置中的 game_name
            output_path: 输出路径，默认使用游戏配置的 save_dir
            n: 生成数量
            
        Returns:
            包含生成结果和本地路径的字典
        """
        # 使用默认值
        theme = theme or self.config["visual"].get("default_theme", "default")
        character_mode = character_mode or self.config["visual"].get("default_character_mode", "single")
        game_name = game_name or self.config["game_name"]
        
        # 构建Prompt
        prompt = self.build_prompt(
            game_name=game_name,
            main_title=main_title,
            sub_title=sub_title,
            theme=theme,
            character_mode=character_mode,
            character_desc=character_desc,
            character_action=character_action,
            expression=expression,
            scene_elements=scene_elements,
            dynamic_pose=dynamic_pose
        )
        
        # 确定输出路径
        if output_path is None:
            output_path = self._generate_output_path(theme, character_mode)
        
        # 调用API生成
        result = self._call_api(prompt, n=n)
        
        # 下载并保存图片
        saved_paths = self._download_images(result, output_path, n)
        
        return {
            "success": True,
            "game_key": self.game_key,
            "game_name": game_name,
            "theme": theme,
            "character_mode": character_mode,
            "prompt": prompt,
            "output_paths": saved_paths,
            "api_response": result
        }
    
    def build_prompt(
        self,
        game_name: str,
        main_title: str,
        sub_title: str,
        theme: str,
        character_mode: str,
        character_desc: str,
        character_action: str,
        expression: str,
        scene_elements: str,
        dynamic_pose: Optional[str] = None
    ) -> str:
        """
        构建生成Prompt
        
        使用配置中的模板和主题/角色模式数据
        """
        # 获取主题配置
        theme_config = self.config["themes"].get(theme)
        if not theme_config:
            available = list(self.config["themes"].keys())
            raise ValueError(f"主题 '{theme}' 不存在。可用主题: {available}")
        
        # 获取角色模式配置
        char_config = self.config["character_modes"].get(character_mode)
        if not char_config:
            available = list(self.config["character_modes"].keys())
            raise ValueError(f"角色模式 '{character_mode}' 不存在。可用模式: {available}")
        
        # 获取风格配置
        style_config = self.config["style_config"]
        visual = style_config.get("visual", {})
        
        # 构建动作描述
        if dynamic_pose:
            action_desc = dynamic_pose
        elif character_mode == "single":
            action_desc = f"{character_action}，姿态自然大方"
        else:
            action_desc = f"{character_action}，动作夸张有张力，姿态生动活泼"
        
        # 使用模板构建Prompt
        template = style_config["prompt_template"]["template"]
        
        prompt = template.format(
            game_name=game_name,
            art_style=visual.get("art_style", "手绘插画风，色彩明亮柔和"),
            mood=theme_config["mood"],
            lighting=theme_config["lighting"],
            count_desc=char_config["count_desc"],
            character_desc=character_desc,
            interaction=char_config["interaction"],
            action_desc=action_desc,
            expression=expression,
            area_ratio=char_config["area_ratio"],
            scene_elements=scene_elements,
            atmosphere=theme_config["atmosphere"],
            background=theme_config["background"],
            main_title=main_title,
            sub_title=sub_title
        )
        
        return prompt
    
    def _generate_output_path(self, theme: str, character_mode: str) -> str:
        """生成输出文件路径"""
        output_config = self.config.get("output", {})
        save_dir = output_config.get("default_save_dir", f"data/game_data/announcement_images/{self.game_key}")
        naming_pattern = output_config.get("naming_pattern", "{game_key}_{theme}_{character_mode}_{timestamp}.jpeg")
        
        # 解析路径变量
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = naming_pattern.format(
            game_key=self.game_key,
            theme=theme,
            character_mode=character_mode,
            timestamp=timestamp
        )
        
        # 确保目录存在
        full_dir = Path(save_dir)
        full_dir.mkdir(parents=True, exist_ok=True)
        
        return str(full_dir / filename)
    
    def _call_api(self, prompt: str, n: int = 2) -> dict:
        """调用火山引擎API生成图片"""
        
        api_key = self.api_config.get("api_key")
        base_url = self.api_config.get("api_base_url", "https://ark.cn-beijing.volces.com/api/v3")
        model = self.api_config.get("default_params", {}).get("model", "doubao-seedream-4-5-251128")
        
        # 参考图URL
        reference_images = self.config.get("reference_images", [])
        
        payload = {
            "model": model,
            "prompt": prompt,
            "sequential_image_generation": "disabled",
            "image": reference_images,
            "size": "2K",
            "watermark": False,
            "max_images": n,
            "response_format": "url",
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        api_url = f"{base_url}/images/generations"
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        return response.json()
    
    def _download_images(self, api_result: dict, output_path: str, n: int) -> List[str]:
        """下载生成的图片到本地"""
        saved_paths = []
        
        if "data" not in api_result:
            return saved_paths
        
        for i, img_data in enumerate(api_result["data"]):
            img_url = img_data.get("url")
            if not img_url:
                continue
            
            # 下载图片
            img_response = requests.get(img_url, timeout=60)
            img_response.raise_for_status()
            
            # 确定保存路径
            if i == 0:
                save_path = output_path
            else:
                # 在文件名后添加序号
                path = Path(output_path)
                save_path = str(path.parent / f"{path.stem}_{i+1}{path.suffix}")
            
            # 保存
            with open(save_path, 'wb') as f:
                f.write(img_response.content)
            
            saved_paths.append(save_path)
            print(f"Saved: {save_path}")
        
        return saved_paths
    
    def list_themes(self) -> List[str]:
        """列出当前游戏可用主题"""
        return list(self.config["themes"].keys())
    
    def list_character_modes(self) -> List[str]:
        """列出当前游戏可用角色模式"""
        return list(self.config["character_modes"].keys())
    
    def preview_prompt(
        self,
        main_title: str,
        sub_title: str = "",
        theme: Optional[str] = None,
        character_mode: Optional[str] = None,
        **kwargs
    ) -> str:
        """预览生成的Prompt（不调用API）"""
        theme = theme or self.config["visual"].get("default_theme", "default")
        character_mode = character_mode or self.config["visual"].get("default_character_mode", "single")
        game_name = kwargs.get("game_name", self.config["game_name"])
        
        return self.build_prompt(
            game_name=game_name,
            main_title=main_title,
            sub_title=sub_title,
            theme=theme,
            character_mode=character_mode,
            character_desc=kwargs.get("character_desc", "穿着休闲服装"),
            character_action=kwargs.get("character_action", "开心地展示新物品"),
            expression=kwargs.get("expression", "开心"),
            scene_elements=kwargs.get("scene_elements", "小镇街景——小房子、绿树"),
            dynamic_pose=kwargs.get("dynamic_pose")
        )


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='游戏公告图生成器 v2.0')
    parser.add_argument('--game', '-g', default='heartopia', help='游戏key (默认: heartopia)')
    parser.add_argument('--main-title', '-t', required=True, help='主标题')
    parser.add_argument('--sub-title', '-s', default='', help='副标题')
    parser.add_argument('--theme', default=None, help='主题 (默认使用游戏配置)')
    parser.add_argument('--character-mode', '-m', default=None, help='角色模式 single/double/multiple')
    parser.add_argument('--character-desc', default='穿着休闲服装', help='角色服装描述')
    parser.add_argument('--character-action', default='开心地展示新物品', help='角色动作描述')
    parser.add_argument('--expression', default='开心', help='角色表情')
    parser.add_argument('--scene', default='小镇街景——小房子、绿树', help='场景元素')
    parser.add_argument('--dynamic-pose', default=None, help='动态动作描述')
    parser.add_argument('--output', '-o', default=None, help='输出路径')
    parser.add_argument('--n', type=int, default=2, help='生成数量')
    parser.add_argument('--preview', '-p', action='store_true', help='仅预览Prompt，不生成')
    
    args = parser.parse_args()
    
    # 创建生成器
    gen = ImageGenerator(args.game)
    
    if args.preview:
        # 仅预览Prompt
        prompt = gen.preview_prompt(
            main_title=args.main_title,
            sub_title=args.sub_title,
            theme=args.theme,
            character_mode=args.character_mode,
            character_desc=args.character_desc,
            character_action=args.character_action,
            expression=args.expression,
            scene_elements=args.scene,
            dynamic_pose=args.dynamic_pose
        )
        print("=" * 60)
        print("Prompt 预览:")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        return 0
    
    # 生成图片
    try:
        result = gen.generate(
            main_title=args.main_title,
            sub_title=args.sub_title,
            theme=args.theme,
            character_mode=args.character_mode,
            character_desc=args.character_desc,
            character_action=args.character_action,
            expression=args.expression,
            scene_elements=args.scene,
            dynamic_pose=args.dynamic_pose,
            output_path=args.output,
            n=args.n
        )
        
        print("\n" + "=" * 60)
        print("生成成功!")
        print("=" * 60)
        print(f"游戏: {result['game_name']}")
        print(f"主题: {result['theme']}")
        print(f"角色模式: {result['character_mode']}")
        print(f"保存路径:")
        for path in result['output_paths']:
            print(f"  - {path}")
        
        return 0
        
    except Exception as e:
        print(f"错误: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
