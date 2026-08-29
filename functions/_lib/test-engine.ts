// functions/_lib/test-engine.ts
// Shared mock-test engine: builds question pools from the user's progress,
// generates random tests, scores submissions, and auto-adds wrong answers
// to the problematic table.
//
// All static content (vocab, grammar, narration, voice) lives in
// /data/*.json files served from public/data/. The worker fetches them
// at runtime via the same Cloudflare CDN (same origin, fast).
//
// Categories supported (matches the existing page_type / item_type taxonomy):
//   'syn-ant'   -> vocab synonym/antonym (from progress.completed in 'stems'/'options')
//   'ows'       -> vocab one-word substitution (from progress.completed in 'ows')
//   'idiom'     -> vocab idioms (from progress.completed in 'idioms')
//   'homonym'   -> vocab homonyms (from progress.completed in 'homonyms')
//   'spelling'  -> vocab spelling (from progress.completed in 'spelling')
//   'grammar'   -> grammar rule MCQs (from progress.completed in 'grammar-rules')
//   'narration' -> narration PYQs (from progress.completed in 'narration')
//   'voice'     -> voice PYQs (from progress.completed in 'voice')

import { Env } from './auth';

// ---- Types ----

export interface TestCategorySpec {
  type: string;        // one of the 8 categories above
  min: number;         // min questions to draw from this category
  max: number;         // max questions to draw from this category
}

export interface TestConfig {
  categories: TestCategorySpec[];
  single_per_item: boolean;  // if true: at most 1 MCQ per word/rule (default true)
  timer_minutes: number | null;  // null = untimed
  shuffle: boolean;          // shuffle question order
  source?: 'auto' | 'problematic' | 'custom';  // where the pool comes from
  name?: string;             // for saved configs
}

export interface QuestionRef {
  type: 'vocab' | 'grammar' | 'narration' | 'voice';
  id: string;            // numeric id (vocab) or string id (grammar/narration/voice)
  itemKey: string;       // the underlying word/rule-id/section-id (for auto-problematic)
  category: string;      // test category
}

export interface TestAttempt {
  id: number;
  user_id: number;
  config: TestConfig;
  question_ids: QuestionRef[];
  total: number;
  started_at: number;
  finished_at: number | null;
  score: number | null;
  timer_minutes: number | null;
}

// Map of page_type -> test category
const PAGE_TYPE_TO_CATEGORY: Record<string, string> = {
  stems: 'syn-ant',
  options: 'syn-ant',
  ows: 'ows',
  idioms: 'idiom',
  homonyms: 'homonym',
  spelling: 'spelling',
  'grammar-rules': 'grammar',
  narration: 'narration',
  voice: 'voice',
};

// Map of test category -> item_type for the problematic table
const CATEGORY_TO_ITEM_TYPE: Record<string, string> = {
  'syn-ant': 'vocab',
  'ows': 'vocab',
  'idiom': 'vocab',
  'homonym': 'vocab',
  'spelling': 'vocab',
  'grammar': 'grammar-mcq',
  'narration': 'narration',
  'voice': 'voice',
};

// ---- Fetch helpers (worker-side) ----

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return (await res.json()) as T;
}

// ---- Progress lookup ----

export async function loadUserProgress(env: Env, userId: number): Promise<Record<string, number[]>> {
  const rows = await env.DB.prepare('SELECT page_type, completed FROM progress WHERE user_id = ?').bind(userId).all<{
    page_type: string; completed: string | null;
  }>();
  const out: Record<string, number[]> = {};
  for (const r of rows.results || []) {
    try { out[r.page_type] = r.completed ? JSON.parse(r.completed) : []; } catch { out[r.page_type] = []; }
  }
  return out;
}

export async function loadUserProblematic(env: Env, userId: number, itemType?: string): Promise<Array<{ item_type: string; item_key: string; sub_type: string | null }>> {
  let stmt;
  if (itemType) {
    stmt = env.DB.prepare('SELECT item_type, item_key, sub_type FROM problematic WHERE user_id = ? AND item_type = ?').bind(userId, itemType);
  } else {
    stmt = env.DB.prepare('SELECT item_type, item_key, sub_type FROM problematic WHERE user_id = ?').bind(userId);
  }
  const rows = await stmt.all<{ item_type: string; item_key: string; sub_type: string | null }>();
  return rows.results || [];
}

