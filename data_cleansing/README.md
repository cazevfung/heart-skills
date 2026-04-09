# Data Cleansing Skill

## 概述

游戏数据仓库清理工具，自动化发现并修复数据质量问题。

## 快速开始

```bash
# 1. 扫描问题（只读，安全）
python scripts/cleaner.py --action scan

# 2. 交互式清理（推荐）
python scripts/cleaner.py --action clean --interactive

# 3. 自动清理（谨慎使用）
python scripts/cleaner.py --action clean --auto
```

## 能发现的问题

| 问题类型 | 说明 | 处理方式 |
|---------|------|---------|
| empty_file | 空文件（0字节） | 删除 |
| corrupted_json | 损坏的 JSON | 删除 |
| empty_array | 空数据数组 | 删除 |
| game_id_mismatch | game_id 与文件夹名不匹配 | 修复 |
| orphan_folder | 未注册的文件夹 | 分析后决定 |
| missing_folder | registry 中有但文件夹不存在 | 跳过 |

## 项目结构

```
data_cleansing/
├── SKILL.md              # 使用文档
├── README.md             # 项目说明
├── config/
│   └── rules.json        # 清理规则配置
└── scripts/
    ├── cleaner.py        # 主入口
    ├── scanner.py        # 扫描模块
    ├── validator.py      # 验证模块
    ├── cleaner.py        # 清理模块
    └── reporter.py       # 报告模块
```

## 配置说明

编辑 `config/rules.json`：

```json
{
  "rules": {
    "empty_file": {
      "enabled": true,
      "threshold_bytes": 0
    },
    "empty_arrays": {
      "enabled": true,
      "fields": ["items", "videos", "transcripts"],
      "min_count": 1
    }
  }
}
```

## 报告输出

每次执行后生成 `cleansing_report_YYYYMMDD_HHMMSS.json`：

```json
{
  "timestamp": "2026-03-20T16:00:00",
  "summary": {
    "total_issues": 12,
    "successful_actions": 12
  },
  "issues": [...],
  "actions": [...]
}
```

## 注意事项

1. 首次使用务必先 `--action scan` 查看问题
2. 重要数据清理前备份
3. `--auto` 模式会直接执行，谨慎使用
4. 合并操作不可逆

## 作者

基于 2026-03-20 实际数据清理经验构建
