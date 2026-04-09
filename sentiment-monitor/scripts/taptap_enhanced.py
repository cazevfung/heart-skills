#!/usr/bin/env python3
"""
TapTap Enhanced Crawler - 增强版采集器
支持完整评论树采集、历史数据回溯、增量追加（含 recorded_at 首次入库时间）。

Usage:
    python taptap_enhanced.py --app-id 45213 --mode full --days 365 --output-dir ./data
    python taptap_enhanced.py --app-id 45213 --mode incremental --days 1 --output-dir ./data
    # 定时（如每小时）执行 incremental，新评论会追加到 state 并带 recorded_at
"""

import argparse
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin

# Heartbeat: emit a line to stderr every N seconds so caller can use "no log = timeout" instead of fixed wall-clock timeout.
_HEARTBEAT_INTERVAL_SEC = int(os.environ.get("TAPTAP_HEARTBEAT_INTERVAL_SEC", "60"))


def _heartbeat(phase: str, **kwargs: object) -> None:
    """Emit a single line to stderr for progress/timeout detection. Flush so exec sees it immediately."""
    msg = " ".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
    print(f"[taptap_enhanced] heartbeat phase={phase} {msg}", file=sys.stderr)
    sys.stderr.flush()


def _maybe_heartbeat(last_ts: list, phase: str, **kwargs: object) -> None:
    """If at least _HEARTBEAT_INTERVAL_SEC since last_ts[0], emit heartbeat and update last_ts."""
    now = time.monotonic()
    if last_ts and (now - last_ts[0]) < _HEARTBEAT_INTERVAL_SEC:
        return
    last_ts[0] = now
    _heartbeat(phase, **kwargs)


