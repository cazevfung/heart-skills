---
name: game_announcement_image
description: "当用户需要根据游戏公告文案生成公告配图（多风格、多尺寸、多平台）时使用本 skill。通过风格注册表与参考图库支持无限扩展；根据文案内容决定张数与尺寸，通过可扩展尺寸库支持各平台规格。"
metadata:
  {
    "copaw": {
      "emoji": "🖼️",
      "requires": {}
    },
    "openclaw": {
      "skillKey": "copaw-shared",
      "requires": {
        "bins": [
          "python3"
        ]
      }
    }
  }
---

# Game Announcement Image Skill（游戏公告图生成）

本 skill 根据公告文案与所选风格，决定需要生成的图片张数与尺寸，并调用图像生成 API 产出公告图。**扩展方式**：新增风格 = 新建 `references/styles/<style_id>.md` 并在风格注册表加一行；新增平台尺寸 = 在 `config/size_registry.json` 加一条；参考图 = 在 `references/refs/<game_key>/` 或 `references/refs/<style_id>/` 下放入图片；模型 = 从 `{base_url}/models` 拉取并选择。

## ⚠️ 版本说明

**当前版本：v2.0（配置驱动版）**

- ✅ **配置驱动**：`config/games/<game_key>.json` 定义游戏专属配置
- ✅ **多游戏支持**：每个游戏独立配置参考图、主题、角色模式
- ✅ **主题扩展**：通过配置添加新主题，无需改代码
- ✅ **向后兼容**：旧版 `generate_theme_v3.py` 仍可用，但不再维护

**主要入口**：`scripts/image_generator.py`

## 何时使用

- 用户说：为某游戏**生成公告图**、**根据公告文案出图**、**做公告配图**、**多平台尺寸的公告图**
- 用户已有公告文案（如由 **game_announcement_copy** 生成），希望产出对应配图
- 用户希望指定**发布平台**（微博、TapTap、Reddit、B站等）或**尺寸**，产出符合规范的图

## 参数

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **game** | 游戏名称或 game_key | 从用户消息或上下文推断，无法推断时询问 |
| **announcement_copy** | 公告文案全文 | 用户提供或上游 skill 产出，缺失时询问 |
| **style** | 视觉风格 override（style_id） | 见「style 解析顺序」 |
| **platforms** / **size_ids** | 限定只出某几个平台或尺寸（size_registry 的 key） | 不填则由 Phase 2 根据文案与尺寸库决定 |
| **model_id** | 图像生成模型（需在 /models 列表中） | 不填则拉取列表后由用户或默认选一个 |
| **image_api_base_url** | 图像 API 根地址 | 见「API 配置」 |

### style 解析顺序

1. 用户明确指定风格（如「用温暖风格」「warm_casual」「正式一点」）→ 匹配风格注册表中的 style_id 或 name_zh/name_en。
2. 未指定则调用 **read_game_registry**，从返回的注册表中取 `games[game_key].announcement_image_style_id`；若无则用 `announcement_style_id`。
3. 若仍无，列出风格注册表让用户选择，或使用注册表第一行作为默认。

### API 配置

- 优先读取本 skill 目录下 `config/image_api.json` 中的 `image_api_base_url`。
- 若不存在或为空，可读取项目根目录 `config.json` 的 `last_api.host` 与 `last_api.port` 拼成 `http://<host>:<port>`。
- 否则默认 `http://127.0.0.1:8088`。模型列表为 GET `{base_url}/models`。

---

## 风格注册表

所有可用**视觉风格**在此表定义。Phase 1 解析、Phase 3 加载定义与参考图均依赖此表。

**新增风格 = 新建 `references/styles/<style_id>.md`（视觉描述：色调、构图、字体感等）+ 在本表加一行。**

| style_id | name_zh | name_en | 适用场景 | 定义文件 | 参考图目录 | 推荐模型 |
|----------|---------|---------|----------|----------|------------|----------|
| announcement_cover | 公告封面 | Announcement Cover | 公测/开服/版本公告封面图 | styles/announcement_cover.md | refs/announcement_cover/ | 火山引擎 Doubao-Seedream-4.5 |
| warm_casual | 温暖口语 | Warm & Casual | 社区向、治愈系、生活模拟 | styles/warm_casual.md | refs/warm_casual/ | - |
| official_formal | 正式简洁 | Official Formal | 版本/维护公告、海外向 | styles/official_formal.md | refs/official_formal/ | - |
| playful_emoji | 活泼表情 | Playful+Emoji | 活动、福利、节日公告 | styles/playful_emoji.md | refs/playful_emoji/ | - |

