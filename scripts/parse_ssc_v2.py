#!/usr/bin/env python3
"""
Comprehensive SSC vocabulary parser.

Extracts ALL vocabulary-related question types:
  - synonym
  - antonym
  - one-word substitution (ows)
  - idiom
  - homonym / homophone
  - spelling

For each question we also compute a best-guess "correct answer" using
WordNet similarity (so we can color-code synonyms/antonyms later).

Outputs (under src/data/):
  - questions.json     — full list of all parsed questions
  - words.json         — vocabulary frequency index (as stem / as option)
  - word_questions.json — word → [question IDs] map
  - summary.json       — overview stats
"""

import os
import re
import json
import glob
from collections import defaultdict
import nltk

nltk.data.path.append('/home/z/nltk_data')
from nltk.corpus import wordnet

SSC_DIR = "/home/z/my-project/ssc-txt"
OUTPUT_DIR = "/home/z/my-project/ssc-vocab-astro/public/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "enriched"), exist_ok=True)

# ─── Question type detectors ────────────────────────────────────────────────
SYNONYM_PATTERNS = [
    r"synonym of the given word",
    r"synonyms? of the",
    r"word which is most similar in meaning",
    r"same in meaning",
    r"similar in meaning",
    r"most nearly the same in meaning",
    r"most nearly the same as",
    r"synonym of the underlined",
    r"synonym of the underlined word",
    r"synonym of the bold",
    r"synonym of the word in bold",
    r"synonym of the highlighted",
    r"synonym of the bracketed",
    r"synonym to replace the italicised",
    r"meaning of the given word",  # sometimes used for synonym
    r"meaning of the underlined word",
    r"meaning of the underlined word in a sentence",
    r"similar in meaning to the given word",
    r"select the most appropriate meaning of the given word",
]
ANTONYM_PATTERNS = [
    r"antonym of the given word",
    r"antonyms? of the",
    r"opposite in meaning",
    r"opposite of the",
    r"word which is most opposite in meaning",
    r"most nearly opposite in meaning",
    r"most nearly opposite to",
    r"antonym of the underlined",
    r"antonym of the bold",
    r"antonym of the highlighted",
    r"antonym of the bracketed",
    r"opposite of the given word",
]
ONEWORD_PATTERNS = [
    r"one[- ]word substitution",
    r"one word substitution",
    r"word that can be used as a substitute",
    r"option that can be used as a one[- ]word substitute",
    r"word which means the same as the group of words",
    r"word which means the same as the given group",
    r"select the word which means the same as the group of words",
    r"single word for the expression given below",
    r"word for the given group of words",
    r"most appropriate word for the given group of words",
    r"option that can be used as a substitute for the given group of words",
]
IDIOM_PATTERNS = [
    r"meaning of the given idiom",
    r"meaning of the underlined idiom",
    r"meaning of the highlighted idiom",
    r"meaning of the following idiom",
    r"meaning of the idiom from the options",
    r"meaning of the given idiom in the given sentence",
    r"meaning of the underlined phrase",
    r"meaning of the given phrase",
    r"idiom to fill in the blank",
    r"idiom to fill the blank",
    r"idiom for the given situation",
    r"idiom for the following sentence",
    r"idiom for the following statement",
    r"idiom from the given options",
    r"idiom that can substitute",
    r"idiomatic expression to fill",
    r"complete the given idiom",
    r"select the most appropriate idiom",
    r"select the most appropriate meaning of the given idiom",
    r"select the most appropriate meaning of the underlined idiom",
]
HOMONYM_PATTERNS = [
    r"most appropriate homophone to fill",
    r"most appropriate homophones to fill",
    r"most appropriate homonym to fill",
]
SPELLING_PATTERNS = [
    r"misspelt word",
    r"incorrectly spelt word",
    r"correctly spelt word",
    r"spelling error",
    r"contains a spelling error",
    r"correctly spelt",
    r"misspelt",
    r"correctly spelt word",
]

