#!/usr/bin/env python3
"""阿语方言模型评测 runner
用法:
  python3 run_eval.py --models deepseek,gpt,gemini --cases cases/cases_draft.jsonl
  python3 run_eval.py --judge --input results/xxx_responses.jsonl
Keys 读取自 ~/.config/eval_keys.env (DEEPSEEK_API_KEY / OPENROUTER_API_KEY)
"""
import argparse, json, os, sys, time
from pathlib import Path
from openai import OpenAI

ENV_FILE = Path.home() / ".config" / "eval_keys.env"
BASE = Path(__file__).resolve().parent

MODELS = {
    # 直接 API
    "deepseek":  dict(provider="deepseek",   model="deepseek-chat"),
    # 通过 OpenRouter
    "gpt":       dict(provider="openrouter", model="openai/gpt-4o"),
    "claude":    dict(provider="openrouter", model="anthropic/claude-sonnet-4"),
    "gemini":    dict(provider="openrouter", model="google/gemini-2.5-pro"),
    "qwen":      dict(provider="openrouter", model="qwen/qwen3-235b-a22b"),
    "falcon":    dict(provider="openrouter", model="tiiuae/falcon-180b-chat"),
    "kimi":      dict(provider="openrouter", model="moonshotai/kimi-k2"),
}

JUDGE_SYSTEM = """你是一名阿语评测助理。请严格按给定 rubric 维度对被测回答打分(0-3)并给出一句理由。
注意:你的评分是初筛,最终判定由阿语专家人工完成。拿不准时标 uncertain=true。
输出 JSON: {"scores":{"D1":0-3,...},"attribution":["A1"...],"reason":"...","uncertain":false}"""

def load_env():
    if not ENV_FILE.exists():
        sys.exit(f"缺少 {ENV_FILE},请先创建并填入 API key")
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

def get_client(provider):
    if provider == "deepseek":
        return OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
                      base_url="https://api.deepseek.com")
    return OpenAI(api_key=os.environ["OPENROUTER_API_KEY"],
                  base_url="https://openrouter.ai/api/v1")

def run_cases(model_keys, cases_file):
    cases = [json.loads(l) for l in Path(cases_file).read_text().splitlines() if l.strip()]
    ts = time.strftime("%m%d_%H%M")
    out = BASE / "results" / f"{ts}_responses.jsonl"
    with out.open("w") as f:
        for mk in model_keys:
            cfg = MODELS[mk]
            client = get_client(cfg["provider"])
            for c in cases:
                try:
                    r = client.chat.completions.create(
                        model=cfg["model"],
                        messages=[{"role": "user", "content": c["prompt"]}],
                        temperature=0.3)
                    resp = r.choices[0].message.content
                except Exception as e:
                    resp = f"__ERROR__: {e}"
                f.write(json.dumps({"case_id": c["id"], "model": mk,
                                    "response": resp}, ensure_ascii=False) + "\n")
                print(f"[{mk}] {c['id']} done")
    print(f"\n已保存: {out}")
    return out

def judge(responses_file, judge_model="deepseek"):
    rubric = (BASE / "rubric.md").read_text()
    client = get_client(MODELS[judge_model]["provider"])
    jm = MODELS[judge_model]["model"]
    out = str(responses_file).replace("_responses.jsonl", "_judged.jsonl")
    with open(out, "w") as fo:
        for line in open(responses_file):
            rec = json.loads(line)
            prompt = f"RUBRIC:\n{rubric}\n\n被测回答:\n{rec['response']}\n\n请评分。"
            try:
                r = client.chat.completions.create(
                    model=jm,
                    messages=[{"role": "system", "content": JUDGE_SYSTEM},
                              {"role": "user", "content": prompt}],
                    temperature=0)
                rec["judge_raw"] = r.choices[0].message.content
            except Exception as e:
                rec["judge_raw"] = f"__ERROR__: {e}"
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"已保存: {out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="deepseek")
    ap.add_argument("--cases", default=str(BASE / "cases" / "cases_draft.jsonl"))
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--input")
    a = ap.parse_args()
    load_env()
    if a.judge:
        judge(a.input)
    else:
        run_cases(a.models.split(","), a.cases)