---

## 尺寸库（可扩展）

所有「平台/场景 → 宽高」以 **`config/size_registry.json`** 为准。当前已包含：weibo_single、weibo_banner、taptap_banner、taptap_cover、reddit_banner、reddit_card、bilibili_cover、bilibili_dynamic、general_square、general_landscape 等。

**扩展**：在 `config/size_registry.json` 的 `sizes` 下新增条目，例如：

```json
"new_platform_cover": {
  "width": 1200,
  "height": 630,
  "name_zh": "新平台封面",
  "name_en": "New platform cover",
  "usage": "用途说明"
}
```

执行时所有「需要什么尺寸」的逻辑均从该文件解析；不得写死宽高。

---

## 执行流程（6 个阶段）

### Phase 1 — 解析 game、style、文案

1. 从用户消息或上下文解析 **game**，调用 **read_game_registry** 并匹配得到 game_key；若游戏未注册，先委托 **game_crawl** 发现并注册再继续。
2. 按「style 解析顺序」得到 **style_id**。
3. 确认 **announcement_copy**（公告文案全文）已就绪；若无则询问或请用户先使用 **game_announcement_copy** 生成。
4. Echo 已解析参数：game_key、style_id、announcement_copy 摘要。

### Phase 2 — 根据文案与尺寸库决定张数与每张规格

1. 读取 `config/size_registry.json`，得到当前所有 size_id 及其 width、height、name_zh、usage。
2. 若用户已指定 **platforms** 或 **size_ids**：只使用这些 size_id 生成，张数 = 指定数量；每张的 size_id 与 purpose 由你按顺序分配。
3. 若未指定：使用 **LLM 规划**一次。输入 = 公告文案全文 + size_registry 摘要（列出各 size_id、name_zh、usage）；输出 = 结构化 JSON：
   - `num_images`：需要生成的图片数量；
   - `specs`：数组，每项 `{ "size_id": "<来自 size_registry>", "purpose": "首图/横幅/..." }`。
4. 校验 specs 中所有 size_id 均存在于 size_registry；若有非法 size_id 则报错并提示可用列表。

### Phase 3 — 加载风格定义与参考图路径

1. 根据风格注册表找到 style_id 对应的定义文件：`<本 skill 目录>/references/styles/<style_id>.md`，读取全文（视觉描述、prompt 建议等）。
2. 解析参考图目录：
   - 优先：`references/refs/<game_key>/` 下图片文件（若存在）；
   - 补充：`references/refs/<style_id>/` 下图片文件（若存在）。
3. 若风格定义文件不存在，报错并列出注册表中已有 style_id。

### Phase 4 — 拉取模型列表并选定模型

1. 确定 **image_api_base_url**（见「API 配置」）。
2. GET `{image_api_base_url}/models`，获取可用模型列表。若请求失败，提示用户检查 8088 服务是否启动、网络与配置。
3. 若用户已指定 **model_id**：在列表中校验存在后使用；否则展示列表由用户选择，或使用列表第一项/配置中的默认项。
4. Echo 将使用的 model_id。

### Phase 5 — 按 specs 逐张调用生成 API（火山引擎 Seedream 4.5）

1. 对 specs 中每一项：
   - 结合 Phase 3 的风格定义与公告文案要点，组装**图像生成 prompt**；
   - **参考图**：使用在线 URL 数组（8张），通过 `"image": ["url1", "url2", ...]` 传递；
   - **调用 API**：POST 到 `https://ark.cn-beijing.volces.com/api/v3/images/generations`；
   - **请求体**：
     ```json
     {
       "model": "doubao-seedream-4-5-251128",
       "prompt": "...",
       "sequential_image_generation": "disabled",
       "image": ["https://img2-tc.tapimg.com/..."],
       "size": "2K",
       "watermark": false,
       "max_images": 2,
       "response_format": "url",
       "stream": false
     }
     ```
