# 平台选择策略

## 决策流程

```
用户请求抓取
    ↓
游戏是否已注册？
    ↓ 是
读取 game_registry.json 中的平台配置
    ↓
用户是否指定平台？
    ↓ 否
根据游戏类型选择默认平台
```

## 游戏类型判断

### 1. 国内手游

**特征：**
- 主要在 TapTap、App Store 中国区、各大安卓商店发行
- 中文名为主，可能有英文名但搜索量低
- 社区主要在 B站、TapTap

**选择平台：**
- ✅ taptap（评价、帖子）
- ✅ bilibili（视频、评论）
- ❌ reddit（除非有海外发行）
- ❌ youtube（除非有海外发行）

### 2. 海外手游

**特征：**
- 主要在 App Store、Google Play 发行
- 英文名为主
- 社区主要在 Reddit、YouTube

**选择平台：**
- ❌ taptap（除非有国服）
- ❌ bilibili（除非有国内热度）
- ✅ reddit（讨论、评价）
- ✅ youtube（视频、评测）

### 3. 全球热门游戏

**特征：**
- 多地区同步发行
- 中英文都有热度
- 全球社区活跃

**选择平台：**
- ✅ taptap（国内社区）
- ✅ bilibili（国内视频）
- ✅ reddit（海外讨论）
- ✅ youtube（海外视频）

### 4. 独立游戏

**特征：**
- Steam 发行为主
- 小众但社区忠诚度高
- Reddit 讨论质量高

**选择平台：**
- ❌ taptap（通常没有）
- ⚠️ bilibili（可能有少量视频）
- ✅ reddit（核心社区）
- ✅ youtube（评测、实况）

## 平台优先级

当资源有限时，按优先级选择：

| 游戏类型 | P0（必选） | P1（推荐） | P2（可选） |
|---------|-----------|-----------|-----------|
| 国内手游 | taptap | bilibili | - |
| 海外手游 | reddit | youtube | - |
| 全球热门 | taptap, reddit | bilibili, youtube | - |
| 独立游戏 | reddit | youtube | bilibili |

## 数据新鲜度检查

在执行抓取前，检查现有数据：

```python
def should_skip_platform(game_id: str, platform: str, force: bool = False) -> bool:
    """
    判断是否应该跳过该平台
    
    规则：
    - force=True: 不跳过
    - 数据 < 7 天: 跳过（太新）
    - 数据 7-30 天: 询问用户
    - 数据 > 30 天 or 无数据: 不跳过
    """
    if force:
        return False
    
    data_age = get_data_age(game_id, platform)
    
    if data_age is None:
        return False  # 无数据，需要抓取
    
    if data_age < 7:
        return True  # 数据太新，跳过
    
    return False  # 需要更新
```

## 关键词生成

每个平台的搜索关键词：

| 平台 | 关键词格式 | 示例 |
|------|-----------|------|
| taptap | 游戏中文名 | "原神" |
| bilibili | 游戏中文名 + 类型词 | "原神 评测", "原神 攻略" |
| reddit | 游戏英文名 or 缩写 | "Genshin Impact", "Genshin" |
| youtube | 游戏英文名 + 类型词 | "Genshin Impact review" |

## 特殊情况处理

### 多语言游戏

如果游戏有多语言版本：
- 优先抓取用户指定的语言
- 默认抓取英文（覆盖面最广）
- 国内游戏额外抓取中文

### 游戏更名

如果游戏有多个名称（如测试期名称 vs 正式名称）：
- 使用 game_registry.json 中的 aliases
- 分别搜索每个别名
- 合并结果时去重

### 平台独占

如果游戏是某平台独占：
- 只抓取该平台的社区
- 其他平台可能有少量讨论，但非核心
