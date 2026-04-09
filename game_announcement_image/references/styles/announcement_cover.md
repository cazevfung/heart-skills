# 风格定义：公告封面图 (Announcement Cover)

## 概述
专为游戏公告/公测/版本更新设计的封面图风格，强调信息清晰、视觉温馨、品牌一致。

## 适用场景
- 游戏公测公告
- 版本更新公告
- 开服/开测公告
- 重大活动预告

## 视觉规范

### 画面比例
- 首选：16:9（横版公告封面）
- 备选：9:16（竖版移动端）、1:1（正方形社交媒体）

### 画面结构
```
┌─────────────────────────────────────┐
│  [Logo]                             │  ← 左上角：游戏Logo
│                                     │
│        ┌─────────────────┐          │
│        │   主标题 20%+   │          │  ← 中上部：主标题区域
│        │   副标题 8-10%  │          │     占屏比要求
│        └─────────────────┘          │
│                                     │
│    [主体角色/元素 - 视觉焦点]        │  ← 中景：主体元素
│                                     │
│  [场景背景 - 氛围营造]               │  ← 背景：场景氛围
└─────────────────────────────────────┘
```

### 风格描述
- **整体风格**：手绘插画风，色彩明亮柔和
- **调性**：日系/治愈系游戏UI感
- **线条**：圆润柔和，无尖锐棱角
- **色彩**：高明度、低饱和度，暖色调为主

## Prompt 模板（2026-03-17 最终定稿版）

### 主题化模板v3（固定规范 + 可变内容）

```
一张温馨可爱的《{游戏名称}》更新公告海报，16:9。

【固定规范】
画面风格：手绘插画风，色彩明亮柔和，带一点日系/治愈系游戏UI感。
画面布局：左上角放置游戏Logo区域，中左部预留文字区域，视觉焦点在右边、标题在左边。
技术要求：信息层级清晰易读，色彩搭配和谐，符合治愈系游戏调性，画面构图平衡。

【主题内容】
主题氛围：{主题氛围}
光线效果：{光线效果}

主体元素：
- 前景（画面核心）：{角色数量描述}，{角色服装描述}，{角色互动描述}，{角色动作描述}，表情{表情描述}。{角色面积要求}，角色与参考图中风格保持高度一致。角色要画得大一些，是画面的主要视觉焦点。
- 中景：卡通风格的{场景描述}，有"{游戏名称}"的{氛围关键词}生活感
- 背景：{背景描述}

文字区域：
- 主标题："{主标题}"（醒目字体，左上角区域）
- 副标题："{副标题}"（清晰字体，主标题下方）

整体氛围：{整体氛围}
```

### 角色配置

| 类型 | 适用场景 | 角色数量 | 面积要求 | 动作风格 |
|------|---------|---------|---------|---------|
| `single` | 公告类 | 1个角色 | 占屏幕25%以上 | 姿态自然大方 |
| `double` | 皮肤类（情侣/双人套装） | 2个角色 | 合计占屏幕40%以上 | 动作夸张有张力，姿态生动活泼 |
| `multiple` | 热闹场景/多人活动 | 多个角色 | 合计占屏幕45%以上 | 动作夸张有张力，姿态生动活泼 |

### 主题配置库

| 主题ID | 背景描述 | 光线效果 | 整体氛围 |
|--------|---------|---------|---------|
| `default` | 浅蓝天空，几朵白云，少量小花点缀 | 明亮的阳光 | 友好、温馨、期待、新鲜感 |
| `alien` | 深蓝紫色渐变星空，闪烁的星星，远处有飞碟发出的神秘光束 | 柔和的星光和飞碟光效 | 神秘、奇幻、探索、未来感 |
| `school` | 秋日黄昏天空，暖黄色调，几片飘落的梧桐叶 | 温暖的午后阳光 | 温馨、学院风、秋日、书卷气 |
| `halloween` | 暗紫色夜空，一轮明月，南瓜灯点缀 | 南瓜灯的暖光和月光 | 神秘、俏皮、节日氛围、惊喜 |
| `summer` | 清澈的蓝天，蓬松的白云，海边或泳池元素 | 明亮的夏日阳光 | 清凉、活力、夏日、放松 |

### 使用示例（外星人主题 - 皮肤类双角色）

```python
prompt = build_prompt_v3(
    theme="alien",
    character_mode="double",
    main_title="外星来客",
    sub_title="全新外星人主题外观上线",
    character_desc="穿着外星人主题发光服装，头戴天线头饰",
    character_action="兴奋地指向天空中的飞碟，身体前倾，一个角色跳起来挥手，另一个角色摆出邀请姿势",
    expression="超级兴奋、眼睛闪闪发光",
    scene_elements="小镇夜晚场景——飞碟悬浮在空中、星星闪烁、神秘光效照亮地面",
    dynamic_pose="动作夸张有活力，一个角色单脚跳起双手高举，另一个角色张开双臂做欢迎姿势，充满动感和张力"
)
```

