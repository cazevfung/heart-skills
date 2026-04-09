#!/usr/bin/env python3
"""
Bilibili Metadata Browser - 使用 Playwright 抓取B站视频搜索
支持 checkpoint 和规范化存储

Usage:
    python bilibili_metadata_browser.py --game-id g_genshin --keyword "原神 前瞻" --limit 10
    python bilibili_metadata_browser.py --game-id g_genshin --keyword "原神 前瞻" --limit 10 --resume
"""
import argparse
import json
import sys
import time
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path("D:/App Dev/openclaw-main/scripts")))
from storage_tool import DataStorage, update_index


def fetch_videos_playwright(keyword: str, limit: int, storage: DataStorage, resume: bool = False) -> list:
    """使用 Playwright 抓取B站视频，支持 checkpoint"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[bilibili_metadata_browser] 错误: 未安装 playwright", file=sys.stderr)
        return []
    
    encoded_keyword = quote(keyword)
    url = f"https://search.bilibili.com/all?keyword={encoded_keyword}"
    print(f"[bilibili_metadata_browser] 打开页面: {url}")
    
    videos = []
    checkpoint_num = 0
    seen_bvids = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(5)
            
            # Resume
            if resume:
                latest = storage.get_latest_checkpoint("bilibili", "metadata")
                if latest > 0:
                    cp_data = storage.load_checkpoint(latest, "bilibili", "metadata")
                    videos = cp_data.get("items", [])
                    seen_bvids = {v['bvid'] for v in videos}
                    checkpoint_num = latest
                    print(f"[bilibili_metadata_browser] 从 checkpoint {latest} 恢复，已有 {len(videos)} 个视频")
                    for _ in range(checkpoint_num * 2):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)
            
            scroll_count = 0
            max_scrolls = (limit // 10) + 10
            last_count = 0
            no_change_count = 0
            
            while len(videos) < limit and scroll_count < max_scrolls and no_change_count < 3:
                # 使用JavaScript提取页面数据
                video_data = page.evaluate("""
                    () => {
                        const results = [];
                        // 查找所有视频卡片
                        const cards = document.querySelectorAll('a[href*="/video/BV"]');
                        cards.forEach(card => {
                            const href = card.getAttribute('href');
                            if (!href) return;
                            
                            // 提取BV号
                            const bvidMatch = href.match(/\/video\/(BV\w+)/);
                            if (!bvidMatch) return;
                            const bvid = bvidMatch[1];
                            
                            // 获取标题
                            let title = '';
                            const heading = card.querySelector('h3');
                            if (heading) {
                                title = heading.textContent.trim();
                            } else {
                                title = card.getAttribute('title') || '';
                            }
                            
                            // 获取所有文本
                            const allText = card.textContent.trim();
                            
                            // 查找UP主信息 - 在同一个卡片容器内
                            let author = '';
                            let pubdate = '';
                            let playCount = '';
                            let duration = '';
                            
                            // 获取父容器
                            let container = card.parentElement;
                            for (let i = 0; i < 5 && container; i++) {
                                // 查找UP主链接
                                const authorLinks = container.querySelectorAll('a[href*="/space/"]');
                                for (const link of authorLinks) {
                                    const text = link.textContent.trim();
                                    if (text.includes(' · ')) {
                                        const parts = text.split(' · ');
                                        author = parts[0];
                                        pubdate = parts[1] || '';
                                        break;
                                    }
                                }
                                if (author) break;
                                container = container.parentElement;
                            }
                            
                            // 从文本中提取播放量和时长
                            const lines = allText.split('\\n').map(l => l.trim()).filter(l => l);
                            for (const line of lines) {
                                // 匹配时长格式
                                if (/^\\d{1,2}:\\d{2}(?::\\d{2})?$/.test(line)) {
                                    duration = line;
                                }
                                // 匹配播放量（包含万）
                                else if (/^\\d+(\\.\\d+)?万?$/.test(line) && line !== title) {
                                    playCount = line;
                                }
                            }
                            
                            results.push({
                                bvid: bvid,
                                title: title,
                                author: author,
                                pubdate: pubdate,
                                playCount: playCount,
                                duration: duration,
                                href: href
                            });
                        });
                        return results;
                    }
                """)
                
                print(f"  页面中找到 {len(video_data)} 个视频")
                
                for data in video_data:
                    try:
                        bvid = data['bvid']
                        
                        # 检查重复
                        if bvid in seen_bvids:
                            continue
                        seen_bvids.add(bvid)
                        
                        href = data['href']
                        video_url = href if href.startswith('http') else f"https:{href}"
                        
                        videos.append({
                            "id": bvid,
                            "bvid": bvid,
                            "title": data['title'][:200] if data['title'] else f"视频 {bvid}",
                            "author": data['author'][:50] if data['author'] else "",
                            "url": video_url,
                            "pubdate": data['pubdate'],
                            "play_count": data['playCount'],
                            "duration": data['duration'],
                        })
                        
                        # Checkpoint
                        if len(videos) % 10 == 0:
                            checkpoint_num += 1
                            storage.save_checkpoint(
                                {"items": videos, "keyword": keyword},
                                checkpoint_num,
                                "bilibili",
                                "metadata"
                            )
                        
                        if len(videos) >= limit:
                            break
                    except Exception as e:
                        print(f"    解析数据失败: {e}")
                        continue
                
                if len(videos) == last_count:
                    no_change_count += 1
                else:
                    no_change_count = 0
                    last_count = len(videos)
                
                print(f"  当前已获取: {len(videos)}/{limit} 个视频")
                
                if len(videos) < limit:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(3)
                    scroll_count += 1
        
        except Exception as e:
            print(f"[bilibili_metadata_browser] 抓取失败: {e}", file=sys.stderr)
        
        finally:
            browser.close()
    
    # Final checkpoint
    if videos:
        storage.save_checkpoint(
            {"items": videos, "keyword": keyword},
            checkpoint_num + 1,
            "bilibili",
            "metadata"
        )
    
    return videos[:limit]


def main():
    parser = argparse.ArgumentParser(description="Bilibili Metadata 搜索 (Playwright)")
    parser.add_argument("--game-id", required=True, help="游戏ID")
    parser.add_argument("--keyword", required=True, help="搜索关键词")
    parser.add_argument("--limit", type=int, default=10, help="数量限制")
    parser.add_argument("--resume", action="store_true", help="从 checkpoint 恢复")
    args = parser.parse_args()
    
    storage = DataStorage(args.game_id)
    
    print(f"[bilibili_metadata_browser] 搜索: {args.keyword}, 限制: {args.limit}")
    if args.resume:
        print("[bilibili_metadata_browser] 启用断点续传模式")
    
    videos = fetch_videos_playwright(args.keyword, args.limit, storage, args.resume)
    print(f"[bilibili_metadata_browser] 找到 {len(videos)} 个视频")
    
    result = {
        "platform": "bilibili",
        "game_id": args.game_id,
        "data_type": "metadata",
        "phase": "metadata",
        "keyword": args.keyword,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(videos),
        "items": videos,
    }
    
    output_path = storage.merge_and_save(result, "bilibili", "metadata", id_field="id")
    print(f"[bilibili_metadata_browser] 输出: {output_path}")
    
    # 更新数据索引
    update_index(args.game_id, args.game_id, "bilibili", "metadata", count=len(videos))
    
    storage.clean_checkpoints(keep_latest=3)


if __name__ == "__main__":
    main()
