# 参考图库（Refs）

本目录用于存放**公告图生成时的参考图**，支持按游戏或按风格分子目录。生成时可将对应目录下的图片路径（或转为 base64）传入图像 API 作为风格/构图参考（若后端支持图生图或 reference image）。

## 目录约定

- **按游戏**：`refs/<game_key>/`  
  例如 `refs/heartopia/`、`refs/afk_journey/`。放入该游戏历史公告图、品牌图等，生成时优先使用当前游戏的 refs。
- **按风格**：`refs/<style_id>/`  
  例如 `refs/warm_casual/`、`refs/official_formal/`。放入该风格的示例图，供所有游戏在该风格下共用。

## 使用方式

1. 在对应子目录下放入图片文件（如 `.png`、`.jpg`）。
2. Skill 执行时会根据当前 **game_key** 与 **style_id** 解析参考图路径：
   - 优先：`refs/<game_key>/` 下全部或部分文件；
   - 补充：`refs/<style_id>/` 下全部或部分文件。
3. 若图像 API 要求 base64：由调用方将图片读入并转为 base64 后填入请求体；若支持 URL：可使用本地 file path 或先上传后传 URL。

## 扩展

- **新游戏**：新建 `refs/<game_key>/` 并放入参考图即可。
- **新风格**：新建 `refs/<style_id>/` 并放入该风格的示例图即可。

无需修改 SKILL 或配置，仅依赖目录存在与文件列表。
