#!/usr/bin/env python3
"""Build clean grammar rules from Rani(60)+Aman(100)+Manisha(120) via Cline AI.
Resumable: saves checkpoint after each phase to work/grammar_clean/checkpoint.json.
Run repeatedly until it prints DONE.

Phases:
  1. match_aman   — assign each aman rule to a rani rule (or null)
  2. match_manisha — same for manisha
  3. merge_rani   — merge each rani group (rani + matched aman/manisha) into one clean rule
  4. cluster_new  — cluster unmatched aman+manisha rules by concept
  5. merge_new    — merge each cluster into one clean rule
  6. assemble     — final list (60 rani + new) -> rules_clean.json + markdown
"""
import os, json, re, sys, html as htmlmod
sys.path.insert(0, '/home/z/my-project/scripts')
from jw_helper import chat_json, parallel_map

ROOT = "/home/z/my-project/ssc-vocab-master"
WORK = "/home/z/my-project/work/grammar_clean"
os.makedirs(WORK, exist_ok=True)
CKPT = os.path.join(WORK, "checkpoint.json")

def load(p): return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))
def clean(s):
    if not s: return ""
    s = re.sub(r'<[^>]+>', '', s); s = htmlmod.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()

def load_ckpt():
    if os.path.exists(CKPT):
        try: return json.load(open(CKPT, encoding="utf-8"))
        except: pass
    return {}

def save_ckpt(d):
    with open(CKPT, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)

# ---- load sources ----
rani_src = load("scripts/work-data/src_rani.json")
aman_src = load("scripts/work-data/src_aman.json")
manisha = load("public/data/manisha/rules.json")

from collections import defaultdict
rani_qs = defaultdict(list)
for q in rani_src["questions"]:
    rani_qs[q["rule_ref"]].append(q)

# normalize
rani_rules = []
seen_no = set()
for r in rani_src["rules"]:
    no = r["rule_no"]
    if no in seen_no: continue
    seen_no.add(no)
    exs = []
    for q in rani_qs.get(r["source_rule_id"], [])[:3]:
        sent = clean(q.get("question","")).replace(" / "," ").replace("/"," ")
        sent = re.sub(r'\s+', ' ', sent).strip()
        exs.append({"sentence": sent, "fix": clean(q.get("explanation",""))})
    rani_rules.append({"src":"rani","src_id":r["source_rule_id"],"no":no,
        "title":clean(r.get("title","")),"topic":clean(r.get("topic","")),
        "concept":clean(r.get("concept","")),"examples":exs})

aman_rules = []
for r in aman_src["rules"]:
    aman_rules.append({"src":"aman","src_id":r["source_rule_id"],"no":r.get("concept_no"),
        "title":clean(r.get("title","")),"topic":clean(r.get("topic","")),
        "concept":clean(r.get("concept","")),
        "examples":[{"incorrect":clean(e.get("incorrect","")),"correct":clean(e.get("correct",""))}
                    for e in (r.get("examples") or [])[:3]]})

manisha_rules = []
for r in manisha:
    exs = []
    for ex in (r.get("examples") or [])[:3]:
        ex = clean(ex)
        if ex.startswith("✗"): exs.append({"incorrect": ex[1:].strip()})
        elif ex.startswith("✓"): exs.append({"correct": ex[1:].strip()})
        else: exs.append({"sentence": ex})
    manisha_rules.append({"src":"manisha","src_id":f"manisha-{r['num']}","no":r["num"],
        "title":clean(r.get("title","")),"topic":clean(r.get("cat","")),
        "concept":clean(r.get("explain","")),"examples":exs})

# non-grammar filter
NON_GRAMMAR = re.compile(r'\b(one[- ]word substitution|synonym|antonym|idiom|spelling|misspell|cloze|comprehension|paraphrase|phrasal verb|collocation|contextual (word|vocabulary)|word choice|meaning[- ]preserving)\b', re.I)
def is_grammar(rule):
    t = (rule["title"]+" "+rule["topic"]+" "+rule["concept"]).lower()
    if NON_GRAMMAR.search(t):
        if re.search(r"\b(its|it's|who|whom|fewer|less|affect|effect|lay|lie|their|there)\b", t): return True
        return False
    return True

