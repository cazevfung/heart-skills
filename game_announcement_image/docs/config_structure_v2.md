# 游戏公告图生成配置结构 v2.0

## 设计目标

1. **游戏隔离** - 每个游戏独立配置，互不干扰
2. **风格扩展** - 新增风格只需添加配置，零代码改动
3. **主题灵活** - 每个游戏可定义自己的主题库
4. **参考图可配置** - 支持URL列表或本地目录扫描
5. **向后兼容** - 保留现有技能调用方式

---

## 配置层级

```
config/
├── games/                    # 游戏专属配置目录
│   ├── heartopia.json       # 心动小镇
│   ├── xxx_game.json        # 其他游戏...
│   └── _template.json       # 配置模板（供复制）
├── refs/                     # 参考图链接文件
│   ├── heartopia.txt        # 心动小镇参考图URL列表
│   ├── _template.txt        # 链接文件模板
│   └── xxx_game.txt         # 其他游戏...
├── styles/                   # 视觉风格定义（图片生成用）
│   ├── announcement_cover.json
│   ├── warm_casual.json
│   └── ...
├── themes/                   # 主题库（可按游戏覆盖）
│   ├── _default_themes.json  # 默认主题库
│   └── heartopia/           # 游戏专属主题覆盖
│       └── custom_themes.json
└── size_registry.json       # 已有，平台尺寸配置
```

---

## 1. 游戏配置 (config/games/<game_key>.json)

每个游戏一个JSON文件，`game_key` 与 `game_registry` 中的 key 保持一致。

```json
{
  "game_key": "heartopia",
  "game_name": "心动小镇",
  "game_name_en": "Heartopia",
  
  "visual": {
    "default_style": "announcement_cover",
    "default_theme": "default",
    "default_character_mode": "single"
  },
  
  "reference_images": {
    "ref_file": "refs/heartopia.txt"
  },
  
  "themes": {
    "inherit_default": true,
    "overrides": {
      "default": {
        "background": "浅蓝天空，几朵白云，少量小花点缀",
        "atmosphere": "友好、温馨、期待、新鲜感",
        "lighting": "明亮的阳光",
        "mood": "温馨日常"
      }
    },
    "custom": {
      "anniversary": {
        "background": "金色庆典舞台，飘落的彩带和气球",
        "atmosphere": "喜庆、热闹、感恩、欢乐",
        "lighting": "温暖的金色庆典灯光",
        "mood": "周年庆典"
      }
    }
  },
  
  "character_modes": {
    "inherit_default": true,
    "overrides": {},
    "custom": {
      "pet_companion": {
        "count_desc": "一个角色带着一只可爱的宠物",
        "area_ratio": "角色和宠物合计占屏幕30%以上",
        "interaction": "和宠物一起展示"
      }
    }
  },
  
  "output": {
    "default_save_dir": "data/game_data/announcement_images/heartopia",
    "naming_pattern": "{game_key}_{theme}_{character_mode}_{timestamp}.jpeg"
  },
  
  "prompt_template": {
    "version": "v3",
    "custom_template_path": null
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `game_key` | string | 唯一标识，与 registry 一致 |
| `visual.default_*` | string | 默认视觉配置 |
| `reference_images.ref_file` | string | 参考图链接文件路径，如 `refs/heartopia.txt` |
| `themes.inherit_default` | bool | 是否继承默认主题库 |
| `themes.overrides` | object | 覆盖默认主题的配置 |
| `themes.custom` | object | 游戏专属新增主题 |
| `character_modes` | object | 同 themes 结构 |
| `output.default_save_dir` | string | 默认保存目录 |
| `output.naming_pattern` | string | 文件名模板 |

### 参考图链接文件格式 (config/refs/<game_key>.txt)

```
# 每行一个URL，支持 # 注释
https://img2-tc.tapimg.com/...
https://img2-tapimg.com/...

