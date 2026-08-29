// src/lib/vocab-data.ts
// Type definitions and data loaders for SSC vocabulary platform.

export interface WordEntry {
  word: string;
  wordLower: string;
  asStem: number;
  asOption: number;
  total: number;
  stemExams: string[];
  optionExams: string[];
  qtypesAsStem: Partial<Record<QType, number>>;
  qtypesAsOption: Partial<Record<QType, number>>;
  correctAsStem: number;
  correctAsOption: number;
}

export type QType = 'synonym' | 'antonym' | 'one-word' | 'idiom' | 'homonym' | 'spelling';

export interface QuestionEntry {
  id: number;
  exam?: string;
  year?: string;
  satwik_id?: number;
  qtype: QType;
  prompt?: string;
  stem: string;
  options: string[];
  correctIdx?: number;  // REAL correct answer from Satwik, not best-guess
  expl?: string;
  src?: string;
  sent?: string;  // The full sentence (for underlined-word questions)
}

export interface SummaryStats {
  totalFiles: number;
  totalQuestions: number;
  byType: Record<string, number>;
  totalSynonym: number;
  totalAntonym: number;
  totalSynonymAntonym: number;
  totalOneWord: number;
  totalIdioms: number;
  totalHomonyms: number;
  totalSpelling: number;
  totalUniqueWords: number;
  totalRoots: number;
}

export interface EnrichedSynonym {
  word: string;
  /** 'correct' = appeared as the actual synonym/antonym in past SSC (GREEN).
   *  'added'   = added by me (GRAY).
   *  (No more 'distractor' — user requested only two colors.)
   */
  status: 'correct' | 'added';
}

export interface RootFamilyWord {
  w: string;
  wLower: string;
  pos: string;
  mean: string;
  bn: string;
  mn: string;
  n: number;
}

export interface EnrichedEntry {
  word: string;
  wordLower: string;
  definition: string;
  pos: string;
  bn: string;        // Bengali meaning
  ex: string;        // Example sentence (curated)
  mnemonic: string;  // Trick to remember
  root: string;
  rootMeaning: string;
  rootBn: string;
  rootFamily: RootFamilyWord[];  // All words in the same root family
  ssSynonyms: EnrichedSynonym[];
  ssAntonyms: EnrichedSynonym[];
}

export interface WordQuestions {
  asStem: number[];
  asOption: number[];
}

export interface RootFamily {
  root: string;
  rm: string;     // root meaning
  rbn: string;     // Bengali root meaning
  words: Array<{
    w: string;
    pos: string;
    mean: string;
    bn: string;
    mn: string;
    n: number;
    mods?: Record<string, number>;
  }>;
}

// Caches
let summaryCache: SummaryStats | null = null;
let wordsCache: WordEntry[] | null = null;
let questionsCache: QuestionEntry[] | null = null;
let wordQuestionsCache: Record<string, WordQuestions> | null = null;
let rootsCache: RootFamily[] | null = null;
const enrichedCache: Record<string, Record<string, EnrichedEntry>> = {};

export async function loadSummary(): Promise<SummaryStats> {
  if (summaryCache) return summaryCache;
  const res = await fetch('/data/summary.json');
  if (!res.ok) throw new Error(`HTTP ${res.status} for summary.json`);
  summaryCache = (await res.json()) as SummaryStats;
  return summaryCache;
}

export async function loadWords(): Promise<WordEntry[]> {
  if (wordsCache) return wordsCache;
  const res = await fetch('/data/words.json');
  if (!res.ok) throw new Error(`HTTP ${res.status} for words.json`);
  wordsCache = (await res.json()) as WordEntry[];
  return wordsCache;
}

export async function loadQuestions(): Promise<{
  questions: QuestionEntry[];
  wordQuestions: Record<string, WordQuestions>;
}> {
  if (questionsCache && wordQuestionsCache) {
    return { questions: questionsCache, wordQuestions: wordQuestionsCache };
  }
  const qRes = await fetch('/data/questions.json');
  if (!qRes.ok) throw new Error(`HTTP ${qRes.status} for questions.json`);
  const questions = (await qRes.json()) as QuestionEntry[];
  const wqRes = await fetch('/data/word_questions.json');
  if (!wqRes.ok) throw new Error(`HTTP ${wqRes.status} for word_questions.json`);
  const wordQuestions = (await wqRes.json()) as Record<string, WordQuestions>;
  questionsCache = questions;
  wordQuestionsCache = wordQuestions;
  return { questions, wordQuestions };
}

