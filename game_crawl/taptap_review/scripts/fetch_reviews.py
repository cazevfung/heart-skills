#!/usr/bin/env python3
"""TapTap Review Crawler - 使用 Browser Relay"""

import json
import time
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage

def fetch_reviews_with_browser(app_id, game_id, game_name, limit=100, profile="openclaw"):
    """使用 Browser Relay 抓取 TapTap 评价"""
    print(f"[taptap_review] 开始抓取 {game_name} (app_id: {app_id}) 的评价...")
    
    url = f"https://www.taptap.cn/app/{app_id}/review?os=android"
    
    # 打开页面
    result = subprocess.run(
        ["openclaw", "browser", "open", "--url", url, "--profile", profile, "--json"],
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
    
    reviews = []
    seen_ids = set()
    
    # 提取评价的 JavaScript
    js_code = """
    () => {
        const reviews = [];
        const seen = new Set();
        const review_elements = document.querySelectorAll('.review-item');
        
        for (const el of review_elements) {
            try {
                const author_el = el.querySelector('.review-item__user-wrap a span, .review-item__user-wrap span');
                const content_el = el.querySelector('.review-item__body .collapse-text-emoji__content span');
                const likes_el = el.querySelector('.review-vote-up span');
                const time_el = el.querySelector('.review-item__footer time');
                const review_link = el.querySelector('a[href^="/review/"]');
                
                let review_id = null;
                if (review_link) {
                    const href = review_link.getAttribute('href');
                    review_id = href.split('/')[2]?.split('#')[0];
                }
                
                if (author_el && content_el && review_id && !seen.has(review_id)) {
                    seen.add(review_id);
                    reviews.push({
                        id: review_id,
                        author: author_el.textContent?.trim() || '',
                        content: content_el.textContent?.trim() || '',
                        likes: parseInt(likes_el?.textContent?.trim() || '0'),
                        time: time_el?.textContent?.trim() || '',
                        url: `https://www.taptap.cn/review/${review_id}`
                    });
                }
            } catch (e) {
                console.error('提取评价失败:', e);
            }
        }
        return reviews;
    }
    """
    
    # 滚动和提取
    for scroll_round in range(20):
        if len(reviews) >= limit:
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
                new_reviews = output.get("result", [])
                for r in new_reviews:
                    if r['id'] not in seen_ids:
                        seen_ids.add(r['id'])
                        reviews.append(r)
                print(f"[taptap_review] 第{scroll_round+1}轮: 已收集 {len(reviews)} 条")
            except:
                pass
        
        if len(reviews) >= limit:
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
    
    # 截取前 limit 条
    reviews = reviews[:limit]
    
    # 保存数据
    storage = DataStorage(game_id)
    output_data = {
        'platform': 'taptap',
        'data_type': 'review',
        'game_id': game_id,
        'game_name': game_name,
        'app_id': app_id,
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'count': len(reviews),
        'reviews': reviews
    }
    
    output_path = storage.save_taptap_reviews(output_data)
    print(f"[taptap_review] 数据已保存到: {output_path}")
    
    return reviews

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="TapTap Review - Browser Relay")
    parser.add_argument("--app-id", required=True, help="TapTap app ID")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--game-name", required=True, help="游戏名称")
    parser.add_argument("--limit", type=int, default=100, help="数量限制")
    parser.add_argument("--profile", default="openclaw", help="Browser profile")
    args = parser.parse_args()
    
    try:
        reviews = fetch_reviews_with_browser(
            args.app_id, 
            args.game_id, 
            args.game_name,
            limit=args.limit,
            profile=args.profile
        )
        print(f"✅ {args.game_name}: 成功抓取 {len(reviews)} 条评价")
    except Exception as e:
        print(f"❌ {args.game_name}: 抓取失败 - {e}")
        import traceback
        traceback.print_exc()
