<script lang="ts">
  // src/components/QuestionListView.svelte
  // Generic list view for "question-type" sections (OWS, Idioms, Homonyms, Spelling).
  // Unlike WordListView (which shows vocabulary words), this shows the actual
  // questions themselves, with search, sort, exam filter, pagination.

  import type { QuestionEntry } from '../lib/vocab-data';

  let {
    questions = [],
    qtype = 'one-word',
    loading = false,
    onSelectQuestion = () => {},
  }: {
    questions?: QuestionEntry[];
    qtype: 'one-word' | 'idiom' | 'homonym' | 'spelling';
    loading?: boolean;
    onSelectQuestion?: (q: QuestionEntry) => void;
  } = $props();

  let query = $state('');
  let examFilter = $state('all');
  let page = $state(1);
  const PAGE_SIZE = 30;

  const allExams = $derived(
    Array.from(new Set(questions.map((q) => q.exam))).sort()
  );

  const filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    let result = questions.filter((qq) => {
      if (q) {
        const blob = (qq.stem + ' ' + qq.options.join(' ')).toLowerCase();
        if (!blob.includes(q)) return false;
      }
      if (examFilter !== 'all' && qq.exam !== examFilter) return false;
      return true;
    });
    // Sort by exam, then by question number
    result = [...result].sort((a, b) => a.exam.localeCompare(b.exam) || a.qno - b.qno);
    return result;
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
    query = '';
    page = 1;
  }

  const sectionTitle: Record<string, string> = {
    'one-word': 'One-Word Substitution',
    idiom: 'Idioms & Phrases',
    homonym: 'Homonyms & Homophones',
    spelling: 'Spelling',
  };
  const qtypeColor: Record<string, string> = {
    'one-word': 'bg-violet-100 text-violet-900 border-violet-300 dark:bg-violet-950/40 dark:text-violet-200 dark:border-violet-800',
    idiom: 'bg-orange-100 text-orange-900 border-orange-300 dark:bg-orange-950/40 dark:text-orange-200 dark:border-orange-800',
    homonym: 'bg-pink-100 text-pink-900 border-pink-300 dark:bg-pink-950/40 dark:text-pink-200 dark:border-pink-800',
    spelling: 'bg-sky-100 text-sky-900 border-sky-300 dark:bg-sky-950/40 dark:text-sky-200 dark:border-sky-800',
  };
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
          placeholder={`Search ${sectionTitle[qtype].toLowerCase()} questions...`}
          class="w-full pl-9 pr-3 py-2 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
        />
      </div>
      <select
        bind:value={examFilter}
        class="h-9 px-3 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400/40"
      >
        <option value="all">All exams</option>
        {#each allExams as exam}
          <option value={exam}>{exam}</option>
        {/each}
      </select>
      {#if examFilter !== 'all' || query}
        <button
          on:click={resetFilters}
          class="h-9 px-3 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md hover:bg-zinc-50 dark:hover:bg-zinc-800"
        >
          Reset
        </button>
      {/if}
    </div>
    <div class="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
      <span>
        <span class="font-semibold text-zinc-900 dark:text-zinc-100">{filtered.length.toLocaleString()}</span>
        questions match
      </span>
      {#if totalPages > 1}
        <span class="ml-auto">page {currentPage} / {totalPages}</span>
      {/if}
    </div>
  </div>

  <!-- Question list -->
  {#if loading}
    <div class="space-y-3">
      {#each Array(10) as _}
        <div class="h-32 rounded-lg bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>
      {/each}
    </div>
  {:else if pageItems.length === 0}
    <div class="text-center py-12 border-2 border-dashed rounded-lg">
      <p class="text-sm text-zinc-500">No questions match your search. Try adjusting filters.</p>
    </div>
  {:else}
    <div class="space-y-3">
      {#each pageItems as q (q.id)}
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden hover:shadow-md hover:border-orange-400/40 transition-all">
          <div class="px-4 pt-3 pb-2 flex items-center justify-between gap-2 flex-wrap">
            <div class="text-sm font-semibold flex items-center gap-2 flex-wrap">
              <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 {qtypeColor[qtype]}">{sectionTitle[qtype]}</span>
              <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 bg-zinc-100 text-zinc-700 dark:bg-zinc-800/50 dark:text-zinc-300 dark:border-zinc-700">{q.exam} · Q{q.qno}</span>
            </div>
          </div>
          <div class="px-4 pb-4 space-y-3">
            {#if qtype === 'one-word' || qtype === 'idiom' || qtype === 'homonym' || qtype === 'spelling'}
              <div class="text-sm text-zinc-700 dark:text-zinc-300 italic leading-relaxed bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded-md border border-zinc-200 dark:border-zinc-700">
                &ldquo;{q.stem}&rdquo;
              </div>
            {/if}
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {#each q.options as opt, i}
                {@const letter = String.fromCharCode(65 + i)}
                {@const isCorrect = q.correctIdx === i}
                <div class="flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors {isCorrect
                  ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
                  : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 hover:border-orange-400/40'}">
                  <span class="font-mono text-xs font-bold text-zinc-500 w-5">({letter})</span>
                  <span class="font-medium">{opt}</span>
                  {#if isCorrect}
                    <span class="ml-auto text-[10px] font-bold text-emerald-700 dark:text-emerald-300 uppercase tracking-wide">Answer</span>
                  {/if}
                </div>
              {/each}
            </div>
            <p class="text-[11px] text-zinc-500 leading-relaxed">
              Best-guess answer highlighted in green. Source PDFs do not include official answer keys.
            </p>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Pagination -->
  {#if totalPages > 1}
    <div class="flex items-center justify-center gap-2 pt-2">
      <button disabled={currentPage === 1} on:click={() => (page = currentPage - 1)} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-zinc-50 dark:hover:bg-zinc-800">Previous</button>
      <span class="text-sm text-zinc-500 px-2 tabular-nums">{currentPage} / {totalPages}</span>
      <button disabled={currentPage === totalPages} on:click={() => (page = currentPage + 1)} class="px-3 py-1.5 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-zinc-50 dark:hover:bg-zinc-800">Next</button>
    </div>
  {/if}
</div>
