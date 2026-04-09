#!/usr/bin/env python3
"""
Bilibili Transcript - 完整转录流程
支持 checkpoint 和规范化存储

Usage:
    python bilibili_transcript.py --game-id g_genshin --input bilibili_metadata.json
    python bilibili_transcript.py --game-id g_genshin --input bilibili_metadata.json --resume
"""
import argparse
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index


def _get_env(key: str) -> str:
    val = os.environ.get(key, "").strip()
    if not val:
        raise ValueError(f"环境变量 {key} 未设置")
    return val


def download_video(bvid: str, output_dir: Path) -> Path | None:
    """yt-dlp 下载视频"""
    try:
        import yt_dlp
        url = f"https://www.bilibili.com/video/{bvid}"
        output_path = output_dir / f"{bvid}.mp4"
        
        ydl_opts = {
            "format": "bv*[height<=480]+ba/b[height<=480] / bv*+ba/b",
            "merge_output_format": "mp4",
            "outtmpl": str(output_path),
            "quiet": True,
            "no_warnings": True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return output_path if output_path.exists() else None
    except Exception as e:
        print(f"  下载失败: {e}", file=sys.stderr)
        return None


def extract_audio(video_path: Path, output_dir: Path) -> Path | None:
    """ffmpeg 提取音频"""
    import subprocess
    audio_path = output_dir / f"{video_path.stem}.mp3"
    
    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-acodec", "libmp3lame", "-q:a", "2",
            str(audio_path)
        ]
        subprocess.run(cmd, capture_output=True, timeout=120, check=True)
        return audio_path if audio_path.exists() else None
    except Exception as e:
        print(f"  音频提取失败: {e}", file=sys.stderr)
        return None


def transcribe_audio(audio_path: Path) -> str:
    """DashScope 转录"""
    import dashscope
    import oss2
    
    dashscope.api_key = _get_env("DASHSCOPE_API_KEY")
    
    access_key = _get_env("OSS_ACCESS_KEY_ID")
    secret_key = _get_env("OSS_ACCESS_KEY_SECRET")
    bucket_name = _get_env("OSS_BUCKET")
    endpoint = _get_env("OSS_ENDPOINT")
    
    auth = oss2.Auth(access_key, secret_key)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    
    oss_key = f"bilibili/{audio_path.name}"
    bucket.put_object_from_file(oss_key, str(audio_path))
    signed_url = bucket.sign_url("GET", oss_key, 3600)
    
    try:
        task = dashscope.audio.asr.Transcription.async_call(
            model=dashscope.audio.asr.Transcription.Models.paraformer_v1,
            file_urls=[signed_url]
        )
        task_id = task.output.get("task_id")
        
        for _ in range(100):
            task_output = dashscope.audio.asr.Transcription.fetch(task=task_id)
            status = task_output.output.get("task_status")
            
            if status == "SUCCEEDED":
                result_url = task_output.output["results"][0].get("transcription_url")
                import urllib.request
                with urllib.request.urlopen(result_url) as resp:
                    result_data = json.loads(resp.read().decode("utf-8"))
                    transcripts = result_data.get("transcripts", [])
                    if transcripts and "sentences" in transcripts[0]:
                        sentences = transcripts[0]["sentences"]
                        text = " ".join([s.get("text", "") for s in sentences])
                    else:
                        text = ""
                bucket.delete_object(oss_key)
                return text
            elif status == "FAILED":
                bucket.delete_object(oss_key)
                return ""
            time.sleep(3)
        
        bucket.delete_object(oss_key)
        return ""
    except Exception as e:
        try:
            bucket.delete_object(oss_key)
        except:
            pass
        print(f"  转录失败: {e}", file=sys.stderr)
        return ""


def load_existing_transcripts(storage: DataStorage) -> dict:
    """加载已有的转录数据，用于增量检测"""
    output_path = storage.get_output_path("bilibili", "transcript")
    if not output_path.exists():
        return {}
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 构建 bvid -> transcript 的映射（只保留成功的）
            return {
                item["bvid"]: item 
                for item in data.get("items", []) 
                if item.get("transcript") and item.get("status") == "success"
            }
    except Exception:
        return {}


