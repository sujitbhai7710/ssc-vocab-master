#!/usr/bin/env python3
"""Merge grammar rules from 3 sources into one clean ruleset.

Backbone = rani rules (in order, 1..N). For each rani rule, find matching rules
from error (100) and aman (101) sources, and write a clean merged concept that
combines all versions into an easy-to-understand explanation. Collect unmatched
error/aman rules and append them as 'new' rules after the rani backbone.

Output: /home/z/my-project/work/grammar/merged_rules.json
  [{backbone_no, title, topic, concept, sources:[ids], examples:[...], source_rule_ids:[...]}]
Also writes: /home/z/my-project/work/grammar/rule_index.json (compact, for pyq mapping)
"""
import os, json, sys
sys.path.insert(0, '/home/z/my-project/scripts')
from ai_helper import chat_json, parallel_map

OUT = "/home/z/my-project/work/grammar"

def load(name):
    return json.load(open(os.path.join(OUT, f"src_{name}.json"), encoding='utf-8'))

rani = load("rani")      # {rules:[{source_rule_id,rule_no,title,topic,concept}], questions:[...]}
error = load("error")
aman = load("aman")

# Build candidate pool from error + aman (compact)
def compact(rule, src):
    # normalize fields
    no = rule.get("rule_no") or rule.get("concept_no")
    return {
        "id": rule.get("source_rule_id") or f"{src}-{no}",
        "src": src,
        "no": no,
        "title": (rule.get("title") or "").strip(),
        "topic": (rule.get("topic") or "").strip(),
        "concept": (rule.get("concept") or "").strip(),
        "examples": rule.get("examples") or [],
    }

candidates = [compact(r, "error") for r in error["rules"]] + [compact(r, "aman") for r in aman["rules"]]
rani_rules = [compact(r, "rani") for r in rani["rules"]]

# dedup rani rules by rule_no (keep first)
seen_no = set(); rani_backbone = []
for r in rani_rules:
    if r["no"] in seen_no:
        continue
    seen_no.add(r["no"])
    rani_backbone.append(r)
print(f"rani backbone: {len(rani_backbone)} unique rules (from {len(rani_rules)})")
print(f"candidates: {len(candidates)} (error {len(error['rules'])} + aman {len(aman['rules'])})")

# compact candidate pool string for the prompt
def cand_line(c):
    return f"{c['id']} | {c['title']} | {c['topic']} | {c['concept'][:160]}"
cand_block = "\n".join(cand_line(c) for c in candidates)

# Process rani backbone in batches of 8
BATCH = 8
matched_ids = set()
merged = []

def merge_batch(batch):
    prompt = (
        "You are merging SSC English-grammar rules from 3 sources (Rani Ma'am 60 Rules, "
        "Rahul Gupta's Top 100 Error-Spotting Rules, and Aman's 100 Grammar Rules). "
        "Below are several Rani rules (the backbone, in order) and a candidate pool of rules "
        "from the other two sources. For EACH Rani rule, find candidate pool rules that cover "
        "the SAME concept (by title/topic/meaning). Then write ONE clean, easy-to-understand "
        "merged concept (3-6 sentences) that combines the best of all matched versions into a "
        "single clear explanation a student can quickly grasp. Preserve the rule's identity.\n\n"
        "Return JSON: an array (one object per rani rule IN ORDER) with fields:\n"
        "{\"rani_no\":<int>, \"title\":\"canonical title\", \"topic\":\"\", \"concept\":\"clean merged explanation\", \"matched_ids\":[candidate ids]}\n"
        "If no candidate matches, matched_ids=[]. Do NOT invent matches. Return ONLY the JSON array."
    )
    rani_block = "\n\n".join(
        f"RANI RULE {r['no']} | {r['title']} | {r['topic']}\n{r['concept']}" for r in batch
    )
    user = prompt + "\n\n=== RANI RULES (this batch) ===\n" + rani_block + \
           "\n\n=== CANDIDATE POOL (error + aman) ===\n" + cand_block
    return chat_json([
        {"role":"system","content":"You are an expert SSC English grammar author. Output only valid JSON."},
        {"role":"user","content": user}
    ], temperature=0.2, max_tokens=4500, timeout=200, retries=4)

batches = [rani_backbone[i:i+BATCH] for i in range(0, len(rani_backbone), BATCH)]
print(f"merge batches: {len(batches)}")
def work(b):
    return merge_batch(b)
