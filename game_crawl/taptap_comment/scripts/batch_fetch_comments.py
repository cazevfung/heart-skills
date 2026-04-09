#!/usr/bin/env python3
"""批量抓取 TapTap 帖子评论"""
import json
import subprocess
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

def fetch_comments_for_post(post_url, post_id, profile="user"):
    """抓取单个帖子的评论"""
    comments = []
    target_id = None
    
    try:
        # 打开页面
        result = subprocess.run(
            ["openclaw", "browser", "open", "--url", post_url, "--profile", profile, "--json"],
            capture_output=True, text=True, encoding='utf-8'
        )
        if result.returncode != 0:
            print(f"  [ERROR] 打开页面失败: {post_id}")
            return []
        
        tab_info = json.loads(result.stdout)
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
                except:
                    pass
            
            if len(comments) >= 50:
                break
            
            # 滚动
            scroll_js = "() => { window.scrollTo(0, document.body.scrollHeight); return 'scrolled'; }"
            subprocess.run(
                ["openclaw", "browser", "act", "--target-id", target_id, "--profile", profile,
                 "--request", json.dumps({"kind": "evaluate", "fn": scroll_js})],
                capture_output=True
            )
            time.sleep(2)
        
    finally:
        # 关闭标签页
        if target_id:
            subprocess.run(
                ["openclaw", "browser", "close", "--target-id", target_id, "--profile", profile],
                capture_output=True
            )
    
    return comments[:50]


def main():
    game_id = "g_a1b2c3d4"
    
    # 读取已有数据
    with open(f"D:/App Dev/openclaw-main/data/game_data/games/{game_id}/taptap/comment.json", "r", encoding="utf-8") as f:
        existing_data = json.load(f)
    
    # 读取所有帖子
    with open(f"D:/App Dev/openclaw-main/data/game_data/games/{game_id}/taptap/official_posts.json", "r", encoding="utf-8") as f:
        posts_data = json.load(f)
    
    existing_items = {item["id"]: item for item in existing_data.get("items", [])}
    all_posts = posts_data.get("items", [])
    
    # 找出未处理的帖子
    remaining_posts = [p for p in all_posts if p["id"] not in existing_items or not existing_items[p["id"]].get("comments")]
    
    print(f"[taptap_comment] 总共 {len(all_posts)} 帖子，已完成 {len(existing_items)}，剩余 {len(remaining_posts)}")
    
    results = list(existing_data.get("items", []))
    processed_count = 0
    total_comments = 0
    
    for i, post in enumerate(remaining_posts):
        post_id = post.get("id")
        post_url = post.get("url")
        title = post.get("title", "")[:30]
        
        print(f"[{i+1}/{len(remaining_posts)}] 处理: {title}...")
        
        try:
            comments = fetch_comments_for_post(post_url, post_id)
            processed_count += 1
            total_comments += len(comments)
            
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
            
            print(f"  获取 {len(comments)} 条评论")
            
            # 每 5 个帖子保存一次
            if processed_count % 5 == 0:
                save_results(game_id, results)
                print(f"  [CHECKPOINT] 已保存进度")
                
        except Exception as e:
            print(f"  [ERROR] 处理失败: {e}")
            continue
    
    # 最终保存
    save_results(game_id, results)
    
    # 统计
    total = sum(r["comment_count"] for r in results)
    print(f"\n[taptap_comment] 完成!")
    print(f"  帖子数: {len(results)}")
    print(f"  评论总数: {total}")
    
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
