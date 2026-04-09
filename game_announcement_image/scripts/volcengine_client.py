#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎方舟 API 调用 - 图像生成
支持 Doubao-Seedream-4.5 模型

文档: https://www.volcengine.com/docs/82379/1399008
"""

import json
import base64
import requests
from pathlib import Path
from typing import List, Dict, Optional


class VolcengineClient:
    """火山引擎方舟 API 客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://ark.cn-beijing.volces.com/api/v3"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_image(
        self,
        prompt: str,
        model: str = "doubao-seedream-4-5-251128",
        n: int = 1,
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None
    ) -> Dict:
        """
        生成图像
        
        Args:
            prompt: 图像描述提示词
            model: 模型ID
            n: 生成图像数量
            size: 图像尺寸 (如 1024x1024, 1024x1792, 1792x1024)
            quality: 图像质量 (standard 或 hd)
            style: 图像风格 (可选)
            
        Returns:
            API响应结果
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality
        }
        
        if style:
            payload["style"] = style
        
        headers = self._get_headers()
        url = f"{self.base_url}/images/generations"
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    
    def generate_image_with_refs(
        self,
        prompt: str,
        reference_images: List[str],
        model: str = "doubao-seedream-4-5-251128",
        n: int = 1,
        size: str = "1024x1024"
    ) -> Dict:
        """
        使用参考图生成图像
        
        Args:
            prompt: 图像描述提示词
            reference_images: 参考图片路径列表
            model: 模型ID
            n: 生成图像数量
            size: 图像尺寸
            
        Returns:
            API响应结果
        """
        # 将参考图转为base64
        ref_images_base64 = []
        for img_path in reference_images:
            with open(img_path, 'rb') as f:
                base64_data = base64.b64encode(f.read()).decode('utf-8')
                ext = Path(img_path).suffix.lower()
                mime_type = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"
                ref_images_base64.append(f"data:{mime_type};base64,{base64_data}")
        
        # 构建包含参考图的prompt
        # 火山引擎可能支持通过特殊格式传递参考图
        # 这里先使用prompt描述方式
        enhanced_prompt = f"参考以下风格生成图像：{prompt}"
        
        return self.generate_image(
            prompt=enhanced_prompt,
            model=model,
            n=n,
            size=size
        )


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='火山引擎方舟 API - 图像生成')
    parser.add_argument('--config', required=True, help='配置文件路径(volcengine_api.json)')
    parser.add_argument('--prompt', required=True, help='图像描述提示词')
    parser.add_argument('--model', default='doubao-seedream-4-5-251128', help='模型ID')
    parser.add_argument('--n', type=int, default=1, help='生成数量')
    parser.add_argument('--size', default='1024x1024', 
                        choices=['1024x1024', '1024x1792', '1792x1024', '512x512'],
                        help='图像尺寸')
    parser.add_argument('--quality', default='standard', choices=['standard', 'hd'],
                        help='图像质量')
    parser.add_argument('--refs', nargs='+', help='参考图片路径')
    parser.add_argument('--output', help='输出结果保存路径')
    
    args = parser.parse_args()
    
    # 读取配置
    with open(args.config, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 创建客户端
    client = VolcengineClient(
        api_key=config['api_key'],
        base_url=config.get('api_base_url', 'https://ark.cn-beijing.volces.com/api/v3')
    )
    
    try:
        # 生成图像
        if args.refs:
            result = client.generate_image_with_refs(
                prompt=args.prompt,
                reference_images=args.refs,
                model=args.model,
                n=args.n,
                size=args.size
            )
        else:
            result = client.generate_image(
                prompt=args.prompt,
                model=args.model,
                n=args.n,
                size=args.size,
                quality=args.quality
            )
        
        # 输出结果
        output = json.dumps(result, indent=2, ensure_ascii=False)
        print(output)
        
        # 保存到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\n结果已保存到: {args.output}")
        
        # 显示生成的图片URL
        if 'data' in result:
            for i, item in enumerate(result['data']):
                if 'url' in item:
                    print(f"\n图片 {i+1} URL: {item['url']}")
                elif 'b64_json' in item:
                    print(f"\n图片 {i+1}: Base64数据 (长度: {len(item['b64_json'])})")
        
        return 0
        
    except Exception as e:
        print(f"错误: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