aman_g = [r for r in aman_rules if is_grammar(r)]
manisha_g = [r for r in manisha_rules if is_grammar(r)]
rani_g = rani_rules  # all 60 grammar
print(f"loaded: rani {len(rani_g)}, aman {len(aman_g)}, manisha {len(manisha_g)}", flush=True)

rani_index = "\n".join(f"R{r['no']} | {r['title']} | {r['topic']} | {r['concept'][:120]}" for r in rani_g)

def assign_one(rule):
    prompt = ("Does this rule teach the SAME grammar concept as any RANI rule below? "
              "If yes return the matching Rani rule number (integer). If no Rani rule covers it, return null.\n\n"
              f"RANI INDEX:\n{rani_index}\n\n"
              f"RULE TO CHECK: [{rule['src_id']}] [{rule['topic']}] {rule['title']}\n{rule['concept'][:200]}\n\n"
              "Return JSON: {\"rani_no\": <int or null>}. Return ONLY the JSON.")
    return chat_json([{"role":"system","content":"You are an expert SSC English grammar editor. Output only valid JSON."},
                      {"role":"user","content":prompt}], temperature=0.0, max_tokens=200, timeout=120, retries=5)

ckpt = load_ckpt()

# Phase 1: match aman (resumable, PARALLEL)
aman_match = ckpt.get("aman_match", {})
todo_aman = [r for r in aman_g if r["src_id"] not in aman_match]
if todo_aman:
    print(f"PHASE 1: matching {len(todo_aman)} remaining aman rules (of {len(aman_g)}) [parallel]...", flush=True)
    def work(rule):
        try:
            res = assign_one(rule)
            return rule["src_id"], (res.get("rani_no") if isinstance(res, dict) else None)
        except Exception as e:
            print(f"  {rule['src_id']} FAIL: {e}", flush=True)
            return rule["src_id"], None
    res = parallel_map(todo_aman, work, workers=6, desc="aman")
    for _item, val in res:
        # val is (src_id, rani_no) tuple
        if isinstance(val, Exception) or not isinstance(val, tuple):
            continue
        sid, rn = val
        aman_match[sid] = rn
    ckpt["aman_match"] = aman_match; save_ckpt(ckpt)
    print(f"  aman matched: {sum(1 for v in aman_match.values() if v)}/{len(aman_g)}", flush=True)
else:
    print("PHASE 1 (aman match): complete (cached)", flush=True)

# Phase 2: match manisha (resumable, PARALLEL)
manisha_match = ckpt.get("manisha_match", {})
todo_manisha = [r for r in manisha_g if r["src_id"] not in manisha_match]
if todo_manisha:
    print(f"PHASE 2: matching {len(todo_manisha)} remaining manisha rules (of {len(manisha_g)}) [parallel]...", flush=True)
    def work_m(rule):
        try:
            res = assign_one(rule)
            return rule["src_id"], (res.get("rani_no") if isinstance(res, dict) else None)
        except Exception as e:
            print(f"  {rule['src_id']} FAIL: {e}", flush=True)
            return rule["src_id"], None
    res = parallel_map(todo_manisha, work_m, workers=6, desc="manisha")
    for _item, val in res:
        if isinstance(val, Exception) or not isinstance(val, tuple):
            continue
        sid, rn = val
        manisha_match[sid] = rn
    ckpt["manisha_match"] = manisha_match; save_ckpt(ckpt)
    print(f"  manisha matched: {sum(1 for v in manisha_match.values() if v)}/{len(manisha_g)}", flush=True)
else:
    print("PHASE 2 (manisha match): complete (cached)", flush=True)

