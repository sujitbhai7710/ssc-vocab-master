#!/usr/bin/env python3
"""AI-verify gray (WordNet-added) synonyms/antonyms and clean enriched data.

Gray = ssSynonyms/ssAntonyms entries with status 'added' (not from exam).
For each gray candidate, AI decides: is it a valid, COMMON synonym/antonym of the
word (not obscure, not multi-word junk)? Keep only verified-true ones; drop the rest.
Exam-sourced 'correct'/'distractor' entries are NEVER touched.

Resumable: verdicts saved to work/grammar/gray_verdicts.jsonl.
After verification, rewrites the 26 per-letter enriched files + master enriched.json.

Usage:
  python3 fix_gray.py verify [limit]   # run AI verification (resume-safe)
  python3 fix_gray.py rebuild          # rebuild enriched files from verdicts
"""
import os, json, re, sys, glob
sys.path.insert(0, '/home/z/my-project/scripts')
from ai_helper import chat_json, parallel_map

PUB = "/home/z/my-project/ssc-vocab-master/public/data"
ENRICHED_DIR = os.path.join(PUB, "enriched")
WORK = "/home/z/my-project/work/grammar"
VERDICTS = os.path.join(WORK, "gray_verdicts.jsonl")

def letter_files():
    return sorted(glob.glob(os.path.join(ENRICHED_DIR, "enriched_*.json")))

def is_clean(w):
    w = w.strip()
    if ' ' in w or len(w) < 2 or len(w) > 16: return False
    if not re.match(r'^[A-Za-z][A-Za-z\-]*$', w): return False
    return True

def collect_gray():
    """Return list of {word, cand, type, letter} for gray 'added' entries."""
    items = []
    for f in letter_files():
        d = json.load(open(f, encoding='utf-8'))
        for w, e in d.items():
            for s in e.get('ssSynonyms', []):
                if s.get('status') == 'added':
                    items.append({"word": w, "cand": s['word'], "type": "syn", "letter": w[0]})
            for s in e.get('ssAntonyms', []):
                if s.get('status') == 'added':
                    items.append({"word": w, "cand": s['word'], "type": "ant", "letter": w[0]})
    return items

def load_verdicts():
    v = {}
    if os.path.exists(VERDICTS):
        for line in open(VERDICTS, encoding='utf-8'):
            line = line.strip()
            if not line: continue
            try:
                o = json.loads(line); v[o["key"]] = o.get("keep")
            except: pass
    return v

def append_verdict(key, keep):
    with open(VERDICTS, 'a', encoding='utf-8') as f:
        f.write(json.dumps({"key": key, "keep": keep}, ensure_ascii=False) + "\n")

def vkey(word, cand, type):
    return f"{word.lower()}|{cand.lower()}|{type}"

def verify_batch(batch):
    prompt = (
        "You are an SSC English vocabulary expert. For each (word, candidate) pair below, decide if the "
        "candidate is a VALID and COMMON (exam-relevant, not obscure) synonym or antonym of the word. "
        "Return keep=true only if the candidate is a normal, well-known single word that is genuinely a "
        "synonym (for syn) or antonym (for ant) of the word. Reject obscure, archaic, multi-word, or "
        "loosely-related words. Note: in antonym questions, options sometimes include near-synonyms as "
        "distractors — judge strictly by the 'type' field (syn=must be synonym, ant=must be antonym).\n\n"
        "Return JSON array, one object per item IN ORDER:\n"
        "[{\"i\":<index in batch>,\"keep\":true/false}]\n"
        "Return ONLY the JSON array."
    )
    def fmt(it, i):
        rel = "synonym" if it['type']=='syn' else "antonym"
        return f"{i}. word='{it['word']}' | candidate='{it['cand']}' | relation={rel}"
    block = "\n".join(fmt(it, i) for i, it in enumerate(batch))
    return chat_json([
        {"role":"system","content":"You are an expert English vocabulary judge. Output only valid JSON arrays."},
        {"role":"user","content": prompt + "\n\n=== ITEMS ===\n" + block}
    ], temperature=0.0, max_tokens=1800, timeout=200, retries=5)

