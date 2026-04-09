#!/usr/bin/env python3
"""
TapTap Review - 使用 Playwright 抓取评价（含发布时间）
支持 checkpoint 和规范化存储

Usage:
    python taptap_review.py --game-id g_genshin --app-id 45213 --limit 50
    python taptap_review.py --game-id g_genshin --app-id 45213 --limit 50 --resume
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index


def parse_relative_time(time_text: str) -> str:
    """解析 TapTap 相对时间为 ISO 格式"""
    if not time_text:
        return ""
    
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    time_text = time_text.strip()
    
    # 匹配 "X天前", "X小时前", "X分钟前", "刚刚"
    patterns = [
        (r'(\d+)\s*天前', 'days'),
        (r'(\d+)\s*小时前', 'hours'),
        (r'(\d+)\s*分钟前', 'minutes'),
        (r'刚刚', 'now'),
    ]
    
    for pattern, unit in patterns:
        match = re.search(pattern, time_text)
        if match:
            if unit == 'now':
                return now.isoformat()
            value = int(match.group(1))
            if unit == 'days':
                dt = now - timedelta(days=value)
            elif unit == 'hours':
                dt = now - timedelta(hours=value)
            elif unit == 'minutes':
                dt = now - timedelta(minutes=value)
            return dt.isoformat()
    
    # 处理日期格式 (2026/3/5 或 2025-03-21)
    date_formats = ["%Y/%m/%d", "%Y-%m-%d", "%Y/%m/%d %H:%M"]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(time_text, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except:
            pass
    
    return ""


def fetch_reviews_playwright(app_id: str, limit: int, storage: DataStorage, resume: bool = False, label: str | None = None, mapping: str | None = None) -> list:
    """使用 Playwright 抓取评价，支持 checkpoint"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[taptap_review] 错误: 未安装 playwright", file=sys.stderr)
        return []
    
    # label=0 表示差评(1星)或中评(3星), mapping 区分类型
    if label is not None and mapping is not None:
        url = f"https://www.taptap.cn/app/{app_id}/review?os=pc&mapping={mapping}&label={label}"
        print(f"[taptap_review] 打开页面: {url}")
    elif label is not None:
        url = f"https://www.taptap.cn/app/{app_id}/review?os=pc&label={label}"
        print(f"[taptap_review] 打开差评页面: {url}")
    else:
        url = f"https://www.taptap.cn/app/{app_id}/review?os=pc"
        print(f"[taptap_review] 打开页面: {url}")
    
    reviews = []
    checkpoint_num = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(3)
            
            # Resume
            if resume:
                latest = storage.get_latest_checkpoint("taptap", "review")
                if latest > 0:
                    cp_data = storage.load_checkpoint(latest, "taptap", "review")
                    reviews = cp_data.get("items", [])
                    checkpoint_num = latest
                    print(f"[taptap_review] 从 checkpoint {latest} 恢复，已有 {len(reviews)} 条评价")
                    # 滚动到之前的位置
                    for _ in range(checkpoint_num * 3):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)
            
            scroll_count = 0
            max_scrolls = (limit // 5) + 10
            last_count = 0
            no_change_count = 0
            
            while len(reviews) < limit and scroll_count < max_scrolls and no_change_count < 3:
                items = page.query_selector_all('.review-item--in-app-tab__content, .review-item__content')
                
                for item in items:
                    try:
                        user_el = item.query_selector('.review-item__user-wrap span, .review-item__user-wrap a span')
                        user = user_el.inner_text().strip() if user_el else ""
                        
                        content_el = item.query_selector('.review-item__body .collapse-text-emoji__content span, .review-item__body span')
                        content = content_el.inner_text().strip() if content_el else ""
                        
                        like_el = item.query_selector('.review-vote-up span, .review-item__operations span')
                        likes_text = like_el.inner_text().strip() if like_el else "0"
                        try:
                            likes = int(likes_text)
                        except:
                            likes = 0
                        
                        # 提取发布时间
                        time_el = item.query_selector('span[class*=time]')
                        time_text = time_el.inner_text().strip() if time_el else ""
                        published_at = parse_relative_time(time_text)
                        
                        if user and content:
                            review = {
                                "author": user,
                                "content": content,
                                "likes": likes,
                                "published_at": published_at,
                                "published_text": time_text,  # 保留原始文本
                            }
                            # 去重检查
                            if not any(r["author"] == user and r["content"] == content for r in reviews):
                                reviews.append(review)
                                
                                # Checkpoint
                                if len(reviews) % 10 == 0:
                                    checkpoint_num += 1
                                    storage.save_checkpoint(
                                        {"items": reviews},
                                        checkpoint_num,
                                        "taptap",
                                        "review"
                                    )
                                
                                if len(reviews) >= limit:
                                    break
                    except Exception as e:
                        continue
                
                if len(reviews) == last_count:
                    no_change_count += 1
                else:
                    no_change_count = 0
                    last_count = len(reviews)
                
                print(f"  当前已获取: {len(reviews)}/{limit} 条评价")
                
                if len(reviews) < limit:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2.5)
                    scroll_count += 1
        
        except Exception as e:
            print(f"[taptap_review] 抓取失败: {e}", file=sys.stderr)
        
        finally:
            browser.close()
    
    # Final checkpoint
    if reviews:
        storage.save_checkpoint(
            {"items": reviews},
            checkpoint_num + 1,
            "taptap",
            "review"
        )
    
    return reviews[:limit]


def main():
    parser = argparse.ArgumentParser(description="TapTap Review 抓取 (Playwright)")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--app-id", required=True, help="TapTap App ID")
    parser.add_argument("--limit", type=int, default=50, help="评价数量限制")
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    parser.add_argument("--label", type=str, default=None, help="评分筛选 (0=差评, 5=好评)")
    parser.add_argument("--mapping", type=str, default=None, help="评价类型 (差评, 中评, 好评)")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    if args.label is not None and args.mapping is not None:
        print(f"[taptap_review] 抓取 {args.mapping} app_id={args.app_id}, limit={args.limit}")
        data_type = f"review_{args.mapping}"
    elif args.label is not None:
        print(f"[taptap_review] 抓取差评 app_id={args.app_id}, label={args.label}, limit={args.limit}")
        data_type = "review_negative"
    else:
        print(f"[taptap_review] 抓取 app_id={args.app_id}, limit={args.limit}")
        data_type = "review"
    
    if args.resume:
        print("[taptap_review] 启用断点续传模式")
    
    reviews = fetch_reviews_playwright(args.app_id, args.limit, storage, args.resume, args.label, args.mapping)
    print(f"[taptap_review] 获取 {len(reviews)} 条评价")
    
    result = {
        "platform": "taptap",
        "game_id": args.game_id,
        "data_type": data_type,
        "app_id": args.app_id,
        "label": args.label,
        "mapping": args.mapping,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(reviews),
        "items": reviews,
    }
    
    output_path = storage.merge_and_save(result, "taptap", data_type, id_field="author")
    print(f"[taptap_review] 输出: {output_path}")
    
    # 更新数据索引
    update_index(args.game_id, args.game_id, "taptap", data_type, count=len(reviews))
    
    storage.clean_checkpoints(keep_latest=3)


if __name__ == "__main__":
    main()
