"""
Reporter Module - 生成清理报告
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


class ReportGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_dir = Path(config["paths"]["base_dir"])
    
    def generate(self, issues: List[Dict[str, Any]], actions: List[Dict[str, Any]]) -> str:
        """生成清理报告"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "base_dir": str(self.base_dir),
                "registry": self.config["paths"]["registry"]
            },
            "summary": {
                "total_issues": len(issues),
                "total_actions": len(actions),
                "successful_actions": sum(1 for a in actions if a.get("success", False)),
                "failed_actions": sum(1 for a in actions if not a.get("success", False))
            },
            "issues": issues,
            "actions": actions
        }
        
        # 保存报告
        report_path = self.base_dir.parent / f"cleansing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return str(report_path)
    
    def print_summary(self, actions: List[Dict[str, Any]]):
        """打印操作摘要"""
        if not actions:
            print("\n未执行任何操作")
            return
        
        print("\n" + "=" * 60)
        print("操作摘要")
        print("=" * 60)
        
        action_types = {}
        for action in actions:
            action_type = action["action"]
            if action_type not in action_types:
                action_types[action_type] = {"success": 0, "failed": 0}
            
            if action.get("success", False):
                action_types[action_type]["success"] += 1
            else:
                action_types[action_type]["failed"] += 1
        
        for action_type, counts in action_types.items():
            total = counts["success"] + counts["failed"]
            print(f"  {action_type}: {counts['success']}/{total} 成功")
