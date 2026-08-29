# Future Roadmap — Mock Tests & Custom Series

This document captures the user's planned features (shared in session 3) and how the current database + architecture already supports them. **None of this is built yet** — it's the spec for future implementation.

## User's vision (verbatim summary)

> In future we will make mock tests. Questions I get wrong will auto-send to problems. Each will have separate problematic things (syn/ant, idiom, spelling, homonym, grammar, etc.). Also allow removing problematic.
>
> For example: first day I read 1-20 vocab, then I can set "read till X" for any page (even grammar rules) to track progress. When we add mock tests, based on my progress, multiple test series will show — mixtures/random questions of just syn/ant which I still haven't read, or idioms, or homonyms, or grammar — anything. It will only add a single MCQ per vocab (no multiple for single vocab). User can set if they want multiple from a single vocab/rule or not.
>
> User can make custom test series based on performance — e.g. if I read till 100 questions of each vocab, I can set like 40-70 questions of syn/ant, 80-100 questions of idioms, or grammar rules 20-30. User can set a timer: SSC gives 25 questions in 15 minutes, so we give 12 minutes max for 25. If 100 questions selected, 48 minutes auto-set. But customizable.
>
> Same for narration and voice.

## Feature 1: Mock tests (auto-generated from progress)

### Concept
Based on the user's `progress.completed` set (what they've marked as "read"), the system auto-generates test series that quiz them on material they've covered but might be forgetting.

### Rules
- **Single MCQ per vocab word** by default — pick one question per word (not all questions for that word). User can toggle "multiple from single vocab/rule" off/on.
- **Only include words/rules the user has marked as read** (in their `progress.completed` set for that page_type).
- **Mixed/random** — questions can come from any category (syn/ant, idioms, spelling, homonyms, grammar, narration, voice) or be filtered to specific categories.
- **Auto-problematic on wrong answer** — if the user answers wrong, that question's vocab/rule auto-adds to `problematic` (with sub_type = the test category).

### Suggested implementation
```
New DB tables (not yet created):
  test_attempts   (id, user_id, config JSON, started_at, finished_at, score)
  test_results    (attempt_id, question_id, selected_idx, correct bool, time_ms)

New worker endpoints:
  POST /api/test/generate  { categories: [...], count: N, single_per_item: bool }
    → picks random questions from user's completed sets, returns a test session
  POST /api/test/submit     { attempt_id, answers: [...] }
    → scores, stores results, auto-adds wrong answers to problematic

New pages:
  /tests          — list of auto-generated + custom test series
  /test/[id]      — take a test (timer, one question at a time or all)
  /test/[id]/results — review answers, see explanations
```

### How the current schema supports it
- `progress.completed` (JSON array of indices) already tracks what the user has read per page_type → use as the question pool
- `problematic` table already has `item_type` + `item_key` + `sub_type` → auto-add wrong answers with sub_type = test category
- The `grammar_rules` + `qs/gr-<no>.json` lazy-loading pattern extends to test questions

## Feature 2: Custom test series

### Concept
The user configures their own test: pick categories + question ranges based on what they've studied.

### Example config
```
Categories:
  - syn/ant:     40-70 questions  (from progress.completed in 'stems'/'options')
  - idioms:      80-100 questions (from progress.completed in 'idioms')
  - grammar:     20-30 rules      (from progress.completed in 'grammar-rules')
  - narration:   10-15 questions
  - voice:       10-15 questions
Total: ~160-230 questions
```

