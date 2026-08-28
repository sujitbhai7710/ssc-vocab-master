<script lang="ts">
  // src/components/WordAccordion.svelte
  // Lists vocabulary words as expandable accordion cards (like sscenglish.pages.dev).
  // Click a card to expand — details show inline (no navigation to a separate page).
  // MCQs shown as a slider with Prev/Next buttons (exam-style).
  // User clicks an option → green if correct, red if wrong (no default answer shown).

  import type { WordEntry, QType, EnrichedEntry, QuestionEntry, WordQuestions } from '../lib/vocab-data';
  import {
    loadEnrichedForWord,
    buildExampleSentence,
    pronounceWord,
  } from '../lib/vocab-data';
  import MCQCard from './MCQCard.svelte';
  import WordExpansion from './WordExpansion.svelte';

  let {
    words = [],
    view = 'stems',
    qtypeFilter = null,
    restrictToSynAnt = false,
  }: {
    words?: WordEntry[];
    view: 'stems' | 'options';
    qtypeFilter?: QType | null;
    restrictToSynAnt?: boolean;
  } = $props();

  let query = $state('');
  let sort = $state<'frequency' | 'alphabetical'>('frequency');
  let examFilter = $state('all');
  let page = $state(1);
  let showFilters = $state(false);
  let expandedWord = $state<string | null>(null);  // currently expanded wordLower

  const PAGE_SIZE = 30;  // Smaller for accordion (each card takes more space)

  const allExams = $derived(
    Array.from(new Set(words.flatMap((w) => [...w.stemExams, ...w.optionExams]))).sort()
  );

  function countInQtype(w: WordEntry, qt: QType): { asStem: number; asOption: number } {
    return {
      asStem: w.qtypesAsStem[qt] ?? 0,
      asOption: w.qtypesAsOption[qt] ?? 0,
    };
  }
  function getSynAntOptionCount(w: WordEntry): number {
    return (w.qtypesAsOption['synonym'] ?? 0) + (w.qtypesAsOption['antonym'] ?? 0);
  }

  const filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    let result = words.filter((w) => {
      if (q && !w.wordLower.includes(q)) return false;
      if (examFilter !== 'all') {
        if (!w.stemExams.includes(examFilter) && !w.optionExams.includes(examFilter)) return false;
      }
      return true;
    });

    if (restrictToSynAnt) {
      result = result.filter((w) => getSynAntOptionCount(w) > 0);
    } else if (qtypeFilter) {
      result = result.filter((w) => {
        const c = countInQtype(w, qtypeFilter);
        return c.asStem > 0 || c.asOption > 0;
      });
    } else if (view === 'stems') {
      result = result.filter((w) => w.asStem > 0);
    } else if (view === 'options') {
      result = result.filter((w) => w.asOption > 0);
    }

    const sorted = [...result];
    if (sort === 'frequency') {
      if (restrictToSynAnt) {
        sorted.sort((a, b) => getSynAntOptionCount(b) - getSynAntOptionCount(a) || a.word.localeCompare(b.word));
      } else if (qtypeFilter) {
        const qt = qtypeFilter;
        sorted.sort((a, b) => {
          const ac = countInQtype(a, qt);
          const bc = countInQtype(b, qt);
          if (qt === 'synonym' || qt === 'antonym') {
            const p = bc.asStem - ac.asStem;
            if (p !== 0) return p;
            const s = bc.asOption - ac.asOption;
            if (s !== 0) return s;
            return a.word.localeCompare(b.word);
          }
          const p = bc.asStem - ac.asStem;
          if (p !== 0) return p;
          const s = bc.asOption - ac.asOption;
          if (s !== 0) return s;
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
  function toggleExpand(w: WordEntry) {
    if (expandedWord === w.wordLower) {
      expandedWord = null;
    } else {
      expandedWord = w.wordLower;
    }
  }

  const isPhraseQtype = $derived(
    qtypeFilter === 'one-word' || qtypeFilter === 'idiom' || qtypeFilter === 'homonym' || qtypeFilter === 'spelling'
  );
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
          oninput={(e) => handleQuery((e.target as HTMLInputElement).value)}
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
        onclick={() => (showFilters = !showFilters)}
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
        <button
          onclick={() => { examFilter = 'all'; query = ''; page = 1; }}
          class="h-8 self-end px-3 text-xs text-zinc-600 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-md border border-zinc-200 dark:border-zinc-700"
        >
          Reset
        </button>
      </div>
    {/if}

    <div class="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
      <span>
        <span class="font-semibold text-zinc-900 dark:text-zinc-100">{filtered.length.toLocaleString()}</span>
        words · click any card to expand
      </span>
      {#if totalPages > 1}
        <span class="ml-auto">page {currentPage} / {totalPages}</span>
      {/if}
    </div>
  </div>

  <!-- Word accordion list -->
  {#if pageItems.length === 0}
    <div class="text-center py-12 border-2 border-dashed rounded-lg">
      <p class="text-sm text-zinc-500">No words match your search.</p>
    </div>
  {:else}
    <div class="space-y-2">
      {#each pageItems as w, i (w.wordLower)}
        {@const rank = (currentPage - 1) * PAGE_SIZE + i + 1}
        {@const expanded = expandedWord === w.wordLower}
        {@const counts = qtypeFilter ? countInQtype(w, qtypeFilter) : (restrictToSynAnt ? { asStem: w.asStem, asOption: getSynAntOptionCount(w) } : { asStem: w.asStem, asOption: w.asOption })}
        <article class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
          <!-- Header (clickable) -->
          <button
            onclick={() => toggleExpand(w)}
            class="w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
          >
            <span class="text-xs font-mono text-zinc-500 tabular-nums shrink-0 w-7">{rank}.</span>
            <h3 class="text-base font-semibold tracking-tight truncate flex-1 min-w-0">{w.word}</h3>
            <span
              onclick={(e) => { e.stopPropagation(); pronounceWord(w.word); }}
              onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); pronounceWord(w.word); } }}
              role="button"
              tabindex="0"
              class="shrink-0 h-6 w-6 rounded-full flex items-center justify-center bg-zinc-100 dark:bg-zinc-800 hover:bg-orange-100 dark:hover:bg-orange-900 text-zinc-600 dark:text-zinc-300 hover:text-orange-700 dark:hover:text-orange-300 transition-colors"
              title="Pronounce {w.word}"
              aria-label="Pronounce {w.word}"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.72a.99.99 0 0 1-.703.286H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.71a.99.99 0 0 1 .703.286l3.484 3.516A.705.705 0 0 0 11 19.298z"/><path d="M16 9a5 5 0 0 1 0 6"/><path d="M19.364 5.636a9 9 0 0 1 0 12.728"/></svg>
            </span>
            <a
              href={`/word/${w.wordLower}`}
              onclick={(e) => e.stopPropagation()}
              class="shrink-0 h-6 px-2 rounded-full flex items-center gap-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-sky-100 dark:hover:bg-sky-900 text-zinc-600 dark:text-zinc-300 hover:text-sky-700 dark:hover:text-sky-300 transition-colors text-[10px] font-medium"
              title="Open {w.word} detail page"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>
              Page
            </a>
            <span class="shrink-0 text-[11px] text-zinc-500 tabular-nums">
              {#if restrictToSynAnt}
                ✍ {w.asStem} ◆ {counts.asOption}
              {:else if qtypeFilter && isPhraseQtype}
                ✍ {counts.asStem}
              {:else if qtypeFilter}
                ✍ {counts.asStem} ◆ {counts.asOption}
              {:else}
                ✍ {w.asStem} ◆ {w.asOption}
              {/if}
            </span>
            <span class="shrink-0 text-zinc-400">
              {expanded ? '▲' : '▼'}
            </span>
          </button>
          {#if expanded}
            <WordExpansion word={w} qtypeFilter={qtypeFilter} restrictToSynAnt={restrictToSynAnt} />
          {/if}
        </article>
      {/each}
    </div>
  {/if}

  {#if totalPages > 1}
    <div class="flex items-center justify-center gap-2 pt-2">
      <button disabled={currentPage === 1} onclick={() => { page = currentPage - 1; expandedWord = null; }} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-zinc-50 dark:hover:bg-zinc-800">Previous</button>
      <span class="text-sm text-zinc-500 px-2 tabular-nums">{currentPage} / {totalPages}</span>
      <button disabled={currentPage === totalPages} onclick={() => { page = currentPage + 1; expandedWord = null; }} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-zinc-50 dark:hover:bg-zinc-800">Next</button>
    </div>
  {/if}
</div>
