// src/lib/vocab-data.ts
// Type definitions and data loaders for SSC vocabulary platform.
// All data files live in /data/*.json and are fetched at runtime.

export interface WordEntry {
  word: string;
  wordLower: string;
  asStem: number;
  asOption: number;
  total: number;
  stemExams: string[];
  optionExams: string[];
  qtypesAsStem: { synonym: number; antonym: number; 'one-word': number };
  qtypesAsOption: { synonym: number; antonym: number; 'one-word': number };
}

export type QType = 'synonym' | 'antonym' | 'one-word';

export interface QuestionEntry {
  id: number;
  exam: string;
  qno: number;
  qtype: QType;
  stem: string;
  options: string[];
  /** Index of the best-guess correct answer in `options`. -1 if unknown. */
  correctIdx?: number;
}

export type QTypeExtended = 'synonym' | 'antonym' | 'one-word' | 'idiom' | 'homonym' | 'spelling';

export interface SummaryStats {
  totalFiles: number;
  exams: string[];
  totalQuestions: number;
  byType: Record<string, number>;
  totalSynonymAntonym: number;
  totalOneWord: number;
  totalIdioms: number;
  totalHomonyms: number;
  totalSpelling: number;
  totalUniqueWords: number;
  questionsPerFile: { exam: string; questions: number }[];
}

export interface EnrichedSynonym {
  word: string;
  source: 'ssc' | 'wordnet';
  added?: boolean;
  /** Status of this synonym/antonym:
   *  - 'correct'    = appeared as the correct answer in past SSC (best-guess via WordNet)
   *  - 'distractor' = appeared as a wrong option in past SSC
   *  - 'added'      = added from WordNet (did NOT appear in any SSC question for this word)
   */
  status?: 'correct' | 'distractor' | 'added';
}

export interface EnrichedEntry {
  word: string;
  wordLower: string;
  definition: string;
  pos: string;
  ssSynonyms: EnrichedSynonym[];
  ssAntonyms: EnrichedSynonym[];
  root: {
    primary: string;
    meaning: string;
    family: string[];
    added: boolean;
  } | null;
  mnemonic: string;
}

export interface WordQuestions {
  asStem: number[];
  asOption: number[];
}

// Module-level caches
let summaryCache: SummaryStats | null = null;
let wordsCache: WordEntry[] | null = null;
let questionsCache: QuestionEntry[] | null = null;
let wordQuestionsCache: Record<string, WordQuestions> | null = null;
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
  const questionsRes = await fetch('/data/questions.json');
  if (!questionsRes.ok) throw new Error(`HTTP ${questionsRes.status} for questions.json`);
  const questions = (await questionsRes.json()) as QuestionEntry[];
  const wqRes = await fetch('/data/word_questions.json');
  if (!wqRes.ok) throw new Error(`HTTP ${wqRes.status} for word_questions.json`);
  const wordQuestions = (await wqRes.json()) as Record<string, WordQuestions>;
  questionsCache = questions;
  wordQuestionsCache = wordQuestions;
  return { questions, wordQuestions };
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

// Helper: build example sentence for a word
export function buildExampleSentence(word: string, pos?: string): string {
  const lower = word.toLowerCase();
  if (lower === 'loquacious') {
    return 'The loquacious tour guide kept the travelers entertained throughout the long bus journey.';
  }
  if (lower === 'reticent') {
    return 'Normally reticent about his private life, the actor refused to comment on the rumors.';
  }
  const p = pos?.toLowerCase();
  if (p === 'noun') return `His attitude toward the issue showed a remarkable sense of ${word.toLowerCase()}.`;
  if (p === 'verb') return `She decided to ${word.toLowerCase()} despite the obvious risks involved.`;
  if (p === 'adjective') return `The speaker gave a remarkably ${word.toLowerCase()} explanation of the situation.`;
  if (p === 'adverb') return `He spoke ${word.toLowerCase()} about his achievements, never boasting.`;
  return `The committee chose to ${word.toLowerCase()} its strategy to fit the new regulations.`;
}