2. 保存生成结果到本地（路径：`D:\App Dev\openclaw-main\data\game_data\announcement_images\`）。

**重要：**
- 参考图必须用**在线 URL**，base64 不生效
- 使用 `"image"` 参数，不是 `"reference_images"`
- 尺寸用 `"2K"`，不是具体像素
- 主生成脚本：`scripts/image_generator.py` (v2.0)
- 旧版脚本：`scripts/generate_theme_v3.py` (已弃用)

### Phase 6 — 汇总输出

1. 向用户返回：生成了几张图、每张的 size_id、用途、本地路径（或展示缩略图/链接）。
2. 附带使用的 style_id、model_id、base_url，便于复现或调整。

---

## 错误处理

| 问题 | 处理 |
|------|------|
| 游戏未在 game_registry 注册 | 委托 game_crawl 发现并注册后继续；若无法发现则提示用户通过 write_game_registry 或 game_crawl 手动配置 |
| 风格定义文件不存在 | 提示「风格 \<style_id\> 定义文件缺失」，列出注册表已有 style_id |
| announcement_copy 缺失 | Phase 1 询问用户粘贴文案或先运行 game_announcement_copy |
| specs 中含不存在的 size_id | 报错并输出 size_registry 中全部 size_id，请用户或 LLM 修正 |
| GET /models 失败 | 提示检查 8088 服务、config 中的 base_url 与网络 |
| 生成 API 调用失败 | 提示检查 body 格式、模型是否可用、后端日志；可建议查看 config/image_api.json 的 request_format_note |

---

## 多图参考生图支持（可灵AI）

本 skill 支持调用**可灵AI (KlingAI)** 进行多图参考生图，适用于风格迁移、角色一致性、场景+主体融合等场景。

### 可灵AI 配置

配置文件：`config/klingai_api.json`

```json
{
  "provider": "klingai",
  "api_base_url": "https://api-beijing.klingai.com",
  "access_key": "你的Access Key",
  "secret_key": "你的Secret Key",
  "models": ["kling-v2", "kling-v2-1"]
}
```

### API 端点

| 端点 | 路径 | 说明 |
|------|------|------|
| 创建任务 | `POST /v1/images/multi-image2image` | 提交多图参考生图任务 |
| 查询任务 | `GET /v1/images/multi-image2image/{task_id}` | 查询单个任务状态 |
| 查询列表 | `GET /v1/images/multi-image2image` | 查询任务列表 |

### 参考图类型

可灵多图参考生图支持三种参考图：

| 类型 | 参数 | 数量 | 说明 |
|------|------|------|------|
| **主体图** | `subject_image_list` | 1-4张 | 主体参考，如角色、物品等 |
| **场景图** | `scene_image` | 0-1张 | 场景/背景参考 |
| **风格图** | `style_image` | 0-1张 | 风格/色调参考 |

### 调用方式

**基础调用（仅主体图）：**
```bash
python scripts/klingai_multi_image.py \
  --config config/klingai_api.json \
  --subject-images char1.png char2.png \
  --prompt "身着飘逸红色连衣裙，在草原上，吉卜力风格" \
  --model-name kling-v2-1 \
  --n 2 \
  --aspect-ratio 9:16
```

**完整调用（主体+场景+风格）：**
```bash
python scripts/klingai_multi_image.py \
  --config config/klingai_api.json \
  --subject-images character.png \
  --scene-image background.jpeg \
  --style-image ghibli_style.png \
  --prompt "游戏角色站在小镇广场上" \
  --model-name kling-v2-1 \
  --n 1 \
  --aspect-ratio 16:9
```

**查询任务状态：**
```bash
python scripts/klingai_multi_image.py \
  --config config/klingai_api.json \
  --query <task_id>
```

### 参数说明

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--subject-images` | 主体参考图片路径 (1-4张) | 是 | - |
| `--prompt` | 正向文本提示词（≤2500字符） | 是 | - |
| `--model-name` | 模型名称 | 否 | kling-v2 |
| `--scene-image` | 场景参考图路径 | 否 | - |
| `--style-image` | 风格参考图路径 | 否 | - |
| `--negative-prompt` | 负向提示词 | 否 | "" |
| `--n` | 生成图片数量 (1-9) | 否 | 1 |
| `--aspect-ratio` | 画面纵横比 | 否 | 16:9 |
| `--query` | 查询指定task_id | 否 | - |
| `--output` | 结果保存路径 | 否 | - |

**支持的 aspect_ratio:**
- `16:9` (默认) - 横屏
- `9:16` - 竖屏
- `1:1` - 正方形
- `4:3`, `3:4`, `3:2`, `2:3`, `21:9`