https://example.com/another-ref.jpg
```

---

## 2. 风格配置 (config/styles/<style_id>.json)

视觉风格定义，与 `game_announcement_copy` 的风格ID保持一致。

```json
{
  "style_id": "announcement_cover",
  "name_zh": "公告封面",
  "name_en": "Announcement Cover",
  "description": "专为游戏公告/公测/版本更新设计的封面图风格",
  
  "applicable_games": ["*"],
  "applicable_types": ["maintenance", "event", "version", "general"],
  
  "visual": {
    "aspect_ratio": "16:9",
    "art_style": "手绘插画风，色彩明亮柔和，带一点日系/治愈系游戏UI感",
    "color_tone": "高明度、低饱和度，暖色调为主",
    "line_style": "圆润柔和，无尖锐棱角"
  },
  
  "layout": {
    "description": "左上角Logo区，中左部文字区，右侧主体焦点",
    "logo_area": "左上角",
    "text_area": "中左部，主标题占屏比20%以上",
    "focus_area": "右侧中景"
  },
  
  "prompt_template": {
    "version": "v3",
    "structure": [
      "【固定规范】画面风格、布局、技术要求",
      "【主题内容】主题氛围、光线",
      "【主体元素】前景角色、中景场景、背景",
      "【文字区域】主标题、副标题",
      "【整体氛围】"
    ]
  },
  
  "character_modes": {
    "single": {
      "count_desc": "一个可爱的卡通角色",
      "area_ratio": "角色形象要饱满突出，占屏幕25%以上",
      "interaction": "单独展示",
      "action_style": "姿态自然大方"
    },
    "double": {
      "count_desc": "两个可爱的卡通角色",
      "area_ratio": "两个角色都要饱满突出，合计占屏幕40%以上",
      "interaction": "一起互动展示",
      "action_style": "动作夸张有张力，姿态生动活泼"
    },
    "multiple": {
      "count_desc": "多个可爱的卡通角色",
      "area_ratio": "角色们饱满突出，合计占屏幕45%以上",
      "interaction": "热闹地一起展示",
      "action_style": "动作夸张有张力，姿态生动活泼"
    }
  },
  
  "reference_images": {
    "description": "手绘插画风，色彩明亮柔和，日系游戏UI感",
    "example_urls": []
  }
}
```

---

## 3. 默认主题库 (config/themes/_default_themes.json)

所有游戏共享的基础主题库。

```json
{
  "version": "1.0",
  "themes": {
    "default": {
      "background": "浅蓝天空，几朵白云，少量小花点缀",
      "atmosphere": "友好、温馨、期待、新鲜感",
      "lighting": "明亮的阳光",
      "mood": "温馨日常"
    },
    "alien": {
      "background": "深蓝紫色渐变星空，闪烁的星星，远处有飞碟发出的神秘光束",
      "atmosphere": "神秘、奇幻、探索、未来感",
      "lighting": "柔和的星光和飞碟光效",
      "mood": "夜晚神秘"
    },
    "school": {
      "background": "秋日黄昏天空，暖黄色调，几片飘落的梧桐叶",
      "atmosphere": "温馨、学院风、秋日、书卷气",
      "lighting": "温暖的午后阳光",
      "mood": "秋日学院"
    },
    "halloween": {
      "background": "暗紫色夜空，一轮明月，南瓜灯点缀",
      "atmosphere": "神秘、俏皮、节日氛围、惊喜",
      "lighting": "南瓜灯的暖光和月光",
      "mood": "夜晚节日"
    },
    "summer": {
      "background": "清澈的蓝天，蓬松的白云，海边或泳池元素",
      "atmosphere": "清凉、活力、夏日、放松",
      "lighting": "明亮的夏日阳光",
      "mood": "夏日清凉"
    },
    "spring": {
      "background": "粉樱飘落的街道，嫩绿新叶，蓝天白云",
      "atmosphere": "生机、浪漫、清新、希望",
      "lighting": "柔和的春日阳光",
      "mood": "春日浪漫"
    },
    "winter": {
      "background": "银装素裹的小镇，飘落的雪花，温暖的灯光",
      "atmosphere": "温暖、宁静、节日、团聚",
      "lighting": "温暖的室内灯光和雪地反光",
      "mood": "冬日温暖"
    }
  }
}
```

---

## 4. 代码加载逻辑

```python
def load_game_config(game_key: str) -> dict:
    """加载游戏配置，自动合并默认主题/角色模式"""
    
    # 1. 加载游戏专属配置
    config_path = f"config/games/{game_key}.json"
    game_config = load_json(config_path)
    
    # 2. 加载默认主题库
    default_themes = load_json("config/themes/_default_themes.json")
    
    # 3. 合并主题（游戏覆盖 + 自定义 > 默认）
    themes = {}
    if game_config.get("themes", {}).get("inherit_default", True):
        themes.update(default_themes["themes"])
    themes.update(game_config.get("themes", {}).get("overrides", {}))
    themes.update(game_config.get("themes", {}).get("custom", {}))
    
    # 4. 加载风格定义中的角色模式作为默认
    style_id = game_config.get("visual", {}).get("default_style", "announcement_cover")
    style_config = load_json(f"config/styles/{style_id}.json")
    
    # 5. 合并角色模式
    character_modes = {}
    if game_config.get("character_modes", {}).get("inherit_default", True):
        character_modes.update(style_config.get("character_modes", {}))
    character_modes.update(game_config.get("character_modes", {}).get("overrides", {}))
    character_modes.update(game_config.get("character_modes", {}).get("custom", {}))
    
    # 6. 组装完整配置
    return {
        "game_key": game_key,
        "game_name": game_config.get("game_name", game_key),
        "reference_images": resolve_reference_images(game_config),
        "themes": themes,
        "character_modes": character_modes,
        "visual": game_config.get("visual", {}),
        "output": game_config.get("output", {}),
        "style_config": style_config
    }


