# Future Roadmap — Mock Tests & Custom Series

> **✅ UPDATE (2026-08-30):** Mock tests, custom test series, auto-problematic from wrong answers, and the SSC-style timer are now **FULLY IMPLEMENTED**. See the "Implemented" badges below. This document remains as the original spec + implementation notes.

This document captures the user's planned features (shared in session 3) and how the current database + architecture already supports them.

## User's vision (verbatim summary)

> In future we will make mock tests. Questions I get wrong will auto-send to problems. Each will have separate problematic things (syn/ant, idiom, spelling, homonym, grammar, etc.). Also allow removing problematic.
>
> For example: first day I read 1-20 vocab, then I can set "read till X" for any page (even grammar rules) to track progress. When we add mock tests, based on my progress, multiple test series will show — mixtures/random questions of just syn/ant which I still haven't read, or idioms, or homonyms, or grammar — anything. It will only add a single MCQ per vocab (no multiple for single vocab). User can set if they want multiple from a single vocab/rule or not.
>
> User can make custom test series based on performance — e.g. if I read till 100 questions of each vocab, I can set like 40-70 questions of syn/ant, 80-100 questions of idioms, or grammar rules 20-30. User can set a timer: SSC gives 25 questions in 15 minutes, so we give 12 minutes max for 25. If 100 questions selected, 48 minutes auto-set. But customizable.
>
> Same for narration and voice.

## ✅ Feature 1: Mock tests (auto-generated from progress) — IMPLEMENTED

### Concept
Based on the user's `progress.completed` set (what they've marked as "read"), the system auto-generates test series that quiz them on material they've covered but might be forgetting.

### Implementation
- **DB tables:** `test_attempts`, `test_results` (see `scripts/schema.sql`)
- **Worker endpoints:** `/api/test/generate`, `/api/test/[id]`, `/api/test/submit`, `/api/test/list`
- **Pages:** `/tests` (list + presets), `/test?id=X` (take), `/test-results?id=X` (review)
- **Components:** `TestList.svelte`, `TestRunner.svelte`, `TestResults.svelte`, `TestCard.svelte`
- **Client API:** `src/lib/test-api.ts`
- **Engine:** `functions/_lib/test-engine.ts`

### Rules (all implemented)
- ✅ **Single MCQ per vocab word** by default — pick one question per word (not all questions for that word). User can toggle "multiple from single vocab/rule" off/on.
- ✅ **Only include words/rules the user has marked as read** (in their `progress.completed` set for that page_type).
- ✅ **Mixed/random** — questions can come from any category (syn/ant, idioms, spelling, homonyms, grammar, narration, voice) or be filtered to specific categories.
- ✅ **Auto-problematic on wrong answer** — if the user answers wrong, that question's vocab/rule auto-adds to `problematic` (with sub_type = the test category).

### 4 auto-generated presets (in `src/lib/test-api.ts → AUTO_PRESETS`)
1. **Quick Mix (25 Q, ~12 min)** — balanced across all 8 categories
2. **Syn/Ant Focus (50 Q, ~24 min)** — syn/ant only
3. **Problematic Revision (20 Q, untimed)** — only from your Problems list, allows multiple-per-item
4. **Grammar + Narration + Voice (40 Q, ~19 min)** — grammar-focused

## ✅ Feature 2: Custom test series — IMPLEMENTED

### Concept
The user configures their own test: pick categories + question ranges based on what they've studied.

### Implementation
- **Page:** `/tests/custom` (build/edit a config)
- **Component:** `CustomTestBuilder.svelte`
- **Saved configs DB table:** `test_configs`
- **CRUD endpoints:** `/api/test/configs` (GET/POST/PATCH/DELETE)

### Example config (matches user's example)
```
Categories:
  - syn/ant:     40-70 questions  (from progress.completed in 'stems'/'options')
  - idioms:      80-100 questions (from progress.completed in 'idioms')
  - grammar:     20-30 rules      (from progress.completed in 'grammar-rules')
  - narration:   10-15 questions
  - voice:       10-15 questions
Total: ~160-230 questions
```

### ✅ Timer (SSC pattern) — IMPLEMENTED
- SSC: 25 questions in 15 minutes, user said "we give 12 min max for 25"
- Ratio: `12/25 = 0.48 min/question`
- Auto-calc: `total_max_questions × 0.48 minutes` (e.g. 100 questions → 48 min)
- **Customizable** — user can override the auto-calculated time in the builder

## ✅ Feature 3: Auto-problematic from wrong answers — IMPLEMENTED

### Concept
When a user gets a test question wrong, the underlying vocab word / grammar rule auto-adds to their `problematic` list.

