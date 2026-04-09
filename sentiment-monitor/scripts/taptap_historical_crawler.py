#!/usr/bin/env python3
"""
批量采集 TapTap 游戏历史帖子数据�?
通过 game_crawl �?taptap_forum.py 一次拉取帖子列表与评论，再按日期过滤并写入 per-post 文件�?不再逐帖调用 taptap_post_detail，评论由 game_crawl 统一产出�?
Usage:
    python taptap_historical_crawler.py --app-id 45213 --days 365 --output-dir ./historical_data
"""
import argparse
import io
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def load_existing_posts(data_dir: Path) -> set:
    """Load already fetched post IDs to avoid duplicates."""
    existing_ids = set()
    if not data_dir.exists():
        return existing_ids
    for json_file in data_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "post" in data and "id" in data["post"]:
                    existing_ids.add(data["post"]["id"])
                if "posts" in data:
                    for post in data["posts"]:
                        if "id" in post:
                            existing_ids.add(post["id"])
        except Exception:
            pass
    return existing_ids


def _get_taptap_forum_timeout_seconds() -> int:
    """Single source: game_crawl config (taptap_forum_timeout_seconds / script_timeout_seconds)."""
    script_dir = Path(__file__).parent
    game_crawl_scripts = (script_dir / ".." / ".." / "game_crawl" / "scripts").resolve()
    if str(game_crawl_scripts) not in sys.path:
        sys.path.insert(0, str(game_crawl_scripts))
    try:
        from _crawl_defaults import get_crawl_defaults  # noqa: E402
        cfg = get_crawl_defaults().get("crawl", {})
        return int(cfg.get("taptap_forum_timeout_seconds") or cfg.get("script_timeout_seconds", 900))
    except Exception:
        return 900


def fetch_forum_posts_with_comments(app_id: str, limit: int) -> list:
    """Fetch post list with comments via game_crawl taptap_forum.py (single run, no --no-comments)."""
    import subprocess

    script_dir = Path(__file__).parent
    forum_script = script_dir / ".." / ".." / "game_crawl" / "scripts" / "taptap_forum.py"
    if not forum_script.exists():
        print(f"[taptap_historical_crawler] game_crawl script not found: {forum_script}", file=sys.stderr)
        return []

    timeout_seconds = _get_taptap_forum_timeout_seconds()
    cmd = [
        sys.executable,
        str(forum_script),
        "--app-id", app_id,
        "--limit", str(limit),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout_seconds)
        if result.returncode != 0:
            print(f"[taptap_historical_crawler] taptap_forum error: {result.stderr}", file=sys.stderr)
            return []
        data = json.loads(result.stdout)
        return data.get("posts", [])
    except subprocess.TimeoutExpired:
        print("[taptap_historical_crawler] taptap_forum timeout", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[taptap_historical_crawler] Exception: {e}", file=sys.stderr)
        return []


def filter_posts_by_date(posts: list, days: int) -> list:
    """Filter posts to only include those from last N days."""
    cutoff_date = datetime.now() - timedelta(days=days)
    filtered = []
    
    for post in posts:
        created_at = post.get("created_at", "")
        # Parse relative time strings
        if "小时�? in created_at or "分钟�? in created_at or "刚刚" in created_at:
            filtered.append(post)
        elif "天前" in created_at:
            try:
                days_ago = int(created_at.replace("天前", "").strip())
                if days_ago <= days:
                    filtered.append(post)
            except:
                pass
        elif "202" in created_at:  # Absolute date
            try:
                post_date = datetime.strptime(created_at[:10], "%Y-%m-%d")
                if post_date >= cutoff_date:
                    filtered.append(post)
            except:
                pass
    
    return filtered


def main():
    parser = argparse.ArgumentParser(description="Batch crawl TapTap historical data")
    parser.add_argument("--app-id", required=True, help="TapTap app ID")
    parser.add_argument("--game-name", default="heartopia", help="Game name for output directory")
    parser.add_argument("--days", type=int, default=365, help="How many days back to crawl")
    parser.add_argument("--output-dir", default="./historical_data", help="Output directory")
    parser.add_argument("--max-posts", type=int, default=1000, help="Maximum posts to fetch")
    parser.add_argument("--skip-existing", action="store_true", default=True, 
                        help="Skip already fetched posts")
    
    args = parser.parse_args()
    
    # Setup output directory
    output_dir = Path(args.output_dir) / args.game_name / "post_details"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting historical crawl for app_id={args.app_id}")
    print(f"Output directory: {output_dir}")
    print(f"Looking back: {args.days} days")
    print(f"Max posts: {args.max_posts}")
    
    # Load existing posts
    existing_ids = load_existing_posts(output_dir) if args.skip_existing else set()
    print(f"Found {len(existing_ids)} existing posts")
    
    # Single run: fetch posts with comments via game_crawl taptap_forum
    print("\nFetching posts with comments (game_crawl taptap_forum)...")
    all_posts = fetch_forum_posts_with_comments(args.app_id, limit=min(args.max_posts, 100))

    if not all_posts:
        print("No posts found!")
        sys.exit(1)

    print(f"Found {len(all_posts)} posts (with comments)")

    # Filter by date
    filtered_posts = filter_posts_by_date(all_posts, args.days)
    print(f"After date filter: {len(filtered_posts)} posts")

    # Remove already fetched
    new_posts = [p for p in filtered_posts if p.get("id") not in existing_ids]
    print(f"New posts to save: {len(new_posts)}")

    # Write one file per post (same shape as taptap_post_detail output for compatibility)
    success_count = 0
    fetched_at = datetime.now(timezone.utc).isoformat()
    for i, post in enumerate(new_posts[: args.max_posts]):
        post_id = post.get("id", "")
        post_title = (post.get("title") or "")[:50]
        comments = post.get("comments") or []
        comment_count = len(comments)

        result = {
            "source": "taptap",
            "game_id": args.app_id,
            "post_id": post_id,
            "data_type": "post_detail",
            "fetched_at": fetched_at,
            "locale": "zh-CN",
            "url": post.get("url", ""),
            "post": {
                "id": post_id,
                "title": post.get("title", ""),
                "body": post.get("body", ""),
                "author": post.get("author", ""),
                "url": post.get("url", ""),
                "created_at": post.get("created_at", ""),
                "score": post.get("score", 0),
                "tags": post.get("tags", []),
            },
            "comments": comments,
            "comment_count": comment_count,
            "status": "success",
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{post_id}.json"
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  [{i+1}/{len(new_posts[:args.max_posts])}] Saved: {filepath.name} ({comment_count} comments)")
        success_count += 1

    # Summary
    print(f"\n{'='*50}")
    print("CRAWL SUMMARY")
    print(f"{'='*50}")
    print(f"Total posts from game_crawl: {len(all_posts)}")
    print(f"After date filter: {len(filtered_posts)}")
    print(f"New posts saved: {min(len(new_posts), args.max_posts)}")
    print(f"Success: {success_count}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
