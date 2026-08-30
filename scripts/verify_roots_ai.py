#!/usr/bin/env python3
"""
Verify suspicious root-family mappings using AI (claude-opus via kktoken.cc).

For each suspicious word (one that doesn't share a substring with its assigned
root), ask the AI whether it's a legitimate etymology connection (keep) or a
data error (remove).

Uses 3 API keys in parallel for faster execution. Resumable — saves progress
to /tmp/root_verification_progress.json after each batch.

Output: /tmp/root_corrections.json — list of {root, word, action: 'remove'}
        for words the AI says don't belong.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


API_KEYS = os.environ.get("OPENAI_API_KEYS", "").split(",")
API_KEYS = [k.strip() for k in API_KEYS if k.strip()]
if not API_KEYS:
    print("ERROR: set OPENAI_API_KEYS env var to a comma-separated list of API keys.", file=sys.stderr)
    sys.exit(1)
API_URL = os.environ.get("API_URL", "https://kktoken.cc/v1/chat/completions")
MODEL = os.environ.get("MODEL", "claude-opus-4-8")
BATCH_SIZE = 20  # roots per API call
MAX_WORKERS = 1  # sequential to avoid rate-limiting (error 1010)
BATCH_DELAY = 1.5  # seconds between batches

PROGRESS_FILE = '/tmp/root_verification_progress.json'
OUTPUT_FILE = '/tmp/root_corrections.json'


def call_ai(api_key: str, batch: list, batch_idx: int) -> dict:
    """Call the AI with a batch of roots to verify. Returns {root: {word: 'keep'|'remove'}}."""
    # Build the prompt
    lines = []
    lines.append('You are an etymology expert. Verify whether each English word truly derives from the given Latin/Greek root.')
    lines.append('')
    lines.append('For each word, respond with KEEP if the etymology is correct (the word genuinely derives from that root, even if the spelling transformed over time — e.g. "solution" from SOLV, "elegant" from LEG, "pleasant" from PLAC), or REMOVE if the word does NOT derive from that root (data error).')
    lines.append('')
    lines.append('Respond ONLY with a JSON object. No other text. Format:')
    lines.append('{"ROOT_NAME": {"word1": "KEEP", "word2": "REMOVE"}, ...}')
    lines.append('')
    lines.append('=== ROOTS TO VERIFY ===')
    for entry in batch:
        root = entry['root']
        rm = entry['rm']
        lines.append(f'\nROOT: {root} (meaning: {rm})')
        for w in entry['words']:
            lines.append(f'  - {w["word"]}: {w["mean"]}')

    prompt = '\n'.join(lines)

    body = json.dumps({
        'model': MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0,
        'max_tokens': 4000,
    }).encode('utf-8')

    req = urllib.request.Request(API_URL, data=body, headers={
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
    })

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            content = data['choices'][0]['message']['content'].strip()
            # Strip markdown code fences if present
            if content.startswith('```'):
                content = content.split('\n', 1)[1] if '\n' in content else content
                if content.endswith('```'):
                    content = content.rsplit('```', 1)[0]
                content = content.strip()
            # Parse JSON
            result = json.loads(content)
            print(f'  [batch {batch_idx}] OK — {len(result)} roots verified', flush=True)
            return result
        except urllib.error.HTTPError as e:
            print(f'  [batch {batch_idx}] HTTP {e.code} (attempt {attempt+1}/3): {e.read().decode("utf-8","ignore")[:200]}', flush=True)
            time.sleep(3 * (attempt + 1))
        except Exception as e:
            print(f'  [batch {batch_idx}] ERROR (attempt {attempt+1}/3): {type(e).__name__}: {str(e)[:200]}', flush=True)
            time.sleep(3 * (attempt + 1))
    print(f'  [batch {batch_idx}] FAILED after 3 attempts', flush=True)
    return {}


def main():
    with open('/tmp/root_audit.json') as f:
        audit = json.load(f)

    suspicious = audit['suspicious_by_root']  # {root: [{word, mean, bn}]}
    roots_to_verify = list(suspicious.keys())
    print(f'Total roots to verify: {len(roots_to_verify)}')

    # Load progress if exists
    verified = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            verified = json.load(f)
        print(f'Resuming — {len(verified)} roots already verified')

    # Build batches
    batches = []
    for i in range(0, len(roots_to_verify), BATCH_SIZE):
        chunk_roots = roots_to_verify[i:i+BATCH_SIZE]
        # Skip batches where all roots are already verified
        if all(r in verified for r in chunk_roots):
            continue
        batch = []
        for root in chunk_roots:
            if root in verified:
                continue
            batch.append({
                'root': root,
                'rm': suspicious[root][0].get('bn', '') if not suspicious[root][0].get('bn') else '',  # placeholder
                'words': suspicious[root],
            })
        if batch:
            batches.append(batch)

    # Actually, let me rebuild batches properly with the rm (root meaning)
    batches = []
    for i in range(0, len(roots_to_verify), BATCH_SIZE):
        chunk_roots = roots_to_verify[i:i+BATCH_SIZE]
        if all(r in verified for r in chunk_roots):
            continue
        batch = []
        for root in chunk_roots:
            if root in verified:
                continue
            # Get rm from the audit — it's stored per-word, take the first
            rm = suspicious[root][0].get('mean', '') if False else ''  # we don't have rm in audit; load from roots.json
            batch.append({
                'root': root,
                'words': suspicious[root],
            })
        if batch:
            batches.append(batch)

    # Load roots.json to get rm for each root
    with open('public/data/roots.json') as f:
        roots_data = json.load(f)
    root_rm = {r['root']: r['rm'] for r in roots_data}
    for batch in batches:
        for entry in batch:
            entry['rm'] = root_rm.get(entry['root'], '')

    print(f'Batches to process: {len(batches)} (batch size={BATCH_SIZE} roots)')

    # Process batches in parallel with 3 workers (one per API key)
    progress_lock = Lock()

    def process_batch(args):
        batch_idx, batch, key_idx = args
        api_key = API_KEYS[key_idx % len(API_KEYS)]
        result = call_ai(api_key, batch, batch_idx)
        # Merge into verified
        with progress_lock:
            for root, word_verdicts in result.items():
                verified[root] = word_verdicts
            # Save progress
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(verified, f, ensure_ascii=False)
        return result

    tasks = [(i, batch, i % len(API_KEYS)) for i, batch in enumerate(batches)]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_batch, t): t for t in tasks}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f'  Batch failed: {e}', flush=True)
            time.sleep(BATCH_DELAY)  # delay between batches to avoid rate-limiting

    # Build corrections list
    corrections = []  # {root, word, action: 'remove'}
    kept = 0
    removed = 0
    for root, word_verdicts in verified.items():
        if not isinstance(word_verdicts, dict):
            continue
        for word, verdict in word_verdicts.items():
            v = str(verdict).upper().strip()
            if v == 'REMOVE':
                corrections.append({'root': root, 'word': word, 'action': 'remove'})
                removed += 1
            else:
                kept += 1

    print(f'\n=== Verification complete ===')
    print(f'Words verified: {kept + removed}')
    print(f'  KEEP: {kept}')
    print(f'  REMOVE: {removed}')

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(corrections, f, ensure_ascii=False, indent=2)
    print(f'\n✅ Wrote {OUTPUT_FILE} ({len(corrections)} corrections)')


if __name__ == '__main__':
    main()
