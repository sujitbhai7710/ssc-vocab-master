// functions/api/test/list.ts
// GET /api/test/list
// Returns: { attempts: [...], configs: [...] }
//
// Lists the user's recent test attempts (with score if finished) and their
// saved custom test configs.
import { Env, getUser, requireUser, json } from '../../_lib/auth';

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  const guard = requireUser(user);
  if (guard instanceof Response) return guard;
  const uid = (guard as { id: number }).id;

  // Recent attempts (last 50)
  const attRows = await ctx.env.DB.prepare(
    'SELECT id, config, total, started_at, finished_at, score, timer_minutes FROM test_attempts WHERE user_id = ? ORDER BY started_at DESC LIMIT 50'
  ).bind(uid).all<{
    id: number; config: string; total: number; started_at: number;
    finished_at: number | null; score: number | null; timer_minutes: number | null;
  }>();

  const attempts = (attRows.results || []).map(r => {
    let cfg: any = {};
    try { cfg = JSON.parse(r.config); } catch {}
    return {
      id: r.id,
      name: cfg?.name || 'Untitled test',
      source: cfg?.source || 'auto',
      total: r.total,
      started_at: r.started_at,
      finished_at: r.finished_at,
      score: r.score,
      timer_minutes: r.timer_minutes,
      in_progress: r.finished_at === null,
    };
  });

  // Saved configs
  const cfgRows = await ctx.env.DB.prepare(
    'SELECT id, name, config, created_at, updated_at FROM test_configs WHERE user_id = ? ORDER BY updated_at DESC'
  ).bind(uid).all<{
    id: number; name: string; config: string; created_at: number; updated_at: number;
  }>();

  const configs = (cfgRows.results || []).map(r => {
    let cfg: any = {};
    try { cfg = JSON.parse(r.config); } catch {}
    return {
      id: r.id,
      name: r.name,
      config: cfg,
      created_at: r.created_at,
      updated_at: r.updated_at,
    };
  });

  // Also include stats: total attempts, total finished, avg score
  const stats = {
    total_attempts: attempts.length,
    finished: attempts.filter(a => !a.in_progress).length,
    in_progress: attempts.filter(a => a.in_progress).length,
    avg_score: attempts.length > 0
      ? Math.round(attempts.filter(a => a.score !== null).reduce((s, a) => s + (a.score || 0), 0) / Math.max(1, attempts.filter(a => a.score !== null).length))
      : 0,
    saved_configs: configs.length,
  };

  return json({ attempts, configs, stats }, 200);
};
