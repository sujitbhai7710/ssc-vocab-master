#!/usr/bin/env python3
"""Detect duplicate rules deterministically (no AI needed).

Method:
1. Exact title match (case-insensitive, punctuation-normalized).
2. Title-keyword containment: rule A title's significant words ⊂ rule B title
   (e.g. "Each vs Every" ⊂ "Each/Every/Either/Neither").
3. Concept Jaccard similarity on significant words (threshold 0.55) — catches
   different titles explaining the same concept.

Prints all duplicate groups. Pure Python, no external API.
"""
import json, re, os
from collections import defaultdict

PUB = "/home/z/my-project/ssc-vocab-master/public/data/grammar"
rules = json.load(open(os.path.join(PUB, "rules.json"), encoding="utf-8"))

STOP = set("""a an the of to in on at for and or nor but if as is are was were be been being
with without by from into onto upon over under between among vs versus use using
rule rules grammar example examples correct incorrect""".split())

def norm_title(t):
    t = t.lower()
    t = re.sub(r'[^a-z0-9 ]', ' ', t)
    return t

def sig_words(s, min_len=2):
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    ws = [w for w in s.split() if w not in STOP and len(w) >= min_len]
    return ws

def sig_set(s):
    return set(sig_words(s))

# Build per-rule signature = title sig words + concept sig words (weighted: title counted twice)
sigs = []
for r in rules:
    tw = sig_words(r['title'])
    cw = sig_words(r.get('concept',''))
    # union, but track title words separately for containment test
    sigs.append({
        'no': r['no'], 'title': r['title'], 'topic': r.get('topic',''),
        'title_words': set(tw), 'concept_words': set(cw),
        'all_words': set(tw) | set(cw),
    })

def jaccard(a, b):
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

groups = defaultdict(set)
n = len(sigs)
for i in range(n):
    a = sigs[i]
    for j in range(i+1, n):
        b = sigs[j]
        # 1. exact normalized title
        same_title = norm_title(a['title']) == norm_title(b['title'])
        # 2. title keyword containment (one title's sig words subset of other's)
        twa, twb = a['title_words'], b['title_words']
        contain = (twa and twa.issubset(twb)) or (twb and twb.issubset(twa))
        # 3. concept similarity (Jaccard on concept words, excluding the shared title words)
        ca = a['concept_words'] - twa
        cb = b['concept_words'] - twb
        concept_sim = jaccard(ca, cb)
        # 4. overall similarity (title overlap strongly counts)
        title_sim = jaccard(twa, twb)
        if same_title or (contain and title_sim >= 0.34) or (concept_sim >= 0.55) or (title_sim >= 0.6):
            groups[a['no']].add(b['no'])
            groups[b['no']].add(a['no'])

# union-find to merge overlapping pairs into groups
parent = {r['no']: r['no'] for r in rules}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb: parent[ra] = rb
for a, bs in groups.items():
    for b in bs:
        union(a, b)
clusters = defaultdict(list)
for no in parent:
    clusters[find(no)].append(no)

dup_clusters = {k:sorted(v) for k,v in clusters.items() if len(v) > 1}
print(f"=== {len(dup_clusters)} duplicate clusters found ===\n")
by_no = {r['no']: r for r in rules}
for k, nos in sorted(dup_clusters.items(), key=lambda x: x[1][0]):
    print(f"CLUSTER {nos}:")
    for n in nos:
        r = by_no[n]
        print(f"  - #{n} [{r.get('topic','')}] {r['title']}")
        print(f"      {r.get('concept','')[:120]}")
    print()
