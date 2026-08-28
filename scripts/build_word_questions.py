#!/usr/bin/env python3
"""
Precompute word -> questions mapping (which questions this word appeared in, as stem vs option).
Also build a smaller "summary" view for each word for the listing pages.
"""

import json
import os
from collections import defaultdict

WORDS_FILE = "/home/z/my-project/src/data/words.json"
QUESTIONS_FILE = "/home/z/my-project/src/data/questions.json"
OUTPUT_DIR = "/home/z/my-project/src/data"

with open(WORDS_FILE) as f:
    words = json.load(f)
with open(QUESTIONS_FILE) as f:
    questions = json.load(f)

# Build: word -> { asStem: [qids], asOption: [qids] }
word_qids = defaultdict(lambda: {"asStem": [], "asOption": []})

# Build an index: wordLower -> qids where it appears
# We need to also build a stem-key for each question
for q in questions:
    qid = q["id"]
    qtype = q["qtype"]
    if qtype in ("synonym", "antonym"):
        stem = q["stem"].strip().lower()
        if stem:
            word_qids[stem]["asStem"].append(qid)
    # options
    for opt in q["options"]:
        opt_low = opt.strip().lower()
        # Only single-word options
        if " " not in opt_low and len(opt_low) > 1:
            word_qids[opt_low]["asOption"].append(qid)

# For each word in words.json, attach the question IDs
word_questions = {}
for w in words:
    wl = w["wordLower"]
    if wl in word_qids:
        word_questions[wl] = word_qids[wl]
    else:
        word_questions[wl] = {"asStem": [], "asOption": []}

with open(os.path.join(OUTPUT_DIR, "word_questions.json"), "w", encoding="utf-8") as f:
    json.dump(word_questions, f, ensure_ascii=False)

print(f"Wrote word_questions.json ({len(word_questions)} words mapped)")

# Stats
print(f"Words with at least 1 stem question: {sum(1 for v in word_questions.values() if v['asStem'])}")
print(f"Words with at least 1 option question: {sum(1 for v in word_questions.values() if v['asOption'])}")
print(f"Words with no question mapping (orphan): {sum(1 for v in word_questions.values() if not v['asStem'] and not v['asOption'])}")
