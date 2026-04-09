#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书云文档发布工具：从 Markdown 内容或本地文件创建飞书云文档。"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

_BASE = "https://open.feishu.cn/open-apis"


def _load_openclaw_env() -> dict:
    """从 OpenClaw 配置文件加载环境变量（根级别 env 字段）。"""
    config_paths = [
        os.path.expanduser("~/.openclaw/openclaw.json"),
        os.path.expanduser("~/.openclaw/config.json"),
    ]
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                # 从根级别 env 字段读取
                env = config.get("env", {})
                return env
            except Exception:
                continue
    return {}


def _get_env(key: str) -> str:
    """获取环境变量，优先从系统环境变量读取，如果没有则从 OpenClaw 配置读取。"""
    value = os.environ.get(key, "").strip()
    if not value:
        openclaw_env = _load_openclaw_env()
        value = openclaw_env.get(key, "").strip()
    return value


def _get_tenant_access_token() -> str:
    app_id = _get_env("FEISHU_APP_ID")
    app_secret = _get_env("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError("未配置飞书凭证。请在 OpenClaw 配置的 env 字段中设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET。")
    url = f"{_BASE}/auth/v3/tenant_access_token/internal"
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json={"app_id": app_id, "app_secret": app_secret})
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"飞书 token 失败: code={data.get('code')} msg={data.get('msg')}")
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError("飞书 tenant_access_token 为空")
    return token


def _create_docx_document(token: str, title: str, folder_token: str) -> str:
    """创建新版 docx 文档，返回 document_id。"""
    url = f"{_BASE}/docx/v1/documents"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload: dict[str, Any] = {"title": title or "未命名文档"}
    if folder_token:
        payload["folder_token"] = folder_token
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        err = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        raise RuntimeError(f"飞书创建 docx 文档失败: code={err.get('code', resp.status_code)} msg={err.get('msg', resp.text)}")
    body = resp.json()
    if body.get("code") != 0:
        raise RuntimeError(f"飞书创建 docx 文档失败: code={body.get('code')} msg={body.get('msg')}")
    data = body.get("data") or {}
    doc_id = data.get("document_id") or (data.get("document") or {}).get("document_id")
    if not doc_id:
        raise RuntimeError("飞书创建 docx 返回无 document_id")
    return doc_id


def _parse_inline_to_elements(raw: str) -> list[dict]:
    """解析行内 Markdown：**加粗**、*斜体*，返回 text_run elements 列表。"""
    if not raw:
        return [{"text_run": {"content": ""}}]
    elements: list[dict] = []
    i = 0
    while i < len(raw):
        if i + 2 <= len(raw) and raw[i:i+2] == "**":
            j = raw.find("**", i + 2)
            if j == -1:
                elements.append({"text_run": {"content": raw[i:]}})
                break
            content = raw[i+2:j]
            elements.append({"text_run": {"content": content, "text_element_style": {"bold": True}}})
            i = j + 2
            continue
        if raw[i] == "*" and (i + 1 >= len(raw) or raw[i+1] != "*"):
            j = i + 1
            while j < len(raw) and raw[j] != "*":
                j += 1
            if j < len(raw):
                content = raw[i+1:j]
                elements.append({"text_run": {"content": content, "text_element_style": {"italic": True}}})
                i = j + 1
                continue
        j = i
        while j < len(raw):
            if raw[j] == "*":
                break
            j += 1
        content = raw[i:j]
        if content:
            elements.append({"text_run": {"content": content}})
        i = j
    if not elements:
        elements.append({"text_run": {"content": ""}})
    return elements


def _block_payload(block_type: int, content: str) -> dict:
    """根据 block_type 与 content 生成块。"""
    elements = _parse_inline_to_elements(content)
    if block_type == 2:
        return {"block_type": 2, "text": {"elements": elements, "style": {}}}
    if 3 <= block_type <= 11:
        key = f"heading{block_type - 2}"
        return {"block_type": block_type, key: {"elements": elements}}
    return {"block_type": 2, "text": {"elements": elements, "style": {}}}


def _block_payload_with_elements(block_type: int, elements: list[dict]) -> dict:
    """使用已有的 elements 列表构造块。"""
    text_payload = {"elements": elements, "style": {}}
    if block_type == 2:
        return {"block_type": 2, "text": text_payload}
    if 3 <= block_type <= 11:
        key = f"heading{block_type - 2}"
        return {"block_type": block_type, key: {"elements": elements}}
    if block_type == 12:
        return {"block_type": 12, "bullet": text_payload}
    if block_type == 13:
        return {"block_type": 13, "ordered": text_payload}
    if block_type == 15:
        return {"block_type": 15, "quote": text_payload}
    return {"block_type": 2, "text": text_payload}


