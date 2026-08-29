# Changelog

Chronological log of what changed across each development session.

## Session 1 — Vocab platform (original, by previous agent)
- Built Astro + Svelte + Tailwind static site from 23 SSC exam `.txt` files
- 6 vocab modules: Stems, Options, OWS, Idioms, Homonyms, Spelling
- 4,892 questions parsed, 7,897 vocab words, frequency-ranked
- WordNet enrichment (definitions, synonyms, antonyms, mnemonics, roots)
- Deployed to `ssc-vocab-master.pages.dev`
- Source: pritammaity7/ssc-txt GitHub repo

## Session 2 — Grammar modules + gray cleanup (this agent)
### Added
- **Grammar Rules page** (`/grammar-rules`): 167 merged error-spotting rules from 3 PDFs
  - Rani Ma'am's 60 Rules (backbone, in order) + Rahul Gupta's Top 100 + Aman's 100
  - AI-merged concepts (deduped, rewritten for clarity)
  - 3,208 practice MCQs (Rani → Error PDF → PYQ order), all AI-answered + explained
  - 515 unmapped PYQs clustered into 53 new rules
- **Narration page** (`/narration`): 10 comprehensive rule sections + 232 PYQs
- **Voice page** (`/voice`): 10 comprehensive rule sections + 329 PYQs
- All grammar MCQs shown in slide/carousel (not stacked)
- AI model: claude-opus-4-8 via Justwoker API (2 keys, parallel)

### Fixed
- Gray (WordNet-added) synonyms/antonyms cleaned: AI-verified 21,880 entries, kept 11,099 valid, removed 13,926 obscure
- Exam-sourced (green/red) entries untouched

### Data pipeline
- `scripts/extract_pdfs.py` — PDF → text (pdfplumber)
- `scripts/parse_grammar_txt.py` — PYQ text → grammar questions (no Satwik)
- `scripts/structure_pdfs.py` — AI-structure each PDF (resumable)
- `scripts/merge_rules.py` — merge 3 sources
- `scripts/answer_explain.py` — AI answer + explain + map
- `scripts/create_unmapped_rules.py` — cluster unmapped
- `scripts/build_narration_voice.py` — narration + voice rule sets
- `scripts/build_grammar_data.py` — assemble final data
- `scripts/split_grammar_qs.py` — per-rule lazy loading

## Session 3 — Auth + database + problematic + progress (this agent)
### Added
- **Cloudflare D1 database** (`ssc-vocab-db`) — 4 tables: users, settings, problematic, progress
- **Pages Functions worker** (`functions/`):
  - Auth: signup, login, logout, me, signup-status
  - Admin: settings (enable/disable signup), users (list/delete)
  - Problematic: CRUD
  - Progress: read_till + completed
- **Login system**: PBKDF2 password hashing, HS256 JWT, httpOnly cookies, 1-year sessions
- **First user = admin** automatically
- **Route gating**: only `/`, `/login`, `/signup` public; all else require login (client + server)
- **Admin dashboard** (`/admin`): toggle signups, list/delete users
- **Problematic feature**: heart button on words, roots, grammar rules, narration/voice, each MCQ → `/problems` page (grouped by type)
- **Progress tracker**: "read till X" on all 9 list pages
- **Word detail pages** (`/word/[word]`, 7,897 pages): definition, Bengali, mnemonic, root, syn/ant, MCQ slider
- **Pronunciation**: dictionaryapi.dev (real audio + IPA), Web Speech fallback
- **Page button** on each word card to open detail page
- **Compact circular avatar** header (replaced wide email button)

### Fixed
- Grammar MCQs converted to slide/carousel view

### Database
- `scripts/schema.sql` — D1 schema
- Migration: added `completed TEXT` column to `progress` (for range tracking)

