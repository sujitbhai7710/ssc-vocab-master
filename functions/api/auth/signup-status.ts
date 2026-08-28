// functions/api/auth/signup-status.ts — public: is signup enabled + is DB empty
import { Env, json } from '../../_lib/auth';

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const userCount = await ctx.env.DB.prepare('SELECT COUNT(*) as c FROM users').first<{ c: number }>();
  const isEmpty = !userCount || userCount.c === 0;
  const setting = await ctx.env.DB.prepare("SELECT value FROM settings WHERE key = 'signup_enabled'").first<{ value: string }>();
  const enabled = isEmpty ? true : (setting ? setting.value !== 'false' : true);
  return json({ signupEnabled: enabled, isEmpty }, 200);
};
