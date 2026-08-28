<script lang="ts">
  // src/components/WordExpansion.svelte
  // Inline expansion of a word — shows definition, Bengali, mnemonic, root family, synonyms/antonyms, and MCQ slider.

  import type { WordEntry, QType, EnrichedEntry, QuestionEntry, WordQuestions } from '../lib/vocab-data';
  import {
    loadEnrichedForWord,
    loadQuestions,
    buildExampleSentence,
    pronounceWord,
  } from '../lib/vocab-data';
  import MCQCard from './MCQCard.svelte';

  let {
    word,
    qtypeFilter = null,
    restrictToSynAnt = false,
  }: {
    word: WordEntry;
    qtypeFilter?: QType | null;
    restrictToSynAnt?: boolean;
  } = $props();

  let enriched = $state<EnrichedEntry | null>(null);
  let allQuestions = $state<QuestionEntry[]>([]);
  let stemQuestionIds = $state<number[]>([]);
  let optionQuestionIds = $state<number[]>([]);
  let loading = $state(true);

  // MCQ slider state
  let mcqMode = $state<'stem' | 'option' | null>(null); // which section we're viewing
  let currentMCQIdx = $state(0); // index within the current set

  if (typeof window !== 'undefined') {
    (async () => {
      try {
        const e = await loadEnrichedForWord(word.wordLower);
        const { questions, wordQuestions } = await loadQuestions();
        const wq: WordQuestions = wordQuestions[word.wordLower] || { asStem: [], asOption: [] };
        enriched = e;
        allQuestions = questions;

        // FILTER MCQs by current section's qtype — DON'T mix question types.
        // E.g., when on /stems (syn/ant section), only show syn/ant questions,
        // not spelling/idiom/ows/homonym questions even if the same word appeared there.
        const filterQids = (ids: number[]): number[] => {
          if (!qtypeFilter && !restrictToSynAnt) return ids; // no filter (home page word click)
          return ids.filter((id) => {
            const q = questions[id];
            if (!q) return false;
            if (restrictToSynAnt) {
              // /options page — only syn/ant option questions
              return q.qtype === 'synonym' || q.qtype === 'antonym';
            }
            if (qtypeFilter === 'synonym' || qtypeFilter === 'antonym') {
              // /stems page — syn OR ant (since they share the same page)
              return q.qtype === 'synonym' || q.qtype === 'antonym';
            }
            return q.qtype === qtypeFilter;
          });
        };

        stemQuestionIds = filterQids(wq.asStem);
        optionQuestionIds = filterQids(wq.asOption);
        // Default: stem mode if any stem questions, else option mode
        if (stemQuestionIds.length > 0) {
          mcqMode = 'stem';
        } else if (optionQuestionIds.length > 0) {
          mcqMode = 'option';
        }
        loading = false;
      } catch (err) {
        console.error('Failed to load word expansion:', err);
        loading = false;
      }
    })();
  }

  const sscSynonyms = $derived(enriched?.ssSynonyms ?? []);
  const sscAntonyms = $derived(enriched?.ssAntonyms ?? []);
  const hasDefinition = $derived(!!enriched?.definition);
  const hasMnemonic = $derived(!!enriched?.mnemonic);
  const hasRoot = $derived(!!enriched?.root);
  const hasRootFamily = $derived(!!enriched?.rootFamily && enriched.rootFamily.length > 0);
  const exampleSentence = $derived(enriched?.ex || buildExampleSentence(word.word, enriched?.pos));

  const allExams = $derived(
    Array.from(new Set([...word.stemExams, ...word.optionExams]))
  );

  // Active MCQ set (based on mode)
  const activeMCQIds = $derived(mcqMode === 'stem' ? stemQuestionIds : mcqMode === 'option' ? optionQuestionIds : []);
  const activeMCQs = $derived(activeMCQIds.map((id) => allQuestions[id]).filter(Boolean));
  const currentMCQ = $derived(activeMCQs[currentMCQIdx]);

  function setMode(mode: 'stem' | 'option') {
    mcqMode = mode;
    currentMCQIdx = 0;
  }
  function prevMCQ() {
    if (currentMCQIdx > 0) currentMCQIdx--;
  }
  function nextMCQ() {
    if (currentMCQIdx < activeMCQs.length - 1) currentMCQIdx++;
  }
</script>