// FAST path: load only one word's questions (per-letter file, ~100-300KB cached).
// Replaces the old loadQuestions() 2.9MB fetch on every word expansion.
const wqLetterCache: Record<string, Record<string, { asStem: QuestionEntry[]; asOption: QuestionEntry[] }>> = {};
export async function loadWordQuestions(wordLower: string): Promise<{ asStem: QuestionEntry[]; asOption: QuestionEntry[] }> {
  const letter = (wordLower[0] || '_').toLowerCase();
  if (!wqLetterCache[letter]) {
    try {
      const res = await fetch(`/data/wq/${letter}.json`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      wqLetterCache[letter] = (await res.json()) as Record<string, { asStem: QuestionEntry[]; asOption: QuestionEntry[] }>;
    } catch (err) {
      console.error(`Failed to load wq/${letter}.json:`, err);
      wqLetterCache[letter] = {};
    }
  }
  return wqLetterCache[letter][wordLower] || { asStem: [], asOption: [] };
}

// FAST path for dashboard: top words only (~7KB vs 2.2MB words.json).
let topWordsCache: { topStems: WordEntry[]; topOptions: WordEntry[] } | null = null;
export async function loadTopWords(): Promise<{ topStems: WordEntry[]; topOptions: WordEntry[] }> {
  if (topWordsCache) return topWordsCache;
  const res = await fetch('/data/top_words.json');
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  topWordsCache = (await res.json()) as { topStems: WordEntry[]; topOptions: WordEntry[] };
  return topWordsCache;
}

export async function loadEnrichedForWord(wordLower: string): Promise<EnrichedEntry | null> {
  const letter = wordLower[0] || '_';
  if (!enrichedCache[letter]) {
    try {
      const res = await fetch(`/data/enriched/enriched_${letter}.json`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      enrichedCache[letter] = (await res.json()) as Record<string, EnrichedEntry>;
    } catch (err) {
      console.error(`Failed to load enriched_${letter}.json:`, err);
      enrichedCache[letter] = {};
    }
  }
  return enrichedCache[letter][wordLower] || null;
}

export async function loadRoots(): Promise<RootFamily[]> {
  if (rootsCache) return rootsCache;
  try {
    const res = await fetch('/data/roots.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    rootsCache = (await res.json()) as RootFamily[];
  } catch (err) {
    console.error('Failed to load roots.json:', err);
    rootsCache = [];
  }
  return rootsCache;
}

// Build a fallback example sentence if Satwik doesn't provide one
export function buildExampleSentence(word: string, pos?: string): string {
  const lower = word.toLowerCase();
  if (lower === 'loquacious') return 'The loquacious tour guide kept the travelers entertained throughout the long bus journey.';
  if (lower === 'reticent') return 'Normally reticent about his private life, the actor refused to comment on the rumors.';
  const p = pos?.toLowerCase();
  if (p === 'noun') return `His attitude toward the issue showed a remarkable sense of ${word.toLowerCase()}.`;
  if (p === 'verb') return `She decided to ${word.toLowerCase()} despite the obvious risks involved.`;
  if (p === 'adjective' || p === 'adj') return `The speaker gave a remarkably ${word.toLowerCase()} explanation of the situation.`;
  if (p === 'adverb' || p === 'adv') return `He spoke ${word.toLowerCase()} about his achievements, never boasting.`;
  return `The committee chose to ${word.toLowerCase()} its strategy to fit the new regulations.`;
}

// Pronunciation: best free source = dictionaryapi.dev (real human recordings + IPA),
// with Web Speech API as instant fallback. Caches results per word.
interface PronResult {
  audio?: string;   // audio URL
  ipa?: string;     // phonetic transcription
  source: 'dictionary' | 'speech' | 'none';
}
const _pronCache: Record<string, PronResult> = {};

// Play pronunciation — INSTANT. Uses Web Speech API immediately (no network wait),
// then prefetches dictionary audio in the background for next time.
// If we already have cached dictionary audio, plays that instantly instead.
export async function pronounceWord(word: string): Promise<PronResult> {
  const w = word.trim();
  if (!w) return { source: 'none' };
  if (typeof window === 'undefined') return { source: 'none' };

  const key = w.toLowerCase();
  const cached = _pronCache[key];

  // Case 1: We have cached dictionary audio → play it instantly
  if (cached?.audio) {
    try {
      const audio = new Audio(cached.audio);
      audio.play().catch(() => {
        // autoplay block → fall back to speech
        _speakFallback(w);
      });
      return cached;
    } catch {
      _speakFallback(w);
      return cached;
    }
  }

  // Case 2: Not cached yet → play Web Speech INSTANTLY (no network wait),
  // then prefetch dictionary audio in the background for next time.
  _speakFallback(w);

  // Prefetch in background (don't await — fire and forget)
  if (!cached) {
    _prefetchPronunciation(w).catch(() => {});
  }

  return cached || { source: 'speech' };
}

// Background prefetch — fetches dictionary audio + IPA, caches result.
// Called by pronounceWord() so the NEXT click plays the better audio instantly.
async function _prefetchPronunciation(word: string): Promise<void> {
  const key = word.toLowerCase();
  if (_pronCache[key]) return; // already cached
  try {
    const res = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(key)}`);
    if (res.ok) {
      const data = await res.json();
      const entry = Array.isArray(data) ? data[0] : null;
      if (entry) {
        const phonetics = entry.phonetics || [];
        let withAudio = phonetics.find((p: any) => p.audio);
        let ipa = (withAudio?.text) || phonetics.find((p: any) => p.text)?.text || entry.phonetic;
        if (withAudio?.audio) {
          _pronCache[key] = { audio: withAudio.audio, ipa, source: 'dictionary' };
          return;
        }
        if (ipa) {
          _pronCache[key] = { ipa, source: 'speech' };
          return;
        }
      }
    }
  } catch {
    /* network — ignore */
  }
  _pronCache[key] = { source: 'speech' };
}

// Keep fetchPronunciation for backward compat (used by WordDetailView for IPA display)
// but make it use the cache-first approach too.
export async function fetchPronunciation(word: string): Promise<PronResult> {
  const w = word.trim();
  if (!w) return { source: 'none' };
  const key = w.toLowerCase();
  if (_pronCache[key]) return _pronCache[key];
  await _prefetchPronunciation(w);
  return _pronCache[key] || { source: 'speech' };
}

function _speakFallback(word: string): void {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(word);
  u.rate = 0.9;
  u.lang = 'en-US';
  window.speechSynthesis.speak(u);
}

// Back-compat: synchronous variant (no audio fetch, just Web Speech).
export function pronounceWordSync(word: string): void {
  _speakFallback(word);
}
