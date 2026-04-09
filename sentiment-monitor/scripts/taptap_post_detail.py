#!/usr/bin/env python3
"""
TapTap post detail extractor with full comments.

Fetches a specific TapTap post and all its comments including nested replies.

Output conforms to the sentiment_monitor CIE schema:
  { source, game_id, post_id, data_type, fetched_at, locale,
    post: { id, title, body, author, url, created_at, score, tags },
    comments: [ { id, author, text, timestamp, likes, parent_id, replies: [...] } ] }

Usage:
    python taptap_post_detail.py --post-url https://www.taptap.cn/moment/xxxx --output out.json
    python taptap_post_detail.py --post-id 781072728173052756 --app-id 45213 --output out.json
"""
import argparse
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
import taptap_selectors as sel

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print(json.dumps({"status": "error", "reason": "Playwright not installed"}), file=sys.stderr)
    sys.exit(1)

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def extract_post_id_from_url(url: str) -> str:
    """Extract post ID from TapTap URL."""
    # URL format: https://www.taptap.cn/moment/781072728173052756
    match = re.search(r'/moment/(\d+)', url)
    if match:
        return match.group(1)
    return ""


def parse_comment_element(comment_el, depth: int = 0) -> dict | None:
    """Parse a single comment element (generic fallback). Prefer moment-page selectors in fetch_post_detail."""
    try:
        text_el = comment_el.query_selector(sel.COMMENT_CONTENT)
        if not text_el:
            text_el = comment_el.query_selector("[class*='content'], [class*='text'], .content, .text")
        if not text_el:
            text_el = comment_el
        text = text_el.inner_text().strip()
        if len(text) < 2:
            return None
        author_el = comment_el.query_selector(sel.COMMENT_AUTHOR)
        if not author_el:
            author_el = comment_el.query_selector("[class*='user'], [class*='author'], [class*='nickname'], .user-name")
        author = author_el.inner_text().strip() if author_el else ""
        time_el = comment_el.query_selector(sel.COMMENT_DATE)
        if not time_el:
            time_el = comment_el.query_selector("[class*='time'], [class*='date'], time")
        timestamp = ""
        if time_el:
            timestamp = time_el.inner_text().strip() if hasattr(time_el, "inner_text") else ""
            if hasattr(time_el, "get_attribute") and time_el.get_attribute("datetime"):
                timestamp = time_el.get_attribute("datetime") or timestamp
        like_el = comment_el.query_selector(sel.COMMENT_LIKES)
        if not like_el:
            like_el = comment_el.query_selector("[class*='like'], [class*='upvote'], [class*='agree']")
        likes = 0
        if like_el:
            num_match = re.search(r"(\d+)", like_el.inner_text())
            if num_match:
                likes = int(num_match.group(1))
        comment_id = comment_el.get_attribute("data-id") or comment_el.get_attribute("id") or ""
        replies = []
        if depth < 3:
            reply_container = comment_el.query_selector(sel.REPLY_CONTAINER)
            if not reply_container:
                reply_container = comment_el.query_selector("[class*='reply'], [class*='children'], [class*='sub-comments']")
            if reply_container:
                reply_els = reply_container.query_selector_all(sel.REPLY_ITEM)
                if not reply_els:
                    reply_els = reply_container.query_selector_all(":scope > [class*='comment'], :scope > [class*='item']")
                for reply_el in reply_els:
                    reply = parse_comment_element(reply_el, depth + 1)
                    if reply:
                        reply["parent_id"] = comment_id
                        replies.append(reply)
        return {
            "id": comment_id or f"comment_{hash(text) % 100000}",
            "author": author[:50],
            "text": text[:1000],
            "timestamp": timestamp,
            "likes": likes,
            "parent_id": None,
            "replies": replies,
        }
    except Exception:
        return None


