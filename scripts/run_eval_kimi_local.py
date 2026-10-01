#!/usr/bin/env python3
"""用本机 Kimi Code 订阅(OAuth, api.kimi.com/coding/v1)跑 kimi k3 阿语评测。
用法:
  python3 run_eval_kimi_local.py [--cases cases/cases_full.jsonl] [--model k3-256k] [--workers 8]
Token 从 ~/.kimi-code/credentials/kimi-code.json 读取,临近过期自动 refresh 并回写。
"""
import argparse, json, threading, time, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = Path(__file__).resolve().parent
CRED = Path.home() / ".kimi-code" / "credentials" / "kimi-code.json"
API = "https://api.kimi.com/coding/v1/chat/completions"
OAUTH_TOKEN_URL = "https://auth.kimi.com/api/oauth/token"
CLIENT_ID = "17e5f671-d194-4dfb-9706-5516cb48c098"

_lock = threading.Lock()
_cred = {}


def _post_form(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def load_cred():
    global _cred
    _cred = json.loads(CRED.read_text())


def save_cred():
    tmp = CRED.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(_cred, ensure_ascii=False))
    tmp.replace(CRED)


def refresh_if_needed(force=False):
    with _lock:
        if not force and _cred["expires_at"] - time.time() > 120:
            return
        d = _post_form(OAUTH_TOKEN_URL, {
            "client_id": CLIENT_ID,
            "refresh_token": _cred["refresh_token"],
            "grant_type": "refresh_token",
        })
        _cred["access_token"] = d["access_token"]
        if d.get("refresh_token"):
            _cred["refresh_token"] = d["refresh_token"]
        _cred["expires_at"] = time.time() + d.get("expires_in", 3600)
        save_cred()
        print(f"[auth] token refreshed, expires in {d.get('expires_in')}s", flush=True)


def call_model(model, prompt, max_retries=4):
    for attempt in range(max_retries):
        refresh_if_needed()
        req = urllib.request.Request(API, data=json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 1,
            "max_tokens": 16384,
        }).encode(), headers={
            "Authorization": f"Bearer {_cred['access_token']}",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                d = json.loads(r.read().decode())
            return d["choices"][0]["message"].get("content") or ""
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            if e.code == 401 and attempt < max_retries - 1:
                refresh_if_needed(force=True)
                continue
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                time.sleep(2 ** attempt * 5)
                continue
            return f"__ERROR__: HTTP {e.code} {body}"
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt * 5)
                continue
            return f"__ERROR__: {type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(BASE / "cases" / "cases_full.jsonl"))
    ap.add_argument("--model", default="k3-256k")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    cases = [json.loads(l) for l in Path(a.cases).read_text().splitlines() if l.strip()]
    load_cred()
    refresh_if_needed()

    ts = time.strftime("%m%d_%H%M")
    out = BASE / "results" / f"{ts}_responses.jsonl"
    results = {}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(call_model, a.model, c["prompt"]): c["id"] for c in cases}
        done = 0
        for fut in as_completed(futs):
            cid = futs[fut]
            results[cid] = fut.result()
            done += 1
            print(f"[{done}/{len(cases)}] {cid} done", flush=True)

    with out.open("w") as f:
        for c in cases:  # 保持题目顺序
            f.write(json.dumps({"case_id": c["id"], "model": "kimi3",
                                "response": results[c["id"]]}, ensure_ascii=False) + "\n")
    n_err = sum(1 for v in results.values() if v.startswith("__ERROR__"))
    print(f"\n已保存: {out}  (错误 {n_err}/{len(cases)})")


if __name__ == "__main__":
    main()