## Session 4 — Rename + speed optimization (this agent)
### Changed
- Renamed site: SSC Vocab Master → SSC PYQs
- New Cloudflare project: `sscpyqs` (old `ssc-vocab-master` deleted)
- Updated wrangler.toml, package.json, README, Layout brand/title/footer
- D1 database reused (user data preserved)

### Speed optimization (major)
- Split `questions.json` (2.45MB) → per-letter `wq/<letter>.json` (~230KB each, cached) — **13× smaller** per word expansion
- Dashboard: `top_words.json` (6.8KB) instead of `words.json` (2.2MB) — **300× smaller**
- `functions/data/_middleware.ts` — long cache headers on `/data/*.json` (browser 1 day + CDN 30 days, was `max-age=0`)
- Deleted 12.2MB dead `enriched.json` master
- Result: home 0.05s, word page 0.28s, grammar-rules 0.31s (was multi-second)

### Added
- **Range "From/To/Set Done"** input on ProgressTracker (all 9 list pages)
- ProblematicButton on RootsView + inline word expansions (was only on dedicated word pages)

## Session 5 — Auth race + header + word-page fixes (this agent)
### Fixed
- **Auth race condition**: ProblemsView + ProgressTracker checked `isLoggedIn()` synchronously before session loaded → showed "please log in" / hid progress bar for logged-in users. Fix: `await loadSession()` in onMount + `onAuthChange` subscription.
- **Word page stuck on "Loading…"**: route-gate redirected on network timing hiccups. Fix: `cache: 'no-store'` + only redirect on definitive no-user response.
- **Header now static** (removed `sticky top-0` so it scrolls with the page)

### Pushed to GitHub
- All commits pushed to `sujitbhai7710/ssc-vocab-master` (main branch)

## Session 6 — Documentation (this session)
### Added
- `scripts/` — full data pipeline (sanitized: API keys → env vars)
- `scripts/work-data/` — intermediate pipeline outputs (for reproducibility)
- `docs/` — comprehensive documentation (this folder)
- `worklog.md` — session-by-session work log
- `.gitignore` updated to block `.env`, `jwt_secret.txt`
- `scripts/.env.example` — template for secrets

## Session 7 — Mock Test System (this agent)
### Added — full mock test platform (all 5 features from the original FUTURE_ROADMAP)
- **Mock test engine** — auto-generates tests from user's `progress.completed` set
  - 4 presets: Quick Mix (25Q/12min), Syn-Ant Focus (50Q/24min), Problematic Revision (20Q untimed), Grammar+Narration+Voice (40Q/19min)
  - Single-MCQ-per-item by default (toggleable)
  - Shuffle question order
- **Auto-problematic from wrong answers** — on submit, each wrong answer auto-adds to `problematic` table with `sub_type = category`
- **Custom test series** — `/tests/custom` page with per-category min/max range inputs, save/edit/delete configs
- **SSC-style timer** — 25Q/12min ratio (0.48 min/Q), auto-calc, customizable override, auto-submit on timeout
- **Test results review** — score summary, per-category breakdown bar chart, per-question review with explanations, filter by correct/wrong/skipped

### Database additions (3 new tables)
- `test_configs` — saved custom configs (named, reusable)
- `test_attempts` — each test run (config snapshot, question refs, score, timer)
- `test_results` — per-question results (selected idx, correct idx, is_correct, time_ms)
- Migration script: `scripts/migrate_mock_test_tables.sh` (idempotent, safe to re-run)

### Architecture
- `functions/_lib/test-engine.ts` — question pool builder, generator, scorer, auto-problematic logic
- `functions/api/test/{generate,[id],submit,list}.ts` + `configs/index.ts` — 5 API endpoints
- `src/lib/test-api.ts` — client API + AUTO_PRESETS + CATEGORIES metadata
- `src/components/{TestList,TestRunner,TestResults,TestCard,CustomTestBuilder}.svelte` — 5 Svelte components
- `src/pages/{tests,test,test-results}.astro` + `tests/custom.astro` — 4 pages
- Added "Tests" nav link in header + Tests module card on Dashboard

