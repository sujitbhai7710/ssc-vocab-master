# Data Pipeline

How the SSC exam content (vocab + grammar) was generated and how to regenerate it. All pipeline scripts are in [`scripts/`](../scripts/).

## Sources

| Source | What it provides | Location |
|--------|------------------|----------|
| **pritammaity7/ssc-txt** (GitHub) | 23 SSC exam paper `.txt` files (CGL/CHSL/CPO/MTS, 2019-2026) + 3 grammar PDFs | cloned to `data-source/` + PDFs processed |
| **rani-maam.pdf** | "English With Rani Ma'am — 60 Rules of Grammar 2.0" (scrambled 2-col OCR) | `scripts/work-data/rani-maam.txt` |
| **error spotting.pdf** | Rahul Gupta "Top 100 Rules For Error Spotting + 300 Error Questions" | `scripts/work-data/error-spotting.txt` |
| **100-grammar-rules.pdf** | Aman "100 Most Important Grammar Rules" (Hinglish answers) | `scripts/work-data/100-grammar-rules.txt` |
| **Justwoker AI API** | claude-opus-4-8 (maps to claude-opus-5) for structuring/answering/explaining | needs API key (see `.env.example`) |

⚠️ **No Satwik/0xSatwik data is used.** The user explicitly said not to use it. All grammar content is extracted fresh from the PDFs + raw txt files.

## Pipeline overview

```
3 PDFs ──pdfplumber──► .txt ──AI chunks──► src_{rani,error,aman}.json (rules + questions)
                                          │
23 PYQ .txt files ──regex parse──► grammar_pyqs.json (error/improvement/narration/voice)
                                          │
                                          ▼
                                    merge_rules.py
                                          │ (Rani 60 backbone + match error/aman + 54 new = 114)
                                          ▼
                                    answer_explain.py
                                          │ (AI answers + explains + maps PYQs to rules)
                                          ▼
                                    create_unmapped_rules.py
                                          │ (clusters 515 unmapped → 53 new rules = 167 total)
                                          ▼
                                    build_grammar_data.py
                                          │ (dedup, order rani→error→pyq, assemble)
                                          ▼
                                    split_grammar_qs.py
                                          │ (per-rule question files for lazy loading)
                                          ▼
                              public/data/grammar/*.json

                          ── build_narration_voice.py ──► narration + voice rules + PYQs
```

## Scripts (run in order)

All scripts are resumable (save partial progress) and use parallel AI calls (2 keys, 6 workers).

### 1. `extract_pdfs.py` — PDF → text
Uses `pdfplumber` to extract text from the 3 grammar PDFs. Output: `work-data/*.txt`.
```bash
pip install pdfplumber
python3 scripts/extract_pdfs.py
```

### 2. `parse_grammar_txt.py` — PYQ text → grammar questions
Regex-parses the 23 SSC `.txt` files to extract error/improvement/narration/voice questions (NO Satwik). Splits question blocks, classifies by keyword, dedupes.
```bash
python3 scripts/parse_grammar_txt.py
# → work-data/grammar_pyqs.json: {error:1077, improvement:1085, narration:232, voice:329}
```

### 3. `structure_pdfs.py` — AI-structure each PDF into rules + questions
Chunks each PDF's text and asks the AI to extract rules + MCQs as JSON. Resumable (saves `src_<name>_partial.json`). Run once per source:
```bash
export JUSTWOKER_KEYS="sk-key1,sk-key2"
python3 scripts/structure_pdfs.py rani    # → src_rani.json (64 rules, 790 Qs)
python3 scripts/structure_pdfs.py error   # → src_error.json (100 rules, 300 Qs)
python3 scripts/structure_pdfs.py aman    # → src_aman.json (101 rules, 363 examples)
```

### 4. `merge_rules.py` — merge 3 sources into 114 rules
Rani's 60 rules form the backbone (in order). For each, AI finds matching rules from error+aman and writes a clean merged concept. Unmatched error/aman rules become "new" rules appended after rule 60.
```bash
python3 scripts/merge_rules.py
# → merged_rules.json (60 backbone + 54 new = 114), src_to_gr.json, rule_index.json
```

### 5. `answer_explain.py` — AI answer + explain + map all MCQs
Two modes (both resumable):
```bash
python3 scripts/answer_explain.py pdf   # verify rani+error answers, write explanations (1090 Qs)
python3 scripts/answer_explain.py pyq   # answer + explain + map PYQs to rules (2162 Qs)
# → expl_pdf.jsonl, expl_pyq.jsonl
```