### 旧版模板（已弃用）

```
一张温馨可爱的{游戏名}公告海报，{宽高比}。

画面风格：手绘插画风，色彩明亮柔和，带一点日系/治愈系游戏UI感。

画面布局：
- 左上角放置游戏Logo区域
- 中上部预留文字区域（主标题占屏比20%以上，副标题占屏比8-10%）
- 视觉焦点在中景偏下位置

主体元素：
- 前景：{角色描述}，{动作描述}，表情开心，角色与参考图中风格保持高度一致。
- 中景：卡通风格的{场景描述}，有"{游戏名}"的温馨生活感
- 背景：{背景描述}

文字区域要求：
- 主标题区域：{主标题}，字体醒目，占屏比20%以上
- 副标题区域：{副标题}，字体清晰，占屏比8-10%
- 文字区域需留白或使用浅色块衬托，确保易读性

整体氛围：{氛围描述}

技术要求：
- 必须适合做游戏开服/公测公告图
- 信息层级清晰、易读
- 色彩搭配和谐，符合治愈系游戏调性
- 画面构图平衡，视觉焦点突出
```

### 基础模板（英文 - 用于SD/ComfyUI）
```
A warm and cute {game_name} announcement poster, {aspect_ratio}.

Art style: Hand-drawn illustration, bright and soft colors, Japanese/healing game UI aesthetic.

Layout:
- Game logo area at top-left corner
- Text area in upper-middle (main title 20%+ screen ratio, subtitle 8-10%)
- Visual focus at lower-middle area

Main elements:
- Foreground: {character_description}, {action_description}, happy expression
- Midground: Cartoon-style {scene_description}, warm life atmosphere of "{game_name}"
- Background: {background_description}

Text area requirements:
- Main title: {main_title}, eye-catching font, 20%+ screen ratio
- Subtitle: {subtitle}, clear font, 8-10% screen ratio
- Text areas should have留白 or light color blocks for readability

Overall atmosphere: {atmosphere_description}

Technical requirements:
- Suitable for game launch/beta announcement
- Clear information hierarchy
- Harmonious color scheme, healing game aesthetic
- Balanced composition with prominent visual focus
```

## 使用示例

### 心动小镇 - 公测公告
```
一张温馨可爱的《心动小镇》公告海报，16:9。

画面风格：手绘插画风，色彩明亮柔和，带一点日系/治愈系游戏UI感。

画面布局：
- 左上角放置游戏Logo区域
- 中上部预留文字区域
- 视觉焦点在中景偏下位置

主体元素：
- 前景：一个可爱的卡通角色，穿着休闲服装，挥手打招呼，表情开心
- 中景：卡通风格的小镇街景——小房子、绿树、蓝天、夏日阳光，有"心动小镇"的温馨生活感
- 背景：浅蓝天空，几朵白云，加少量小花点缀

文字区域要求：
- 主标题区域：占屏比20%以上
- 副标题区域：占屏比8-10%
- 文字区域需留白或使用浅色块衬托

整体氛围：友好、温馨、夏日、入住新家的期待感
```

## 可灵AI 多图参考建议

使用可灵AI多图参考生图时，建议提供：

1. **主体图**（1-2张）：游戏角色参考
2. **风格图**（1张）：期望的视觉风格参考
3. **场景图**（可选）：背景氛围参考

Prompt结构：
```
{游戏名}公告海报，{宽高比}。
手绘插画风，色彩明亮柔和，日系治愈系游戏UI感。
画面包含：{主体描述}，{场景描述}。
主标题占屏比20%以上，副标题占屏比8-10%，文字区域清晰留白。
整体氛围：{氛围描述}。
```

## 参考图库（2026-03-17 更新）

### 在线URL列表（推荐，用于Seedream 4.5）

**8张心动小镇官方公告图URL：**

