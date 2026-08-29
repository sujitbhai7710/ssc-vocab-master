// functions/api/test/[id].ts
// GET /api/test/<id>            -> get attempt details (only if belongs to user, not yet submitted)
// GET /api/test/<id>?results=1  -> get attempt + results (after submission)
// DELETE /api/test/<id>         -> abandon/delete an attempt (and its results)
import { Env, getUser, requireUser, json } from '../../_lib/auth';

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;

  const id = parseInt(ctx.params.id, 10);
  if (!Number.isFinite(id) || id < 1) return json({ error: 'Invalid id' }, 400);

  const url = new URL(ctx.request.url);
  const includeResults = url.searchParams.get('results') === '1';

  const att = await ctx.env.DB.prepare(
    'SELECT id, user_id, config, question_ids, total, started_at, finished_at, score, timer_minutes FROM test_attempts WHERE id = ?'
  ).bind(id).first<{
    id: number; user_id: number; config: string; question_ids: string; total: number;
    started_at: number; finished_at: number | null; score: number | null; timer_minutes: number | null;
  }>();

  if (!att) return json({ error: 'Test not found' }, 404);
  if (att.user_id !== uid) return json({ error: 'Not your test' }, 403);

  let parsedConfig: any = {};
  let parsedQuestionIds: any[] = [];
  try { parsedConfig = JSON.parse(att.config); } catch {}
  try { parsedQuestionIds = JSON.parse(att.question_ids); } catch {}

  const response: any = {
    id: att.id,
    config: parsedConfig,
    question_refs: parsedQuestionIds,
    total: att.total,
    started_at: att.started_at,
    finished_at: att.finished_at,
    score: att.score,
    timer_minutes: att.timer_minutes,
  };

  if (includeResults && att.finished_at !== null) {
    const results = await ctx.env.DB.prepare(
      'SELECT question_idx, question_type, question_id, item_key, category, selected_idx, correct_idx, is_correct, time_ms FROM test_results WHERE attempt_id = ? ORDER BY question_idx'
    ).bind(id).all<{
      question_idx: number; question_type: string; question_id: string; item_key: string | null;
      category: string; selected_idx: number | null; correct_idx: number; is_correct: number; time_ms: number | null;
    }>();
    response.results = (results.results || []).map(r => ({
      ...r,
      is_correct: !!r.is_correct,
    }));
  }

  return json(response, 200);
};

export const onRequestDelete: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;

  const id = parseInt(ctx.params.id, 10);
  if (!Number.isFinite(id) || id < 1) return json({ error: 'Invalid id' }, 400);

  const att = await ctx.env.DB.prepare('SELECT user_id FROM test_attempts WHERE id = ?').bind(id).first<{ user_id: number }>();
  if (!att) return json({ error: 'Test not found' }, 404);
  if (att.user_id !== uid) return json({ error: 'Not your test' }, 403);

  // Delete results first (FK-like), then the attempt
  await ctx.env.DB.batch([
    ctx.env.DB.prepare('DELETE FROM test_results WHERE attempt_id = ?').bind(id),
    ctx.env.DB.prepare('DELETE FROM test_attempts WHERE id = ?').bind(id),
  ]);

  return json({ ok: true }, 200);
};
