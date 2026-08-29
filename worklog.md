# Worklog — SSC Vocab Master: Grammar + Gray cleanup

---
Task ID: ALL (single-agent run)
Agent: Super Z (main)
Task: Extend the SSC Vocab Master Astro site with Grammar Rules, Narration, Voice pages (merged from 3 PDFs + PYQs, AI-answered/explained), and clean gray WordNet synonyms/antonyms via AI.

Work Log:
- Cloned pritammaity7/ssc-txt (23 SSC papers + 3 grammar PDFs) and the existing ssc-vocab-master Astro+Svelte project from GitHub.
- Built ai_helper.py: justwoker.icu API (claude-opus-4-8 → claude-opus-5), 2 keys round-robined in parallel, retry+backoff. Fixed Cloudflare 1010 by adding browser User-Agent.
- extract_pdfs.py: pdfplumber → rani-maam.txt (60 Rules, scrambled 2-col), error-spotting.txt (Top 100 Rules + 300 Qs), 100-grammar-rules.txt (Aman, 100 concepts).
- parse_grammar_txt.py: parsed 23 raw txt files (NO Satwik data) → 1077 error, 1085 improvement, 232 narration, 329 voice PYQs.
- structure_pdfs.py: parallel chunked AI extraction (resumable) → rani 64 rules/790 Qs, error 100 rules/300 Qs, aman 101 rules/363 examples.
- merge_rules.py: 60-rule Rani backbone (deduped from 64) + matched 143 candidates + 54 new rules = 114 merged rules, clean combined concepts.
- answer_explain.py: AI answered+explained 1090 PDF Qs (verified answers) + 2162 PYQs (answers+explanations+rule mapping).
- create_unmapped_rules.py: clustered 515 unmapped Qs → 53 new rules. Final: 167 rules, 0 unmapped.
- build_narration_voice.py: 10 narration sections + 10 voice sections (comprehensive, synthesised from Wren&Martin/Rani/Adda/Testbook), all 232+329 PYQs answered+explained+mapped.
- build_grammar_data.py + split_grammar_qs.py: assembled public/data/grammar/ (rules.json, questions.json 3208 Qs, per-rule qs/ files, narration/voice, summary). Deduped, ordered rani→error→pyq.
- Built Astro pages: GrammarRulesView (lazy per-rule MCQ loading), GrammarMCQCard, TopicRulesView, TopicLanding. Pages: /grammar-rules, /narration + /narration/[slug]×10, /voice + /voice/[slug]×10. Updated Layout nav + Dashboard modules.
- fix_gray.py: AI-verified all 21,880 clean gray (WordNet-added) syn/ant entries (100% coverage, 4 cycles with git-restore resume). Kept 11,099 verified-common (9,621 syn + 1,478 ant), dropped 13,926 obscure/invalid. Exam-sourced correct/distractor untouched. Rewrote 26 per-letter enriched files + master.
- Built (31 pages) + deployed to Cloudflare Pages (global key cfk_30U3…/akaprantikdas@gmail.com), project ssc-vocab-master.

Stage Summary:
- Live: https://ssc-vocab-master.pages.dev
- Grammar Rules: 167 merged rules (Rani 60 order + 54 new + 53 from unmapped PYQ clustering) with 3,208 practice MCQs (Rani→Error PDF→PYQ), all AI-answered+explained, lazy-loaded per rule.
- Narration: 10 comprehensive sections + 232 PYQs (answered+explained+mapped).
- Voice: 10 comprehensive sections + 329 PYQs (answered+explained+mapped).
- Gray syn/ant cleaned: only AI-verified-common entries remain; obscure WordNet noise removed.
- AI model used throughout: claude-opus-4-8 (claude-opus-5) via api.justwoker.icu, 2 keys in parallel.

---
Task ID: AUTH+DB
Agent: Super Z (main)
Task: Make the SSC Vocab Master site login-based with a Cloudflare D1 database + Pages Functions worker, admin dashboard, problematic items, progress tracking, word detail pages, enhanced pronunciation, and grammar MCQ slider.

