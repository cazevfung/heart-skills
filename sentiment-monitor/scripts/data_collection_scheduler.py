#!/usr/bin/env python3
"""
批量数据采集任务调度器
支持多游戏、多批次、增量更新

Usage:
    python data_collection_scheduler.py --config collection_config.json
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import subprocess


class DataCollectionScheduler:
    """数据采集调度器"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.output_base = Path(self.config.get('output_base', './collected_data'))
        self.output_base.mkdir(parents=True, exist_ok=True)
        
    def run_collection(self):
        """运行采集任务"""
        print("="*60)
        print("DATA COLLECTION SCHEDULER")
        print("="*60)
        print(f"Start time: {datetime.now().isoformat()}")
        print(f"Total games: {len(self.config['games'])}")
        print()
        
        results = []
        
        for game_config in self.config['games']:
            result = self._collect_game(game_config)
            results.append(result)
            
            # 游戏间延迟
            delay = self.config.get('delay_between_games', 30)
            print(f"[Delay] Waiting {delay}s before next game...")
            time.sleep(delay)
        
        # 生成汇总报告
        self._generate_summary_report(results)
        
        print()
        print("="*60)
        print("COLLECTION COMPLETE")
        print("="*60)
    
    def _collect_game(self, game_config: Dict) -> Dict:
        """采集单个游戏的数据"""
        game_name = game_config['name']
        app_id = game_config['app_id']
        
        print(f"\n[Game] {game_name} (app_id: {app_id})")
        print("-" * 60)
        
        output_dir = self.output_base / game_name
        output_dir.mkdir(exist_ok=True)
        
        result = {
            "game_name": game_name,
            "app_id": app_id,
            "start_time": datetime.now().isoformat(),
            "batches": []
        }
        
        # 根据策略执行采集
        strategy = game_config.get('strategy', 'full')
        
        if strategy == 'full':
            # 完整采集
            batch_result = self._run_full_collection(app_id, output_dir, game_config)
            result['batches'].append(batch_result)
            
        elif strategy == 'incremental':
            # 增量采集
            batches = game_config.get('batches', [])
            for batch_config in batches:
                batch_result = self._run_incremental_collection(
                    app_id, output_dir, batch_config
                )
                result['batches'].append(batch_result)
                
                delay = self.config.get('delay_between_batches', 10)
                print(f"[Delay] Waiting {delay}s before next batch...")
                time.sleep(delay)
        
        result['end_time'] = datetime.now().isoformat()
        
        # 保存游戏采集结果
        result_file = output_dir / f"collection_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"[Result] Saved to {result_file}")
        
        return result
    
    def _run_full_collection(self, app_id: str, output_dir: Path, config: Dict) -> Dict:
        """运行完整采集"""
        print("[Mode] Full collection")
        
        days = config.get('days_back', 365)
        limit = config.get('post_limit', 500)
        
        cmd = [
            sys.executable,
            "taptap_enhanced.py",
            "--app-id", app_id,
            "--mode", "full",
            "--days", str(days),
            "--limit", str(limit),
            "--output-dir", str(output_dir)
        ]
        
        print(f"[Command] {' '.join(cmd)}")
        
        start_time = datetime.now()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=3600  # 1小时超时
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "type": "full",
                "days_back": days,
                "post_limit": limit,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout[-1000:] if result.stdout else "",  # 最后1000字符
                "stderr": result.stderr[-1000:] if result.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "type": "full",
                "status": "timeout",
                "error": "Collection timed out after 1 hour"
            }
        except Exception as e:
            return {
                "type": "full",
                "status": "error",
                "error": str(e)
            }
    
    def _run_incremental_collection(self, app_id: str, output_dir: Path, batch_config: Dict) -> Dict:
        """运行增量采集"""
        print(f"[Mode] Incremental collection: {batch_config.get('name', 'unnamed')}")
        
        since = batch_config.get('since')
        until = batch_config.get('until')
        limit = batch_config.get('limit', 100)
        
        # 构建命令
        cmd = [
            sys.executable,
            "taptap_enhanced.py",
            "--app-id", app_id,
            "--mode", "list",
            "--limit", str(limit),
            "--output-dir", str(output_dir)
        ]
        
        if since:
            # 计算天数
            since_date = datetime.fromisoformat(since)
            days_back = (datetime.now() - since_date).days
            cmd.extend(["--days", str(days_back)])
        
        print(f"[Command] {' '.join(cmd)}")
        
        start_time = datetime.now()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=1800  # 30分钟超时
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "type": "incremental",
                "batch_name": batch_config.get('name', 'unnamed'),
                "since": since,
                "until": until,
                "limit": limit,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "status": "success" if result.returncode == 0 else "failed"
            }
            
        except Exception as e:
            return {
                "type": "incremental",
                "batch_name": batch_config.get('name', 'unnamed'),
                "status": "error",
                "error": str(e)
            }
    
    def _generate_summary_report(self, results: List[Dict]):
        """生成汇总报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_games": len(results),
            "successful_collections": sum(1 for r in results if all(b.get('status') == 'success' for b in r.get('batches', []))),
            "failed_collections": sum(1 for r in results if any(b.get('status') != 'success' for b in r.get('batches', []))),
            "game_results": results
        }
        
        report_file = self.output_base / f"collection_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n[Summary Report] Saved to {report_file}")
        print(f"  Total games: {report['total_games']}")
        print(f"  Successful: {report['successful_collections']}")
        print(f"  Failed: {report['failed_collections']}")


def create_sample_config():
    """创建示例配置文件"""
    config = {
        "output_base": "./collected_data",
        "delay_between_games": 30,
        "delay_between_batches": 10,
        "games": [
            {
                "name": "heartopia",
                "app_id": "45213",
                "strategy": "full",
                "days_back": 365,
                "post_limit": 500
            }
        ]
    }
    
    with open('collection_config_sample.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("Created sample config: collection_config_sample.json")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Collection Scheduler")
    parser.add_argument("--config", help="Path to config JSON file")
    parser.add_argument("--create-sample", action="store_true", help="Create sample config file")
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_config()
        return
    
    if not args.config:
        parser.error("--config required (or use --create-sample to generate example)")
    
    scheduler = DataCollectionScheduler(args.config)
    scheduler.run_collection()


if __name__ == "__main__":
    main()
