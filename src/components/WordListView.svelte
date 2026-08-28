<script lang="ts">
  // src/components/WordListView.svelte
  // Lists vocabulary words ranked by frequency.
  // For Syn/Ant pages: sorts by asStem or asOption (overall).
  // For OWS/Idioms/Homonyms/Spelling pages: filters to words that appeared in
  // that specific question type, then sorts by appearance count in that type.

  import WordCard from './WordCard.svelte';
  import type { WordEntry, QTypeExtended } from '../lib/vocab-data';

  let {
    words = [],
    view = 'stems',
    qtypeFilter = null,
    loading = false,
    onSelectWord = () => {},
  }: {
    words?: WordEntry[];
    view: 'stems' | 'options';
    qtypeFilter?: QTypeExtended | null;
    loading?: boolean;
    onSelectWord?: (w: WordEntry) => void;
  } = $props();

  let query = $state('');
  let sort = $state<'frequency' | 'alphabetical'>('frequency');
  let examFilter = $state('all');
  let minStem = $state(0);
  let minOption = $state(0);
  let page = $state(1);
  let showFilters = $state(false);

  const PAGE_SIZE = 60;

  const allExams = $derived(
    Array.from(new Set(words.flatMap((w) => [...w.stemExams, ...w.optionExams]))).sort()
  );

  function countInQtype(w: WordEntry, qt: QTypeExtended): { asStem: number; asOption: number } {
    return {
      asStem: w.qtypesAsStem[qt] ?? 0,
      asOption: w.qtypesAsOption[qt] ?? 0,
    };
  }

  const filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    let result = words.filter((w) => {
      if (q && !w.wordLower.includes(q)) return false;
      if (examFilter !== 'all') {
        if (!w.stemExams.includes(examFilter) && !w.optionExams.includes(examFilter)) return false;
      }
      if (w.asStem < minStem) return false;
      if (w.asOption < minOption) return false;
      return true;
    });

    if (qtypeFilter) {
      result = result.filter((w) => {
        const c = countInQtype(w, qtypeFilter);
        return c.asStem > 0 || c.asOption > 0;
      });
    } else {
      if (view === 'stems') result = result.filter((w) => w.asStem > 0);
      else if (view === 'options') result = result.filter((w) => w.asOption > 0);
    }

    const sorted = [...result];
    if (sort === 'frequency') {
      if (qtypeFilter) {
        const qt = qtypeFilter;
        sorted.sort((a, b) => {
          const ac = countInQtype(a, qt);
          const bc = countInQtype(b, qt);
          if (qt === 'synonym' || qt === 'antonym') {
            const primary = bc.asStem - ac.asStem;
            if (primary !== 0) return primary;
            const sec = bc.asOption - ac.asOption;
            if (sec !== 0) return sec;
            return a.word.localeCompare(b.word);
          }
          const primary = bc.asOption - ac.asOption;
          if (primary !== 0) return primary;
          return a.word.localeCompare(b.word);
        });
      } else if (view === 'stems') {
        sorted.sort((a, b) => b.asStem - a.asStem || (b.total - a.total) || a.word.localeCompare(b.word));
      } else {
        sorted.sort((a, b) => b.asOption - a.asOption || (b.total - a.total) || a.word.localeCompare(b.word));
      }
    } else {
      sorted.sort((a, b) => a.word.localeCompare(b.word));
    }
    return sorted;
  });

  const totalPages = $derived(Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)));
  const currentPage = $derived(Math.min(page, totalPages));
  const pageItems = $derived(filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE));

  function handleQuery(v: string) {
    query = v;
    page = 1;
  }
  function resetFilters() {
    examFilter = 'all';
    minStem = 0;
    minOption = 0;
    query = '';
    page = 1;
  }
</script>

