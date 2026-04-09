#!/usr/bin/env python3
"""
批量获取 YouTube 转录 - 简化版
每款游戏处理前 10 个视频
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

from supadata import Supadata, SupadataError

API_KEY = os.environ.get("SUPADATA_API_KEY", "").strip()

GAMES = [
    ("g_a1b2c3d4", "Heartopia"),
    ("g_ragnarok_m", "Ragnarok M"),
    ("g_3bdaf71b", "Torchlight Infinite"),
    ("g_etheria", "Etheria"),
    ("g_palia", "Palia"),
    ("g_komori_life", "Komori Life"),
]

def get_transcript(video_id: str) -> str:
    """获取单个视频转录"""
    supadata = Supadata(api_key=API_KEY)
    try:
        result = supadata.transcript(
            url=f"https://youtube.com/watch?v={video_id}",
            text=True,
        )
        # Handle different result types
        if hasattr(result, 'content'):
            return result.content
        elif isinstance(result, str):
            return result
        else:
            return str(result) if result else ""
    except Exception as e:
        safe_print(f"    Error: {e}")
        return ""

def safe_print(text: str):
    """安全打印，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))

def process_game(game_id: str, game_name: str):
    """处理单个游戏"""
    safe_print(f"\n[{game_name}] Processing...")
    
    storage = DataStorage(game_id)
    metadata_path = f"D:/App Dev/openclaw-main/data/game_data/games/{game_id}/youtube/metadata.json"
    
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    videos = metadata.get("items", [])[:10]  # 只处理前10个
    safe_print(f"  Videos to process: {len(videos)}")
    
    results = []
    for i, v in enumerate(videos):
        video_id = v.get("id")
        title = v.get("title", "")[:40]
        safe_print(f"  [{i+1}/10] {title}...")
        
        transcript = get_transcript(video_id)
        results.append({
            "id": video_id,
            "title": v.get("title"),
            "channel": v.get("channel"),
            "url": v.get("url"),
            "published_at": v.get("published_at"),
            "view_count": v.get("view_count"),
            "duration": v.get("duration"),
            "transcript": transcript,
            "transcript_length": len(transcript),
            "status": "success" if transcript else "no_transcript",
        })
    
    success_count = sum(1 for r in results if r["status"] == "success")
    total_chars = sum(r.get("transcript_length", 0) for r in results)
    
    safe_print(f"  Done: {success_count}/{len(results)} with transcript, {total_chars} chars")
    
    output = {
        "platform": "youtube",
        "game_id": game_id,
        "data_type": "transcript",
        "phase": "transcript",
        "query": metadata.get("query"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "success_count": success_count,
        "total_chars": total_chars,
        "items": results,
    }
    
    output_path = storage.merge_and_save(output, "youtube", "transcript", id_field="id")
    update_index(game_id, game_name, "youtube", "transcript", count=len(results))
    
    return output_path

def main():
    if not API_KEY:
        print("Error: SUPADATA_API_KEY not set")
        sys.exit(1)
    
    print("=" * 50)
    print("YouTube Transcript Batch Processing")
    print("=" * 50)
    
    for game_id, game_name in GAMES:
        try:
            path = process_game(game_id, game_name)
            print(f"  Saved: {path}")
        except Exception as e:
            print(f"  FAILED: {e}")
    
    print("\n" + "=" * 50)
    print("All games processed")

if __name__ == "__main__":
    main()