def parse_days_ago(created_at: str) -> Optional[float]:
    """将列表页时间文案解析为「距今天数」。无法解析时返回 None（视为近期，不用于停止条件）。"""
    if not created_at or not created_at.strip():
        return None
    s = created_at.strip()
    # "N 天前" / "N天前"
    m = re.search(r"(\d+)\s*天\s*前", s)
    if m:
        return float(m.group(1))
    # "N 小时前" / "N小时前"
    m = re.search(r"(\d+)\s*小时\s*前", s)
    if m:
        return float(m.group(1)) / 24.0
    # "N 分钟前" / "N分钟前"
    m = re.search(r"(\d+)\s*分钟\s*前", s)
    if m:
        return float(m.group(1)) / (24.0 * 60)
    # "刚刚"
    if "刚刚" in s:
        return 0.0
    # "YYYY-MM-DD" / "YYYY-M-D"
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        try:
            t = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - t
            return max(0.0, delta.total_seconds() / 86400.0)
        except ValueError:
            pass
    return None

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:
    print(json.dumps({"status": "error", "reason": "Playwright not installed"}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)

# Load selectors from same directory (run from scripts/ or add to path)
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
import taptap_selectors as sel

# #region agent log
def _debug_log(location: str, message: str, data: dict, hypothesis_id: str = "") -> None:
    _log_path = _scripts_dir.parent.parent.parent / "debug-0f888a.log"
    try:
        import json as _json
        payload = {"sessionId": "0f888a", "location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000)}
        if hypothesis_id:
            payload["hypothesisId"] = hypothesis_id
        with open(_log_path, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion

class TapTapEnhancedCrawler:
    """TapTap增强版采集器"""
    
    BASE_URL = "https://www.taptap.cn"
    
    def __init__(self, app_id: str, output_dir: str = "./taptap_data"):
        self.app_id = app_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def fetch_post_list(self, limit: int = 100, days_back: int = 365, topic_type: str = "official") -> List[Dict]:
        """采集帖子列表。topic_type: 'official' 仅官方帖，'' 为全部。
        按时间加载直到遇到超过 days_back 天的帖子才停止，确保覆盖用户要求的完整时间范围；
        最终只保留 created_at 在 [0, days_back) 天内的帖子（不含触发停止的那条及更老的）。"""
        url = f"{self.BASE_URL}/app/{self.app_id}/topic"
        if topic_type:
            url = f"{url}?type={topic_type}"
        
        posts: List[Dict] = []
        # 滚动次数上限：按天数停止时可能需较多滚动，给足次数
        max_scrolls = max(min(limit // 10 + 5, 20), 100)
        last_heartbeat: list = [0.0]
        scrolls_without_new = 0

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()

            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)
                # Anti-scraping: check page title
                try:
                    title = (page.title() or "").lower()
                    if any(kw in title for kw in ("验证", "captcha", "人机", "verify", "安全")):
                        print(
                            f"[taptap_enhanced] possible_antiscrape page_title={page.title()!r}",
                            file=sys.stderr,
                        )
                        sys.stderr.flush()
                except Exception:
                    pass
                # 关闭弹窗
                self._close_popups(page)

                for scroll in range(max_scrolls):
                    _maybe_heartbeat(
                        last_heartbeat, "post_list", app_id=self.app_id, scroll=scroll + 1,
                        max_scrolls=max_scrolls, posts=len(posts), limit=limit,
                    )
                    new_posts = self._extract_posts_from_page(page)
                    prev_len = len(posts)
                    for post in new_posts:
                        if post["id"] not in [p["id"] for p in posts]:
                            posts.append(post)
                    if len(posts) > prev_len:
                        scrolls_without_new = 0
                    else:
                        scrolls_without_new += 1
                    print(
                        f"[taptap_enhanced] post_list scroll={scroll+1} new_this_page={len(new_posts)} posts={len(posts)}",
                        file=sys.stderr,
                    )
                    sys.stderr.flush()
                    if scrolls_without_new >= 2:
                        print(
                            f"[taptap_enhanced] possible_stuck_or_antiscrape scroll={scroll+1} posts={len(posts)} scrolls_without_new={scrolls_without_new}",
                            file=sys.stderr,
                        )
                        sys.stderr.flush()

                    if len(posts) >= limit:
                        break

                    # 按 days_back 停止：若已出现 >= days_back 天的帖子，说明已覆盖完整时间范围
                    max_days_ago: Optional[float] = None
                    for p in posts:
                        d = parse_days_ago(p.get("created_at") or "")
                        if d is not None and (max_days_ago is None or d > max_days_ago):
                            max_days_ago = d
                    if max_days_ago is not None and max_days_ago >= days_back:
                        break

                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                    self._click_load_more(page)

                _heartbeat("post_list_done", posts=len(posts), limit=limit)
                browser.close()

            except Exception as e:
                print(f"[Error] Failed to fetch post list: {e}", file=sys.stderr)
                browser.close()
        
        # 只保留时间在 [0, days_back) 内的帖子（未解析出日期的保留）
        within_window: List[Dict] = []
        for p in posts:
            d = parse_days_ago(p.get("created_at") or "")
            if d is None:
                within_window.append(p)
            elif d < days_back:
                within_window.append(p)
        
        return within_window[:limit]
    
    def fetch_post_detail(self, post_url: str, post_id: str) -> Dict:
        """采集单个帖子的完整内容（包括评论树）"""
        
        result = {
            "post_id": post_id,
            "url": post_url,
            "title": "",
            "content": "",
            "author": "",
            "created_at": "",
            "likes": 0,
            "comments": [],
            "comment_count": 0,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            
            try:
                page.goto(post_url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)
                # Anti-scraping: check page title on detail page
                try:
                    title = (page.title() or "").lower()
                    if any(kw in title for kw in ("验证", "captcha", "人机", "verify", "安全")):
                        print(
                            f"[taptap_enhanced] possible_antiscrape detail page_title={page.title()!r} post_id={post_id}",
                            file=sys.stderr,
                        )
                        sys.stderr.flush()
                except Exception:
                    pass
                # 关闭弹窗
                self._close_popups(page)

                # 提取帖子基本信息
                result.update(self._extract_post_info(page))
                
                # 加载并提取所有评论
                result["comments"] = self._extract_all_comments(page)
                result["comment_count"] = len(result["comments"]) + sum(
                    len(c.get("replies") or []) for c in result["comments"]
                )
                # 为每条评论添加首次入库时间（供增量追加与审计）
                self._set_recorded_at_on_comments(result["comments"], datetime.now(timezone.utc).isoformat())
                
                browser.close()
                
            except Exception as e:
                print(f"[Error] Failed to fetch post detail {post_id}: {e}", file=sys.stderr)
                browser.close()
        
        return result
    
    def _extract_posts_from_page(self, page: Page) -> List[Dict]:
        """从页面提取帖子列表"""
        posts = []
        
        # 尝试多种选择器
        selectors = [
            '[class*="feed"] > div',
            '[class*="card"]',
            '[class*="moment-item"]',
            'a[href*="/moment/"]'
        ]
        
        for selector in selectors:
            elements = page.query_selector_all(selector)
            
            for el in elements:
                try:
                    post = self._parse_post_element(el)
                    if post and post.get('id'):
                        posts.append(post)
                except:
                    continue
        
        return posts
    
    def _parse_post_element(self, element) -> Optional[Dict]:
        """解析单个帖子元素"""
        try:
            # 获取链接
            link_el = element.query_selector('a[href*="/moment/"]')
            if not link_el:
                return None
            
            href = link_el.get_attribute('href')
            if not href:
                return None
            
            post_id = href.split('/moment/')[-1].split('?')[0]
            url = urljoin(self.BASE_URL, href)
            
            # 获取标题/内容
            title_el = element.query_selector('[class*="title"], [class*="content"]')
            title = title_el.inner_text()[:200] if title_el else ""
            
            # 获取作者
            author_el = element.query_selector('[class*="user"], [class*="author"]')
            author = author_el.inner_text()[:50] if author_el else ""
            
            # 获取时间
            time_el = element.query_selector('[class*="time"], [class*="date"]')
            created_at = time_el.inner_text() if time_el else ""
            
            # 获取互动数
            likes = 0
            like_el = element.query_selector('[class*="like"], [class*="agree"]')
            if like_el:
                like_text = like_el.inner_text()
                try:
                    likes = int(''.join(filter(str.isdigit, like_text)))
                except:
                    pass
            
            return {
                "id": post_id,
                "title": title,
                "author": author,
                "url": url,
                "created_at": created_at,
                "likes": likes
            }
            
        except Exception as e:
            return None
    
    def _extract_post_info(self, page: Page) -> Dict:
        """提取帖子详细信息（使用 TapTap moment 页选择器）"""
        info = {}
        try:
            # 标题
            title_el = page.query_selector(sel.POST_TITLE)
            if not title_el:
                title_el = page.query_selector("h1, [class*='title']")
            info["title"] = title_el.inner_text()[:200].strip() if title_el else ""

            # 内容
            content_el = page.query_selector(sel.POST_CONTENT)
            if not content_el:
                content_el = page.query_selector(sel.POST_CONTENT_FALLBACK)
            if not content_el:
                content_el = page.query_selector("[class*='content'], [class*='body'], article")
            info["content"] = content_el.inner_text()[:2000].strip() if content_el else ""

            # 作者（发布者）
            author_el = page.query_selector(sel.POST_AUTHOR)
            if not author_el:
                author_el = page.query_selector(sel.POST_AUTHOR_FALLBACK)
            if not author_el:
                author_el = page.query_selector("[class*='author'], [class*='user-name']")
            info["author"] = author_el.inner_text()[:50].strip() if author_el else ""

            # 发布日期（优先取 title 属性完整时间）
            date_el = page.query_selector(sel.POST_DATE)
            if not date_el:
                date_el = page.query_selector(sel.POST_DATE_FALLBACK)
            if date_el:
                info["created_at"] = (date_el.get_attribute("title") or date_el.inner_text()).strip()
            else:
                time_el = page.query_selector("[class*='time'], [class*='date']")
                info["created_at"] = time_el.inner_text().strip() if time_el else ""

            # 点赞数
            likes_el = page.query_selector("[class*='like-count'], [class*='agree-count']")
            if likes_el:
                try:
                    info["likes"] = int("".join(filter(str.isdigit, likes_el.inner_text())))
                except Exception:
                    info["likes"] = 0
        except Exception as e:
            print(f"[Warning] Error extracting post info: {e}", file=sys.stderr)
        return info
    
    def _extract_all_comments(self, page: Page) -> List[Dict]:
        """提取所有评论（包括嵌套回复），使用 TapTap moment 页选择器"""
        comments: List[Dict] = []
        try:
            page.wait_for_timeout(3000)
            # 等待评论区出现（懒加载或 SPA），任一选择器出现即继续
            comment_list_selectors = [
                sel.COMMENT_LIST,
                "[class*='moment-comment']",
                "[class*='tap-list']",
                "[class*='comment-list']",
            ]
            for i, comment_list_sel in enumerate(comment_list_selectors):
                try:
                    page.wait_for_selector(comment_list_sel, timeout=12000 if i == 0 else 5000)
                    break
                except Exception:
                    continue
            page.wait_for_timeout(2000)
            self._load_all_comments(page)
            # 优先用 moment-post 选择器，再试 fallback
            comments = self._extract_comments_moment_page(page)
            if not comments:
                comments = self._extract_comments_via_js(page)
            if not comments:
                for selector in [
                    sel.COMMENT_ITEM,
                    "[class*='moment-post']",
                    "[class*='comment-item']",
                    "[class*='comment']",
                ]:
                    try:
                        comment_els = page.query_selector_all(selector)
                        for el in comment_els:
                            comment = self._parse_comment_element(el)
                            if comment and comment.get("text"):
                                comments.append(comment)
                        if comments:
                            break
                    except Exception:
                        continue
            if not comments:
                print("[Debug] Comment extraction returned 0 items; selectors may not match current TapTap DOM.", file=sys.stderr)
            # #region agent log
            total_replies = sum(len(c.get("replies") or []) for c in comments)
            _debug_log("taptap_enhanced.py:_extract_all_comments", "comment counts", {"top_level": len(comments), "replies": total_replies, "total_all": len(comments) + total_replies}, "H1")
            # #endregion
        except Exception as e:
            print(f"[Warning] Error extracting comments: {e}", file=sys.stderr)
        return comments

    def _extract_comments_moment_page(self, page: Page) -> List[Dict]:
        """使用 moment-post 选择器提取评论；回复在弹窗内，需逐条点击「查看更多回复」后解析弹窗"""
        out: List[Dict] = []
        list_selectors = [
            sel.COMMENT_LIST,
            "[class*='moment-comment-list']",
            "[class*='tap-list']",
        ]
        item_selectors = [sel.COMMENT_ITEM, "[class*='moment-post']"]
        for list_sel in list_selectors:
            list_el = page.query_selector(list_sel)
            if not list_el:
                continue
            for item_sel in item_selectors:
                try:
                    items = list_el.query_selector_all(item_sel)
                    for idx, el in enumerate(items):
                        comment = self._parse_moment_comment(el, idx)
                        if not comment:
                            continue
                        # 回复在弹窗中：点击该条评论的「查看更多回复」→ 解析弹窗 → 关闭
                        replies_from_modal = self._open_modal_and_parse_replies(page, el, idx)
                        if replies_from_modal:
                            comment["replies"] = replies_from_modal
                        if comment.get("text") or comment.get("replies"):
                            out.append(comment)
                    if out:
                        return out
                except Exception as e:
                    print(f"[Debug] _extract_comments_moment_page: {e}", file=sys.stderr)
        return out

    def _open_modal_and_parse_replies(self, page: Page, comment_element, comment_index: int) -> List[Dict]:
        """点击该条评论的「查看更多回复」，等弹窗出现后解析弹窗内回复并关闭弹窗。"""
        replies: List[Dict] = []
        try:
            btn = (
                comment_element.query_selector(sel.LOAD_MORE_REPLIES)
                or comment_element.query_selector("[class*='comment-more']")
            )
            if not btn or not btn.is_visible():
                return replies
            btn.click()
            page.wait_for_selector(sel.REPLY_MODAL, timeout=6000)
            page.wait_for_timeout(800)
            reply_els = page.query_selector_all(sel.REPLY_MODAL_ITEM)
            for i, r_el in enumerate(reply_els):
                r = self._parse_reply_from_modal_item(r_el, comment_index, i)
                if r:
                    replies.append(r)
        except Exception as e:
            print(f"[Debug] _open_modal_and_parse_replies: {e}", file=sys.stderr)
        finally:
            self._close_reply_modal(page)
        return replies

    def _parse_reply_from_modal_item(self, element, comment_index: int, reply_index: int) -> Optional[Dict]:
        """解析弹窗内单条回复（作者、内容、点赞）。"""
        try:
            author_el = element.query_selector(sel.REPLY_AUTHOR) or element.query_selector(".moment-post__user-name a")
            author = author_el.inner_text().strip()[:50] if author_el else ""
            content_el = element.query_selector(sel.REPLY_CONTENT) or element.query_selector(".moment-post__content-wrapper div")
            text = content_el.inner_text().strip()[:1000] if content_el else ""
            like_el = element.query_selector(sel.COMMENT_LIKES) or element.query_selector(".vote-button__button-text")
            likes = 0
            if like_el:
                try:
                    likes = int("".join(filter(str.isdigit, like_el.inner_text())))
                except Exception:
                    pass
            if not text and not author:
                return None
            return {"id": f"reply_{comment_index}_{reply_index}", "author": author, "text": text, "timestamp": "", "likes": likes}
        except Exception:
            return None

    def _close_reply_modal(self, page: Page) -> None:
        """关闭回复弹窗（点击遮罩或关闭按钮）。"""
        try:
            overlay = page.query_selector(sel.REPLY_MODAL_CLOSE)
            if overlay:
                overlay.click()
            page.wait_for_timeout(400)
        except Exception:
            pass

    def _parse_moment_comment(self, element, index: int) -> Optional[Dict]:
        """解析单条 moment-post（含回复）；主选择器失败时用元素内 fallback"""
        try:
            author_el = element.query_selector(sel.COMMENT_AUTHOR) or element.query_selector("[class*='user-name'] a") or element.query_selector("[class*='author']")
            author = author_el.inner_text().strip()[:50] if author_el else ""
            content_el = element.query_selector(sel.COMMENT_CONTENT) or element.query_selector("[class*='content-wrapper'] div") or element.query_selector("[class*='content']")
            text = content_el.inner_text().strip()[:1000] if content_el else ""
            date_els = element.query_selector_all(sel.COMMENT_DATE)
            if not date_els:
                date_els = element.query_selector_all("[class*='footer'] span, [class*='time']")
            timestamp = date_els[-1].inner_text().strip() if date_els else ""
            like_el = element.query_selector(sel.COMMENT_LIKES) or element.query_selector("[class*='vote']") or element.query_selector("[class*='like']")
            likes = 0
            if like_el:
                try:
                    likes = int("".join(filter(str.isdigit, like_el.inner_text())))
                except Exception:
                    pass
            replies = []
            # 多种回复容器/子项选择器（当前页 DOM 可能与 taptap_selectors 不一致）
            reply_container = (
                element.query_selector(sel.REPLY_CONTAINER)
                or element.query_selector("[class*='comments']")
                or element.query_selector("[class*='moment-post-item']")
                or element.query_selector("[class*='reply']")
                or element.query_selector("[class*='replies']")
                or element.query_selector("[class*='child']")
            )
            if reply_container:
                reply_items = (
                    reply_container.query_selector_all(sel.REPLY_ITEM)
                    or reply_container.query_selector_all("[class*='body--child']")
                    or reply_container.query_selector_all("[class*='moment-post']")
                    or reply_container.query_selector_all("[class*='child']")
                    or reply_container.query_selector_all("div[class*='post']")
                )
            else:
                # 无单独容器时：在当前评论元素内找所有“像回复”的块
                reply_items = element.query_selector_all(
                    "[class*='moment-post__body--child'], [class*='moment-post'][class*='child'], "
                    "[class*='reply'] div[class*='content'], [class*='replies'] > div"
                )
            for r_el in reply_items:
                reply = self._parse_moment_reply(r_el)
                if reply:
                    replies.append(reply)
            if not replies:
                # 选择器均无结果时用 JS 从当前评论节点内摘出“作者+内容”的回复块
                js_replies = self._extract_replies_via_js(element)
                for r in js_replies:
                    replies.append(r)
            # #region agent log
            if index < 3:
                _debug_log("taptap_enhanced.py:_parse_moment_comment", "reply extraction", {"comment_index": index, "reply_container_found": reply_container is not None, "reply_items_count": len(reply_items) if reply_container else len(reply_items), "replies_parsed": len(replies)}, "H2")
            # #endregion
            if not text and not replies:
                return None
            return {
                "id": f"comment_{index}",
                "author": author,
                "text": text,
                "timestamp": timestamp,
                "likes": likes,
                "replies": replies,
            }
        except Exception as e:
            print(f"[Debug] _parse_moment_comment: {e}", file=sys.stderr)
            return None

    def _extract_replies_via_js(self, comment_element) -> List[Dict]:
        """当选择器无法匹配时，用 JS 在评论元素内查找“作者+内容”的回复块"""
        out: List[Dict] = []
        try:
            raw = comment_element.evaluate("""(el) => {
                const items = [];
                const candidates = el.querySelectorAll('[class*="child"], [class*="reply"], [class*="replies"] [class*="content"]');
                for (const c of candidates) {
                    const text = (c.innerText || '').trim();
                    const lines = text.split('\\n').filter(l => l.trim());
                    if (lines.length < 2 || text.length > 1500) continue;
                    const author = lines[0].trim().slice(0, 80);
                    const content = lines.slice(1).join(' ').trim().slice(0, 1000);
                    if (content.length < 2) continue;
                    if (/^(回复|查看更多|\\d+.*前)$/.test(author)) continue;
                    items.push({ author, text: content });
                }
                return items;
            }""")
            for i, r in enumerate(raw or []):
                out.append({"id": f"reply_{i}", "author": r.get("author", ""), "text": r.get("text", ""), "timestamp": ""})
        except Exception:
            pass
        return out

    def _parse_moment_reply(self, element) -> Optional[Dict]:
        """解析评论下的单条回复"""
        try:
            author_el = element.query_selector(sel.REPLY_AUTHOR) or element.query_selector("[class*='user-name'] a")
            author = author_el.inner_text().strip()[:50] if author_el else ""
            content_el = element.query_selector(sel.REPLY_CONTENT) or element.query_selector("[class*='content']")
            text = content_el.inner_text().strip()[:1000] if content_el else ""
            if not text and not author:
                return None
            return {"author": author, "text": text, "timestamp": ""}
        except Exception:
            return None
    
    # UI 文案黑名单：不计入真实评论
    _COMMENT_UI_BLACKLIST = frozenset({
        "评论", "只看作者", "最热", "回复", "分享", "举报", "删除", "心动小镇", "首页",
        "加载更多", "查看更多", "已经到底了", "赞", "点赞",
    })

    def _extract_comments_via_js(self, page: Page) -> List[Dict]:
        """通过 JavaScript 按文本特征提取评论（选择器不可用时的兜底）"""
        try:
            js_result = page.evaluate("""() => {
                const comments = [];
                const uiBlacklist = new Set([
                    '评论', '只看作者', '最热', '回复', '分享', '举报', '删除',
                    '心动小镇', '首页', '加载更多', '查看更多', '已经到底了', '赞', '点赞'
                ]);
                const possibleContainers = document.querySelectorAll('div, article, section');
                for (const container of possibleContainers) {
                    if (container.offsetHeight < 40) continue;
                    const text = container.innerText || '';
                    const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
                    const hasTime = /\\d+\\s*(分钟|小时|天)前|刚刚/.test(text);
                    const hasLike = /\\d+\\s*(赞|likes?|agree)/i.test(text);
                    const contentLines = lines.filter(l => l.length > 15 && l.length < 2000)
                        .filter(l => !/\\d+\\s*(分钟|小时|天)前|刚刚/.test(l))
                        .filter(l => !/\\d+\\s*(赞|likes?|agree)/i.test(l))
                        .filter(l => !uiBlacklist.has(l));
                    if ((hasTime || hasLike) && contentLines.length > 0) {
                        const contentLine = contentLines[contentLines.length - 1];
                        const authorLine = lines.find(l => l.length > 0 && l.length < 40 && !uiBlacklist.has(l)) || '';
                        const timeMatch = text.match(/(\\d+\\s*(分钟|小时|天)前|刚刚)/);
                        const likeMatch = text.match(/(\\d+)\\s*(赞|likes?|agree)/i);
                        comments.push({
                            text: contentLine,
                            author: authorLine,
                            time: timeMatch ? timeMatch[1] : '',
                            likes: likeMatch ? parseInt(likeMatch[1]) : 0
                        });
                    }
                }
                const seen = new Set();
                return comments.filter(c => {
                    if (seen.has(c.text) || c.text.length < 2) return false;
                    seen.add(c.text);
                    return true;
                }).slice(0, 500);
            }""")
            # 再过滤一次 UI 文案（与 _COMMENT_UI_BLACKLIST 一致）
            filtered = [
                c for c in js_result
                if (c.get("text") or "").strip()
                and (c.get("text") or "").strip() not in self._COMMENT_UI_BLACKLIST
                and len((c.get("text") or "").strip()) > 2
            ]
            print(f"[Debug] JS extraction found {len(filtered)} comments (raw {len(js_result)})", file=sys.stderr)
            return [{"id": f"comment_{i}", **c, "replies": []} for i, c in enumerate(filtered)]
        except Exception as e:
            print(f"[Warning] JS extraction failed: {e}", file=sys.stderr)
            return []
    
    def _load_all_comments(self, page: Page):
        """滚动加载所有评论；点击「查看更多回复」；遇「已经到底了」停止。输出诊断日志供 agent 判断分页/嵌套是否卡住。"""
        max_attempts = 20
        no_progress_attempts = 0
        prev_clicked_total = 0
        for attempt in range(max_attempts):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
            # 检查是否已到底（TapTap 文案）
            end_el = page.query_selector(sel.COMMENT_LIST_END)
            if end_el and sel.COMMENT_LIST_END_TEXT in (end_el.inner_text() or ""):
                print(
                    f"[taptap_enhanced] comments reached end marker at attempt={attempt+1}",
                    file=sys.stderr,
                )
                sys.stderr.flush()
                break
            # 点击主评论区「加载更多」
            for selector in [
                "button:has-text('加载更多')",
                "button:has-text('查看更多')",
                "[class*='load-more']",
            ]:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue
            # 点击每条评论下的「查看更多回复」；多轮重查并点击直到无新按钮（展开后 DOM 会变）
            more_btns = []
            clicked = 0
            try:
                for _ in range(3):
                    more_btns = page.query_selector_all(sel.LOAD_MORE_REPLIES)
                    if not more_btns:
                        more_btns = page.query_selector_all("[class*='comment-more']")
                    n = 0
                    for btn in more_btns:
                        try:
                            if btn.is_visible():
                                btn.click()
                                n += 1
                                page.wait_for_timeout(600)
                        except Exception:
                            pass
                    clicked += n
                    if n == 0:
                        break
                if clicked > 0:
                    page.wait_for_timeout(1500)
            except Exception:
                pass
            print(
                f"[taptap_enhanced] comments load_more attempt={attempt+1} num_buttons={len(more_btns)} clicked={clicked}",
                file=sys.stderr,
            )
            sys.stderr.flush()
            if clicked > prev_clicked_total:
                prev_clicked_total = clicked
                no_progress_attempts = 0
            else:
                no_progress_attempts += 1
            if no_progress_attempts >= 3:
                print(
                    f"[taptap_enhanced] possible_stuck no new reply buttons for 3 attempts (nested comments) attempt={attempt+1}",
                    file=sys.stderr,
                )
                sys.stderr.flush()
                break
            # #region agent log
            if attempt < 3:
                _debug_log("taptap_enhanced.py:_load_all_comments", "load more replies", {"attempt": attempt, "num_buttons": len(more_btns), "clicked": clicked}, "H3")
            # #endregion
            page.wait_for_timeout(1000)
    
    def _parse_comment_element(self, element) -> Optional[Dict]:
        """解析单个评论元素"""
        try:
            # 使用JavaScript获取内容（更可靠）
            comment_data = element.evaluate("""(el) => {
                // 尝试多种可能的选择器
                const authorSelectors = ['.user-name', '.author', '.nickname', '[class*="user"]', '[class*="author"]'];
                const contentSelectors = ['.content', '.text', '[class*="content"]', '[class*="text"]', 'p'];
                const timeSelectors = ['.time', '[class*="time"]', '[class*="date"]'];
                const likeSelectors = ['.like-count', '.agree-count', '[class*="like"]', '[class*="agree"]'];
                
                let author = '';
                let content = '';
                let timestamp = '';
                let likes = 0;
                
                // 提取作者
                for (const sel of authorSelectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        author = el.innerText.trim();
                        break;
                    }
                }
                
                // 提取内容
                for (const sel of contentSelectors) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText.trim().length > 2) {
                        content = el.innerText.trim();
                        break;
                    }
                }
                
                // 提取时间
                for (const sel of timeSelectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        timestamp = el.innerText.trim();
                        break;
                    }
                }
                
                // 提取点赞数
                for (const sel of likeSelectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        const match = el.innerText.match(/\\d+/);
                        if (match) {
                            likes = parseInt(match[0]);
                            break;
                        }
                    }
                }
                
                return { author, content, timestamp, likes };
            }""")
            
            if not comment_data or not comment_data.get('content'):
                return None
            
            # 跳过太短的（可能是UI元素）
            if len(comment_data['content']) < 3:
                return None
            
            # 提取回复
            replies = []
            try:
                reply_container = element.query_selector('[class*="reply"], [class*="children"], [class*="replies"]')
                if reply_container:
                    reply_els = reply_container.query_selector_all(':scope > div, :scope > [class*="item"]')
                    for reply_el in reply_els:
                        reply = self._parse_comment_element(reply_el)
                        if reply:
                            reply['parent_id'] = element.get_attribute('data-id') or ""
                            replies.append(reply)
            except:
                pass
            
            return {
                "id": element.get_attribute('data-id') or f"comment_{hash(comment_data['content']) % 100000}",
                "author": comment_data['author'][:50],
                "text": comment_data['content'][:1000],
                "timestamp": comment_data['timestamp'],
                "likes": comment_data['likes'],
                "replies": replies
            }
            
        except Exception as e:
            print(f"[Debug] Parse comment error: {e}", file=sys.stderr)
            return None
    
    def _close_popups(self, page: Page):
        """关闭弹窗"""
        try:
            close_selectors = [
                'button:has-text("关闭")',
                'button:has-text("知道了")',
                '.close',
                '[class*="close"]'
            ]
            for selector in close_selectors:
                btn = page.query_selector(selector)
                if btn:
                    btn.click()
                    page.wait_for_timeout(500)
                    break
        except:
            pass
    
    def _click_load_more(self, page: Page):
        """点击加载更多"""
        try:
            selectors = [
                'button:has-text("加载更多")',
                'button:has-text("查看更多")'
            ]
            for selector in selectors:
                btn = page.query_selector(selector)
                if btn and btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(2000)
                    break
        except:
            pass
    
    def run_full_crawl(self, days_back: int = 365, post_limit: int = 500, topic_type: str = "official"):
        """运行完整采集。topic_type='official' 仅采官方帖列表."""
        last_heartbeat: list = [0.0]
        print(f"[Full Crawl] Starting full crawl for app_id={self.app_id}, topic_type={topic_type or 'all'}")
        print(f"[Full Crawl] Days back: {days_back}, Post limit: {post_limit}")
        _heartbeat("full_crawl_start", app_id=self.app_id, days_back=days_back, post_limit=post_limit)
        print("[Full Crawl] Step 1: Fetching post list...")
        posts = self.fetch_post_list(limit=post_limit, days_back=days_back, topic_type=topic_type or "")
        print(f"[Full Crawl] Found {len(posts)} posts")
        _heartbeat("full_crawl_post_list_done", posts=len(posts))

        # 2. 采集每个帖子的详情
        print("[Full Crawl] Step 2: Fetching post details...")
        detailed_posts = []
        total_posts = len(posts)

        for i, post in enumerate(posts):
            _maybe_heartbeat(
                last_heartbeat, "full_crawl", app_id=self.app_id, post_index=i + 1,
                total_posts=total_posts, posts_done=len(detailed_posts),
            )
            print(f"[Full Crawl] [{i+1}/{len(posts)}] Fetching: {post.get('title', '')[:50]}...")
            sys.stderr.flush()

            detail = self.fetch_post_detail(post['url'], post['id'])
            detail.update(post)  # 合并基本信息
            detailed_posts.append(detail)

            # 保存中间结果
            if (i + 1) % 10 == 0:
                self._save_checkpoint(detailed_posts, i + 1)

            # 延迟避免被封
            time.sleep(2)
        
        # 3. 为所有评论设置首次入库时间
        crawled_at = datetime.now(timezone.utc).isoformat()
        for p in detailed_posts:
            self._set_recorded_at_on_comments(p.get("comments") or [], crawled_at)
        # 4. 保存最终结果
        final_result = {
            "source": "taptap",
            "app_id": self.app_id,
            "crawl_type": "full",
            "crawled_at": crawled_at,
            "total_posts": len(detailed_posts),
            "total_comments": sum(p.get("comment_count", 0) for p in detailed_posts),
            "posts": detailed_posts,
        }
        output_file = self.output_dir / f"full_crawl_{self.app_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        print(f"[Full Crawl] Complete! Saved to {output_file}")
        print(f"[Full Crawl] Total posts: {len(detailed_posts)}")
        print(f"[Full Crawl] Total comments: {final_result['total_comments']}")
        
        return final_result
    
    def _save_checkpoint(self, posts: List[Dict], count: int):
        """保存检查点"""
        checkpoint_file = self.output_dir / f"checkpoint_{self.app_id}_{count}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"[Checkpoint] Saved {count} posts to {checkpoint_file}")

    @staticmethod
    def _set_recorded_at_on_comments(comments: List[Dict], recorded_at: str) -> None:
        """为评论及回复设置 recorded_at（若尚未设置），表示首次写入我们数据的时间。"""
        for c in comments:
            if c.get("recorded_at") is None:
                c["recorded_at"] = recorded_at
            replies = c.get("replies") or []
            for r in replies:
                if isinstance(r, dict) and r.get("recorded_at") is None:
                    r["recorded_at"] = recorded_at
            if replies:
                TapTapEnhancedCrawler._set_recorded_at_on_comments(replies, recorded_at)

    @staticmethod
    def _comment_signature(c: Dict) -> str:
        """用于去重的评论特征（同一条评论多次抓取只保留一条，并保留首次 recorded_at）。"""
        text = (c.get("text") or "")[:500]
        author = (c.get("author") or "")[:100]
        ts = (c.get("timestamp") or "")[:50]
        return f"{author}|{ts}|{text}"

    def run_incremental_append(
        self,
        days_back: int = 1,
        post_limit: int = 300,
        topic_type: str = "official",
        state_file: Optional[Path] = None,
    ) -> Dict:
        """
        增量追加：拉取近期帖子与评论，与已有数据合并，新评论带 recorded_at。
        适合定时（如每小时）执行，将新评论持续写入同一 state_file。
        """
        state_path = state_file or (self.output_dir / f"incremental_state_{self.app_id}.json")
        state_path = Path(state_path)
        recorded_at = datetime.now(timezone.utc).isoformat()

        # 加载已有状态
        existing_by_id: Dict[str, Dict] = {}
        if state_path.exists():
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for p in (data.get("posts") or []):
                    pid = p.get("post_id") or p.get("id")
                    if pid:
                        existing_by_id[pid] = p
                print(f"[Incremental] Loaded {len(existing_by_id)} existing posts from {state_path}")
            except Exception as e:
                print(f"[Warning] Could not load state {state_path}: {e}", file=sys.stderr)

        # 拉取近期帖子列表
        print(f"[Incremental] Fetching recent list (days_back={days_back}, limit={post_limit})...")
        posts = self.fetch_post_list(limit=post_limit, days_back=days_back, topic_type=topic_type or "official")
        print(f"[Incremental] Found {len(posts)} posts in window")

        # 对每个帖子拉详情并合并评论
        merged_posts: List[Dict] = []
        seen_post_ids = set()
        for i, post in enumerate(posts):
            pid = post.get("id")
            if not pid:
                continue
            print(f"[Incremental] [{i+1}/{len(posts)}] Post {pid}...")
            detail = self.fetch_post_detail(post["url"], pid)
            detail.update(post)

            existing = existing_by_id.get(pid)
            if existing:
                existing_sigs = set()
                for c in (existing.get("comments") or []):
                    existing_sigs.add(self._comment_signature(c))
                    for r in (c.get("replies") or []):
                        if isinstance(r, dict):
                            existing_sigs.add(self._comment_signature(r))
                new_comments = []
                for c in (detail.get("comments") or []):
                    sig = self._comment_signature(c)
                    if sig not in existing_sigs:
                        if c.get("recorded_at") is None:
                            c["recorded_at"] = recorded_at
                        new_comments.append(c)
                        existing_sigs.add(sig)
                    for r in (c.get("replies") or []):
                        if isinstance(r, dict):
                            sr = self._comment_signature(r)
                            if sr not in existing_sigs:
                                if r.get("recorded_at") is None:
                                    r["recorded_at"] = recorded_at
                                existing_sigs.add(sr)
                existing_comments = existing.get("comments") or []
                detail["comments"] = existing_comments + new_comments
                detail["comment_count"] = len(detail["comments"]) + sum(
                    len(c.get("replies") or []) for c in (detail.get("comments") or [])
                )
                if new_comments:
                    print(f"[Incremental]   +{len(new_comments)} new comments")
            else:
                self._set_recorded_at_on_comments(detail.get("comments") or [], recorded_at)

            merged_posts.append(detail)
            seen_post_ids.add(pid)
            time.sleep(2)

        # 保留未在本次窗口内的旧帖子（避免丢失历史）
        for pid, p in existing_by_id.items():
            if pid not in seen_post_ids:
                merged_posts.append(p)

        final = {
            "source": "taptap",
            "app_id": self.app_id,
            "crawl_type": "incremental",
            "crawled_at": recorded_at,
            "total_posts": len(merged_posts),
            "total_comments": sum((p.get("comment_count") or len(p.get("comments") or [])) for p in merged_posts),
            "posts": merged_posts,
        }
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(final, f, ensure_ascii=False, indent=2)
        snapshot_path = self.output_dir / f"incremental_{self.app_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(final, f, ensure_ascii=False, indent=2)
        print(f"[Incremental] Saved state to {state_path}, snapshot to {snapshot_path}")
        print(f"[Incremental] Total posts: {len(merged_posts)}, total comments: {final['total_comments']}")
        return final


def main():
    parser = argparse.ArgumentParser(description="TapTap Enhanced Crawler")
    parser.add_argument("--app-id", required=True, help="TapTap app ID")
    parser.add_argument(
        "--mode",
        choices=["full", "list", "detail", "incremental"],
        default="full",
        help="full=list+details; list=posts only; detail=single post; incremental=append new comments to state file",
    )
    parser.add_argument("--topic-type", default="official",
                        help="Topic filter for list: 'official' (default) or '' for all")
    parser.add_argument("--days", type=int, default=365, help="Days back to crawl (incremental default 1)")
    parser.add_argument("--limit", type=int, default=9999, help="Max posts to fetch (default 9999 for 'all')")
    parser.add_argument("--output-dir", default="./taptap_data", help="Output directory")
    parser.add_argument("--post-url", help="Single post URL (for detail mode)")
    parser.add_argument("--state-file", help="For incremental: path to JSON state (default: output_dir/incremental_state_<app_id>.json)")
    args = parser.parse_args()

    crawler = TapTapEnhancedCrawler(args.app_id, args.output_dir)
    state_file = Path(args.state_file) if args.state_file else None

    if args.mode == "full":
        result = crawler.run_full_crawl(
            days_back=args.days, post_limit=args.limit,
            topic_type=(args.topic_type or "").strip() or "official",
        )
    elif args.mode == "incremental":
        days = args.days if args.days != 365 else 1
        result = crawler.run_incremental_append(
            days_back=days,
            post_limit=args.limit,
            topic_type=(args.topic_type or "").strip() or "official",
            state_file=state_file,
        )
    elif args.mode == "list":
        posts = crawler.fetch_post_list(
            limit=args.limit, days_back=args.days,
            topic_type=(args.topic_type or "").strip() or "official",
        )
        result = {
            "source": "taptap",
            "app_id": args.app_id,
            "crawl_type": "list",
            "post_count": len(posts),
            "posts": posts
        }
        output_file = Path(args.output_dir) / f"post_list_{args.app_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(posts)} posts to {output_file}")
    elif args.mode == "detail" and args.post_url:
        post_id = args.post_url.split('/moment/')[-1].split('?')[0]
        result = crawler.fetch_post_detail(args.post_url, post_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.error("--post-url required for detail mode")


if __name__ == "__main__":
    main()
