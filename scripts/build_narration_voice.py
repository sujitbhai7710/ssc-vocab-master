#!/usr/bin/env python3
"""Build Narration & Voice modules.

1. Generate comprehensive, multi-section rule sets (top-level, synthesised from broad
   grammar knowledge) for Narration and Voice. Each section = one "page" (TopicRule).
2. Answer + explain + map the narration (232) and voice (329) PYQs to those rules.

Outputs:
  work/grammar/narration_rules.json
  work/grammar/narration_questions.json
  work/grammar/voice_rules.json
  work/grammar/voice_questions.json
"""
import os, json, sys
sys.path.insert(0, '/home/z/my-project/scripts')
from ai_helper import chat_json, parallel_map

OUT = "/home/z/my-project/work/grammar"

NARR_SECTIONS = [
    ("Assertive / Statement Sentences", "Conversion of simple statement (assertive) sentences from direct to indirect speech: reporting verb changes (said->said that/told), conjunction 'that', and tense backshift rules."),
    ("Interrogative Sentences", "Yes/no questions (said->asked if/whether) and WH-questions (said->asked + WH word, no 'that'), word order changes to statement form, auxiliary inversion removal."),
    ("Imperative Sentences", "Commands, requests, advice, orders (said->ordered/requested/advised/told + to/not to + verb); negatives and 'let' type imperatives."),
    ("Exclamatory Sentences", "Exclamations (said->exclaimed with joy/sorrow/surprise/contempt; 'what'/'how' become 'that'; 'alas'->exclaimed with sorrow)."),
    ("Reporting Verb & Tense Backshift Rules", "When tense changes and when it stays; rules for universal truths, habits, past-perfect-already; changes in say/tell/reply."),
    ("Pronoun Changes", "First/second/third person pronoun changes (I/we follow speaker, you follows listener, he/she/they unchanged); possessive and reflexive pronouns."),
    ("Time & Place Word Changes", "now->then, today->that day, tonight->that night, tomorrow->the next day, yesterday->the previous day, here->there, this->that, these->those, thus->so, come->go."),
    ("Question Tags & 'Yes/No' Replies", "Conversion of sentences with question tags, and short 'Yes/No' replies (He said, 'Yes' -> He replied in the affirmative)."),
    ("Optative, Prayer & Wishes", "Optative sentences and prayers (said->prayed/wished/blessed + that + subject + may/might; 'May you...' -> He prayed that I might...)."),
    ("Mixed, Exception & Special Cases", "Mixed sentence types, indirect of indirect, exceptions, quotations/proverbs (kept as-is), and SSC common traps."),
]

VOICE_SECTIONS = [
    ("Basic Active-Passive Structure & Rules", "Core S-V-O rule; only transitive sentences can be passive; object becomes subject; verb becomes be+V3; by+agent (often dropped)."),
    ("Tense-wise Passive Forms (Part 1)", "Simple present, present continuous, present perfect, simple past passive forms with examples."),
    ("Tense-wise Passive Forms (Part 2)", "Past continuous, past perfect, simple future, future perfect, and modal-passive forms (can/must/should + be + V3)."),
    ("Interrogative Sentences (Passive)", "Passive of yes/no and WH-interrogatives; auxiliary handling and word order."),
    ("Imperative Sentences (Passive)", "Passive of commands/orders/requests (Let + object + be + V3; You are requested to...)."),
    ("Sentences with Two Objects (Ditransitive)", "Passive with two objects: either IO or DO can become subject; preferred patterns."),
    ("Sentences without Object & No-Passive Cases", "Intransitive verbs, linking verbs, and sentences that have no passive form."),
    ("Impersonal Passive ('It is said/believed')", "Passive of 'People say that...' -> 'It is said that...' / 'He is said to...' constructions."),
    ("Quasi-Passive / Middle Voice", "Active-looking sentences with passive meaning (the book sells well; the food tastes good) and how to spot them."),
    ("Special & Exception Cases", "Passive with prepositions, phrasal verbs, 'let' type, questions with prepositions, and SSC common traps."),
]

def _section_prompt(title, brief, kind, prefix, no):
    if kind == "narration":
        k1, k2 = "direct", "indirect"
    else:
        k1, k2 = "active", "passive"
    return (
        f"You are a top SSC English-grammar author. Write ONE comprehensive, exam-ready section for "
        f"{'DIRECT-INDIRECT SPEECH (NARRATION)' if kind=='narration' else 'ACTIVE-PASSIVE VOICE'}.\n"
        f"Section topic: {title}\nFocus: {brief}\n\n"
        "Synthesise the best content from standard grammar references (Wren & Martin, P.K. De Sarker, "
        "Rani Ma'am, Adda247, Testbook). Make rules concrete and easy to understand.\n\n"
        "Return JSON object (NOT an array):\n"
        f'{{"id":"{prefix}-{no}","no":{no},"title":"{title}","concept":"2-4 sentence overview",'
        '"rules":["detailed rule point 1","detailed rule point 2",...],'
        f'"examples":[{{"{k1}":"","{k2}":"","note":""}}]}}\n'
        "Include 3-5 rules and 2-4 examples. Return ONLY the JSON object."
    )

