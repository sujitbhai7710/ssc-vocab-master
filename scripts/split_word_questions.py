#!/usr/bin/env python3
"""Speed optimization: split the huge questions.json (2.45MB) into per-letter
word-question files so word expansions load ~100KB (cached) instead of 2.9MB.

Outputs:
  public/data/wq/<letter>.json   = { wordLower: { asStem:[QuestionEntry...], asOption:[...] } }
Also:
  public/data/top_words.json     = top 10 stem + top 10 option words (for dashboard)
Deletes (unused) public/data/enriched.json master (12.7MB) to shrink deploy.
"""
import os, json
from collections import defaultdict

PUB = "/home/z/my-project/ssc-vocab-master/public/data"
WQDIR = os.path.join(PUB, "wq")
os.makedirs(WQDIR, exist_ok=True)

questions = json.load(open(os.path.join(PUB, "questions.json"), encoding="utf-8"))
word_questions = json.load(open(os.path.join(PUB, "word_questions.json"), encoding="utf-8"))

# Build per-letter grouped word→questions
by_letter = defaultdict(dict)
for wordLower, wq in word_questions.items():
    letter = (wordLower[0] or "_").lower()
    entry = {
        "asStem": [questions[i] for i in wq.get("asStem", []) if i < len(questions)],
        "asOption": [questions[i] for i in wq.get("asOption", []) if i < len(questions)],
    }
    by_letter[letter][wordLower] = entry

total_size = 0
for letter, data in by_letter.items():
    p = os.path.join(WQDIR, f"{letter}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    total_size += os.path.getsize(p)
print(f"wq/: {len(by_letter)} letter files, total {total_size/1024:.0f} KB")

# index: which letters exist
with open(os.path.join(WQDIR, "index.json"), "w", encoding="utf-8") as f:
    json.dump(sorted(by_letter.keys()), f)

# top words for dashboard (avoid loading 2.2MB words.json on home)
words = json.load(open(os.path.join(PUB, "words.json"), encoding="utf-8"))
top_stems = sorted([w for w in words if w["asStem"] > 0], key=lambda w: w["asStem"], reverse=True)[:10]
top_options = sorted([w for w in words if (w.get("qtypesAsOption", {}).get("synonym", 0) + w.get("qtypesAsOption", {}).get("antonym", 0)) > 0],
                     key=lambda w: w.get("qtypesAsOption", {}).get("synonym", 0) + w.get("qtypesAsOption", {}).get("antonym", 0), reverse=True)[:10]
with open(os.path.join(PUB, "top_words.json"), "w", encoding="utf-8") as f:
    json.dump({"topStems": top_stems, "topOptions": top_options}, f, ensure_ascii=False)
print(f"top_words.json: {os.path.getsize(os.path.join(PUB,'top_words.json'))/1024:.1f} KB")

# delete unused 12.7MB master enriched.json (per-letter files are what's actually loaded)
master = os.path.join(PUB, "enriched.json")
if os.path.exists(master):
    sz = os.path.getsize(master)
    os.remove(master)
    print(f"deleted enriched.json master ({sz/1024/1024:.1f} MB) — unused, per-letter files are used instead")
print("DONE")
