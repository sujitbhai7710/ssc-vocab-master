#!/usr/bin/env python3
"""
SSC vocabulary parser v4 — uses Satwik's repo for accuracy.

Strategy:
1. Use Satwik's questions.json (sa, idioms, ows, spelling, homonyms) for:
   - Real correct answers (`ans` field) — overrides WordNet best-guess
   - Question stem extraction (`main` field — the actual idiom phrase or correct word)
   - Explanations (`expl` field)
   - Exam/year metadata
2. Use Satwik's vocab.json files for word-level info:
   - Definitions, parts of speech
   - Bengali meanings (extra)
   - Mnemonics / tricks to remember
   - Root words + families
   - Per-word question counts (with role main/opt + correct flag)
3. Use Satwik's roots.json for the new Root Words page

Key fixes vs v3:
- Idiom vocab words = the idiom PHRASE (e.g. "By and by"), NOT the meaning-options
- Spelling vocab words = the correct spelling (e.g. "accommodation"), NOT "no error"
- OWS vocab words = the correct one-word answer (e.g. "barrel"), NOT the description
- Homonym vocab words = the correct homonym (e.g. "add")
- Module 2 — Option Choices restricted to syn/ant only

Two-color scheme (per user request):
- Green  = correct answer (the word WAS asked as a synonym/antonym for this word)
- Gray   = added by me from WordNet (did NOT appear in SSC)
- (Remove red "distractor" — too noisy)

Outputs (under public/data/):
  - questions.json (with REAL correct answers)
  - words.json (per-word frequency + per-qtype breakdown)
  - word_questions.json
  - ssc_relations.json (correct / added only)
  - summary.json
  - roots.json (1600+ root families for new Root Words page)
  - words/[letter].json (Bengali + mnemonics + roots, per letter)
"""

import os, re, json, glob
from collections import defaultdict, Counter

SATWIK_DIR = "/home/z/my-project/ssc-question-bank/frontend/static/data"
OUTPUT_DIR = "/home/z/my-project/ssc-vocab-astro/public/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "enriched"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "words"), exist_ok=True)

# ─── Load Satwik data ───────────────────────────────────────────────────────
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

print("Loading Satwik data...")
satwik_sa_q = load_json(f"{SATWIK_DIR}/sa/questions.json")
satwik_idiom_q = load_json(f"{SATWIK_DIR}/idioms/questions.json")
satwik_ows_q = load_json(f"{SATWIK_DIR}/ows/questions.json")
satwik_spelling_q = load_json(f"{SATWIK_DIR}/spelling/questions.json")
satwik_homonym_q = load_json(f"{SATWIK_DIR}/homonyms/questions.json")
satwik_sa_vocab = load_json(f"{SATWIK_DIR}/sa/vocab.json")
satwik_idiom_vocab = load_json(f"{SATWIK_DIR}/idioms/vocab.json")
satwik_ows_vocab = load_json(f"{SATWIK_DIR}/ows/vocab.json")
satwik_spelling_vocab = load_json(f"{SATWIK_DIR}/spelling/vocab.json")
satwik_homonym_vocab = load_json(f"{SATWIK_DIR}/homonyms/vocab.json")
satwik_roots = load_json(f"{SATWIK_DIR}/roots.json")

# Satwik words/ per-letter (for Bengali + mnemonics)
satwik_words_by_letter = {}
for letter in "abcdefghijklmnopqrstuvwxyz":
    p = f"{SATWIK_DIR}/words/{letter}.json"
    if os.path.exists(p):
        try:
            satwik_words_by_letter[letter] = load_json(p)
        except Exception as e:
            print(f"Failed to load words/{letter}.json: {e}")
            satwik_words_by_letter[letter] = {}

print(f"  SA questions:     {len(satwik_sa_q)}")
print(f"  Idiom questions:  {len(satwik_idiom_q)}")
print(f"  OWS questions:    {len(satwik_ows_q)}")
print(f"  Spelling Qs:      {len(satwik_spelling_q)}")
print(f"  Homonym Qs:       {len(satwik_homonym_q)}")
print(f"  SA vocab words:   {len(satwik_sa_vocab)}")
print(f"  Idiom vocab:      {len(satwik_idiom_vocab)}")
print(f"  OWS vocab:        {len(satwik_ows_vocab)}")
print(f"  Spelling vocab:   {len(satwik_spelling_vocab)}")
print(f"  Homonym vocab:    {len(satwik_homonym_vocab)}")
print(f"  Root families:    {len(satwik_roots)}")
print(f"  Word letter files: {len(satwik_words_by_letter)}")