# Phase 3: merge each rani group (resumable)
aman_match = ckpt["aman_match"]; manisha_match = ckpt["manisha_match"]
if "unmatched_aman" not in ckpt or "unmatched_manisha" not in ckpt:
    rani_groups = {r["no"]: {"rani": r, "aman": [], "manisha": []} for r in rani_g}
    unmatched_aman = []; unmatched_manisha = []
    for r in aman_g:
        rn = aman_match.get(r["src_id"])
        if rn and rn in rani_groups: rani_groups[rn]["aman"].append(r)
        else: unmatched_aman.append(r)
    for r in manisha_g:
        rn = manisha_match.get(r["src_id"])
        if rn and rn in rani_groups: rani_groups[rn]["manisha"].append(r)
        else: unmatched_manisha.append(r)
    ckpt["unmatched_aman"] = [r["src_id"] for r in unmatched_aman]
    ckpt["unmatched_manisha"] = [r["src_id"] for r in unmatched_manisha]
    ckpt["rani_group_map"] = {str(rn): {"aman_ids":[a["src_id"] for a in g["aman"]], "manisha_ids":[m["src_id"] for m in g["manisha"]]} for rn,g in rani_groups.items()}
    save_ckpt(ckpt)
    print(f"  unmatched: aman {len(unmatched_aman)}, manisha {len(unmatched_manisha)}", flush=True)
else:
    print("PHASE 3 grouping: cached", flush=True)

# build rani_groups from cached map
rani_groups = {r["no"]: {"rani": r, "aman": [], "manisha": []} for r in rani_g}
aid_to_rule = {r["src_id"]: r for r in aman_g}
mid_to_rule = {r["src_id"]: r for r in manisha_g}
for no_str, gmap in ckpt.get("rani_group_map", {}).items():
    no = int(no_str)
    if no in rani_groups:
        rani_groups[no]["aman"] = [aid_to_rule[i] for i in gmap["aman_ids"] if i in aid_to_rule]
        rani_groups[no]["manisha"] = [mid_to_rule[i] for i in gmap["manisha_ids"] if i in mid_to_rule]

merged_rani = ckpt.get("merged_rani", [])
done_nos = set(r.get("_rani_no") for r in merged_rani if "_rani_no" in r)
todo_rani = [r for r in rani_g if r["no"] not in done_nos]
if todo_rani:
    print(f"PHASE 3: merging {len(todo_rani)} remaining rani groups [parallel]...", flush=True)
    def merge_one(r):
        g = rani_groups[r["no"]]
        parts = [f"RANI: [{g['rani']['topic']}] {g['rani']['title']}\n{g['rani']['concept']}"]
        for a in g["aman"]: parts.append(f"AMAN: [{a['topic']}] {a['title']}\n{a['concept']}")
        for m in g["manisha"]: parts.append(f"MANISHA: [{m['topic']}] {m['title']}\n{m['concept']}")
        block = "\n\n".join(parts)
        try:
            prompt = ("Write ONE merged grammar rule combining the best of these source rules into a clear, "
                      "easy-to-understand explanation (3-6 sentences). Keep the title short. Include 2-4 examples (✗/✓ format).\n"
                      "Return JSON: {\"title\":\"\",\"topic\":\"\",\"concept\":\"\",\"examples\":[{\"incorrect\":\"\",\"correct\":\"\"}]}\n"
                      "Return ONLY the JSON.\n\n=== SOURCES ===\n" + block)
            mr = chat_json([{"role":"system","content":"You are an expert SSC English grammar author. Output only valid JSON."},
                            {"role":"user","content":prompt}], temperature=0.2, max_tokens=1500, timeout=120, retries=5)
            sources = ["rani"] + (["aman"] if g["aman"] else []) + (["manisha"] if g["manisha"] else [])
            mr["_rani_no"] = r["no"]
            return mr
        except Exception as e:
            print(f"  rani R{r['no']} merge FAIL: {e}", flush=True)
            return {"_rani_no":r["no"],"title":g["rani"]["title"],"topic":g["rani"]["topic"],
                "concept":g["rani"]["concept"],"examples":g["rani"]["examples"],"sources":["rani"]}
    res = parallel_map(todo_rani, merge_one, workers=6, desc="rani-merge")
    for r, mr in res:
        if not isinstance(mr, Exception) and isinstance(mr, dict):
            merged_rani.append(mr)
    ckpt["merged_rani"] = merged_rani; save_ckpt(ckpt)
    print(f"  merged {len(merged_rani)} rani rules", flush=True)
else:
    print("PHASE 3 (merge rani): complete (cached)", flush=True)