// ---- Question pool builders ----
// Each returns a list of { questionId, itemKey } pairs. The actual question
// payload (stem, options, correctIdx, explanation) is fetched on the client side
// when taking the test — only refs are stored in the DB.

interface VocabQuestion { id: number; qtype: string; stem: string; options: string[]; correctIdx?: number; }

// Per-letter wq/<letter>.json shape: { word: { asStem: VocabQuestion[], asOption: VocabQuestion[] } }
type WqLetterFile = Record<string, { asStem: VocabQuestion[]; asOption: VocabQuestion[] }>;

// Build pool for a vocab category (syn-ant, ows, idiom, homonym, spelling).
// Uses the user's completed indices in the corresponding page_type(s) to pick words.
async function buildVocabPool(
  env: Env,
  userId: number,
  category: string,
  source: 'auto' | 'problematic',
  progress: Record<string, number[]>,
  problematic: Array<{ item_type: string; item_key: string }>,
): Promise<QuestionRef[]> {
  const pool: QuestionRef[] = [];
  // Determine which page_types feed this category
  const pageTypes: string[] = category === 'syn-ant' ? ['stems', 'options'] : [category];
  // Determine the qtypes to include
  const qtypes: string[] = category === 'syn-ant' ? ['synonym', 'antonym'] : [category === 'idiom' ? 'idiom' : category === 'homonym' ? 'homonym' : category === 'spelling' ? 'spelling' : 'one-word'];

  if (source === 'problematic') {
    // Use problematic vocab items — load each word's questions
    const probWords = problematic.filter(p => p.item_type === 'vocab').map(p => p.item_key.toLowerCase());
    if (probWords.length === 0) return [];
    // Group by letter for efficient fetching
    const byLetter: Record<string, string[]> = {};
    for (const w of probWords) {
      const letter = (w[0] || '_').toLowerCase();
      if (!byLetter[letter]) byLetter[letter] = [];
      byLetter[letter].push(w);
    }
    for (const [letter, words] of Object.entries(byLetter)) {
      try {
        const data = await fetchJson<WqLetterFile>(`/data/wq/${letter}.json`);
        for (const w of words) {
          const entry = data[w];
          if (!entry) continue;
          const allQs = [...(entry.asStem || []), ...(entry.asOption || [])];
          // filter by qtype
          const matching = allQs.filter(q => qtypes.includes(q.qtype));
          for (const q of matching) {
            pool.push({ type: 'vocab', id: String(q.id), itemKey: w, category });
          }
        }
      } catch { /* letter file missing — skip */ }
    }
    return pool;
  }

  // source === 'auto' — use progress.completed indices to pick words
  // We need the words list (words.json) to map indices -> words
  // But words.json is 2.2MB — too big to fetch in worker every time.
  // Strategy: fetch the per-letter word files (words/<letter>.json) only for letters
  // that contain completed words. But we don't know which letters without the index map.
  //
  // Simpler approach: words.json IS cached on the CDN (1 day browser + 30 day CDN per _middleware).
  // The worker can fetch it. 2.2MB once per test generation is acceptable.
  // (If this becomes a bottleneck, we can build a per-letter index file later.)

  // Collect all completed indices across the relevant page types
  const completedIndices = new Set<number>();
  for (const pt of pageTypes) {
    for (const idx of progress[pt] || []) completedIndices.add(idx);
  }
  if (completedIndices.size === 0) return [];

  // Fetch words.json — array of { word, wordLower, asStem, asOption, ... }
  // indices are 1-based (per progress.completed semantics: "1" = first word)
  interface WordEntry { word: string; wordLower: string; asStem: number; asOption: number; }
  let words: WordEntry[] = [];
  try {
    words = await fetchJson<WordEntry[]>('/data/words.json');
  } catch (e) {
    console.error('Failed to load words.json in test engine:', e);
    return [];
  }

  // For each completed index, get the word and load its questions
  const targetWords = new Set<string>();
  for (const idx of completedIndices) {
    // 1-based index
    if (idx >= 1 && idx <= words.length) {
      const w = words[idx - 1];
      if (w) targetWords.add(w.wordLower);
    }
  }
  if (targetWords.size === 0) return [];

  // Group by letter for efficient fetching
  const byLetter: Record<string, string[]> = {};
  for (const w of targetWords) {
    const letter = (w[0] || '_').toLowerCase();
    if (!byLetter[letter]) byLetter[letter] = [];
    byLetter[letter].push(w);
  }

  for (const [letter, ws] of Object.entries(byLetter)) {
    try {
      const data = await fetchJson<WqLetterFile>(`/data/wq/${letter}.json`);
      for (const w of ws) {
        const entry = data[w];
        if (!entry) continue;
        const allQs = [...(entry.asStem || []), ...(entry.asOption || [])];
        const matching = allQs.filter(q => qtypes.includes(q.qtype));
        for (const q of matching) {
          pool.push({ type: 'vocab', id: String(q.id), itemKey: w, category });
        }
      }
    } catch { /* letter file missing — skip */ }
  }
  return pool;
}

