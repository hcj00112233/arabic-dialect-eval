#!/usr/bin/env python3
"""judge 初筛: deepseek-chat 按 rubric 给 kimi3 回答打分,输出与 mini_judge.json 同格式。
用法: python3 judge_kimi3.py [--input results/0930_0034_responses.jsonl] [--out results/kimi3_judge.json] [--workers 8]
"""
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = Path(__file__).resolve().parent
ENV_FILE = Path.home() / ".config" / "eval_keys.env"

JUDGE_SYSTEM = """你是一名阿语评测助理。请严格按给定 rubric 维度对被测回答打分(0-3)并给出一句理由。
注意:你的评分是初筛,最终判定由阿语专家人工完成。拿不准时标 uncertain=true。
输出 JSON: {"scores":{"D1":0-3,...},"attribution":["A1"...],"reason":"...","uncertain":false}"""


def load_env():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


def parse_judge(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError("no json")
    d = json.loads(m.group(0))
    return {
        "scores": d.get("scores", {}),
        "tags": d.get("attribution", d.get("tags", [])),
        "reason": d.get("reason", ""),
        "uncertain": bool(d.get("uncertain", False)),
    }


def judge_one(client, jm, rubric, rec, max_retries=3):
    prompt = f"RUBRIC:\n{rubric}\n\n被测回答:\n{rec['response']}\n\n请评分。"
    for attempt in range(max_retries):
        try:
            r = client.chat.completions.create(
                model=jm,
                messages=[{"role": "system", "content": JUDGE_SYSTEM},
                          {"role": "user", "content": prompt}],
                temperature=0)
            return parse_judge(r.choices[0].message.content)
        except Exception as e:
            if attempt == max_retries - 1:
                return {"scores": {}, "tags": [], "reason": f"__ERROR__: {e}", "uncertain": True}
            time.sleep(2 ** attempt * 5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    load_env()
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
    rubric = (BASE / "rubric.md").read_text()
    recs = [json.loads(l) for l in Path(a.input).read_text().splitlines() if l.strip()]

    results = {}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(judge_one, client, "deepseek-chat", rubric, rec): rec["case_id"] for rec in recs}
        done = 0
        for fut in as_completed(futs):
            cid = futs[fut]
            results[cid] = fut.result()
            done += 1
            print(f"[{done}/{len(recs)}] {cid} judged", flush=True)

    ordered = {rec["case_id"]: results[rec["case_id"]] for rec in recs}
    Path(a.out).write_text(json.dumps(ordered, ensure_ascii=False, indent=1))
    n_err = sum(1 for v in ordered.values() if v["reason"].startswith("__ERROR__"))
    print(f"\n已保存: {a.out}  (judge失败 {n_err}/{len(recs)})")


if __name__ == "__main__":
    main()