# ─── Build unified questions list ──────────────────────────────────────────
# Each question gets a unified schema:
#   id, exam, year, qno (or satwik_id), qtype, stem, options, correctIdx, expl
all_questions = []

def normalize_qtype(t):
    return t

def add_satwik_questions(qs, qtype):
    out = []
    for q in qs:
        # `main` is the word/idiom/phrase; for syn/ant it's the stem word
        stem = q.get("main") or q.get("text") or q.get("sent") or ""
        opts = q.get("opts") or []
        ans = q.get("ans", -1)
        if ans is None:
            ans = -1
        out.append({
            "id": None,  # assigned later
            "exam": (q.get("exam") or "").strip(),
            "year": (q.get("year") or "").strip(),
            "satwik_id": q.get("id"),
            "qtype": qtype,
            "prompt": q.get("prompt") or "",
            "stem": stem,
            "options": opts,
            "correctIdx": ans,
            "expl": q.get("expl") or "",
            "src": q.get("src") or "",
        })
    return out

sa_qs = add_satwik_questions(satwik_sa_q, "synonym-antonym")  # mixed; will split later
idiom_qs = add_satwik_questions(satwik_idiom_q, "idiom")
ows_qs = add_satwik_questions(satwik_ows_q, "one-word")
spelling_qs = add_satwik_questions(satwik_spelling_q, "spelling")
homonym_qs = add_satwik_questions(satwik_homonym_q, "homonym")

# Satwik SA questions have a "dir" field: "SYN" or "ANT" — split them
for q in sa_qs:
    dir_val = (satwik_sa_q[q["satwik_id"]].get("dir") or "").upper() if q["satwik_id"] is not None else ""
    if "ANT" in dir_val:
        q["qtype"] = "antonym"
    else:
        q["qtype"] = "synonym"

all_questions = sa_qs + idiom_qs + ows_qs + spelling_qs + homonym_qs
# Assign sequential IDs
for i, q in enumerate(all_questions):
    q["id"] = i

print(f"\nTotal questions: {len(all_questions)}")
by_type = Counter(q["qtype"] for q in all_questions)
for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
    print(f"  {t:20s} {c:5d}")

# ─── Build word frequency index ─────────────────────────────────────────────
"""
Word frequency index rules (per user request):

For Synonym + Antonym (combined into a single category "syn-ant"):
  - Stem: the word being asked (this is the "main question" appearance)
  - Options: each of the 4 options is a vocab word (synonym or antonym of the stem)
  - These go into Module 1 (Stems) and Module 2 (Options)

For Idiom:
  - The "word" = the idiom phrase itself (e.g. "By and by", "square peg in a round hole")
  - The options are MEANINGS (not vocab) — so we do NOT add them as vocab
  - Goes into Module 4 (Idioms) only

For OWS:
  - The "word" = the correct one-word answer (e.g. "barrel", "philanthropist")
  - The other options are distractor words — still vocab but only counted as options
  - Goes into Module 3 (OWS) — sorted by appearance count

For Homonym:
  - The "word" = the correct homonym (e.g. "add")
  - The other options are distractor homophones — still vocab
  - Goes into Module 5 (Homonyms)

For Spelling:
  - The "word" = the correctly-spelt option (e.g. "accommodation")
  - The misspelt options are NOT real words — exclude them
  - Goes into Module 6 (Spelling)
"""

words_db = defaultdict(lambda: {
    "word": "",
    "asStem": 0,
    "asOption": 0,
    "stemExams": [],
    "optionExams": [],
    "qtypesAsStem": defaultdict(int),
    "qtypesAsOption": defaultdict(int),
    "questionIds": {"asStem": [], "asOption": []},
    "correctAsStem": 0,    # times as stem AND there was a correct answer
    "correctAsOption": 0,  # times as option AND this was the correct answer
})

# For idiom/ows/spelling/homonym: the "stem" is actually the WORD we want to track
# (since the actual stem is a phrase, and the "word" we want is the answer or the idiom)
# So we'll treat:
# - For syn/ant: stem = vocab word, options = vocab words (counted)
# - For idiom: stem = idiom phrase (vocab word), options = MEANINGS (NOT vocab)
# - For ows: stem = correct word (counted as "main"), options = distractor words (counted as options)
#            BUT for the WRONG options, they ARE still vocab — but the user said NOT to mix OWS
#            options into Module 2. So we count OWS options as qtypesAsOption['one-word'] but
#            the Module 2 page will only show syn/ant.

