#!/usr/bin/env python3
"""
Reddit Metadata - 仅抓取帖子元数据（不含评论）
支持 checkpoint 和规范化存储

Usage:
    python reddit_metadata.py --game-id g_genshin --subreddit gaming --limit 30
    python reddit_metadata.py --game-id g_genshin --subreddit gaming --limit 30 --resume
"""
import argparse
import http.cookiejar
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

_RETRY_WAIT = 2
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


def fetch_posts(subreddit: str, limit: int, storage: DataStorage, resume: bool = False, query: str = None) -> list:
    """抓取帖子列表（不含评论），支持 checkpoint"""
    opener, headers, base_url = _build_opener_and_headers()
    
    posts = []
    after = None
    checkpoint_num = 0
    
    # Resume
    if resume:
        latest = storage.get_latest_checkpoint("reddit", "metadata")
        if latest > 0:
            cp_data = storage.load_checkpoint(latest, "reddit", "metadata")
            posts = cp_data.get("items", [])
            after = cp_data.get("after")
            checkpoint_num = latest
            print(f"[reddit_metadata] 从 checkpoint {latest} 恢复，已有 {len(posts)} 个帖子")
    
    while len(posts) < limit:
        remaining = limit - len(posts)
        fetch_count = min(100, remaining)
        if query:
            # Search mode
            url = f"{base_url}/search.json?q={urllib.parse.quote(query)}&limit={fetch_count}&sort=new"
        else:
            # Subreddit mode
            url = f"{base_url}/r/{subreddit}/new.json?limit={fetch_count}"
        if after:
            url += f"&after={after}"
        
        data = _fetch_json(opener, url, headers)
        
        children = data.get("data", {}).get("children", [])
        if not children:
            break
        
        for child in children:
            if len(posts) >= limit:
                break
            post = child.get("data", {})
            posts.append({
                "id": post.get("id"),
                "title": post.get("title", ""),
                "author": post.get("author", ""),
                "content": post.get("selftext", ""),
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "created_utc": datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc).isoformat(),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
            })
            
            # Checkpoint
            if len(posts) % 10 == 0:
                checkpoint_num += 1
                storage.save_checkpoint(
                    {"items": posts, "after": child.get("data", {}).get("name")},
                    checkpoint_num,
                    "reddit",
                    "metadata"
                )
        
        after = data.get("data", {}).get("after")
        if not after:
            break
    
    # Final checkpoint
    if posts:
        storage.save_checkpoint(
            {"items": posts, "after": after},
            checkpoint_num + 1,
            "reddit",
            "metadata"
        )
    
    return posts[:limit]


def main():
    parser = argparse.ArgumentParser(description="Reddit Metadata 抓取")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--subreddit", help="Subreddit 名称")
    parser.add_argument("--query", help="搜索关键词（与subreddit二选一）")
    parser.add_argument("--limit", type=int, default=30, help="帖子数量")
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    args = parser.parse_args()
    
    if not args.subreddit and not args.query:
        parser.error("必须提供 --subreddit 或 --query 之一")
    
    storage = DataStorage(args.game_id)
    
    if args.query:
        print(f"[reddit_metadata] 搜索关键词: {args.query}, 限制 {args.limit}")
    else:
        print(f"[reddit_metadata] 抓取 r/{args.subreddit}, 限制 {args.limit}")
    if args.resume:
        print("[reddit_metadata] 启用断点续传模式")
    
    posts = fetch_posts(args.subreddit, args.limit, storage, args.resume, query=args.query)
    print(f"[reddit_metadata] 获取 {len(posts)} 个帖子")
    
    result = {
        "platform": "reddit",
        "game_id": args.game_id,
        "data_type": "metadata",
        "phase": "metadata",
        "subreddit": args.subreddit or f"search:{args.query}",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(posts),
        "items": posts,
    }
    
    output_path = storage.merge_and_save(result, "reddit", "metadata", id_field="id")
    print(f"[reddit_metadata] 输出: {output_path}")
    
    # 更新数据索引
    update_index(args.game_id, args.game_id, "reddit", "metadata", count=len(posts))
    
    storage.clean_checkpoints(keep_latest=3)


if __name__ == "__main__":
    main()
