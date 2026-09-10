#!/usr/bin/env python3
"""AI helper using Justwoker /v1/messages endpoint (Anthropic-style) with gpt-5.6-sol.
Fast + reliable. Used by build_clean_grammar.py.
"""
import os, json, time, random, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "https://api.justwoker.icu/v1/messages"
MODEL = os.environ.get("JW_MODEL", "gpt-5.6-sol")
KEY = os.environ.get("JW_KEY", "sk-P2RGSaBYRpNJBxNFcpI1bLwKE5QGXJY0GQCiTd8JjpAm1b0G")

def chat(messages, *, temperature=0.2, max_tokens=2000, timeout=120, retries=4):
    """Anthropic-style messages API. Returns assistant text (str)."""
    # convert OpenAI-style messages (system+user) to Anthropic-style (system top-level + messages)
    system = ""
    user_msgs = []
    for m in messages:
        if m["role"] == "system": system = m["content"]
        else: user_msgs.append({"role": m["role"], "content": m["content"]})
    if not user_msgs:
        user_msgs = [{"role": "user", "content": ""}]
    body_obj = {"model": MODEL, "max_tokens": max_tokens, "messages": user_msgs}
    if system: body_obj["system"] = system
    body = json.dumps(body_obj).encode()
    last_err = None
    for attempt in range(retries):
        req = urllib.request.Request(API_URL, data=body, headers={
            "x-api-key": KEY, "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        }, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                obj = json.loads(r.read().decode())
                # Anthropic format: content is array of {text, type}
                content = obj.get("content", [])
                if isinstance(content, list) and content:
                    return content[0].get("text", "")
                return ""
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read()[:200]}"
            time.sleep((2**attempt)+random.random())
        except Exception as e:
            last_err = str(e)
            time.sleep((2**attempt)+random.random())
    raise RuntimeError(f"justwoker messages failed after {retries} retries: {last_err}")

def chat_json(messages, *, temperature=0.0, max_tokens=2000, timeout=120, retries=5):
    msgs = list(messages)
    if msgs and isinstance(msgs[-1], dict):
        c = msgs[-1].get("content","")
        if "json" not in c.lower()[:200]:
            msgs[-1] = {**msgs[-1], "content": c + "\n\nReturn ONLY valid minified JSON, no prose, no code fences."}
    text = chat(msgs, temperature=temperature, max_tokens=max_tokens, timeout=timeout, retries=retries)
    return _extract(text)

def _extract(text):
    t = text.strip()
    if t.startswith("```"):
        parts = t.split("```")
        if len(parts) >= 3: t = parts[1]
        if t.startswith("json"): t = t[4:]
    t = t.strip()
    start = min([i for i in [t.find("{"), t.find("[")] if i != -1] or [-1])
    if start == -1: raise ValueError(f"no JSON in: {text[:200]}")
    try: return json.loads(t[start:])
    except Exception:
        for end in range(len(t), start, -1):
            try: return json.loads(t[start:end])
            except: continue
    raise ValueError(f"could not parse: {text[:200]}")

def parallel_map(items, fn, *, workers=6, desc=""):
    """Parallel via ThreadPoolExecutor (works fine here)."""
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fn, it): it for it in items}
        done = 0
        for fut in as_completed(futs):
            it = futs[fut]
            try: results.append((it, fut.result()))
            except Exception as e: results.append((it, e))
            done += 1
            if desc and done % 10 == 0:
                print(f"  [{desc}] {done}/{len(items)}", flush=True)
    if desc: print(f"  [{desc}] done {len(items)}/{len(items)}", flush=True)
    return results

if __name__ == "__main__":
    print("model:", MODEL)
    print(chat([{"role":"user","content":"reply OK"}], max_tokens=50))
    print(chat_json([{"role":"user","content":"return {\"ok\":true}"}]))