def add_word(word_low, word_display, as_stem=False, as_option=False, exam="", qtype="", qid=None, correct=False):
    if not word_low or len(word_low) < 2:
        return
    entry = words_db[word_low]
    if not entry["word"]:
        entry["word"] = word_display
    if as_stem:
        entry["asStem"] += 1
        entry["stemExams"].append(exam)
        entry["qtypesAsStem"][qtype] += 1
        if qid is not None:
            entry["questionIds"]["asStem"].append(qid)
        if correct:
            entry["correctAsStem"] += 1
    if as_option:
        entry["asOption"] += 1
        entry["optionExams"].append(exam)
        entry["qtypesAsOption"][qtype] += 1
        if qid is not None:
            entry["questionIds"]["asOption"].append(qid)
        if correct:
            entry["correctAsOption"] += 1

def norm_lower(s):
    return s.strip().strip(".,;:!?\"'()[]{}").strip().lower()

def norm_display(s):
    s = s.strip().strip(".,;:!?\"'()[]{}").strip()
    if not s:
        return ""
    return s[0].upper() + s[1:]

for q in all_questions:
    qtype = q["qtype"]
    exam = q["exam"]
    qid = q["id"]
    correct_idx = q.get("correctIdx", -1)
    opts = q["options"]
    stem = q["stem"]

    if qtype in ("synonym", "antonym"):
        # Stem is the vocab word being asked
        stem_low = norm_lower(stem)
        if stem_low and len(stem_low.split()) <= 3:
            add_word(stem_low, norm_display(stem), as_stem=True, exam=exam, qtype=qtype, qid=qid, correct=True)
        # Each option is a vocab word (synonym or antonym of stem)
        for i, opt in enumerate(opts):
            opt_low = norm_lower(opt)
            if not opt_low or len(opt_low.split()) > 3:
                continue
            is_correct = (i == correct_idx)
            add_word(opt_low, norm_display(opt), as_option=True, exam=exam, qtype=qtype, qid=qid, correct=is_correct)

    elif qtype == "idiom":
        # The IDIOM PHRASE is the vocab word (not the options which are meanings)
        idiom_low = norm_lower(stem)
        if idiom_low and 2 <= len(idiom_low.split()) <= 8:
            # Use the idiom phrase as the "word"
            # We capitalize first letter, keep rest
            disp = norm_display(stem)
            add_word(idiom_low, disp, as_stem=True, exam=exam, qtype="idiom", qid=qid, correct=True)
        # DO NOT add options as vocab — they are MEANINGS, not words

    elif qtype == "one-word":
        # The correct answer IS the vocab word we want
        # The distractor options are also words, but we still count them (they appeared in OWS)
        if 0 <= correct_idx < len(opts):
            correct_word = opts[correct_idx]
            wlow = norm_lower(correct_word)
            if wlow and len(wlow.split()) <= 3:
                add_word(wlow, norm_display(correct_word), as_stem=True, exam=exam, qtype="one-word", qid=qid, correct=True)
        # The distractor options also count (but as options)
        for i, opt in enumerate(opts):
            if i == correct_idx:
                continue
            opt_low = norm_lower(opt)
            if not opt_low or len(opt_low.split()) > 3:
                continue
            add_word(opt_low, norm_display(opt), as_option=True, exam=exam, qtype="one-word", qid=qid, correct=False)

    elif qtype == "homonym":
        # Same as OWS — correct answer is the vocab word
        if 0 <= correct_idx < len(opts):
            correct_word = opts[correct_idx]
            wlow = norm_lower(correct_word)
            if wlow and len(wlow.split()) <= 3:
                add_word(wlow, norm_display(correct_word), as_stem=True, exam=exam, qtype="homonym", qid=qid, correct=True)
        for i, opt in enumerate(opts):
            if i == correct_idx:
                continue
            opt_low = norm_lower(opt)
            if not opt_low or len(opt_low.split()) > 3:
                continue
            add_word(opt_low, norm_display(opt), as_option=True, exam=exam, qtype="homonym", qid=qid, correct=False)

    elif qtype == "spelling":
        # Only the correct spelling is a real vocab word — misspelt options are NOT real words
        if 0 <= correct_idx < len(opts):
            correct_word = opts[correct_idx]
            wlow = norm_lower(correct_word)
            # Exclude "no error" type answers
            if wlow and "no error" not in wlow and "none" not in wlow and len(wlow.split()) <= 3:
                add_word(wlow, norm_display(correct_word), as_stem=True, exam=exam, qtype="spelling", qid=qid, correct=True)
        # Skip the misspelt options — they're not real vocab

