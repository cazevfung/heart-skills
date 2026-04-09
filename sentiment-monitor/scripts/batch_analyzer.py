#!/usr/bin/env python3
"""
批量分析多个评论数据集
生成综合报告
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加scripts目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from regional_toxicity_analyzer import RegionalToxicityAnalyzer


def analyze_multiple_batches(data_dir: str, region: str = "zh-CN"):
    """分析多个数据批次并生成综合报告"""
    
    data_path = Path(data_dir)
    all_results = []
    
    # 查找所有JSON文件
    json_files = sorted(data_path.glob("heartopia_batch_*.json"))
    
    print(f"Found {len(json_files)} batch files to analyze")
    
    analyzer = RegionalToxicityAnalyzer(region, auto_evolve=False)
    
    for json_file in json_files:
        print(f"\nAnalyzing: {json_file.name}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            comments = json.load(f)
        
        result = analyzer.analyze(comments)
        result['batch_name'] = json_file.name
        result['comment_count'] = len(comments)
        
        all_results.append(result)
        
        print(f"  Toxicity Score: {result['toxicity_score']:.2f}")
        print(f"  Level: {result['toxicity_level']}")
        print(f"  Comments: {len(comments)}")
    
    # 生成综合报告
    report = generate_comprehensive_report(all_results)
    
    return report


def generate_comprehensive_report(results: list) -> dict:
    """生成综合报告"""
    
    if not results:
        return {"error": "No results to report"}
    
    # 计算平均毒性评分
    avg_toxicity = sum(r['toxicity_score'] for r in results) / len(results)
    
    # 统计各等级数量
    level_counts = {}
    for r in results:
        level = r['toxicity_level']
        level_counts[level] = level_counts.get(level, 0) + 1
    
    # 找出最高毒性批次
    max_toxicity = max(results, key=lambda x: x['toxicity_score'])
    
    # 统计总评论数
    total_comments = sum(r['comment_count'] for r in results)
    
    # 统计主导叙事
    motif_counts = {}
    for r in results:
        dominant = r['narrative_analysis'].get('dominant_motif', {}).get('id', 'unknown')
        motif_counts[dominant] = motif_counts.get(dominant, 0) + 1
    
    # 统计回声室效应
    echo_chamber_count = sum(1 for r in results if r['emotion_analysis'].get('is_echo_chamber', False))
    
    report = {
        "analysis_timestamp": datetime.now().isoformat(),
        "total_batches": len(results),
        "total_comments": total_comments,
        "summary": {
            "average_toxicity_score": round(avg_toxicity, 2),
            "toxicity_level_distribution": level_counts,
            "dominant_narratives": motif_counts,
            "echo_chamber_batches": echo_chamber_count,
            "highest_toxicity": {
                "batch": max_toxicity['batch_name'],
                "score": max_toxicity['toxicity_score'],
                "level": max_toxicity['toxicity_level']
            }
        },
        "batch_details": results,
        "recommendations": generate_recommendations(avg_toxicity, level_counts, motif_counts)
    }
    
    return report


def generate_recommendations(avg_toxicity: float, level_counts: dict, motif_counts: dict) -> list:
    """生成干预建议"""
    
    recommendations = []
    
    if avg_toxicity > 0.7:
        recommendations.append({
            "priority": "critical",
            "action": "立即暂停公开回应，通过侧翼渠道沟通",
            "reason": f"平均毒性评分{avg_toxicity:.2f}处于危急水平"
        })
    elif avg_toxicity > 0.5:
        recommendations.append({
            "priority": "high",
            "action": "主动沟通，打断叙事垄断",
            "reason": f"平均毒性评分{avg_toxicity:.2f}处于中度水平"
        })
    elif avg_toxicity > 0.3:
        recommendations.append({
            "priority": "medium",
            "action": "关注情绪聚集点，准备预案",
            "reason": f"平均毒性评分{avg_toxicity:.2f}处于轻度水平"
        })
    else:
        recommendations.append({
            "priority": "low",
            "action": "维持现状，定期监控",
            "reason": f"平均毒性评分{avg_toxicity:.2f}处于健康水平"
        })
    
    # 基于主导叙事的建议
    if motif_counts.get('nationalism', 0) > 0:
        recommendations.append({
            "priority": "high",
            "action": "针对民族主义叙事，提供透明数据对比，避免对立情绪升级",
            "reason": "检测到民族主义叙事"
        })
    
    if motif_counts.get('betrayal_core_players', 0) > 0:
        recommendations.append({
            "priority": "high",
            "action": "针对核心玩家背叛感，承认情感真实性，提供具体补偿方案",
            "reason": "检测到核心玩家背叛叙事"
        })
    
    if motif_counts.get('technical_debt', 0) > 0:
        recommendations.append({
            "priority": "medium",
            "action": "针对技术问题，提供详细修复时间表，增加透明度",
            "reason": "检测到技术债务叙事"
        })
    
    return recommendations


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch analyze sentiment data")
    parser.add_argument("--data-dir", default="../test_data", help="Directory containing batch JSON files")
    parser.add_argument("--region", default="zh-CN", help="Region code")
    parser.add_argument("--output", "-o", help="Output report file")
    
    args = parser.parse_args()
    
    report = analyze_multiple_batches(args.data_dir, args.region)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nReport saved to: {args.output}")
    else:
        print("\n" + "="*60)
        print("COMPREHENSIVE ANALYSIS REPORT")
        print("="*60)
        print(json.dumps(report['summary'], ensure_ascii=False, indent=2))
        print("\nRECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. [{rec['priority'].upper()}] {rec['action']}")
            print(f"   Reason: {rec['reason']}")


if __name__ == "__main__":
    main()
