#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏公告封面图生成器 - 火山引擎 Doubao-Seedream-4.5
主题化模板v3（角色多样性 + 面积控制）
"""

import json
import requests
from pathlib import Path


# 心动小镇参考图URL列表（8张）
HEARTOPIA_REF_IMAGES = [
    "https://img2-tc.tapimg.com/moment/etag/FjSX_iltfweQnyj9XqF2Naml0vMG_20260306165555.jpg/_tap_ugc.jpg",
    "https://img2-tc.tapimg.com/moment/etag/FklCYDD11W49qhjsHk6J6RaGHbUd_20260128152132.jpg/_tap_ugc.jpg",
    "https://img2-tc.tapimg.com/moment/etag/FoGeCBAn1smL8nidtmcbdJ1dZdi6_20260109102534.jpg/_tap_ugc.jpg",
    "https://img2-tc.tapimg.com/moment/etag/Fi_v57DrNBocoomvTt3FXU8V1AqS_20251208151456.jpg/_tap_ugc.jpg",
    "https://img2-tc.tapimg.com/moment/etag/FldrfzEyyPF1xP451cGRCwo0JBP9_20260122174319.png/_tap_ugc.jpg",
    "https://img2-tc.tapimg.com/moment/etag/FhewBX82mHph6Nm8lhp5t_apn5am.jpg/_tap_ugc_m.jpg",
    "https://img2-tc.tapimg.com/moment/etag/FtLCNfFU2xwKOoNxO7AU5759tw7G.png/_tap_ugc_m.jpg",
    "https://img2-tc.tapimg.com/moment/etag/Fsw9J7JfmdYSC2Up1n5tJ_cbQuTg_20251127143416.jpg/_tap_ugc_m.jpg"
]


# 主题配置库
THEME_CONFIGS = {
    "default": {
        "background": "浅蓝天空，几朵白云，少量小花点缀",
        "atmosphere": "友好、温馨、期待、新鲜感",
        "lighting": "明亮的阳光",
        "mood": "温馨日常"
    },
    "alien": {
        "background": "深蓝紫色渐变星空，闪烁的星星，远处有飞碟发出的神秘光束",
        "atmosphere": "神秘、奇幻、探索、未来感",
        "lighting": "柔和的星光和飞碟光效",
        "mood": "夜晚神秘"
    },
    "school": {
        "background": "秋日黄昏天空，暖黄色调，几片飘落的梧桐叶",
        "atmosphere": "温馨、学院风、秋日、书卷气",
        "lighting": "温暖的午后阳光",
        "mood": "秋日学院"
    },
    "halloween": {
        "background": "暗紫色夜空，一轮明月，南瓜灯点缀",
        "atmosphere": "神秘、俏皮、节日氛围、惊喜",
        "lighting": "南瓜灯的暖光和月光",
        "mood": "夜晚节日"
    },
    "summer": {
        "background": "清澈的蓝天，蓬松的白云，海边或泳池元素",
        "atmosphere": "清凉、活力、夏日、放松",
        "lighting": "明亮的夏日阳光",
        "mood": "夏日清凉"
    }
}


# 角色数量配置
CHARACTER_CONFIGS = {
    "single": {
        "count_desc": "一个可爱的卡通角色",
        "area_ratio": "角色形象要饱满突出，占屏幕25%以上",
        "interaction": "单独展示"
    },
    "double": {
        "count_desc": "两个可爱的卡通角色",
        "area_ratio": "两个角色都要饱满突出，合计占屏幕40%以上，是画面的主要视觉焦点",
        "interaction": "一起互动展示"
    },
    "multiple": {
        "count_desc": "多个可爱的卡通角色",
        "area_ratio": "角色们饱满突出，合计占屏幕45%以上，是画面的主要视觉焦点",
        "interaction": "热闹地一起展示"
    }
}


def build_prompt_v3(
    game_name: str = "心动小镇",
    main_title: str = "更新公告",
    sub_title: str = "全新内容上线",
    theme: str = "default",
    character_mode: str = "single",  # single/double/multiple
    character_desc: str = "穿着休闲服装",
    character_action: str = "开心地展示新物品",
    expression: str = "开心",
    scene_elements: str = "小镇街景——小房子、绿树",
    dynamic_pose: str = None  # 皮肤类可传入浮夸动作
) -> str:
    """
    使用主题化模板v3构建Prompt
    
    固定规范 + 可变主题内容 + 角色多样性控制
    """
    
    # 获取主题配置
    theme_config = THEME_CONFIGS.get(theme, THEME_CONFIGS["default"])
    char_config = CHARACTER_CONFIGS.get(character_mode, CHARACTER_CONFIGS["single"])
    
    # 根据类型调整动作描述
    if dynamic_pose:
        action_desc = dynamic_pose
    elif character_mode == "single":
        action_desc = f"{character_action}，姿态自然大方"
    else:
        action_desc = f"{character_action}，动作夸张有张力，姿态生动活泼"
    
    prompt = f"""一张温馨可爱的《{game_name}》更新公告海报，16:9。

