<script lang="ts">
  // src/components/WordDetailView.svelte
  // Standalone word detail page content. Same data as WordExpansion but for /word/[word].
  import type { WordEntry, EnrichedEntry, QuestionEntry, QType } from '../lib/vocab-data';
  import { loadEnrichedForWord, loadWordQuestions, buildExampleSentence, pronounceWord, fetchPronunciation } from '../lib/vocab-data';
  import MCQCard from './MCQCard.svelte';
  import ProblematicButton from './ProblematicButton.svelte';

  let { word }: { word: WordEntry } = $props();

  let enriched = $state<EnrichedEntry | null>(null);
  let stemQuestions = $state<QuestionEntry[]>([]);
  let optionQuestions = $state<QuestionEntry[]>([]);
  let loading = $state(true);
  let pronIpa = $state<string>('');
  let pronLoading = $state(false);

  // MCQ slider state
  let mcqMode = $state<'stem' | 'option' | null>(null);
  let currentMCQIdx = $state(0);

  if (typeof window !== 'undefined') {
    (async () => {
      try {
        const [e, wq] = await Promise.all([
          loadEnrichedForWord(word.wordLower),
          loadWordQuestions(word.wordLower),
        ]);
        enriched = e;
        stemQuestions = wq.asStem || [];
        optionQuestions = wq.asOption || [];
        if (stemQuestions.length > 0) mcqMode = 'stem';
        else if (optionQuestions.length > 0) mcqMode = 'option';
        pronLoading = true;
        fetchPronunciation(word.word).then((p) => { pronIpa = p.ipa || ''; pronLoading = false; });
      } catch (err) {
        console.error(err);
      } finally {
        loading = false;
      }
    })();
  }

  const activeMCQs = $derived.by(() => {
    if (mcqMode === 'stem') return stemQuestions;
    if (mcqMode === 'option') return optionQuestions;
    return [];
  });
  const currentMCQ = $derived(activeMCQs[currentMCQIdx]);

  function setMode(m: 'stem' | 'option') {
    mcqMode = m;
    currentMCQIdx = 0;
  }
  function prevMCQ() { if (currentMCQIdx > 0) currentMCQIdx--; }
  function nextMCQ() { if (currentMCQIdx < activeMCQs.length - 1) currentMCQIdx++; }

  async function playPron() {
    await pronounceWord(word.word);
  }
</script>

