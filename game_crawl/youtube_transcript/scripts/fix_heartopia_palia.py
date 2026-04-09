#!/usr/bin/env python3
"""
处理 Heartopia 和 Palia 的转录 - 完全跳过打印问题字符
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

from supadata import Supadata

API_KEY = os.environ.get("SUPADATA_API_KEY", "").strip()

def get_transcript(video_id: str) -> str:
    """获取单个视频转录"""
    supadata = Supadata(api_key=API_KEY)
    try:
        result = supadata.transcript(
            url=f"https://youtube.com/watch?v={video_id}",
            text=True,
        )
        if hasattr(result, 'content'):
            return result.content
        elif isinstance(result, str):
            return result
        else:
            return str(result) if result else ""
    except Exception as e:
        return ""

def process_game(game_id: str, game_name: str):
    """处理单个游戏"""
    sys.stderr.write(f"\n[{game_name}] Processing...\n")
    
    storage = DataStorage(game_id)
    metadata_path = f"D:/App Dev/openclaw-main/data/game_data/games/{game_id}/youtube/metadata.json"
    
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    videos = metadata.get("items", [])[:10]
    sys.stderr.write(f"  Videos: {len(videos)}\n")
    
    results = []
    for i, v in enumerate(videos):
        video_id = v.get("id")
        sys.stderr.write(f"  [{i+1}/10] {video_id}\n")
        
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
    
    sys.stderr.write(f"  Done: {success_count}/{len(results)}, {total_chars} chars\n")
    
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
    
    games = [
        ("g_a1b2c3d4", "Heartopia"),
        ("g_palia", "Palia"),
    ]
    
    for game_id, game_name in games:
        try:
            path = process_game(game_id, game_name)
            sys.stderr.write(f"  Saved: {path}\n")
        except Exception as e:
            sys.stderr.write(f"  FAILED: {e}\n")

if __name__ == "__main__":
    main()
