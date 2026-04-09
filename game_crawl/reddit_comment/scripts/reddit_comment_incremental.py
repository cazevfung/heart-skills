#!/usr/bin/env python3
"""
抓取心动小镇 Reddit 新增帖子评论
时间范围: 2026-03-21T13:30:00+00:00 之后
"""
import json
import http.cookiejar
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

# 配置
GAME_ID = "g_a1b2c3d4"
METADATA_PATH = Path("D:/App Dev/openclaw-main/data/game_data/games/g_a1b2c3d4/reddit/metadata.json")
EXISTING_COMMENTS_PATH = Path("D:/App Dev/openclaw-main/data/game_data/games/g_a1b2c3d4/reddit/comments.json")
CUTOFF_TIME = datetime.fromisoformat("2026-03-21T13:30:00+00:00")

_RETRY_WAIT = 10
_MAX_RETRIES = 3
_BASE_URL = "https://www.reddit.com"
_OAUTH_BASE_URL = "https://oauth.reddit.com"

def _load_oauth_token():
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

def fetch_comments(post_id, opener, headers, base_url, limit=50):
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
    print(f"[reddit_comment_incremental] Heartopia Reddit Comment Incremental Fetch")
    print(f"[reddit_comment_incremental] Time threshold: {CUTOFF_TIME.isoformat()}")
    
    # 加载 metadata
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    # 筛选新帖子
    all_posts = metadata.get("items", [])
    new_posts = []
    for post in all_posts:
        post_time = datetime.fromisoformat(post.get("created_utc", "").replace("+00:00", "+00:00"))
        if post_time > CUTOFF_TIME:
            new_posts.append(post)
    
    print(f"[reddit_comment_incremental] Total posts: {len(all_posts)}")
    print(f"[reddit_comment_incremental] New posts: {len(new_posts)}")
    
    if not new_posts:
        print("[reddit_comment_incremental] No new posts to fetch")
        return
    
    # 加载已有评论
    existing_ids = set()
    if EXISTING_COMMENTS_PATH.exists():
        with open(EXISTING_COMMENTS_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
        for item in existing.get("items", []):
            existing_ids.add(item.get("id"))
        print(f"[reddit_comment_incremental] Existing comment posts: {len(existing_ids)}")
    
    # 过滤掉已抓取的
    posts_to_fetch = [p for p in new_posts if p.get("id") not in existing_ids]
    print(f"[reddit_comment_incremental] Posts to fetch: {len(posts_to_fetch)}")
    
    if not posts_to_fetch:
        print("[reddit_comment_incremental] All new posts already fetched")
        return
    
    # 开始抓取
    opener, headers, base_url = _build_opener_and_headers()
    storage = DataStorage(GAME_ID)
    
    new_results = []
    for i, post in enumerate(posts_to_fetch):
        post_id = post.get("id")
        title = post.get("title", "")[:50]
        # 过滤非 ASCII 字符避免编码错误
        title_safe = title.encode('ascii', 'replace').decode('ascii')
        print(f"[reddit_comment_incremental] [{i+1}/{len(posts_to_fetch)}] Fetch {post_id} - {title_safe}...")
        
        try:
            comments = fetch_comments(post_id, opener, headers, base_url, 50)
            print(f"  OK: {len(comments)} comments")
        except Exception as e:
            print(f"  FAIL: {e}")
            comments = []
        
        new_results.append({
            "id": post_id,
            "title": post.get("title"),
            "url": post.get("url"),
            "comment_count": len(comments),
            "comments": comments,
        })
        
        time.sleep(5)
    
    # 合并并保存
    total_new_comments = sum(r["comment_count"] for r in new_results)
    print(f"[reddit_comment_incremental] New comments fetched: {total_new_comments}")
    
    # 读取现有 comments.json 并合并
    if EXISTING_COMMENTS_PATH.exists():
        with open(EXISTING_COMMENTS_PATH, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        existing_items = existing_data.get("items", [])
    else:
        existing_items = []
    
    # 合并 (新数据追加到后面)
    all_items = existing_items + new_results
    
    output = {
        "platform": "reddit",
        "game_id": GAME_ID,
        "data_type": "comment",
        "phase": "comment",
        "subreddit": metadata.get("subreddit", "heartopia"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "post_count": len(all_items),
        "total_comments": sum(r["comment_count"] for r in all_items),
        "items": all_items,
    }
    
    # 保存
    output_path = storage.merge_and_save(output, "reddit", "comment", id_field="id")
    print(f"[reddit_comment_incremental] Saved to: {output_path}")
    
    # 更新索引
    update_index(GAME_ID, "Heartopia", "reddit", "comment", count=len(all_items))
    print(f"[reddit_comment_incremental] Index updated")
    
    print(f"\n[reddit_comment_incremental] DONE!")
    print(f"  - New posts: {len(new_results)}")
    print(f"  - New comments: {total_new_comments}")
    print(f"  - Total posts with comments: {len(all_items)}")

if __name__ == "__main__":
    main()
