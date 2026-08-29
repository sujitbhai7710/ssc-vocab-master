#!/usr/bin/env python3
"""Shared AI helper for the SSC grammar pipeline.

Uses the justwoker.icu OpenAI-compatible endpoint with model claude-opus-4-8.
Two API keys are rotated in parallel for throughput. Calls are retried with
exponential backoff. Designed to be imported by other scripts.
"""
import os, json, time, threading, random
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error

API_URL = os.environ.get("JUSTWOKER_API_URL", "https://api.justwoker.icu/v1/chat/completions")
MODEL = os.environ.get("JUSTWOKER_MODEL", "claude-opus-4-8")
# Read API keys from env. Comma-separated, or two env vars JUSTWOKER_KEY_1 / JUSTWOKER_KEY_2.
# NEVER hardcode keys in this file. Copy .env.example -> .env and fill in your keys.
_env_keys = []
if os.environ.get("JUSTWOKER_KEYS"):
    _env_keys = [k.strip() for k in os.environ["JUSTWOKER_KEYS"].split(",") if k.strip()]
elif os.environ.get("JUSTWOKER_KEY_1"):
    _env_keys = [os.environ["JUSTWOKER_KEY_1"]]
    if os.environ.get("JUSTWOKER_KEY_2"):
        _env_keys.append(os.environ["JUSTWOKER_KEY_2"])
KEYS = _env_keys
if not KEYS:
    raise RuntimeError(
        "No API keys found. Set JUSTWOKER_KEYS (comma-separated) or JUSTWOKER_KEY_1/JUSTWOKER_KEY_2 env vars. "
        "See scripts/.env.example."
    )
_key_lock = threading.Lock()
_key_idx = 0

def _next_key():
    global _key_idx
    with _key_lock:
        k = KEYS[_key_idx % len(KEYS)]
        _key_idx += 1
        return k

def chat(messages, *, temperature=0.3, max_tokens=4096, timeout=180, retries=4):
    """Single chat completion. Returns the assistant text (str)."""
    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(body).encode("utf-8")
    last_err = None
    for attempt in range(retries):
        key = _next_key()
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                obj = json.loads(resp.read().decode("utf-8"))
                return obj["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read()[:300]}"
            wait = (2 ** attempt) + random.random()
            time.sleep(min(wait, 20))
        except Exception as e:
            last_err = str(e)
            time.sleep((2 ** attempt) + random.random())
    raise RuntimeError(f"AI call failed after {retries} retries: {last_err}")

def chat_json(messages, *, temperature=0.2, max_tokens=4096, timeout=180, retries=4):
    """Chat completion that must return valid JSON."""
    msgs = list(messages)
    if msgs and isinstance(msgs[-1], dict):
        c = msgs[-1].get("content", "")
        if "json" not in c.lower()[:200]:
            msgs[-1] = {**msgs[-1], "content": c + "\n\nReturn ONLY valid minified JSON, no prose, no code fences."}
    text = chat(msgs, temperature=temperature, max_tokens=max_tokens, timeout=timeout, retries=retries)
    return _extract_json(text)

def _extract_json(text):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)
        t = t[1] if len(t) >= 2 else text
        if t.startswith("json"):
            t = t[4:]
    t = t.strip()
    start = min([i for i in [t.find("{"), t.find("[")] if i != -1] or [-1])
    if start == -1:
        raise ValueError(f"No JSON found in: {text[:300]}")
    try:
        return json.loads(t[start:])
    except Exception:
        for end in range(len(t), start, -1):
            try:
                return json.loads(t[start:end])
            except Exception:
                continue
    raise ValueError(f"Could not parse JSON: {text[:300]}")

def parallel_map(items, fn, *, workers=6, desc=""):
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fn, it): it for it in items}
        done = 0
        for fut in as_completed(futs):
            it = futs[fut]
            try:
                res = fut.result()
                results.append((it, res))
            except Exception as e:
                results.append((it, e))
            done += 1
            if desc and done % 10 == 0:
                print(f"  [{desc}] {done}/{len(items)}", flush=True)
    return results

if __name__ == "__main__":
    print("Testing AI API with both keys...")
    def test_key(k):
        body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": "Reply with the single word: OK"}], "temperature": 0, "max_tokens": 10}).encode()
        req = urllib.request.Request(API_URL, data=body, headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                o = json.loads(r.read())
                return f"KEY ...{k[-6:]}: " + o["choices"][0]["message"]["content"]
        except Exception as e:
            return f"KEY ...{k[-6:]}: FAIL {e}"
    for k in KEYS:
        print(test_key(k))
    print("\nFull chat() test:")
    print(chat([{"role": "user", "content": "What is 7*8? Reply with just the number."}], max_tokens=20))
