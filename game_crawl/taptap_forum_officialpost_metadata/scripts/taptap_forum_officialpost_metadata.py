#!/usr/bin/env python3
"""TapTap Forum Official Post Metadata - 使用 Browser Relay 抓取官方帖子
支持 checkpoint 和规范化存储

Usage:
    python taptap_forum_officialpost_metadata.py --game-id g_genshin --app-id 45213 --limit 10
    python taptap_forum_officialpost_metadata.py --game-id g_genshin --app-id 45213 --limit 10 --resume
"""
import argparse
import json
import sys
import subprocess
import re
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index


def open_page(url, profile="openclaw"):
    """打开页面，返回 target_id"""
    result = subprocess.run(
        ["openclaw", "browser", "open", "--url", url, "--profile", profile, "--json"],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        return None
    try:
        tab_info = json.loads(result.stdout)
        return tab_info.get("targetId")
    except:
        return None


def close_page(target_id, profile="openclaw"):
    """关闭页面"""
    subprocess.run(
        ["openclaw", "browser", "close", "--target-id", target_id, "--profile", profile],
        capture_output=True
    )


def evaluate_js(target_id, js_code, profile="openclaw"):
    """执行 JavaScript"""
    result = subprocess.run(
        ["openclaw", "browser", "act", "--target-id", target_id, "--profile", profile,
         "--request", json.dumps({"kind": "evaluate", "fn": js_code})],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode == 0:
        try:
            output = json.loads(result.stdout)
            return output.get("result")
        except:
            pass
    return None


def scroll_page(target_id, profile="openclaw"):
    """滚动页面"""
    js_code = "() => { window.scrollTo(0, document.body.scrollHeight); return 'scrolled'; }"
    return evaluate_js(target_id, js_code, profile)


def fetch_posts_browser(app_id: str, limit: int, storage: DataStorage, resume: bool = False, profile="openclaw") -> list:
    """使用 Browser Relay 抓取官方帖子"""
    
    list_url = f"https://www.taptap.cn/app/{app_id}/topic?type=official"
    print(f"[taptap_forum] 打开页面: {list_url}")
    
    target_id = open_page(list_url, profile)
    if not target_id:
        print("[ERROR] 无法打开页面", file=sys.stderr)
        return []
    
    posts = []
    checkpoint_num = 0
    
    # Resume
    if resume:
        latest = storage.get_latest_checkpoint("taptap", "metadata")
        if latest > 0:
            cp_data = storage.load_checkpoint(latest, "taptap", "metadata")
            posts = cp_data.get("items", [])
            checkpoint_num = latest
            print(f"[taptap_forum] 从 checkpoint {latest} 恢复，已有 {len(posts)} 个帖子")
            # 滚动恢复位置
            for _ in range(checkpoint_num * 2):
                scroll_page(target_id, profile)
                time.sleep(1)
    
    # 提取帖子列表
    extract_js = """
    () => {
        const posts = [];
        const links = document.querySelectorAll('a[href*="/moment/"], a[href*="/t/"]');
        for (const link of links) {
            try {
                const href = link.getAttribute('href');
                const title = link.textContent?.trim() || '';
                const match = href.match(/\\/(?:moment|t)\\/(\\d+)/);
                if (match) {
                    posts.push({
                        id: match[1],
                        title: title.slice(0, 200) || `帖子 ${match[1]}`,
                        url: href.startsWith('http') ? href : `https://www.taptap.cn${href}`
                    });
                }
            } catch (e) {}
        }
        return posts;
    }
    """
    
    scroll_count = 0
    max_scrolls = (limit // 3) + 10
    last_count = 0
    no_change_count = 0
    
    while len(posts) < limit and scroll_count < max_scrolls and no_change_count < 3:
        new_posts = evaluate_js(target_id, extract_js, profile) or []
        
        for post in new_posts:
            if not any(p.get('id') == post['id'] for p in posts):
                posts.append(post)
                
                # Checkpoint
                if len(posts) % 5 == 0:
                    checkpoint_num += 1
                    storage.save_checkpoint(
                        {"items": posts},
                        checkpoint_num,
                        "taptap",
                        "metadata"
                    )
                
                if len(posts) >= limit:
                    break
        
        if len(posts) == last_count:
            no_change_count += 1
        else:
            no_change_count = 0
            last_count = len(posts)
        
        print(f"  当前已获取: {len(posts)}/{limit} 个帖子")
        
        if len(posts) < limit:
            scroll_page(target_id, profile)
            time.sleep(3)
            scroll_count += 1
    
    close_page(target_id, profile)
    
    # 获取每个帖子的完整内容
    print(f"[taptap_forum] 进入帖子获取完整内容...")
    for i, post in enumerate(posts):
        try:
            print(f"  [{i+1}/{len(posts)}] 获取: {post['title'][:30]}...")
            
            post_target = open_page(post['url'], profile)
            if not post_target:
                post['content'] = ""
                continue
            
            time.sleep(3)
            
            # 提取内容
            content_js = """
            () => {
                const selectors = [
                    '.moment-page__content > div:nth-child(4) > div',
                    '.moment-page__content',
                    '.moment-content',
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.textContent.length > 20) {
                        return el.textContent.trim();
                    }
                }
                return '';
            }
            """
            
            content = evaluate_js(post_target, content_js, profile) or ""
            post['content'] = content
            
            close_page(post_target, profile)
            
            if i < len(posts) - 1:
                time.sleep(1)
                
        except Exception as e:
            print(f"    获取失败: {e}")
            post['content'] = ""
    
    # Final checkpoint
    if posts:
        storage.save_checkpoint(
            {"items": posts},
            checkpoint_num + 1,
            "taptap",
            "metadata"
        )
    
    return posts[:limit]


def main():
    parser = argparse.ArgumentParser(description="TapTap 官方帖子 Metadata 抓取 (Browser Relay)")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--app-id", required=True, help="TapTap App ID")
    parser.add_argument("--limit", type=int, default=10, help="帖子数量")
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    parser.add_argument("--profile", default="openclaw", help="Browser profile")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    print(f"[taptap_forum] 抓取官方帖子 app_id={args.app_id}, limit={args.limit}")
    if args.resume:
        print("[taptap_forum] 启用断点续传模式")
    
    posts = fetch_posts_browser(args.app_id, args.limit, storage, args.resume, args.profile)
    print(f"[taptap_forum] 获取 {len(posts)} 个帖子")
    
    result = {
        "platform": "taptap",
        "game_id": args.game_id,
        "data_type": "metadata",
        "phase": "metadata",
        "app_id": args.app_id,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(posts),
        "items": posts,
    }
    
    output_path = storage.merge_and_save(result, "taptap", "metadata", id_field="id")
    print(f"[taptap_forum] 输出: {output_path}")
    
    update_index(args.game_id, args.game_id, "taptap", "metadata", count=len(posts))
    storage.clean_checkpoints(keep_latest=3)


if __name__ == "__main__":
    main()
