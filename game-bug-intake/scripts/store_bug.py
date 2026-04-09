#!/usr/bin/env python3
"""
存储 Bug 报告到飞书表格
"""
import argparse
import json
import os
import sys
from datetime import datetime

def store_bug(args):
    """
    将 Bug 信息存储到飞书表格
    实际实现需要调用飞书 API
    """
    bug_data = {
        "uid": args.uid,
        "timestamp": datetime.now().isoformat(),
        "bug_type": args.type,
        "severity": args.severity,
        "title": args.title,
        "description": args.description,
        "location": args.location or "",
        "device": args.device or "",
        "version": args.version or "",
        "reproduction_steps": args.steps or "",
        "workarounds_tried": args.workarounds or "",
        "screenshots": args.screenshots or "",
        "status": "pending",
        "handler": ""
    }
    
    # TODO: 实现飞书 API 调用
    # 这里先打印到控制台，实际使用时替换为飞书 API 调用
    print(json.dumps(bug_data, ensure_ascii=False, indent=2))
    print("\n[NOTE] Bug 数据已准备好，需要配置飞书 API 后写入表格")
    
    return bug_data

def main():
    parser = argparse.ArgumentParser(description='Store bug report to Feishu spreadsheet')
    parser.add_argument('--title', required=True, help='Bug title/summary')
    parser.add_argument('--type', required=True, 
                       choices=['progression_blocker', 'visual_bug', 'data_loss', 
                               'performance', 'functional', 'text_error'],
                       help='Bug type')
    parser.add_argument('--severity', required=True,
                       choices=['blocker', 'major', 'minor'],
                       help='Severity level')
    parser.add_argument('--uid', required=True, help='Player UID')
    parser.add_argument('--description', default='', help='Detailed description')
    parser.add_argument('--location', default='', help='Where the bug occurs')
    parser.add_argument('--device', default='', help='Device info')
    parser.add_argument('--version', default='', help='Game version')
    parser.add_argument('--steps', default='', help='Reproduction steps')
    parser.add_argument('--workarounds', default='', help='Workarounds tried')
    parser.add_argument('--screenshots', default='', help='Screenshot URLs')
    
    args = parser.parse_args()
    store_bug(args)

if __name__ == '__main__':
    main()