### 6. `create_unmapped_rules.py` — cluster unmapped PYQs into 53 new rules
515 PYQs couldn't map to existing rules. AI clusters them by concept and creates new rules (gr-115 onwards). Final: 167 rules, 0 unmapped.
```bash
python3 scripts/create_unmapped_rules.py
```

### 7. `build_narration_voice.py` — generate narration + voice rule sets
AI writes 10 comprehensive sections each for narration (direct-indirect speech) and voice (active-passive), synthesised from Wren & Martin / Rani / Adda247 / Testbook. Then answers + explains + maps their PYQs.
```bash
python3 scripts/build_narration_voice.py
# → narration_rules.json (10 sections), narration_questions.json (232 PYQs)
# → voice_rules.json (10 sections), voice_questions.json (329 PYQs)
```

### 8. `build_grammar_data.py` — assemble final public/data/grammar/
Dedupes questions (rani → error → pyq priority), attaches questionIds to rules, writes the final files.
```bash
python3 scripts/build_grammar_data.py
# → public/data/grammar/{rules,questions,narration_*,voice_*,summary}.json
```

### 9. `split_grammar_qs.py` — per-rule question files (lazy loading)
Splits `questions.json` into `public/data/grammar/qs/gr-<no>.json` so the Grammar Rules page loads one rule's questions at a time instead of the full 2MB.
```bash
python3 scripts/split_grammar_qs.py
```

### 10. `split_word_questions.py` — speed optimization for vocab
Splits the vocab `questions.json` (2.45MB) into per-letter `public/data/wq/<letter>.json` (~230KB each) + creates `top_words.json` (6.8KB) for the dashboard. Deletes the 12.2MB dead `enriched.json` master.
```bash
python3 scripts/split_word_questions.py
```

### 11. `fix_gray.py` — AI-clean WordNet-added synonyms/antonyms
The vocab data had "gray" (added by WordNet, not from exams) syn/ant entries — many obscure. AI verifies each one and keeps only valid common ones.
```bash
python3 scripts/fix_gray.py verify   # resumable, runs in cycles (21,880 entries)
python3 scripts/fix_gray.py rebuild  # rewrite enriched files keeping only verified
```

## Intermediate data

`scripts/work-data/` contains the intermediate pipeline outputs (kept for reproducibility):
- `*.txt` — extracted PDF text
- `src_*.json` + `src_*_partial.json` — per-source structured rules/questions
- `merged_rules.json`, `rule_index.json`, `src_to_gr.json` — merge intermediates
- `expl_pdf.jsonl`, `expl_pyq.jsonl` — AI explanations (resumable log)
- `gray_verdicts.jsonl` — gray syn/ant AI verdicts
- `grammar_pyqs.json` — parsed PYQ questions

## AI API details

- **Endpoint:** `https://api.justwoker.icu/v1/chat/completions` (OpenAI-compatible)
- **Model:** `claude-opus-4-8` (server maps to `claude-opus-5`)
- **Auth:** Bearer token, 2 keys rotated in parallel (round-robin)
- **Headers:** MUST include a browser `User-Agent` header (Cloudflare blocks default `Python-urllib` with error 1010)
- **Retries:** 4 attempts, exponential backoff
- **Timeouts:** Cloudflare proxy kills requests >120s (error 524) — keep chunks small

## Regenerating everything from scratch

```bash
cd ssc-vocab-master
export JUSTWOKER_KEYS="sk-key1,sk-key2"
pip install pdfplumber

python3 scripts/extract_pdfs.py
python3 scripts/parse_grammar_txt.py
python3 scripts/structure_pdfs.py rani
python3 scripts/structure_pdfs.py error
python3 scripts/structure_pdfs.py aman
python3 scripts/merge_rules.py
python3 scripts/answer_explain.py pdf
python3 scripts/answer_explain.py pyq
python3 scripts/create_unmapped_rules.py
python3 scripts/build_narration_voice.py
python3 scripts/build_grammar_data.py
python3 scripts/split_grammar_qs.py
python3 scripts/split_word_questions.py
python3 scripts/fix_gray.py verify
python3 scripts/fix_gray.py rebuild

npm run build
npx wrangler pages deploy ./dist --project-name=sscpyqs
```

This takes ~1-2 hours of AI API time (mostly the answer/explain + gray verification steps).
