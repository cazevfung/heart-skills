#!/usr/bin/env python3
"""
Reddit Comment - 仅抓取帖子评论
支持 checkpoint 和规范化存储

Usage:
    python reddit_comment.py --game-id g_genshin --input reddit_metadata.json
    python reddit_comment.py --game-id g_genshin --input reddit_metadata.json --resume
"""
import argparse
import http.cookiejar
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

_RETRY_WAIT = 10
_MAX_RETRIES = 3
_BASE_URL = "https://www.reddit.com"
_OAUTH_BASE_URL = "https://oauth.reddit.com"


def _load_oauth_token() -> str:
    token = os.environ.get("REDDIT_ACCESS_TOKEN", "").strip()
    if token:
        return token
    creds_path = Path(os.environ.get("COPAW_CREDENTIALS_FILE", str(Path.home() / ".copaw" / "config" / "credentials.json")))
    if creds_path.exists():
        try:
            with creds_path.open("r", encoding="utf-8") as f:
                creds = json.load(f)
            return creds.get("reddit_access_token", "").strip()
        except:
            pass
    return ""


def _build_opener_and_headers():
    token = _load_oauth_token()
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    
    if token:
        base_url = _OAUTH_BASE_URL
        headers = {
            "User-Agent": "CoPaw-CommunityCrawler/1.0",
            "Accept": "application/json",
            "Authorization": f"bearer {token}",
        }
    else:
        base_url = _BASE_URL
        headers = {
            "User-Agent": "CoPaw-CommunityCrawler/1.0",
            "Accept": "application/json",
        }
        try:
            opener.open(urllib.request.Request(f"{base_url}/", headers=headers, method="GET"), timeout=15)
        except:
            pass
    
    return opener, headers, base_url


def _fetch_json(opener, url, headers):
    for attempt in range(_MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=headers)
            with opener.open(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_WAIT * (attempt + 1))
            else:
                raise
    return {}


def fetch_comments(post_id: str, opener, headers, base_url, limit: int = 50) -> list:
    """抓取单个帖子的评论"""
    url = f"{base_url}/comments/{post_id}.json?limit={limit}&sort=top"
    data = _fetch_json(opener, url, headers)
    
    if not data or len(data) < 2:
        return []
    
    comments = []
    comment_data = data[1].get("data", {}).get("children", [])
    
    for child in comment_data:
        comment = child.get("data", {})
        if comment.get("body"):
            comments.append({
                "id": comment.get("id"),
                "author": comment.get("author", ""),
                "body": comment.get("body", ""),
                "created_utc": datetime.fromtimestamp(comment.get("created_utc", 0), tz=timezone.utc).isoformat(),
                "score": comment.get("score", 0),
            })
    
    return comments


def main():
    parser = argparse.ArgumentParser(description="Reddit Comment 抓取")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--input", required=True, help="reddit_metadata 输出文件")
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    parser.add_argument("--comment-limit", type=int, default=50, help="每帖子评论数")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    with open(args.input, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    posts = metadata.get("items", [])
    print(f"[reddit_comment] 处理 {len(posts)} 个帖子的评论")
    
    opener, headers, base_url = _build_opener_and_headers()
    
    # Resume
    results = []
    start_idx = 0
    if args.resume:
        latest = storage.get_latest_checkpoint("reddit", "comment")
        if latest > 0:
            cp_data = storage.load_checkpoint(latest, "reddit", "comment")
            results = cp_data.get("items", [])
            start_idx = len(results)
            print(f"[reddit_comment] 从 checkpoint {latest} 恢复，已处理 {len(results)} 个帖子")
    
    for i, post in enumerate(posts[start_idx:], start=start_idx):
        post_id = post.get("id")
        print(f"[reddit_comment] [{i+1}/{len(posts)}] 抓取帖子 {post_id} 的评论...")
        
        try:
            comments = fetch_comments(post_id, opener, headers, base_url, args.comment_limit)
        except Exception as e:
            print(f"  抓取失败: {e}", file=sys.stderr)
            comments = []
        
        results.append({
            "id": post_id,
            "title": post.get("title"),
            "url": post.get("url"),
            "comment_count": len(comments),
            "comments": comments,
        })
        
        # Checkpoint
        if (i + 1 - start_idx) % 5 == 0:
            storage.save_checkpoint(
                {"items": results},
                (i + 1) // 5,
                "reddit",
                "comment"
            )
        
        time.sleep(5)
    
    # Final checkpoint
    if results:
        storage.save_checkpoint(
            {"items": results},
            len(results) // 5 + 1,
            "reddit",
            "comment"
        )
    
    total_comments = sum(r["comment_count"] for r in results)
    print(f"[reddit_comment] 完成，共 {total_comments} 条评论")
    
    output = {
        "platform": "reddit",
        "game_id": args.game_id,
        "data_type": "comment",
        "phase": "comment",
        "subreddit": metadata.get("subreddit"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "post_count": len(results),
        "total_comments": total_comments,
        "items": results,
    }
    
    output_path = storage.merge_and_save(output, "reddit", "comment", id_field="id")
    print(f"[reddit_comment] 输出: {output_path}")
    
    # 更新数据索引
    update_index(args.game_id, args.game_id, "reddit", "comment", count=len(results))
    
    storage.clean_checkpoints(keep_latest=3)


if __name__ == "__main__":
    main()
