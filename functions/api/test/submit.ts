// functions/api/test/submit.ts
// POST /api/test/submit
// Body: { attempt_id, answers: [{ question_idx, selected_idx, time_ms? }] }
// Returns: { ok, score, total, auto_problematic_added, results: [...] }
//
// Scores the test, stores per-question results, auto-adds wrong answers to the
// problematic table, and marks the attempt as finished.
//
// CRITICAL: The correct answers are looked up from the static /data/*.json files
// (NOT sent from the client — the client only sends its selected option index).
// This prevents cheating by tampering with the request.
import { Env, getUser, requireUser, json } from '../../_lib/auth';
import { autoProblematicFromResults, type QuestionRef } from '../../_lib/test-engine';

// ---- Static-question lookup (server-side, from /data/*.json) ----

interface VocabQuestion { id: number; qtype: string; stem: string; options: string[]; correctIdx?: number; }
interface GrammarQuestion { id: string; ruleId?: string | null; qtype: string; sentence: string; options: string[]; correctIdx: number | null; }

// Per-letter wq file shape: { word: { asStem: VocabQuestion[], asOption: VocabQuestion[] } }
type WqLetterFile = Record<string, { asStem: VocabQuestion[]; asOption: VocabQuestion[] }>;

const wqLetterCache: Record<string, WqLetterFile> = {};
async function getVocabQuestion(wordLower: string, qid: number): Promise<VocabQuestion | null> {
  const letter = (wordLower[0] || '_').toLowerCase();
  if (!wqLetterCache[letter]) {
    try {
      const res = await fetch(`/data/wq/${letter}.json`);
      if (!res.ok) return null;
      wqLetterCache[letter] = (await res.json()) as WqLetterFile;
    } catch {
      wqLetterCache[letter] = {};
      return null;
    }
  }
  const entry = wqLetterCache[letter]?.[wordLower];
  if (!entry) return null;
  const all = [...(entry.asStem || []), ...(entry.asOption || [])];
  return all.find(q => q.id === qid) || null;
}

// Grammar question lookup: lazy-load per-rule file (qs/gr-<no>.json)
const ruleQsCache: Record<string, GrammarQuestion[]> = {};
async function getGrammarQuestion(qid: string, ruleIdHint: string): Promise<GrammarQuestion | null> {
  // qid format: "gr-7-q3" or "gq-123" — we try to find it via the rule file
  // If ruleIdHint is provided (e.g. "gr-7"), load that file directly.
  if (ruleIdHint && ruleIdHint.startsWith('gr-')) {
    const no = ruleIdHint.replace('gr-', '');
    if (!ruleQsCache[ruleIdHint]) {
      try {
        const res = await fetch(`/data/grammar/qs/gr-${no}.json`);
        if (res.ok) ruleQsCache[ruleIdHint] = (await res.json()) as GrammarQuestion[];
        else ruleQsCache[ruleIdHint] = [];
      } catch { ruleQsCache[ruleIdHint] = []; }
    }
    return ruleQsCache[ruleIdHint].find(q => q.id === qid) || null;
  }
  // Fallback: scan all rule files (slow, but rare) — skip for now
  return null;
}

// Narration/voice question lookup: load the full questions file once
let narrationQsCache: Record<string, GrammarQuestion> | null = null;
let voiceQsCache: Record<string, GrammarQuestion> | null = null;
async function getNarrationQuestion(qid: string): Promise<GrammarQuestion | null> {
  if (!narrationQsCache) {
    try {
      const res = await fetch('/data/grammar/narration_questions.json');
      if (res.ok) {
        const arr = (await res.json()) as GrammarQuestion[];
        narrationQsCache = {};
        for (const q of arr) narrationQsCache[q.id] = q;
      } else narrationQsCache = {};
    } catch { narrationQsCache = {}; }
  }
  return narrationQsCache?.[qid] || null;
}
async function getVoiceQuestion(qid: string): Promise<GrammarQuestion | null> {
  if (!voiceQsCache) {
    try {
      const res = await fetch('/data/grammar/voice_questions.json');
      if (res.ok) {
        const arr = (await res.json()) as GrammarQuestion[];
        voiceQsCache = {};
        for (const q of arr) voiceQsCache[q.id] = q;
      } else voiceQsCache = {};
    } catch { voiceQsCache = {}; }
  }
  return voiceQsCache?.[qid] || null;
}

async function lookupCorrectIdx(ref: QuestionRef): Promise<{ correctIdx: number | null; options: string[] } | null> {
  if (ref.type === 'vocab') {
    const q = await getVocabQuestion(ref.itemKey, parseInt(ref.id, 10));
    if (!q || q.correctIdx === undefined) return null;
    return { correctIdx: q.correctIdx, options: q.options };
  } else if (ref.type === 'grammar') {
    const q = await getGrammarQuestion(ref.id, ref.itemKey);
    if (!q || q.correctIdx === null) return null;
    return { correctIdx: q.correctIdx, options: q.options };
  } else if (ref.type === 'narration') {
    const q = await getNarrationQuestion(ref.id);
    if (!q || q.correctIdx === null) return null;
    return { correctIdx: q.correctIdx, options: q.options };
  } else if (ref.type === 'voice') {
    const q = await getVoiceQuestion(ref.id);
    if (!q || q.correctIdx === null) return null;
    return { correctIdx: q.correctIdx, options: q.options };
  }
  return null;
}

