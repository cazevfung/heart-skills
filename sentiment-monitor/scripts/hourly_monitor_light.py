#!/usr/bin/env python3
"""
心动小镇每小时舆情监控任�?- 轻量�?直接使用现有数据，不依赖实时爬取
"""

import os
import sys
import json
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置
GAME_ID = "heartopia"
GAME_NAME = "心动小镇"
PLATFORMS = ["taptap", "reddit"]

# 路径配置
SKILL_DIR = Path("d:/App Dev/openclaw-main/skills")
FEISHU_DIR = SKILL_DIR / "feishu-doc"
DATA_ROOT = Path("d:/App Dev/openclaw-main/data/game_data")
SNAPSHOT_DIR = DATA_ROOT / "sentiment_snapshots" / GAME_ID
REPORT_DIR = DATA_ROOT / "sentiment_reports" / GAME_ID

SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def try_crawl_platform(platform: str, limit: int = 50) -> bool:
    """尝试实时爬取平台数据"""
    log(f"  尝试实时爬取 {platform}...")
    
    GAME_CRAWL_DIR = SKILL_DIR / "game_crawl"
    data_type = "forum_posts"
    
    cmd = [
        "python",
        str(GAME_CRAWL_DIR / "scripts" / "crawl_runner.py"),
        "--game", GAME_ID,
        "--platforms", platform,
        "--data-types", data_type,
        "--limit", str(limit)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,  # 3分钟超时
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode == 0:
            log(f"    �?{platform} 实时爬取成功")
            return True
        else:
            log(f"    �?{platform} 爬取失败: {result.stderr[:100] if result.stderr else 'Unknown'}")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"    �?{platform} 爬取超时")
        return False
    except Exception as e:
        log(f"    �?{platform} 异常: {e}")
        return False