STOP_WORDS = {
    "a", "an", "the", "of", "to", "in", "on", "at", "for", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "and", "or",
    "but", "if", "then", "than", "so", "as", "by", "with", "from", "this", "that",
    "these", "those", "it", "its", "their", "they", "we", "you", "he", "she", "him",
    "her", "his", "our", "your", "my", "me", "us", "i", "who", "whom", "which",
    "what", "where", "when", "why", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "very", "s", "t", "can", "will", "just", "should", "now",
    "select", "given", "word", "option", "options", "following", "sentence",
    "blank", "underline", "underlined", "segment", "substitute", "fill",
    "appropriate", "best", "phrase", "group", "words", "match",
    "list", "list-i", "list-ii", "code", "find", "choose", "identify",
    "indicate", "pick", "matches", "column", "column-i", "column-ii",
    "above", "below", "between", "after", "before", "during", "through",
    "out", "up", "down", "off", "over", "under", "again", "further",
    "here", "there", "what", "whatever", "whenever", "wherever", "whoever",
    "whichever", "however", "although", "though", "even", "since", "until",
    "while", "because", "unless", "whether", "yet", "once", "into",
    "across", "around", "against", "toward", "towards", "upon", "within",
    "without", "among", "amongst", "along", "alongside", "behind", "beyond",
    "near", "nearby", "outside", "inside", "onto",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "first", "second", "third", "fourth", "fifth", "last", "next",
    "no", "yes", "very", "quite", "rather", "too", "also",
    "would", "could", "should", "may", "might", "must", "shall",
    "did", "done", "got", "get", "make", "made", "go", "going",
    "said", "say", "says", "saying", "told", "tell", "telling",
}

# ─── Helpers ────────────────────────────────────────────────────────────────
def is_vocab_token(tok: str) -> bool:
    tok = tok.strip().lower()
    if not tok or len(tok) < 2:
        return False
    if tok in STOP_WORDS:
        return False
    if tok.isdigit():
        return False
    if not re.search(r"[a-zA-Z]", tok):
        return False
    if not re.match(r"^[A-Za-z][A-Za-z\s'-]*$", tok):
        return False
    return True

def normalize_word(w: str) -> str:
    w = w.strip().strip(".,;:!?\"'()[]{}").strip()
    if not w:
        return ""
    return w[0].upper() + w[1:].lower()

def normalize_lower(w: str) -> str:
    return w.strip().strip(".,;:!?\"'()[]{}").strip().lower()

# WordNet similarity cache
_WN_CACHE: dict = {}

def wn_sim(a: str, b: str) -> float:
    """Return Wu-Palmer similarity between two words (max over all synset pairs)."""
    a, b = a.lower(), b.lower()
    if a == b:
        return 1.0
    key = tuple(sorted([a, b]))
    if key in _WN_CACHE:
        return _WN_CACHE[key]
    sa = wordnet.synsets(a)
    sb = wordnet.synsets(b)
    if not sa or not sb:
        _WN_CACHE[key] = 0.0
        return 0.0
    best = 0.0
    for x in sa[:3]:
        for y in sb[:3]:
            try:
                s = x.wup_similarity(y)
                if s is not None and s > best:
                    best = s
            except Exception:
                pass
    _WN_CACHE[key] = best
    return best