def _spacer_block() -> dict:
    """返回表示空一行的段落块。"""
    return {"block_type": 2, "text": {"elements": [{"text_run": {"content": "\u200b"}}], "style": {}}, "_spacer": True}


def _logical_type(block: dict) -> str:
    """块逻辑类型。"""
    if block.get("_spacer"):
        return "spacer"
    if block.get("_internal_table"):
        return "table"
    bt = block.get("block_type")
    if bt in (3, 4, 5, 6, 7, 8, 9, 10, 11):
        return "heading"
    if bt == 12:
        return "bullet"
    if bt == 13:
        return "ordered"
    if bt == 15:
        return "quote"
    if bt == 22:
        return "divider"
    return "text"


def _insert_spacers(blocks: list[dict]) -> list[dict]:
    """在合适位置插入空行块。"""
    if not blocks:
        return []
    result: list[dict] = []
    for i, block in enumerate(blocks):
        prev_type = _logical_type(blocks[i-1]) if i > 0 else "spacer"
        curr_type = _logical_type(block)
        insert_before = False
        if prev_type == "spacer":
            insert_before = False
        elif prev_type == "heading" and curr_type not in ("bullet", "ordered", "heading"):
            insert_before = True
        elif prev_type == "table":
            insert_before = True
        elif curr_type == "table":
            insert_before = True
        elif prev_type == "quote" and curr_type not in ("bullet", "ordered"):
            insert_before = True
        elif prev_type in ("bullet", "ordered") and curr_type in ("text", "heading"):
            insert_before = True
        elif i > 0 and curr_type == "heading":
            insert_before = True
        if insert_before and curr_type == "spacer":
            insert_before = False
        if insert_before:
            result.append(_spacer_block())
        result.append(block)
    return result


def _is_table_separator(s: str) -> bool:
    """是否表格分隔行。"""
    t = s.strip()
    if "|" not in t:
        return False
    parts = [p.strip() for p in t.split("|") if p.strip()]
    return all(all(c in "-:" for c in part) and len(part) >= 1 for part in parts)