def resolve_reference_images(game_config: dict) -> list:
    """解析参考图配置，从 .txt 文件读取URL列表"""
    
    ref_config = game_config.get("reference_images", {})
    ref_file = ref_config.get("ref_file")
    
    if not ref_file:
        return []
    
    return load_ref_urls(ref_file)


def load_ref_urls(ref_file: str) -> list:
    """从 .txt 文件加载参考图URL列表"""
    
    with open(f"config/{ref_file}", 'r') as f:
            local_urls = scan_and_upload_local_images(local_dir)
            urls.extend(local_urls)
        return urls
    
    return []
```

---

## 5. 新增游戏流程

1. **复制游戏配置模板**
   ```bash
   cp config/games/_template.json config/games/my_game.json
   ```

2. **创建参考图链接文件**
   ```bash
   cp config/refs/_template.txt config/refs/my_game.txt
   ```

3. **编辑参考图链接文件**
   打开 `config/refs/my_game.txt`，每行粘贴一个参考图URL：
   ```
   https://example.com/ref1.jpg
   https://example.com/ref2.jpg
   ```

4. **编辑游戏配置**
   - 修改 `game_key`, `game_name`
   - 确认 `reference_images.ref_file` 指向正确的链接文件
   - 调整默认 `theme` 和 `character_mode`
   - 可选：添加 `themes.custom` 游戏专属主题

5. **开始使用**
   ```python
   from scripts.image_generator import ImageGenerator
   
   gen = ImageGenerator(game_key="my_game")
   result = gen.generate(
       theme="summer",
       character_mode="double",
       main_title="夏日活动",
       sub_title="清凉一夏"
   )
   ```

---

## 6. 向后兼容

现有 `generate_theme_v3.py` 保持不动，新代码作为 `generate_theme_v4.py` 或重构后的 `image_generator.py`：

```python
# 旧调用（硬编码，仅支持心动小镇）
from scripts.generate_theme_v3 import build_prompt_v3, generate_image

# 新调用（配置驱动，支持任意游戏）
from scripts.image_generator_v2 import ImageGenerator
gen = ImageGenerator(game_key="heartopia")  # 或其他游戏
```

---

## 7. 迁移检查清单

- [ ] 创建 `config/games/heartopia.json` 迁移心动小镇配置
- [ ] 创建 `config/styles/announcement_cover.json` 迁移风格定义
- [ ] 创建 `config/themes/_default_themes.json` 迁移主题库
- [ ] 创建 `config/games/_template.json` 模板文件
- [ ] 实现配置加载和合并逻辑
- [ ] 实现新的 `ImageGenerator` 类
- [ ] 测试多游戏场景
- [ ] 标记 `generate_theme_v3.py` 为 deprecated