def best_guess_correct_answer(stem: str, options: list, qtype: str) -> int:
    """
    Return index of the best-guess correct answer in `options` for the given
    question type. Returns -1 if no guess can be made.
    """
    if not options or len(options) < 2:
        return -1
    if qtype == "synonym":
        # The option most similar to the stem word
        scores = [wn_sim(stem, opt) for opt in options]
        if max(scores) == 0.0:
            return -1
        return scores.index(max(scores))
    if qtype == "antonym":
        # The option most dissimilar to the stem word
        scores = [wn_sim(stem, opt) for opt in options]
        if max(scores) == 0.0:
            return -1
        return scores.index(min(scores))
    if qtype == "one-word":
        # The stem is a phrase; the option that has the most "specific" word match.
        # Try matching any token from the stem to each option via WordNet
        stem_tokens = [t for t in re.findall(r"[a-z]+", stem.lower()) if is_vocab_token(t)]
        if not stem_tokens:
            return -1
        scores = []
        for opt in options:
            best = 0.0
            for st in stem_tokens:
                s = wn_sim(st, opt)
                if s > best:
                    best = s
            scores.append(best)
        if max(scores) == 0.0:
            return -1
        return scores.index(max(scores))
    # For idiom/homonym/spelling — no reliable way to guess correct answer
    return -1

# ─── File parser ────────────────────────────────────────────────────────────
def detect_qtype(body_lower: str) -> str | None:
    if any(re.search(p, body_lower) for p in SYNONYM_PATTERNS):
        return "synonym"
    if any(re.search(p, body_lower) for p in ANTONYM_PATTERNS):
        return "antonym"
    if any(re.search(p, body_lower) for p in ONEWORD_PATTERNS):
        return "one-word"
    if any(re.search(p, body_lower) for p in IDIOM_PATTERNS):
        return "idiom"
    if any(re.search(p, body_lower) for p in HOMONYM_PATTERNS):
        return "homonym"
    if any(re.search(p, body_lower) for p in SPELLING_PATTERNS):
        return "spelling"
    return None

def extract_stem_word(body: str, qtype: str) -> str:
    """Extract the 'stem' for the question (single word for syn/anto, descriptive phrase for OWS/idiom)."""
    first_opt_idx = body.find("(A)")
    if first_opt_idx == -1:
        first_opt_idx = body.find("(a)")
    if first_opt_idx == -1:
        return ""
    pre = body[:first_opt_idx]
    lines = [ln.strip() for ln in pre.split("\n") if ln.strip()]

    if qtype in ("synonym", "antonym"):
        # Skip instruction lines; the stem word is usually the last short line
        candidates = []
        for ln in lines:
            low = ln.lower()
            if any(kw in low for kw in ("select", "given", "sentence", "following", "passage", "italicised", "italicised", "highlighted", "bracketed", "bold", "underlined")):
                continue
            words_in_ln = ln.split()
            if len(words_in_ln) <= 6:
                candidates.append(ln)
        if candidates:
            return candidates[-1].strip()
        return lines[-1].strip() if lines else ""
    else:
        # For one-word / idiom / homonym / spelling: the stem is the descriptive text
        desc_lines = []
        for ln in lines:
            low = ln.lower()
            # Skip pure instruction lines (start with "select the most appropriate ...")
            if low.startswith("select ") and any(p in low for p in (
                "synonym", "antonym", "one word", "one-word", "substitution",
                "idiom", "homonym", "homophone", "spelling", "misspelt",
                "spelt", "group of words", "substitute", "meaning of",
                "fill", "blank",
            )):
                continue
            desc_lines.append(ln)
        return " ".join(desc_lines).strip() if desc_lines else ""

