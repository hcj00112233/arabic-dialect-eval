# Arabic Dialect Eval — 阿语方言语体能力三模型横评

**LLM Arabic Studies** ｜ DeepSeek-V4-Flash · Kimi K3 · GPT-6 Astra 三模型阿拉伯语综合能力横评

📄 **在线报告（完整结论与交互式对照）**：https://hcj00112233.github.io/arabic-dialect-eval/

## 这是什么

一套面向**真实产品场景**的阿语能力评测，而非学术 benchmark 复跑：

- **154 条人工原创 case**，覆盖沙特方言 / 埃及方言 / MSA 三种语体，场景含社媒、日常交流、客服、职场、宗教文化敏感题，每题配 Gold 标准与预设陷阱；
- **D1–D6 六维计分**（语体准确性 / 语域切换 / 知识准确性 / 文化适切性 / 推理质量 / 表达水准）+ **A1–A10 归因体系**（语体错配、字母污染、事实幻觉、Arabizi 解析失败等）；
- **judge 初筛 + 人工复核双层管线**：judge 全量 154 条三侧打分，人工层判定 67 / 67 / 72 条（人工判定 + AI 代审分开标注、逐条存档）；
- 产出**产品口径指标**：采纳率、硬伤率、幻觉率、拒答率——直接可写进 PRD 模型行为边界。

## 核心结论（人工层）

| 指标 | DeepSeek-V4-Flash | Kimi K3 | GPT-6 Astra |
|---|---|---|---|
| 采纳率（同意+基本同意） | 94.0% | 89.6% | **97.2%** |
| 硬伤率 | 6.0% | 9.0% | **2.8%** |
| 幻觉率（A7） | 1.5% | 1.5% | 1.4% |
| 拒答率 | 0% | 0% | 0% |

judge-人工校准实测揭示 judge 系统性盲区（漏检、幻觉式扣分），所有关键结论以人工层为准——方法与证据见报告第 3 节。

## 仓库结构

```
index.html      评测报告（GitHub Pages 首页）
cases/
  cases_full.jsonl                154 条人工原创 case（Gold 标准 + 预设陷阱）
scripts/
  run_eval.py                     DeepSeek 侧评测管线
  run_eval_kimi_local.py          Kimi K3 侧评测管线（k3-256k）
  run_eval_codex.py               GPT-6 Astra 侧评测管线
  judge_kimi3.py                  judge 初筛（deepseek-chat，D1–D6 打分 + A1–A10 归因）
  gen_review.py                   复核稿生成
  run_interventions.py            干预实验（提示词层 / 工程层修复验证）
data/
  responses_{deepseek,kimi3,gpt6astra}.jsonl   三模型各 154 条原始回答存档
  {ds,kimi3,gpt6astra}_verdicts.json           三侧人工层判定（人工判定 + AI 代审分开标注）
  expert_verdicts.json            DS 早期人工判定 11 条
  {ds,kimi3,gpt6astra}_judge.json              judge 三侧全量初筛结果
  interventions.json              干预实验存档
review/
  rubric.md                       完整评分框架（D1–D6 / A1–A10）
  arabizi_reference.md            Arabizi 数字映射调研基线
  deepseek_review.md              DeepSeek 全量复核稿（含逐条 judge 归因）
  kimi3_core_review.md            Kimi K3 复核稿（核心）
  kimi3_extra_review.md           Kimi K3 复核稿（补充）
  gpt6astra_core_review.md        GPT-6 Astra 复核稿（核心）
  gpt6astra_extra_review.md       GPT-6 Astra 复核稿（补充）
  gpt6astra_manual_review.md      Astra 人工复核 13 条原始记录
  *.html                          上述 MD 的网页版，按 case 锚点定位（报告内直接跳转）
```

API 密钥均从环境变量 / 外部配置读取，仓库内不含任何凭证。

## 与现有工作的关系

PALM / Dialectal-MMLU / AraDiCE / Jawaher 等公开工作（均发表于 2026 年前）覆盖的是理解型或文化知识型评测；本评测的增量在四个维度：**真实产品场景、语域切换显式计分、工程呈现层（RTL 混排 / 数字系统 / Arabizi）、干预实验**。详细对标矩阵见报告第 1.6 节。

## 作者

**Aaron** · 求职作品集 · 2026