Work Log:
- Discovered the `cfk_` global key works as X-Auth-Email + X-Auth-Key (not Bearer). Got account ID 448154c5d61fdb71ea8a752b5bcb3b3d.
- Created D1 database `ssc-vocab-db` (uuid 9e974122...) via API; initialized schema (users, settings, problematic, progress) via D1 query API.
- Key learning: D1 bindings set via deployment_configs API DON'T persist; must declare `[[d1_databases]]` in wrangler.toml. Added binding + JWT_SECRET env var.
- Built Pages Functions worker (functions/): _lib/auth.ts (PBKDF2 password hashing + HS256 JWT via Web Crypto, httpOnly cookie, 1-year session); api/auth/{signup,login,logout,me,signup-status}; api/admin/{settings,users}; api/problematic; api/progress. Server-side auth on all user-data endpoints.
- Frontend: src/lib/auth.ts (client API + route gating); AuthGate, AuthBar, AuthForm components; /login + /signup pages; inline route-gate script in Layout (redirects to /login before paint for non-public pages; only /, /login, /signup are public).
- Admin dashboard (/admin): toggle signup enabled/disabled, list users, delete users (can't delete self / last admin). First signup becomes admin automatically.
- Pronunciation: researched free APIs → dictionaryapi.dev (real human recordings + IPA, no key) is best. Rewrote pronounceWord to fetch dictionary audio+IPA, fall back to Web Speech API. Caches per word.
- Word detail pages: created /word/[word] (7,897 static pages) with WordDetailView (definition, Bengali, mnemonic, root, syn/ant chips, MCQ slider, pronunciation button + IPA display). Added "Page" button in WordAccordion to open each word's own page.
- Grammar MCQs: converted from stacked list to slide/carousel (single card + Prev/Next + counter) matching the vocab slider.
- Problematic feature: ProblematicButton on word pages, grammar rules, narration/voice sections, and each grammar MCQ. /problems page groups items by type (vocab, grammar rules, narration, voice, grammar-mcq) with remove. Schema supports per-type sub_type for future mock-test wrong-answer auto-add.
- Progress tracker: ProgressTracker ("read till X") on stems, options, ows, idioms, homonyms, spelling, grammar-rules, narration, voice. Persists per page_type to D1. Progress bar + quick-set buttons (25/50/100/200).
- Database foundation ready for future mock tests (single-MCQ-per-vocab, custom test series, SSC timer 25Q/12min → 100Q/48min) — schema designed to support it.

Stage Summary:
- Live: https://ssc-vocab-master.pages.dev (7,932 pages + Pages Functions worker + D1)
- Auth: signup/login/logout, first user=admin, persistent 1-year session, home-only public, all else gated.
- Admin: enable/disable signup, list/delete users.
- Database: Cloudflare D1 (ssc-vocab-db), 4 tables, JWT_SECRET env.
- New pages: /login, /signup, /admin, /problems, /word/[word] (×7897).
- Pronunciation: dictionaryapi.dev real audio + IPA, Web Speech fallback.
- Grammar MCQs now slide; word pages work; problematic + progress persist per user.

---
Task ID: SPEED+UI-FIXES
Agent: Super Z (main)
Task: Fix missing problematic/progress on OWS/Idioms/Homonyms/Spelling/Roots/Options, add range "from-to set done" input, compact circular header avatar, and major speed optimization. Research Monid.ai.

Work Log:
- Monid: installed CLI (@monid-ai/cli 0.1.6), read SKILL.md. It's a data-endpoint discovery tool (scraping/external data) — needs an API key from app.monid.ai which the user hasn't pasted yet. Not applicable to my own site's speed (bottlenecks were in my code, found via direct analysis).
- Speed root cause: every word expansion fetched the FULL questions.json (2.45MB) + word_questions.json (414KB) = 2.9MB; dashboard fetched words.json (2.2MB); enriched.json master (12.2MB) was dead weight; no cache headers (max-age=0).
- split_word_questions.py: created /data/wq/<letter>.json (26 files, ~229KB each) with per-word question objects; /data/top_words.json (6.8KB) for dashboard; deleted 12.2MB enriched.json master.
- vocab-data.ts: added loadWordQuestions(word) (per-letter, cached) + loadTopWords(). Updated WordExpansion, WordDetailView, WordAccordion to use the fast path. Dashboard now uses loadTopWords. WordDetailView receives word entry as prop (no loadWords). Removed unused loadQuestions import from WordAccordion.
- functions/data/_middleware.ts: long cache headers on /data/*.json (browser max-age=86400 + stale-while-revalidate=604800, CDN 30 days).
- ProblematicButton: added to WordExpansion (inline expansion on ALL list pages — stems/options/ows/idioms/homonyms/spelling) and RootsView. Was previously only on the dedicated /word/[word] page.
- ProgressTracker: added to roots.astro (was missing). Rewrote with "From / To / Set Done" range input + completed count / progress bar + reset. Applied to all pages (stems, options, ows, idioms, homonyms, spelling, roots, grammar-rules, narration, voice).
- DB: ALTER TABLE progress ADD COLUMN completed TEXT (JSON array of completed indices). Updated progress API to support range [from,to] additions + reset_completed. Client auth.ts: added saveProgressRange + resetProgressCompleted.
- AuthBar: rewritten as compact 8x8 circular avatar (initial) with click-to-open dropdown (email, Problems, Admin, Logout). Outside-click/escape closes. Saves header space.
- ProblemsView: added root + grammar-mcq tabs; linkFor handles new types.

Stage Summary:
- Live: https://sscpyqs.pages.dev
- Speed: home 0.05s, word page 0.28s, grammar-rules 0.31s. Data payloads: dashboard 2.2MB→6.8KB (300×), word expansion 2.9MB→229KB cached (13×), 12.2MB dead file removed. Cache headers set.
- Problematic button now on all list-page word expansions + roots + grammar + narration/voice + each grammar MCQ.
- Progress "From/To/Set Done" range input on all 9 list pages; persists completed-index set per page_type in D1.
- Compact circular avatar header (was wide email-text button).
- Monid CLI installed; needs user's API key (from app.monid.ai) for external-data research tasks.