### Python API 调用

```python
from scripts.klingai_multi_image import KlingAIClient

client = KlingAIClient(
    access_key="AQQFYQQyaJEbTGLadeD989fpKRBRYra4",
    secret_key="hnMNJFbFaJMb99EMbFr8aMCeeftn9f9P"
)

# 提交多图参考生图任务
result = client.multi_image_to_image(
    subject_images=["char_ref1.png", "char_ref2.png"],
    prompt="身着飘逸红色连衣裙，在草原上，吉卜力风格",
    model_name="kling-v2-1",
    scene_image="background.jpeg",  # 可选
    style_image="ghibli_style.png",  # 可选
    n=2,
    aspect_ratio="9:16"
)

task_id = result['data']['task_id']
print(f"任务ID: {task_id}")

# 查询任务状态
status = client.query_task(task_id)
if status['data']['task_status'] == 'succeed':
    for img in status['data']['task_result']['images']:
        print(f"生成图片URL: {img['url']}")
```

### 重要注意事项

1. **Base64格式**: 图片转Base64时**不要加** `data:image/png;base64,` 前缀，直接传递编码后的字符串
   - ✅ 正确: `iVBORw0KGgoAAAANSUhEUgAAAAUA...`
   - ❌ 错误: `data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...`

2. **图片要求**:
   - 格式: .jpg / .jpeg / .png
   - 大小: ≤ 10MB
   - 尺寸: ≥ 300px
   - 宽高比: 1:2.5 ~ 2.5:1

3. **任务状态**: 
   - `submitted` - 已提交
   - `processing` - 处理中
   - `succeed` - 成功
   - `failed` - 失败

---

## 火山引擎版生成（推荐）

使用 **火山引擎方舟 Doubao-Seedream-4.5** 模型生成公告图，OpenAI兼容API，响应更快。

### 关键配置（2026-03-17 更新）

**API 参数说明：**

| 参数 | 正确用法 | 说明 |
|------|---------|------|
| `image` | `["url1", "url2", ...]` | **参考图必须用在线URL数组**，base64不生效 |
| `size` | `"2K"` | 使用"2K"而非具体像素 |
| `watermark` | `false` | 设置为false去除水印 |
| `max_images` | `2` | 最多生成数量 |
| `sequential_image_generation` | `"disabled"` | 单图模式（非组图） |
| `output_format` | - | **不支持**，只能用jpeg |

**参考图URL列表（心动小镇公告图）：**
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

### 配置

配置文件：`config/volcengine_api.json`

```json
{
  "provider": "volcengine",
  "api_base_url": "https://ark.cn-beijing.volces.com/api/v3",
  "api_key": "your-api-key",
  "models": ["doubao-seedream-4-5-251128"]
}
```

### API 调用示例

```python
import requests

payload = {
    "model": "doubao-seedream-4-5-251128",
    "prompt": "一张温馨可爱的《心动小镇》更新公告海报...",
    "sequential_image_generation": "disabled",
    "image": ["https://img2-tc.tapimg.com/..."],  # 在线URL数组
    "size": "2K",
    "watermark": False,
    "max_images": 2,
    "response_format": "url",
    "stream": False
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://ark.cn-beijing.volces.com/api/v3/images/generations",
    headers=headers,
    json=payload,
    timeout=300
)
```

### 重要教训

1. **参考图必须用在线URL** - base64编码的图片不会被正确处理
2. **8张参考图效果最好** - 10张可能太多，建议用8张
3. **Prompt要简洁** - 避免技术说明被画进图里
4. **尺寸用"2K"** - 不要用具体像素值

---

## 可灵AI版生成（多图参考）

使用 **可灵AI** 进行多图参考生图，支持上传参考图片学习风格。

### 配置

配置文件：`config/klingai_api.json`

```json
{
  "provider": "klingai",
  "api_base_url": "https://api-beijing.klingai.com",
  "access_key": "your-access-key",
  "secret_key": "your-secret-key"
}
```

---

## 公告封面图生成（announcement_cover 风格）

专为游戏公告/公测/版本更新设计的封面图生成流程，使用 **火山引擎 Doubao-Seedream-4.5** 模型。

### 风格特点

- **画面比例**: 16:9（横版公告封面首选）
- **画面结构**:
  - 左上角：游戏Logo区域
  - 中左部：文字区域
  - 右侧：主体角色/元素（视觉焦点）
