#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心动小镇 - 赛车系列皮肤公告图生成
"""
import sys
sys.path.insert(0, 'scripts')
from image_generator import ImageGenerator

# 创建生成器
gen = ImageGenerator(game_key="heartopia")

# 生成赛车主题公告图
result = gen.generate(
    main_title="极速风暴",
    sub_title="全新赛车系列皮肤登场",
    theme="default",  # 使用默认主题，可以换成其他主题如 "alien" 等
    character_mode="double",  # 双角色展示皮肤
    character_desc="穿着赛车手主题服装，头戴头盔，身穿炫酷赛车服",
    character_action="兴奋地展示全新赛车坐骑，一个角色驾驶赛车，另一个角色挥舞方格旗",
    expression="超级兴奋、眼神坚定",
    scene_elements="心动小镇赛车场——彩色旗帜飘扬、轮胎装饰、终点线、看台观众",
    n=2  # 生成2张图供选择
)

print("\n" + "="*60)
print("生成完成!")
print("="*60)
print(f"游戏: {result['game_name']}")
print(f"主题: {result['theme']}")
print(f"角色模式: {result['character_mode']}")
print(f"\n图片已保存到:")
for path in result['output_paths']:
    print(f"  - {path}")