{#if loading}
  <!-- SSR-friendly fallback: show the word header immediately (not just a spinner) -->
  <div class="space-y-5">
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-5">
      <div class="flex items-center gap-3 flex-wrap">
        <h1 class="text-3xl font-bold tracking-tight capitalize">{word.word}</h1>
        <div class="h-9 w-9 rounded-full border-2 border-orange-400 border-t-transparent animate-spin"></div>
      </div>
      <div class="text-xs text-zinc-500 mt-2 flex items-center gap-3 flex-wrap">
        <span>✍ as stem: <strong class="text-zinc-700 dark:text-zinc-300">{word.asStem}</strong></span>
        <span>◆ as option: <strong class="text-zinc-700 dark:text-zinc-300">{word.asOption}</strong></span>
        <span>total: <strong class="text-zinc-700 dark:text-zinc-300">{word.total}</strong></span>
      </div>
      <p class="text-xs text-zinc-400 mt-3">Loading definitions, synonyms, and past SSC MCQs…</p>
    </div>
  </div>
{:else}
  <div class="space-y-5">
    <!-- Word header -->
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-5">
      <div class="flex items-start justify-between gap-3 flex-wrap">
        <div class="min-w-0">
          <div class="flex items-center gap-3 flex-wrap">
            <h1 class="text-3xl font-bold tracking-tight capitalize">{word.word}</h1>
            <button onclick={playPron} class="h-9 w-9 rounded-full flex items-center justify-center bg-orange-100 dark:bg-orange-950/40 text-orange-700 dark:text-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900 transition-colors" title="Hear pronunciation" aria-label="Pronounce {word.word}">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.72a.99.99 0 0 1-.703.286H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.71a.99.99 0 0 1 .703.286l3.484 3.516A.705.705 0 0 0 11 19.298z"/><path d="M16 9a5 5 0 0 1 0 6"/><path d="M19.364 5.636a9 9 0 0 1 0 12.728"/></svg>
            </button>
            {#if pronLoading}<span class="text-xs text-zinc-400">loading IPA…</span>{/if}
            {#if pronIpa}<span class="text-sm text-zinc-500 font-mono">{pronIpa}</span>{/if}
          </div>
          <div class="text-xs text-zinc-500 mt-2 flex items-center gap-3 flex-wrap">
            <span>✍ as stem: <strong class="text-zinc-700 dark:text-zinc-300">{word.asStem}</strong></span>
            <span>◆ as option: <strong class="text-zinc-700 dark:text-zinc-300">{word.asOption}</strong></span>
            <span>total: <strong class="text-zinc-700 dark:text-zinc-300">{word.total}</strong></span>
          </div>
        </div>
        <ProblematicButton itemType="vocab" itemKey={word.wordLower} subType="syn-ant" label="Mark problematic" />
      </div>

      {#if enriched?.definition}
        <div class="mt-4 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          <span class="font-semibold text-orange-600 dark:text-orange-400">Meaning: </span>{enriched.definition}
        </div>
      {/if}
      {#if enriched?.pos}<div class="mt-1 text-xs italic text-zinc-500">{enriched.pos}</div>{/if}
      {#if enriched?.bn}<div class="mt-1 text-sm font-bengali text-zinc-700 dark:text-zinc-300" lang="bn">বাংলা: {enriched.bn}</div>{/if}
      {#if enriched?.ex}<div class="mt-3 text-sm text-zinc-600 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded-md border border-zinc-200 dark:border-zinc-700">"{enriched.ex}"</div>{/if}
      {#if enriched?.mnemonic}
        <div class="mt-3 bg-amber-50 dark:bg-amber-950/20 border-l-2 border-amber-300 dark:border-amber-700 p-2.5 rounded-r-md text-sm">
          <span class="font-semibold text-amber-700 dark:text-amber-400">💡 Trick: </span>{enriched.mnemonic}
        </div>
      {/if}
      {#if enriched?.root}
        <div class="mt-3 text-xs text-zinc-500 flex items-center gap-1.5 flex-wrap">
          <span class="font-semibold">Root:</span>
          <span class="font-mono font-bold text-rose-600 dark:text-rose-400">{enriched.root}</span>
          <span>—</span>
          <span>{enriched.rootMeaning}</span>
        </div>
      {/if}
    </div>

    <!-- Synonyms / Antonyms -->
    {#if enriched && (enriched.ssSynonyms.length > 0 || enriched.ssAntonyms.length > 0)}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {#if enriched.ssSynonyms.length > 0}
          <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4">
            <h3 class="text-sm font-semibold mb-2 flex items-center gap-2"><span class="h-2 w-2 rounded-full bg-emerald-500"></span>Synonyms ({enriched.ssSynonyms.length})</h3>
            <div class="flex flex-wrap gap-1.5">
              {#each enriched.ssSynonyms as s}
                <span class="text-xs px-2 py-1 rounded-md border {s.status === 'correct' ? 'bg-emerald-50 border-emerald-300 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-800' : 'bg-zinc-50 border-zinc-200 text-zinc-600 dark:bg-zinc-800/40 dark:text-zinc-400 dark:border-zinc-700'}">{s.word}</span>
              {/each}
            </div>
            <p class="text-[10px] text-zinc-400 mt-2">🟩 = appeared in SSC exams · ⬜ = verified-related (added)</p>
          </div>
        {/if}
        {#if enriched.ssAntonyms.length > 0}
          <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4">
            <h3 class="text-sm font-semibold mb-2 flex items-center gap-2"><span class="h-2 w-2 rounded-full bg-rose-500"></span>Antonyms ({enriched.ssAntonyms.length})</h3>
            <div class="flex flex-wrap gap-1.5">
              {#each enriched.ssAntonyms as s}
                <span class="text-xs px-2 py-1 rounded-md border {s.status === 'correct' ? 'bg-rose-50 border-rose-300 text-rose-800 dark:bg-rose-950/30 dark:text-rose-300 dark:border-rose-800' : 'bg-zinc-50 border-zinc-200 text-zinc-600 dark:bg-zinc-800/40 dark:text-zinc-400 dark:border-zinc-700'}">{s.word}</span>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- MCQ slider -->
    {#if activeMCQs.length > 0}
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4 space-y-3">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <h3 class="text-sm font-semibold">Past SSC MCQs</h3>
          <div class="flex items-center gap-1.5">
            {#if stemQuestions.length > 0}
              <button onclick={() => setMode('stem')} class="text-[11px] h-7 px-2 rounded-md {mcqMode === 'stem' ? 'bg-amber-500 text-white' : 'border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800'}">As stem ({stemQuestions.length})</button>
            {/if}
            {#if optionQuestions.length > 0}
              <button onclick={() => setMode('option')} class="text-[11px] h-7 px-2 rounded-md {mcqMode === 'option' ? 'bg-emerald-500 text-white' : 'border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800'}">As option ({optionQuestions.length})</button>
            {/if}
          </div>
        </div>
        <div class="relative">
          {#if currentMCQ}
            <MCQCard question={currentMCQ} highlightWord={word.wordLower} index={currentMCQIdx} />
          {/if}
          <div class="flex items-center justify-between mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800">
            <button onclick={prevMCQ} disabled={currentMCQIdx === 0} class="flex items-center gap-1.5 text-xs h-8 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-30"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>Previous</button>
            <span class="text-xs text-zinc-500 tabular-nums">{currentMCQIdx + 1} / {activeMCQs.length}</span>
            <button onclick={nextMCQ} disabled={currentMCQIdx === activeMCQs.length - 1} class="flex items-center gap-1.5 text-xs h-8 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-30">Next<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg></button>
          </div>
        </div>
      </div>
    {/if}
  </div>
{/if}