def parse_moment_comment(comment_el, index: int) -> dict | None:
    """Parse a single .moment-post comment and its replies using TapTap moment selectors."""
    try:
        author_el = comment_el.query_selector(sel.COMMENT_AUTHOR)
        author = author_el.inner_text().strip()[:50] if author_el else ""
        content_el = comment_el.query_selector(sel.COMMENT_CONTENT)
        text = content_el.inner_text().strip()[:1000] if content_el else ""
        date_els = comment_el.query_selector_all(sel.COMMENT_DATE)
        timestamp = date_els[-1].inner_text().strip() if date_els else ""
        like_el = comment_el.query_selector(sel.COMMENT_LIKES)
        likes = 0
        if like_el:
            num_match = re.search(r"(\d+)", like_el.inner_text())
            if num_match:
                likes = int(num_match.group(1))
        replies = []
        reply_container = comment_el.query_selector(sel.REPLY_CONTAINER)
        if reply_container:
            for reply_el in reply_container.query_selector_all(sel.REPLY_ITEM):
                ra = reply_el.query_selector(sel.REPLY_AUTHOR)
                rc = reply_el.query_selector(sel.REPLY_CONTENT)
                if ra or rc:
                    replies.append({
                        "author": (ra.inner_text().strip() if ra else "")[:50],
                        "text": (rc.inner_text().strip() if rc else "")[:1000],
                        "timestamp": "",
                        "likes": 0,
                        "parent_id": None,
                        "replies": [],
                    })
        return {
            "id": f"comment_{index}",
            "author": author,
            "text": text,
            "timestamp": timestamp,
            "likes": likes,
            "parent_id": None,
            "replies": replies,
        }
    except Exception:
        return None


def fetch_post_detail(post_url: str = None, post_id: str = None, app_id: str = None) -> dict:
    """Fetch post detail and all comments from TapTap."""
    
    if post_url:
        url = post_url
        post_id = extract_post_id_from_url(post_url) or "unknown"
    elif post_id and app_id:
        url = f"https://www.taptap.cn/moment/{post_id}"
    else:
        return {"status": "error", "reason": "Either post_url or (post_id + app_id) required"}
    
    print(f"Fetching post: {url}", file=sys.stderr)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        try:
            # Navigate to post
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)
            
            # Close popup if exists
            try:
                close_selectors = [
                    'button:has-text("关闭")',
                    'button:has-text("知道了")',
                    '.close',
                    '[class*="close"]'
                ]
                for close_sel in close_selectors:
                    btn = page.query_selector(close_sel)
                    if btn:
                        btn.click()
                        page.wait_for_timeout(500)
                        break
            except:
                pass
            
            # Post metadata (TapTap moment page selectors)
            title_el = page.query_selector(sel.POST_TITLE)
            if not title_el:
                title_el = page.query_selector("h1, [class*='title'], .post-title")
            post_title = title_el.inner_text().strip()[:200] if title_el else ""

            body_el = page.query_selector(sel.POST_CONTENT)
            if not body_el:
                body_el = page.query_selector(sel.POST_CONTENT_FALLBACK)
            if not body_el:
                body_el = page.query_selector("[class*='content'], [class*='body'], .post-content, article")
            post_body = body_el.inner_text().strip()[:2000] if body_el else ""

            author_el = page.query_selector(sel.POST_AUTHOR)
            if not author_el:
                author_el = page.query_selector(sel.POST_AUTHOR_FALLBACK)
            if not author_el:
                author_el = page.query_selector("[class*='author'], [class*='user-name'], [class*='nickname']")
            post_author = author_el.inner_text().strip()[:50] if author_el else ""

            date_el = page.query_selector(sel.POST_DATE)
            if not date_el:
                date_el = page.query_selector(sel.POST_DATE_FALLBACK)
            post_created_at = ""
            if date_el:
                post_created_at = (date_el.get_attribute("title") or date_el.inner_text() or "").strip()

            post_score = 0
            stats_el = page.query_selector("[class*='stats'], [class*='count'], [class*='meta']")
            if stats_el:
                num_match = re.search(r"(\d+)", stats_el.inner_text())
                if num_match:
                    post_score = int(num_match.group(1))

            # Load all comments: scroll, click 加载更多 / 查看更多回复, stop at 已经到底了
            comments = []
            max_scrolls = 20
            for scroll in range(max_scrolls):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1500)
                end_el = page.query_selector(sel.COMMENT_LIST_END)
                if end_el and sel.COMMENT_LIST_END_TEXT in (end_el.inner_text() or ""):
                    break
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
                try:
                    for btn in page.query_selector_all(sel.LOAD_MORE_REPLIES):
                        if btn.is_visible():
                            btn.click()
                            page.wait_for_timeout(1000)
                except Exception:
                    pass
                page.wait_for_timeout(1000)

            # Parse comments: prefer moment-post list
            list_el = page.query_selector(sel.COMMENT_LIST)
            if list_el:
                comment_els = list_el.query_selector_all(sel.COMMENT_ITEM)
                for idx, el in enumerate(comment_els):
                    c = parse_moment_comment(el, idx)
                    if c and (c.get("text") or c.get("replies")):
                        comments.append(c)
            if not comments:
                comment_els = page.query_selector_all("[class*='comment'], [class*='reply-item'], [class*='discuss-item']")
                for el in comment_els:
                    c = parse_comment_element(el)
                    if c:
                        comments.append(c)
            print(f"Found {len(comments)} comments", file=sys.stderr)
            
            browser.close()
            
            return {
                "source": "taptap",
                "game_id": app_id or "unknown",
                "post_id": post_id,
                "data_type": "post_detail",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "locale": "zh-CN",
                "url": url,
                "post": {
                    "id": post_id,
                    "title": post_title,
                    "body": post_body,
                    "author": post_author,
                    "url": url,
                    "created_at": post_created_at,
                    "score": post_score,
                    "tags": []
                },
                "comments": comments,
                "comment_count": len(comments),
                "status": "success"
            }
            
        except Exception as e:
            browser.close()
            return {
                "status": "error",
                "reason": str(e),
                "url": url
            }