def _parse_table_rows(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    """解析连续表格行。"""
    rows: list[list[str]] = []
    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or "|" not in stripped:
            break
        if _is_table_separator(stripped):
            i += 1
            continue
        cells = [c.strip() for c in stripped.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        rows.append(cells)
        i += 1
    return rows, i


def _table_to_block(rows: list[list[str]]) -> dict:
    """将表格行转为内部表格标记。"""
    if not rows:
        return _block_payload(2, "(空表)")
    ncols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < ncols:
            r.append("")
    return {"_internal_table": True, "block_type": 31, "_rows": rows, "_ncols": ncols}


def _md_to_docx_blocks(md: str) -> list[dict]:
    """将 Markdown 转为飞书 docx 子块列表。"""
    blocks: list[dict] = []
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            if blocks and not blocks[-1].get("_spacer"):
                blocks.append(_spacer_block())
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            continue
        if stripped.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            blocks.append(_block_payload(2, "\n".join(code_lines)))
            continue
        if stripped.startswith("#"):
            level = 0
            while level < len(stripped) and stripped[level] == "#":
                level += 1
            title_text = stripped[level:].strip()
            if title_text and level <= 9:
                blocks.append(_block_payload(2 + level, title_text))
            i += 1
            continue
        if stripped.startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                part = lines[i].strip()[1:].strip()
                quote_lines.append(part)
                i += 1
            merged = " ".join(quote_lines)
            elements = _parse_inline_to_elements(merged)
            blocks.append(_block_payload_with_elements(15, elements))
            continue
        if "|" in stripped and ((i + 1 < len(lines) and ("|" in lines[i+1] or _is_table_separator(lines[i+1].strip()))) or (i > 0 and "|" in lines[i-1])):
            table_rows, next_i = _parse_table_rows(lines, i)
            if table_rows:
                blocks.append(_table_to_block(table_rows))
                i = next_i
                continue
        if stripped in ("---", "***", "___") or (len(stripped) >= 3 and all(c == stripped[0] for c in stripped) and stripped[0] in ("-", "*", "_")):
            blocks.append({"block_type": 22, "divider": {}})
            i += 1
            continue
        leading_spaces = len(line) - len(line.lstrip(" \t"))
        is_indented = leading_spaces >= 2
        if stripped.startswith("- ") or (stripped.startswith("* ") and len(stripped) > 2):
            list_content = stripped[2:].strip()
            elements = _parse_inline_to_elements(list_content)
            if is_indented:
                sub_elements = [{"text_run": {"content": "• "}}] + elements
                blocks.append(_block_payload_with_elements(2, sub_elements))
            else:
                blocks.append(_block_payload_with_elements(12, elements))
            i += 1
            continue
        num_end = 0
        while num_end < len(stripped) and stripped[num_end].isdigit():
            num_end += 1
        if num_end > 0 and num_end < len(stripped) and stripped[num_end] == "." and (num_end + 1 >= len(stripped) or stripped[num_end+1].isspace()):
            list_content = stripped[num_end+1:].strip()
            elements = _parse_inline_to_elements(list_content)
            blocks.append(_block_payload_with_elements(13, elements))
            i += 1
            continue
        blocks.append(_block_payload(2, line))
        i += 1
    if not blocks:
        blocks.append(_block_payload(2, "(无内容)"))
    return blocks


def _add_docx_blocks(token: str, document_id: str, parent_block_id: str, children: list[dict]) -> None:
    """向指定块下追加子块（单次最多 50 个）。"""
    if not children:
        return
    url = f"{_BASE}/docx/v1/documents/{document_id}/blocks/{parent_block_id}/children"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"index": -1, "children": children[:50]}
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        err = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        raise RuntimeError(f"飞书追加块失败: code={err.get('code', resp.status_code)} msg={err.get('msg', resp.text)}")
    body = resp.json()
    if body.get("code") != 0:
        raise RuntimeError(f"飞书追加块失败: code={body.get('code')} msg={body.get('msg')}")


def _get_cell_first_child(token: str, document_id: str, cell_block_id: str) -> str | None:
    """获取 TableCell 的第一个子块 block_id。"""
    url = f"{_BASE}/docx/v1/documents/{document_id}/blocks/{cell_block_id}/children"
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, headers=headers, params={"page_size": 5, "document_revision_id": -1})
    if resp.status_code != 200:
        return None
    body = resp.json()
    if body.get("code") != 0:
        return None
    items = (body.get("data") or {}).get("items") or []
    if not items or items[0].get("block_type") != 2:
        return None
    return items[0].get("block_id")


def _patch_block_text(token: str, document_id: str, block_id: str, elements: list[dict]) -> bool:
    """用 PATCH 更新块内文本。"""
    url = f"{_BASE}/docx/v1/documents/{document_id}/blocks/{block_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"update_text_elements": {"elements": elements}}
    with httpx.Client(timeout=15) as client:
        resp = client.patch(url, headers=headers, params={"document_revision_id": -1}, json=payload)
    return resp.status_code == 200 and (resp.json() or {}).get("code") == 0


def _delete_cell_auto_block(token: str, document_id: str, cell_block_id: str) -> None:
    """删除 TableCell 中飞书自动插入的空文本块。"""
    url = f"{_BASE}/docx/v1/documents/{document_id}/blocks/{cell_block_id}/children/batch_delete"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with httpx.Client(timeout=15) as client:
        client.request("DELETE", url, headers=headers, params={"document_revision_id": -1}, json={"start_index": 0, "end_index": 1})


def _display_width(s: str) -> int:
    """计算字符串显示宽度，CJK 字符算 2 单位。"""
    w = 0
    for c in s:
        w += 2 if ('\u1100' <= c <= '\u115f' or '\u2e80' <= c <= '\u9fff' or
                   '\ua960' <= c <= '\ua97f' or '\uac00' <= c <= '\ud7ff' or
                   '\uf900' <= c <= '\ufaff' or '\ufe10' <= c <= '\ufe19' or
                   '\ufe30' <= c <= '\ufe6f' or '\uff01' <= c <= '\uff60' or
                   '\uffe0' <= c <= '\uffe6') else 1
    return w or 1