def parse_file(filepath: str):
    exam_name = os.path.basename(filepath).replace("_EN.txt", "").replace("_", " ")
    questions = []
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    parts = re.split(r"\n(?=Q\d+\.)", text)
    for part in parts:
        m = re.match(r"Q(\d+)\.\s*(.*)", part, re.DOTALL)
        if not m:
            continue
        qno = int(m.group(1))
        body = m.group(2)
        body_lower = body.lower()
        qtype = detect_qtype(body_lower)
        if qtype is None:
            continue
        # Extract options
        option_matches = list(re.finditer(
            r"\(\s*([A-Da-d])\s*\)\s*(.+?)(?=\n\s*\(\s*[A-Da-d]\s*\)|\n\s*Q\d+\.|\Z)",
            body, re.DOTALL
        ))
        options = []
        for om in option_matches:
            opt_text = om.group(2).strip()
            opt_text = re.sub(r"\s+", " ", opt_text).strip().rstrip(".")
            options.append(opt_text)
        if not options:
            continue
        # Extract stem
        stem = extract_stem_word(body, qtype)
        # Best-guess correct answer
        correct_idx = best_guess_correct_answer(stem, options, qtype) if qtype in ("synonym", "antonym", "one-word") else -1
        questions.append({
            "exam": exam_name,
            "qno": qno,
            "qtype": qtype,
            "stem": stem,
            "options": options,
            "correctIdx": correct_idx,  # -1 = unknown
        })
    return questions

# ─── Build vocabulary index ─────────────────────────────────────────────────
def build_vocab_db(all_questions):
    """Build per-word stats + appearance tracking."""
    words = defaultdict(lambda: {
        "word": "",
        "asStem": 0,
        "asOption": 0,
        "stemExams": [],
        "optionExams": [],
        "stemQuestions": [],
        "optionQuestions": [],
        "qtypesAsStem": defaultdict(int),
        "qtypesAsOption": defaultdict(int),
    })
    for q in all_questions:
        exam = q["exam"]
        qtype = q["qtype"]
        # Stem — only for syn/anto (single-word stems)
        if qtype in ("synonym", "antonym"):
            stem = q["stem"].strip().strip(".,").strip()
            tokens = stem.split()
            if 1 <= len(tokens) <= 3:
                stem_norm = normalize_word(stem)
                stem_low = stem_norm.lower()
                if is_vocab_token(stem_low) or len(tokens) > 1:
                    entry = words[stem_low]
                    entry["word"] = stem_norm
                    entry["asStem"] += 1
                    entry["stemExams"].append(exam)
                    entry["stemQuestions"].append(q)
                    entry["qtypesAsStem"][qtype] += 1
        # Options — for syn/anto/one-word, options are vocab words
        # For idiom/homonym/spelling — options are usually phrases (skip as vocab)
        if qtype in ("synonym", "antonym", "one-word"):
            for opt in q["options"]:
                opt_clean = opt.strip().strip(".").strip()
                opt_tokens = opt_clean.split()
                if not (1 <= len(opt_tokens) <= 3):
                    continue
                opt_norm = normalize_word(opt_clean)
                opt_low = opt_norm.lower()
                if not is_vocab_token(opt_low):
                    if len(opt_tokens) == 1:
                        continue
                    valid_count = sum(1 for t in opt_tokens if is_vocab_token(t.lower()))
                    if valid_count < 2:
                        continue
                entry = words[opt_low]
                entry["word"] = opt_norm
                entry["asOption"] += 1
                entry["optionExams"].append(exam)
                entry["optionQuestions"].append(q)
                entry["qtypesAsOption"][qtype] += 1
    # Convert defaultdicts and drop empty
    result = {}
    for k, v in words.items():
        if v["asStem"] == 0 and v["asOption"] == 0:
            continue
        v["qtypesAsStem"] = dict(v["qtypesAsStem"])
        v["qtypesAsOption"] = dict(v["qtypesAsOption"])
        result[k] = v
    return result

# ─── Build word → questions map ─────────────────────────────────────────────
def build_word_question_map(words_db, all_questions):
    """For each word, list question IDs where it appeared as stem or option."""
    word_qids = defaultdict(lambda: {"asStem": [], "asOption": []})
    # Build stem -> qid (for syn/anto only — those are the only ones with vocab stems)
    for i, q in enumerate(all_questions):
        if q["qtype"] in ("synonym", "antonym"):
            stem = q["stem"].strip().lower()
            if stem:
                word_qids[stem]["asStem"].append(i)
        # Options
        if q["qtype"] in ("synonym", "antonym", "one-word"):
            for opt in q["options"]:
                opt_low = opt.strip().lower()
                if " " not in opt_low and len(opt_low) > 1:
                    word_qids[opt_low]["asOption"].append(i)
    return dict(word_qids)

