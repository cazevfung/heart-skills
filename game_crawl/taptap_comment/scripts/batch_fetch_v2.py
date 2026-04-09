#!/usr/bin/env python3
"""批量抓取 TapTap 帖子评论 - 使用 browser 工具直接调用"""
import json
import time
import sys
from pathlib import Path

# Fix Windows encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

# 导入 browser 工具
def browser_open(url, profile="user"):
    """使用 browser 工具打开页面"""
    import subprocess
    result = subprocess.run(
        ["openclaw", "browser", "open", "--url", url, "--profile", profile, "--json"],
        capture_output=True, text=True, encoding='utf-8', shell=False
    )
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None

def browser_close(target_id, profile="user"):
    """关闭页面"""
    import subprocess
    subprocess.run(
        ["openclaw", "browser", "close", "--target-id", target_id, "--profile", profile],
        capture_output=True
    )

def browser_evaluate(target_id, js_code, profile="user"):
    """执行 JavaScript"""
    import subprocess
    result = subprocess.run(
        ["openclaw", "browser", "act", "--target-id", target_id, "--profile", profile,
         "--request", json.dumps({"kind": "evaluate", "fn": js_code})],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except:
            pass
    return None

def fetch_comments_for_post(post_url, post_id, profile="user"):
    """抓取单个帖子的评论"""
    comments = []
    target_id = None
    
    try:
        # 打开页面
        tab_info = browser_open(post_url, profile)
        if not tab_info:
            print(f"  [ERROR] 打开页面失败: {post_id}")
            return []
        
        target_id = tab_info.get("targetId")
        
        if not target_id:
            print(f"  [ERROR] 无法获取 targetId: {post_id}")
            return []
        
        # 等待加载
        time.sleep(3)
        
        # 提取评论的 JavaScript
        js_code = """
        () => {
            const comments = [];
            const items = document.querySelectorAll('.moment-comment-list .tap-list > div, .moment-post-item');
            
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
                } catch (e) {}
            }
            return comments;
        }
        """
        
        # 滚动和提取
        seen = set()
        for scroll_round in range(10):
            output = browser_evaluate(target_id, js_code, profile)
            
            if output and "result" in output:
                new_comments = output.get("result", [])
                for c in new_comments:
                    key = c['author'] + c['content'][:50]
                    if key not in seen:
                        seen.add(key)
                        comments.append(c)
            
            if len(comments) >= 50:
                break
            
            # 滚动
            scroll_js = "() => { window.scrollTo(0, document.body.scrollHeight); return 'scrolled'; }"
            browser_evaluate(target_id, scroll_js, profile)
            time.sleep(2)
        
    finally:
        # 关闭标签页
        if target_id:
            browser_close(target_id, profile)
    
    return comments[:50]


def main():
    game_id = "g_a1b2c3d4"
    
    # 读取已有数据
    comment_path = f"D:/App Dev/openclaw-main/data/game_data/games/{game_id}/taptap/comment.json"
    with open(comment_path, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
    
    # 读取所有帖子
    posts_path = f"D:/App Dev/openclaw-main/data/game_data/games/{game_id}/taptap/official_posts.json"
    with open(posts_path, "r", encoding="utf-8") as f:
        posts_data = json.load(f)
    
    existing_items = {item["id"]: item for item in existing_data.get("items", [])}
    all_posts = posts_data.get("items", [])
    
    # 找出未处理的帖子（没有 comments 或 comments 为空的）
    remaining_posts = []
    for p in all_posts:
        existing = existing_items.get(p["id"])
        if not existing or not existing.get("comments"):
            remaining_posts.append(p)
    
    print(f"[taptap_comment] Total: {len(all_posts)}, Done: {len(existing_items)}, Remaining: {len(remaining_posts)}")
    
    results = list(existing_data.get("items", []))
    processed_count = 0
    
    for i, post in enumerate(remaining_posts):
        post_id = post.get("id")
        post_url = post.get("url")
        title = post.get("title", "")[:30]
        
        print(f"[{i+1}/{len(remaining_posts)}] Processing: {title}...")
        
        try:
            comments = fetch_comments_for_post(post_url, post_id)
            processed_count += 1
            
            # 更新或添加结果
            result_item = {
                "id": post_id,
                "title": post.get("title"),
                "url": post_url,
                "comment_count": len(comments),
                "comments": comments,
            }
            
            # 替换已有条目或添加新条目
            existing_idx = next((idx for idx, item in enumerate(results) if item["id"] == post_id), None)
            if existing_idx is not None:
                results[existing_idx] = result_item
            else:
                results.append(result_item)
            
            print(f"  Got {len(comments)} comments")
            
            # 每 5 个帖子保存一次
            if processed_count % 5 == 0:
                save_results(game_id, results)
                print(f"  [CHECKPOINT] Saved progress")
                
        except Exception as e:
            print(f"  [ERROR] Failed: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 最终保存
    save_results(game_id, results)
    
    # 统计
    total = sum(r["comment_count"] for r in results)
    print(f"\n[taptap_comment] Done!")
    print(f"  Posts: {len(results)}")
    print(f"  Total comments: {total}")
    
    # 更新索引
    update_index(game_id, "心动小镇", "taptap", "comment", count=len(results))


def save_results(game_id, results):
    """保存结果"""
    from datetime import datetime, timezone
    
    output = {
        "platform": "taptap",
        "game_id": game_id,
        "data_type": "comment",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "items": results,
    }
    
    output_path = f"D:/App Dev/openclaw-main/data/game_data/games/{game_id}/taptap/comment.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    return output_path


if __name__ == "__main__":
    main()