def run_verify(limit=None):
    items = collect_gray()
    # heuristic: only verify clean candidates; junk ones are auto-dropped at rebuild
    clean = [it for it in items if is_clean(it['cand'])]
    junk = [it for it in items if not is_clean(it['cand'])]
    verdicts = load_verdicts()
    todo = [it for it in clean if vkey(it['word'],it['cand'],it['type']) not in verdicts]
    print(f"gray total={len(items)} clean={len(clean)} junk(auto-drop)={len(junk)} already-verdicted={len(verdicts)} todo={len(todo)}", flush=True)
    if limit: todo = todo[:limit]; print(f"limited to {len(todo)}", flush=True)
    if not todo: return
    BATCH = 40
    batches = [todo[i:i+BATCH] for i in range(0, len(todo), BATCH)]
    print(f"batches={len(batches)} (size {BATCH})", flush=True)
    def work(b): return verify_batch(b)
    BOB = 6
    for b in range(0, len(batches), BOB):
        grp = batches[b:b+BOB]
        results = parallel_map(grp, work, workers=6, desc="gray")
        for batch, res in results:
            if isinstance(res, Exception) or not isinstance(res, list):
                continue
            for item in res:
                i = item.get("i")
                if i is None or i >= len(batch): continue
                it = batch[i]
                append_verdict(vkey(it['word'],it['cand'],it['type']), bool(item.get("keep")))
        print(f"  progress {min((b+1)*BOB,len(batches))}/{len(batches)} batches", flush=True)

def rebuild():
    verdicts = load_verdicts()
    items = collect_gray()
    keep_set = set()
    for it in items:
        k = vkey(it['word'],it['cand'],it['type'])
        if verdicts.get(k) is True:
            keep_set.add((it['word'].lower(), it['cand'].lower(), it['type']))
    print(f"verdicts={len(verdicts)} kept_gray={len(keep_set)}", flush=True)
    kept_syn = kept_ant = dropped = 0
    for f in letter_files():
        d = json.load(open(f, encoding='utf-8'))
        changed = False
        for w, e in d.items():
            new_syn = []
            for s in e.get('ssSynonyms', []):
                if s.get('status') != 'added':
                    new_syn.append(s); continue
                if is_clean(s['word']) and (w.lower(), s['word'].lower(), 'syn') in keep_set:
                    new_syn.append(s); kept_syn += 1
                else:
                    dropped += 1
            new_ant = []
            for s in e.get('ssAntonyms', []):
                if s.get('status') != 'added':
                    new_ant.append(s); continue
                if is_clean(s['word']) and (w.lower(), s['word'].lower(), 'ant') in keep_set:
                    new_ant.append(s); kept_ant += 1
                else:
                    dropped += 1
            if len(new_syn) != len(e.get('ssSynonyms',[])) or len(new_ant) != len(e.get('ssAntonyms',[])):
                e['ssSynonyms'] = new_syn
                e['ssAntonyms'] = new_ant
                changed = True
        if changed:
            with open(f,'w',encoding='utf-8') as fh:
                json.dump(d, fh, ensure_ascii=False, indent=1)
    # rebuild master enriched.json
    master = {}
    for f in letter_files():
        d = json.load(open(f, encoding='utf-8'))
        master.update(d)
    with open(os.path.join(PUB,'enriched.json'),'w',encoding='utf-8') as fh:
        json.dump(master, fh, ensure_ascii=False, indent=1)
    print(f"rebuild done: kept_syn={kept_syn} kept_ant={kept_ant} dropped={dropped}", flush=True)

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "verify":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
        run_verify(lim)
    elif cmd == "rebuild":
        rebuild()
    else:
        print("usage: verify [limit] | rebuild")