// Build pool for a grammar category (grammar, narration, voice).
// Uses progress.completed indices in grammar-rules / narration / voice page types
// to pick rules/sections, then loads the questions for those.
async function buildGrammarPool(
  env: Env,
  userId: number,
  category: 'grammar' | 'narration' | 'voice',
  source: 'auto' | 'problematic',
  progress: Record<string, number[]>,
  problematic: Array<{ item_type: string; item_key: string }>,
): Promise<QuestionRef[]> {
  const pool: QuestionRef[] = [];
  const pageType = category === 'grammar' ? 'grammar-rules' : category;

  if (source === 'problematic') {
    // problematic item_type for grammar is 'grammar-mcq'; for narration is 'narration'; voice is 'voice'
    const itemType = category === 'grammar' ? 'grammar-mcq' : category;
    const probItems = problematic.filter(p => p.item_type === itemType).map(p => p.item_key);
    // For grammar-mcq, item_key IS the question id (e.g. "gr-7-q3"). For narration/voice, item_key is the section id (e.g. "nar-5").
    if (category === 'grammar') {
      // item_key format: "gr-7" (rule id) or "gr-7-q3" (specific MCQ). Treat as rule id, load all its MCQs.
      for (const key of probItems) {
        const ruleId = key.replace(/-q\d+$/, '');
        try {
          const no = ruleId.replace('gr-', '');
          const qs = await fetchJson<Array<{ id: string; ruleId?: string }>>(`/data/grammar/qs/gr-${no}.json`);
          for (const q of qs) {
            pool.push({ type: 'grammar', id: q.id, itemKey: ruleId, category: 'grammar' });
          }
        } catch { /* skip */ }
      }
    } else {
      // narration/voice: item_key is the section id (e.g. "nar-5"). Load all PYQs with that ruleId.
      const dataFile = category === 'narration' ? '/data/grammar/narration_questions.json' : '/data/grammar/voice_questions.json';
      try {
        const allQs = await fetchJson<Array<{ id: string; ruleId?: string; qtype: string }>>(dataFile);
        for (const q of allQs) {
          if (probItems.includes(q.ruleId || '')) {
            pool.push({ type: category, id: q.id, itemKey: q.ruleId || '', category });
          }
        }
      } catch { /* skip */ }
    }
    return pool;
  }

  // source === 'auto' — use progress.completed indices to pick rules/sections
  const completedIndices = progress[pageType] || [];
  if (completedIndices.length === 0) return [];

  if (category === 'grammar') {
    // Load rules.json to map index -> rule id
    interface GrammarRule { id: string; no: number; title: string; }
    const rules = await fetchJson<GrammarRule[]>('/data/grammar/rules.json');
    const targetRules = new Set<string>();
    for (const idx of completedIndices) {
      if (idx >= 1 && idx <= rules.length) {
        targetRules.add(rules[idx - 1].id);
      }
    }
    // Load questions for each target rule
    for (const ruleId of targetRules) {
      const no = ruleId.replace('gr-', '');
      try {
        const qs = await fetchJson<Array<{ id: string; ruleId?: string }>>(`/data/grammar/qs/gr-${no}.json`);
        for (const q of qs) {
          pool.push({ type: 'grammar', id: q.id, itemKey: ruleId, category: 'grammar' });
        }
      } catch { /* skip */ }
    }
  } else {
    // narration / voice
    const rulesFile = category === 'narration' ? '/data/grammar/narration_rules.json' : '/data/grammar/voice_rules.json';
    const qsFile = category === 'narration' ? '/data/grammar/narration_questions.json' : '/data/grammar/voice_questions.json';
    interface TopicRule { id: string; no: number; title: string; }
    const rules = await fetchJson<TopicRule[]>(rulesFile);
    const targetSections = new Set<string>();
    for (const idx of completedIndices) {
      if (idx >= 1 && idx <= rules.length) {
        targetSections.add(rules[idx - 1].id);
      }
    }
    const allQs = await fetchJson<Array<{ id: string; ruleId?: string }>>(qsFile);
    for (const q of allQs) {
      if (targetSections.has(q.ruleId || '')) {
        pool.push({ type: category, id: q.id, itemKey: q.ruleId || '', category });
      }
    }
  }
  return pool;
}

