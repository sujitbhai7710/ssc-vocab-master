#!/usr/bin/env python3
"""Answer + explain all grammar MCQs and map PYQs to rules (resumable, incremental).

Two modes (run both; resume-safe):
  pdf  : rani (790) + error (300) questions. Have answer_idx -> verify + write explanation.
  pyq  : pyq error (1077) + improvement (1085). Need answer_idx + explanation + rule mapping.

For each question batch, AI returns per-question {correctIdx, explanation, ruleId?}.
Saves incrementally to work/grammar/expl_<mode>.jsonl (one JSON line per question id).
Final assembly into questions.json happens in build_grammar_data.py.

Usage:
  python3 answer_explain.py pdf
  python3 answer_explain.py pyq
"""
import os, json, sys
sys.path.insert(0, '/home/z/my-project/scripts')
from ai_helper import chat_json, parallel_map

OUT = "/home/z/my-project/work/grammar"

def load(name):
    return json.load(open(os.path.join(OUT, f"src_{name}.json"), encoding='utf-8'))

# rule index for mapping
RULE_INDEX = json.load(open(os.path.join(OUT, "rule_index.json"), encoding='utf-8'))
SRC_TO_GR = json.load(open(os.path.join(OUT, "src_to_gr.json"), encoding='utf-8'))
RULE_INDEX_STR = "\n".join(f"{r['id']} | Rule {r['no']} | {r['title']} | {r['topic']}" for r in RULE_INDEX)

def load_done(mode):
    p = os.path.join(OUT, f"expl_{mode}.jsonl")
    done = {}
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
                done[o["qid"]] = o
            except Exception:
                pass
    return done

def append_done(mode, obj):
    p = os.path.join(OUT, f"expl_{mode}.jsonl")
    with open(p, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# ---- build the work items ----
def build_pdf_items():
    items = []
    rani = load("rani"); error = load("error")
    for q in rani["questions"]:
        items.append({
            "qid": "rani-" + str(q.get("source_q_id","").replace("rani-","")),
            "source": "rani",
            "qtype": "error",
            "prompt": "Identify the part with the grammatical error (or 'No error').",
            "sentence": q.get("question",""),
            "options": q.get("options",[]),
            "given_answer": q.get("answer_idx"),
            "rule_ref": q.get("rule_ref"),
        })
    for q in error["questions"]:
        items.append({
            "qid": "error-" + str(q.get("source_q_id","").replace("error-","")),
            "source": "error",
            "qtype": "error",
            "prompt": "Identify the part with the grammatical error (or 'No error').",
            "sentence": q.get("question",""),
            "options": q.get("options",[]),
            "given_answer": q.get("answer_idx"),
            "rule_ref": q.get("rule_ref"),
        })
    return items

def build_pyq_items():
    items = []
    pyqs = json.load(open(os.path.join(OUT, "grammar_pyqs.json"), encoding='utf-8'))
    for qt in ["error","improvement"]:
        for q in pyqs.get(qt,[]):
            items.append({
                "qid": q["id"],
                "source": f"pyq-{qt}",
                "qtype": qt,
                "prompt": q.get("prompt",""),
                "sentence": q.get("sentence",""),
                "options": q.get("options",[]),
                "given_answer": q.get("correctIdx"),
                "exam": q.get("exam"),
                "year": q.get("year"),
            })
    return items

def explain_batch(items, mode):
    """One AI call for a batch. Returns list of {qid, correctIdx, explanation, ruleId?}."""
    if mode == "pdf":
        prompt = (
            "You are an SSC English-grammar expert. For each error-spotting MCQ below, the answer "
            "may be given (given_answer, 0-indexed). VERIFY it; correct it if wrong. Then write a "
            "concise explanation (1-2 sentences) of WHY that part is the error and how to fix it. "
            "If the answer is 'No error' (the 'No error' option), say so.\n\n"
            "Return JSON array, one object per question IN ORDER:\n"
            "[{\"qid\":\"\",\"correctIdx\":<0-3>,\"explanation\":\"\"}]\n"
            "Return ONLY the JSON array."
        )
        user_q = lambda it: f"[{it['qid']}] sentence: {it['sentence']}\n    options: {it['options']}\n    given_answer: {it['given_answer']}"
    else:  # pyq
        prompt = (
            "You are an SSC English-grammar expert. For each MCQ below, determine the correct option "
            "(0-indexed correctIdx), write a concise explanation (1-2 sentences) of why, AND assign it "
            "to the single best-matching rule from the RULE INDEX (ruleId like 'gr-7'). If no rule fits, "
            "ruleId=null.\n\n"
            "RULE INDEX:\n" + RULE_INDEX_STR + "\n\n"
            "Return JSON array, one object per question IN ORDER:\n"
            "[{\"qid\":\"\",\"correctIdx\":<0-3>,\"explanation\":\"\",\"ruleId\":\"gr-N\"}]}\n"
            "Return ONLY the JSON array."
        )
        user_q = lambda it: f"[{it['qid']}] ({it['source']}) {it['prompt']}\n    sentence: {it['sentence']}\n    options: {it['options']}"
    block = "\n\n".join(user_q(it) for it in items)
    return chat_json([
        {"role":"system","content":"You are an expert SSC English grammar tutor. Output only valid JSON arrays."},
        {"role":"user","content": prompt + "\n\n=== QUESTIONS ===\n" + block}
    ], temperature=0.1, max_tokens=4000, timeout=200, retries=4)

def run(mode, limit=None):
    items = build_pdf_items() if mode == "pdf" else build_pyq_items()
    done = load_done(mode)
    todo = [it for it in items if it["qid"] not in done]
    print(f"[{mode}] total={len(items)} done={len(done)} todo={len(todo)}", flush=True)
    if limit:
        todo = todo[:limit]
        print(f"[{mode}] limited to {len(todo)}", flush=True)
    if not todo:
        return
    BATCH = 20
    batches = [todo[i:i+BATCH] for i in range(0, len(todo), BATCH)]
    print(f"[{mode}] batches={len(batches)}", flush=True)
    def work(batch):
        return explain_batch(batch, mode)
    BATCH_OF_BATCHES = 6
    for b in range(0, len(batches), BATCH_OF_BATCHES):
        grp = batches[b:b+BATCH_OF_BATCHES]
        results = parallel_map(grp, work, workers=6, desc=mode)
        for batch, res in results:
            if isinstance(res, Exception):
                print(f"  [{mode}] batch FAIL: {res}", flush=True)
                continue
            if not isinstance(res, list):
                print(f"  [{mode}] batch bad type {type(res)}", flush=True)
                continue
            qmap = {it["qid"]: it for it in batch}
            for item in res:
                qid = item.get("qid")
                if qid in qmap:
                    append_done(mode, {
                        "qid": qid,
                        "correctIdx": item.get("correctIdx"),
                        "explanation": item.get("explanation",""),
                        "ruleId": item.get("ruleId"),
                    })
        print(f"  [{mode}] progress: {min((b+1)*BATCH_OF_BATCHES, len(batches))}/{len(batches)} batches", flush=True)

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else "pyq"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(mode, limit)