# ─── Build the per-word stats ──────────────────────────────────────────────
print(f"\nUnique vocab words: {len(words_db)}")

# Sort by total freq desc, then alphabetical
sorted_words = sorted(words_db.items(),
                      key=lambda kv: (- (kv[1]["asStem"] + kv[1]["asOption"]), kv[0]))

words_out = []
for word_low, v in sorted_words:
    words_out.append({
        "word": v["word"],
        "wordLower": word_low,
        "asStem": v["asStem"],
        "asOption": v["asOption"],
        "total": v["asStem"] + v["asOption"],
        "stemExams": sorted(set(v["stemExams"])),
        "optionExams": sorted(set(v["optionExams"])),
        "qtypesAsStem": dict(v["qtypesAsStem"]),
        "qtypesAsOption": dict(v["qtypesAsOption"]),
        "correctAsStem": v["correctAsStem"],
        "correctAsOption": v["correctAsOption"],
    })

# ─── Build word → questions map ────────────────────────────────────────────
word_questions = {w["wordLower"]: words_db[w["wordLower"]]["questionIds"] for w in words_out}

# ─── Compute SSC relations (only TWO colors: correct + added) ─────────────
# Per user: only green (correct) + gray (added by me from WordNet). Remove red (distractor).
# We use Satwik's vocab.json syn/ant fields directly — these are the "real" SSC synonyms/antonyms.
synonyms_map = defaultdict(set)   # word → set of correct synonyms (from SSC)
antonyms_map = defaultdict(set)   # word → set of correct antonyms (from SSC)

# From sa_vocab — each entry has `syn` and `ant` arrays
for entry in satwik_sa_vocab:
    w = norm_lower(entry.get("w", ""))
    if not w:
        continue
    for syn in entry.get("syn") or []:
        syn_low = norm_lower(syn)
        if syn_low and syn_low != w:
            synonyms_map[w].add(syn_low)
            synonyms_map[syn_low].add(w)  # symmetric
    for ant in entry.get("ant") or []:
        ant_low = norm_lower(ant)
        if ant_low and ant_low != w:
            antonyms_map[w].add(ant_low)
            antonyms_map[ant_low].add(w)  # symmetric

# Also infer from each SA question: stem + correct answer are synonyms/antonyms
for q in all_questions:
    if q["qtype"] not in ("synonym", "antonym"):
        continue
    stem_low = norm_lower(q["stem"])
    correct_idx = q.get("correctIdx", -1)
    if not stem_low or correct_idx < 0 or correct_idx >= len(q["options"]):
        continue
    correct_opt = norm_lower(q["options"][correct_idx])
    if not correct_opt or correct_opt == stem_low:
        continue
    if q["qtype"] == "synonym":
        synonyms_map[stem_low].add(correct_opt)
        synonyms_map[correct_opt].add(stem_low)
    else:
        antonyms_map[stem_low].add(correct_opt)
        antonyms_map[correct_opt].add(stem_low)

ssc_relations = {
    "synonyms": {k: list(v) for k, v in synonyms_map.items()},
    "antonyms": {k: list(v) for k, v in antonyms_map.items()},
}

# ─── Build per-word enriched entries ──────────────────────────────────────
# Combine MY word stats with Satwik's per-word info (definition, Bengali, mnemonic, root, etc.)

# Build satwik vocab lookup by word (across all question types)
satwik_word_info = {}  # word_lower → info dict

# sa vocab
for entry in satwik_sa_vocab:
    wlow = norm_lower(entry.get("w", ""))
    if not wlow:
        continue
    satwik_word_info[wlow] = {
        "pos": entry.get("pos", ""),
        "definition": entry.get("mean", ""),
        "bn": entry.get("bn", ""),
        "ex": entry.get("ex", ""),
        "root": entry.get("root", ""),
        "rootMeaning": entry.get("rm", ""),
        "rootBn": entry.get("rbn", ""),
        "mnemonic": entry.get("mn", ""),
        "syn": entry.get("syn") or [],
        "ant": entry.get("ant") or [],
    }

