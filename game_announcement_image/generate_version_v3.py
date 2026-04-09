#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'scripts')
import requests
from datetime import datetime

# 加载配置
import json
config_path = "config/volcengine_api.json"
with open(config_path, 'r', encoding='utf-8') as f:
    api_config = json.load(f)

ref_file = "config/refs/heartopia.txt"
with open(ref_file, 'r', encoding='utf-8') as f:
    ref_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# 精心设计的Prompt - 参考动物森友会风格
custom_prompt = """《心动小镇》版本预告宣传图，16:9横版。

画面布局：
- 正中央：心动小镇游戏Logo（唯一视觉焦点，占画面高度30%）
- Logo正下方：分两行显示日期文字
  第一行："5月22日 版本先知"（较小字号）
  第二行："5月28日 全新版本登场！"（稍大字号，更醒目）
- 无角色、无装饰元素、无其他图案

背景要求：
- 温暖的橘黄色渐变底色
- 添加细微的纸张纹理或布料纹理
- 纹理要淡雅、不抢眼、均匀分布
- 整体色调柔和温馨，类似牛皮纸或暖色宣纸质感

风格：手绘插画风，日系可爱游戏UI感，色彩明亮柔和，高明度低饱和度

禁止：不要出现多个Logo，不要出现角色，不要出现复杂图案"""

payload = {
    "model": "doubao-seedream-4-5-251128",
    "prompt": custom_prompt,
    "sequential_image_generation": "disabled",
    "image": ref_urls,
    "size": "2K",
    "watermark": False,
    "max_images": 1,
    "response_format": "url",
    "stream": False
}

headers = {
    "Authorization": f"Bearer {api_config['api_key']}",
    "Content-Type": "application/json"
}

api_url = f"{api_config.get('api_base_url', 'https://ark.cn-beijing.volces.com/api/v3')}/images/generations"

print("正在生成...")
response = requests.post(api_url, headers=headers, json=payload, timeout=300)
response.raise_for_status()
result = response.json()

# 下载图片
output_path = "D:/App Dev/openclaw-main/data/game_data/announcement_images/heartopia/heartopia_version_v3.jpeg"

if 'data' in result:
    img_url = result['data'][0].get('url')
    if img_url:
        img_response = requests.get(img_url, timeout=60)
        img_response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(img_response.content)
        print(f"已保存: {output_path}")
        print("请查看效果")
