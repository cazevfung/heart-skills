---
name: user_acquisition
description: "当用户提供付费/留存/渠道数据（文件或粘贴）需要 LTV 思路或买量 ROI 测算框架时使用本 skill。给出公式、假设、口径与解读注意点；侧重「回收与获客效率」。可与 game_monetization 并列：game_monetization 偏付费结构与健康度，本 skill 偏 LTV/买量 ROI 测算与解读。"
metadata:
  {
    "copaw": {
      "emoji": "📊",
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

# LTV 与买量 ROI 测算专家 Skill

本 skill 在用户提供付费/留存/渠道数据（文件或粘贴）时，给出版本思路或买量 ROI 测算框架：公式、假设、口径、解读注意点。不替代专业 BI 工具，侧重「回收与获客效率」的测算逻辑与报告输出。

## 何时使用

- 用户提到：**LTV**、买量 ROI、回收、CPI、付费回收、留存回收、LTV/CAC、回收周期
- 用户问：如何算 LTV、买量 ROI 怎么估、这些数据怎么解读
- 用户提供了指标文件或表格（含日期、付费、留存、渠道等列），希望得到测算说明与解读建议

若用户仅要付费结构/健康度分析（含 UGC），使用 **game_monetization**；若用户提供了指标数据且要 LTV/ROI 测算与解读，使用本 skill。

## 参数提取

| 参数 | 含义 | 默认值 |
|------|------|--------|
| **data_source** | 用户提供的指标文件路径或粘贴内容 | 用户提供 |
| **analysis_focus** | 测算焦点：LTV / 买量ROI / 回收周期 / 综合 | 从用户意图推断 |
| **product** | 产品/游戏名称（可选） | 从用户消息或数据推断 |
| **report_format** | `markdown` / `feishu` | `markdown` |
| **output_path** | 输出目录 | `user/documents/游戏分析报告/` |
| **output_destination** | `file` 仅写文件 / `chat` 仅在对话中输出 | `file` |

执行前 Echo 已解析参数。

## 数据与就绪

- 用户提供的数据需包含可识别列：如日期、付费率、ARPU、ARPPU、LTV、留存、渠道、CPI、CAC 等（见 references/ltv_roi_framework.md）。
- 通过 **file_reader** 或用户粘贴读取；若无法解析，列出已识别列并请用户确认。

## 执行流程

### Phase 1 — 理解与输入

1. 解析用户消息，填写参数表；获取用户数据（路径或粘贴）。
2. 识别列名与样本行，确认可解析；若无法解析则告知用户并列出已识别列。
3. Echo 已解析参数与数据概况。

### Phase 2 — 测算与解读

1. 阅读 **references/ltv_roi_framework.md**（公式、假设、口径、解读注意）。
2. 按 **analysis_focus** 执行：LTV 思路（如 LTV = ARPU × 生命周期月数或按留存曲线估算）；买量 ROI（如 ROI = LTV / CAC，或回收周期）；回收周期（如 N 日回本）。
3. 注明假设与口径（如留存口径、付费口径、渠道口径）；解读注意点（如样本偏差、时间窗口、品类对比）。

### Phase 3 — 输出

1. 按 **references/template_ltv_roi.md** 生成测算说明与解读建议文档。
2. 按 `output_destination` 与 `report_format` 写文件或调用飞书工具。

## 与其他 skill 的关系

| 场景 | 使用 skill |
|------|------------|
| LTV/买量 ROI 测算、回收周期、指标解读 | **user_acquisition**（本 skill） |
| 付费结构、付费健康度、UGC 付费洞察 | **game_monetization** |

## 参考文件

- LTV/ROI 公式与口径：[references/ltv_roi_framework.md](references/ltv_roi_framework.md)
- 测算报告模板：[references/template_ltv_roi.md](references/template_ltv_roi.md)
