#!/usr/bin/env python3
"""
心动小镇每小时舆情监控任务 - 使用现有数据版本
- 分析现有 TapTap、Reddit、YouTube 数据
- 生成叙事变化报告并推送到飞书
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

# 配置
GAME_ID = "heartopia"
GAME_NAME = "心动小镇"
PLATFORMS = ["taptap", "reddit", "youtube"]

# 路径配置
SKILL_DIR = Path("d:/App Dev/openclaw-main/skills")
FEISHU_DIR = SKILL_DIR / "feishu-doc"
DATA_ROOT = Path("d:/App Dev/openclaw-main/data/game_data")
SNAPSHOT_DIR = DATA_ROOT / "sentiment_snapshots" / GAME_ID
REPORT_DIR = DATA_ROOT / "sentiment_reports" / GAME_ID

# 确保目录存在
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    """打印日志"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    try:
        print(f"[{timestamp}] {msg}")
    except UnicodeEncodeError:
        print(f"[{timestamp}] {msg.encode('gbk', errors='ignore').decode('gbk')}")


def load_merged_data(platform: str) -> List[Dict]:
    """从 merged 目录加载已合并的数据"""
    if platform == "youtube":
        merged_path = DATA_ROOT / "merged" / platform / GAME_ID / "videos" / "data.json"
    else:
        merged_path = DATA_ROOT / "merged" / platform / GAME_ID / "forum_posts" / "data.json"
    
    if not merged_path.exists():
        log(f"  {platform} 数据文件不存在")
        return []
    
    try:
        with open(merged_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if platform == "youtube":
                return data.get("videos", [])
            elif platform == "reddit":
                return data.get("posts", [])
            else:
                return data.get("posts", [])
    except Exception as e:
        log(f"  读取 {platform} 数据失败: {e}")
        return []


def extract_topics(records: List[Dict]) -> Dict:
    """提取主题和热点"""
    topics = {}
    
    # 关键词映射
    keyword_map = {
        "活动": ["活动", "event", "奖励", "reward", "体力"],
        "抽卡": ["抽卡", "gacha", "保底", "概率", "池子"],
        "bug": ["bug", "闪退", "卡顿", "crash", "错误"],
        "运营": ["运营", "官方", "客服", "communication", "策划"],
        "氪金": ["氪金", "付费", "充值", "pay", "price", "太贵"],
        "玩法": ["玩法", "内容", "关卡", "gameplay", "任务"],
        "社交": ["社交", "好友", "公会", "social", "联机"],
        "更新": ["更新", "版本", "延期", "update", "patch", "维护"]
    }
    
    for record in records:
        content = (record.get("body", "") + " " + record.get("title", "") + " " + record.get("content", "")).lower()
        
        for topic, keywords in keyword_map.items():
            if any(kw in content for kw in keywords):
                if topic not in topics:
                    topics[topic] = {"count": 0, "heat": 0}
                topics[topic]["count"] += 1
                # 热度 = 点赞 + 回复*2
                heat = record.get("score", 0) + record.get("likes", 0) + record.get("replies_count", 0) * 2 + record.get("upvotes", 0)
                topics[topic]["heat"] += heat
    
    return topics


def load_previous_snapshot() -> Optional[Dict]:
    """加载最近的小时级快照"""
    snapshots = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    for snap in snapshots[:3]:
        try:
            with open(snap, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            continue
    return None


def save_snapshot(data: Dict):
    """保存当前快照"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    snap_path = SNAPSHOT_DIR / f"snapshot_{timestamp}.json"
    with open(snap_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log(f"  快照已保存: {snap_path.name}")
    return snap_path


def analyze_narrative_shift(current_records: Dict[str, List[Dict]], previous_snapshot: Optional[Dict]) -> Dict:
    """分析叙事变化"""
    
    # 提取当前主题
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
            "toxicity_momentum": 0.0,
            "new_topics": list(current_topics.keys()),
            "rising_topics": [],
            "falling_topics": [],
            "ai_assessment": "首次分析，建立基线",
            "recommended_action": "继续监控",
            "total_records": total_current
        }
    
    # 提取历史主题
    prev_topics = previous_snapshot.get("topics", {})
    
    # 检测新议题
    new_topics = list(set(current_topics.keys()) - set(prev_topics.keys()))
    
    # 检测热度变化
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
    
    # 按热度排序
    rising.sort(key=lambda x: float(x["change"].replace('%', '').replace('+', '')), reverse=True)
    
    # 计算预警级别
    alert_level = "green"
    if len(new_topics) >= 2 or len(rising) >= 2:
        alert_level = "yellow"
    if len(new_topics) >= 4 or any(r["topic"] in ["运营", "氪金", "bug"] for r in rising):
        alert_level = "red"
    
    # 生成评估文本
    assessment_parts = []
    if new_topics:
        assessment_parts.append(f"新出现议题: {', '.join(new_topics[:3])}")
    if rising:
        assessment_parts.append(f"热度上升: {', '.join(r['topic'] for r in rising[:2])}")
    if not assessment_parts:
        assessment_parts.append("舆情场域相对稳定")
    
    # 建议行动
    if alert_level == "red":
        action = "建议 2 小时内官方回应"
    elif alert_level == "yellow":
        action = "建议 6 小时内关注并准备回应素材"
    else:
        action = "保持常规监控"
    
    return {
        "alert_level": alert_level,
        "narrative_cohesion": round(max(t["count"] for t in current_topics.values()) / sum(t["count"] for t in current_topics.values()), 2) if current_topics else 0,
        "toxicity_momentum": 0.0,
        "new_topics": new_topics,
        "rising_topics": rising,
        "falling_topics": falling,
        "ai_assessment": "；".join(assessment_parts),
        "recommended_action": action,
        "total_records": total_current,
        "topics": current_topics
    }


def generate_report(all_records: Dict[str, List[Dict]], narrative: Dict, timestamp: datetime) -> str:
    """生成 Markdown 报告"""
    
    alert_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    alert = narrative.get("alert_level", "green")
    
    # 统计各平台数据
    platform_stats = {}
    for platform, records in all_records.items():
        platform_stats[platform] = len(records)
    
    md = f"""# 📊 {GAME_NAME} 舆情监控报告

**生成时间**: {timestamp.strftime('%Y-%m-%d %H:%M')} (Asia/Shanghai)  
**监控周期**: 基于现有数据分析

---

## 🚨 早期预警

| 指标 | 数值 | 状态 |
|------|------|------|
| 预警级别 | {alert_emoji.get(alert, '⚪')} {alert.upper()} | - |
| 叙事凝聚度 | {narrative.get('narrative_cohesion', 'N/A')} | - |
| 数据总量 | {narrative.get('total_records', 0)} 条 | - |

**AI 评估**: {narrative.get('ai_assessment', '暂无')}

**建议行动**: {narrative.get('recommended_action', '保持监控')}

---

## 📈 叙事分析

### 平台数据分布

"""
    
    for platform, count in platform_stats.items():
        md += f"- **{platform.upper()}**: {count} 条记录\n"
    
    md += "\n### 主题热度分布\n\n"
    
    topics = narrative.get('topics', {})
    if topics:
        md += "| 主题 | 提及次数 | 热度值 |\n"
        md += "|------|---------|--------|\n"
        sorted_topics = sorted(topics.items(), key=lambda x: x[1]['heat'], reverse=True)
        for topic, data in sorted_topics[:10]:
            md += f"| {topic} | {data['count']} | {data['heat']} |\n"
    else:
        md += "暂无主题数据\n"
    
    new = narrative.get('new_topics', [])
    if new:
        md += f"\n**🆕 新出现议题**: {', '.join(new[:5])}\n"
    
    rising = narrative.get('rising_topics', [])
    if rising:
        md += "\n**📈 热度上升**:\n"
        for r in rising[:5]:
            md += f"- {r['topic']} ({r['change']})\n"
    
    falling = narrative.get('falling_topics', [])
    if falling:
        md += "\n**📉 热度下降**:\n"
        for f in falling[:5]:
            md += f"- {f['topic']} ({f['change']})\n"
    
    md += """
---

## 📡 数据来源状态

"""
    
    for platform in PLATFORMS:
        count = platform_stats.get(platform, 0)
        status = "✅ 有数据" if count > 0 else "⚠️ 无数据"
        md += f"{status} **{platform.upper()}**: {count} 条\n"
    
    md += f"\n**总计数据**: {narrative.get('total_records', 0)} 条\n"
    
    md += """
---

## 📝 关键发现

"""
    
    # 基于数据分析生成发现
    findings = []
    
    # 检查Reddit投诉帖
    reddit_records = all_records.get('reddit', [])
    complaint_posts = [r for r in reddit_records if 'complaint' in r.get('title', '').lower() or 'call out' in r.get('title', '').lower()]
    if complaint_posts:
        findings.append(f"- Reddit 存在投诉集中帖: '{complaint_posts[0].get('title', '')}' ({complaint_posts[0].get('score', 0)} upvotes)")
    
    # 检查高热度评论
    all_comments = []
    for record in reddit_records:
        for comment in record.get('comments', []):
            all_comments.append(comment)
    
    if all_comments:
        top_comment = max(all_comments, key=lambda x: x.get('score', 0))
        findings.append(f"- Reddit 高赞评论关注: {top_comment.get('body', '')[:50]}... ({top_comment.get('score', 0)} upvotes)")
    
    if findings:
        md += "\n".join(findings)
    else:
        md += "暂无特别突出的舆情信号"
    
    md += """

---

*本报告由 CoPaw 舆情监控系统自动生成*
*数据来源: TapTap, Reddit, YouTube (现有数据快照)*
"""
    
    return md


def publish_to_feishu(title: str, content: str) -> Dict:
    """发布到飞书文档"""
    script_path = FEISHU_DIR / "scripts" / "publish.py"
    
    if not script_path.exists():
        log(f"  警告: 飞书发布脚本不存在: {script_path}")
        return {"error": "Script not found"}
    
    try:
        # 写入临时文件
        temp_file = REPORT_DIR / "temp_publish.md"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        cmd = [
            "python", str(script_path),
            "--title", title,
            "--file", str(temp_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='ignore')
        
        # 清理临时文件
        temp_file.unlink(missing_ok=True)
        
        try:
            return json.loads(result.stdout)
        except:
            return {"error": result.stderr or result.stdout}
            
    except Exception as e:
        return {"error": str(e)}


def main():
    """主流程"""
    log("=" * 50)
    log(f"开始执行 {GAME_NAME} 舆情监控任务 (基于现有数据)")
    log("=" * 50)
    
    timestamp = datetime.now()
    
    # Phase 1: 加载现有数据
    log("\n[Phase 1] 加载现有数据")
    all_records = {}
    
    for platform in PLATFORMS:
        records = load_merged_data(platform)
        all_records[platform] = records
        log(f"  {platform}: {len(records)} 条记录")
    
    total_records = sum(len(r) for r in all_records.values())
    if total_records == 0:
        log("\n❌ 无可用数据，任务终止")
        return 1
    
    log(f"\n✅ 总计: {total_records} 条记录")
    
    # Phase 2: 叙事分析
    log("\n[Phase 2] 叙事分析")
    previous = load_previous_snapshot()
    if previous:
        log("  已加载历史快照")
    
    narrative = analyze_narrative_shift(all_records, previous)
    log(f"  预警级别: {narrative['alert_level'].upper()}")
    log(f"  主题数: {len(narrative.get('topics', {}))}")
    log(f"  新议题: {len(narrative['new_topics'])} 个")
    log(f"  热度上升: {len(narrative['rising_topics'])} 个")
    
    # 保存快照
    snapshot_data = {
        "timestamp": timestamp.isoformat(),
        "topics": narrative.get("topics", {}),
        "records_summary": {p: len(r) for p, r in all_records.items()}
    }
    save_snapshot(snapshot_data)
    
    # Phase 3: 生成报告
    log("\n[Phase 3] 生成报告")
    report_md = generate_report(all_records, narrative, timestamp)
    
    # 保存本地报告
    report_file = REPORT_DIR / f"report_{timestamp.strftime('%Y%m%d_%H%M')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_md)
    log(f"  报告已保存: {report_file}")
    
    # Phase 4: 飞书推送
    log("\n[Phase 4] 飞书推送")
    title = f"{GAME_NAME} 舆情监控 - {timestamp.strftime('%m-%d %H:%M')}"
    result = publish_to_feishu(title, report_md)
    
    feishu_url = None
    if 'url' in result:
        feishu_url = result['url']
        log(f"  ✅ 推送成功: {feishu_url}")
    else:
        log(f"  ⚠️ 推送失败: {result.get('error', 'Unknown')}")
    
    log("\n" + "=" * 50)
    log("任务完成")
    log("=" * 50)
    
    # 输出结果摘要
    print("\n" + "=" * 50)
    print("执行结果摘要")
    print("=" * 50)
    print(f"\n1. 各平台数据状态:")
    for platform in PLATFORMS:
        count = len(all_records.get(platform, []))
        status = "✅ 成功" if count > 0 else "⚠️ 无数据"
        print(f"   - {platform.upper()}: {status} ({count} 条)")
    
    print(f"\n2. 叙事分析关键发现:")
    print(f"   - 预警级别: {narrative['alert_level'].upper()}")
    print(f"   - AI评估: {narrative['ai_assessment']}")
    print(f"   - 建议行动: {narrative['recommended_action']}")
    
    print(f"\n3. 飞书文档链接:")
    if feishu_url:
        print(f"   {feishu_url}")
    else:
        print(f"   推送失败: {result.get('error', 'Unknown')}")
    
    print(f"\n4. 本地报告路径:")
    print(f"   {report_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