# Other vocab types
for vocab, qtype in [
    (satwik_idiom_vocab, "idiom"),
    (satwik_ows_vocab, "one-word"),
    (satwik_spelling_vocab, "spelling"),
    (satwik_homonym_vocab, "homonym"),
]:
    for entry in vocab:
        wlow = norm_lower(entry.get("w", ""))
        if not wlow:
            continue
        if wlow not in satwik_word_info:
            satwik_word_info[wlow] = {
                "pos": entry.get("pos", ""),
                "definition": entry.get("mean", ""),
                "bn": entry.get("bn", ""),
                "ex": entry.get("ex", ""),
                "root": entry.get("root", ""),
                "rootMeaning": entry.get("rm", ""),
                "rootBn": entry.get("rbn", ""),
                "mnemonic": entry.get("mn", ""),
                "syn": [],
                "ant": [],
            }
        else:
            # Merge in missing fields
            for k, v in [
                ("pos", entry.get("pos", "")),
                ("definition", entry.get("mean", "")),
                ("bn", entry.get("bn", "")),
                ("ex", entry.get("ex", "")),
                ("root", entry.get("root", "")),
                ("rootMeaning", entry.get("rm", "")),
                ("rootBn", entry.get("rbn", "")),
                ("mnemonic", entry.get("mn", "")),
            ]:
                if not satwik_word_info[wlow].get(k) and v:
                    satwik_word_info[wlow][k] = v

# Also from words/<letter>.json (rich data: definitions, Bengali, mnemonics, roots)
for letter, words_data in satwik_words_by_letter.items():
    if not isinstance(words_data, dict):
        continue
    for wlow, info in words_data.items():
        wlow = norm_lower(wlow)
        if not wlow:
            continue
        if wlow not in satwik_word_info:
            satwik_word_info[wlow] = {
                "pos": info.get("pos", ""),
                "definition": info.get("mean", ""),
                "bn": info.get("bn", ""),
                "ex": info.get("ex", ""),
                "root": info.get("root", ""),
                "rootMeaning": info.get("rm", ""),
                "rootBn": info.get("rbn", ""),
                "mnemonic": info.get("mn", ""),
                "syn": [],
                "ant": [],
            }
        else:
            for k, v in [
                ("pos", info.get("pos", "")),
                ("definition", info.get("mean", "")),
                ("bn", info.get("bn", "")),
                ("ex", info.get("ex", "")),
                ("root", info.get("root", "")),
                ("rootMeaning", info.get("rm", "")),
                ("rootBn", info.get("rbn", "")),
                ("mnemonic", info.get("mn", "")),
            ]:
                if not satwik_word_info[wlow].get(k) and v:
                    satwik_word_info[wlow][k] = v

print(f"Satwik word info entries: {len(satwik_word_info)}")

# Build enriched entries
enriched = {}
no_def = 0
has_bn = 0
has_mn = 0
has_root = 0
for w_low, v in words_db.items():
    info = satwik_word_info.get(w_low, {})
    if not info.get("definition"):
        no_def += 1
    if info.get("bn"):
        has_bn += 1
    if info.get("mnemonic"):
        has_mn += 1
    if info.get("root"):
        has_root += 1

    # Synonyms/antonyms: TWO colors only
    # - 'correct' = appeared as a real SSC synonym/antonym for this word (GREEN)
    # - 'added'   = added by me from WordNet (we don't have WordNet here anymore, so just empty)
    ss_syn = []
    seen_syn = set()
    for s in synonyms_map.get(w_low, []):
        if s and s != w_low and s not in seen_syn:
            ss_syn.append({"word": s.capitalize(), "status": "correct"})
            seen_syn.add(s)
    # Also from satwik word_info.syn
    for s in info.get("syn", []):
        s_low = norm_lower(s)
        if s_low and s_low != w_low and s_low not in seen_syn:
            ss_syn.append({"word": s.capitalize(), "status": "correct"})
            seen_syn.add(s_low)
    ss_syn = ss_syn[:12]

    ss_ant = []
    seen_ant = set()
    for a in antonyms_map.get(w_low, []):
        if a and a != w_low and a not in seen_ant:
            ss_ant.append({"word": a.capitalize(), "status": "correct"})
            seen_ant.add(a)
    for a in info.get("ant", []):
        a_low = norm_lower(a)
        if a_low and a_low != w_low and a_low not in seen_ant:
            ss_ant.append({"word": a.capitalize(), "status": "correct"})
            seen_ant.add(a_low)
    ss_ant = ss_ant[:12]

    enriched[w_low] = {
        "word": v["word"],
        "wordLower": w_low,
        "definition": info.get("definition", ""),
        "pos": info.get("pos", ""),
        "bn": info.get("bn", ""),
        "ex": info.get("ex", ""),
        "mnemonic": info.get("mnemonic", ""),
        "root": info.get("root", ""),
        "rootMeaning": info.get("rootMeaning", ""),
        "rootBn": info.get("rootBn", ""),
        "ssSynonyms": ss_syn,
        "ssAntonyms": ss_ant,
    }