<div class="space-y-4">
  <!-- Search & filter bar -->
  <div class="sticky top-1 z-20 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <div class="relative flex-1 min-w-[200px]">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400 pointer-events-none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
        <input
          type="search"
          value={query}
          on:input={(e) => handleQuery((e.target as HTMLInputElement).value)}
          placeholder="Search words..."
          class="w-full pl-9 pr-3 py-2 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
        />
      </div>
      <select
        bind:value={sort}
        class="h-9 px-3 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
      >
        <option value="frequency">Sort: Frequency</option>
        <option value="alphabetical">Sort: A→Z</option>
      </select>
      <button
        on:click={() => (showFilters = !showFilters)}
        class="h-9 px-3 text-sm rounded-md border {showFilters ? 'bg-orange-500 text-white border-orange-500' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700'} transition-colors"
      >
        Filters
      </button>
    </div>

    {#if showFilters}
      <div class="flex flex-wrap gap-3 pt-1 border-t border-zinc-200 dark:border-zinc-700">
        <div class="flex flex-col gap-1.5 min-w-[200px]">
          <label class="text-[11px] font-medium text-zinc-500">Exam</label>
          <select
            bind:value={examFilter}
            class="h-8 px-2 text-xs bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
          >
            <option value="all">All exams</option>
            {#each allExams as exam}
              <option value={exam}>{exam}</option>
            {/each}
          </select>
        </div>
        <div class="flex flex-col gap-1.5 w-[120px]">
          <label class="text-[11px] font-medium text-zinc-500">Min. Stem count</label>
          <input
            type="number"
            min="0"
            bind:value={minStem}
            class="h-8 px-2 text-xs bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
          />
        </div>
        <div class="flex flex-col gap-1.5 w-[120px]">
          <label class="text-[11px] font-medium text-zinc-500">Min. Option count</label>
          <input
            type="number"
            min="0"
            bind:value={minOption}
            class="h-8 px-2 text-xs bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
          />
        </div>
        <button
          on:click={resetFilters}
          class="h-8 self-end px-3 text-xs text-zinc-600 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-md border border-zinc-200 dark:border-zinc-700"
        >
          Reset
        </button>
      </div>
    {/if}

    <div class="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
      <span>
        <span class="font-semibold text-zinc-900 dark:text-zinc-100">{filtered.length.toLocaleString()}</span>
        words match
        {#if query}
          for &ldquo;<span class="font-medium text-zinc-900 dark:text-zinc-100">{query}</span>&rdquo;
        {/if}
      </span>
      {#if examFilter !== 'all'}
        <span class="text-[10px] font-medium bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded-md">exam: {examFilter}</span>
      {/if}
      {#if minStem > 0}
        <span class="text-[10px] font-medium bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded-md">stem ≥ {minStem}</span>
      {/if}
      {#if minOption > 0}
        <span class="text-[10px] font-medium bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded-md">option ≥ {minOption}</span>
      {/if}
      {#if totalPages > 1}
        <span class="ml-auto">page {currentPage} / {totalPages}</span>
      {/if}
    </div>
  </div>

  <!-- Word grid -->
  {#if loading}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
      {#each Array(12) as _}
        <div class="h-32 rounded-lg bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>
      {/each}
    </div>
  {:else if pageItems.length === 0}
    <div class="text-center py-12 border-2 border-dashed rounded-lg">
      <p class="text-sm text-zinc-500">No words match your search. Try adjusting filters.</p>
    </div>
  {:else}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
      {#each pageItems as w, i (w.wordLower)}
        <WordCard
          word={w}
          rank={(currentPage - 1) * PAGE_SIZE + i + 1}
          {view}
          {qtypeFilter}
          onSelect={onSelectWord}
        />
      {/each}
    </div>
  {/if}

  <!-- Pagination -->
  {#if totalPages > 1}
    <div class="flex items-center justify-center gap-2 pt-2">
      <button
        disabled={currentPage === 1}
        on:click={() => (page = currentPage - 1)}
        class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-zinc-50 dark:hover:bg-zinc-800"
      >
        Previous
      </button>
      <span class="text-sm text-zinc-500 px-2 tabular-nums">{currentPage} / {totalPages}</span>
      <button
        disabled={currentPage === totalPages}
        on:click={() => (page = currentPage + 1)}
        class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-zinc-50 dark:hover:bg-zinc-800"
      >
        Next
      </button>
    </div>
  {/if}
</div>
