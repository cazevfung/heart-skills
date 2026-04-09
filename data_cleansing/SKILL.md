# Data Cleansing Skill

## 用途

清理游戏数据仓库中的无效、重复、损坏数据，确保数据质量。

## 核心功能

1. **扫描 (Scan)** - 发现潜在问题
   - 孤儿文件夹（未在 registry 中注册）
   - 空文件/空数组
   - 损坏的 JSON
   - game_id 不匹配
   - 重复数据

2. **分析 (Analyze)** - 判断处理方式
   - 读取样本确认内容
   - 判断数据有效性
   - 决定保留/删除/合并

3. **清理 (Clean)** - 执行修复
   - 删除无效文件
   - 合并重复数据
   - 修复 game_id
   - 更新 registry

4. **验证 (Verify)** - 确认结果
   - 最终扫描确认干净
   - 生成清理报告

## 使用方式

```bash
# 扫描并生成报告（不执行清理）
python scripts/cleaner.py --action scan

# 交互式清理（每个操作前确认）
python scripts/cleaner.py --action clean --interactive

# 自动清理（无需确认，谨慎使用）
python scripts/cleaner.py --action clean --auto

# 指定数据目录
python scripts/cleaner.py --data-dir "D:\custom\path"
```

## 配置

编辑 `config/rules.json` 自定义清理规则：

```json
{
  "empty_file_threshold": 0,
  "min_items_count": 1,
  "allowed_test_prefixes": ["test_", "g_test"],
  "required_fields": ["game_id"],
  "array_fields": ["items", "videos", "transcripts", "posts"]
}
```

## 输出

清理完成后生成 `cleansing_report.json`：

```json
{
  "timestamp": "2026-03-20T16:00:00",
  "stats": {
    "total_files": 421,
    "issues_found": 12,
    "issues_fixed": 12
  },
  "actions": [
    {"type": "delete", "file": "g_test/empty.json", "reason": "empty"},
    {"type": "merge", "from": "g_hsr", "to": "g_starrail"},
    {"type": "fix", "file": "g_sos/transcripts.json", "field": "game_id"}
  ]
}
```

## 注意事项

- 首次使用建议先 `--action scan` 查看问题
- 重要数据清理前建议备份
- 合并操作不可逆，谨慎使用 `--auto`