print(f"\nEnriched stats:")
print(f"  No definition:  {no_def}")
print(f"  Has Bengali:    {has_bn}")
print(f"  Has mnemonic:   {has_mn}")
print(f"  Has root word:  {has_root}")

# Split enriched per letter
out_dir = os.path.join(OUTPUT_DIR, "enriched")
os.makedirs(out_dir, exist_ok=True)
# Clear old
for f in glob.glob(os.path.join(out_dir, "enriched_*.json")):
    os.remove(f)

buckets = defaultdict(dict)
for w_low, entry in enriched.items():
    letter = w_low[0] if w_low else "_"
    buckets[letter][w_low] = entry
for letter, entries in buckets.items():
    with open(os.path.join(out_dir, f"enriched_{letter}.json"), "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)
print(f"\nWrote {len(buckets)} enriched_<letter>.json files")

# ─── Write all output files ────────────────────────────────────────────────
with open(os.path.join(OUTPUT_DIR, "words.json"), "w", encoding="utf-8") as f:
    json.dump(words_out, f, ensure_ascii=False, indent=2)
print(f"Wrote words.json ({len(words_out)} words)")

with open(os.path.join(OUTPUT_DIR, "questions.json"), "w", encoding="utf-8") as f:
    # Strip None fields
    qs_out = []
    for q in all_questions:
        qo = {k: v for k, v in q.items() if v is not None}
        qs_out.append(qo)
    json.dump(qs_out, f, ensure_ascii=False, indent=2)
print(f"Wrote questions.json ({len(qs_out)} questions)")

with open(os.path.join(OUTPUT_DIR, "word_questions.json"), "w", encoding="utf-8") as f:
    json.dump(word_questions, f, ensure_ascii=False)
print(f"Wrote word_questions.json ({len(word_questions)} words)")

with open(os.path.join(OUTPUT_DIR, "ssc_relations.json"), "w", encoding="utf-8") as f:
    json.dump(ssc_relations, f, ensure_ascii=False)
print(f"Wrote ssc_relations.json")

# Roots data — for the new Root Words page
with open(os.path.join(OUTPUT_DIR, "roots.json"), "w", encoding="utf-8") as f:
    json.dump(satwik_roots, f, ensure_ascii=False)
print(f"Wrote roots.json ({len(satwik_roots)} root families)")

# Per-letter word data (Bengali, mnemonics, etc.) — for word detail pages
words_dir = os.path.join(OUTPUT_DIR, "words")
os.makedirs(words_dir, exist_ok=True)
# Clear old
for f in glob.glob(os.path.join(words_dir, "*.json")):
    os.remove(f)
for letter, data in satwik_words_by_letter.items():
    with open(os.path.join(words_dir, f"{letter}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
print(f"Wrote {len(satwik_words_by_letter)} words/<letter>.json files")

# Summary
summary = {
    "totalFiles": 23,
    "totalQuestions": len(all_questions),
    "byType": dict(by_type),
    "totalSynonym": by_type["synonym"],
    "totalAntonym": by_type["antonym"],
    "totalSynonymAntonym": by_type["synonym"] + by_type["antonym"],
    "totalOneWord": by_type["one-word"],
    "totalIdioms": by_type["idiom"],
    "totalHomonyms": by_type["homonym"],
    "totalSpelling": by_type["spelling"],
    "totalUniqueWords": len(words_db),
    "totalRoots": len(satwik_roots),
}
with open(os.path.join(OUTPUT_DIR, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"Wrote summary.json")

# Print top 20
print("\nTop 20 words (by total frequency):")
for w in words_out[:20]:
    types_s = [f"{t}:{c}" for t, c in w["qtypesAsStem"].items() if c > 0]
    types_o = [f"{t}:{c}" for t, c in w["qtypesAsOption"].items() if c > 0]
    print(f"  {w['word']:25s}  stem={w['asStem']:3d} ({', '.join(types_s) or '-'})  opt={w['asOption']:3d} ({', '.join(types_o) or '-'})  total={w['total']:3d}")