- **视觉风格**: 手绘插画风，色彩明亮柔和，日系/治愈系游戏UI感

### 快速生成

使用主脚本 `generate_theme_v3.py`：

```bash
python scripts/generate_theme_v3.py
```

或自定义参数：

```python
from scripts.generate_theme_v3 import build_prompt_v3, generate_image

prompt = build_prompt_v3(
    theme="alien",  # 主题：alien/school/halloween/summer/default
    character_mode="double",  # 角色数量：single/double/multiple
    main_title="外星来客",
    sub_title="全新外星人主题外观上线",
    character_desc="穿着外星人主题发光服装，头戴天线头饰",
    character_action="兴奋地指向天空中的飞碟",
    expression="超级兴奋、眼睛闪闪发光",
    scene_elements="小镇夜晚场景——飞碟悬浮在空中、星星闪烁"
)

result = generate_image(
    prompt=prompt,
    output_path="output.jpeg"
)
```

### 角色配置

| 类型 | 适用场景 | 角色数 | 面积要求 | 动作风格 |
|------|---------|-------|---------|---------|
| `single` | 公告类 | 1个 | 占屏幕25%+ | 姿态自然大方 |
| `double` | 皮肤类 | 2个 | 占屏幕40%+ | 动作夸张有张力 |
| `multiple` | 热闹场景 | 多个 | 占屏幕45%+ | 动作夸张有张力 |

### 主题库

| 主题ID | 背景 | 光线 | 氛围 |
|--------|------|------|------|
| `default` | 浅蓝天空，白云，小花 | 明亮阳光 | 友好、温馨、期待 |
| `alien` | 深蓝紫星空，飞碟光束 | 星光和光效 | 神秘、奇幻、未来感 |
| `school` | 秋日黄昏，梧桐落叶 | 温暖午后阳光 | 温馨、学院风、书卷气 |
| `halloween` | 暗紫夜空，明月，南瓜灯 | 南瓜灯暖光和月光 | 神秘、俏皮、节日氛围 |
| `summer` | 清澈蓝天，白云，海边 | 明亮夏日阳光 | 清凉、活力、放松 |

### 参考图URL（8张心动小镇官方图）

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

### 完整Prompt模板

见 `references/styles/announcement_cover.md`

---

---

## 配置结构 v2.0

### 目录结构

```
config/
├── games/                    # 游戏专属配置
│   ├── heartopia.json       # 心动小镇配置
│   ├── _template.json       # 新增游戏模板
│   └── ...
├── styles/                   # 视觉风格定义（JSON）
│   └── announcement_cover.json
├── themes/
│   └── _default_themes.json  # 共享主题库
└── size_registry.json       # 平台尺寸配置
```

### 新增游戏流程

1. **复制模板**
   ```bash
   cp config/games/_template.json config/games/my_game.json
   ```

2. **编辑配置**
   ```json
   {
     "game_key": "my_game",
     "game_name": "我的游戏",
     "reference_images": {
       "source": "urls",
       "urls": ["https://...", "https://..."]
     },
     "visual": {
       "default_theme": "default",
       "default_character_mode": "single"
     }
   }
   ```

3. **使用**
   ```python
   from scripts.image_generator import ImageGenerator
   gen = ImageGenerator(game_key="my_game")
   result = gen.generate(main_title="测试标题")
   ```

### 配置继承机制

**主题**：默认主题库 → 游戏覆盖 → 游戏自定义
**角色模式**：风格默认 → 游戏覆盖 → 游戏自定义

通过 `inherit_default: false` 可禁用继承。

### 可用主题

- `default`, `summer`, `winter`, `spring`
- `halloween`, `alien`, `school`
- `anniversary`, `chinese_new_year`, `cyberpunk`

通过 `themes.custom` 添加游戏专属主题。

---

## 扩展说明

- **新增游戏**：复制 `config/games/_template.json`，填入参考图URL即可
- **新增视觉风格**：在 `config/styles/` 下新建 `<style_id>.json`
- **新增主题**：在 `config/themes/_default_themes.json` 添加，或在游戏配置 `themes.custom` 中添加
- **新增角色模式**：在风格配置或游戏配置的 `character_modes` 中添加
- **新增平台/尺寸**：在 `config/size_registry.json` 的 `sizes` 中新增

**当前主要使用：火山引擎 Doubao-Seedream-4.5**

可灵AI作为备用方案保留。