### Implementation (in `functions/api/test/submit.ts`)
- After scoring, for each wrong answer:
  - `item_type` = derived from category (`vocab` for syn-ant/ows/idiom/homonym/spelling, `grammar-mcq` for grammar, `narration` for narration, `voice` for voice)
  - `item_key` = the word/rule-id/section-id
  - `sub_type` = the test category (e.g. 'syn-ant', 'narration')
- Deduped automatically (`UNIQUE(user_id, item_type, item_key)` constraint + `ON CONFLICT DO NOTHING`)
- User can still manually remove from `/problems`
- The submit response includes `auto_problematic_added` count

## ✅ Feature 4: Per-category problematic (already done ✓)

The `problematic` table's `item_type` column already separates:
- `vocab` (syn/ant words)
- `root` (root word families)
- `grammar-rule` (grammar rules)
- `grammar-mcq` (individual grammar MCQs)
- `narration` (narration sections)
- `voice` (voice sections)

The `/problems` page has tabs for each. Mock tests use this for the "Problematic Revision" preset.

## ✅ Feature 5: Narration + voice in mock tests — IMPLEMENTED

Narration (232 PYQs) and voice (329 PYQs) questions are included as test categories. The test engine loads them from `public/data/grammar/narration_questions.json` + `voice_questions.json`.

## Implementation priority (suggested vs actual)

| # | Feature | Suggested | Actual |
|---|---------|-----------|--------|
| 1 | Mock test engine (auto-generate from progress) | Highest value | ✅ Done |
| 2 | Auto-problematic from wrong answers | Small addition | ✅ Done (in submit handler) |
| 3 | Custom test series | UI-heavy | ✅ Done |
| 4 | Timer | Straightforward | ✅ Done |
| 5 | Test results review | Shows explanations | ✅ Done |

## Database additions (all implemented)

```sql
-- Saved custom test configs (user can build & reuse these)
CREATE TABLE IF NOT EXISTS test_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  config TEXT NOT NULL,         -- JSON: { categories: [{type, min, max}], single_per_item, timer_minutes, shuffle }
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_testcfg_user ON test_configs(user_id);

-- Each test attempt (auto-generated or from a saved config)
CREATE TABLE IF NOT EXISTS test_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  config TEXT NOT NULL,         -- JSON snapshot of the config used
  question_ids TEXT NOT NULL,   -- JSON array of question refs: [{type, id, itemKey, category}]
  total INTEGER NOT NULL,
  started_at INTEGER NOT NULL,
  finished_at INTEGER,          -- NULL until submitted
  score INTEGER,                -- correct count (NULL until submitted)
  timer_minutes INTEGER         -- allotted duration (NULL = untimed)
);
CREATE INDEX IF NOT EXISTS idx_testatt_user ON test_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_testatt_user_finished ON test_attempts(user_id, finished_at);

-- Per-question results for each attempt
CREATE TABLE IF NOT EXISTS test_results (
  attempt_id INTEGER NOT NULL,
  question_idx INTEGER NOT NULL,    -- 0-based position in the test
  question_type TEXT NOT NULL,      -- 'vocab' | 'grammar' | 'narration' | 'voice'
  question_id TEXT NOT NULL,        -- numeric id (vocab) or string id (grammar/narration/voice)
  item_key TEXT,                    -- the underlying word/rule-id (for auto-problematic)
  category TEXT NOT NULL,           -- test category
  selected_idx INTEGER,             -- NULL if not answered
  correct_idx INTEGER NOT NULL,
  is_correct INTEGER NOT NULL,      -- 0 or 1
  time_ms INTEGER,
  PRIMARY KEY (attempt_id, question_idx)
);
CREATE INDEX IF NOT EXISTS idx_testres_attempt ON test_results(attempt_id);
```

### Migration
Run `scripts/migrate_mock_test_tables.sh` against the live D1 database (all statements use `CREATE TABLE IF NOT EXISTS`, safe to re-run).

## What was already in place (no work needed)

- ✅ `progress.completed` tracks what's been read (the question pool)
- ✅ `problematic` table with `item_type` separation
- ✅ All grammar/narration/voice questions AI-answered + explained (for test review)
- ✅ Per-letter `wq/<letter>.json` + per-rule `qs/gr-<no>.json` for fast question loading
- ✅ Auth + per-user data isolation
- ✅ GrammarMCQCard component pattern (reused for TestCard)

## Future enhancements (not yet built)

- **Test history charts** — track score over time per category
- **Adaptive difficulty** — weight question selection by past performance
- **Shareable test configs** — let users share their custom configs with others
- **Timed vs. casual mode toggle** — quick "practice" mode without timer
- **Question pool size display** — show how many questions are available per category before starting

