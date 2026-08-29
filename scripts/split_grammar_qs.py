#!/usr/bin/env python3
"""Split grammar questions.json into per-rule files for lazy loading.
Also keep the full file for any fallback use.
  public/data/grammar/qs/gr-<no>.json  -> [questions for that rule]
"""
import os, json
PUB = "/home/z/my-project/ssc-vocab-master/public/data/grammar"
QSDIR = os.path.join(PUB, "qs")
os.makedirs(QSDIR, exist_ok=True)
questions = json.load(open(os.path.join(PUB,"questions.json"), encoding='utf-8'))
rules = json.load(open(os.path.join(PUB,"rules.json"), encoding='utf-8'))
# group by ruleId
by_rule = {}
for q in questions:
    rid = q.get("ruleId")
    if rid:
        by_rule.setdefault(rid, []).append(q)
# write per-rule file using the rule's "no" for a stable filename
no_by_id = {r["id"]: r["no"] for r in rules}
written = 0
for rid, qs in by_rule.items():
    no = no_by_id.get(rid)
    if no is None:
        continue
    with open(os.path.join(QSDIR, f"gr-{no}.json"),'w',encoding='utf-8') as f:
        json.dump(qs, f, ensure_ascii=False)
    written += 1
# index: rule id -> file
index = {rid: f"gr-{no_by_id[rid]}.json" for rid in by_rule if rid in no_by_id}
with open(os.path.join(QSDIR,"index.json"),'w',encoding='utf-8') as f:
    json.dump(index, f, ensure_ascii=False)
print(f"split: {written} rule files, {sum(len(v) for v in by_rule.values())} questions; index {len(index)}")
# also copy qs to dist after build (build will copy public/ anyway)
