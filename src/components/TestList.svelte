<script lang="ts">
  // src/components/TestList.svelte
  // The /tests landing page:
  // - Shows stats (total attempts, avg score, saved configs)
  // - Auto-generated test presets (4 presets: Quick Mix, Syn/Ant Focus, Problematic Revision, Grammar+Narration+Voice)
  // - Saved custom configs (with start / edit / delete)
  // - Recent attempts (with retake / view results / continue)
  // - Button to create a new custom config
  import { onMount, onDestroy } from 'svelte';
  import { isLoggedIn, loadSession, onAuthChange } from '../lib/auth';
  import { listTests, generateTest, deleteTest, deleteConfig, AUTO_PRESETS, type TestListResponse, type TestConfig } from '../lib/test-api';

  let data = $state<TestListResponse | null>(null);
  let loading = $state(true);
  let loggedIn = $state(false);
  let unsub: (() => void) | null = null;
  let generating = $state<string | null>(null); // preset name or config id being generated
  let error = $state('');

  async function refresh() {
    loading = true;
    data = await listTests();
    loading = false;
  }

  onMount(async () => {
    await loadSession();
    loggedIn = isLoggedIn();
    unsub = onAuthChange((u) => {
      const now = !!u;
      if (now !== loggedIn) {
        loggedIn = now;
        if (now) refresh();
      }
    });
    if (loggedIn) await refresh();
    else loading = false;
  });

  onDestroy(() => { unsub?.(); });

  async function startPreset(presetName: string, config: TestConfig) {
    generating = presetName;
    error = '';
    const r = await generateTest(config);
    generating = null;
    if (!r.ok || !r.test) {
      error = r.error || 'Failed to generate test';
      return;
    }
    // Navigate to the test page
    window.location.href = `/test?id=${r.test.attempt_id}`;
  }

  async function startSavedConfig(configId: number, config: TestConfig) {
    generating = `config-${configId}`;
    error = '';
    const r = await generateTest(config);
    generating = null;
    if (!r.ok || !r.test) {
      error = r.error || 'Failed to generate test';
      return;
    }
    window.location.href = `/test?id=${r.test.attempt_id}`;
  }

  async function handleDeleteTest(id: number) {
    if (!confirm('Delete this test attempt? This cannot be undone.')) return;
    const ok = await deleteTest(id);
    if (ok) await refresh();
  }

  async function handleDeleteConfig(id: number) {
    if (!confirm('Delete this saved config? This cannot be undone.')) return;
    const ok = await deleteConfig(id);
    if (ok) await refresh();
  }

  function formatDate(ts: number): string {
    const d = new Date(ts);
    const now = Date.now();
    const diff = now - ts;
    if (diff < 60_000) return 'just now';
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
    if (diff < 7 * 86_400_000) return `${Math.floor(diff / 86_400_000)}d ago`;
    return d.toLocaleDateString();
  }
</script>