# Phase 4 + 5: cluster + merge unmatched (resumable)
um_aid = set(ckpt.get("unmatched_aman", []))
um_mid = set(ckpt.get("unmatched_manisha", []))
unmatched = [r for r in aman_g if r["src_id"] in um_aid] + [r for r in manisha_g if r["src_id"] in um_mid]

# Phase 4: clustering (resumable — compute parent array, cached after first run)
if "cluster_parent" not in ckpt:
    print(f"PHASE 4: clustering {len(unmatched)} unmatched rules...", flush=True)
    parent = list(range(len(unmatched)))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b): parent[find(a)]=find(b)
    for bi in range(0, len(unmatched), 25):
        batch = unmatched[bi:bi+25]
        idx = "\n".join(f"{i}. [{r['src_id']}] [{r['topic']}] {r['title']} :: {r['concept'][:140]}" for i,r in enumerate(batch))
        try:
            prompt = ("Group rules below teaching the SAME grammar concept. Return JSON {\"groups\":[{\"is\":[0,2,5]}]} — "
                      "one group per duplicate set; non-duplicates appear in NO group. If none, return {\"groups\":[]}. Return ONLY the JSON.\n\n"
                      "=== RULES ===\n" + idx)
            res = chat_json([{"role":"system","content":"You are an expert SSC English grammar editor. Output only valid JSON."},
                             {"role":"user","content":prompt}], temperature=0.0, max_tokens=1200, timeout=150, retries=5)
            for g in res.get("groups", []):
                is_ = g.get("is", [])
                for k in range(1, len(is_)):
                    if is_[k] < len(batch) and is_[0] < len(batch):
                        union(bi+is_[0], bi+is_[k])
        except Exception as e:
            print(f"  cluster batch FAIL: {e}", flush=True)
        print(f"  cluster {min(bi+25,len(unmatched))}/{len(unmatched)}", flush=True)
        ckpt["cluster_parent"] = parent; save_ckpt(ckpt)
    ckpt["cluster_parent"] = parent; save_ckpt(ckpt)
else:
    parent = ckpt["cluster_parent"]
    print(f"PHASE 4 (cluster): cached", flush=True)

from collections import defaultdict as _dd
# define find() at module level (needed even when phase 4 is cached)
def _make_find(parent):
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    return find
parent = ckpt["cluster_parent"]
find = _make_find(parent)
clusters = _dd(list)
for i in range(len(unmatched)): clusters[find(i)].append(unmatched[i])
cluster_list = list(clusters.values())
print(f"  -> {len(cluster_list)} clusters", flush=True)

# Phase 5: merge each cluster (resumable, PARALLEL)
merged_new = ckpt.get("merged_new", [])
done_clusters = set(m.get("_cluster_idx") for m in merged_new if "_cluster_idx" in m)
todo_clusters = [(i, c) for i, c in enumerate(cluster_list) if i not in done_clusters]
if todo_clusters:
    print(f"PHASE 5: merging {len(todo_clusters)} remaining clusters [parallel]...", flush=True)
    def merge_cluster(item):
        ci, c = item
        parts = [f"{r['src'].upper()}: [{r['topic']}] {r['title']}\n{r['concept']}" for r in c]
        block = "\n\n".join(parts)
        try:
            prompt = ("Write ONE merged grammar rule combining the best of these sources into a clear explanation (3-6 sentences). "
                      "Include 2-4 examples (✗/✓ format).\nReturn JSON: {\"title\":\"\",\"topic\":\"\",\"concept\":\"\",\"examples\":[{\"incorrect\":\"\",\"correct\":\"\"}]}\n"
                      "Return ONLY the JSON.\n\n=== SOURCES ===\n" + block)
            mr = chat_json([{"role":"system","content":"You are an expert SSC English grammar author. Output only valid JSON."},
                            {"role":"user","content":prompt}], temperature=0.2, max_tokens=1500, timeout=120, retries=5)
            sources = sorted(set(x["src"] for x in c))
            mr["_cluster_idx"] = ci
            mr["sources"] = sources
            return mr
        except Exception as e:
            print(f"  cluster {ci} merge FAIL: {e}", flush=True)
            return {"_cluster_idx":ci,"title":c[0]["title"],"topic":c[0]["topic"],
                "concept":c[0]["concept"],"examples":c[0]["examples"],
                "sources":sorted(set(x["src"] for x in c))}
    res = parallel_map(todo_clusters, merge_cluster, workers=6, desc="merge-new")
    for item, mr in res:
        if not isinstance(mr, Exception) and isinstance(mr, dict):
            merged_new.append(mr)
    ckpt["merged_new"] = merged_new; save_ckpt(ckpt)
    print(f"  merged {len(merged_new)} new rules", flush=True)
