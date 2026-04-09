# 游戏公告图生成器 v2.0

支持多游戏、配置驱动、主题化生成。

## 快速开始

### 1. 生成图片（心动小镇示例）

```bash
# 基础生成
python scripts/image_generator.py \
  --main-title "新版本上线" \
  --sub-title "全新内容等你体验"

# 指定主题和角色模式
python scripts/image_generator.py \
  --main-title "夏日狂欢" \
  --sub-title "泳装派对开启" \
  --theme summer \
  --character-mode double \
  --n 2

# 自定义角色和场景
python scripts/image_generator.py \
  --main-title "外星来客" \
  --sub-title "全新皮肤上线" \
  --theme alien \
  --character-mode double \
  --character-desc "穿着外星人发光服装，头戴天线" \
  --character-action "兴奋地指向天空中的飞碟" \
  --expression "超级兴奋、眼睛闪闪发光" \
  --scene "小镇夜晚——飞碟悬浮、星光闪烁"
```

### 2. 仅预览 Prompt（不生成图片）

```bash
python scripts/image_generator.py \
  --main-title "测试标题" \
  --sub-title "测试副标题" \
  --theme spring \
  --character-mode single \
  --preview
```

### 3. Python API 调用

```python
from scripts.image_generator import ImageGenerator

# 创建生成器
gen = ImageGenerator(game_key="heartopia")

# 生成图片
result = gen.generate(
    main_title="周年庆典",
    sub_title="感恩有你，共庆周年",
    theme="anniversary",
    character_mode="multiple",
    character_desc="穿着庆典礼服，手持彩带",
    character_action="欢呼庆祝",
    scene_elements="装饰华丽的庆典广场——彩旗飘扬、气球升空",
    n=2
)

print(f"图片已保存: {result['output_paths']}")

# 仅预览 Prompt
prompt = gen.preview_prompt(
    main_title="测试",
    theme="winter",
    character_mode="single"
)
print(prompt)

# 查看可用主题和角色模式
print(gen.list_themes())
print(gen.list_character_modes())
```

---

## 新增游戏

### 1. 复制模板

```bash
cp config/games/_template.json config/games/your_game.json
```

### 2. 创建参考图链接文件

```bash
cp config/refs/_template.txt config/refs/your_game_key.txt
```

编辑 `config/refs/your_game_key.txt`，每行粘贴一个参考图URL：

```
https://example.com/ref1.jpg
https://example.com/ref2.jpg
https://example.com/ref3.png
```

### 3. 编辑游戏配置

修改 `config/games/your_game.json`：

```json
{
  "game_key": "your_game_key",
  "game_name": "你的游戏中文名",
  "game_name_en": "Your Game Name",
  
  "reference_images": {
    "ref_file": "refs/your_game_key.txt"
  },
  
  "visual": {
    "default_style": "announcement_cover",
    "default_theme": "default",
    "default_character_mode": "single"
  },
  
  "output": {
    "default_save_dir": "data/game_data/announcement_images/your_game_key"
  }
}
```

### 4. 开始使用

```python
gen = ImageGenerator(game_key="your_game_key")
result = gen.generate(main_title="测试标题")
```

---

## 配置说明

### 游戏配置 (`config/games/{game_key}.json`)

| 字段 | 说明 |
|------|------|
| `reference_images.ref_file` | 参考图链接文件路径，如 `refs/heartopia.txt` |
| `visual.default_theme` | 默认主题ID |
| `visual.default_character_mode` | 默认角色模式 |
| `themes.custom` | 游戏专属新主题 |
| `character_modes.custom` | 游戏专属新角色模式 |

### 参考图链接文件 (`config/refs/{game_key}.txt`)

每行一个URL，支持 `#` 注释：

```
# 这是注释
https://example.com/ref1.jpg
https://example.com/ref2.png

# 空行会被忽略
https://example.com/ref3.jpg
```

### 可用主题

继承自 `config/themes/_default_themes.json`：

- `default` - 温馨日常
- `summer` - 夏日清凉
- `winter` - 冬日温暖
- `spring` - 春日浪漫
- `halloween` - 万圣节
- `alien` - 外星科幻
- `school` - 秋日学院
- `anniversary` - 周年庆典
- `chinese_new_year` - 春节喜庆
- `cyberpunk` - 赛博朋克

可在游戏配置中通过 `themes.custom` 添加专属主题。

### 角色模式

继承自风格配置（`announcement_cover`）：

- `single` - 单角色（公告类），占屏25%+
- `double` - 双角色（皮肤类），占屏40%+
- `multiple` - 多角色（热闹场景），占屏45%+

可在游戏配置中通过 `character_modes.custom` 添加新模式。

---

## 目录结构

```
config/
├── games/                    # 游戏配置
│   ├── heartopia.json       # 心动小镇
│   ├── _template.json       # 新增游戏模板
│   └── ...
├── refs/                     # 参考图链接文件
│   ├── heartopia.txt        # 心动小镇参考图URL
│   ├── _template.txt        # 链接文件模板
│   └── ...
├── styles/                   # 视觉风格定义
│   └── announcement_cover.json
├── themes/
│   └── _default_themes.json  # 共享主题库
└── size_registry.json       # 平台尺寸配置

scripts/
├── config_loader.py         # 配置加载器
├── image_generator.py       # 图片生成器（主入口）
├── generate_theme_v3.py     # 旧版（已弃用）
├── volcengine_client.py     # API客户端
└── klingai_multi_image.py   # 可灵AI客户端
```

---

## 迁移说明

### 从 v3 迁移到 v4

| v3 (旧版) | v4 (新版) |
|-----------|-----------|
| `generate_theme_v3.py` | `image_generator.py` |
| 硬编码配置 | 配置驱动 |
| 仅支持心动小镇 | 支持任意游戏 |
| 修改代码添加主题 | 修改配置添加主题 |

v3 代码保持兼容，但不再维护。新项目请使用 v4。

---

## 高级用法

### 动态切换游戏

```python
from scripts.image_generator import ImageGenerator

games = ["heartopia", "game_a", "game_b"]

for game_key in games:
    gen = ImageGenerator(game_key=game_key)
    result = gen.generate(
        main_title=f"{gen.config['game_name']} 更新公告",
        sub_title="全新版本上线"
    )
```

### 批量生成多主题

```python
gen = ImageGenerator(game_key="heartopia")
themes = ["spring", "summer", "autumn", "winter"]

for theme in themes:
    gen.generate(
        main_title="四季主题活动",
        sub_title=f"{theme} 季限定",
        theme=theme,
        character_mode="double"
    )
```

### 自定义输出路径

```python
result = gen.generate(
    main_title="测试",
    output_path="custom/path/my_image.jpeg"
)
```