# ─── Compute per-word SSC synonym/antonym relationships with status ─────────
def compute_ssc_relations(words_db, all_questions):
    """
    For each word W, compute:
      synonyms: list of {word, status} where status ∈ {'correct', 'distractor', 'added'}
      antonyms: list of {word, status} where status ∈ {'correct', 'distractor', 'added'}

    Logic:
      For each SYNONYM question where W is the stem:
        - The best-guess correct option → mark as 'correct' synonym of W
        - The other options → mark as 'distractor' synonyms of W
      For each SYNONYM question where W is an option:
        - The stem S is a synonym of W. (The question asked for a synonym of S,
          and W was among the options — meaning W is semantically close to S.)
        - We can't be sure if W was the correct answer or distractor, so mark
          S as a 'distractor' synonym of W (conservative).
      Similarly for ANTONYM questions.

    The 'added' status is filled in later by the enrich script for WordNet-only words.
    """
    syn_correct = defaultdict(set)
    syn_distractor = defaultdict(set)
    ant_correct = defaultdict(set)
    ant_distractor = defaultdict(set)

    for q in all_questions:
        qtype = q["qtype"]
        if qtype not in ("synonym", "antonym"):
            continue
        stem = q["stem"].strip().lower()
        if not stem:
            continue
        opts = [o.strip().lower() for o in q["options"]]
        correct_idx = q.get("correctIdx", -1)

        if qtype == "synonym":
            for i, opt in enumerate(opts):
                if not opt or opt == stem:
                    continue
                # Stem side: opt is a synonym of stem
                if i == correct_idx:
                    syn_correct[stem].add(opt)
                    syn_correct[opt].add(stem)  # symmetric
                else:
                    syn_distractor[stem].add(opt)
                    # If opt was an option, stem is also related (as distractor synonym)
                    syn_distractor[opt].add(stem)
                # Cross-option: other options are also (likely) synonyms of this option
                for j, other in enumerate(opts):
                    if i == j or other == opt or not other:
                        continue
                    if j == correct_idx:
                        # other is the correct answer; opt is a distractor
                        # they're still semantically related
                        syn_distractor[opt].add(other)
                    else:
                        syn_distractor[opt].add(other)
        elif qtype == "antonym":
            for i, opt in enumerate(opts):
                if not opt or opt == stem:
                    continue
                if i == correct_idx:
                    ant_correct[stem].add(opt)
                    ant_correct[opt].add(stem)
                else:
                    ant_distractor[stem].add(opt)
                    ant_distractor[opt].add(stem)
                # Other options are also antonyms of this option
                for j, other in enumerate(opts):
                    if i == j or other == opt or not other:
                        continue
                    if j == correct_idx:
                        ant_distractor[opt].add(other)
                    else:
                        ant_distractor[opt].add(other)

    return {
        "syn_correct": {k: list(v) for k, v in syn_correct.items()},
        "syn_distractor": {k: list(v) for k, v in syn_distractor.items()},
        "ant_correct": {k: list(v) for k, v in ant_correct.items()},
        "ant_distractor": {k: list(v) for k, v in ant_distractor.items()},
    }

