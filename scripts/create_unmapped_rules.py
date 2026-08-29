#!/usr/bin/env python3
"""Cluster the 515 unmapped grammar questions into NEW rules (per user request),
append them to the ruleset (gr-115+), and remap their questionIds.

Step 1: batch the unmapped questions + existing rule index; AI returns per-question
        {qid, ruleId} where ruleId is an EXISTING gr-id OR a proposed new short label.
Step 2: collect proposed-new labels; AI dedups/merges them into final new rules with
        clean concepts.
Step 3: assign questions, append new rules, rewrite rules.json + questions.json.
"""
import os, json, sys
sys.path.insert(0, '/home/z/my-project/scripts')
from ai_helper import chat_json, parallel_map

PUB = "/home/z/my-project/ssc-vocab-master/public/data/grammar"
WORK = "/home/z/my-project/work/grammar"

rules = json.load(open(os.path.join(PUB,"rules.json"), encoding='utf-8'))
questions = json.load(open(os.path.join(PUB,"questions.json"), encoding='utf-8'))
RULE_INDEX_STR = "\n".join(f"{r['id']} | Rule {r['no']} | {r['title']} | {r['topic']}" for r in rules)

unmapped = [q for q in questions if not q.get("ruleId")]
print(f"unmapped: {len(unmapped)}", flush=True)
if not unmapped:
    print("nothing to do"); sys.exit(0)

def assign_batch(batch):
    prompt = (
        "You are an SSC English-grammar expert. For each grammar MCQ below, assign it to the single "
        "best-matching EXISTING rule from the RULE INDEX (return that ruleId like 'gr-7'). If NONE of "
        "the existing rules fits, propose a NEW short rule label (3-6 words, the grammar concept tested, "
        "e.g. 'Subject-Verb Agreement with 'One of''). Use the existing ruleId whenever reasonable; only "
        "propose a new label when truly no existing rule covers it.\n\n"
        "RULE INDEX:\n" + RULE_INDEX_STR + "\n\n"
        "Return JSON array, one object per question IN ORDER:\n"
        "[{\"qid\":\"\",\"ruleId\":\"gr-N or NEW: <short label>\"}]\n"
        "Return ONLY the JSON array."
    )
    def fmt(q):
        return f"[{q['id']}] ({q['source']}) {q.get('prompt','')}\n   sentence: {q.get('sentence','')}\n   options: {q.get('options',[])}"
    block = "\n\n".join(fmt(q) for q in batch)
    return chat_json([
        {"role":"system","content":"You are an expert SSC English grammar tutor. Output only valid JSON arrays."},
        {"role":"user","content": prompt + "\n\n=== QUESTIONS ===\n" + block}
    ], temperature=0.1, max_tokens=3500, timeout=200, retries=4)

BATCH = 25
batches = [unmapped[i:i+BATCH] for i in range(0, len(unmapped), BATCH)]
print(f"batches: {len(batches)}", flush=True)
def work(b): return assign_batch(b)
results = parallel_map(batches, work, workers=6, desc="unmapped")
assign = {}  # qid -> ruleId string
for batch, res in results:
    if isinstance(res, Exception) or not isinstance(res, list):
        continue
    for item in res:
        qid = item.get("qid")
        if qid: assign[qid] = item.get("ruleId")
print(f"assigned: {len(assign)}", flush=True)

# split into existing vs new
existing_mapped = {}
new_groups = {}  # label -> [qids]
for q in unmapped:
    rid = assign.get(q["id"])
    if not rid:
        continue
    if rid.startswith("gr-"):
        existing_mapped[q["id"]] = rid
    elif rid.startswith("NEW:"):
        label = rid[4:].strip()
        new_groups.setdefault(label, []).append(q["id"])
    else:
        new_groups.setdefault(rid, []).append(q["id"])
print(f"remapped to existing: {len(existing_mapped)}; new groups: {len(new_groups)} ({sum(len(v) for v in new_groups.values())} qs)", flush=True)

