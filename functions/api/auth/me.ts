// functions/api/auth/me.ts
import { Env, getUser, json } from '../../_lib/auth';

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const user = await getUser(ctx.request, ctx.env);
  if (!user) return json({ user: null }, 200);
  return json({ user }, 200);
};