// ---- Submit handler ----

export const onRequestPost: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;

  let body: { attempt_id?: number; answers?: Array<{ question_idx: number; selected_idx: number | null; time_ms?: number }> };
  try { body = await ctx.request.json(); } catch { return json({ error: 'Invalid JSON' }, 400); }

  const attemptId = body.attempt_id;
  if (!Number.isFinite(attemptId)) return json({ error: 'attempt_id required' }, 400);
  if (!Array.isArray(body.answers)) return json({ error: 'answers must be an array' }, 400);

  // Fetch the attempt
  const att = await ctx.env.DB.prepare(
    'SELECT id, user_id, config, question_ids, total, started_at, finished_at FROM test_attempts WHERE id = ?'
  ).bind(attemptId).first<{
    id: number; user_id: number; config: string; question_ids: string; total: number;
    started_at: number; finished_at: number | null;
  }>();

  if (!att) return json({ error: 'Test not found' }, 404);
  if (att.user_id !== uid) return json({ error: 'Not your test' }, 403);
  if (att.finished_at !== null) return json({ error: 'Test already submitted' }, 400);

  let questionRefs: QuestionRef[] = [];
  try { questionRefs = JSON.parse(att.question_ids); } catch {}

  // Build a map of question_idx -> answer for quick lookup
  const answerMap = new Map<number, { selected_idx: number | null; time_ms?: number }>();
  for (const a of body.answers) {
    if (Number.isFinite(a.question_idx) && a.question_idx >= 0 && a.question_idx < questionRefs.length) {
      answerMap.set(a.question_idx, { selected_idx: a.selected_idx, time_ms: a.time_ms });
    }
  }

  // Score each question
  const results: Array<{
    question_idx: number;
    question_type: string;
    question_id: string;
    item_key: string;
    category: string;
    selected_idx: number | null;
    correct_idx: number;
    is_correct: boolean;
    time_ms: number | null;
  }> = [];
  let score = 0;
  const wrongItems: Array<{ itemKey: string; category: string; isCorrect: boolean }> = [];

  for (let i = 0; i < questionRefs.length; i++) {
    const ref = questionRefs[i];
    const ans = answerMap.get(i);
    const selectedIdx = ans?.selected_idx ?? null;

    const lookup = await lookupCorrectIdx(ref);
    let correctIdx: number | null = lookup?.correctIdx ?? null;
    let isCorrect = false;
    if (correctIdx !== null && selectedIdx !== null && selectedIdx === correctIdx) {
      isCorrect = true;
      score++;
    }

    results.push({
      question_idx: i,
      question_type: ref.type,
      question_id: ref.id,
      item_key: ref.itemKey,
      category: ref.category,
      selected_idx: selectedIdx,
      correct_idx: correctIdx ?? -1,
      is_correct: isCorrect,
      time_ms: ans?.time_ms ?? null,
    });

    if (!isCorrect && ref.itemKey) {
      wrongItems.push({ itemKey: ref.itemKey, category: ref.category, isCorrect: false });
    }
  }

  // Store results in D1 (batch insert)
  const now = Date.now();
  const stmts = results.map(r => ctx.env.DB.prepare(
    'INSERT INTO test_results (attempt_id, question_idx, question_type, question_id, item_key, category, selected_idx, correct_idx, is_correct, time_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(attempt_id, question_idx) DO UPDATE SET selected_idx = excluded.selected_idx, correct_idx = excluded.correct_idx, is_correct = excluded.is_correct, time_ms = excluded.time_ms'
  ).bind(
    attemptId, r.question_idx, r.question_type, r.question_id, r.item_key, r.category,
    r.selected_idx, r.correct_idx, r.is_correct ? 1 : 0, r.time_ms
  ));
  // Also mark the attempt as finished
  stmts.push(ctx.env.DB.prepare(
    'UPDATE test_attempts SET finished_at = ?, score = ? WHERE id = ?'
  ).bind(now, score, attemptId));

  // Execute in batches of 20 (D1 batch limit safety)
  for (let i = 0; i < stmts.length; i += 20) {
    await ctx.env.DB.batch(stmts.slice(i, i + 20));
  }

  // Auto-add wrong answers to problematic
  const autoAdded = await autoProblematicFromResults(ctx.env, uid, wrongItems);

  return json({
    ok: true,
    attempt_id: attemptId,
    score,
    total: questionRefs.length,
    auto_problematic_added: autoAdded,
    finished_at: now,
  }, 200);
};