<div class="px-4 pb-4 pt-2 border-t border-zinc-200 dark:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-800/20 space-y-4">
  {#if loading}
    <div class="flex items-center gap-3 text-sm text-zinc-500 py-4">
      <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
      <span>Loading details...</span>
    </div>
  {:else}
    <!-- Header: badges + Bengali meaning -->
    <div class="space-y-2">
      <div class="flex flex-wrap items-baseline gap-3">
        {#if enriched?.pos}
          <span class="text-xs italic text-zinc-500">{enriched.pos}</span>
        {/if}
        {#if enriched?.bn}
          <span class="text-sm font-bengali text-zinc-700 dark:text-zinc-300" lang="bn">{enriched.bn}</span>
        {/if}
        <span class="text-[11px] text-zinc-500 tabular-nums">
          {#if restrictToSynAnt}
            ✍ {word.asStem} · ◆ {((word.qtypesAsOption['synonym'] ?? 0) + (word.qtypesAsOption['antonym'] ?? 0))} · Total {word.total}
          {:else if qtypeFilter}
            ✍ {word.qtypesAsStem[qtypeFilter] ?? 0} · ◆ {word.qtypesAsOption[qtypeFilter] ?? 0} · Total {word.total}
          {:else}
            ✍ {word.asStem} · ◆ {word.asOption} · Total {word.total}
          {/if}
        </span>
      </div>
    </div>

    <!-- Definition + Bengali -->
    {#if hasDefinition}
      <p class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed">
        <span class="text-[10px] uppercase font-semibold text-zinc-500 mr-1">meaning.</span>
        {enriched!.definition}
      </p>
    {/if}

    <!-- Mnemonic -->
    {#if hasMnemonic}
      <p class="text-xs leading-relaxed text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/30 p-2 rounded-md border-l-4 border-amber-400 dark:border-amber-700">
        <span class="font-semibold">💡 TRICK: </span>{enriched!.mnemonic}
      </p>
    {/if}

    <!-- Example sentence -->
    <blockquote class="text-xs italic leading-relaxed text-zinc-700 dark:text-zinc-300 border-l-2 border-sky-300 pl-3 py-1">
      &ldquo;{exampleSentence}&rdquo;
    </blockquote>

    <!-- Root word + family -->
    {#if hasRoot}
      <div class="bg-violet-50 dark:bg-violet-950/20 p-2.5 rounded-md border border-violet-200 dark:border-violet-800">
        <div class="text-xs">
          <span class="text-violet-600">🌱</span>
          <span class="font-mono font-bold ml-1">{enriched!.root}</span>
          <span class="text-zinc-500 mx-1.5">=</span>
          <span>{enriched!.rootMeaning}</span>
          {#if enriched!.rootBn}
            <span class="text-zinc-500 mx-1.5">·</span>
            <span class="font-bengali" lang="bn">{enriched!.rootBn}</span>
          {/if}
        </div>
        {#if hasRootFamily}
          <details class="mt-2">
            <summary class="text-[11px] font-medium text-violet-700 dark:text-violet-400 cursor-pointer hover:underline">
              Show full family ({enriched!.rootFamily.length} words) →
            </summary>
            <ul class="mt-2 space-y-1.5 max-h-72 overflow-y-auto pr-1">
              {#each enriched!.rootFamily as fam (fam.wLower)}
                {@const isCurrent = fam.wLower === word.wordLower}
                <li class="text-xs leading-relaxed {isCurrent ? 'bg-amber-100 dark:bg-amber-950/40 p-1.5 rounded-md' : ''}">
                  <div class="flex items-baseline gap-2 flex-wrap">
                    <span class="font-semibold {isCurrent ? 'text-amber-900 dark:text-amber-200' : ''}">{fam.w}</span>
                    {#if fam.pos}
                      <span class="text-[10px] italic text-zinc-500">{fam.pos}</span>
                    {/if}
                    {#if fam.n}
                      <span class="text-[10px] text-zinc-500 ml-auto tabular-nums">{fam.n}× in PYQ</span>
                    {/if}
                  </div>
                  {#if fam.mean}
                    <div class="text-zinc-700 dark:text-zinc-300">{fam.mean}</div>
                  {/if}
                  {#if fam.bn}
                    <div class="text-zinc-600 dark:text-zinc-400 font-bengali" lang="bn">{fam.bn}</div>
                  {/if}
                  {#if fam.mn}
                    <div class="text-[11px] text-amber-700 dark:text-amber-400 italic">💡 {fam.mn}</div>
                  {/if}
                </li>
              {/each}
            </ul>
          </details>
        {/if}
      </div>
    {/if}

    <!-- Synonyms & Antonyms (TWO colors only: green=from SSC, gray=added from WordNet) -->
    {#if sscSynonyms.length > 0 || sscAntonyms.length > 0}
      <div class="space-y-2">
        <div class="text-[10px] text-zinc-500 flex flex-wrap items-center gap-3">
          <span class="flex items-center gap-1">
            <span class="w-2.5 h-2.5 rounded border border-emerald-400 bg-emerald-100"></span>
            appeared in past SSC
          </span>
          <span class="flex items-center gap-1">
            <span class="w-2.5 h-2.5 rounded border border-zinc-300 bg-zinc-100"></span>
            added from WordNet (not in SSC)
          </span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
          {#if sscSynonyms.length > 0}
            <div>
              <div class="text-[10px] uppercase font-semibold text-zinc-500 mb-1.5">Synonyms</div>
              <div class="flex flex-wrap gap-1">
                {#each sscSynonyms as s}
                  <span class="text-xs font-medium border rounded-md px-2 py-1 {s.status === 'correct'
                    ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
                    : 'bg-zinc-100 border-zinc-300 text-zinc-600 dark:bg-zinc-800/40 dark:text-zinc-400 dark:border-zinc-700'}">
                    {s.word}
                  </span>
                {/each}
              </div>
            </div>
          {/if}
          {#if sscAntonyms.length > 0}
            <div>
              <div class="text-[10px] uppercase font-semibold text-zinc-500 mb-1.5">Antonyms</div>
              <div class="flex flex-wrap gap-1">
                {#each sscAntonyms as a}
                  <span class="text-xs font-medium border rounded-md px-2 py-1 {a.status === 'correct'
                    ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
                    : 'bg-zinc-100 border-zinc-300 text-zinc-600 dark:bg-zinc-800/40 dark:text-zinc-400 dark:border-zinc-700'}">
                    {a.word}
                  </span>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      </div>
    {/if}

    <!-- Exam list -->
    {#if allExams.length > 0}
      <div class="flex flex-wrap gap-1.5">
        <span class="text-[10px] uppercase font-semibold text-zinc-500 self-center mr-1">Exams:</span>
        {#each allExams as exam}
          {@const isStem = word.stemExams.includes(exam)}
          {@const isOption = word.optionExams.includes(exam)}
          <span class="text-[10px] font-medium border rounded-md px-1.5 py-0.5 {isStem && isOption
            ? 'bg-amber-50 border-amber-200 dark:bg-amber-950/30 dark:border-amber-800'
            : isStem
              ? 'bg-amber-50 border-amber-200 dark:bg-amber-950/30 dark:border-amber-800'
              : 'bg-emerald-50 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-800'}">
            {exam}{isStem && isOption ? ' (S+O)' : isStem ? ' (S)' : ' (O)'}
          </span>
        {/each}
      </div>
    {/if}

    <!-- PYQs section: slider with Prev/Next -->
    {#if activeMCQs.length > 0}
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg p-3 space-y-3">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <h4 class="text-sm font-semibold flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-600"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>
            Past SSC MCQs
          </h4>
          <div class="flex items-center gap-1.5">
            {#if stemQuestionIds.length > 0}
              <button
                onclick={() => setMode('stem')}
                class="text-[11px] h-7 px-2 rounded-md {mcqMode === 'stem' ? 'bg-amber-500 text-white' : 'border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800'}"
              >
                As stem ({stemQuestionIds.length})
              </button>
            {/if}
            {#if optionQuestionIds.length > 0}
              <button
                onclick={() => setMode('option')}
                class="text-[11px] h-7 px-2 rounded-md {mcqMode === 'option' ? 'bg-emerald-500 text-white' : 'border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800'}"
              >
                As option ({optionQuestionIds.length})
              </button>
            {/if}
          </div>
        </div>

        <!-- Slider -->
        <div class="relative">
          {#if currentMCQ}
            <MCQCard question={currentMCQ} highlightWord={word.wordLower} index={currentMCQIdx} />
          {/if}

          <!-- Nav: Prev / Next -->
          <div class="flex items-center justify-between mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-800">
            <button
              onclick={prevMCQ}
              disabled={currentMCQIdx === 0}
              class="flex items-center gap-1.5 text-xs h-8 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
              Previous
            </button>
            <span class="text-xs text-zinc-500 tabular-nums">
              {currentMCQIdx + 1} / {activeMCQs.length}
            </span>
            <button
              onclick={nextMCQ}
              disabled={currentMCQIdx === activeMCQs.length - 1}
              class="flex items-center gap-1.5 text-xs h-8 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Next
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </button>
          </div>
        </div>
      </div>
    {/if}
  {/if}
</div>
