#!/usr/bin/env python3
"""Shared HTTP helper for game_crawl scripts.

Provides ``get_json()`` with uniform exponential back-off and structured
error signals so each platform script no longer duplicates retry logic.

Pure stdlib — no third-party dependencies.
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

_DEFAULT_RETRY_WAIT = 2   # base seconds for exponential back-off
_DEFAULT_MAX_RETRIES = 3


def get_json(
    url: str,
    headers: dict,
    params: dict | None = None,
    retries: int = _DEFAULT_MAX_RETRIES,
    retry_on: tuple = (429, 412),
    timeout: int = 20,
    opener=None,
    label: str = "",
) -> tuple[dict, int, str]:
    """Fetch a JSON endpoint with exponential back-off on rate-limits.

    Args:
        url: Target URL (query params may be supplied separately via ``params``).
        headers: Request headers dict.
        params: Optional query parameters dict, URL-encoded and appended to ``url``.
        retries: Maximum number of attempts. Default 3.
        retry_on: HTTP status codes that trigger a retry. Default ``(429, 412)``.
        timeout: Per-request timeout in seconds. Default 20.
        opener: Optional ``urllib.request.OpenerDirector`` (e.g. with cookie jar).
            Uses ``urllib.request.urlopen`` when ``None``.
        label: Short log prefix shown in stderr messages, e.g. ``"[reddit]"``.

    Returns:
        A ``(data, status_code, error_msg)`` tuple:

        - **Success**: ``({...}, 200, "")``
        - **401 / 403 blocked**: ``({}, 4xx, "blocked: HTTP 4xx")`` — no retry,
          a ``{"status": "blocked"}`` JSON line is printed to stderr.
        - **Retry exhausted**: ``({}, last_status, "rate-limited after N retries")``
          — a ``{"status": "blocked"}`` JSON line is printed to stderr.
        - **Non-JSON response**: ``({}, 0, "non-JSON response")``
        - **Other network / HTTP error**: re-raises on the final attempt.
    """
    if params:
        url = url + "?" + urllib.parse.urlencode(params)

    tag = f"{label} " if label else ""
    _open = opener.open if opener else urllib.request.urlopen
    last_status = 0

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with _open(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw), 200, ""

        except urllib.error.HTTPError as exc:
            last_status = exc.code
            if exc.code in retry_on:
                wait = _DEFAULT_RETRY_WAIT * (2 ** attempt)
                print(
                    f"{tag}rate-limited (HTTP {exc.code}), retrying in {wait}s…",
                    file=sys.stderr,
                )
                time.sleep(wait)
            elif exc.code in (401, 403):
                msg = f"blocked: HTTP {exc.code}"
                print(
                    json.dumps({"status": "blocked", "reason": f"HTTP {exc.code}"}),
                    file=sys.stderr,
                )
                return {}, exc.code, msg
            else:
                print(f"{tag}HTTP {exc.code} for {url}", file=sys.stderr)
                if attempt < retries - 1:
                    time.sleep(_DEFAULT_RETRY_WAIT)
                else:
                    raise

        except json.JSONDecodeError:
            print(f"{tag}non-JSON response from {url}", file=sys.stderr)
            return {}, 0, "non-JSON response"

        except Exception as exc:  # pylint: disable=broad-except
            print(f"{tag}request error: {exc}", file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(_DEFAULT_RETRY_WAIT)
            else:
                raise

    # All retries on rate-limit exhausted
    msg = f"rate-limited after {retries} retries"
    print(
        json.dumps({"status": "blocked", "reason": msg}),
        file=sys.stderr,
    )
    return {}, last_status, msg
