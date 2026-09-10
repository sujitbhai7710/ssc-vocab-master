#!/usr/bin/env python3
"""Deduplicate the 167 combined rules -> 155 unique rules (clean version).

Drops 12 verified duplicate rules, remaps their questions to the kept rule,
renumbers the remaining rules 1..155, and rewrites all data files + the markdown.
"""
import json, os, re, html

ROOT = "/home/z/my-project/ssc-vocab-master"
PUB = os.path.join(ROOT, "public/data/grammar")

# drop_no -> keep_no (verified by deterministic semantic analysis)
DROP = {101:73, 126:119, 128:122, 129:63, 159:115, 160:116, 162:118,
        163:119, 164:120, 165:121, 166:122, 167:123}

rules = json.load(open(os.path.join(PUB, "rules.json"), encoding="utf-8"))
questions = json.load(open(os.path.join(PUB, "questions.json"), encoding="utf-8"))
print(f"before: {len(rules)} rules, {len(questions)} questions")

# 1. Build old_no -> new_no for KEPT rules (sequential 1..N), and collect dropped qids
old_no_to_new_no = {}
kept_rules = []
new_idx = 0
dropped_qids = []
for r in rules:
    if r['no'] in DROP:
        dropped_qids.extend(r.get('questionIds', []))
        continue
    new_idx += 1
    old_no_to_new_no[r['no']] = new_idx
    r['id'] = f"gr-{new_idx}"
    r['no'] = new_idx
    kept_rules.append(r)
print(f"kept {len(kept_rules)} rules; remapping {len(dropped_qids)} questions from dropped rules")

# 2. Remap questions: ruleId old gr-<old_no> -> new gr-<new_no> (kept) or keeper's new (dropped)
def new_id_for_old_rule(old_no):
    if old_no in old_no_to_new_no:           # kept rule
        return f"gr-{old_no_to_new_no[old_no]}"
    if old_no in DROP:                        # dropped rule -> its keeper
        keep_old = DROP[old_no]
        return f"gr-{old_no_to_new_no[keep_old]}"
    return None

for q in questions:
    rid = q.get('ruleId')
    if not rid: continue
    m = re.match(r'gr-(\d+)$', rid)
    if not m: continue
    old_no = int(m.group(1))
    nid = new_id_for_old_rule(old_no)
    q['ruleId'] = nid  # may be None (orphan) — fine

# 3. Rebuild questionIds on each kept rule
by_rule = {}
for q in questions:
    rid = q.get('ruleId')
    if rid: by_rule.setdefault(rid, []).append(q['id'])
for r in kept_rules:
    r['questionIds'] = by_rule.get(r['id'], [])

# 4. Write rules.json + questions.json
with open(os.path.join(PUB, "rules.json"), "w", encoding="utf-8") as f:
    json.dump(kept_rules, f, ensure_ascii=False, indent=1)
with open(os.path.join(PUB, "questions.json"), "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=1)

# 5. Regenerate per-rule qs files
QSDIR = os.path.join(PUB, "qs")
for fn in os.listdir(QSDIR):
    if re.match(r"gr-\d+\.json$", fn):
        os.remove(os.path.join(QSDIR, fn))
written = 0
for r in kept_rules:
    qs = [q for q in questions if q.get('ruleId') == r['id']]
    if qs:
        with open(os.path.join(QSDIR, f"gr-{r['no']}.json"), "w", encoding="utf-8") as f:
            json.dump(qs, f, ensure_ascii=False)
        written += 1
with open(os.path.join(QSDIR, "index.json"), "w", encoding="utf-8") as f:
    json.dump(sorted([r['no'] for r in kept_rules]), f)

# 6. Update summary
summ = json.load(open(os.path.join(PUB, "summary.json"), encoding="utf-8"))
summ['grammarRules'] = len(kept_rules)
with open(os.path.join(PUB, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(summ, f, ensure_ascii=False, indent=1)
print(f"-> rules.json ({len(kept_rules)}), questions.json ({len(questions)}), qs/ ({written} files)")

# 7. Regenerate combined-grammar-rules.md
def clean(s):
    if not s: return ""
    s = re.sub(r'<[^>]+>', '', s); s = html.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()

lines = ["# Combined Grammar Rules — Merged from 3 Sources (Deduplicated)\n",
         "A single deduplicated list following **Rani Ma'am's 60-rule order** as the backbone, ",
         "with matching rules from **Aman Sir (100)** and **Manisha Bansal (120)** merged in ",
         "(concepts rewritten to combine the best of each), then extra rules from Aman/Manisha ",
         "appended after rule 60. Duplicate rules have been removed — no two rules teach the same concept.\n",
         f"**Total: {len(kept_rules)} unique rules** (was 167; 12 duplicates removed)\n",
         "---\n"]
for r in kept_rules:
    title = clean(r.get("title","")) or f"Rule {r['no']}"
    topic = clean(r.get("topic",""))
    concept = clean(r.get("concept",""))
    sources = r.get("sources") or []
    lines.append(f"## Rule {r['no']}: {title}\n")
    if topic: lines.append(f"**Topic:** {topic}\n")
    if sources:
        src_labels = {"rani":"Rani Ma'am","error":"Rahul Gupta","aman":"Aman Sir","pyq":"PYQ"}.get
        srcs = ", ".join(sorted(set(src_labels(s,s) for s in sources)))
        lines.append(f"**Sources:** {srcs}\n")
    lines.append(f"\n{concept}\n")
    exs = r.get("examples") or []
    if exs:
        lines.append("\n**Examples**\n")
        for ex in exs[:5]:
            inc = clean(ex.get("incorrect") or ex.get("sentence") or "")
            cor = clean(ex.get("correct") or ex.get("correction") or "")
            if inc and cor:
                lines.append(f"- ✗ {inc}")
                lines.append(f"- ✓ {cor}")
            elif cor:
                lines.append(f"- {cor}")
        lines.append("")
    lines.append("")
with open(os.path.join(ROOT, "docs/rules/combined-grammar-rules.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"-> docs/rules/combined-grammar-rules.md ({len(kept_rules)} rules)")
print("DONE")
