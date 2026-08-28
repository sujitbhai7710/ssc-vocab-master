# SSC Vocab Master 📚

A feature-rich, blazing-fast vocabulary platform covering **every synonym, antonym, and one-word substitution question** from 5 years of SSC exams (2019–2026). Built with **Astro + Svelte + Tailwind CSS** and deployed to **Cloudflare Pages**.

## ✨ Features

- **23 SSC exam papers** parsed (CGL Tier-1/2, CHSL, CPO, MTS — 2019 to 2026)
- **2,549 questions** extracted (synonyms, antonyms, one-word substitutions)
- **6,132 unique vocabulary words** with frequency tracking
- Frequency badges on every word: `Main Question: X times | Option Choice: Y times`
- Module 1 — Words that appeared as Main Question Stems (sorted most-repeated → least)
- Module 2 — Words that appeared as Option Choices (sorted most-repeated → least)
- Word detail page with definition, SSC synonyms/antonyms, example, mnemonic, root words, and up to 5 actual past SSC MCQs with reveal-answer buttons
- Search, sort, filter by exam, and pagination
- 100% English content (per spec)
- Mobile-first responsive design
- Sub-second page loads (static site on Cloudflare CDN)

## 🏗️ Tech Stack

- **[Astro 5](https://astro.build)** — Static site generator with island architecture
- **[Svelte 5](https://svelte.dev)** — Reactive UI components (with runes)
- **[Tailwind CSS 3](https://tailwindcss.com)** — Utility-first styling
- **[Cloudflare Pages](https://pages.cloudflare.com)** — Global CDN hosting
- **[NLTK WordNet](https://www.nltk.org)** — Definitions, POS, synonyms, antonyms

## 📁 Project Structure

```
ssc-vocab-astro/
├── astro.config.mjs        # Astro config (static output + Svelte + Tailwind)
├── tailwind.config.mjs     # Tailwind theme
├── tsconfig.json
├── wrangler.toml           # Cloudflare Pages config
├── package.json
├── public/
│   └── data/               # Pre-built JSON datasets served statically
│       ├── summary.json
│       ├── words.json             # 6,132 word entries
│       ├── questions.json         # 2,549 questions
│       ├── word_questions.json    # word → question IDs mapping
│       └── enriched/
│           └── enriched_*.json    # per-letter definitions + mnemonics
├── data-source/           # Original SSC .txt files (from pritammaity7/ssc-txt)
│   └── SSC_*_EN.txt
├── scripts/               # Python data pipeline (regenerates public/data/)
│   ├── parse_ssc.py
│   ├── enrich_vocab.py
│   ├── build_word_questions.py
│   └── split_enriched.py
└── src/
    ├── env.d.ts
    ├── layouts/
    │   └── Layout.astro
    ├── components/
    │   ├── App.svelte             # Root stateful component (view router)
    │   ├── Dashboard.svelte
    │   ├── WordListView.svelte
    │   ├── WordCard.svelte
    │   ├── WordDetail.svelte
    │   ├── MCQCard.svelte
    │   └── FrequencyBadge.svelte
    ├── lib/
    │   └── vocab-data.ts          # Typed data loaders + caches
    ├── pages/
    │   └── index.astro
    └── styles/
        └── global.css
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ (or Bun)
- Python 3.9+ (only if regenerating data files)

### Install & run locally
```bash
npm install
npm run dev
# → http://localhost:4321
```

### Build for production
```bash
npm run build
# Output is in ./dist
```

### Preview the production build
```bash
npm run preview
```

## 🔄 Regenerating the Vocabulary Data

If you want to re-parse the SSC source files (e.g. new papers added):

```bash
# 1. Parse SSC .txt files → questions + words
python3 scripts/parse_ssc.py

# 2. Enrich words with WordNet definitions, synonyms, antonyms, mnemonics
python3 scripts/enrich_vocab.py

# 3. Build word → question mapping
python3 scripts/build_word_questions.py

# 4. Split enriched.json by letter (for lazy loading)
python3 scripts/split_enriched.py
```

All output goes to `public/data/`. The Astro app fetches these files at runtime.

## ☁️ Deploy to Cloudflare Pages

### Option A: Wrangler CLI (recommended for CI/CD)

```bash
# Set your Cloudflare API token (use CLOUDFLARE_API_TOKEN env var)
export CLOUDFLARE_API_TOKEN=cfk_xxxxxxxx
export CLOUDFLARE_ACCOUNT_ID=your-account-id  # optional if token is scoped

# One-shot deploy
npm run deploy

# Or step by step
npm run build
npx wrangler pages deploy ./dist --project-name=ssc-vocab-master
```

### Option B: Cloudflare Dashboard

1. Push this repo to GitHub
2. Go to Cloudflare Pages → Create a project → Connect to Git
3. Set build command: `npm run build`
4. Set output directory: `dist`
5. Deploy 🚀

## 📊 Sample Dataset Stats

- Total SSC papers parsed: 23
- Total questions parsed: 2,549
- Total synonym/antonym questions: 2,272
- Total one-word substitution questions: 277
- Unique vocabulary words: 6,132

### Top 5 Question Stems
| Word | Stem Count | Option Count |
|------|------------|--------------|
| Harmony | 6 | 11 |
| Benevolent | 5 | 5 |
| Magnificent | 5 | 4 |
| Absurd | 5 | 3 |
| Reluctant | 5 | 2 |

### Top 5 Option Choices
| Word | Stem Count | Option Count |
|------|------------|--------------|
| Trivial | 3 | 15 |
| Atheist | 0 | 15 |
| Humble | 2 | 14 |
| Modest | 0 | 14 |
| Ordinary | 0 | 14 |

## 📝 License

This project is for educational use by SSC aspirants. The SSC exam content (questions) is property of the Staff Selection Commission of India — this tool only aggregates vocabulary statistics.

## 🙏 Acknowledgements

- [pritammaity7/ssc-txt](https://github.com/pritammaity7/ssc-txt) — Source SSC paper text files
- [NLTK WordNet](https://www.nltk.org) — Definitions and synonyms
- [Astro](https://astro.build), [Svelte](https://svelte.dev), [Tailwind CSS](https://tailwindcss.com)
