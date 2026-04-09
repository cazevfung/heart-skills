#!/usr/bin/env python3
"""
YouTube Transcript - 仅获取视频转录
使用 Supadata Python SDK，支持 checkpoint 和规范化存储

Usage:
    python youtube_transcript.py --game-id g_genshin --input youtube_metadata.json
    python youtube_transcript.py --game-id g_genshin --input youtube_metadata.json --resume
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from supadata import Supadata, SupadataError

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index


def _get_api_key() -> str:
    key = os.environ.get("SUPADATA_API_KEY", "").strip()
    if not key:
        raise ValueError("SUPADATA_API_KEY 环境变量未设置")
    return key


def get_transcript(video_id: str, api_key: str) -> str:
    """获取单个视频转录"""
    supadata = Supadata(api_key=api_key)
    
    try:
        result = supadata.transcript(
            url=f"https://youtube.com/watch?v={video_id}",
            text=True,
        )
        # 处理不同类型的返回结果
        if result is None:
            return ""
        if hasattr(result, 'content'):
            return result.content
        if hasattr(result, 'text'):
            return result.text
        if isinstance(result, str):
            return result
        # 尝试从 result 对象获取文本
        return str(result) if result else ""
    except SupadataError as e:
        msg = e.message if hasattr(e, 'message') else str(e)
        print(f"  SupadataError: {msg}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        return ""


def load_existing_transcripts(storage: DataStorage) -> dict:
    """加载已有的转录数据，用于增量检测"""
    output_path = storage.get_output_path("youtube", "transcript")
    if not output_path.exists():
        return {}
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 构建 id -> transcript 的映射
            return {item["id"]: item for item in data.get("items", []) if item.get("transcript")}
    except Exception:
        return {}


def process_videos(videos: list, api_key: str, storage: DataStorage, resume: bool = False, incremental: bool = True) -> list:
    """批量获取转录，支持 checkpoint 和增量模式"""
    results = []
    checkpoint_num = 0
    start_idx = 0
    existing_transcripts = {}
    
    # 如果 resume，加载最新 checkpoint
    if resume:
        latest = storage.get_latest_checkpoint("youtube", "transcript")
        if latest > 0:
            cp_data = storage.load_checkpoint(latest, "youtube", "transcript")
            results = cp_data.get("items", [])
            start_idx = len(results)
            checkpoint_num = latest
            print(f"[youtube_transcript] Resumed from checkpoint {latest}, processed {len(results)} videos")
    
    # 增量模式：加载已有转录，跳过已处理的视频
    if incremental and not resume:
        existing_transcripts = load_existing_transcripts(storage)
        if existing_transcripts:
            print(f"[youtube_transcript] 增量模式：发现 {len(existing_transcripts)} 条已有转录")
    
    # 过滤已转录的视频（增量模式）
    videos_to_process = []
    skipped_count = 0
    for v in videos:
        vid = v.get("id")
        if incremental and vid in existing_transcripts:
            skipped_count += 1
            # 保留已有转录数据
            results.append(existing_transcripts[vid])
        else:
            videos_to_process.append(v)
    
    if skipped_count > 0:
        print(f"[youtube_transcript] 跳过 {skipped_count} 条已有转录的视频")
    
    # 处理剩余视频
    for i, v in enumerate(videos_to_process):
        video_id = v.get("id")
        title = v.get("title", "")
        safe_title = title[:30] if title else "(no title)"
        safe_title = safe_title.encode('ascii', 'ignore').decode('ascii')
        total_videos = len(videos)
        processed = skipped_count + i + 1
        print(f"[youtube_transcript] [{processed}/{total_videos}] {safe_title}...")
        
        try:
            transcript = get_transcript(video_id, api_key)
        except Exception as e:
            print(f"  Failed: {e}")
            transcript = ""
        
        results.append({
            "id": video_id,
            "title": title,
            "channel": v.get("channel"),
            "url": v.get("url"),
            "published_at": v.get("published_at"),
            "view_count": v.get("view_count"),
            "duration": v.get("duration"),
            "transcript": transcript,
            "transcript_length": len(transcript),
            "status": "success" if transcript else "no_transcript",
        })
        
        # 每 5 个保存一次 checkpoint（仅针对新处理的视频）
        if (i + 1) % 5 == 0:
            checkpoint_num += 1
            storage.save_checkpoint(
                {"items": results},
                checkpoint_num,
                "youtube",
                "transcript"
            )
    
    # 最终 checkpoint（仅当有新处理的视频时）
    if videos_to_process:
        storage.save_checkpoint(
            {"items": results},
            checkpoint_num + 1,
            "youtube",
            "transcript"
        )
    
    return results


def main():
    parser = argparse.ArgumentParser(description="YouTube Transcript 转录")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--input", required=True, help="youtube_metadata 输出文件")
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    args = parser.parse_args()
    
    try:
        api_key = _get_api_key()
    except ValueError as e:
        print(f"[youtube_transcript] Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 初始化存储
    storage = DataStorage(args.game_id)
    
    # 读取 metadata
    with open(args.input, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    videos = metadata.get("items", [])
    print(f"[youtube_transcript] Processing {len(videos)} videos")
    if args.resume:
        print("[youtube_transcript] Resume mode enabled")
    
    # 默认启用增量模式，可通过环境变量关闭
    incremental = os.environ.get("YOUTUBE_TRANSCRIPT_INCREMENTAL", "true").lower() != "false"
    if incremental:
        print("[youtube_transcript] 增量模式：将跳过已有转录的视频")
    
    results = process_videos(videos, api_key, storage, args.resume, incremental)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    total_chars = sum(r.get("transcript_length", 0) for r in results)
    print(f"[youtube_transcript] Done: {success_count}/{len(results)}")
    print(f"[youtube_transcript] Total chars: {total_chars}")
    
    # 构建数据
    output = {
        "platform": "youtube",
        "game_id": args.game_id,
        "data_type": "transcript",
        "phase": "transcript",
        "query": metadata.get("query"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "success_count": success_count,
        "total_chars": total_chars,
        "items": results,
    }
    
    # 保存到规范路径
    output_path = storage.merge_and_save(output, "youtube", "transcript", id_field="id")
    print(f"[youtube_transcript] Output: {output_path}")
    
    # Update data index
    update_index(args.game_id, args.game_id, "youtube", "transcript", count=len(results))
    
    # 清理旧 checkpoint
    storage.clean_checkpoints(keep_latest=3)


if __name__ == "__main__":
    main()
