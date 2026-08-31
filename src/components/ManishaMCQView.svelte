<script lang="ts">
  // src/components/ManishaMCQView.svelte
  // 360 MCQs from Manisha Bansal's grammar rules — click-to-reveal answers.
  // Each MCQ shows: question, 4 options, user clicks → green if correct, red if wrong,
  // correct answer highlighted, explanation shown. Includes: search, category filter,
  // problematic button per MCQ, progress tracking.
  import { onMount, onDestroy } from 'svelte';
  import { isLoggedIn, loadSession, onAuthChange } from '../lib/auth';
  import ProblematicButton from './ProblematicButton.svelte';
  import ProgressTracker from './ProgressTracker.svelte';

  interface MCQ {
    num: number;
    q: string;
    opts: string[];
    ans: number;
    exp: string;
    rule: string;
  }

  let mcqs = $state<MCQ[]>([]);
  let loading = $state(true);
  let query = $state('');
  let catFilter = $state('all');
  let page = $state(1);
  const PAGE_SIZE = 10;

  // Per-MCQ state: which option the user selected (null = not answered)
  let selectedAnswers = $state<Record<number, number | null>>({});

  // Categories derived from the 'rule' field
  const categories = $derived.by(() => {
    const set = new Set(mcqs.map(m => m.rule));
    return [{ key: 'all', label: 'All' }, ...Array.from(set).sort().map(r => ({ key: r, label: r }))];
  });

  if (typeof window !== 'undefined') {
    (async () => {
      try {
        const res = await fetch('/data/manisha/mcqs.json');
        if (res.ok) mcqs = await res.json();
      } catch (e) { console.error('Failed to load manisha mcqs:', e); }
      finally { loading = false; }
    })();
  }

  const filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    return mcqs.filter((m) => {
      if (catFilter !== 'all' && m.rule !== catFilter) return false;
      if (q) {
        const haystack = `${m.num} ${m.q} ${m.exp} ${m.rule} ${m.opts.join(' ')}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  });

  const totalPages = $derived(Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)));
  const currentPage = $derived(Math.min(page, totalPages));
  const pageItems = $derived(filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE));

  // Stats
  const attempted = $derived(Object.keys(selectedAnswers).filter(k => selectedAnswers[Number(k)] !== null).length);
  const correct = $derived(Object.entries(selectedAnswers).filter(([k, v]) => v !== null && mcqs.find(m => m.num === Number(k))?.ans === v).length);
  const wrong = $derived(attempted - correct);

  function handleClick(mcqNum: number, optIdx: number) {
    if (selectedAnswers[mcqNum] !== null && selectedAnswers[mcqNum] !== undefined) return;
    selectedAnswers[mcqNum] = optIdx;
    selectedAnswers = { ...selectedAnswers };
  }

  function reset() {
    selectedAnswers = {};
  }

  function handleQuery(v: string) { query = v; page = 1; }
</script>

<div class="space-y-4">
  <!-- Stats bar -->
  <div class="grid grid-cols-3 gap-2">
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 text-center">
      <div class="text-2xl font-bold tabular-nums text-zinc-900 dark:text-zinc-100">{attempted}</div>
      <div class="text-[10px] text-zinc-500 uppercase tracking-wide">Attempted</div>
    </div>
    <div class="bg-white dark:bg-zinc-900 border border-emerald-200 dark:border-emerald-800 rounded-lg p-3 text-center">
      <div class="text-2xl font-bold tabular-nums text-emerald-600 dark:text-emerald-400">{correct}</div>
      <div class="text-[10px] text-zinc-500 uppercase tracking-wide">Correct</div>
    </div>
    <div class="bg-white dark:bg-zinc-900 border border-rose-200 dark:border-rose-800 rounded-lg p-3 text-center">
      <div class="text-2xl font-bold tabular-nums text-rose-600 dark:text-rose-400">{wrong}</div>
      <div class="text-[10px] text-zinc-500 uppercase tracking-wide">Wrong</div>
    </div>
  </div>

  <!-- Search & filter bar -->
  <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <div class="relative flex-1 min-w-[200px]">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400 pointer-events-none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        <input
          type="search"
          value={query}
          oninput={(e) => handleQuery((e.target as HTMLInputElement).value)}
          placeholder="Search questions..."
          class="w-full pl-9 pr-3 py-2 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
        />
      </div>
      <select
        bind:value={catFilter}
        onchange={() => { page = 1; }}
        class="h-9 px-3 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
      >
        {#each categories as c}
          <option value={c.key}>{c.label}</option>
        {/each}
      </select>
      <button
        onclick={reset}
        class="h-9 px-3 text-sm rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800"
      >↺ Reset</button>
    </div>
    <div class="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
      <span><span class="font-semibold text-zinc-900 dark:text-zinc-100">{filtered.length}</span> questions</span>
      {#if totalPages > 1}<span class="ml-auto">page {currentPage} / {totalPages}</span>{/if}
    </div>
  </div>

  <ProgressTracker client:idle pageType="manisha-mcq" total={360} />

  {#if loading}
    <div class="space-y-3">
      {#each Array(5) as _}<div class="h-32 rounded-xl bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>{/each}
    </div>
  {:else if pageItems.length === 0}
    <div class="text-center py-12 border-2 border-dashed rounded-lg">
      <p class="text-sm text-zinc-500">No questions match your search.</p>
    </div>
  {:else}
    <div class="space-y-3">
      {#each pageItems as m (m.num)}
        {@const selected = selectedAnswers[m.num]}
        {@const answered = selected !== null && selected !== undefined}
        {@const isCorrect = answered && selected === m.ans}
        {@const clickedWrong = answered && selected !== m.ans}
        <div class="bg-white dark:bg-zinc-900 border rounded-lg overflow-hidden {isCorrect ? 'border-emerald-300 dark:border-emerald-700' : clickedWrong ? 'border-rose-300 dark:border-rose-700' : 'border-zinc-200 dark:border-zinc-700'}">
          <div class="px-4 pt-3 pb-2 flex items-center justify-between gap-2 flex-wrap border-b border-zinc-100 dark:border-zinc-800">
            <div class="text-sm font-semibold flex items-center gap-2 flex-wrap">
              <span class="text-xs font-mono text-zinc-500 tabular-nums">Q{m.num}</span>
              <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 bg-amber-100 text-amber-900 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800">{m.rule}</span>
            </div>
            <ProblematicButton itemType="manisha-mcq" itemKey={String(m.num)} subType={m.rule} label="Mark" />
          </div>
          <div class="px-4 pb-4 space-y-3">
            <div class="text-sm text-zinc-800 dark:text-zinc-200 font-medium pt-2 break-words">{m.q}</div>
            <div class="grid grid-cols-1 gap-2">
              {#each m.opts as opt, i}
                {@const letter = String.fromCharCode(65 + i)}
                {@const isSelected = selected === i}
                {@const isCorrectOpt = i === m.ans}
                {@const clickedCorrect = answered && isSelected && isCorrectOpt}
                {@const clickedWrongOpt = answered && isSelected && !isCorrectOpt}
                {@const missedCorrect = answered && !isSelected && isCorrectOpt}
                <button
                  onclick={() => handleClick(m.num, i)}
                  disabled={answered}
                  class="flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors text-left
                  {clickedCorrect
                    ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
                    : clickedWrongOpt
                      ? 'bg-rose-100 border-rose-400 text-rose-900 dark:bg-rose-950/50 dark:text-rose-100 dark:border-rose-700'
                      : missedCorrect
                        ? 'bg-emerald-50 border-emerald-300 text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100 dark:border-emerald-700'
                        : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 hover:border-orange-400/40 enabled:hover:bg-zinc-50 dark:enabled:hover:bg-zinc-800/50'}">
                  <span class="font-mono text-xs font-bold text-zinc-500 w-5">({letter})</span>
                  <span class="font-medium break-words">{opt}</span>
                  {#if clickedCorrect}
                    <span class="ml-auto text-[10px] font-bold text-emerald-700 dark:text-emerald-300 uppercase shrink-0">✓ Correct</span>
                  {:else if clickedWrongOpt}
                    <span class="ml-auto text-[10px] font-bold text-rose-700 dark:text-rose-300 uppercase shrink-0">✗ Wrong</span>
                  {:else if missedCorrect}
                    <span class="ml-auto text-[10px] font-bold text-emerald-700 dark:text-emerald-300 uppercase shrink-0">✓ Correct</span>
                  {/if}
                </button>
              {/each}
            </div>
            {#if answered}
              <div class="bg-sky-50 dark:bg-sky-950/20 border-l-4 border-sky-400 dark:border-sky-700 p-3 rounded-md">
                <div class="text-[10px] uppercase font-semibold text-sky-700 dark:text-sky-400 mb-1">{isCorrect ? '🎉 Correct!' : '❌ Wrong answer'}</div>
                <p class="text-xs leading-relaxed text-zinc-800 dark:text-zinc-200">{m.exp}</p>
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}

  {#if totalPages > 1}
    <div class="flex items-center justify-center gap-2 pt-2">
      <button disabled={currentPage === 1} onclick={() => page = currentPage - 1} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 hover:bg-zinc-50 dark:hover:bg-zinc-800">Previous</button>
      <span class="text-sm text-zinc-500 px-2 tabular-nums">{currentPage} / {totalPages}</span>
      <button disabled={currentPage === totalPages} onclick={() => page = currentPage + 1} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 hover:bg-zinc-50 dark:hover:bg-zinc-800">Next</button>
    </div>
  {/if}
</div>
