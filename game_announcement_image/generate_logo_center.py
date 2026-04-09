#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'scripts')
from image_generator import ImageGenerator

# 创建生成器
gen = ImageGenerator(game_key="heartopia")

# 清除配置缓存以加载新的 character_modes
gen.loader.clear_cache()
gen.config = gen.loader.load_game_config("heartopia")

# 生成无角色的Logo居中版本预告图
result = gen.generate(
    main_title="心动小镇",
    sub_title="5月22日 版本先知\n5月28日 全新版本登场！",
    theme="default",
    character_mode="none",
    character_desc="无角色",
    character_action="",
    expression="",
    scene_elements="橘黄色温暖背景，带有细腻的纹理和质感，简单干净，无其他元素",
    output_path="D:/App Dev/openclaw-main/data/game_data/announcement_images/heartopia/heartopia_logo_version_preview.jpeg",
    n=1
)

print("\n生成完成!")
print(f"保存路径: {result['output_paths'][0]}")
