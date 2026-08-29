<script lang="ts">
  // src/components/AdminDashboard.svelte
  import { onMount } from 'svelte';
  import { getUser } from '../lib/auth';

  let user = $state(getUser());
  let signupEnabled = $state(true);
  let users = $state<Array<{ id: number; email: string; role: string; created_at: number }>>([]);
  let loading = $state(true);
  let saving = $state(false);
  let error = $state('');
  let msg = $state('');

  onMount(async () => {
    if (!user || user.role !== 'admin') {
      window.location.href = '/';
      return;
    }
    await refresh();
  });

  async function refresh() {
    loading = true;
    try {
      const [sRes, uRes] = await Promise.all([
        fetch('/api/admin/settings', { credentials: 'include' }),
        fetch('/api/admin/users', { credentials: 'include' }),
      ]);
      if (sRes.ok) {
        const sd = await sRes.json();
        signupEnabled = sd.signupEnabled;
      }
      if (uRes.ok) {
        const ud = await uRes.json();
        users = ud.users || [];
      }
    } catch (e) {
      error = String(e);
    } finally {
      loading = false;
    }
  }

  async function toggleSignup() {
    saving = true; msg = ''; error = '';
    try {
      const res = await fetch('/api/admin/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ signupEnabled: !signupEnabled }),
      });
      if (res.ok) {
        signupEnabled = !signupEnabled;
        msg = `Signups ${signupEnabled ? 'enabled' : 'disabled'}.`;
      } else {
        const d = await res.json().catch(() => ({}));
        error = d.error || 'Failed to update';
      }
    } finally {
      saving = false;
    }
  }

  async function deleteUser(id: number, email: string) {
    if (!confirm(`Delete user "${email}"? This also removes their problematic & progress data.`)) return;
    const res = await fetch(`/api/admin/users?id=${id}`, { method: 'DELETE', credentials: 'include' });
    if (res.ok) {
      users = users.filter((u) => u.id !== id);
      msg = `Deleted ${email}.`;
    } else {
      const d = await res.json().catch(() => ({}));
      error = d.error || 'Failed to delete';
    }
  }
</script>

<div class="space-y-5">
  <div>
    <div class="text-[11px] uppercase font-semibold tracking-wide text-amber-600">Admin</div>
    <h2 class="text-2xl font-bold tracking-tight mt-1">Admin Dashboard</h2>
    <p class="text-sm text-zinc-500 mt-1">Manage signups and users.</p>
  </div>

  {#if loading}
    <div class="space-y-3">{#each Array(3) as _}<div class="h-20 rounded-xl bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>{/each}</div>
  {:else}
    {#if msg}<div class="bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-md p-2.5 text-xs text-emerald-700 dark:text-emerald-300">{msg}</div>{/if}
    {#if error}<div class="bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-md p-2.5 text-xs text-rose-700 dark:text-rose-300">{error}</div>{/if}

    <!-- Signup toggle -->
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4 flex items-center justify-between gap-3">
      <div>
        <h3 class="text-sm font-semibold">New signups</h3>
        <p class="text-xs text-zinc-500 mt-0.5">When disabled, no new users can create an account.</p>
      </div>
      <button
        onclick={toggleSignup} disabled={saving}
        class={`relative h-7 w-12 rounded-full transition-colors ${signupEnabled ? 'bg-emerald-500' : 'bg-zinc-300 dark:bg-zinc-700'}`}
      >
        <span class={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-transform ${signupEnabled ? 'translate-x-5' : 'translate-x-0.5'}`}></span>
      </button>
    </div>

    <!-- Users -->
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl overflow-hidden">
      <div class="px-4 py-3 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
        <h3 class="text-sm font-semibold">Users ({users.length})</h3>
      </div>
      <div class="divide-y divide-zinc-100 dark:divide-zinc-800">
        {#each users as u}
          <div class="px-4 py-3 flex items-center gap-3">
            <div class="h-9 w-9 rounded-full bg-gradient-to-br from-orange-500 to-rose-500 text-white flex items-center justify-center text-sm font-bold uppercase">{u.email.charAt(0)}</div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate flex items-center gap-2">
                {u.email}
                {#if u.role === 'admin'}<span class="text-[9px] font-bold text-amber-600 border border-amber-300 rounded px-1.5 py-0.5">ADMIN</span>{/if}
                {#if u.id === user?.id}<span class="text-[9px] font-bold text-sky-600 border border-sky-300 rounded px-1.5 py-0.5">YOU</span>{/if}
              </div>
              <div class="text-[11px] text-zinc-500">Joined {new Date(u.created_at).toLocaleDateString()}</div>
            </div>
            {#if u.id !== user?.id}
              <button onclick={() => deleteUser(u.id, u.email)} class="text-xs h-8 px-3 rounded-md border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30">Delete</button>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
