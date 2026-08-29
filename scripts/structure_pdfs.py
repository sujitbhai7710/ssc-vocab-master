#!/usr/bin/env python3
"""Structure the 3 grammar PDFs into rules + questions JSON via AI.

Usage:
  python3 structure_pdfs.py            # all sources
  python3 structure_pdfs.py rani       # one source

Resumable: saves per-chunk results to src_<name>_partial.json and skips chunks
already done. Final merge -> src_<name>.json.
"""
import os, re, json, sys, time
sys.path.insert(0, '/home/z/my-project/scripts')
from ai_helper import chat_json, parallel_map

PDF_DIR = "/home/z/my-project/work/pdf_text"
OUT = "/home/z/my-project/work/grammar"
os.makedirs(OUT, exist_ok=True)

SOURCES = {
    "rani": {
        "file": "rani-maam.txt", "pages_per_chunk": 3,
        "prompt": (
            "You are parsing a scanned SSC English-grammar PDF page text. The text is from "
            "'English With Rani Ma'am — 60 Rules of Grammar 2.0'. The 2-column layout got "
            "scrambled by OCR, so read contextually. Each rule is headed 'Rule N' with a short "
            "concept, followed by numbered error-spotting questions. Each question has a sentence "
            "divided into parts (often shown as ' / ' separated or labelled (a)(b)(c)(d)), four "
            "options which are the parts themselves plus 'No error', and an answer key "
            "(e.g. '1.4 2.4 3.1' meaning Q1->option4). \n\n"
            "Extract from the given chunk ONLY, as JSON:\n"
            "{\"rules\":[{\"source_rule_id\":\"rani-<n>\",\"rule_no\":<int>,\"title\":\"\",\"topic\":\"\",\"concept\":\"clean 2-4 sentence explanation\"}],"
            "\"questions\":[{\"source_q_id\":\"rani-<rule>-<n>\",\"rule_ref\":\"rani-<n>\",\"question\":\"the full sentence with parts\",\"options\":[4 strings],\"answer_idx\":<0-3 or null>,\"explanation\":\"\"}]}\n"
            "Rules: list every rule header present in this chunk. If concept text is scrambled, reconstruct a concise concept. "
            "Questions: list every error-spotting MCQ. options exactly 4 strings (parts + 'No error' if present). "
            "Map answer_idx from the answer key (1->0,2->1,3->2,4->3; a->0,b->1,c->2,d->3); null if not present. "
            "Do NOT invent questions. Return ONLY the JSON object."
        ),
    },
    "error": {
        "file": "error-spotting.txt", "pages_per_chunk": 4,
        "prompt": (
            "You are parsing a clean SSC English-grammar PDF: 'Top 100 Rules For Error Spotting + "
            "300 Most Important Error Questions' (Rahul Gupta). Two parts: (1) rules as 'Rule N: Title' "
            "with 'Concept:', 'Incorrect:', 'Correct:' lines; (2) 300 error-detection MCQs each with a "
            "sentence (parts labelled or ' / ' separated), four options (parts + 'No error'), and an answer.\n\n"
            "Extract from the given chunk ONLY, as JSON:\n"
            "{\"rules\":[{\"source_rule_id\":\"error-<n>\",\"rule_no\":<int>,\"title\":\"\",\"topic\":\"e.g. Subject-Verb Agreement\",\"concept\":\"the Concept text\",\"examples\":[{\"incorrect\":\"\",\"correct\":\"\"}]}],"
            "\"questions\":[{\"source_q_id\":\"error-q<n>\",\"rule_ref\":\"error-<n> if grouped under a rule else null\",\"question\":\"full sentence with parts\",\"options\":[4 strings],\"answer_idx\":<0-3 or null>,\"explanation\":\"if given\"}]}\n"
            "If chunk has only rules, return empty questions; if only MCQs, empty rules. options exactly 4 strings. "
            "Map answer labels a/A->0,b/B->1,c/C->2,d/D->3,1->0,2->1,3->2,4->3. Do NOT invent content. Return ONLY the JSON object."
        ),
    },
    "aman": {
        "file": "100-grammar-rules.txt", "pages_per_chunk": 4,
        "prompt": (
            "You are parsing a clean SSC English-grammar PDF: '100 Most Important Grammar Rules' (Aman). "
            "Organized by topic headings (PRONOUN, VERB) and within them 'CONCEPT NO. N' with a rule line and "
            "numbered examples. Each example is an error-spotting sentence with an answer like "
            "\"Ans:- Use 'your' instead of 'yours'\" (often Hinglish).\n\n"
            "Extract from the given chunk ONLY, as JSON:\n"
            "{\"rules\":[{\"source_rule_id\":\"aman-<n>\",\"concept_no\":<int>,\"title\":\"\",\"topic\":\"e.g. Pronoun\",\"concept\":\"rule explanation (translate Hinglish to clear English)\",\"examples\":[{\"sentence\":\"\",\"correction\":\"\"}]}],"
            "\"questions\":[{\"source_q_id\":\"aman-ex<n>\",\"rule_ref\":\"aman-<n>\",\"question\":\"the example sentence\",\"options\":[],\"answer_idx\":null,\"explanation\":\"the Ans text translated to clear English\"}]}\n"
            "For aman, 'questions' are example corrections (options empty, answer_idx null, explanation=correction). "
            "List every concept and every numbered example. Translate Hinglish to clear English. Do NOT invent content. Return ONLY the JSON object."
        ),
    },
}