def process_video(v: dict, temp_dir: Path) -> dict:
    """处理单个视频完整流程"""
    try:
        bvid = v.get("bvid")
        title = v.get("title", "")
        duration = v.get("duration", "0:0")
        
        # 跳过超长视频 (>60分钟)
        if ":" in duration:
            parts = duration.split(":")
            if len(parts) >= 2:
                try:
                    minutes = int(parts[0])
                    if minutes > 60:
                        print(f"  跳过超长视频 ({duration}): {title[:40]}...")
                        return {**v, "transcript": "", "transcript_length": 0, "status": "skipped_too_long"}
                except:
                    pass
        
        print(f"  处理: {title[:50]}...")
        
        # 下载
        video_path = download_video(bvid, temp_dir)
        if not video_path:
            return {**v, "transcript": "", "transcript_length": 0, "status": "download_failed"}
        
        # 提取音频
        audio_path = extract_audio(video_path, temp_dir)
        video_path.unlink(missing_ok=True)
        if not audio_path:
            return {**v, "transcript": "", "transcript_length": 0, "status": "audio_extract_failed"}
        
        # 转录
        transcript = transcribe_audio(audio_path)
        audio_path.unlink(missing_ok=True)
        
        return {
            **v,
            "transcript": transcript,
            "transcript_length": len(transcript),
            "status": "success" if transcript else "transcription_failed",
        }
    except Exception as e:
        print(f"  处理视频时异常: {e}", file=sys.stderr)
        return {**v, "transcript": "", "transcript_length": 0, "status": f"error: {str(e)[:50]}"}


def main():
    parser = argparse.ArgumentParser(description="Bilibili Transcript 转录")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--input", required=True, help="bilibili_metadata 输出文件")
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    with open(args.input, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    videos = metadata.get("items", [])
    print(f"[bilibili_transcript] 处理 {len(videos)} 个视频")
    
    # 默认启用增量模式
    incremental = os.environ.get("BILIBILI_TRANSCRIPT_INCREMENTAL", "true").lower() != "false"
    
    # Checkpoint 恢复
    results = []
    start_idx = 0
    if args.resume:
        latest = storage.get_latest_checkpoint("bilibili", "transcript")
        if latest > 0:
            cp_data = storage.load_checkpoint(latest, "bilibili", "transcript")
            results = cp_data.get("items", [])
            start_idx = len(results)
            print(f"[bilibili_transcript] 从 checkpoint {latest} 恢复，已处理 {len(results)} 个")
    
    # 增量模式：加载已有转录
    existing_transcripts = {}
    skipped_count = 0
    if incremental and not args.resume:
        existing_transcripts = load_existing_transcripts(storage)
        if existing_transcripts:
            print(f"[bilibili_transcript] 增量模式：发现 {len(existing_transcripts)} 条已有转录")
    
    # 过滤已转录的视频
    videos_to_process = []
    for v in videos:
        bvid = v.get("bvid")
        if incremental and bvid in existing_transcripts:
            skipped_count += 1
            results.append(existing_transcripts[bvid])
        else:
            videos_to_process.append(v)
    
    if skipped_count > 0:
        print(f"[bilibili_transcript] 跳过 {skipped_count} 条已有转录的视频")
    
    if not videos_to_process:
        print("[bilibili_transcript] 没有新视频需要处理")
    else:
        print(f"[bilibili_transcript] 新视频: {len(videos_to_process)} 个")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    for i, v in enumerate(videos_to_process):
        total_processed = skipped_count + i + 1
        print(f"\n[bilibili_transcript] [{total_processed}/{len(videos)}] 新视频 {i+1}/{len(videos_to_process)}")
        result = process_video(v, temp_dir)
        results.append(result)
        
        # 每 3 个保存 checkpoint
        if (i + 1) % 3 == 0:
            storage.save_checkpoint(
                {"items": results},
                (i + 1) // 3,
                "bilibili",
                "transcript"
            )
    
    temp_dir.rmdir()
    
    # 最终 checkpoint（仅当有新处理的视频时）
    if videos_to_process:
        storage.save_checkpoint(
            {"items": results},
            len(videos_to_process) // 3 + 1,
            "bilibili",
            "transcript"
        )
    
    success_count = sum(1 for r in results if r.get("status") == "success")
    total_chars = sum(r.get("transcript_length", 0) for r in results)
    print(f"\n[bilibili_transcript] 完成: {success_count}/{len(results)}")
    print(f"[bilibili_transcript] 总字符数: {total_chars}")
    
    output = {
        "platform": "bilibili",
        "game_id": args.game_id,
        "data_type": "transcript",
        "phase": "transcript",
        "keyword": metadata.get("keyword"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "success_count": success_count,
        "total_chars": total_chars,
        "items": results,
    }
    
    output_path = storage.merge_and_save(output, "bilibili", "transcript", id_field="id")
    print(f"[bilibili_transcript] 输出: {output_path}")
    
    # 更新数据索引
    update_index(args.game_id, args.game_id, "bilibili", "transcript", count=len(results))
    
    storage.clean_checkpoints(keep_latest=3)


if __name__ == "__main__":
    main()
