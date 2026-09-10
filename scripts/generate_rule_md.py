#!/usr/bin/env python3
"""Generate markdown rule files from the 3 grammar sources + a merged combined file.

Outputs (in docs/rules/):
  1. rani-maam-60-rules.md        — Rani Ma'am's 60 rules (concept + examples from her error-spotting Qs)
  2. aman-sir-100-rules.md         — Aman Sir's 100 rules (concept + examples)
  3. manisha-bansal-120-rules.md   — Manisha Bansal's 120 rules (explain + usage + examples + trick)
  4. combined-grammar-rules.md     — merged list (Rani order + Aman/Manisha extras), deduped, better wording

Format per rule:
  ## Rule N: Title
  **Topic:** ... 
  Concept/explanation paragraph
  **Examples**
  ✗ incorrect
  ✓ correct
  (trick if available)
"""
import os, json, re, html
from collections import defaultdict, OrderedDict

ROOT = "/home/z/my-project/ssc-vocab-master"
OUT = os.path.join(ROOT, "docs/rules")
os.makedirs(OUT, exist_ok=True)

def clean(s):
    """strip HTML tags, normalize whitespace, decode entities."""
    if not s: return ""
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def load(p):
    return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))

# ---- sources ----
rani_src = load("scripts/work-data/src_rani.json")
aman_src = load("scripts/work-data/src_aman.json")
manisha = load("public/data/manisha/rules.json")
merged = load("public/data/grammar/rules.json")

# rani: dedupe by rule_no -> 60 unique
rani_rules = OrderedDict()
for r in rani_src["rules"]:
    no = r["rule_no"]
    if no in rani_rules: continue
    rani_rules[no] = r
# rani questions grouped by rule_ref
rani_qs = defaultdict(list)
for q in rani_src["questions"]:
    rani_qs[q["rule_ref"]].append(q)

# ---- 1. RANI 60 ----
def rani_examples(rule_ref, max_n=3):
    out = []
    for q in rani_qs.get(rule_ref, [])[:max_n]:
        sent = clean(q.get("question","")).replace(" / ", " ").replace("/", " ")
        sent = re.sub(r'\s+', ' ', sent).strip()
        expl = clean(q.get("explanation",""))
        out.append((sent, expl))
    return out

lines = ["# Rani Ma'am — 60 Rules of Grammar\n",
         "Source: *English With Rani Ma'am — 60 Rules of Grammar 2.0* PDF. ",
         "60 rules (deduped from 64 OCR-scattered headers). Examples are drawn from the ",
         "error-spotting questions that accompany each rule in the PDF.\n",
         "---\n"]
for no, r in rani_rules.items():
    title = clean(r.get("title","")) or f"Rule {no}"
    topic = clean(r.get("topic",""))
    concept = clean(r.get("concept",""))
    lines.append(f"## Rule {no}: {title}\n")
    if topic: lines.append(f"**Topic:** {topic}\n")
    lines.append(f"\n{concept}\n")
    exs = rani_examples(r["source_rule_id"])
    if exs:
        lines.append("\n**Examples**\n")
        for sent, expl in exs:
            lines.append(f"- ✗ {sent}")
            if expl:
                lines.append(f"  - {expl}")
        lines.append("")
    lines.append("")
with open(os.path.join(OUT, "rani-maam-60-rules.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"rani: {len(rani_rules)} rules -> rani-maam-60-rules.md")

# ---- 2. AMAN 100 ----
lines = ["# Aman Sir — 100 Most Important Grammar Rules\n",
         "Source: *100 Most Important Grammar Rules* PDF by Aman Sir. ",
         "101 concepts (listed as ~100 rules). Original Hinglish explanations translated to clear English.\n",
         "---\n"]
for r in aman_src["rules"]:
    no = r.get("concept_no")
    title = clean(r.get("title","")) or f"Concept {no}"
    topic = clean(r.get("topic",""))
    concept = clean(r.get("concept",""))
    lines.append(f"## Rule {no}: {title}\n")
    if topic: lines.append(f"**Topic:** {topic}\n")
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
with open(os.path.join(OUT, "aman-sir-100-rules.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"aman: {len(aman_src['rules'])} rules -> aman-sir-100-rules.md")

# ---- 3. MANISHA 120 ----
lines = ["# Manisha Bansal — 120 Rules of Grammar\n",
         "Source: *120 Rules of Grammar* by Nimisha (Manisha) Bansal. ",
         "120 rules with explanations, usage notes, examples, and memory tricks.\n",
         "---\n"]
for r in manisha:
    no = r.get("num")
    title = clean(r.get("title","")) or f"Rule {no}"
    cat = clean(r.get("cat",""))
    explain = clean(r.get("explain",""))
    lines.append(f"## Rule {no}: {title}\n")
    if cat: lines.append(f"**Category:** {cat}\n")
    lines.append(f"\n{explain}\n")
    usage = r.get("usage") or []
    if usage:
        lines.append("\n**Usage**\n")
        for u in usage:
            term = clean(u.get("term",""))
            desc = clean(u.get("desc",""))
            lines.append(f"- **{term}** — {desc}")
        lines.append("")
    exs = r.get("examples") or []
    if exs:
        lines.append("\n**Examples**\n")
        for ex in exs:
            ex = clean(ex)
            if ex.startswith("✓"):
                lines.append(f"- {ex}")
            elif ex.startswith("✗"):
                lines.append(f"- {ex}")
            else:
                lines.append(f"- {ex}")
        lines.append("")
    trick = clean(r.get("trick",""))
    if trick:
        lines.append(f"**Trick:** {trick}\n")
    lines.append("")
with open(os.path.join(OUT, "manisha-bansal-120-rules.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"manisha: {len(manisha)} rules -> manisha-bansal-120-rules.md")

# ---- 4. COMBINED MERGED ----
# 167 merged rules (Rani order + Aman/Manisha/Rahul extras), deduped, better wording.
lines = ["# Combined Grammar Rules — Merged from 3 Sources\n",
         "A single deduplicated list following **Rani Ma'am's 60-rule order** as the backbone, ",
         "with matching rules from **Aman Sir (100)** and **Manisha Bansal (120)** merged in ",
         "(concepts rewritten to combine the best of each), then extra rules from Aman/Manisha ",
         "appended after rule 60. No rule is repeated; where two sources cover the same concept, ",
         "the explanations are merged into one clearer version.\n",
         f"**Total: {len(merged)} rules** (60 backbone + {len(merged)-60} extra)\n",
         "---\n"]
for r in merged:
    no = r.get("no")
    title = clean(r.get("title","")) or f"Rule {no}"
    topic = clean(r.get("topic",""))
    concept = clean(r.get("concept",""))
    sources = r.get("sources") or []
    lines.append(f"## Rule {no}: {title}\n")
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
with open(os.path.join(OUT, "combined-grammar-rules.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"combined: {len(merged)} rules -> combined-grammar-rules.md")
print("\nDONE — 4 markdown files in docs/rules/")
