#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'scripts')
from image_generator import ImageGenerator

# 自定义Prompt，覆盖默认模板
custom_prompt = """一张温馨可爱的《心动小镇》版本预告海报，16:9。

【固定规范】
画面风格：手绘插画风，色彩明亮柔和，带一点日系/治愈系游戏UI感。
技术要求：信息层级清晰易读，色彩搭配和谐，符合治愈系游戏调性，画面构图平衡。

【画面布局】
- 正中央：心动小镇Logo（占屏幕25%以上，是画面唯一核心视觉焦点）
- Logo正下方：副标题文字区域（居中对齐，清晰可见）
- 无角色、无其他装饰元素，画面简洁干净

【背景】
温暖的橘黄色渐变背景，带有细腻的纸张纹理或布纹质感，纹理适量不抢眼，整体色调柔和温馨。

【文字区域】
- 主标题："心动小镇"（Logo本身，居中放置）
- 副标题："5月22日 版本先知"（第一行，Logo正下方）
- 副标题："5月28日 全新版本登场！"（第二行，继续下方，字体稍大更醒目）

整体氛围：温馨、期待、可爱、简洁大方"""

# 创建生成器
gen = ImageGenerator(game_key="heartopia")

# 直接调用API生成
gen.api_config = gen._load_api_config()
config = gen.config

import requests
from pathlib import Path
from datetime import datetime

payload = {
    "model": "doubao-seedream-4-5-251128",
    "prompt": custom_prompt,
    "sequential_image_generation": "disabled",
    "image": config["reference_images"],
    "size": "2K",
    "watermark": False,
    "max_images": 1,
    "response_format": "url",
    "stream": False
}

headers = {
    "Authorization": f"Bearer {gen.api_config['api_key']}",
    "Content-Type": "application/json"
}

api_url = f"{gen.api_config.get('api_base_url', 'https://ark.cn-beijing.volces.com/api/v3')}/images/generations"

print("正在生成...")
response = requests.post(api_url, headers=headers, json=payload, timeout=300)
response.raise_for_status()
result = response.json()

# 下载图片
output_path = "D:/App Dev/openclaw-main/data/game_data/announcement_images/heartopia/heartopia_logo_v2.jpeg"

if 'data' in result:
    img_url = result['data'][0].get('url')
    if img_url:
        img_response = requests.get(img_url, timeout=60)
        img_response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(img_response.content)
        print(f"已保存: {output_path}")