def main():
    parser = argparse.ArgumentParser(description="Fetch TapTap post detail with comments")
    parser.add_argument("--post-url", help="Full URL of the post")
    parser.add_argument("--post-id", help="Post ID")
    parser.add_argument("--app-id", help="App ID (required if using post-id)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--format", choices=["cie", "raw"], default="cie", 
                        help="Output format: cie (for sentiment_monitor) or raw")
    
    args = parser.parse_args()
    
    if not args.post_url and not (args.post_id and args.app_id):
        parser.error("Either --post-url or (--post-id and --app-id) required")
    
    result = fetch_post_detail(args.post_url, args.post_id, args.app_id)
    
    # Convert to CIE format if requested
    if args.format == "cie" and result.get("status") == "success":
        cie_result = convert_to_cie(result)
        result["cie_data"] = cie_result
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def convert_to_cie(raw_data: dict) -> list:
    """Convert raw post data to CIE format."""
    cie_list = []
    
    post = raw_data.get("post", {})
    comments = raw_data.get("comments", [])
    
    for comment in comments:
        cie = {
            "cie_id": f"cie_{comment['id']}",
            "timestamp": comment.get("timestamp", raw_data.get("fetched_at")),
            "platform": "taptap",
            "regional_context": {
                "cluster": "east_asia",
                "region": "zh-CN",
                "language": "zh"
            },
            "participants": {
                "author": {
                    "id": comment["author"],
                    "role": "player"
                },
                "respondents": [r["author"] for r in comment.get("replies", [])]
            },
            "narrative": {
                "surface_topic": "post_response",
                "narrative_motif": "unknown",
                "narrative_stage": "unknown"
            },
            "affective_field": {
                "dominant_emotion": "unknown",
                "emotional_intensity": 0.5,
                "toxicity_level": 0.5,
                "resonance_pattern": "unknown"
            },
            "temporal_topology": {
                "event_phase": "response",
                "narrative_momentum": "unknown",
                "intervention_window": "unknown"
            },
            "raw_data": {
                "text": comment["text"],
                "likes": comment["likes"],
                "parent_id": comment.get("parent_id"),
                "post_title": post.get("title")
            }
        }
        cie_list.append(cie)
    
    return cie_list


if __name__ == "__main__":
    main()
