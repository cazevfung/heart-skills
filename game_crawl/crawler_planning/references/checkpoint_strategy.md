# Checkpoint 策略

## 核心原则

**频繁保存，快速恢复，不丢数据。**

## Checkpoint 机制

### 保存时机

| 场景 | 保存频率 | 说明 |
|------|---------|------|
| 正常抓取 | 每 10-20 条数据 | 或每 60 秒 |
| 滚动加载 | 每 3-5 次滚动 | 避免内存溢出 |
| API 分页 | 每页结束 | 便于从页码恢复 |
| 任务完成 | 立即保存 | 最终数据 |

### 保存位置

```
data/game_data/games/{game_id}/checkpoints/
├── {platform}_{data_type}_checkpoint_1.json
├── {platform}_{data_type}_checkpoint_2.json
└── {platform}_{data_type}_checkpoint_3.json
```

### 文件格式

```json
{
  "checkpoint_id": 3,
  "platform": "taptap",
  "data_type": "review",
  "game_id": "g_genshin",
  "saved_at": "2026-03-19T15:30:00Z",
  "items": [
    {"id": "review_001", "author": "...", "content": "..."}
  ],
  "progress": {
    "current": 35,
    "total": 50,
    "percentage": 70
  },
  "metadata": {
    "last_page": 3,
    "last_scroll_position": 1500,
    "next_url": "..."
  }
}
```

## 恢复机制

### 自动恢复

脚本启动时检查 checkpoint：

```python
def auto_resume(game_id: str, platform: str, data_type: str) -> tuple[bool, list]:
    """
    自动从 checkpoint 恢复
    
    返回: (是否恢复成功, 已抓取的数据)
    """
    storage = DataStorage(game_id)
    latest = storage.get_latest_checkpoint(platform, data_type)
    
    if latest == 0:
        return False, []  # 无 checkpoint
    
    checkpoint = storage.load_checkpoint(latest, platform, data_type)
    items = checkpoint.get("items", [])
    
    print(f"从 checkpoint {latest} 恢复，已有 {len(items)} 条数据")
    return True, items
```

### 手动恢复

用户显式指定 `--resume`：

```bash
python taptap_review.py --game-id g_genshin --resume
```

## 清理策略

### 自动清理

任务完成后，保留最近 3 个 checkpoint：

```python
def clean_old_checkpoints(game_id: str, platform: str, data_type: str, keep: int = 3):
    """清理旧 checkpoint"""
    storage = DataStorage(game_id)
    storage.clean_checkpoints(keep_latest=keep)
```

### 手动清理

批量清理所有游戏的 checkpoint：

```bash
python scripts/clean_checkpoints.py --keep 3 --older-than 7days
```

## 数据合并

### 合并策略

新数据与 checkpoint 数据合并：

```python
def merge_with_checkpoint(new_items: list, checkpoint_items: list, id_field: str = "id") -> list:
    """
    合并新数据和 checkpoint 数据
    
    策略：新数据覆盖旧数据（如果 ID 相同）
    """
    item_map = {item[id_field]: item for item in checkpoint_items if id_field in item}
    
    for item in new_items:
        if id_field in item:
            item_map[item[id_field]] = item
    
    return list(item_map.values())
```

### 去重规则

| 数据类型 | 去重字段 | 说明 |
|---------|---------|------|
| review | author + content_hash | 同一用户的相似评价 |
| comment | id | 评论唯一 ID |
| post | id | 帖子唯一 ID |
| video | bvid / video_id | 视频唯一 ID |

## 最佳实践

### 1. 频繁保存

长任务（> 5 分钟）必须启用 checkpoint：

```python
# 每 10 条保存一次
if len(items) % 10 == 0:
    storage.save_checkpoint(
        {"items": items, "progress": progress},
        batch_num=len(items) // 10,
        platform="taptap",
        data_type="review"
    )
```

### 2. 原子性保存

先写临时文件，再重命名，避免写入中断导致文件损坏：

```python
def atomic_save(data: dict, filepath: Path):
    """原子性保存文件"""
    temp_file = filepath.with_suffix('.tmp')
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    temp_file.replace(filepath)  # 原子性重命名
```

### 3. 验证完整性

加载 checkpoint 时验证数据完整性：

```python
def validate_checkpoint(checkpoint: dict) -> bool:
    """验证 checkpoint 是否完整"""
    required_fields = ["checkpoint_id", "platform", "data_type", "items"]
    
    for field in required_fields:
        if field not in checkpoint:
            print(f"Checkpoint 缺少字段: {field}")
            return False
    
    if not isinstance(checkpoint["items"], list):
        print("Checkpoint items 不是列表")
        return False
    
    return True
```

### 4. 错误恢复

抓取失败时，保存当前进度：

```python
try:
    # 抓取逻辑
    items = fetch_data(...)
except Exception as e:
    # 保存当前进度
    storage.save_checkpoint(
        {"items": items, "error": str(e)},
        batch_num=999,  # 特殊标记：错误 checkpoint
        platform=platform,
        data_type=data_type
    )
    raise
```

## 监控与报警

### Checkpoint 状态检查

```python
def check_checkpoint_health(game_id: str) -> dict:
    """检查 checkpoint 健康状态"""
    storage = DataStorage(game_id)
    checkpoints = list(storage.checkpoint_dir.glob("*checkpoint_*.json"))
    
    return {
        "total_checkpoints": len(checkpoints),
        "total_size_mb": sum(cp.stat().st_size for cp in checkpoints) / 1024 / 1024,
        "oldest_checkpoint": min(cp.stat().st_mtime for cp in checkpoints) if checkpoints else None,
        "latest_checkpoint": max(cp.stat().st_mtime for cp in checkpoints) if checkpoints else None
    }
```

### 磁盘空间预警

当 checkpoint 目录超过 1GB 时报警：

```python
import shutil

def check_disk_space(path: Path, threshold_gb: float = 1.0) -> bool:
    """检查磁盘空间"""
    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    total_gb = total_size / 1024 / 1024 / 1024
    
    if total_gb > threshold_gb:
        print(f"⚠️ Checkpoint 目录超过 {threshold_gb}GB: {total_gb:.2f}GB")
        return False
    
    return True
```

---

_频繁保存，安心抓取。_
