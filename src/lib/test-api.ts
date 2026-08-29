// src/lib/test-api.ts
// Client-side API for the mock test system.
// All functions call the /api/test/* worker endpoints (authed via httpOnly cookie).

export interface TestCategorySpec {
  type: string;
  min: number;
  max: number;
}

export interface TestConfig {
  categories: TestCategorySpec[];
  single_per_item: boolean;
  timer_minutes: number | null;
  shuffle: boolean;
  source?: 'auto' | 'problematic' | 'custom';
  name?: string;
}

export interface QuestionRef {
  type: 'vocab' | 'grammar' | 'narration' | 'voice';
  id: string;
  itemKey: string;
  category: string;
}

export interface TestAttemptSummary {
  id: number;
  name: string;
  source: string;
  total: number;
  started_at: number;
  finished_at: number | null;
  score: number | null;
  timer_minutes: number | null;
  in_progress: boolean;
}

export interface SavedConfig {
  id: number;
  name: string;
  config: TestConfig;
  created_at: number;
  updated_at: number;
}

export interface TestListResponse {
  attempts: TestAttemptSummary[];
  configs: SavedConfig[];
  stats: {
    total_attempts: number;
    finished: number;
    in_progress: number;
    avg_score: number;
    saved_configs: number;
  };
}

export interface GeneratedTest {
  attempt_id: number;
  total: number;
  question_refs: QuestionRef[];
  timer_minutes: number;
  config: TestConfig;
  started_at: number;
}

export interface TestDetail {
  id: number;
  config: TestConfig;
  question_refs: QuestionRef[];
  total: number;
  started_at: number;
  finished_at: number | null;
  score: number | null;
  timer_minutes: number | null;
  results?: Array<{
    question_idx: number;
    question_type: string;
    question_id: string;
    item_key: string | null;
    category: string;
    selected_idx: number | null;
    correct_idx: number;
    is_correct: boolean;
    time_ms: number | null;
  }>;
}

export interface SubmitResult {
  ok: boolean;
  attempt_id: number;
  score: number;
  total: number;
  auto_problematic_added: number;
  finished_at: number;
}

// ---- generate a new test ----
export async function generateTest(config: TestConfig): Promise<{ ok: boolean; error?: string; test?: GeneratedTest }> {
  try {
    const res = await fetch('/api/test/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(config),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, error: data.error || 'Failed to generate test' };
    return { ok: true, test: data as GeneratedTest };
  } catch (e: any) {
    return { ok: false, error: e?.message || 'Network error' };
  }
}

// ---- get a test attempt (for taking or reviewing) ----
export async function getTest(id: number, includeResults = false): Promise<{ ok: boolean; error?: string; test?: TestDetail }> {
  try {
    const url = `/api/test/${id}${includeResults ? '?results=1' : ''}`;
    const res = await fetch(url, { credentials: 'include' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, error: data.error || 'Failed to load test' };
    return { ok: true, test: data as TestDetail };
  } catch (e: any) {
    return { ok: false, error: e?.message || 'Network error' };
  }
}

// ---- submit a test ----
export async function submitTest(
  attemptId: number,
  answers: Array<{ question_idx: number; selected_idx: number | null; time_ms?: number }>,
): Promise<{ ok: boolean; error?: string; result?: SubmitResult }> {
  try {
    const res = await fetch('/api/test/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ attempt_id: attemptId, answers }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, error: data.error || 'Failed to submit test' };
    return { ok: true, result: data as SubmitResult };
  } catch (e: any) {
    return { ok: false, error: e?.message || 'Network error' };
  }
}

// ---- delete/abandon a test ----
export async function deleteTest(id: number): Promise<boolean> {
  try {
    const res = await fetch(`/api/test/${id}`, { method: 'DELETE', credentials: 'include' });
    return res.ok;
  } catch { return false; }
}

// ---- list attempts + saved configs + stats ----
export async function listTests(): Promise<TestListResponse | null> {
  try {
    const res = await fetch('/api/test/list', { credentials: 'include' });
    if (!res.ok) return null;
    return (await res.json()) as TestListResponse;
  } catch { return null; }
}

// ---- saved config CRUD ----
export async function saveConfig(name: string, config: TestConfig): Promise<{ ok: boolean; error?: string; id?: number }> {
  try {
    const res = await fetch('/api/test/configs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ name, config }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, error: data.error || 'Failed to save config' };
    return { ok: true, id: data.id };
  } catch (e: any) {
    return { ok: false, error: e?.message || 'Network error' };
  }
}

export async function updateConfig(id: number, updates: { name?: string; config?: TestConfig }): Promise<{ ok: boolean; error?: string }> {
  try {
    const res = await fetch(`/api/test/configs?id=${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(updates),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, error: data.error || 'Failed to update config' };
    return { ok: true };
  } catch (e: any) {
    return { ok: false, error: e?.message || 'Network error' };
  }
}

export async function deleteConfig(id: number): Promise<boolean> {
  try {
    const res = await fetch(`/api/test/configs?id=${id}`, { method: 'DELETE', credentials: 'include' });
    return res.ok;
  } catch { return false; }
}

// ---- timer calculation (mirrors server-side) ----
// SSC pattern: 25 questions in 12 minutes -> 0.48 min/question
// 100 questions -> 48 minutes
export function calculateTimerMinutes(totalQuestions: number): number {
  return Math.max(1, Math.round(totalQuestions * 0.48));
}

// ---- category metadata for UI ----
export const CATEGORIES = [
  { type: 'syn-ant', label: 'Synonyms / Antonyms', color: 'amber', desc: 'From your completed stems/options' },
  { type: 'ows', label: 'One-Word Substitution', color: 'violet', desc: 'From your completed OWS list' },
  { type: 'idiom', label: 'Idioms', color: 'orange', desc: 'From your completed idioms' },
  { type: 'homonym', label: 'Homonyms', color: 'pink', desc: 'From your completed homonyms' },
  { type: 'spelling', label: 'Spelling', color: 'teal', desc: 'From your completed spelling list' },
  { type: 'grammar', label: 'Grammar Rules', color: 'amber', desc: 'From your completed grammar rules' },
  { type: 'narration', label: 'Narration', color: 'sky', desc: 'From your completed narration sections' },
  { type: 'voice', label: 'Voice', color: 'teal', desc: 'From your completed voice sections' },
] as const;

export const AUTO_PRESETS = [
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
      timer_minutes: null,
      shuffle: true,
      source: 'auto' as const,
    },
  },
  {
    name: 'Syn/Ant Focus (50 questions, ~24 min)',
    config: {
      categories: [{ type: 'syn-ant', min: 40, max: 50 }],
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
      single_per_item: false,
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
