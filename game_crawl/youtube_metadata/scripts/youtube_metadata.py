#!/usr/bin/env python3
"""
YouTube Metadata - 搜索获取视频元数据，包含发布日期
使用 Supadata Python SDK，支持 checkpoint 和规范化存储

Usage:
    python youtube_metadata.py --game-id g_genshin --query "Tolan app review" --limit 30
    python youtube_metadata.py --game-id g_genshin --query "Tolan app review" --limit 30 --resume
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# 设置 stdout 编码为 utf-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from supadata import Supadata, SupadataError

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index


def _get_api_key() -> str:
    key = os.environ.get("SUPADATA_API_KEY", "").strip()
    if not key:
        raise ValueError("SUPADATA_API_KEY 环境变量未设置")
    return key


def get_video_metadata(supadata: Supadata, video_id: str) -> dict:
    """获取单个视频的详细元数据（含发布日期）"""
    try:
        video = supadata.metadata(url=f"https://youtube.com/watch?v={video_id}")
        return {
            "published_at": video.created_at.isoformat() if video.created_at else "",
            "author": video.author.display_name if video.author else "",
            "likes": video.stats.likes if video.stats else 0,
        }
    except Exception as e:
        print(f"  [metadata] 获取失败 {video_id}: {e}", file=sys.stderr)
        return {"published_at": "", "author": "", "likes": 0}


def search_videos(query: str, limit: int, api_key: str, storage: DataStorage, resume: bool = False) -> list:
    """使用 Supadata SDK 搜索视频，支持 checkpoint 和获取发布日期"""
    supadata = Supadata(api_key=api_key)
    
    videos = []
    checkpoint_num = 0
    
    # 如果 resume，加载最新 checkpoint
    if resume:
        latest = storage.get_latest_checkpoint("youtube", "metadata")
        if latest > 0:
            cp_data = storage.load_checkpoint(latest, "youtube", "metadata")
            videos = cp_data.get("items", [])
            checkpoint_num = latest
            print(f"[youtube_metadata] 从 checkpoint {latest} 恢复，已有 {len(videos)} 个视频")
    
    try:
        # 搜索视频
        print(f"[youtube_metadata] 搜索: {query}")
        result = supadata.youtube.search(
            query=query,
            type="video",
            limit=limit,
            sort_by="relevance",
            duration="medium",
        )
        
        print(f"[youtube_metadata] 搜索返回 {len(result.results)} 个视频，开始获取详情...")
        
        for i, v in enumerate(result.results):
            # 处理 channel 可能是 dict 的情况
            channel_name = ""
            if v.channel:
                if isinstance(v.channel, dict):
                    channel_name = v.channel.get("name", "")
                else:
                    channel_name = getattr(v.channel, "name", "")
            
            video_data = {
                "id": v.id,
                "title": v.title,
                "channel": channel_name,
                "url": f"https://youtube.com/watch?v={v.id}",
                "view_count": v.view_count or 0,
                "duration": v.duration or 0,
                "published_at": "",
            }
            
            # 获取详细元数据（含发布日期）
            safe_title = v.title[:40].encode('utf-8', errors='ignore').decode('utf-8')
            print(f"  [{i+1}/{len(result.results)}] 获取详情: {safe_title}...")
            metadata = get_video_metadata(supadata, v.id)
            video_data["published_at"] = metadata.get("published_at", "")
            
            videos.append(video_data)
            
            # 每 10 个保存一次 checkpoint
            if (i + 1) % 10 == 0:
                checkpoint_num += 1
                storage.save_checkpoint(
                    {"items": videos, "query": query},
                    checkpoint_num,
                    "youtube",
                    "metadata"
                )
                print(f"  [checkpoint] 已保存 {checkpoint_num}")
            
            # 避免 API 限流
            time.sleep(0.5)
        
        # 最终 checkpoint
        if videos:
            storage.save_checkpoint(
                {"items": videos, "query": query},
                checkpoint_num + 1,
                "youtube",
                "metadata"
            )
        
        return videos
        
    except SupadataError as e:
        print(f"[youtube_metadata] Supadata 错误: {e.message}", file=sys.stderr)
        return videos


def main():
    parser = argparse.ArgumentParser(description="YouTube Metadata 搜索")
    parser.add_argument("--game-id", required=True, help="游戏ID（如 g_genshin）")
    parser.add_argument("--query", required=True, help="搜索关键词（英文）")
    parser.add_argument("--limit", type=int, default=30, help="数量限制")
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    parser.add_argument("--output", help="输出文件（可选，默认使用规范路径）")
    args = parser.parse_args()
    
    try:
        api_key = _get_api_key()
    except ValueError as e:
        print(f"[youtube_metadata] 错误: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 初始化存储
    storage = DataStorage(args.game_id)
    
    print(f"[youtube_metadata] 搜索: {args.query}, 限制: {args.limit}")
    if args.resume:
        print("[youtube_metadata] 启用断点续传模式")
    
    videos = search_videos(args.query, args.limit, api_key, storage, args.resume)
    print(f"[youtube_metadata] 完成，共 {len(videos)} 个视频")
    
    # 构建数据
    result = {
        "platform": "youtube",
        "game_id": args.game_id,
        "data_type": "metadata",
        "phase": "metadata",
        "query": args.query,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(videos),
        "items": videos,
    }
    
    # 保存到规范路径或指定路径
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[youtube_metadata] 输出: {args.output}")
    else:
        # 使用规范化存储
        output_path = storage.merge_and_save(result, "youtube", "metadata", id_field="id")
        print(f"[youtube_metadata] 输出: {output_path}")
    
    # 更新数据索引
    if not args.output:
        update_index(args.game_id, args.game_id, "youtube", "metadata", count=len(videos))
    
    # 清理旧 checkpoint
    storage.clean_checkpoints(keep_latest=3)


if __name__ == "__main__":
    main()
