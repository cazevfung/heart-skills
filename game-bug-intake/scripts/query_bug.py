#!/usr/bin/env python3
"""
查询玩家上报的 Bug 状态
"""
import argparse
import json
import os

def query_bug(uid):
    """
    查询指定 UID 的 Bug 上报记录
    """
    # TODO: 实现飞书 API 查询
    print(f"查询 UID: {uid} 的 Bug 记录")
    print("[NOTE] 需要配置飞书 API 后实现查询功能")
    return []

def main():
    parser = argparse.ArgumentParser(description='Query bug reports by UID')
    parser.add_argument('--uid', required=True, help='Player UID')
    
    args = parser.parse_args()
    query_bug(args.uid)

if __name__ == '__main__':
    main()