```json
[
  "https://img2-tc.tapimg.com/moment/etag/FjSX_iltfweQnyj9XqF2Naml0vMG_20260306165555.jpg/_tap_ugc.jpg",
  "https://img2-tc.tapimg.com/moment/etag/FklCYDD11W49qhjsHk6J6RaGHbUd_20260128152132.jpg/_tap_ugc.jpg",
  "https://img2-tc.tapimg.com/moment/etag/FoGeCBAn1smL8nidtmcbdJ1dZdi6_20260109102534.jpg/_tap_ugc.jpg",
  "https://img2-tc.tapimg.com/moment/etag/Fi_v57DrNBocoomvTt3FXU8V1AqS_20251208151456.jpg/_tap_ugc.jpg",
  "https://img2-tc.tapimg.com/moment/etag/FldrfzEyyPF1xP451cGRCwo0JBP9_20260122174319.png/_tap_ugc.jpg",
  "https://img2-tc.tapimg.com/moment/etag/FhewBX82mHph6Nm8lhp5t_apn5am.jpg/_tap_ugc_m.jpg",
  "https://img2-tc.tapimg.com/moment/etag/FtLCNfFU2xwKOoNxO7AU5759tw7G.png/_tap_ugc_m.jpg",
  "https://img2-tc.tapimg.com/moment/etag/Fsw9J7JfmdYSC2Up1n5tJ_cbQuTg_20251127143416.jpg/_tap_ugc_m.jpg"
]
```

**重要提示：**
- **必须使用在线URL** - Seedream 4.5 API 只支持公网可访问的图片URL
- **base64编码的图片不会被正确处理**
- **8张效果最好** - 经测试，8张参考图比10张效果更好
- 这些URL来自TapTap官方公告图，风格统一、质量高

### 本地文件列表（仅作备份）

本地 `references/refs/announcement_cover/` 目录下有10张JPG文件：

| 文件名 | 大小 |
|--------|------|
| _tap_ugc (1).jpg | 127KB |
| _tap_ugc (3).jpg | 185KB |
| _tap_ugc (4).jpg | 246KB |
| _tap_ugc (5).jpg | 241KB |
| _tap_ugc (6).jpg | 170KB |
| _tap_ugc (8).jpg | 147KB |
| _tap_ugc (10).jpg | 212KB |
| _tap_ugc (11).jpg | 195KB |
| _tap_ugc (12).jpg | 384KB |
| _tap_ugc (14).jpg | 224KB |

**注意：** 本地文件不能直接用于Seedream 4.5 API，需要上传到图床获取在线URL。

### 参考图特点

- **风格**：手绘插画风，色彩明亮柔和
- **色调**：暖色调为主，高明度低饱和度
- **构图**：符合公告封面图规范（Logo区、标题区、主体区、背景区）
- **氛围**：温馨、治愈、日系游戏UI感

### 使用建议

#### 🎨 10张风格库机制

预置的10张参考图作为一个固定的**风格库**，每次生成时：
1. 从10张中选择4张最具代表性的（分散选择，最大化风格覆盖）
2. AI学习这4张的**整体风格特征**（色彩、笔触、氛围）
3. 不复制任何一张的具体内容，而是融合学习

**选择策略**：
- 选择第1、3、5、8张（`_tap_ugc (1)`, `(3)`, `(5)`, `(8)`）
- 分散选择，覆盖不同构图和场景类型
- 在API限制（最多4张）下最大化风格多样性

**使用风格库生成（默认，推荐）**：
```bash
python scripts/generate_cover_v2.py \
  --game "心动小镇" \
  --main-title "新版本上线" \
  --sub-title "全新内容上线" \
  --character "可爱卡通角色，原创设计" \
  --action "开心地展示新物品" \
  --scene "小镇街景，小房子、绿树" \
  --n 2
```

**风格库 + 额外自定义参考图**：
```bash
python scripts/generate_cover_v2.py \
  --game "心动小镇" \
  --main-title "新版本上线" \
  --character "可爱卡通角色" \
  --scene "小镇街景" \
  --subject-refs "my_custom_char.jpg"
```

**纯文本生成（无参考图）**：
```bash
python scripts/generate_cover_v2.py \
  --game "心动小镇" \
  --main-title "新版本上线" \
  --character "可爱卡通角色" \
  --scene "小镇街景" \
  --no-refs
```

**作为风格参考图 (`--style-ref`)**：
```bash
python scripts/generate_cover.py \
  --game "心动小镇" \
  --main-title "新版本上线" \
  --character "可爱角色" \
  --scene "小镇场景" \
  --style-ref "references/refs/announcement_cover/_tap_ugc (5).jpg"
```

**作为主体参考图 (`--subject-refs`)**：
```bash
python scripts/generate_cover.py \
  --game "心动小镇" \
  --main-title "新版本上线" \
  --character "可爱角色" \
  --scene "小镇场景" \
  --subject-refs \
    "references/refs/announcement_cover/_tap_ugc (1).jpg"
```

## 注意事项

1. **文字占位**：AI生成时预留文字区域，实际文字建议后期用设计软件添加
2. **Logo位置**：左上角固定位置，生成时避免在该区域放置重要视觉元素
3. **信息层级**：确保画面不会因过于复杂而影响文字可读性
4. **品牌一致性**：保持与游戏整体视觉风格的一致性
5. **参考图选择**：从预置图库中选择与目标风格最接近的作为参考
