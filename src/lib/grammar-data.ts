// src/lib/grammar-data.ts
// Types and loaders for the grammar modules (Grammar Rules, Narration, Voice).

export interface GrammarExample {
  incorrect?: string;
  correct?: string;
  sentence?: string;
  correction?: string;
  note?: string;
}

export interface GrammarRule {
  id: string;
  no: number;
  title: string;
  topic: string;
  concept: string;          // merged, clean, easy-to-understand explanation
  examples: GrammarExample[];
  sources: string[];        // e.g. ['rani','error','aman']
  questionIds: string[];    // attached MCQ ids
}

export interface GrammarQuestion {
  id: string;
  ruleId?: string | null;
  source: string;           // rani | error | aman | pyq-error | pyq-improvement
  qtype: 'error' | 'improvement' | 'narration' | 'voice';
  prompt: string;
  sentence: string;
  options: string[];
  correctIdx: number | null;
  explanation: string;
  exam?: string;
  year?: string;
}

export interface TopicRule {
  id: string;
  no: number;
  title: string;
  concept: string;
  rules: string[];          // detailed rule points
  examples: GrammarExample[];
  questionIds: string[];
}

// ---- caches ----
let rulesCache: GrammarRule[] | null = null;
let questionsCache: Record<string, GrammarQuestion> | null = null;
let narrationRulesCache: TopicRule[] | null = null;
let narrationQuestionsCache: Record<string, GrammarQuestion> | null = null;
let voiceRulesCache: TopicRule[] | null = null;
let voiceQuestionsCache: Record<string, GrammarQuestion> | null = null;

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return (await res.json()) as T;
}

export async function loadGrammarRules(): Promise<GrammarRule[]> {
  if (rulesCache) return rulesCache;
  rulesCache = await fetchJson<GrammarRule[]>('/data/grammar/rules.json');
  return rulesCache;
}

export async function loadGrammarQuestions(): Promise<Record<string, GrammarQuestion>> {
  if (questionsCache) return questionsCache;
  const arr = await fetchJson<GrammarQuestion[]>('/data/grammar/questions.json');
  questionsCache = {};
  for (const q of arr) questionsCache[q.id] = q;
  return questionsCache;
}

// Lazy-load questions for a single rule (ruleId like 'gr-7').
const ruleQsCache: Record<string, GrammarQuestion[]> = {};
export async function loadQuestionsForRule(ruleId: string): Promise<GrammarQuestion[]> {
  if (ruleQsCache[ruleId]) return ruleQsCache[ruleId];
  const no = ruleId.replace('gr-', '');
  try {
    const arr = await fetchJson<GrammarQuestion[]>(`/data/grammar/qs/gr-${no}.json`);
    ruleQsCache[ruleId] = arr;
    return arr;
  } catch {
    ruleQsCache[ruleId] = [];
    return [];
  }
}

export async function loadNarrationRules(): Promise<TopicRule[]> {
  if (narrationRulesCache) return narrationRulesCache;
  narrationRulesCache = await fetchJson<TopicRule[]>('/data/grammar/narration_rules.json');
  return narrationRulesCache;
}

export async function loadNarrationQuestions(): Promise<Record<string, GrammarQuestion>> {
  if (narrationQuestionsCache) return narrationQuestionsCache;
  const arr = await fetchJson<GrammarQuestion[]>('/data/grammar/narration_questions.json');
  narrationQuestionsCache = {};
  for (const q of arr) narrationQuestionsCache[q.id] = q;
  return narrationQuestionsCache;
}

export async function loadVoiceRules(): Promise<TopicRule[]> {
  if (voiceRulesCache) return voiceRulesCache;
  voiceRulesCache = await fetchJson<TopicRule[]>('/data/grammar/voice_rules.json');
  return voiceRulesCache;
}

export async function loadVoiceQuestions(): Promise<Record<string, GrammarQuestion>> {
  if (voiceQuestionsCache) return voiceQuestionsCache;
  const arr = await fetchJson<GrammarQuestion[]>('/data/grammar/voice_questions.json');
  voiceQuestionsCache = {};
  for (const q of arr) voiceQuestionsCache[q.id] = q;
  return voiceQuestionsCache;
}
