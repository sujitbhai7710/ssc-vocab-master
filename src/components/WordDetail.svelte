<script lang="ts">
  // src/components/WordDetail.svelte
  import FrequencyBadge from './FrequencyBadge.svelte';
  import MCQCard from './MCQCard.svelte';
  import type { WordEntry, EnrichedEntry, QuestionEntry } from '../lib/vocab-data';
  import {
    loadEnrichedForWord,
    loadQuestions,
    buildExampleSentence,
  } from '../lib/vocab-data';

  let {
    word,
    onBack = () => {},
  }: {
    word: WordEntry;
    onBack?: () => void;
  } = $props();

  let enriched = $state<EnrichedEntry | null>(null);
  let allQuestions = $state<QuestionEntry[]>([]);
  let stemQuestionIds = $state<number[]>([]);
  let optionQuestionIds = $state<number[]>([]);
  let error = $state<string | null>(null);
  let loading = $state(true);

  $effect(() => {
    const wordLower = word.wordLower;
    let cancelled = false;
    loading = true;
    error = null;
    (async () => {
      try {
        const e = await loadEnrichedForWord(wordLower);
        if (cancelled) return;
        const { questions, wordQuestions } = await loadQuestions();
        if (cancelled) return;
        const wq = wordQuestions[wordLower] || { asStem: [], asOption: [] };
        enriched = e;
        allQuestions = questions;
        stemQuestionIds = wq.asStem;
        optionQuestionIds = wq.asOption;
        loading = false;
      } catch (err) {
        console.error('Failed to load word detail:', err);
        if (!cancelled) {
          error = err instanceof Error ? err.message : 'Unknown error';
          loading = false;
        }
      }
    })();
    return () => { cancelled = true; };
  });

  // All stem questions first (where the word is the question stem)
  const stemQuestions = $derived(
    stemQuestionIds.map((id) => allQuestions[id]).filter(Boolean)
  );
  // Then all option questions (where the word is one of the options)
  const optionQuestions = $derived(
    optionQuestionIds.map((id) => allQuestions[id]).filter(Boolean)
  );
  const totalMCQs = $derived(stemQuestions.length + optionQuestions.length);

  const sscSynonyms = $derived(enriched?.ssSynonyms ?? []);
  const sscAntonyms = $derived(enriched?.ssAntonyms ?? []);
  const hasDefinition = $derived(!!enriched?.definition);
  const hasRoot = $derived(!!enriched?.root);
  const hasMnemonic = $derived(!!enriched?.mnemonic);
  const exampleSentence = $derived(buildExampleSentence(word.word, enriched?.pos));

  const allExams = $derived(
    Array.from(new Set([...word.stemExams, ...word.optionExams]))
  );

  // Count of correct vs distractor vs added
  const synStats = $derived.by(() => {
    let correct = 0, distractor = 0, added = 0;
    for (const s of sscSynonyms) {
      if (s.status === 'correct') correct++;
      else if (s.status === 'distractor') distractor++;
      else added++;
    }
    return { correct, distractor, added };
  });
  const antStats = $derived.by(() => {
    let correct = 0, distractor = 0, added = 0;
    for (const a of sscAntonyms) {
      if (a.status === 'correct') correct++;
      else if (a.status === 'distractor') distractor++;
      else added++;
    }
    return { correct, distractor, added };
  });
</script>

