#!/usr/bin/env python3
"""
TapTap moment-page selectors for game_crawl.

Target pages:
- List: https://www.taptap.cn/app/{app_id}/topic?type=official
- Post:  https://www.taptap.cn/moment/{moment_id}

Comment list end marker: element with class tap-list__bottom-finished-text and text "已经到底了".
"""

# --- List page (app/{id}/topic?type=official) ---
# Posts are in feed/cards; links are /moment/{id}. Keep generic list selectors in crawler.

# --- Post (moment) page ---
# Publisher (post author)
POST_AUTHOR = ".moment-head__status a"
POST_AUTHOR_FALLBACK = "div.topic-detail__status.caption-m12-w12.gray-04.moment-head__status a"

# Post title
POST_TITLE = ".moment-head__title-wrapper h1"

# Post body (first main content block under head)
POST_CONTENT = ".moment-page__content div.moment-head__title-wrapper + * + div div"
POST_CONTENT_FALLBACK = ".moment-page__content > div > div:nth-child(3) > div"

# Post date (prefer title= full datetime)
POST_DATE = 'span.tap-time.moment-status-tag[itemprop="dateCreated"]'
POST_DATE_FALLBACK = "span.tap-time.moment-status-tag.topic-detail__space-right"

# --- Comment list (under .moment-page__comment) ---
COMMENT_LIST = ".moment-comment-list__tap-list"
COMMENT_ITEM = ".moment-post"

# Comment author
COMMENT_AUTHOR = ".moment-post__user-name a"

# Comment date (in footer)
COMMENT_DATE = ".moment-post__footer span"

# Comment content
COMMENT_CONTENT = ".moment-post__content-wrapper div"

# Comment like count
COMMENT_LIKES = ".vote-button__button-text"

# Reply container under a comment
REPLY_CONTAINER = ".moment-post-item__comments"

# Reply item (nested post)
REPLY_ITEM = ".moment-post__body--child"

# Reply author (same as comment within reply item)
REPLY_AUTHOR = ".moment-post__user-name a"

# Reply content
REPLY_CONTENT = ".moment-post__content-wrapper div"

# "Load more replies" button
LOAD_MORE_REPLIES = ".moment-post-item__comment-more > div"

# End of comment list marker
COMMENT_LIST_END = ".tap-list__bottom-finished-text"
COMMENT_LIST_END_TEXT = "已经到底了"

# --- 回复弹窗（点击「查看更多回复」后出现）---
REPLY_MODAL = ".tap-overlay .media-modal__body"
REPLY_MODAL_ITEM = ".tap-overlay .media-modal__body .tap-list > div"
REPLY_MODAL_CLOSE = ".tap-overlay"