results = parallel_map(batches, work, workers=4, desc="merge")
for batch, res in results:
    if isinstance(res, Exception):
        print(f"  merge batch FAIL: {res}", flush=True)
        continue
    if isinstance(res, list):
        for item in res:
            no = item.get("rani_no")
            # find original rani rule
            orig = next((r for r in rani_backbone if r["no"] == no), None)
            if not orig:
                continue
            for mid in item.get("matched_ids", []):
                matched_ids.add(mid)
            merged.append({
                "backbone_no": no,
                "title": item.get("title") or orig["title"],
                "topic": item.get("topic") or orig["topic"],
                "concept": item.get("concept") or orig["concept"],
                "sources": ["rani"] + ([c["src"] for c in candidates if c["id"] in item.get("matched_ids",[])]),
                "matched_ids": item.get("matched_ids", []),
                "rani_id": orig["id"],
            })
        print(f"  merged batch ok ({len(res)} rules)", flush=True)

# sort merged by backbone_no
merged.sort(key=lambda x: x["backbone_no"])
print(f"merged rani rules: {len(merged)}; matched candidate ids: {len(matched_ids)}")

# Unmatched candidates -> new rules. Dedup among themselves via AI.
unmatched = [c for c in candidates if c["id"] not in matched_ids]
print(f"unmatched candidates: {len(unmatched)}")

# Dedup + write clean concepts for unmatched, in batches of 12
def dedup_batch(batch):
    prompt = (
        "Here are SSC grammar rules from error/aman sources that were NOT covered by the Rani "
        "60-rule backbone. Some may duplicate EACH OTHER. Group duplicates, and for each group "
        "write ONE clean, easy-to-understand concept (3-5 sentences). Return JSON array:\n"
        "[{\"title\":\"\",\"topic\":\"\",\"concept\":\"\",\"source_ids\":[ids in this group]}]\n"
        "One object per distinct rule. Return ONLY the JSON array."
    )
    block = "\n\n".join(f"{c['id']} | {c['title']} | {c['topic']}\n{c['concept']}" for c in batch)
    return chat_json([
        {"role":"system","content":"You are an expert SSC English grammar author. Output only valid JSON."},
        {"role":"user","content": prompt + "\n\n=== UNMATCHED RULES ===\n" + block}
    ], temperature=0.2, max_tokens=4000, timeout=200, retries=4)

UBATCH = 12
ubatches = [unmatched[i:i+UBATCH] for i in range(0, len(unmatched), UBATCH)]
new_rules = []
def uwork(b):
    return dedup_batch(b)
uresults = parallel_map(ubatches, uwork, workers=4, desc="newrules")
next_no = (max(m["backbone_no"] for m in merged) if merged else 0) + 1
for batch, res in uresults:
    if isinstance(res, Exception):
        print(f"  newrules batch FAIL: {res}", flush=True)
        continue
    if isinstance(res, list):
        for item in res:
            srcs = []
            for cid in item.get("source_ids", []):
                c = next((x for x in candidates if x["id"] == cid), None)
                if c and c["src"] not in srcs:
                    srcs.append(c["src"])
            new_rules.append({
                "backbone_no": next_no,
                "title": item.get("title",""),
                "topic": item.get("topic",""),
                "concept": item.get("concept",""),
                "sources": srcs or ["error","aman"],
                "matched_ids": item.get("source_ids", []),
                "rani_id": None,
            })
            next_no += 1
        print(f"  newrules batch ok ({len(res)} rules)", flush=True)

final = merged + new_rules
# attach examples from matched candidates + rani (rani has none in rules)
cand_by_id = {c["id"]: c for c in candidates}
for fr in final:
    ex = []
    for mid in fr.get("matched_ids", []):
        c = cand_by_id.get(mid)
        if c:
            ex.extend(c.get("examples") or [])
    fr["examples"] = ex[:6]  # cap
    fr["id"] = f"gr-{fr['backbone_no']}"
    fr["no"] = fr["backbone_no"]

# attach rani question rule_ref mapping: rani questions use rani-<no>; map to gr-<no>
# (rani_id like 'rani-1' -> backbone_no 1 -> gr-1)
# build source_rule_id -> gr-id map
src_to_gr = {}
for fr in final:
    if fr.get("rani_id"):
        src_to_gr[fr["rani_id"]] = fr["id"]
    for mid in fr.get("matched_ids", []):
        src_to_gr[mid] = fr["id"]

with open(os.path.join(OUT, "merged_rules.json"), "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "src_to_gr.json"), "w", encoding="utf-8") as f:
    json.dump(src_to_gr, f, ensure_ascii=False)
# compact rule index for pyq mapping
index = [{"id": r["id"], "no": r["no"], "title": r["title"], "topic": r["topic"]} for r in final]
with open(os.path.join(OUT, "rule_index.json"), "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=1)
print(f"FINAL rules: {len(final)} (rani backbone {len(merged)} + new {len(new_rules)})")
print(f"-> merged_rules.json, rule_index.json, src_to_gr.json")