else:
    print("PHASE 5 (merge new): complete (cached)", flush=True)

# Phase 6: assemble
print("PHASE 6: assembling final...", flush=True)
# sort merged_rani by _rani_no (Rani's original backbone order)
mr_list = ckpt["merged_rani"]
mr_sorted = sorted(mr_list, key=lambda r: r.get("_rani_no", 999))
final = mr_sorted + ckpt["merged_new"]
for i, r in enumerate(final, 1):
    r["no"] = i; r["id"] = f"gr-{i}"; r["questionIds"] = []
    # ensure sources exists (some AI responses may omit it)
    if "sources" not in r or not r["sources"]:
        if "_rani_no" in r: r["sources"] = ["rani"]
        else: r["sources"] = ["aman","manisha"]
    for k in ("_rani_no","_cluster_idx"): r.pop(k, None)
print(f"FINAL: {len(final)} rules ({len(ckpt['merged_rani'])} rani + {len(ckpt['merged_new'])} new)", flush=True)
from collections import Counter
sc = Counter()
for r in final:
    for s in r["sources"]: sc[s]+=1
print("source coverage:", dict(sc), flush=True)

with open(os.path.join(ROOT, "public/data/grammar/rules_clean.json"), "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=1)
print("-> public/data/grammar/rules_clean.json", flush=True)

# markdown
lines = ["# Combined Grammar Rules — Rani Ma'am + Aman Sir + Manisha Bansal (Clean)\n",
         "Built fresh from the 3 source PDFs using AI analysis. Pure grammar rules only — "
         "vocabulary, one-word substitution, synonyms, antonyms, idioms, and spelling are excluded "
         "(they are not grammar rules). Rani Ma'am's 60 rules form the backbone order; matching rules "
         "from Aman Sir and Manisha Bansal are merged into clearer combined explanations; extra rules "
         "from Aman/Manisha are appended after rule 60. No duplicate rule teaches the same concept.\n",
         f"**Total: {len(final)} unique grammar rules** "
         f"({len(ckpt['merged_rani'])} Rani backbone + {len(ckpt['merged_new'])} new from Aman/Manisha)\n",
         "---\n"]
for r in final:
    lines.append(f"## Rule {r['no']}: {clean(r['title'])}\n")
    if r.get("topic"): lines.append(f"**Topic:** {clean(r['topic'])}\n")
    src_labels = {"rani":"Rani Ma'am","aman":"Aman Sir","manisha":"Manisha Bansal"}.get
    lines.append(f"**Sources:** {', '.join(src_labels(s,s) for s in r['sources'])}\n")
    lines.append(f"\n{clean(r['concept'])}\n")
    if r.get("examples"):
        lines.append("\n**Examples**\n")
        for ex in r["examples"][:4]:
            inc = clean(ex.get("incorrect") or ex.get("sentence") or "")
            cor = clean(ex.get("correct") or ex.get("fix") or "")
            # strip any leading ✗/✓ that the AI already put in the text
            inc = re.sub(r'^[✗✘]\s*', '', inc).strip()
            cor = re.sub(r'^[✓✔]\s*', '', cor).strip()
            if inc and cor: lines.append(f"- ✗ {inc}"); lines.append(f"- ✓ {cor}")
            elif cor: lines.append(f"- ✓ {cor}")
            elif inc: lines.append(f"- ✗ {inc}")
        lines.append("")
    lines.append("")
with open(os.path.join(ROOT, "docs/rules/combined-grammar-rules.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("-> docs/rules/combined-grammar-rules.md", flush=True)
print("DONE", flush=True)
