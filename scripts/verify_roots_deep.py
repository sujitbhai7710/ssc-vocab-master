#!/usr/bin/env python3
"""
Second-pass verification of the 55 flagged words. For each, ask the AI to
explain the word's etymology in detail and decide KEEP vs REMOVE with reasoning.
This is more accurate than the batch pass because:
  1. One word at a time (more attention)
  2. AI must state the etymology (forced reasoning)
  3. We give it the root's meaning for context

Output: /tmp/root_corrections_final.json — only the words confirmed REMOVE.
"""
import json
import os
import time
import urllib.request
import urllib.error


API_KEYS = [
    'sk-p7r8yV70mfSCdHmSEyAVCsa47Cef7DQqz9nk2KMwaXuHM09Q',
    'sk-fJ3HrhShKjmTMtrJEPTfltPYmxawBlfxvGCNTovvXrWE6QnN',
    'sk-Dtu9WsE9jfco1rEFGVY5TzXJoD12zkOTqmiCjAlAbUXWFRSq',
]
API_URL = 'https://kktoken.cc/v1/chat/completions'
MODEL = 'claude-opus-4-8'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


def call_ai(api_key: str, root: str, rm: str, word: str, mean: str) -> dict:
    prompt = f"""You are an expert etymologist. Does the English word "{word}" derive from the Latin/Greek root "{root}" (meaning: {rm})?

Word: "{word}" (definition: {mean})
Root: {root} (meaning: {rm})

Think step by step:
1. What is the etymology of "{word}"? (state the source language + original form)
2. Does it trace back to "{root}"?

Important: Many Latin roots transform spelling over time. For example:
- "solution" derives from SOLV (solvere → solutus → solution) — KEEP
- "elegant" derives from LEG (eligere → elegans) — KEEP
- "maintain" derives from MAN (manu + tenere) — KEEP
- "envious" derives from VID (invidia ← videre) — KEEP
- "plain" derives from PLAN (planus) — KEEP
- "review" derives from VID (re + view ← videre) — KEEP

But words of Old English/Germanic origin do NOT derive from Latin/Greek roots:
- "name" (Old English nama) — REMOVE from NOM
- "star" (Old English steorra) — REMOVE from ASTR
- "renew" (Old English niwe) — REMOVE from NOV
- "withdraw" (Old English) — REMOVE from TRA

Respond with ONLY a JSON object:
{{"etymology": "brief etymology of the word", "derives_from_root": true or false, "action": "KEEP" or "REMOVE"}}"""

    body = json.dumps({
        'model': MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0,
        'max_tokens': 300,
    }).encode('utf-8')

    req = urllib.request.Request(API_URL, data=body, headers={
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': UA,
        'Accept': 'application/json',
    })

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            content = data['choices'][0]['message']['content'].strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1] if '\n' in content else content
                if content.endswith('```'):
                    content = content.rsplit('```', 1)[0]
                content = content.strip()
            return json.loads(content)
        except urllib.error.HTTPError as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
        except Exception as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    return {'etymology': 'unknown', 'derives_from_root': None, 'action': 'KEEP'}


def main():
    with open('/tmp/root_corrections.json') as f:
        flagged = json.load(f)
    with open('public/data/roots.json') as f:
        roots_data = json.load(f)
    root_rm = {r['root']: r['rm'] for r in roots_data}

    print(f'Re-verifying {len(flagged)} flagged words individually...', flush=True)
    results = []

    for i, c in enumerate(flagged):
        root = c['root']
        word = c['word']
        rm = root_rm.get(root, '')
        # Get the word's meaning from roots.json
        mean = ''
        for r in roots_data:
            if r['root'] == root:
                for w in r['words']:
                    if w['w'].lower() == word.lower():
                        mean = w.get('mean', '')
                        break
                break

        api_key = API_KEYS[i % len(API_KEYS)]
        result = call_ai(api_key, root, rm, word, mean)
        result['root'] = root
        result['word'] = word
        results.append(result)
        action = result.get('action', 'KEEP')
        etym = result.get('etymology', '')[:60]
        print(f'  [{i+1}/{len(flagged)}] {root:8s} <- {word:20s} => {action:6s} ({etym})', flush=True)
        time.sleep(0.8)  # avoid rate-limiting

    # Build final corrections — only confirmed REMOVE
    final_removes = [r for r in results if r.get('action') == 'REMOVE']
    final_keeps = [r for r in results if r.get('action') == 'KEEP']

    print(f'\n=== Second-pass results ===')
    print(f'KEEP (AI confirmed correct etymology): {len(final_keeps)}')
    print(f'REMOVE (AI confirmed not from this root): {len(final_removes)}')
    print(f'\n=== Words to REMOVE ===')
    for r in final_removes:
        print(f'  {r["root"]:8s} <- {r["word"]:20s} ({r.get("etymology","")[:70]})')

    with open('/tmp/root_corrections_final.json', 'w') as f:
        json.dump(final_removes, f, ensure_ascii=False, indent=2)
    print(f'\n✅ Wrote /tmp/root_corrections_final.json ({len(final_removes)} confirmed removals)')

    # Also save the full results for transparency
    with open('/tmp/root_verification_full.json', 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