<div class="space-y-5 animate-fade-in">
  <button
    on:click={onBack}
    class="flex items-center gap-1.5 text-sm text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition-colors -ml-2"
  >
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path></svg>
    Back to list
  </button>

  <!-- Header card -->
  <div class="overflow-hidden border border-orange-200 dark:border-orange-800 rounded-xl bg-white dark:bg-zinc-900">
    <div class="bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-800/50 dark:to-zinc-900 p-5 pb-3">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div class="space-y-2 min-w-0">
          <div class="flex items-baseline gap-3 flex-wrap">
            <h2 class="text-3xl font-bold tracking-tight">{word.word}</h2>
            {#if enriched?.pos}
              <span class="text-xs font-medium italic bg-zinc-100 dark:bg-zinc-800 px-2 py-1 rounded-md">{enriched.pos}</span>
            {/if}
          </div>
          <div class="flex flex-wrap gap-2">
            <FrequencyBadge label="Main Question" count={word.asStem} variant="stem" />
            <FrequencyBadge label="Option Choice" count={word.asOption} variant="option" />
          </div>
        </div>
        <div class="flex flex-col items-end gap-1 text-right">
          <div class="text-2xl font-bold tabular-nums text-orange-600">
            {word.total}<span class="text-sm font-normal text-zinc-500 ml-1.5">total</span>
          </div>
          <div class="text-xs text-zinc-500">across {allExams.length} exam paper{allExams.length === 1 ? '' : 's'}</div>
        </div>
      </div>
    </div>
    {#if allExams.length > 0}
      <div class="p-5 pt-4 space-y-3">
        <div class="flex flex-wrap gap-1.5">
          {#each allExams as exam}
            {@const isStem = word.stemExams.includes(exam)}
            {@const isOption = word.optionExams.includes(exam)}
            <span
              class="exam-chip {isStem && isOption
                ? 'bg-gradient-to-r from-amber-50 to-emerald-50 border-amber-200 dark:from-amber-950/30 dark:to-emerald-950/30 dark:border-amber-800'
                : isStem
                  ? 'bg-amber-50 border-amber-200 dark:bg-amber-950/30 dark:border-amber-800'
                  : 'bg-emerald-50 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-800'}"
              title={isStem && isOption ? 'Appeared as both stem and option' : isStem ? 'Appeared as question stem' : 'Appeared as option choice'}
            >
              {exam}{isStem && isOption ? ' (S+O)' : isStem ? ' (S)' : ' (O)'}
            </span>
          {/each}
        </div>
        <!-- Per-question-type breakdown -->
        <div class="flex flex-wrap gap-2 pt-2 border-t border-zinc-200 dark:border-zinc-700">
          <span class="text-[11px] font-medium text-zinc-500 self-center mr-1">Question types:</span>
          {#each [
            { key: 'synonym', label: 'Syn', color: 'bg-sky-100 text-sky-900 border-sky-300 dark:bg-sky-950/40 dark:text-sky-200 dark:border-sky-800' },
            { key: 'antonym', label: 'Ant', color: 'bg-rose-100 text-rose-900 border-rose-300 dark:bg-rose-950/40 dark:text-rose-200 dark:border-rose-800' },
            { key: 'one-word', label: 'OWS', color: 'bg-violet-100 text-violet-900 border-violet-300 dark:bg-violet-950/40 dark:text-violet-200 dark:border-violet-800' },
            { key: 'idiom', label: 'Idiom', color: 'bg-orange-100 text-orange-900 border-orange-300 dark:bg-orange-950/40 dark:text-orange-200 dark:border-orange-800' },
            { key: 'homonym', label: 'Hom', color: 'bg-pink-100 text-pink-900 border-pink-300 dark:bg-pink-950/40 dark:text-pink-200 dark:border-pink-800' },
            { key: 'spelling', label: 'Spell', color: 'bg-teal-100 text-teal-900 border-teal-300 dark:bg-teal-950/40 dark:text-teal-200 dark:border-teal-800' },
          ] as qt}
            {@const stemCount = word.qtypesAsStem[qt.key] ?? 0}
            {@const optCount = word.qtypesAsOption[qt.key] ?? 0}
            {#if stemCount > 0 || optCount > 0}
              <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 {qt.color}" title={`${qt.label}: ${stemCount} as stem, ${optCount} as option`}>
                {qt.label}: {stemCount}S+{optCount}O
              </span>
            {/if}
          {/each}
        </div>
      </div>
    {/if}
  </div>

  {#if loading}
    <div class="border border-dashed border-zinc-200 dark:border-zinc-700 rounded-xl bg-white dark:bg-zinc-900 py-6 px-4 flex items-center gap-3 text-sm text-zinc-500">
      <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
      <span>Loading full vocabulary data (definitions, mnemonics, MCQs)...</span>
    </div>
  {:else if error}
    <div class="border border-rose-300 dark:border-rose-800 rounded-xl bg-white dark:bg-zinc-900 py-4 px-4 text-sm text-rose-700 dark:text-rose-300">
      Failed to load data: {error}
    </div>
  {:else}
    <!-- Definition Box -->
    {#if hasDefinition}
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl">
        <div class="px-5 pt-3 pb-2 text-sm font-semibold flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-orange-500"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>
          Definition
        </div>
        <p class="px-5 pb-4 text-sm leading-relaxed">{enriched!.definition}</p>
      </div>
    {:else}
      <div class="bg-white dark:bg-zinc-900 border border-dashed border-zinc-200 dark:border-zinc-700 rounded-xl">
        <div class="px-5 pt-3 pb-2 text-sm font-semibold text-zinc-500 flex items-center gap-2">Definition</div>
        <p class="px-5 pb-4 text-sm text-zinc-500 italic">No curated definition available for this word yet.</p>
      </div>
    {/if}

    <!-- Synonyms & Antonyms Grid (with color-coded legend) -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Synonyms -->
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl">
        <div class="px-5 pt-3 pb-2 flex items-center justify-between">
          <span class="text-sm font-semibold flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-emerald-600"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .962 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.962 0z"/></svg>
            SSC Exam Synonyms
          </span>
          <span class="text-[10px] text-zinc-500">
            {synStats.correct} correct · {synStats.distractor} distractor · {synStats.added} added
          </span>
        </div>
        {#if sscSynonyms.length === 0}
          <p class="px-5 pb-4 text-xs text-zinc-500 italic">No synonyms recorded.</p>
        {:else}
          <div class="px-5 pb-4 flex flex-wrap gap-1.5">
            {#each sscSynonyms as s}
              <span class="text-xs font-medium border rounded-md px-2 py-1 {s.status === 'correct'
                ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
                : s.status === 'distractor'
                  ? 'bg-rose-50 border-rose-300 text-rose-900 dark:bg-rose-950/30 dark:text-rose-100 dark:border-rose-700'
                  : 'bg-zinc-100 border-zinc-300 text-zinc-600 dark:bg-zinc-800/40 dark:text-zinc-400 dark:border-zinc-700'}"
                title={s.status === 'correct' ? 'Appeared as the correct answer in past SSC (best-guess)' : s.status === 'distractor' ? 'Appeared as a distractor option in past SSC' : 'Added from WordNet (did NOT appear in SSC)'}
              >
                {s.word}
              </span>
            {/each}
          </div>
        {/if}
      </div>
      <!-- Antonyms -->
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl">
        <div class="px-5 pt-3 pb-2 flex items-center justify-between">
          <span class="text-sm font-semibold flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-rose-600"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .962 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.962 0z"/></svg>
            SSC Exam Antonyms
          </span>
          <span class="text-[10px] text-zinc-500">
            {antStats.correct} correct · {antStats.distractor} distractor · {antStats.added} added
          </span>
        </div>
        {#if sscAntonyms.length === 0}
          <p class="px-5 pb-4 text-xs text-zinc-500 italic">No antonyms recorded.</p>
        {:else}
          <div class="px-5 pb-4 flex flex-wrap gap-1.5">
            {#each sscAntonyms as a}
              <span class="text-xs font-medium border rounded-md px-2 py-1 {a.status === 'correct'
                ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
                : a.status === 'distractor'
                  ? 'bg-rose-50 border-rose-300 text-rose-900 dark:bg-rose-950/30 dark:text-rose-100 dark:border-rose-700'
                  : 'bg-zinc-100 border-zinc-300 text-zinc-600 dark:bg-zinc-800/40 dark:text-zinc-400 dark:border-zinc-700'}"
                title={a.status === 'correct' ? 'Appeared as the correct answer in past SSC (best-guess)' : a.status === 'distractor' ? 'Appeared as a distractor option in past SSC' : 'Added from WordNet (did NOT appear in SSC)'}
              >
                {a.word}
              </span>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- Legend -->
    <div class="bg-zinc-50 dark:bg-zinc-800/30 border border-zinc-200 dark:border-zinc-700 rounded-lg px-4 py-3 flex flex-wrap items-center gap-4 text-[11px] text-zinc-600 dark:text-zinc-400">
      <span class="font-semibold">Legend:</span>
      <span class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded border-2 border-emerald-400 bg-emerald-100"></span>
        Correct answer in past SSC (best-guess via WordNet)
      </span>
      <span class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded border-2 border-rose-300 bg-rose-50"></span>
        Appeared as a distractor option in past SSC
      </span>
      <span class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded border-2 border-zinc-300 bg-zinc-100"></span>
        Added from WordNet (did NOT appear in SSC)
      </span>
    </div>

    <!-- Example Sentence -->
    <div class="bg-gradient-to-br from-sky-50/50 to-transparent dark:from-sky-950/20 border border-sky-200 dark:border-sky-800 rounded-xl">
      <div class="px-5 pt-3 pb-2 text-sm font-semibold flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-sky-600"><path d="M3 12c-1-4 4-9 9-9s10 5 9 9c-1 4-4 6-9 6s-8-2-9-6z"/><path d="M9 12h6"/></svg>
        Example Sentence
      </div>
      <blockquote class="px-5 pb-4 text-sm italic leading-relaxed border-l-4 border-sky-300 pl-3 py-1">
        &ldquo;{exampleSentence}&rdquo;
      </blockquote>
    </div>

    <!-- Mnemonic -->
    {#if hasMnemonic}
      <div class="bg-gradient-to-br from-amber-50/70 to-yellow-50/30 dark:from-amber-950/20 dark:to-yellow-950/10 border border-amber-200 dark:border-amber-800 rounded-xl">
        <div class="px-5 pt-3 pb-2 text-sm font-semibold flex items-center gap-2 text-amber-900 dark:text-amber-200">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 3 3 0 0 0 5.997-.875Z"/><path d="M2.5 21H21.5"/><path d="M12 5v16"/></svg>
          Mnemonic / Memory Tip
        </div>
        <p class="px-5 pb-4 text-sm leading-relaxed">{enriched!.mnemonic}</p>
      </div>
    {/if}

    <!-- Root Words & Family -->
    {#if hasRoot}
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl">
        <div class="px-5 pt-3 pb-2 text-sm font-semibold flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-violet-600"><path d="M12 5v14"/><path d="M5 12h14"/><circle cx="12" cy="12" r="9"/></svg>
          Root Words & Family
        </div>
        <div class="px-5 pb-4 space-y-3">
          <div class="text-sm">
            <span class="font-semibold text-violet-700 dark:text-violet-400">Primary Root: </span>
            <span>{enriched!.root!.primary}</span>
            <span class="text-zinc-500 mx-1.5">=</span>
            <span class="italic">{enriched!.root!.meaning}</span>
          </div>
          <hr class="border-zinc-200 dark:border-zinc-700" />
          <ul class="space-y-1.5 text-sm leading-relaxed">
            {#each enriched!.root!.family as fam}
              <li class="flex items-start gap-2">
                <span class="text-violet-500 mt-0.5">•</span>
                <span>{fam}</span>
              </li>
            {/each}
          </ul>
        </div>
      </div>
    {/if}

    <!-- Past SSC Exam MCQs — ALL of them, stem first then options -->
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl">
      <div class="px-5 pt-3 pb-3 flex items-center gap-2 flex-wrap">
        <span class="text-sm font-semibold flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-600"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>
          Actual Past SSC Exam MCQs
        </span>
        <span class="text-[10px] font-medium bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded-md">
          {totalMCQs} total · {stemQuestions.length} as stem · {optionQuestions.length} as option
        </span>
      </div>
      <p class="px-5 pb-2 text-xs text-zinc-500 leading-relaxed">
        All SSC questions where <span class="font-semibold">{word.word}</span> appeared, ordered with question-stem appearances first, then option-choice appearances.
      </p>

      {#if totalMCQs === 0}
        <p class="px-5 pb-4 text-sm text-zinc-500 italic">No past SSC questions surfaced for this word.</p>
      {:else}
        <!-- Stem questions section -->
        {#if stemQuestions.length > 0}
          <div class="px-5 pb-2 pt-2">
            <h3 class="text-xs font-bold uppercase tracking-wide text-amber-700 dark:text-amber-400 mb-2 flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-amber-500"></span>
              As Question Stem ({stemQuestions.length} question{stemQuestions.length === 1 ? '' : 's'})
            </h3>
          </div>
        {/if}
        <div class="px-5 pb-4 space-y-3 max-h-[800px] overflow-y-auto pr-1">
          {#each stemQuestions as q, i (q.id)}
            <MCQCard question={q} highlightWord={word.wordLower} index={i} />
          {/each}

          {#if optionQuestions.length > 0}
            <div class="pt-2 pb-1">
              <h3 class="text-xs font-bold uppercase tracking-wide text-emerald-700 dark:text-emerald-400 mb-2 flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                As Option Choice ({optionQuestions.length} question{optionQuestions.length === 1 ? '' : 's'})
              </h3>
            </div>
            {#each optionQuestions as q, i (q.id)}
              <MCQCard question={q} highlightWord={word.wordLower} index={stemQuestions.length + i} />
            {/each}
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>