# ─── Main ───────────────────────────────────────────────────────────────────
def main():
    all_files = sorted(glob.glob(os.path.join(SSC_DIR, "*_EN.txt")))
    print(f"Found {len(all_files)} SSC files")
    all_questions = []
    file_stats = []
    for fpath in all_files:
        qs = parse_file(fpath)
        exam_name = os.path.basename(fpath).replace("_EN.txt", "").replace("_", " ")
        all_questions.extend(qs)
        file_stats.append({"exam": exam_name, "questions": len(qs)})

    print("\nParsed questions per file:")
    for fs in file_stats:
        print(f"  {fs['exam']:35s}  {fs['questions']:5d}")

    # Count by qtype
    by_type = defaultdict(int)
    for q in all_questions:
        by_type[q["qtype"]] += 1
    print(f"\nTotal parsed questions: {len(all_questions)}")
    for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t:15s}  {c:5d}")

    words_db = build_vocab_db(all_questions)
    print(f"\nUnique vocabulary words: {len(words_db)}")

    word_qids = build_word_question_map(words_db, all_questions)
    print(f"Word→question map entries: {len(word_qids)}")

    ssc_relations = compute_ssc_relations(words_db, all_questions)
    print(f"\nSSC relations:")
    print(f"  Synonyms (correct):    {sum(len(v) for v in ssc_relations['syn_correct'].values())}")
    print(f"  Synonyms (distractor): {sum(len(v) for v in ssc_relations['syn_distractor'].values())}")
    print(f"  Antonyms (correct):    {sum(len(v) for v in ssc_relations['ant_correct'].values())}")
    print(f"  Antonyms (distractor): {sum(len(v) for v in ssc_relations['ant_distractor'].values())}")

    # Sort words by total freq desc, then alphabetical
    sorted_words = sorted(words_db.items(),
                          key=lambda kv: (- (kv[1]["asStem"] + kv[1]["asOption"]), kv[0]))

    # Write words.json
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
            "qtypesAsStem": v["qtypesAsStem"],
            "qtypesAsOption": v["qtypesAsOption"],
        })
    with open(os.path.join(OUTPUT_DIR, "words.json"), "w", encoding="utf-8") as f:
        json.dump(words_out, f, ensure_ascii=False, indent=2)
    print(f"\nWrote words.json ({len(words_out)} words)")

    # Write questions.json
    questions_out = []
    for i, q in enumerate(all_questions):
        questions_out.append({
            "id": i,
            "exam": q["exam"],
            "qno": q["qno"],
            "qtype": q["qtype"],
            "stem": q["stem"],
            "options": q["options"],
            "correctIdx": q.get("correctIdx", -1),
        })
    with open(os.path.join(OUTPUT_DIR, "questions.json"), "w", encoding="utf-8") as f:
        json.dump(questions_out, f, ensure_ascii=False, indent=2)
    print(f"Wrote questions.json ({len(questions_out)} questions)")

    # Write word_questions.json
    with open(os.path.join(OUTPUT_DIR, "word_questions.json"), "w", encoding="utf-8") as f:
        json.dump(word_qids, f, ensure_ascii=False)
    print(f"Wrote word_questions.json ({len(word_qids)} words)")

    # Write ssc_relations.json
    with open(os.path.join(OUTPUT_DIR, "ssc_relations.json"), "w", encoding="utf-8") as f:
        json.dump(ssc_relations, f, ensure_ascii=False)
    print(f"Wrote ssc_relations.json")

    # Summary
    summary = {
        "totalFiles": len(all_files),
        "exams": [fs["exam"] for fs in file_stats],
        "totalQuestions": len(all_questions),
        "byType": dict(by_type),
        "totalSynonymAntonym": by_type["synonym"] + by_type["antonym"],
        "totalOneWord": by_type["one-word"],
        "totalIdioms": by_type["idiom"],
        "totalHomonyms": by_type["homonym"],
        "totalSpelling": by_type["spelling"],
        "totalUniqueWords": len(words_db),
        "questionsPerFile": file_stats,
    }
    with open(os.path.join(OUTPUT_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Wrote summary.json")

    # Print top 20
    print("\nTop 20 words (by total frequency):")
    for w in words_out[:20]:
        print(f"  {w['word']:25s}  stem={w['asStem']:3d}  opt={w['asOption']:3d}  total={w['total']:3d}")

if __name__ == "__main__":
    main()
