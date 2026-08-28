#!/usr/bin/env python3
"""
Parse all SSC .txt exam files and extract vocabulary data:
- Words that appeared as Question Stems (synonym/antonym/one-word-substitution questions)
- Words that appeared as Options
- Frequency count per word, per exam, per question type
- Store results as JSON for the Next.js web app
"""

import os
import re
import json
import glob
from collections import defaultdict, Counter

SSC_DIR = "/home/z/my-project/ssc-txt"
OUTPUT_DIR = "/home/z/my-project/src/data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- Question type classifiers --------------------------------------------------
SYNONYM_PATTERNS = [
    r"synonym of the given word",
    r"synonyms? of the",
    r"word which is most similar in meaning",
    r"same in meaning",
    r"similar in meaning",
    r"select the word which is most nearly the same in meaning",
    r"most nearly the same in meaning",
]

ANTONYM_PATTERNS = [
    r"antonym of the given word",
    r"antonyms? of the",
    r"opposite in meaning",
    r"opposite of the",
    r"word which is most opposite in meaning",
    r"most nearly opposite in meaning",
    r"select the word which is most nearly opposite in meaning",
]

ONEWORD_PATTERNS = [
    r"one[- ]word substitution",
    r"one word substitution",
    r"word that can be used as a substitute",
    r"option that can be used as a one[- ]word substitute",
    r"word which means the same as the group of words",
    r"select the word which means the same as the group of words",
]

# Question text indicators that mark a synonym / antonym / oneword question
QUESTION_KEYWORDS = ("synonym", "antonym", "one-word", "one word", "opposite in meaning",
                     "same as the group of words", "substitute")

# Stop words we shouldn't add to vocabulary (common pronouns / articles / etc)
STOP_WORDS = {
    "a", "an", "the", "of", "to", "in", "on", "at", "for", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "and", "or",
    "but", "if", "then", "than", "so", "as", "by", "with", "from", "this", "that",
    "these", "those", "it", "its", "their", "they", "we", "you", "he", "she", "him",
    "her", "his", "our", "your", "my", "me", "us", "i", "who", "whom", "which",
    "what", "where", "when", "why", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "very", "s", "t", "can", "will", "just", "should", "now",
    "outside", "starting", "experiencing", "avoided",  # noise from "from the following sentence" type
    "select", "given", "word", "option", "options", "following", "sentence",
    "blank", "underline", "underlined", "segment", "substitute", "fill",
    "appropriate", "most", "best", "phrase", "group", "words", "match",
    "list", "list-i", "list-ii", "code", "find", "choose", "identify",
    "indicate", "pick", "matches", "column", "column-i", "column-ii",
    "above", "below", "between", "after", "before", "during", "through",
    "out", "up", "down", "off", "over", "under", "again", "further",
    "here", "there", "what", "whatever", "whenever", "wherever", "whoever",
    "whichever", "however", "although", "though", "even", "since", "until",
    "while", "because", "unless", "whether", "yet", "once",
}

# Sometimes options are not single words (phrases). We only treat short, single-word
# tokens as vocabulary entries.
MAX_OPTION_TOKENS = 3   # allow "fall apart" / "look after" type phrasal options

def is_vocab_token(tok: str) -> bool:
    tok = tok.strip().lower()
    if not tok:
        return False
    if len(tok) < 2:
        return False
    if tok in STOP_WORDS:
        return False
    if tok.isdigit():
        return False
    # must contain at least one letter
    if not re.search(r"[a-zA-Z]", tok):
        return False
    # disallow tokens with weird characters (only letters, -, space, ' allowed)
    if not re.match(r"^[A-Za-z][A-Za-z\s'-]*$", tok):
        return False
    return True

def normalize_word(w: str) -> str:
    """Capitalize first letter, lowercase the rest, strip whitespace/punctuation."""
    w = w.strip().strip(".,;:!?\"'()[]{}").strip()
    if not w:
        return ""
    # Capitalize first letter
    return w[0].upper() + w[1:].lower()