// ---- Test generation ----

export async function generateTest(
  env: Env,
  userId: number,
  config: TestConfig,
): Promise<{ questionRefs: QuestionRef[]; total: number }> {
  const progress = await loadUserProgress(env, userId);
  const problematic = config.source === 'problematic' ? await loadUserProblematic(env, userId) : [];

  const allPools: Record<string, QuestionRef[]> = {};
  for (const cat of config.categories) {
    let pool: QuestionRef[] = [];
    if (cat.type === 'grammar' || cat.type === 'narration' || cat.type === 'voice') {
      pool = await buildGrammarPool(env, userId, cat.type as 'grammar' | 'narration' | 'voice', config.source || 'auto', progress, problematic);
    } else {
      pool = await buildVocabPool(env, userId, cat.type, config.source || 'auto', progress, problematic);
    }
    allPools[cat.type] = pool;
  }

  const selected: QuestionRef[] = [];

  for (const cat of config.categories) {
    const pool = allPools[cat.type] || [];
    if (pool.length === 0) continue;

    if (config.single_per_item) {
      // Group by itemKey, pick at most 1 question per item
      const byItem: Record<string, QuestionRef[]> = {};
      for (const q of pool) {
        if (!byItem[q.itemKey]) byItem[q.itemKey] = [];
        byItem[q.itemKey].push(q);
      }
      const itemKeys = Object.keys(byItem);
      // Shuffle item keys
      for (let i = itemKeys.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [itemKeys[i], itemKeys[j]] = [itemKeys[j], itemKeys[i]];
      }
      // Pick min..max items
      const target = cat.min + Math.floor(Math.random() * (cat.max - cat.min + 1));
      const count = Math.min(target, itemKeys.length);
      for (let i = 0; i < count; i++) {
        const itemKey = itemKeys[i];
        const qs = byItem[itemKey];
        // Pick a random question for this item
        const q = qs[Math.floor(Math.random() * qs.length)];
        selected.push(q);
      }
    } else {
      // No single-per-item limit — pick min..max random questions from the pool
      const shuffled = [...pool];
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
      }
      const target = cat.min + Math.floor(Math.random() * (cat.max - cat.min + 1));
      const count = Math.min(target, shuffled.length);
      for (let i = 0; i < count; i++) selected.push(shuffled[i]);
    }
  }

  if (config.shuffle) {
    for (let i = selected.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [selected[i], selected[j]] = [selected[j], selected[i]];
    }
  }

  return { questionRefs: selected, total: selected.length };
}

// ---- Auto-problematic from wrong answers ----

export async function autoProblematicFromResults(
  env: Env,
  userId: number,
  results: Array<{ itemKey: string; category: string; isCorrect: boolean }>,
): Promise<number> {
  let added = 0;
  const now = Date.now();
  for (const r of results) {
    if (r.isCorrect) continue;
    if (!r.itemKey) continue;
    const itemType = CATEGORY_TO_ITEM_TYPE[r.category] || 'vocab';
    try {
      await env.DB.prepare(
        'INSERT INTO problematic (user_id, item_type, item_key, sub_type, created_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id, item_type, item_key) DO NOTHING'
      ).bind(userId, itemType, r.itemKey, r.category, now).run();
      added++;
    } catch (e) {
      // continue on error
    }
  }
  return added;
}