【固定规范】
画面风格：手绘插画风，色彩明亮柔和，带一点日系/治愈系游戏UI感。
画面布局：左上角放置游戏Logo区域，中左部预留文字区域，视觉焦点在右边、标题在左边。
技术要求：信息层级清晰易读，色彩搭配和谐，符合治愈系游戏调性，画面构图平衡。

【主题内容】
主题氛围：{theme_config['mood']}
光线效果：{theme_config['lighting']}

主体元素：
- 前景（画面核心）：{char_config['count_desc']}，{character_desc}，{char_config['interaction']}，{action_desc}，表情{expression}。{char_config['area_ratio']}，角色与参考图中风格保持高度一致。角色要画得大一些，是画面的主要视觉焦点。
- 中景：卡通风格的{scene_elements}，有"{game_name}"的{theme_config['atmosphere'].split('、')[0]}生活感
- 背景：{theme_config['background']}

文字区域：
- 主标题："{main_title}"（醒目字体，左上角区域）
- 副标题："{sub_title}"（清晰字体，主标题下方）

整体氛围：{theme_config['atmosphere']}"""
    
    return prompt


def generate_image(
    prompt: str,
    output_path: str,
    reference_images: list = None
) -> dict:
    """生成图片"""
    
    if reference_images is None:
        reference_images = HEARTOPIA_REF_IMAGES
    
    config_path = Path(__file__).parent.parent / "config" / "volcengine_api.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    payload = {
        "model": "doubao-seedream-4-5-251128",
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "image": reference_images,
        "size": "2K",
        "watermark": False,
        "max_images": 2,
        "response_format": "url",
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    api_url = f"{config.get('api_base_url', 'https://ark.cn-beijing.volces.com/api/v3')}/images/generations"
    
    response = requests.post(api_url, headers=headers, json=payload, timeout=300)
    response.raise_for_status()
    result = response.json()
    
    # 下载图片
    if 'data' in result:
        for i, img_data in enumerate(result['data']):
            img_url = img_data.get('url')
            if img_url:
                img_response = requests.get(img_url, timeout=60)
                img_response.raise_for_status()
                
                save_path = output_path if i == 0 else output_path.replace('.jpeg', f'_{i+1}.jpeg')
                with open(save_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"Saved: {save_path}")
    
    return result


def main():
    """测试外星人主题 - 双角色（皮肤类）"""
    
    # 构建外星人主题Prompt - 两个角色（皮肤套装展示）
    prompt = build_prompt_v3(
        theme="alien",
        character_mode="double",  # 两个角色
        main_title="外星来客",
        sub_title="全新外星人主题外观上线",
        character_desc="穿着外星人主题发光服装，头戴天线头饰",
        character_action="兴奋地指向天空中的飞碟，身体前倾，一个角色跳起来挥手，另一个角色摆出邀请姿势",
        expression="超级兴奋、眼睛闪闪发光",
        scene_elements="小镇夜晚场景——飞碟悬浮在空中、星星闪烁、神秘光效照亮地面",
        dynamic_pose="动作夸张有活力，一个角色单脚跳起双手高举，另一个角色张开双臂做欢迎姿势，充满动感和张力"
    )
    
    print("=" * 60)
    print("外星人主题 Prompt (双角色 - 皮肤类):")
    print("=" * 60)
    print(prompt)
    print("=" * 60)
    
    # 生成
    output = "D:/App Dev/openclaw-main/data/game_data/announcement_images/heartopia_alien_double.jpeg"
    result = generate_image(prompt=prompt, output_path=output)
    
    print("\nResult:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == '__main__':
    exit(main())