def normalize_lower(w: str) -> str:
    return w.strip().strip(".,;:!?\"'()[]{}").strip().lower()

# ---- File parser ---------------------------------------------------------------
def parse_file(filepath: str):
    """
    Return list of question dicts:
    [
        {
            "exam": "SSC CGL Tier1 2022",
            "qno": 710,
            "qtype": "synonym" | "antonym" | "one-word",
            "stem_word": "Irrevocable",
            "options": ["Unmediated", "Congruent", "Irreversible", "Irresponsive"],
        }, ...
    ]
    """
    exam_name = os.path.basename(filepath).replace("_EN.txt", "").replace("_", " ")
    questions = []

    with open(filepath, encoding="utf-8", errors="ignore") as f:
        text = f.read()

    # Split into questions by "Q<number>." at start of line
    # Use lookahead to keep the Q delimiter
    parts = re.split(r"\n(?=Q\d+\.)", text)

    for part in parts:
        # Match the question number
        m = re.match(r"Q(\d+)\.\s*(.*)", part, re.DOTALL)
        if not m:
            continue
        qno = int(m.group(1))
        body = m.group(2)

        # Detect question type
        body_lower = body.lower()
        qtype = None
        if any(re.search(p, body_lower) for p in SYNONYM_PATTERNS):
            qtype = "synonym"
        elif any(re.search(p, body_lower) for p in ANTONYM_PATTERNS):
            qtype = "antonym"
        elif any(re.search(p, body_lower) for p in ONEWORD_PATTERNS):
            qtype = "one-word"

        if qtype is None:
            continue

        # Extract options: lines like "(A) xxx" "(B) xxx" "(C) xxx" "(D) xxx"
        # Some files use (a), (b), (c), (d). Match case-insensitively.
        option_matches = list(re.finditer(
            r"\(\s*([A-Da-d])\s*\)\s*(.+?)(?=\n\s*\(\s*[A-Da-d]\s*\)|\n\s*Q\d+\.|\Z)",
            body, re.DOTALL
        ))
        options = []
        for om in option_matches:
            opt_text = om.group(2).strip()
            # Clean trailing line break / extra whitespace
            opt_text = re.sub(r"\s+", " ", opt_text).strip()
            # Strip trailing punctuation that's clearly not part of the word
            opt_text = opt_text.rstrip(".")
            options.append(opt_text)

        # Extract the "stem word" — for synonym/antonym, it's typically the line
        # right after the question text. For one-word substitution, the stem is
        # the descriptive phrase (not a single word); we still try to extract a
        # reasonable key.
        stem_word = ""

        if qtype in ("synonym", "antonym"):
            # The body looks like:
            #   Select the most appropriate synonym of the given word.
            #   PERSEVERANCE
            #   (A) ...
            # OR
            #   Select the most appropriate synonym of the given word: PERSEVERANCE
            # OR
            #   Select the most appropriate synonym of the given word from the following sentence.
            #   Encountered
            #   Many people have been experiencing ...
            #
            # Strategy: find the line(s) between the question text and the first option,
            # the LAST capitalized token-line is typically the stem word.
            first_opt_idx = body.find("(A)")
            if first_opt_idx == -1:
                first_opt_idx = body.find("(a)")
            if first_opt_idx == -1:
                # skip if no options found
                continue
            pre = body[:first_opt_idx]
            # Remove the question text line(s) - take the LAST non-empty line that is short
            lines = [ln.strip() for ln in pre.split("\n") if ln.strip()]
            # Filter out the instruction line(s)
            # Heuristic: stem is the last short line (<=4 words) that doesn't contain
            # words like "select", "given", "sentence"
            candidates = []
            for ln in lines:
                ln_clean = ln.strip()
                if not ln_clean:
                    continue
                low = ln_clean.lower()
                if "select" in low or "given" in low or "sentence" in low or "following" in low:
                    continue
                # skip the instruction line
                words_in_ln = ln_clean.split()
                if len(words_in_ln) <= 6:
                    candidates.append(ln_clean)
            if candidates:
                stem_word = candidates[-1].strip()
            else:
                # Fallback: take the last non-empty line
                stem_word = lines[-1].strip() if lines else ""
        elif qtype == "one-word":
            # The body looks like:
            #   Select the most appropriate one word substitution for the given group of words.
            #   A person very reserved in speech
            #   (A) Confident
            #   ...
            # The "stem" is the descriptive phrase. We'll record it as-is but NOT add it
            # to the vocabulary frequency count (we only count option words for this type).
            first_opt_idx = body.find("(A)")
            if first_opt_idx == -1:
                first_opt_idx = body.find("(a)")
            if first_opt_idx == -1:
                continue
            pre = body[:first_opt_idx]
            lines = [ln.strip() for ln in pre.split("\n") if ln.strip()]
            # Remove instruction line(s)
            desc_lines = []
            for ln in lines:
                low = ln.lower()
                if "select" in low or "given" in low or "group of words" in low or "substitute" in low:
                    continue
                desc_lines.append(ln)
            stem_word = " ".join(desc_lines).strip() if desc_lines else ""
            # For one-word substitution: ONLY add the option words to vocabulary.
            # The "stem" is a description, not a vocabulary word.

        # Don't require options to be present in case parsing missed some
        if not options:
            continue

        questions.append({
            "exam": exam_name,
            "qno": qno,
            "qtype": qtype,
            "stem_word": stem_word,
            "options": options,
        })

    return questions