// ---- Timer calculation ----
// SSC pattern: 25 questions in 12 minutes (user said "25 question 15 min, we give 12 min max")
// Ratio: 12/25 = 0.48 minutes per question
// 100 questions -> 100 * 0.48 = 48 minutes (matches user's example)
export function calculateTimerMinutes(totalQuestions: number): number {
  return Math.max(1, Math.round(totalQuestions * 0.48));
}

// ---- Default auto-generated configs ----
// The "auto" test series that the system suggests based on progress.
// These are generated on the fly by the /tests page, not stored.

export const AUTO_TEST_PRESETS = [
  {
    name: 'Quick Mix (25 questions, ~12 min)',
    config: {
      categories: [
        { type: 'syn-ant', min: 5, max: 10 },
        { type: 'ows', min: 3, max: 5 },
        { type: 'idiom', min: 3, max: 5 },
        { type: 'spelling', min: 2, max: 3 },
        { type: 'homonym', min: 1, max: 2 },
        { type: 'grammar', min: 2, max: 3 },
        { type: 'narration', min: 1, max: 2 },
        { type: 'voice', min: 1, max: 2 },
      ],
      single_per_item: true,
      timer_minutes: null, // auto-calc
      shuffle: true,
      source: 'auto' as const,
    },
  },
  {
    name: 'Syn/Ant Focus (50 questions, ~24 min)',
    config: {
      categories: [
        { type: 'syn-ant', min: 40, max: 50 },
      ],
      single_per_item: true,
      timer_minutes: null,
      shuffle: true,
      source: 'auto' as const,
    },
  },
  {
    name: 'Problematic Revision (20 questions, untimed)',
    config: {
      categories: [
        { type: 'syn-ant', min: 5, max: 8 },
        { type: 'ows', min: 2, max: 4 },
        { type: 'idiom', min: 2, max: 4 },
        { type: 'spelling', min: 2, max: 3 },
        { type: 'grammar', min: 2, max: 3 },
        { type: 'narration', min: 1, max: 2 },
        { type: 'voice', min: 1, max: 2 },
      ],
      single_per_item: false, // problematic revision: allow multiple from same word
      timer_minutes: null,
      shuffle: true,
      source: 'problematic' as const,
    },
  },
  {
    name: 'Grammar + Narration + Voice (40 questions, ~19 min)',
    config: {
      categories: [
        { type: 'grammar', min: 15, max: 20 },
        { type: 'narration', min: 10, max: 12 },
        { type: 'voice', min: 8, max: 10 },
      ],
      single_per_item: true,
      timer_minutes: null,
      shuffle: true,
      source: 'auto' as const,
    },
  },
];

// All valid category types (for validation)
export const VALID_CATEGORIES = ['syn-ant', 'ows', 'idiom', 'homonym', 'spelling', 'grammar', 'narration', 'voice'];

export function validateConfig(config: any): { ok: boolean; error?: string; config?: TestConfig } {
  if (!config || typeof config !== 'object') return { ok: false, error: 'Config must be an object' };
  if (!Array.isArray(config.categories) || config.categories.length === 0) {
    return { ok: false, error: 'categories must be a non-empty array' };
  }
  for (const cat of config.categories) {
    if (!cat || typeof cat !== 'object') return { ok: false, error: 'Each category must be an object' };
    if (!VALID_CATEGORIES.includes(cat.type)) return { ok: false, error: `Invalid category type: ${cat.type}` };
    if (typeof cat.min !== 'number' || typeof cat.max !== 'number') return { ok: false, error: 'min and max must be numbers' };
    if (cat.min < 0 || cat.max < cat.min) return { ok: false, error: 'min must be >= 0 and max must be >= min' };
    if (cat.max > 500) return { ok: false, error: 'max per category cannot exceed 500' };
  }
  return {
    ok: true,
    config: {
      categories: config.categories,
      single_per_item: config.single_per_item !== false, // default true
      timer_minutes: typeof config.timer_minutes === 'number' ? config.timer_minutes : null,
      shuffle: config.shuffle !== false, // default true
      source: config.source === 'problematic' ? 'problematic' : (config.source === 'custom' ? 'custom' : 'auto'),
      name: typeof config.name === 'string' ? config.name : undefined,
    },
  };
}
