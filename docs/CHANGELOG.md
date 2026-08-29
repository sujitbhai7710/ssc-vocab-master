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
