<script lang="ts">
  // src/components/AuthForm.svelte
  // Shared login/signup form. Shows signup-disabled / first-user-admin hints.
  import { onMount } from 'svelte';
  import { login, signup } from '../lib/auth';

  let { mode }: { mode: 'login' | 'signup' } = $props();
  let email = $state('');
  let password = $state('');
  let error = $state('');
  let busy = $state(false);
  let signupEnabled = $state(true);
  let isEmpty = $state(false);

  onMount(async () => {
    try {
      const res = await fetch('/api/auth/signup-status');
      if (res.ok) {
        const d = await res.json();
        signupEnabled = d.signupEnabled;
        isEmpty = d.isEmpty;
      }
    } catch {}
  });

  async function submit(e: SubmitEvent) {
    e.preventDefault();
    if (busy) return;
    error = '';
    busy = true;
    try {
      const fn = mode === 'login' ? login : signup;
      const r = await fn(email.trim(), password);
      if (!r.ok) {
        error = r.error || 'Something went wrong';
      } else {
        const next = new URLSearchParams(window.location.search).get('next') || '/';
        window.location.href = next;
      }
    } finally {
      busy = false;
    }
  }
</script>

<div class="max-w-md mx-auto">
  <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-6 shadow-sm">
    <div class="text-center mb-5">
      <div class="h-12 w-12 rounded-xl bg-gradient-to-br from-amber-500 via-orange-500 to-rose-500 flex items-center justify-center text-white mx-auto shadow-md">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="m10 17 5-5-5-5"/><path d="M15 12H3"/></svg>
      </div>
      <h2 class="text-xl font-bold tracking-tight mt-3">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
      <p class="text-sm text-zinc-500 mt-1">
        {mode === 'login' ? 'Log in to continue your SSC prep.' : 'Sign up to track progress & save problematic items.'}
      </p>
    </div>

    {#if mode === 'signup' && isEmpty}
      <div class="mb-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-md p-3 text-xs text-amber-800 dark:text-amber-300">
        <strong>First user becomes the admin.</strong> You'll be able to enable/disable signups and manage users.
      </div>
    {/if}
    {#if mode === 'signup' && !signupEnabled && !isEmpty}
      <div class="mb-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-md p-3 text-xs text-rose-800 dark:text-rose-300">
        New signups are currently disabled by the admin. Please contact an administrator.
      </div>
    {/if}

    <form onsubmit={submit} class="space-y-3">
      <div>
        <label for="email" class="block text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-1">Email</label>
        <input
          id="email" type="email" autocomplete="email" required
          bind:value={email}
          class="w-full px-3 py-2 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
          placeholder="you@example.com"
        />
      </div>
      <div>
        <label for="password" class="block text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-1">Password</label>
        <input
          id="password" type="password" autocomplete={mode === 'login' ? 'current-password' : 'new-password'} required
          bind:value={password}
          class="w-full px-3 py-2 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
          placeholder={mode === 'login' ? 'Your password' : 'At least 6 characters'}
        />
      </div>
      {#if error}
        <div class="bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-md p-2.5 text-xs text-rose-700 dark:text-rose-300">{error}</div>
      {/if}
      <button
        type="submit" disabled={busy || (mode === 'signup' && !signupEnabled && !isEmpty)}
        class="w-full h-10 rounded-md bg-gradient-to-r from-orange-500 to-rose-500 text-white font-medium text-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
      >
        {#if busy}<span class="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>{/if}
        {mode === 'login' ? 'Log in' : 'Sign up'}
      </button>
    </form>

    <div class="mt-4 text-center text-xs text-zinc-500">
      {#if mode === 'login'}
        <span>Don't have an account? <a href="/signup" class="text-orange-600 dark:text-orange-400 font-medium hover:underline">Sign up</a></span>
      {:else}
        <span>Already have an account? <a href="/login" class="text-orange-600 dark:text-orange-400 font-medium hover:underline">Log in</a></span>
      {/if}
    </div>
  </div>
  <p class="text-center text-[10px] text-zinc-400 mt-3">
    🔒 Passwords are hashed (PBKDF2). Sessions stay logged in for 1 year unless you log out.
  </p>
</div>