{#if !loggedIn}
  <div class="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-6 text-center">
    <p class="text-sm text-amber-700 dark:text-amber-300 font-medium">Please log in to access mock tests.</p>
    <a href="/login?next=/tests" class="inline-block mt-3 text-xs h-8 px-4 leading-8 rounded-md bg-amber-600 text-white font-medium hover:bg-amber-700">Log in</a>
  </div>
{:else if loading}
  <div class="flex items-center justify-center py-20">
    <div class="h-8 w-8 rounded-full border-4 border-orange-500 border-t-transparent animate-spin"></div>
  </div>
{:else if data}
  <div class="space-y-6">
    <!-- Header + stats -->
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div>
        <h2 class="text-xl font-bold tracking-tight">Mock Tests</h2>
        <p class="text-sm text-zinc-500 mt-1">Test yourself on what you've studied. Wrong answers auto-add to your <a href="/problems" class="underline">Problems</a> list.</p>
      </div>
      <a href="/tests/custom" class="text-xs h-9 px-4 leading-9 rounded-md bg-orange-600 text-white font-medium hover:bg-orange-700 flex items-center gap-1.5">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        Build Custom Test
      </a>
    </div>

    {#if error}
      <div class="bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-md p-3 text-xs text-rose-700 dark:text-rose-300">
        {error}
      </div>
    {/if}

    <!-- Stats row -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {#each [
        { label: 'Total Attempts', value: data.stats.total_attempts, sub: `${data.stats.finished} finished` },
        { label: 'In Progress', value: data.stats.in_progress, sub: 'resume any time' },
        { label: 'Avg Score', value: `${data.stats.avg_score}%`, sub: 'across finished tests' },
        { label: 'Saved Configs', value: data.stats.saved_configs, sub: 'reusable test setups' },
      ] as stat}
        <div class="border border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 p-4">
          <div class="text-[10px] uppercase font-semibold tracking-wide text-zinc-500">{stat.label}</div>
          <div class="text-2xl font-bold tabular-nums tracking-tight mt-1">{stat.value}</div>
          <div class="text-[10px] text-zinc-500 mt-0.5">{stat.sub}</div>
        </div>
      {/each}
    </div>

    <!-- Auto-generated presets -->
    <div>
      <h3 class="text-sm font-semibold mb-2 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        Quick Start — Auto-Generated Tests
      </h3>
      <p class="text-xs text-zinc-500 mb-3">Pre-built test configs based on your progress. Click to start instantly.</p>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        {#each AUTO_PRESETS as preset}
          <div class="border border-zinc-200 dark:border-zinc-700 rounded-lg p-4 bg-white dark:bg-zinc-900 hover:border-orange-400/40 transition-colors">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <div class="text-sm font-semibold">{preset.name}</div>
                <div class="text-xs text-zinc-500 mt-1">
                  {preset.config.categories.map(c => c.type).join(' · ')}
                  {#if preset.config.source === 'problematic'} · from your Problems{/if}
                </div>
                <div class="text-[10px] text-zinc-400 mt-1">
                  {preset.config.single_per_item ? '1 MCQ per item' : 'Multiple per item allowed'}
                  · {preset.config.shuffle ? 'shuffled' : 'in order'}
                </div>
              </div>
              <button
                onclick={() => startPreset(preset.name, preset.config)}
                disabled={generating === preset.name}
                class="text-xs h-8 px-3 rounded-md bg-orange-600 text-white font-medium hover:bg-orange-700 disabled:opacity-50 shrink-0"
              >
                {#if generating === preset.name}<span class="h-3 w-3 rounded-full border-2 border-white border-t-transparent animate-spin inline-block"></span>{:else}Start{/if}
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Saved custom configs -->
    {#if data.configs.length > 0}
      <div>
        <h3 class="text-sm font-semibold mb-2 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
          Your Saved Custom Configs
        </h3>
        <div class="space-y-2">
          {#each data.configs as cfg}
            <div class="border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 bg-white dark:bg-zinc-900 flex items-center justify-between gap-3">
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium">{cfg.name}</div>
                <div class="text-xs text-zinc-500 mt-0.5">
                  {cfg.config.categories.map(c => `${c.type}: ${c.min}-${c.max}`).join(' · ')}
                </div>
                <div class="text-[10px] text-zinc-400 mt-0.5">Updated {formatDate(cfg.updated_at)}</div>
              </div>
              <div class="flex items-center gap-1.5 shrink-0">
                <button
                  onclick={() => startSavedConfig(cfg.id, cfg.config)}
                  disabled={generating === `config-${cfg.id}`}
                  class="text-xs h-8 px-3 rounded-md bg-emerald-600 text-white font-medium hover:bg-emerald-700 disabled:opacity-50"
                >
                  {#if generating === `config-${cfg.id}`}<span class="h-3 w-3 rounded-full border-2 border-white border-t-transparent animate-spin inline-block"></span>{:else}Start{/if}
                </button>
                <a href="/tests/custom?id={cfg.id}" class="text-xs h-8 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center">Edit</a>
                <button
                  onclick={() => handleDeleteConfig(cfg.id)}
                  class="text-xs h-8 px-2.5 rounded-md border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30"
                  title="Delete"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/></svg>
                </button>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Recent attempts -->
    {#if data.attempts.length > 0}
      <div>
        <h3 class="text-sm font-semibold mb-2 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          Recent Attempts
        </h3>
        <div class="space-y-2">
          {#each data.attempts.slice(0, 15) as att}
            <div class="border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 bg-white dark:bg-zinc-900 flex items-center justify-between gap-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium">{att.name}</span>
                  {#if att.in_progress}
                    <span class="text-[10px] font-medium border rounded-md px-1.5 py-0.5 bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-200 dark:border-amber-700">In progress</span>
                  {/if}
                </div>
                <div class="text-xs text-zinc-500 mt-0.5">
                  {att.total} questions · {formatDate(att.started_at)}
                  {#if !att.in_progress && att.score !== null}
                    · Score: <span class="font-mono tabular-nums font-semibold text-emerald-700 dark:text-emerald-400">{att.score}/{att.total}</span>
                  {/if}
                </div>
              </div>
              <div class="flex items-center gap-1.5 shrink-0">
                {#if att.in_progress}
                  <a href="/test?id={att.id}" class="text-xs h-8 px-3 rounded-md bg-sky-600 text-white font-medium hover:bg-sky-700">Resume</a>
                {:else}
                  <a href="/test-results?id={att.id}" class="text-xs h-8 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800">Results</a>
                  <a href="/test?id={att.id}" class="text-xs h-8 px-3 rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium hover:bg-zinc-800 dark:hover:bg-white">Retake</a>
                {/if}
                <button
                  onclick={() => handleDeleteTest(att.id)}
                  class="text-xs h-8 px-2.5 rounded-md border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30"
                  title="Delete"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/></svg>
                </button>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {:else}
      <div class="text-center py-10 text-sm text-zinc-500">
        No attempts yet. Start a test above to see your history here.
      </div>
    {/if}
  </div>
{/if}
