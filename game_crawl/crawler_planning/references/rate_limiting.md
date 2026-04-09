# 速率限制策略

## 核心原则

**宁可慢，不可封。尊重平台，保护自己。**

## 各平台限制

### TapTap

| 指标 | 值 | 说明 |
|------|---|------|
| 请求间隔 | 2-3 秒 | 滚动加载间隔 |
| 并发数 | 1 | 单账号单会话 |
| 日限额 | 无明确限制 | 但异常行为会触发验证码 |
| 账号要求 | 可选 | 登录后可看更多内容 |

**策略：**
- 使用 Playwright 模拟真实用户滚动
- 每次滚动后等待 2-3 秒
- 遇到验证码立即停止，切换账号或等待

### Bilibili

| 指标 | 值 | 说明 |
|------|---|------|
| API 调用间隔 | 0.5 秒 | 搜索 API |
| 并发数 | 1 | 单 IP |
| 日限额 | 无明确限制 | 但频繁调用会 412 |
| 账号要求 | 推荐 | 登录后配额更高 |

**策略：**
- API 调用间隔 0.5 秒
- 使用 BILIBILI_COOKIE 环境变量
- 遇到 412/429 状态码，等待 30 秒后重试
- 最多重试 3 次

### Reddit

| 指标 | 值 | 说明 |
|------|---|------|
| API 调用间隔 | 1 秒 | PRAW 推荐 |
| 并发数 | 1 | 单账号 |
| 日限额 | 1000 请求 | OAuth 应用 |
| 账号要求 | 必须 | 需要 API key |

**策略：**
- 使用 PRAW 库自动处理速率限制
- 优先读取已有数据，减少 API 调用
- 大 subreddit 使用流式读取

### YouTube

| 指标 | 值 | 说明 |
|------|---|------|
| API 调用间隔 | 1 秒 | Data API |
| 并发数 | 1 | 单 API key |
| 日限额 | 10,000 单位 | 搜索 100 单位/次 |
| 账号要求 | 必须 | 需要 API key |

**策略：**
- 优先使用 Supadata API（不需要 key）
- Data API 作为备选
- 批量获取视频信息（减少 API 调用）

## 通用策略

### 请求间隔

```python
import time
import random

def sleep_between_requests(platform: str):
    """根据平台设置请求间隔"""
    intervals = {
        "taptap": (2, 3),      # 2-3 秒随机
        "bilibili": (0.5, 1),  # 0.5-1 秒随机
        "reddit": (1, 2),      # 1-2 秒随机
        "youtube": (1, 2),     # 1-2 秒随机
    }
    
    min_sleep, max_sleep = intervals.get(platform, (1, 2))
    time.sleep(random.uniform(min_sleep, max_sleep))
```

### 重试机制

```python
from functools import wraps
import time

def retry_on_failure(max_retries=3, delay=5):
    """装饰器：失败时重试"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"  失败，{delay}秒后重试 ({attempt + 1}/{max_retries}): {e}")
                        time.sleep(delay * (attempt + 1))  # 递增延迟
                    else:
                        raise
            return None
        return wrapper
    return decorator
```

### 并发控制

**禁止同一平台的多任务并发。**

```python
from threading import Lock

platform_locks = {
    "taptap": Lock(),
    "bilibili": Lock(),
    "reddit": Lock(),
    "youtube": Lock(),
}

def run_with_platform_lock(platform: str, func, *args, **kwargs):
    """使用平台锁执行函数"""
    lock = platform_locks.get(platform)
    if lock:
        with lock:
            return func(*args, **kwargs)
    else:
        return func(*args, **kwargs)
```

## 异常检测

### 被封迹象

| 平台 | 被封迹象 | 应对措施 |
|------|---------|---------|
| taptap | 验证码、登录要求 | 切换账号，等待 1 小时 |
| bilibili | 412/429 状态码 | 等待 30 分钟，减少频率 |
| reddit | 403/429 状态码 | 检查 API 配额，等待重置 |
| youtube | 403 配额超限 | 等待次日配额重置 |

### 自动降级

当检测到被封时：
1. 立即停止该平台的所有任务
2. 记录错误和当前进度
3. 继续执行其他平台的任务
4. 任务完成后报告被封情况

## 最佳实践

1. **优先使用已有数据** — 减少不必要的抓取
2. **试点先行** — 先抓 5 条验证可行性
3. **分散时间** — 长任务分时段执行
4. **监控配额** — 定期检查 API 使用情况
5. **多账号备用** — 关键平台准备多个账号
