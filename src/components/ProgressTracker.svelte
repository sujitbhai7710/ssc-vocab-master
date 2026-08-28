<script lang="ts">
  // src/components/ProgressTracker.svelte
  // "From / To / Set Done" range tracker + read-till, persisted per page_type.
  // Shows completed count / total with a progress bar.
  import { onMount } from 'svelte';
  import { isLoggedIn, loadProgress, saveProgressRange, resetProgressCompleted, type ProgressMap } from '../lib/auth';

  let { pageType, total }: { pageType: string; total: number } = $props();

  let completed = $state<number[]>([]);
  let fromVal = $state<string>('1');
  let toVal = $state<string>('');
  let busy = $state(false);
  let msg = $state('');
  let loaded = $state(false);

  onMount(async () => {
    if (!isLoggedIn()) { loaded = true; return; }
    try {
      const p: ProgressMap = await loadProgress();
      completed = p[pageType]?.completed || [];
      if (completed.length > 0) {
        const maxDone = Math.max(...completed);
        toVal = String(maxDone);
      } else {
        toVal = String(Math.min(25, total));
      }
    } catch {} finally {
      loaded = true;
    }
  });

  const doneCount = $derived(completed.length);
  const pct = $derived(total > 0 ? Math.round((doneCount / total) * 100) : 0);

  async function setRange() {
    const from = parseInt(fromVal, 10);
    const to = parseInt(toVal, 10);
    if (!Number.isFinite(from) || !Number.isFinite(to) || from < 1 || to < from) {
      msg = 'Enter a valid From and To (From ≥ 1, To ≥ From).';
      return;
    }
    if (!isLoggedIn()) {
      window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
      return;
    }
    busy = true; msg = '';
    const r = await saveProgressRange(pageType, from, to);
    if (r.ok && r.completed) {
      completed = r.completed;
      msg = `Marked ${from}–${to} as done. (${doneCount}/${total})`;
    } else {
      msg = 'Failed to save.';
    }
    busy = false;
  }

  async function reset() {
    busy = true; msg = '';
    const ok = await resetProgressCompleted(pageType);
    if (ok) { completed = []; msg = 'Progress reset.'; }
    busy = false;
  }
</script>

{#if loaded && isLoggedIn()}
  <div class="bg-gradient-to-r from-emerald-50 to-sky-50 dark:from-emerald-950/30 dark:to-sky-950/30 border border-emerald-200 dark:border-emerald-800 rounded-lg p-3 space-y-2">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-emerald-600"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
        <span class="text-xs font-semibold text-emerald-800 dark:text-emerald-300">Your progress</span>
      </div>
      <div class="flex items-center gap-2">
        {#if busy}<span class="h-3 w-3 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin"></span>{/if}
        <span class="text-xs text-zinc-600 dark:text-zinc-300 tabular-nums">{doneCount} / {total} done</span>
        <span class="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">{pct}%</span>
      </div>
    </div>
    <div class="h-2 bg-emerald-100 dark:bg-emerald-950/50 rounded-full overflow-hidden">
      <div class="h-full bg-gradient-to-r from-emerald-500 to-sky-500 transition-all" style="width: {pct}%"></div>
    </div>
    <!-- Range input: From / To / Set Done -->
    <div class="flex items-center gap-1.5 flex-wrap">
      <span class="text-[11px] text-zinc-500">Mark range done:</span>
      <span class="text-[11px] text-zinc-500">From</span>
      <input
        type="number" min="1" max={total} value={fromVal}
        oninput={(e) => (fromVal = (e.target as HTMLInputElement).value)}
        class="w-16 h-7 px-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-emerald-400/40"
      />
      <span class="text-[11px] text-zinc-500">to</span>
      <input
        type="number" min="1" max={total} value={toVal}
        oninput={(e) => (toVal = (e.target as HTMLInputElement).value)}
        class="w-16 h-7 px-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-emerald-400/40"
      />
      <button onclick={setRange} disabled={busy} class="text-[11px] h-7 px-3 rounded-md bg-emerald-600 text-white font-medium hover:bg-emerald-700 disabled:opacity-50">
        Set done
      </button>
      <button onclick={reset} disabled={busy} class="text-[10px] h-7 px-2 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-white dark:hover:bg-zinc-800">Reset</button>
    </div>
    {#if msg}<p class="text-[10px] text-emerald-700 dark:text-emerald-400">{msg}</p>{/if}
  </div>
{/if}
