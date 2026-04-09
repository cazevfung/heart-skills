#!/usr/bin/env python3
"""TapTap Comment - Playwright 版本"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index


def fetch_comments_playwright(post_url: str, limit: int) -> list:
    """使用 Playwright 抓取单个帖子的评论"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[taptap_comment] 错误: 未安装 playwright", file=sys.stderr)
        return []
    
    comments = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(post_url, wait_until="networkidle", timeout=60000)
            time.sleep(3)
            
            scroll_count = 0
            max_scrolls = (limit // 5) + 10
            last_count = 0
            no_change_count = 0
            
            while len(comments) < limit and scroll_count < max_scrolls and no_change_count < 3:
                items = page.query_selector_all('.moment-post-item, .moment-comment-list .tap-list > div')
                
                for item in items:
                    try:
                        user_el = item.query_selector('.moment-post__user-name a, .moment-post__user-name span')
                        content_el = item.query_selector('.moment-post__content-wrapper')
                        like_el = item.query_selector('.vote-button__button-text')
                        
                        user = user_el.inner_text().strip() if user_el else ""
                        content = content_el.inner_text().strip() if content_el else ""
                        likes_text = like_el.inner_text().strip() if like_el else "0"
                        try:
                            likes = int(likes_text)
                        except:
                            likes = 0
                        
                        if user and content:
                            comment = {
                                "author": user,
                                "content": content,
                                "likes": likes
                            }
                            # 去重
                            key = user + content[:50]
                            if not any(c.get("author") + c.get("content", "")[:50] == key for c in comments):
                                comments.append(comment)
                                
                                if len(comments) >= limit:
                                    break
                    except Exception as e:
                        continue
                
                if len(comments) == last_count:
                    no_change_count += 1
                else:
                    no_change_count = 0
                    last_count = len(comments)
                
                if len(comments) < limit:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2.5)
                    scroll_count += 1
        
        except Exception as e:
            print(f"[taptap_comment] 抓取失败: {e}", file=sys.stderr)
        
        finally:
            browser.close()
    
    return comments[:limit]


def main():
    parser = argparse.ArgumentParser(description="TapTap Comment 抓取 (Playwright)")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--input", required=True, help="taptap_metadata 输出文件")
    parser.add_argument("--comment-limit", type=int, default=50, help="每帖子评论数")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    with open(args.input, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    posts = metadata.get("items", [])
    print(f"[taptap_comment] 处理 {len(posts)} 个帖子")
    
    results = []
    
    for i, post in enumerate(posts):
        post_url = post.get("url")
        safe_title = post.get('title', '')[:30] or "(no title)"
        print(f"[taptap_comment] [{i+1}/{len(posts)}] {safe_title}...")
        
        try:
            comments = fetch_comments_playwright(post_url, args.comment_limit)
            print(f"  获取 {len(comments)} 条评论")
        except Exception as e:
            print(f"  失败: {e}", file=sys.stderr)
            comments = []
        
        results.append({
            "id": post.get("id"),
            "title": post.get("title"),
            "url": post_url,
            "comment_count": len(comments),
            "comments": comments,
        })
        
        # 每3个帖子保存 checkpoint
        if (i + 1) % 3 == 0:
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
    print(f"[taptap_comment] 完成: {len(results)} 帖子, {total_comments} 评论")
    
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
