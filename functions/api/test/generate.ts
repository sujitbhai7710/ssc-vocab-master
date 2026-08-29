// functions/api/test/generate.ts
// POST /api/test/generate
// Body: TestConfig (categories, single_per_item, timer_minutes, shuffle, source)
// Returns: { attempt_id, total, question_refs, timer_minutes, config, started_at }
//
// Generates a new test attempt from the user's progress (or problematic items).
// The actual question payloads (stem, options, correctIdx, explanation) are
// NOT returned here — the client fetches them via /data/*.json when taking the test.
// Only question refs are stored in the DB and returned.
import { Env, getUser, requireUser, json } from '../../_lib/auth';
import { generateTest, validateConfig, calculateTimerMinutes } from '../../_lib/test-engine';

export const onRequestPost: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;

  let body: any;
  try { body = await ctx.request.json(); } catch { return json({ error: 'Invalid JSON' }, 400); }

  const validation = validateConfig(body);
  if (!validation.ok) return json({ error: validation.error }, 400);
  const config = validation.config!;

  // Generate the question pool
  let gen;
  try {
    gen = await generateTest(ctx.env, uid, config);
  } catch (e: any) {
    console.error('Test generation failed:', e);
    return json({ error: 'Failed to generate test: ' + (e?.message || 'unknown') }, 500);
  }

  if (gen.total === 0) {
    return json({
      error: 'No questions available. Mark some words/rules as "read" first (using the progress tracker on any module page), or wait until you have problematic items.',
    }, 400);
  }

  // Calculate timer if not specified
  const timerMinutes = config.timer_minutes ?? calculateTimerMinutes(gen.total);

  // Create the attempt row
  const now = Date.now();
  const ins = await ctx.env.DB.prepare(
    'INSERT INTO test_attempts (user_id, config, question_ids, total, started_at, timer_minutes) VALUES (?, ?, ?, ?, ?, ?) RETURNING id'
  ).bind(
    uid,
    JSON.stringify(config),
    JSON.stringify(gen.questionRefs),
    gen.total,
    now,
    timerMinutes,
  ).first<{ id: number }>();

  if (!ins || !ins.id) return json({ error: 'Failed to create test attempt' }, 500);

  return json({
    attempt_id: ins.id,
    total: gen.total,
    question_refs: gen.questionRefs,
    timer_minutes: timerMinutes,
    config,
    started_at: now,
  }, 200);
};
