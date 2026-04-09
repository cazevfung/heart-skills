#!/usr/bin/env python3
"""
Bilibili Metadata - 仅搜索获取视频元数据
使用 B站 API，支持 checkpoint 和规范化存储

Usage:
    python bilibili_metadata.py --game-id g_genshin --keyword "原神 前瞻" --limit 10
    python bilibili_metadata.py --game-id g_genshin --keyword "原神 前瞻" --limit 10 --resume
"""
import argparse
import json
import os
import sys
import time
import gzip
from datetime import datetime, timezone
from pathlib import Path

import urllib.request
import urllib.parse

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

_SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/type"
_RETRY_WAIT = 2
_MAX_RETRIES = 3


def _parse_cookie() -> str:
    raw = os.environ.get("BILIBILI_COOKIE", "").strip()
    if not raw:
        return ""
    if raw.startswith("{"):
        try:
            d = json.loads(raw)
            return "; ".join(f"{k}={v}" for k, v in d.items() if v)
        except:
            pass
    return raw


def _build_headers() -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://search.bilibili.com",
        "Referer": "https://search.bilibili.com/all",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Connection": "keep-alive",
    }
    cookie = _parse_cookie()
    if cookie:
        headers["Cookie"] = cookie
    return headers


def _get(url: str, params: dict | None = None) -> dict:
    headers = _build_headers()
    if params:
        query = urllib.parse.urlencode(params, encoding='utf-8')
        full_url = url + "?" + query
    else:
        full_url = url
    
    for attempt in range(_MAX_RETRIES):
        try:
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                # 处理 gzip
                if resp.headers.get('Content-Encoding') == 'gzip':
                    data = gzip.decompress(data)
                return json.loads(data.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (412, 429) and attempt < _MAX_RETRIES - 1:
                wait_time = _RETRY_WAIT * (attempt + 1) + 1
                print(f"[bilibili_metadata] 频率限制(412/429)，等待 {wait_time}s...", file=sys.stderr)
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_WAIT)
            else:
                raise
    return {}


def search_videos(keyword: str, limit: int, storage: DataStorage, resume: bool = False) -> list:
    """搜索 B站视频，支持 checkpoint"""
    videos = []
    checkpoint_num = 0
    page = 1
    
    # 如果 resume，加载最新 checkpoint
    if resume:
        latest = storage.get_latest_checkpoint("bilibili", "metadata")
        if latest > 0:
            cp_data = storage.load_checkpoint(latest, "bilibili", "metadata")
            videos = cp_data.get("items", [])
            page = (len(videos) // 20) + 1
            checkpoint_num = latest
            print(f"[bilibili_metadata] 从 checkpoint {latest} 恢复，已有 {len(videos)} 个视频")
    
    while len(videos) < limit:
        params = {
            "search_type": "video",
            "keyword": keyword,
            "page": page,
            "pagesize": 20,
        }
        
        try:
            data = _get(_SEARCH_URL, params)
        except Exception as e:
            print(f"[bilibili_metadata] 搜索失败: {e}", file=sys.stderr)
            break
        
        if not data or data.get("code") != 0:
            break
        
        result = data.get("data", {}).get("result", [])
        if not result:
            break
        
        for item in result:
            bvid = item.get("bvid")
            if bvid:
                videos.append({
                    "id": bvid,
                    "bvid": bvid,
                    "title": item.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                    "author": item.get("author", ""),
                    "url": f"https://www.bilibili.com/video/{bvid}",
                    "pubdate": item.get("pubdate"),
                    "duration": item.get("duration"),
                })
                
                # 每 10 个保存 checkpoint
                if len(videos) % 10 == 0:
                    checkpoint_num += 1
                    storage.save_checkpoint(
                        {"items": videos, "keyword": keyword},
                        checkpoint_num,
                        "bilibili",
                        "metadata"
                    )
                
                if len(videos) >= limit:
                    break
        
        page += 1
        time.sleep(0.5)
    
    # 最终 checkpoint
    if videos:
        storage.save_checkpoint(
            {"items": videos, "keyword": keyword},
            checkpoint_num + 1,
            "bilibili",
            "metadata"
        )
    
    return videos[:limit]


def main():
    parser = argparse.ArgumentParser(description="Bilibili Metadata 搜索")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--keyword", required=True, help="搜索关键词")
    parser.add_argument("--limit", type=int, default=10, help="数量限制")
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    print(f"[bilibili_metadata] 搜索: {args.keyword}, 限制: {args.limit}")
    if args.resume:
        print("[bilibili_metadata] 启用断点续传模式")
    
    videos = search_videos(args.keyword, args.limit, storage, args.resume)
    print(f"[bilibili_metadata] 找到 {len(videos)} 个视频")
    
    result = {
        "platform": "bilibili",
        "game_id": args.game_id,
        "data_type": "metadata",
        "phase": "metadata",
        "keyword": args.keyword,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(videos),
        "items": videos,
    }
    
    output_path = storage.merge_and_save(result, "bilibili", "metadata", id_field="id")
    print(f"[bilibili_metadata] 输出: {output_path}")
    
    # 更新数据索引
    update_index(args.game_id, args.game_id, "bilibili", "metadata", count=len(videos))
    
    storage.clean_checkpoints(keep_latest=3)


if __name__ == "__main__":
    main()