def chunk_text(text, pages_per_chunk):
    parts = [p for p in re.split(r'===== PAGE \d+ =====', text) if p.strip()]
    chunks = []
    for i in range(0, len(parts), pages_per_chunk):
        grp = parts[i:i+pages_per_chunk]
        chunk = '\n'.join(f'===== PAGE {i+j+1} =====' + g for j, g in enumerate(grp))
        chunks.append(chunk)
    return chunks

def load_partial(name):
    p = os.path.join(OUT, f"src_{name}_partial.json")
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding='utf-8'))
        except Exception:
            return {}
    return {}

def save_partial(name, data):
    p = os.path.join(OUT, f"src_{name}_partial.json")
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def process_source(name, cfg):
    text = open(os.path.join(PDF_DIR, cfg["file"]), encoding='utf-8').read()
    chunks = chunk_text(text, cfg["pages_per_chunk"])
    partial = load_partial(name)  # {chunk_idx: {rules,questions}}
    print(f"[{name}] {len(chunks)} chunks; already done: {len(partial)}", flush=True)
    todo = [i for i in range(len(chunks)) if str(i) not in partial]
    print(f"[{name}] todo: {len(todo)} chunks", flush=True)
    if not todo:
        return finalize(name)
    def work(ci):
        return chat_json([
            {"role":"system","content":"You are a precise data-extraction assistant for SSC English grammar material. Output only valid JSON."},
            {"role":"user","content": cfg["prompt"] + "\n\n=== CHUNK TEXT ===\n" + chunks[ci]}
        ], temperature=0.1, max_tokens=5000, timeout=200, retries=4)
    # process in small batches to save incrementally
    BATCH = 6
    for b in range(0, len(todo), BATCH):
        batch = todo[b:b+BATCH]
        results = parallel_map(batch, work, workers=6, desc=name)
        for ci, res in results:
            if isinstance(res, Exception):
                print(f"  [{name}] chunk {ci} FAIL: {res}", flush=True)
                continue
            if isinstance(res, dict):
                partial[str(ci)] = res
                print(f"  [{name}] chunk {ci} ok: rules={len(res.get('rules',[]))} qs={len(res.get('questions',[]))}", flush=True)
            else:
                print(f"  [{name}] chunk {ci} bad type {type(res)}", flush=True)
        save_partial(name, partial)
    return finalize(name)

def finalize(name):
    partial = load_partial(name)
    rules, qs = [], []
    for ci in sorted(int(k) for k in partial.keys()):
        d = partial[str(ci)]
        rules.extend(d.get("rules", []))
        qs.extend(d.get("questions", []))
    out = {"source": name, "rules": rules, "questions": qs}
    outp = os.path.join(OUT, f"src_{name}.json")
    with open(outp, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"[{name}] DONE: rules={len(rules)} questions={len(qs)} -> {outp}", flush=True)
    return out

def main():
    names = sys.argv[1:] if len(sys.argv) > 1 else list(SOURCES.keys())
    for name in names:
        if name not in SOURCES:
            print(f"unknown source: {name}"); continue
        process_source(name, SOURCES[name])

if __name__ == '__main__':
    main()
