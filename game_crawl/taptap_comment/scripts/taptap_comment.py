#!/usr/bin/env python3
"""TapTap Comment - 使用 Browser Relay 抓取帖子评论

Usage:
    python taptap_comment.py --game-id g_genshin --input taptap_metadata.json
    python taptap_comment.py --game-id g_genshin --input taptap_metadata.json --resume
"""
import argparse
import json
import sys
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index


def fetch_comments_browser(post_url: str, limit: int, profile="openclaw") -> list:
    """使用 Browser Relay 抓取单个帖子的评论"""
    comments = []
    
    # 打开页面
    result = subprocess.run(
        ["openclaw", "browser", "open", "--url", post_url, "--profile", profile, "--json"],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        print(f"[ERROR] 打开页面失败: {result.stderr}", file=sys.stderr)
        return []
    
    tab_info = json.loads(result.stdout)
    target_id = tab_info.get("targetId")
    
    if not target_id:
        print("[ERROR] 无法获取 targetId", file=sys.stderr)
        return []
    
    # 等待加载
    time.sleep(3)
    
    # 提取评论的 JavaScript
    js_code = """
    () => {
        const comments = [];
        const items = document.querySelectorAll('.moment-post-item, .moment-comment-list .tap-list > div');
        
        for (const item of items) {
            try {
                const user_el = item.querySelector('.moment-post__user-name a, .moment-post__user-name span');
                const content_el = item.querySelector('.moment-post__content-wrapper');
                const like_el = item.querySelector('.vote-button__button-text');
                
                const user = user_el?.textContent?.trim() || '';
                const content = content_el?.textContent?.trim() || '';
                const likes = parseInt(like_el?.textContent?.trim() || '0');
                
                if (user && content) {
                    comments.push({author: user, content: content, likes: likes});
                }
            } catch (e) {
                console.error('提取评论失败:', e);
            }
        }
        return comments;
    }
    """
    
    # 滚动和提取
    seen = set()
    for scroll_round in range(20):
        if len(comments) >= limit:
            break
        
        # 执行提取
        result = subprocess.run(
            ["openclaw", "browser", "act", "--target-id", target_id, "--profile", profile,
             "--request", json.dumps({"kind": "evaluate", "fn": js_code})],
            capture_output=True, text=True, encoding='utf-8'
        )
        
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                new_comments = output.get("result", [])
                for c in new_comments:
                    key = c['author'] + c['content'][:50]
                    if key not in seen:
                        seen.add(key)
                        comments.append(c)
                print(f"  第{scroll_round+1}轮: 已收集 {len(comments)} 条")
            except:
                pass
        
        if len(comments) >= limit:
            break
        
        # 滚动
        scroll_js = "() => { window.scrollTo(0, document.body.scrollHeight); return 'scrolled'; }"
        subprocess.run(
            ["openclaw", "browser", "act", "--target-id", target_id, "--profile", profile,
             "--request", json.dumps({"kind": "evaluate", "fn": scroll_js})],
            capture_output=True
        )
        time.sleep(2)
    
    # 关闭标签页
    subprocess.run(
        ["openclaw", "browser", "close", "--target-id", target_id, "--profile", profile],
        capture_output=True
    )
    
    return comments[:limit]


def main():
    # Fix Windows console encoding
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    parser = argparse.ArgumentParser(description="TapTap Comment 抓取 (Browser Relay)")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--input", required=True, help="taptap_metadata 输出文件")
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    parser.add_argument("--comment-limit", type=int, default=50, help="每帖子评论数")
    parser.add_argument("--profile", default="openclaw", help="Browser profile")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    with open(args.input, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    posts = metadata.get("items", [])
    print(f"[taptap_comment] Processing {len(posts)} posts")
    
    # Resume
    results = []
    start_idx = 0
    if args.resume:
        latest = storage.get_latest_checkpoint("taptap", "comment")
        if latest > 0:
            cp_data = storage.load_checkpoint(latest, "taptap", "comment")
            results = cp_data.get("items", [])
            start_idx = len(results)
            print(f"[taptap_comment] Resumed from checkpoint {latest}, processed {len(results)} posts")
    
    for i, post in enumerate(posts[start_idx:], start=start_idx):
        post_url = post.get("url")
        safe_title = post.get('title', '')[:30] or "(no title)"
        print(f"[taptap_comment] [{i+1}/{len(posts)}] {safe_title}...")
        
        try:
            comments = fetch_comments_browser(post_url, args.comment_limit, args.profile)
        except Exception as e:
            print(f"  Failed: {e}", file=sys.stderr)
            comments = []
        
        results.append({
            "id": post.get("id"),
            "title": post.get("title"),
            "url": post_url,
            "comment_count": len(comments),
            "comments": comments,
        })
        
        # Save checkpoint every 3 posts
        if (i + 1 - start_idx) % 3 == 0:
            storage.save_checkpoint(
                {"items": results},
                (i + 1) // 3,
                "taptap",
                "comment"
            )
    
    # Final checkpoint
    if results:
        storage.save_checkpoint(
            {"items": results},
            len(results) // 3 + 1,
            "taptap",
            "comment"
        )
    
    total_comments = sum(r["comment_count"] for r in results)
    print(f"[taptap_comment] Done: {len(results)} posts, {total_comments} comments")
    
    output = {
        "platform": "taptap",
        "game_id": args.game_id,
        "data_type": "comment",
        "phase": "comment",
        "app_id": metadata.get("app_id"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "post_count": len(results),
        "total_comments": total_comments,
        "items": results,
    }
    
    output_path = storage.merge_and_save(output, "taptap", "comment", id_field="id")
    print(f"[taptap_comment] 输出: {output_path}")
    
    update_index(args.game_id, args.game_id, "taptap", "comment", count=len(results))
    storage.clean_checkpoints(keep_latest=3)


if __name__ == "__main__":
    main()