### Security
- All `/api/test/*` endpoints require auth (`requireUser`)
- Correct answers looked up **server-side** from `/data/*.json` — client only sends selected option index (no cheating)
- Per-user isolation (can't access other users' tests/configs)
- SQL parameterized throughout

### Commits
- `1ecb164` — feat: mock test system (main feature, 345+ files)
- `71b672b` — fix: rename `validateTestConfig` → `validateConfig` to match actual export (wrangler bundler caught it; tsc didn't)

## Session 8 — UI bug fixes (this agent, current session)
### Fixed — 6 user-reported bugs
1. **Mobile hamburger menu** — header nav had 13 items that overflowed/wrapped badly on mobile. New `Nav.svelte` component with:
   - Desktop (sm+): horizontal nav bar (unchanged)
   - Mobile (<sm): hamburger button reveals full dropdown with all 13 items, outside-click/escape closes
   - Replaced ~50 lines of inline nav in `Layout.astro` with `<Nav client:load activeNav={activeNav} />`

2. **Word page slow loading** (`/word/defamation/` etc.) — root cause: `WordDetailView.svelte` referenced undefined variables `stemQuestionIds` and `optionQuestionIds` (actual vars are `stemQuestions`/`optionQuestions`), throwing a JS error on hydration → page stuck on spinner forever. Also `client:load` blocked render. Fixes:
   - Renamed `stemQuestionIds` → `stemQuestions`, `optionQuestionIds` → `optionQuestions`
   - Changed `client:load` → `client:idle` (defer hydration until browser is idle)
   - Added SSR-friendly fallback: word header + spinner renders immediately in initial HTML (no blank white flash)
   - Added breadcrumb in the `.astro` page itself (was only in the Svelte component)

3. **Yellow color revealing answer before clicking** — `MCQCard.svelte` had a `hi && !answered` branch that highlighted the `highlightWord` option in amber BEFORE the user clicked. For OWS where the answer word IS the highlightWord, this revealed the answer. Fix: removed the `hi && !answered` branch entirely — all options are now neutral until click.

4. **OWS: question stem = answer** — for OWS questions, the data has `stem` = "Atheist" (the answer word) and `sent` = "A person who does not believe in God" (the actual question text). The old code showed `stem` as the question, making the answer obvious (since "Atheist" was also option A). Fix: for OWS, show `sent` (the description) as the question with a "Find the one-word substitute for:" label — NEVER show `stem`.

5. **Idioms: half of questions not showing stem** — for idioms where `sent` equals `stem` (both are just the idiom phrase, no context sentence), the old code showed nothing or showed the idiom itself (revealing the answer). Fix: detect this case (`idiomIsStemOnly`) and show "What does this idiom mean?" prompt instead — never show the idiom phrase itself when it's also the answer.

6. **Homonyms: pair not shown before question** — user wanted the set of similar-sounding words (the options, e.g. `accept / expect / expert`) shown as a heading BEFORE the question, with show/hide toggle. Fix: added a collapsible "Confused pair (homophones)" heading at the top of every homonym MCQ:
   - Collapsed by default (so user can test themselves)
   - Click "Show" → reveals the sorted, deduped pair joined with middle dots
   - Resets to collapsed when navigating to a new question
   - Pink color theme to match the homonym category

### Files changed
- `src/components/Nav.svelte` (NEW) — mobile-aware nav with hamburger
- `src/layouts/Layout.astro` — replaced inline nav with `<Nav />` component
- `src/components/WordDetailView.svelte` — fixed undefined refs, SSR fallback
- `src/pages/word/[word].astro` — `client:load` → `client:idle`, added breadcrumb
- `src/components/MCQCard.svelte` — removed yellow reveal, rewrote question display logic per qtype, added homonym pair heading

### Commits
- (this session) — feat: fix mobile menu, word page speed, MCQ yellow reveal, OWS/idiom display, homonym pair heading
