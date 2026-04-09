#!/usr/bin/env python3
"""
Game Data Pipeline - 游戏数据全流程管理

一站式处理：发现 → 注册 → 抓取 → 汇总

Usage:
    python run_pipeline.py --game-name "原神" --limit 30
    python run_pipeline.py --game-name "Genshin Impact" --platforms youtube,reddit --limit 50
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
from storage_tool import DataStorage


def discover_game(game_name: str) -> dict:
    """发现游戏信息"""
    print(f"[pipeline] 发现游戏: {game_name}")
    # 调用 game_discovery
    result = subprocess.run(
        ["python", "skills/game_discovery/scripts/discover.py", "--game", game_name],
        capture_output=True, text=True
    )
    # 简化：返回基本信息
    return {"name": game_name, "name_en": game_name}


def get_or_create_game_id(game_name: str) -> str:
    """获取或创建 game_id"""
    print(f"[pipeline] 检查注册: {game_name}")
    # 检查 registry
    result = subprocess.run(
        ["python", "scripts/registry_tool.py", "--get-id", game_name],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    
    # 未注册，需要添加
    print(f"[pipeline] 游戏未注册，请先注册:")
    print(f"  python scripts/registry_tool.py --add --name \"{game_name}\" --en \"英文名\"")
    return None


def run_youtube_pipeline(game_id: str, query: str, limit: int):
    """执行 YouTube 抓取"""
    print(f"[pipeline] 执行 YouTube 抓取...")
    
    # metadata
    subprocess.run([
        "python", "active_skills/youtube_metadata/scripts/youtube_metadata.py",
        "--game-id", game_id,
        "--query", query,
        "--limit", str(limit)
    ])


def run_bilibili_pipeline(game_id: str, keyword: str, limit: int):
    """执行 Bilibili 抓取"""
    print(f"[pipeline] 执行 Bilibili 抓取...")
    
    subprocess.run([
        "python", "active_skills/bilibili_metadata/scripts/bilibili_metadata.py",
        "--game-id", game_id,
        "--keyword", keyword,
        "--limit", str(limit)
    ])


def run_reddit_pipeline(game_id: str, subreddit: str, limit: int):
    """执行 Reddit 抓取"""
    print(f"[pipeline] 执行 Reddit 抓取...")
    
    subprocess.run([
        "python", "active_skills/reddit_metadata/scripts/reddit_metadata.py",
        "--game-id", game_id,
        "--subreddit", subreddit,
        "--limit", str(limit)
    ])


def run_taptap_pipeline(game_id: str, app_id: str, limit: int):
    """执行 TapTap 抓取"""
    print(f"[pipeline] 执行 TapTap 抓取...")
    
    subprocess.run([
        "python", "active_skills/taptap_review/scripts/taptap_review.py",
        "--game-id", game_id,
        "--app-id", app_id,
        "--limit", str(limit)
    ])


def main():
    parser = argparse.ArgumentParser(description="Game Data Pipeline")
    parser.add_argument("--game-name", required=True, help="游戏名称")
    parser.add_argument("--platforms", help="指定平台（逗号分隔，默认自动）")
    parser.add_argument("--limit", type=int, default=30, help="每个平台数量")
    args = parser.parse_args()
    
    print(f"=" * 50)
    print(f"Game Data Pipeline: {args.game_name}")
    print(f"=" * 50)
    
    # 1. 发现游戏
    game_info = discover_game(args.game_name)
    
    # 2. 获取 game_id
    game_id = get_or_create_game_id(args.game_name)
    if not game_id:
        print("[pipeline] 错误: 游戏未注册")
        sys.exit(1)
    
    print(f"[pipeline] game_id: {game_id}")
    
    # 3. 执行抓取
    # 简化版：需要用户指定平台或从 registry 读取
    print("[pipeline] 请手动执行各平台抓取:")
    print(f"  YouTube: python active_skills/youtube_metadata/scripts/youtube_metadata.py --game-id {game_id} --query \"{game_info['name_en']} review\" --limit {args.limit}")
    print(f"  Bilibili: python active_skills/bilibili_metadata/scripts/bilibili_metadata.py --game-id {game_id} --keyword \"{args.game_name}\" --limit {args.limit}")
    
    print(f"[pipeline] 完成")


if __name__ == "__main__":
    main()