def gen_rules(kind, sections, prefix):
    print(f"[{kind}] generating {len(sections)} sections...", flush=True)
    def work(args):
        no, (title, brief) = args
        return chat_json([
            {"role":"system","content":"You are an expert SSC English grammar author. Output only valid JSON."},
            {"role":"user","content": _section_prompt(title, brief, kind, prefix, no)}
        ], temperature=0.3, max_tokens=3000, timeout=200, retries=4)
    items = list(enumerate(sections, 1))
    results = parallel_map(items, work, workers=6, desc=kind)
    out = []
    for (no,(title,brief)), res in results:
        if isinstance(res, Exception):
            print(f"  [{kind}] section {no} FAIL: {res}", flush=True)
            continue
        if isinstance(res, dict):
            res["id"] = f"{prefix}-{no}"
            res["no"] = no
            res.setdefault("questionIds", [])
            out.append(res)
            print(f"  [{kind}] section {no} ok: {len(res.get('rules',[]))} rules", flush=True)
    out.sort(key=lambda r: r["no"])
    outp = os.path.join(OUT, f"{kind}_rules.json")
    with open(outp, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"[{kind}] {len(out)} sections -> {outp}", flush=True)
    return out

# ---- answer/explain/map pyqs ----
def load_pyqs(qt):
    pyqs = json.load(open(os.path.join(OUT, "grammar_pyqs.json"), encoding='utf-8'))
    return pyqs.get(qt, [])

def rule_index_str(rules):
    return "\n".join(f"{r['id']} | {r['no']}. {r['title']}" for r in rules)

def explain_nv_batch(items, kind, ridx_str):
    label = "narration (direct-indirect speech)" if kind=="narration" else "voice (active-passive)"
    prompt = (
        f"You are an SSC English-grammar expert. For each {label} MCQ below, determine the correct "
        "option (0-indexed correctIdx), write a concise explanation (1-2 sentences) of the transformation "
        f"applied, AND assign it to the single best-matching rule section from the RULE INDEX (ruleId). "
        "If none fits, ruleId=null.\n\nRULE INDEX:\n" + ridx_str + "\n\n"
        "Return JSON array, one object per question IN ORDER:\n"
        "[{\"qid\":\"\",\"correctIdx\":<0-3>,\"explanation\":\"\",\"ruleId\":\"\"}]\n"
        "Return ONLY the JSON array."
    )
    def fmt(it):
        return f"[{it['id']}] {it.get('prompt','')}\n   sentence: {it.get('sentence','')}\n   options: {it.get('options',[])}"
    block = "\n\n".join(fmt(it) for it in items)
    return chat_json([
        {"role":"system","content":"You are an expert SSC English grammar tutor. Output only valid JSON arrays."},
        {"role":"user","content": prompt + "\n\n=== QUESTIONS ===\n" + block}
    ], temperature=0.1, max_tokens=4000, timeout=200, retries=4)

def process_pyqs(kind, rules):
    qt = kind  # 'narration' or 'voice'
    pyqs = load_pyqs(qt)
    print(f"[{kind}] pyqs={len(pyqs)}", flush=True)
    ridx = rule_index_str(rules)
    BATCH = 20
    batches = [pyqs[i:i+BATCH] for i in range(0, len(pyqs), BATCH)]
    def work(b):
        return explain_nv_batch(b, kind, ridx)
    results = parallel_map(batches, work, workers=6, desc=kind)
    out = []
    for batch, res in results:
        if isinstance(res, Exception):
            print(f"  [{kind}] batch FAIL: {res}", flush=True)
            continue
        if not isinstance(res, list):
            continue
        qmap = {it["id"]: it for it in batch}
        for item in res:
            qid = item.get("qid")
            if qid in qmap:
                orig = qmap[qid]
                out.append({
                    "id": qid,
                    "ruleId": item.get("ruleId"),
                    "source": f"pyq-{kind}",
                    "qtype": kind,
                    "prompt": orig.get("prompt",""),
                    "sentence": orig.get("sentence",""),
                    "options": orig.get("options",[]),
                    "correctIdx": item.get("correctIdx"),
                    "explanation": item.get("explanation",""),
                    "exam": orig.get("exam"),
                    "year": orig.get("year"),
                })
    # attach questionIds to rules
    for r in rules:
        r["questionIds"] = [q["id"] for q in out if q.get("ruleId")==r["id"]]
    # save
    with open(os.path.join(OUT, f"{kind}_rules.json"),'w',encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, f"{kind}_questions.json"),'w',encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"[{kind}] questions={len(out)}; mapped={sum(1 for q in out if q.get('ruleId'))}", flush=True)
    # retry unmapped/missing
    missing = [p for p in pyqs if p["id"] not in {q["id"] for q in out}]
    if missing:
        print(f"[{kind}] missing={len(missing)}, retrying...", flush=True)
        mb = [missing[i:i+BATCH] for i in range(0,len(missing),BATCH)]
        r2 = parallel_map(mb, work, workers=6, desc=kind+"-retry")
        for batch,res in r2:
            if isinstance(res,Exception) or not isinstance(res,list): continue
            qmap={it["id"]:it for it in batch}
            for item in res:
                qid=item.get("qid")
                if qid in qmap:
                    orig=qmap[qid]
                    out.append({"id":qid,"ruleId":item.get("ruleId"),"source":f"pyq-{kind}","qtype":kind,
                        "prompt":orig.get("prompt",""),"sentence":orig.get("sentence",""),"options":orig.get("options",[]),
                        "correctIdx":item.get("correctIdx"),"explanation":item.get("explanation",""),"exam":orig.get("exam"),"year":orig.get("year")})
        for r in rules:
            r["questionIds"]=[q["id"] for q in out if q.get("ruleId")==r["id"]]
        with open(os.path.join(OUT,f"{kind}_rules.json"),'w',encoding='utf-8') as f: json.dump(rules,f,ensure_ascii=False,indent=1)
        with open(os.path.join(OUT,f"{kind}_questions.json"),'w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=1)
        print(f"[{kind}] after retry questions={len(out)}", flush=True)

def main():
    nar = gen_rules("narration", NARR_SECTIONS, "nar")
    voi = gen_rules("voice", VOICE_SECTIONS, "voi")
    process_pyqs("narration", nar)
    process_pyqs("voice", voi)

if __name__ == '__main__':
    main()
