#!/usr/bin/env python3
"""干预实验: bad case -> 修复 -> 重跑 -> 对比。结果存 results/interventions.json"""
import json, os, re, time, urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
CRED = Path.home() / ".kimi-code" / "credentials" / "kimi-code.json"
ENV_FILE = Path.home() / ".config" / "eval_keys.env"
for line in ENV_FILE.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"'))

cases = {json.loads(l)["id"]: json.loads(l) for l in open(BASE/"cases/cases_full.jsonl")}

def call_kimi(messages, max_tokens=16384):
    cred = json.loads(CRED.read_text())
    req = urllib.request.Request("https://api.kimi.com/coding/v1/chat/completions",
        data=json.dumps({"model":"k3-256k","messages":messages,"temperature":1,"max_tokens":max_tokens}).encode(),
        headers={"Authorization":f"Bearer {cred['access_token']}","Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.loads(r.read().decode())
    m = d["choices"][0]["message"]
    return m.get("content") or "", m.get("reasoning_content") or ""

def call_ds(messages):
    req = urllib.request.Request("https://api.deepseek.com/chat/completions",
        data=json.dumps({"model":"deepseek-chat","messages":messages,"temperature":0.3}).encode(),
        headers={"Authorization":f"Bearer {os.environ['DEEPSEEK_API_KEY']}","Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.loads(r.read().decode())
    return d["choices"][0]["message"]["content"]

out = {}

# --- 实验1: S-T3-05 语体错配(A2) -> 系统提示词约束语体 ---
SYS = "你是沙特利雅得本地人。你的全部输出必须使用沙特Najdi日常口语(像发推特/跟朋友说话那样),严禁使用MSA书面句式、正式演讲措辞、古典表达。"
p = cases["S-T3-05"]["prompt"]
out["exp1_S-T3-05"] = {
  "fix": "系统提示词显式约束语体(提示词层)",
  "kimi": call_kimi([{"role":"system","content":SYS},{"role":"user","content":p}])[0],
  "ds": call_ds([{"role":"system","content":SYS},{"role":"user","content":p}]),
}
print("exp1 done", flush=True)

# --- 实验2: E-T7-04 Arabizi 9=ص -> 提示词注入映射表(RAG式外挂) ---
MAP = """参考(埃及Arabizi数字映射基线): 2=ء或ق(埃及方言ق发/ʔ/), 3=ع, 3'=غ, 5=خ, 6=ط, 7=ح, 7'=خ, 8=غ或ق(海湾用法,埃及基本不用), 9=ص, 9'=ض。注意数字可能兼作真实数字,需按上下文消歧。
"""
p2 = cases["E-T7-04"]["prompt"]
out["exp2_E-T7-04"] = {
  "fix": "提示词注入埃及Arabizi映射表(短期RAG式外挂)",
  "kimi": call_kimi([{"role":"user","content":MAP+p2}])[0],
  "ds": call_ds([{"role":"user","content":MAP+p2}]),
}
print("exp2 done", flush=True)

# --- 实验3: CoT语言切换观测(K3 thinking, 3条T6) ---
cot = {}
for cid in ["S-T6-03","E-T6-03","M-T6-01"]:
    content, reasoning = call_kimi([{"role":"user","content":cases[cid]["prompt"]}])
    ar = len(re.findall(r'[\u0600-\u06FF]', reasoning))
    lat = len(re.findall(r'[a-zA-Z]', reasoning))
    cjk = len(re.findall(r'[\u4e00-\u9fff]', reasoning))
    cot[cid] = {"dialect": cases[cid]["dialect"], "reasoning_chars": len(reasoning),
                "arabic": ar, "latin": lat, "cjk": cjk,
                "reasoning_sample": reasoning[:300]}
    print(f"cot {cid} done", flush=True)
out["exp3_cot"] = cot

json.dump(out, open(BASE/"results/interventions.json","w"), ensure_ascii=False, indent=1)
print("saved results/interventions.json")
