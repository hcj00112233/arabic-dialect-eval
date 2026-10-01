#!/usr/bin/env python3
"""用本机 Codex CLI(GPT-6 Astra, ChatGPT 订阅鉴权)跑阿语评测。
每条 case 一次独立 codex exec 调用,保证上下文零污染。
用法:
  python3 run_eval_codex.py [--cases cases/cases_full.jsonl] [--workers 4] [--only S-T1-01,E-T1-02]
"""
import argparse, json, subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = Path(__file__).resolve().parent
CODEX = "codex"  # npm 全局安装的新版(0.159+);app 内置的旧版不支持 gpt-6-astra

INSTR = """You are answering ONE Arabic language test case. Rules:
- Do NOT use any tools. Do NOT read or write files. Answer directly.
- Detect the register implied by the case (Modern Standard Arabic, Saudi dialect, or Egyptian dialect) and answer ENTIRELY in that register. Never answer in English unless the case explicitly asks for it.
- If the case contains Arabizi or mixed Arabic-Latin script, interpret it as intended.
- Output the answer only. No explanations, no commentary, no headers.

Case:
"""


def run_case(case, timeout=600):
    cid = case["id"]
    prompt = INSTR + case["prompt"]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "last.txt"
        cmd = [CODEX, "exec", "--skip-git-repo-check", "-s", "read-only",
               "-C", td, "-o", str(out), prompt]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            resp = out.read_text().strip() if out.exists() else ""
            if not resp:  # 兜底:从 stdout 里找 final message
                resp = p.stdout.strip().split("\n")[-1] if p.stdout.strip() else ""
            return {"case_id": cid, "model": "gpt-6-astra", "response": resp,
                    "error": None if resp else (p.stderr.strip()[-300:] or "empty response")}
        except subprocess.TimeoutExpired:
            return {"case_id": cid, "model": "gpt-6-astra", "response": "", "error": "timeout"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="cases/cases_full.jsonl")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    cases = [json.loads(l) for l in open(BASE / args.cases)]
    if args.only:
        keep = set(args.only.split(","))
        cases = [c for c in cases if c["id"] in keep]
    out_path = Path(args.out) if args.out else \
        BASE / "results" / (time.strftime("%m%d_%H%M") + "_responses_gpt6astra.jsonl")

    done, errs = 0, 0
    with open(out_path, "w") as f, ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_case, c): c for c in cases}
        for fut in as_completed(futs):
            r = fut.result()
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
            done += 1
            if r["error"]: errs += 1
            print(f"[{done}/{len(cases)}] {r['case_id']} {'ERR:' + r['error'][:80] if r['error'] else 'ok'}")
    print(f"完成: {out_path}  错误 {errs} 条")


if __name__ == "__main__":
    main()
