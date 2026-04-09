#!/usr/bin/env python3
"""小红书Comment获取（Browser Relay版）"""
import argparse
import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index


def open_page(url, profile="openclaw"):
    """打开页面"""
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


def fetch_post_content_and_comments(post_url, max_comments=50, profile="openclaw"):
    """获取帖子内容和评论"""
    print(f"[xiaohongshu_comment] 访问帖子: {post_url}")
    
    target_id = open_page(post_url, profile)
    if not target_id:
        print("[ERROR] 无法打开帖子", file=sys.stderr)
        return {"content": "", "comments_count": 0, "comments": []}
    
    time.sleep(3)  # 等待加载
    
    # 提取内容和评论
    js_code = """
    () => {
        const result = { content: "", comments: [] };
        
        // 提取帖子内容
        const contentEl = document.querySelector('#noteContainer .note-content, .note-content, .content-container');
        if (contentEl) {
            result.content = contentEl.textContent?.trim() || "";
        }
        
        // 提取评论
        const commentItems = document.querySelectorAll('.comment-item, .comment-wrapper > div');
        let count = 0;
        for (const item of commentItems) {
            if (count >= 50) break;
            try {
                const authorEl = item.querySelector('.author, .author-name, .user-name');
                const contentEl = item.querySelector('.content span, .comment-content, .text');
                const likeEl = item.querySelector('.like .count, .like-count, .vote-count');
                
                const author = authorEl?.textContent?.trim() || "匿名";
                const content = contentEl?.textContent?.trim() || "";
                const likes = parseInt(likeEl?.textContent?.trim() || '0') || 0;
                
                if (content) {
                    result.comments.push({
                        id: item.getAttribute('id') || `comment-${count}`,
                        author: author,
                        content: content,
                        likes: likes,
                    });
                    count++;
                }
            } catch (e) {}
        }
        
        result.comments_count = result.comments.length;
        return result;
    }
    """
    
    data = evaluate_js(target_id, js_code, profile) or {"content": "", "comments": []}
    data["comments_count"] = len(data.get("comments", []))
    
    close_page(target_id, profile)
    
    print(f"[xiaohongshu_comment] 成功提取 {data['comments_count']} 条评论")
    return data


def main():
    parser = argparse.ArgumentParser(description="小红书Comment获取（Browser Relay）")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--input", required=True, help="xiaohongshu_metadata.json文件路径")
    parser.add_argument("--resume", action="store_true", help="从checkpoint恢复")
    parser.add_argument("--profile", default="openclaw", help="Browser profile")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    # 读取metadata
    with open(args.input, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    posts = metadata.get("items", [])
    print(f"[xiaohongshu_comment] 处理 {len(posts)} 个帖子")
    
    # Checkpoint恢复
    results = []
    start_idx = 0
    if args.resume:
        latest = storage.get_latest_checkpoint("xiaohongshu", "comment")
        if latest > 0:
            cp_data = storage.load_checkpoint(latest, "xiaohongshu", "comment")
            results = cp_data.get("items", [])
            start_idx = len(results)
            print(f"[xiaohongshu_comment] 从 checkpoint {latest} 恢复，已处理 {len(results)} 个帖子")
    
    checkpoint_num = (start_idx // 5) + 1
    
    for idx, post in enumerate(posts[start_idx:], start=start_idx + 1):
        print(f"\n[xiaohongshu_comment] [{idx}/{len(posts)}] {post.get('title', '')[:40]}...")
        
        data = fetch_post_content_and_comments(post["url"], max_comments=50, profile=args.profile)
        
        results.append({
            **post,
            "content": data["content"],
            "comments_count": data["comments_count"],
            "comments": data["comments"],
        })
        
        # Checkpoint：每5个帖子保存一次
        if idx % 5 == 0:
            checkpoint_num += 1
            storage.save_checkpoint(
                {"items": results},
                checkpoint_num,
                "xiaohongshu",
                "comment"
            )
            print(f"[xiaohongshu_comment] Checkpoint {checkpoint_num} 已保存")
        
        # 间隔，避免请求过快
        if idx < len(posts):
            time.sleep(1)
    
    # 保存最终结果
    result = {
        "platform": "xiaohongshu",
        "game_id": args.game_id,
        "data_type": "comment",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "items": results,
    }
    
    path = storage.merge_and_save(result, "xiaohongshu", "comment", id_field="id")
    update_index(args.game_id, args.game_id, "xiaohongshu", "comment", count=len(results))
    
    print(f"\n[xiaohongshu_comment] 完成！处理{len(results)}个帖子，保存到: {path}")
    print(f"[xiaohongshu_comment] 总评论数: {sum(item.get('comments_count', 0) for item in results)}")


if __name__ == "__main__":
    main()
