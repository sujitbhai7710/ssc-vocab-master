#!/usr/bin/env python3
"""Assemble final grammar data files into public/data/grammar/.

Produces:
  rules.json              - 114 merged rules (with questionIds attached)
  questions.json          - all Grammar-Rules-page MCQs (rani + error + pyq-error + pyq-improvement),
                            deduped, ordered rani -> error -> pyq, with answers+explanations
  narration_rules.json    - 10 narration sections (already built, copied)
  narration_questions.json
  voice_rules.json
  voice_questions.json
  summary.json            - counts for the dashboard
"""
import os, json, re, shutil

WORK = "/home/z/my-project/work/grammar"
PUB = "/home/z/my-project/ssc-vocab-master/public/data/grammar"
os.makedirs(PUB, exist_ok=True)

def load(name):
    return json.load(open(os.path.join(WORK, name), encoding='utf-8'))

merged_rules = load("merged_rules.json")
src_to_gr = load("src_to_gr.json")
rani_src = load("src_rani.json")
error_src = load("src_error.json")
pyqs = load("grammar_pyqs.json")

# load explanations
def load_expl(mode):
    d = {}
    p = os.path.join(WORK, f"expl_{mode}.jsonl")
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            line = line.strip()
            if not line: continue
            try:
                o = json.loads(line); d[o["qid"]] = o
            except: pass
    return d
expl_pdf = load_expl("pdf")
expl_pyq = load_expl("pyq")

def norm(s):
    return re.sub(r'\W+', '', (s or '').lower())[:90]

def optkey(opts):
    return tuple(re.sub(r'\W+','',o.lower())[:30] for o in opts)

# ---- Build questions for Grammar Rules page ----
# Priority order: rani, error, pyq-error, pyq-improvement
questions = []
seen = set()  # (norm_sentence, optkey)

def add_q(qid, source, qtype, prompt, sentence, options, correctIdx, explanation, ruleId, exam=None, year=None):
    if not options or len(options) != 4:
        return
    key = (norm(sentence or prompt), optkey(options))
    if key in seen:
        return
    seen.add(key)
    questions.append({
        "id": qid,
        "ruleId": ruleId,
        "source": source,
        "qtype": qtype,
        "prompt": prompt,
        "sentence": sentence,
        "options": options,
        "correctIdx": correctIdx,
        "explanation": explanation or "",
        "exam": exam,
        "year": year,
    })

# 1. rani questions
rid = 0
for q in rani_src["questions"]:
    rid += 1
    qid = f"grq-rani-{rid}"
    src_id = q.get("source_q_id","")  # e.g. rani-1-1
    # rule_ref like rani-1 -> gr-1
    rr = q.get("rule_ref")
    ruleId = src_to_gr.get(rr) if rr else None
    expl = expl_pdf.get(src_id) or expl_pdf.get(qid)
    given = q.get("answer_idx")
    ans = expl["correctIdx"] if expl and expl.get("correctIdx") is not None else given
    add_q(qid, "rani", "error",
          "Identify the part with the grammatical error (or 'No error').",
          q.get("question",""), q.get("options",[]),
          ans, (expl or {}).get("explanation",""), ruleId)

# 2. error questions
eid = 0
for q in error_src["questions"]:
    eid += 1
    qid = f"grq-error-{eid}"
    src_id = q.get("source_q_id","")
    rr = q.get("rule_ref")
    ruleId = src_to_gr.get(rr) if rr else None
    expl = expl_pdf.get(src_id)
    given = q.get("answer_idx")
    ans = expl["correctIdx"] if expl and expl.get("correctIdx") is not None else given
    add_q(qid, "error", "error",
          "Identify the part with the grammatical error (or 'No error').",
          q.get("question",""), q.get("options",[]),
          ans, (expl or {}).get("explanation",""), ruleId)

# 3. pyq error
for q in pyqs.get("error",[]):
    qid = q["id"]
    expl = expl_pyq.get(qid)
    ruleId = expl.get("ruleId") if expl else None
    ans = expl["correctIdx"] if expl else None
    add_q(qid, "pyq-error", "error", q.get("prompt",""), q.get("sentence",""),
          q.get("options",[]), ans, (expl or {}).get("explanation",""), ruleId,
          q.get("exam"), q.get("year"))

# 4. pyq improvement
for q in pyqs.get("improvement",[]):
    qid = q["id"]
    expl = expl_pyq.get(qid)
    ruleId = expl.get("ruleId") if expl else None
    ans = expl["correctIdx"] if expl else None
    add_q(qid, "pyq-improvement", "improvement", q.get("prompt",""), q.get("sentence",""),
          q.get("options",[]), ans, (expl or {}).get("explanation",""), ruleId,
          q.get("exam"), q.get("year"))

print(f"grammar questions (deduped): {len(questions)}")

# attach questionIds to rules (in priority order)
by_rule = {}
for q in questions:
    by_rule.setdefault(q["ruleId"], []).append(q["id"])
for r in merged_rules:
    r["questionIds"] = by_rule.get(r["id"], [])
# also count unmapped
unmapped = [q for q in questions if not q.get("ruleId")]
print(f"unmapped questions: {len(unmapped)}")

# save rules (clean final shape)
final_rules = []
for r in merged_rules:
    final_rules.append({
        "id": r["id"],
        "no": r["no"],
        "title": r["title"],
        "topic": r["topic"],
        "concept": r["concept"],
        "examples": r.get("examples",[]),
        "sources": r["sources"],
        "questionIds": r["questionIds"],
    })

with open(os.path.join(PUB,"rules.json"),'w',encoding='utf-8') as f:
    json.dump(final_rules, f, ensure_ascii=False, indent=1)
with open(os.path.join(PUB,"questions.json"),'w',encoding='utf-8') as f:
    json.dump(questions, f, ensure_ascii=False, indent=1)
print(f"-> rules.json ({len(final_rules)}), questions.json ({len(questions)})")

# copy narration/voice
for fn in ["narration_rules.json","narration_questions.json","voice_rules.json","voice_questions.json"]:
    shutil.copy(os.path.join(WORK,fn), os.path.join(PUB,fn))
print("copied narration/voice files")

# summary
nar_q = load("narration_questions.json") if os.path.exists(os.path.join(WORK,"narration_questions.json")) else []
voi_q = load("voice_questions.json") if os.path.exists(os.path.join(WORK,"voice_questions.json")) else []
summary = {
    "grammarRules": len(final_rules),
    "grammarQuestions": len(questions),
    "narrationRules": len(load("narration_rules.json")),
    "narrationQuestions": len(nar_q),
    "voiceRules": len(load("voice_rules.json")),
    "voiceQuestions": len(voi_q),
    "questionsBySource": {
        "rani": sum(1 for q in questions if q["source"]=="rani"),
        "error": sum(1 for q in questions if q["source"]=="error"),
        "pyq-error": sum(1 for q in questions if q["source"]=="pyq-error"),
        "pyq-improvement": sum(1 for q in questions if q["source"]=="pyq-improvement"),
    },
    "unmappedQuestions": len(unmapped),
}
with open(os.path.join(PUB,"summary.json"),'w',encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)
print("summary:", json.dumps(summary, indent=2))