### Timer (SSC pattern)
- SSC: 25 questions in 15 minutes = **0.6 min/question**
- Auto-calc: `total_questions × 0.6 minutes` (e.g. 100 questions → 60 min... user said 48 min for 100, so maybe 0.48 min/Q — confirm the SSC ratio)
- User said: "25 question 15 min, we give 12 min max" → so the ratio is `12/25 = 0.48 min/question`
- 100 questions → `100 × 0.48 = 48 minutes` (matches user's example)
- **Customizable** — user can override the auto-calculated time

### Suggested implementation
```
New DB table:
  test_configs  (id, user_id, name, config JSON, created_at)
    config = {
      categories: [{ type: 'stems', min: 40, max: 70 }, ...],
      single_per_item: true,
      timer_minutes: 48,  // auto = sum × 0.48, overridable
      shuffle: true
    }

New page:
  /tests/custom  — build a custom test config (sliders for each category range)
```

## Feature 3: Auto-problematic from wrong answers

### Concept
When a user gets a test question wrong, the underlying vocab word / grammar rule auto-adds to their `problematic` list (so it surfaces for revision).

### Rules
- Wrong answer → `INSERT INTO problematic (user_id, item_type, item_key, sub_type)` 
  - `item_type` = 'vocab' / 'grammar-rule' / etc. (derived from the question)
  - `item_key` = the word/rule-id
  - `sub_type` = the test category (e.g. 'syn-ant', 'narration')
- Deduped automatically (UNIQUE constraint on user_id + item_type + item_key)
- User can still manually remove from `/problems`

### Suggested implementation
In the test submit handler:
```ts
// functions/api/test/submit.ts
for (const answer of answers) {
  if (!answer.correct) {
    const { itemType, itemKey } = deriveFromQuestion(answer.questionId);
    await ctx.env.DB.prepare(
      'INSERT INTO problematic (user_id, item_type, item_key, sub_type, created_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING'
    ).bind(uid, itemType, itemKey, answer.category, Date.now()).run();
  }
}
```

## Feature 4: Per-category problematic (already done ✓)

The `problematic` table's `item_type` column already separates:
- `vocab` (syn/ant words)
- `root` (root word families)
- `grammar-rule` (grammar rules)
- `grammar-mcq` (individual grammar MCQs)
- `narration` (narration sections)
- `voice` (voice sections)

The `/problems` page already has tabs for each. For mock tests, filter problematic by `item_type` to generate "revision tests" of only problematic items.

## Feature 5: Narration + voice in mock tests

Same as grammar — narration (232 PYQs) and voice (329 PYQs) questions are already in `public/data/grammar/narration_questions.json` + `voice_questions.json`. The test generator can include them by category.

## Implementation priority (suggested)

1. **Mock test engine** (auto-generate from progress) — highest value, uses existing data
2. **Auto-problematic from wrong answers** — small addition to the submit handler
3. **Custom test series** — UI-heavy (range sliders per category)
4. **Timer** — straightforward once the test page exists
5. **Test results review** — shows explanations (already in data)

## Database additions needed (when building)

```sql
CREATE TABLE test_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  config TEXT NOT NULL,        -- JSON: categories, count, timer, etc.
  question_ids TEXT NOT NULL,  -- JSON array of question IDs in this test
  started_at INTEGER NOT NULL,
  finished_at INTEGER,
  score INTEGER                -- correct count
);

CREATE TABLE test_results (
  attempt_id INTEGER NOT NULL,
  question_id TEXT NOT NULL,
  question_type TEXT NOT NULL, -- 'vocab' | 'grammar-rule' | etc.
  selected_idx INTEGER,
  correct INTEGER NOT NULL,    -- 0 or 1
  time_ms INTEGER,
  PRIMARY KEY (attempt_id, question_id)
);

CREATE TABLE test_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  config TEXT NOT NULL,        -- JSON
  created_at INTEGER NOT NULL
);
```

## What's already in place (no work needed)

- ✅ `progress.completed` tracks what's been read (the question pool)
- ✅ `problematic` table with `item_type` separation
- ✅ All grammar/narration/voice questions AI-answered + explained (for test review)
- ✅ Per-letter `wq/<letter>.json` + per-rule `qs/gr-<no>.json` for fast question loading
- ✅ Auth + per-user data isolation
- ✅ GrammarMCQCard component (reusable for test questions — click-to-reveal, but tests need a "submit all at end" variant)
