#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'scripts')
import requests
import json

# 加载API配置
config_path = "config/volcengine_api.json"
with open(config_path, 'r', encoding='utf-8') as f:
    api_config = json.load(f)

# 只用心动小镇8张参考图
ref_urls = [
    "https://img2-tc.tapimg.com/moment/etag/FjSX_iltfweQnyj9XqF2Naml0vMG_20260306165555.jpg/_tap_ugc.jpg",
    "https://img2-tc.tapimg.com/moment/etag/FklCYDD11W49qhjsHk6J6RaGHbUd_20260128152132.jpg/_tap_ugc.jpg",
    "https://img2-tc.tapimg.com/moment/etag/FoGeCBAn1smL8nidtmcbdJ1dZdi6_20260109102534.jpg/_tap_ugc.jpg",
    "https://img2-tc.tapimg.com/moment/etag/Fi_v57DrNBocoomvTt3FXU8V1AqS_20251208151456.jpg/_tap_ugc.jpg",
    "https://img2-tc.tapimg.com/moment/etag/FldrfzEyyPF1xP451cGRCwo0JBP9_20260122174319.png/_tap_ugc.jpg",
    "https://img2-tc.tapimg.com/moment/etag/FhewBX82mHph6Nm8lhp5t_apn5am.jpg/_tap_ugc_m.jpg",
    "https://img2-tc.tapimg.com/moment/etag/FtLCNfFU2xwKOoNxO7AU5759tw7G.png/_tap_ugc_m.jpg",
    "https://img2-tc.tapimg.com/moment/etag/Fsw9J7JfmdYSC2Up1n5tJ_cbQuTg_20251127143416.jpg/_tap_ugc_m.jpg"
]

# 详细的Prompt，描述动物森友会风格
custom_prompt = """心动小镇版本预告宣传图，16:9横版。

【布局要求-类似动物森友会风格】：
- 画面中央：心动小镇Logo（占画面高度约25%，居中放置，周围适当留白）
- Logo下方居中：分两行显示日期
  * 第一行："5月22日 版本先知"（精致小字，优雅字体）
  * 第二行："5月28日 全新版本登场！"（稍大字号，突出显示）
- 无角色、无其他装饰元素、画面极简

【背景要求】：
- 温暖的橘黄色/米黄色渐变
- 添加细腻的纸张纹理或布纹，类似牛皮纸或手工纸质感
- 纹理均匀、淡雅，不抢眼
- 整体色调温暖柔和，高明度低饱和度

【风格】：
- 日系治愈游戏UI风格
- 手绘插画感
- 简洁大方，重点突出Logo和文字
- 类似动物森友会的标题画面风格

禁止：多个Logo、角色、复杂图案"""

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
output_path = "D:/App Dev/openclaw-main/data/game_data/announcement_images/heartopia/heartopia_version_v4.jpeg"

if 'data' in result:
    img_url = result['data'][0].get('url')
    if img_url:
        img_response = requests.get(img_url, timeout=60)
        img_response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(img_response.content)
        print(f"已保存: {output_path}")