def _create_and_fill_table(token: str, document_id: str, parent_block_id: str, rows: list[list[str]], ncols: int) -> None:
    """两步创建飞书表格：先建空表，再逐 cell 填写内容。"""
    col_max_widths = [0] * ncols
    for row in rows:
        for ci, cell in enumerate(row):
            col_max_widths[ci] = max(col_max_widths[ci], _display_width(cell))
    total_disp = sum(col_max_widths) or 1
    total_px = 750
    min_col_px = 120
    col_widths = [max(min_col_px, int(total_px * w / total_disp)) for w in col_max_widths]

    url = f"{_BASE}/docx/v1/documents/{document_id}/blocks/{parent_block_id}/children"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "index": -1,
        "children": [{
            "block_type": 31,
            "table": {
                "property": {
                    "row_size": len(rows),
                    "column_size": ncols,
                    "column_width": col_widths,
                }
            }
        }]
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, headers=headers, json=payload)
    body = resp.json()
    if resp.status_code >= 400 or body.get("code") != 0:
        raise RuntimeError(f"创建表格失败: code={body.get('code')} msg={body.get('msg')}")

    children_resp = (body.get("data") or {}).get("children") or []
    table_block = children_resp[0] if children_resp else {}
    table_block_id = table_block.get("block_id", "")
    cell_ids: list[str] = table_block.get("children") or []

    if not cell_ids and table_block_id:
        q_url = f"{_BASE}/docx/v1/documents/{document_id}/blocks/{table_block_id}/children"
        with httpx.Client(timeout=30) as client:
            qresp = client.get(q_url, headers={"Authorization": f"Bearer {token}"}, params={"page_size": 500})
        qbody = qresp.json()
        items = (qbody.get("data") or {}).get("items") or []
        cell_ids = [item.get("block_id") for item in items if item.get("block_type") == 32]

    for row_idx, row in enumerate(rows):
        for col_idx, cell_text in enumerate(row):
            linear_idx = row_idx * ncols + col_idx
            if linear_idx >= len(cell_ids):
                continue
            cell_block_id = cell_ids[linear_idx]
            elements = _parse_inline_to_elements(cell_text)
            first_child_id = _get_cell_first_child(token, document_id, cell_block_id)
            if first_child_id and _patch_block_text(token, document_id, first_child_id, elements):
                continue
            _delete_cell_auto_block(token, document_id, cell_block_id)
            text_block = {"block_type": 2, "text": {"elements": elements, "style": {}}}
            try:
                _add_docx_blocks(token, document_id, cell_block_id, [text_block])
            except RuntimeError:
                pass


def publish_md(title: str, content: str, folder_token: str = "") -> dict:
    """发布 Markdown 内容到飞书文档。"""
    token = _get_tenant_access_token()
    doc_token = _create_docx_document(token, title, folder_token)
    blocks = _md_to_docx_blocks(content.strip())
    blocks = _insert_spacers(blocks)

    pending: list[dict] = []

    def _flush_pending() -> None:
        nonlocal pending
        if not pending:
            return
        for start in range(0, len(pending), 50):
            _add_docx_blocks(token, doc_token, doc_token, pending[start:start+50])
        pending = []

    for block in blocks:
        if block.get("_internal_table"):
            _flush_pending()
            try:
                _create_and_fill_table(token, doc_token, doc_token, block["_rows"], block["_ncols"])
            except RuntimeError:
                fallback = _block_payload(2, "\n".join(" | ".join(r) for r in block["_rows"]))
                pending.append(fallback)
        else:
            pending.append(block)

    _flush_pending()
    url = f"https://feishu.cn/docx/{doc_token}"
    return {"url": url, "document_id": doc_token}


def main():
    parser = argparse.ArgumentParser(description="发布 Markdown 到飞书云文档")
    parser.add_argument("--title", required=True, help="文档标题")
    parser.add_argument("--content", help="Markdown 内容")
    parser.add_argument("--file", help="本地 Markdown 文件路径")
    parser.add_argument("--folder-token", default="", help="目标文件夹 Token（默认从环境变量 FEISHU_FOLDER_TOKEN 读取）")
    args = parser.parse_args()

    if not args.content and not args.file:
        print(json.dumps({"error": "请提供 --content 或 --file 其一"}, ensure_ascii=False))
        sys.exit(1)

    try:
        if args.file:
            content = Path(args.file).read_text(encoding="utf-8")
        else:
            content = args.content

        # 优先使用命令行参数，如果没有则从环境变量读取
        folder_token = args.folder_token or _get_env("FEISHU_FOLDER_TOKEN")
        result = publish_md(args.title, content, folder_token)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
