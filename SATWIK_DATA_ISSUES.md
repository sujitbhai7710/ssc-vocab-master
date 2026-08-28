# Satwik Data Issues — Found & Fixed

This document lists every issue found in 0xSatwik's SSC Question Bank data, and how our parser fixed each.

## Summary of Issues Fixed

| Issue | Count | Fix Applied |
|-------|-------|-------------|
| SA questions with empty `main` (underlined word) | 173 | Recovered 156 via regex on `expl`; fallback to `opts[ans]` for 17 |
| Idiom questions where `main` was non-idiom phrase (e.g. 'because of') | 361 | Replaced with `opts[ans]` (the actual idiom) |
| Spelling questions with empty `main` | 74 | Skipped (no clean single-word answer) |
| Spelling questions where answer was 'No error' | 2 | Skipped (no vocab word to track) |
| Homonym questions with empty `main` | 20 | Used `opts[ans]` as the homonym word |
| OWS questions with multi-word `main` (e.g. 'Alma mater') | 13 | Kept as-is (valid multi-word OWS answers) |

## Issue 1: Idiom `main` field sometimes contains the underlined segment, not the idiom

**Example:**
```json
{
  "id": 101,
  "prompt": "Select the most appropriate idiom that can substitute the italicised words in the given sentence.",
  "sent": "He was sacked from his job because of a grave error on his part.",
  "main": "because of",   // WRONG: should be "Himalayan blunder" (the correct idiom)
  "opts": ["raining cats and dogs", "minding one's p's and q's", "picking holes in one's cot", "Himalayan blunder"],
  "ans": 3,
  "expl": "'Himalayan blunder' means grave/serious mistake"
}
```

**Root cause:** Satwik's parser set `main` to the italicised segment from the sentence ('because of a grave error') instead of the idiom that replaces it ('Himalayan blunder').

**Our fix:** For idiom questions with 'substitute' in the prompt and `main` that doesn't look like an idiom phrase (e.g. 'because of', 'in spite of'), replace `main` with `opts[ans]` (the actual idiom).

## Issue 2: SA questions with empty `main` (173 questions)

**Pattern:** Questions like 'Select the most appropriate synonym of the underlined word in the given sentence.' have an empty `main` field because the underlined word in the PDF didn't translate to text.

**Example:**
```json
{
  "id": 184,
  "prompt": "Select the most appropriate synonym of the underlined word in the given sentence.",
  "sent": "The professor refused to comment on the erroneous description of the historical events in the journal.",
  "main": null,    // WRONG: should be "erroneous" (the underlined word)
  "opts": ["Suitable", "Lucid", "Inaccurate", "Sensitive"],
  "ans": 2,
  "expl": "'Erroneous' means inaccurate/wrong."
}
```

**Root cause:** The underlined word in the original PDF was a visual underline, which doesn't survive text extraction.

**Our fix:** Regex-based extraction from `expl` (e.g. `'Erroneous' means ...`). Recovered 156 of 173 (90%). For the unrecoverable 17, fall back to `opts[ans]` (which is the synonym/antonym of the stem — at least we get a related word).

## Issue 3: Spelling questions with empty `main` (97 questions)

**Pattern:** Two sub-types:
1. 'Select the sentence that contains a spelling error.' — answer is a full sentence (no clean word).
2. 'Identify the INCORRECTLY spelt word (A/B/C/D).' — answer is a letter (A/B/C/D), not a word.

**Our fix:** Skip these entirely (no clean single-word vocab entry). Also skip questions where the answer is 'No error' (means all sentences were correctly spelt).

## Issue 4: Homonym questions with empty `main` (20 questions)

**Pattern:** Fill-in-the-blank homonym questions where Satwik didn't fill `main`.

**Our fix:** Use `opts[ans]` (the correct homonym) as the word.

## Issue 5: OWS multi-word `main` (13 questions)

**Examples:** 'Alma mater', 'Exit poll', 'Vicious cycle', 'All are correct'.

**Note:** These are NOT errors — the OWS answer can legitimately be a multi-word phrase. We keep these as-is.

## Other Observations

- Satwik's `sa/vocab.json` has 4,327 word entries with rich metadata: pos, English meaning, Bengali meaning (bn), example (ex), root (root+rm+rbn), mnemonic (mn).
- `roots.json` has 1,603 root families with full word lists.
- `words/<letter>.json` files have additional word-level data.
- Real correct answers (`ans` field) appear reliable for all 4,892+ questions.
- Explanations (`expl` field) are valuable for the MCQ reveal-answer box.
