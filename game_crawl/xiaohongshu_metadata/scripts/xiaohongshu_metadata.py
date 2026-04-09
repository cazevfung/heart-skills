#!/usr/bin/env python3
"""小红书Metadata获取（使用OpenClaw Browser Relay）"""
import argparse
import json
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone
import urllib.parse

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index

def get_browser_data(url, profile="openclaw"):
    """使用OpenClaw browser获取页面数据"""
    # 打开页面
    result = subprocess.run(
        ["openclaw", "browser", "open", "--url", url, "--profile", profile, "--json"],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        print(f"[ERROR] 打开页面失败: {result.stderr}", file=sys.stderr)
        return None
    
    tab_info = json.loads(result.stdout)
    target_id = tab_info.get("targetId")
    
    if not target_id:
        return None
    
    # 等待加载
    time.sleep(3)
    
    # 执行JavaScript提取数据
    js_code = """
    () => {
        const posts = [];
        const seen = new Set();
        const items = document.querySelectorAll('section');
        items.forEach(item => {
            const linkEl = item.querySelector('a[href*="/search_result/"]');
            const titleEl = item.querySelector('.title, .desc');
            const authorEl = item.querySelector('.name');
            const likeEl = item.querySelector('span[class*="like"], span[class*="count"]');
            
            if (linkEl) {
                const id = linkEl.href.match(/search_result\\/(\\w+)/)?.[1];
                if (id && !seen.has(id)) {
                    seen.add(id);
                    posts.push({
                        id: id,
                        url: linkEl.href,
                        title: titleEl?.textContent?.trim() || '',
                        author: authorEl?.textContent?.trim() || '',
                        likes: likeEl?.textContent?.trim() || ''
                    });
                }
            }
        });
        return posts;
    }
    """
    
    result = subprocess.run(
        ["openclaw", "browser", "act", "--target-id", target_id, "--profile", profile,
         "--request", json.dumps({"kind": "evaluate", "fn": js_code})],
        capture_output=True, text=True, encoding='utf-8'
    )
    
    # 关闭标签页
    subprocess.run(
        ["openclaw", "browser", "close", "--target-id", target_id, "--profile", profile],
        capture_output=True
    )
    
    if result.returncode != 0:
        print(f"[ERROR] 提取数据失败: {result.stderr}", file=sys.stderr)
        return None
    
    try:
        output = json.loads(result.stdout)
        return output.get("result", [])
    except:
        return None

def main():
    parser = argparse.ArgumentParser(description="小红书Metadata获取（Browser Relay版）")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--keyword", required=True, help="搜索关键词")
    parser.add_argument("--limit", type=int, default=100, help="数量限制")
    parser.add_argument("--profile", default="openclaw", help="Browser profile")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    # 编码关键词
    encoded_keyword = urllib.parse.quote(args.keyword)
    url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}"
    
    print(f"[xiaohongshu_metadata] 抓取关键词: {args.keyword}")
    print(f"[xiaohongshu_metadata] 使用profile: {args.profile}")
    
    all_posts = []
    
    # 第一轮获取
    posts = get_browser_data(url, args.profile)
    if posts:
        all_posts.extend(posts)
        print(f"[xiaohongshu_metadata] 第一轮获取 {len(posts)} 条")
    
    # 去重
    seen = set()
    unique_posts = []
    for p in all_posts:
        if p.get("id") and p["id"] not in seen:
            seen.add(p["id"])
            unique_posts.append(p)
    
    unique_posts = unique_posts[:args.limit]
    
    # 保存结果
    result = {
        "platform": "xiaohongshu",
        "game_id": args.game_id,
        "data_type": "metadata",
        "keyword": args.keyword,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(unique_posts),
        "items": unique_posts,
    }
    
    path = storage.merge_and_save(result, "xiaohongshu", "metadata", id_field="id")
    update_index(args.game_id, args.game_id, "xiaohongshu", "metadata", count=len(unique_posts))
    
    print(f"[xiaohongshu_metadata] 完成，找到 {len(unique_posts)} 条帖子，保存到: {path}")

if __name__ == "__main__":
    main()