# ---- Build vocabulary database --------------------------------------------------
def build_vocab_db(all_questions):
    """
    Build:
      words: {
          "<word>": {
              "word": "<Word>",
              "as_stem": <int>,    # times appeared as the question word (synonym/antonym only)
              "as_option": <int>,  # times appeared as an option
              "stem_exams": [<exam>, ...],
              "option_exams": [<exam>, ...],
              "stem_questions": [<full question dict>, ...],
              "option_questions": [<full question dict>, ...],
              "qtypes_as_stem": {"synonym": N, "antonym": N, "one-word": N},
              "qtypes_as_option": {"synonym": N, "antonym": N, "one-word": N},
          }
      }
    """
    words = defaultdict(lambda: {
        "word": "",
        "as_stem": 0,
        "as_option": 0,
        "stem_exams": [],
        "option_exams": [],
        "stem_questions": [],
        "option_questions": [],
        "qtypes_as_stem": {"synonym": 0, "antonym": 0, "one-word": 0},
        "qtypes_as_option": {"synonym": 0, "antonym": 0, "one-word": 0},
    })

    for q in all_questions:
        exam = q["exam"]
        qtype = q["qtype"]

        # --- Stem handling ---
        if qtype in ("synonym", "antonym"):
            stem = q["stem_word"]
            # Only accept stems that look like vocabulary words (single token ideally,
            # but allow up to 3 words for compound stems)
            stem_clean = stem.strip().strip(".,").strip()
            # Skip if it's clearly a phrase (e.g. contains lowercase conjunctions)
            tokens = stem_clean.split()
            if 1 <= len(tokens) <= 3:
                # Use lowercase for normalization
                stem_norm = normalize_word(stem_clean)
                stem_low = stem_norm.lower()
                if is_vocab_token(stem_low) or len(tokens) > 1:
                    entry = words[stem_low]
                    entry["word"] = stem_norm
                    entry["as_stem"] += 1
                    entry["stem_exams"].append(exam)
                    entry["stem_questions"].append(q)
                    entry["qtypes_as_stem"][qtype] += 1

        # --- Option handling ---
        for opt in q["options"]:
            opt_clean = opt.strip().strip(".").strip()
            # For one-word: the correct answer (and other single-word options) are vocab words
            # For synonym/antonym: ALL options are vocab words
            # Only accept single-word options (or short phrases up to MAX_OPTION_TOKENS)
            opt_tokens = opt_clean.split()
            if not (1 <= len(opt_tokens) <= MAX_OPTION_TOKENS):
                continue
            opt_norm = normalize_word(opt_clean)
            opt_low = opt_norm.lower()
            if not is_vocab_token(opt_low):
                # Allow phrases that contain at least one valid vocab token
                # Skip otherwise
                if len(opt_tokens) == 1:
                    continue
                # For phrases, only count if at least 2 tokens are valid vocab
                valid_count = sum(1 for t in opt_tokens if is_vocab_token(t.lower()))
                if valid_count < 2:
                    continue
            entry = words[opt_low]
            entry["word"] = opt_norm
            entry["as_option"] += 1
            entry["option_exams"].append(exam)
            entry["option_questions"].append(q)
            entry["qtypes_as_option"][qtype] += 1

    # Convert defaultdict to dict and sort
    result = {}
    for k, v in words.items():
        if v["as_stem"] == 0 and v["as_option"] == 0:
            continue
        result[k] = v
    return result

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

    print(f"\nTotal synonym/antonym/one-word questions: {len(all_questions)}")

    words = build_vocab_db(all_questions)
    print(f"Unique vocabulary words: {len(words)}")

    # Sort words: by total frequency desc, then alphabetically
    sorted_words = sorted(words.items(),
                          key=lambda kv: (- (kv[1]["as_stem"] + kv[1]["as_option"]),
                                          kv[0]))

    # Build the final JSON structure
    # 1. words.json — all words with their stats
    # 2. questions.json — all raw parsed questions (for MCQs)
    # 3. summary.json — overview stats

    words_out = []
    for word_low, v in sorted_words:
        words_out.append({
            "word": v["word"],
            "wordLower": word_low,
            "asStem": v["as_stem"],
            "asOption": v["as_option"],
            "total": v["as_stem"] + v["as_option"],
            "stemExams": sorted(set(v["stem_exams"])),
            "optionExams": sorted(set(v["option_exams"])),
            "qtypesAsStem": v["qtypes_as_stem"],
            "qtypesAsOption": v["qtypes_as_option"],
        })

    # Save questions separately (lighter)
    questions_out = []
    for i, q in enumerate(all_questions):
        questions_out.append({
            "id": i,
            "exam": q["exam"],
            "qno": q["qno"],
            "qtype": q["qtype"],
            "stem": q["stem_word"],
            "options": q["options"],
        })

    # Summary
    total_stems = sum(1 for q in all_questions if q["qtype"] in ("synonym", "antonym"))
    total_oneword = sum(1 for q in all_questions if q["qtype"] == "one-word")
    summary = {
        "totalFiles": len(all_files),
        "exams": [fs["exam"] for fs in file_stats],
        "totalQuestions": len(all_questions),
        "totalSynonymAntonym": total_stems,
        "totalOneWord": total_oneword,
        "totalUniqueWords": len(words),
        "questionsPerFile": file_stats,
    }

    # Write outputs
    with open(os.path.join(OUTPUT_DIR, "words.json"), "w", encoding="utf-8") as f:
        json.dump(words_out, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUTPUT_DIR, "questions.json"), "w", encoding="utf-8") as f:
        json.dump(questions_out, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUTPUT_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nOutputs written to {OUTPUT_DIR}/")
    print(f"  words.json      {len(words_out):6d} words")
    print(f"  questions.json  {len(questions_out):6d} questions")
    print(f"  summary.json    overview")

    # Print top 20 words
    print("\nTop 20 words (by total frequency):")
    for w in words_out[:20]:
        print(f"  {w['word']:25s}  stem={w['asStem']:3d}  opt={w['asOption']:3d}  total={w['total']:3d}")

if __name__ == "__main__":
    main()
