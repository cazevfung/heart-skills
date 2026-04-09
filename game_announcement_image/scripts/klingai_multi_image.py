#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可灵AI (KlingAI) API 调用 - 多图参考生图
文档: https://app.klingai.com/cn/dev/document-api/apiReference/model/multiImageToImage

注意：Base64图片不要加 data:image/png;base64, 前缀
"""

import json
import time
import hmac
import hashlib
import base64
import requests
from pathlib import Path
from typing import List, Dict, Optional


class KlingAIClient:
    """可灵AI API 客户端 - 多图参考生图"""
    
    def __init__(self, access_key: str, secret_key: str, base_url: str = "https://api-beijing.klingai.com"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip('/')
    
    def _generate_token(self) -> str:
        """生成JWT认证令牌 (纯Python实现，不依赖PyJWT)"""
        # JWT Header
        header = json.dumps({"alg": "HS256", "typ": "JWT"})
        header_b64 = base64.urlsafe_b64encode(header.encode()).decode().rstrip('=')
        
        # JWT Payload - 需要包含nbf字段
        now = int(time.time())
        payload = json.dumps({
            "iss": self.access_key,
            "iat": now - 60,  # 签发时间（稍微提前一点避免时钟偏差）
            "nbf": now - 60,  # 生效时间（not before）
            "exp": now + 3600  # 过期时间：1小时
        })
        payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')
        
        # 签名
        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        return f"{message}.{signature_b64}"
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        token = self._generate_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def _encode_image(self, image_path: str) -> str:
        """
        将图片转为Base64字符串（不带data:前缀）
        可灵API要求：直接传递Base64编码后的字符串，不要加 data:image/png;base64, 前缀
        """
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def multi_image_to_image(
        self,
        subject_images: List[str],
        prompt: str,
        model_name: str = "kling-v2",
        scene_image: Optional[str] = None,
        style_image: Optional[str] = None,
        negative_prompt: str = "",
        n: int = 1,
        aspect_ratio: str = "16:9",
        callback_url: Optional[str] = None,
        external_task_id: Optional[str] = None
    ) -> Dict:
        """
        多图参考生图
        
        Args:
            subject_images: 主体参考图片路径列表 (1-4张)
            prompt: 正向文本提示词（不超过2500字符）
            model_name: 模型名称 (kling-v2, kling-v2-1)
            scene_image: 场景参考图路径（可选）
            style_image: 风格参考图路径（可选）
            negative_prompt: 负向提示词
            n: 生成图片数量 (1-9)
            aspect_ratio: 画面纵横比 (16:9, 9:16, 1:1, 4:3, 3:4, 3:2, 2:3, 21:9)
            callback_url: 回调通知地址（可选）
            external_task_id: 自定义任务ID（可选）
            
        Returns:
            API响应结果，包含task_id、task_status等
        """
        if len(subject_images) < 1 or len(subject_images) > 4:
            raise ValueError("主体参考图需要1-4张")
        
        if n < 1 or n > 9:
            raise ValueError("生成数量n需要在1-9之间")
        
        # 构建subject_image_list
        subject_image_list = [
            {"subject_image": self._encode_image(path)}
            for path in subject_images
        ]
        
        # 构建请求体
        payload = {
            "model_name": model_name,
            "prompt": prompt,
            "subject_image_list": subject_image_list,
            "n": n,
            "aspect_ratio": aspect_ratio
        }
        
        # 可选参数
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if scene_image:
            payload["scene_image"] = self._encode_image(scene_image)
        if style_image:
            payload["style_image"] = self._encode_image(style_image)
        if callback_url:
            payload["callback_url"] = callback_url
        if external_task_id:
            payload["external_task_id"] = external_task_id
        
        headers = self._get_headers()
        url = f"{self.base_url}/v1/images/multi-image2image"
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    
    def query_task(self, task_id: str) -> Dict:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务详情，包含task_status、task_result等
        """
        headers = self._get_headers()
        url = f"{self.base_url}/v1/images/multi-image2image/{task_id}"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def query_task_list(self, page_num: int = 1, page_size: int = 30) -> Dict:
        """
        查询任务列表
        
        Args:
            page_num: 页码 (1-1000)
            page_size: 每页数据量 (1-500)
            
        Returns:
            任务列表
        """
        headers = self._get_headers()
        url = f"{self.base_url}/v1/images/multi-image2image"
        params = {
            "pageNum": page_num,
            "pageSize": page_size
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='可灵AI API - 多图参考生图')
    parser.add_argument('--config', required=True, help='配置文件路径(klingai_api.json)')
    parser.add_argument('--subject-images', nargs='+', help='主体参考图片路径 (1-4张)')
    parser.add_argument('--prompt', help='正向文本提示词')
    parser.add_argument('--model-name', default='kling-v2', help='模型名称 (kling-v2, kling-v2-1)')
    parser.add_argument('--scene-image', help='场景参考图路径')
    parser.add_argument('--style-image', help='风格参考图路径')
    parser.add_argument('--negative-prompt', default='', help='负向提示词')
    parser.add_argument('--n', type=int, default=1, help='生成图片数量 (1-9)')
    parser.add_argument('--aspect-ratio', default='16:9', 
                        choices=['16:9', '9:16', '1:1', '4:3', '3:4', '3:2', '2:3', '21:9'],
                        help='画面纵横比')
    parser.add_argument('--query', help='查询指定task_id的状态')
    parser.add_argument('--output', help='输出结果保存路径')
    
    args = parser.parse_args()
    
    # 读取配置
    with open(args.config, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 创建客户端
    client = KlingAIClient(
        access_key=config['access_key'],
        secret_key=config['secret_key'],
        base_url=config.get('api_base_url', 'https://api-beijing.klingai.com')
    )
    
    try:
        # 查询模式
        if args.query:
            result = client.query_task(args.query)
        else:
            # 生成模式 - 检查必需参数
            if not args.subject_images:
                print("错误: 生成模式需要提供 --subject-images 参数")
                return 1
            if not args.prompt:
                print("错误: 生成模式需要提供 --prompt 参数")
                return 1
            result = client.multi_image_to_image(
                subject_images=args.subject_images,
                prompt=args.prompt,
                model_name=args.model_name,
                scene_image=args.scene_image,
                style_image=args.style_image,
                negative_prompt=args.negative_prompt,
                n=args.n,
                aspect_ratio=args.aspect_ratio
            )
        
        # 输出结果
        output = json.dumps(result, indent=2, ensure_ascii=False)
        print(output)
        
        # 保存到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\n结果已保存到: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"错误: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