def load_merged_data(platform: str) -> List[Dict]:
    merged_path = DATA_ROOT / "merged" / platform / GAME_ID / "forum_posts" / "data.json"
    
    if not merged_path.exists():
        return []
    
    try:
        with open(merged_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("posts", data.get("records", []))
    except Exception as e:
        log(f"  读取 {platform} 失败: {e}")
        return []


def check_data_freshness(platform: str) -> Dict:
    merged_path = DATA_ROOT / "merged" / platform / GAME_ID / "forum_posts" / "data.json"
    
    if not merged_path.exists():
        return {"exists": False}
    
    try:
        mtime = datetime.fromtimestamp(merged_path.stat().st_mtime)
        hours_old = (datetime.now() - mtime).total_seconds() / 3600
        
        return {
            "exists": True,
            "hours_old": round(hours_old, 1),
            "last_update": mtime.strftime('%Y-%m-%d %H:%M')
        }
    except Exception as e:
        return {"exists": True, "error": str(e)}


def load_previous_snapshot() -> Optional[Dict]:
    snapshots = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    for snap in snapshots[:3]:
        try:
            with open(snap, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            continue
    return None


def save_snapshot(data: Dict):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    snap_path = SNAPSHOT_DIR / f"snapshot_{timestamp}.json"
    with open(snap_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log(f"  快照已保�? {snap_path.name}")
    return snap_path


def extract_topics(records: List[Dict]) -> Dict:
    topics = {}
    
    keyword_map = {
        "活动": ["活动", "event", "奖励", "reward", "体力", "打卡"],
        "抽卡": ["抽卡", "gacha", "保底", "概率", "池子", "�?],
        "bug": ["bug", "闪退", "卡顿", "crash", "错误", "修复"],
        "运营": ["运营", "官方", "客服", "策划", "公告"],
        "氪金": ["氪金", "付费", "充�?, "pay", "price", "太贵", "性价�?],
        "玩法": ["玩法", "内容", "关卡", "gameplay", "任务", "无聊"],
        "社交": ["社交", "好友", "公会", "social", "联机", "固玩"],
        "更新": ["更新", "版本", "延期", "update", "patch", "维护", "新赛�?]
    }
    
    for record in records:
        content = (record.get("body", "") + " " + record.get("title", "") + " " + record.get("author", "")).lower()
        
        for topic, keywords in keyword_map.items():
            if any(kw in content for kw in keywords):
                if topic not in topics:
                    topics[topic] = {"count": 0, "heat": 0}
                topics[topic]["count"] += 1
                heat = record.get("score", 0) + record.get("likes", 0) + record.get("replies_count", 0) * 2
                topics[topic]["heat"] += heat
    
    return topics


def analyze_narrative_shift(current_records: Dict[str, List[Dict]], previous_snapshot: Optional[Dict]) -> Dict:
    current_topics = {}
    total_current = 0
    for platform, records in current_records.items():
        total_current += len(records)
        topics = extract_topics(records)
        for t, data in topics.items():
            if t not in current_topics:
                current_topics[t] = {"count": 0, "heat": 0}
            current_topics[t]["count"] += data["count"]
            current_topics[t]["heat"] += data["heat"]
    
    if not previous_snapshot:
        return {
            "alert_level": "green",
            "narrative_cohesion": 0.0,
            "new_topics": list(current_topics.keys()),
            "rising_topics": [],
            "falling_topics": [],
            "ai_assessment": "首次分析，建立基�?,
            "recommended_action": "继续监控",
            "total_records": total_current,
            "topics": current_topics
        }
    
    prev_topics = previous_snapshot.get("topics", {})
    new_topics = list(set(current_topics.keys()) - set(prev_topics.keys()))
    
    rising = []
    falling = []
    for topic in set(current_topics.keys()) & set(prev_topics.keys()):
        curr_heat = current_topics[topic]["heat"]
        prev_heat = prev_topics[topic].get("heat", 1)
        change = (curr_heat - prev_heat) / max(prev_heat, 1)
        
        if change > 0.3:
            rising.append({"topic": topic, "change": f"+{change*100:.0f}%"})
        elif change < -0.2:
            falling.append({"topic": topic, "change": f"{change*100:.0f}%"})
    
    rising.sort(key=lambda x: float(x["change"].replace('%', '').replace('+', '')), reverse=True)
    
    alert_level = "green"
    if len(new_topics) >= 2 or len(rising) >= 2:
        alert_level = "yellow"
    if len(new_topics) >= 4 or any(r["topic"] in ["运营", "氪金", "bug"] for r in rising):
        alert_level = "red"
    
    assessment_parts = []
    if new_topics:
        assessment_parts.append(f"新出现议�? {', '.join(new_topics[:3])}")
    if rising:
        assessment_parts.append(f"热度上升: {', '.join(r['topic'] for r in rising[:2])}")
    if not assessment_parts:
        assessment_parts.append("舆情场域相对稳定")
    
    if alert_level == "red":
        action = "建议 2 小时内官方回�?
    elif alert_level == "yellow":
        action = "建议 6 小时内关注并准备回应素材"
    else:
        action = "保持常规监控"
    
    return {
        "alert_level": alert_level,
        "narrative_cohesion": round(max(t["count"] for t in current_topics.values()) / sum(t["count"] for t in current_topics.values()), 2) if current_topics else 0,
        "new_topics": new_topics,
        "rising_topics": rising,
        "falling_topics": falling,
        "ai_assessment": "�?.join(assessment_parts),
        "recommended_action": action,
        "total_records": total_current,
        "topics": current_topics
    }


def generate_report(platform_results: Dict[str, Dict], narrative: Dict, timestamp: datetime) -> str:
    alert_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    alert = narrative.get("alert_level", "green")
    
    md = f"""# {GAME_NAME} 舆情监控报告

**生成时间**: {timestamp.strftime('%Y-%m-%d %H:%M')} (Asia/Shanghai)  
**监控周期**: 过去 1 小时

---

## 早期预警

| 指标 | 数�?| 状�?|
|------|------|------|
| 预警级别 | {alert_emoji.get(alert, '�?)} {alert.upper()} | - |
| 叙事凝聚�?| {narrative.get('narrative_cohesion', 'N/A')} | - |
| 数据总量 | {narrative.get('total_records', 0)} �?| - |

**AI 评估**: {narrative.get('ai_assessment', '暂无')}

**建议行动**: {narrative.get('recommended_action', '保持监控')}

---

## 叙事变化对比 (vs 上一小时)

"""
    
    new = narrative.get('new_topics', [])
    if new:
        md += f"**新出现议�?*: {', '.join(new[:5])}\n\n"
    
    rising = narrative.get('rising_topics', [])
    if rising:
        md += "**热度上升**:\n"
        for r in rising[:5]:
            md += f"- {r['topic']} ({r['change']})\n"
        md += "\n"
    
    falling = narrative.get('falling_topics', [])
    if falling:
        md += "**热度下降**:\n"
        for f in falling[:5]:
            md += f"- {f['topic']} ({f['change']})\n"
        md += "\n"
    
    md += "---\n\n## 数据来源状态\n\n"
    
    for platform, result in platform_results.items():
        count = result.get('count', 0)
        method = result.get('method', 'unknown')
        crawl_ok = result.get('crawl_success', False)
        emoji = "�? if crawl_ok else "⚠️"
        md += f"- {emoji} **{platform.upper()}**: {count} �?[{method}]\n"
    
    md += f"\n**总计**: {narrative.get('total_records', 0)} 条\n"
    
    md += """
---

*本报告由 CoPaw 舆情监控系统自动生成*
"""
    
    return md


def publish_to_feishu(title: str, content: str) -> Dict:
    script_path = FEISHU_DIR / "scripts" / "publish.py"
    
    if not script_path.exists():
        return {"error": "Script not found"}
    
    try:
        cmd = ["python", str(script_path), "--title", title, "--content", content]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='ignore')
        
        try:
            return json.loads(result.stdout)
        except:
            return {"error": result.stderr or result.stdout}
    except Exception as e:
        return {"error": str(e)}


def main():
    log("=" * 50)
    log(f"开始执�?{GAME_NAME} 舆情监控任务")
    log("=" * 50)
    
    timestamp = datetime.now()
    
    # Phase 1: 爬取/加载数据
    log("Phase 1: 爬取/加载数据")
    platform_results = {}
    all_records = {}
    
    for platform in PLATFORMS:
        # 先尝试实时爬�?        crawl_success = try_crawl_platform(platform, limit=50)
        
        # 然后加载数据（无论爬取成功与否）
        records = load_merged_data(platform)
        freshness = check_data_freshness(platform)
        
        if crawl_success:
            method = "实时"
        else:
            method = f"缓存({freshness.get('hours_old', '?')}h�?"
        
        platform_results[platform] = {
            "status": "success" if records else "failed",
            "count": len(records),
            "freshness": freshness,
            "crawl_success": crawl_success,
            "method": method
        }
        all_records[platform] = records
        
        log(f"  {platform}: {len(records)} �?[{method}]")
    
    # Phase 2: 叙事分析
    log("Phase 2: 叙事分析")
    previous = load_previous_snapshot()
    narrative = analyze_narrative_shift(all_records, previous)
    
    log(f"  预警级别: {narrative['alert_level'].upper()}")
    log(f"  新议�? {len(narrative['new_topics'])} �?)
    
    # 保存快照
    snapshot_data = {
        "timestamp": timestamp.isoformat(),
        "topics": narrative.get("topics", {}),
        "records_summary": {p: len(r) for p, r in all_records.items()}
    }
    save_snapshot(snapshot_data)
    
    # Phase 3: 生成报告
    log("Phase 3: 生成报告")
    report_md = generate_report(platform_results, narrative, timestamp)
    
    report_file = REPORT_DIR / f"report_{timestamp.strftime('%Y%m%d_%H%M')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_md)
    log(f"  报告已保�? {report_file.name}")
    
    # Phase 4: 飞书推�?    log("Phase 4: 飞书推�?)
    title = f"{GAME_NAME} 舆情监控 - {timestamp.strftime('%m-%d %H:%M')}"
    result = publish_to_feishu(title, report_md)
    
    if 'url' in result:
        log(f"  推送成�? {result['url']}")
    else:
        log(f"  推送失�? {result.get('error', 'Unknown')}")
    
    log("=" * 50)
    log("任务完成")
    log("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