# Step 2: dedup/merge new labels into final new rules
new_labels = list(new_groups.keys())
if new_labels:
    def merge_labels(labels):
        prompt = (
            "Here are proposed grammar-rule labels (from clustering SSC questions). Some labels mean the "
            "same thing. Merge duplicates and for each distinct rule write a clean, easy-to-understand "
            "concept (3-5 sentences). Return JSON array:\n"
            "[{\"title\":\"canonical title\",\"topic\":\"\",\"concept\":\"\",\"source_labels\":[labels in this group]}]\n"
            "Return ONLY the JSON array."
        )
        block = "\n".join(f"- {l}" for l in labels)
        return chat_json([
            {"role":"system","content":"You are an expert SSC English grammar author. Output only valid JSON arrays."},
            {"role":"user","content": prompt + "\n\n=== LABELS ===\n" + block}
        ], temperature=0.2, max_tokens=3000, timeout=200, retries=4)
    # merge in one batch if small, else batches of 30
    if len(new_labels) <= 40:
        merged = merge_labels(new_labels)
        merged = [merged] if isinstance(merged, list) else []
        mlists = [new_labels]
    else:
        LB = 30
        lbatches = [new_labels[i:i+LB] for i in range(0,len(new_labels),LB)]
        r2 = parallel_map(lbatches, merge_labels, workers=4, desc="mergelabels")
        merged = []; mlists = lbatches
        for b,res in r2:
            if isinstance(res,list): merged.extend(res)
    # build label->newrule map
    label_to_newrule = {}
    final_new = []
    next_no = (max(r["no"] for r in rules) if rules else 0) + 1
    for m in merged:
        nid = f"gr-{next_no}"
        qids = []
        for lab in m.get("source_labels",[]):
            if lab in new_groups:
                qids.extend(new_groups[lab])
                label_to_newrule[lab] = nid
        final_new.append({
            "id": nid, "no": next_no,
            "title": m.get("title",""), "topic": m.get("topic",""),
            "concept": m.get("concept",""),
            "examples": [], "sources": ["pyq"],
            "questionIds": qids,
        })
        next_no += 1
    # any new_groups labels not merged -> create generic rules
    for lab, qids in new_groups.items():
        if lab not in label_to_newrule:
            nid = f"gr-{next_no}"
            final_new.append({"id":nid,"no":next_no,"title":lab,"topic":"Grammar",
                "concept":lab,"examples":[],"sources":["pyq"],"questionIds":qids})
            label_to_newrule[lab] = nid
            next_no += 1
    print(f"new rules created: {len(final_new)}", flush=True)
    rules.extend(final_new)

# remap question ruleIds
for q in questions:
    if q.get("ruleId"): continue
    qid = q["id"]
    if qid in existing_mapped:
        q["ruleId"] = existing_mapped[qid]
    else:
        for lab, nid in label_to_newrule.items() if new_labels else []:
            if qid in new_groups.get(lab, []):
                q["ruleId"] = nid; break

# rebuild questionIds on all rules
by_rule = {}
for q in questions:
    if q.get("ruleId"):
        by_rule.setdefault(q["ruleId"], []).append(q["id"])
for r in rules:
    r["questionIds"] = by_rule.get(r["id"], [])

still_unmapped = sum(1 for q in questions if not q.get("ruleId"))
print(f"final rules: {len(rules)}; still unmapped: {still_unmapped}", flush=True)

with open(os.path.join(PUB,"rules.json"),'w',encoding='utf-8') as f:
    json.dump(rules, f, ensure_ascii=False, indent=1)
with open(os.path.join(PUB,"questions.json"),'w',encoding='utf-8') as f:
    json.dump(questions, f, ensure_ascii=False, indent=1)
# update summary
summ = json.load(open(os.path.join(PUB,"summary.json"),encoding='utf-8'))
summ["grammarRules"] = len(rules)
summ["unmappedQuestions"] = still_unmapped
with open(os.path.join(PUB,"summary.json"),'w',encoding='utf-8') as f:
    json.dump(summ, f, ensure_ascii=False, indent=1)
print("done; rules.json + questions.json + summary.json updated")
