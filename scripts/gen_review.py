#!/usr/bin/env python3
"""从 responses jsonl + cases jsonl 生成人工复核稿(与 deepseek_review.md 同格式)。
用法: python3 gen_review.py --responses results/xxx_responses.jsonl [--cases cases/cases_full.jsonl] [--name "Kimi K3"] [--out results/kimi3_review.md]
"""
import argparse, json
from pathlib import Path

BASE = Path(__file__).resolve().parent

ap = argparse.ArgumentParser()
ap.add_argument("--responses", required=True)
ap.add_argument("--cases", default=str(BASE / "cases" / "cases_full.jsonl"))
ap.add_argument("--name", default="Kimi K3")
ap.add_argument("--out", default=None)
ap.add_argument("--core", action="store_true", help="核心集复核稿格式(同 deepseek_core_review.md)")
a = ap.parse_args()

cases = [json.loads(l) for l in Path(a.cases).read_text().splitlines() if l.strip()]
resp = {}
for l in Path(a.responses).read_text().splitlines():
    if l.strip():
        r = json.loads(l)
        resp[r["case_id"]] = r["response"]

out = a.out or str(BASE / "results" / "kimi3_review.md")
if a.core:
    parts = [f"# {a.name} 核心集复核稿（{len(cases)}条）\n",
             "> 只评这些，其余由 judge 初筛+抽样复核。判定格式：D1-D6 各维度 0-3 分 + 归因标签 + 一句话依据。\n\n\n---"]
    gold_label, trap_label = "**Gold**", "**陷阱**"
else:
    parts = [f"# {a.name} 阿语评测结果（人工复核用）\n",
             f"> 每条格式：case 元信息 → gold 标准 → {a.name} 回答。复核时请在每条后面标注你的判定。\n\n\n---"]
    gold_label, trap_label = "**Gold 标准**", "**预设陷阱**"
missing = []
for c in cases:
    r = resp.get(c["id"])
    if r is None:
        missing.append(c["id"])
        r = "__MISSING__"
    parts.append(
        f"## {c['id']} [{c['task_type']} / {c['dialect']} / {c['difficulty']}]\n"
        f"**题目**：{c['prompt_zh']}\n"
        f"**题干**：{c['prompt']}\n"
        f"{gold_label}：{c['gold_criteria']}\n"
        f"{trap_label}：{c['trap']}\n\n"
        f"**{a.name} 回答**：\n{r}\n\n"
        f"**专家判定**：【待填】\n\n---"
    )
Path(out).write_text("\n".join(parts))
print(f"已生成: {out}  ({len(cases)} 条, 缺失 {len(missing)}: {missing or '无'})")
