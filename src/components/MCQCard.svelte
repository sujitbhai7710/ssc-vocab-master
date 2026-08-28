<script lang="ts">
  // src/components/MCQCard.svelte
  import type { QuestionEntry } from '../lib/vocab-data';

  let {
    question,
    highlightWord = '',
    index,
  }: {
    question: QuestionEntry;
    highlightWord?: string;
    index: number;
  } = $props();

  // Per-MCQ state: user's selected option index (null = not answered)
  let selectedIdx = $state<number | null>(null);

  const qtypeLabels: Record<string, string> = {
    synonym: 'Synonym',
    antonym: 'Antonym',
    'one-word': 'One-word substitution',
    idiom: 'Idiom',
    homonym: 'Homonym',
    spelling: 'Spelling',
  };

  const qtypeColors: Record<string, string> = {
    synonym: 'bg-sky-100 text-sky-900 border-sky-300 dark:bg-sky-950/40 dark:text-sky-200 dark:border-sky-800',
    antonym: 'bg-rose-100 text-rose-900 border-rose-300 dark:bg-rose-950/40 dark:text-rose-200 dark:border-rose-800',
    'one-word': 'bg-violet-100 text-violet-900 border-violet-300 dark:bg-violet-950/40 dark:text-violet-200 dark:border-violet-800',
    idiom: 'bg-orange-100 text-orange-900 border-orange-300 dark:bg-orange-950/40 dark:text-orange-200 dark:border-orange-800',
    homonym: 'bg-pink-100 text-pink-900 border-pink-300 dark:bg-pink-950/40 dark:text-pink-200 dark:border-pink-800',
    spelling: 'bg-teal-100 text-teal-900 border-teal-300 dark:bg-teal-950/40 dark:text-teal-200 dark:border-teal-800',
  };

  const wordIsOption = $derived(
    !!highlightWord && question.options.some((o) => o.toLowerCase() === highlightWord!.toLowerCase())
  );
  const wordIsStem = $derived(
    !!highlightWord && question.stem.toLowerCase().trim() === highlightWord!.toLowerCase()
  );
  const hasCorrectAnswer = $derived(
    question.correctIdx !== undefined && question.correctIdx >= 0 && question.correctIdx < question.options.length
  );

  // For "synonym of underlined word in sentence" type — show the sentence
  const promptLower = (question.prompt || '').toLowerCase();
  const showSentence = $derived(
    promptLower.includes('underlined word in the given sentence') ||
    promptLower.includes('underlined word in the following sentence') ||
    promptLower.includes('underlined word in a sentence') ||
    promptLower.includes('underlined word') ||
    promptLower.includes('italicised words') ||
    promptLower.includes('italicized words') ||
    promptLower.includes('underlined segment') ||
    promptLower.includes('underlined words')
  );

  function isHighlighted(opt: string): boolean {
    return !!highlightWord && opt.toLowerCase() === highlightWord!.toLowerCase();
  }

  function handleClick(i: number) {
    if (selectedIdx !== null) return; // already answered
    selectedIdx = i;
  }
  function reset() {
    selectedIdx = null;
  }
</script>

<div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden">
  <div class="px-4 pt-3 pb-2 flex items-center justify-between gap-2 flex-wrap">
    <div class="text-sm font-semibold flex items-center gap-2 flex-wrap">
      <span class="text-xs font-mono text-zinc-500 tabular-nums">Q{index + 1}</span>
      <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 {qtypeColors[question.qtype]}">
        {qtypeLabels[question.qtype] ?? question.qtype}
      </span>
      {#if question.exam}
        <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 bg-zinc-100 text-zinc-700 dark:bg-zinc-800/50 dark:text-zinc-300 dark:border-zinc-700">
          {question.exam}{#if question.year} · {question.year}{/if}
        </span>
      {/if}
      {#if wordIsStem}
        <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 bg-amber-100 text-amber-900 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800">★ as stem</span>
      {:else if wordIsOption}
        <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 bg-emerald-100 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200 dark:border-emerald-800">○ as option</span>
      {/if}
    </div>
  </div>
  <div class="px-4 pb-4 space-y-3">
    {#if showSentence && question.sent}
      <!-- Show the sentence with the underlined word highlighted -->
      <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded-md border border-zinc-200 dark:border-zinc-700">
        &ldquo;{question.sent}&rdquo;
      </div>
    {/if}
    {#if question.qtype === 'one-word' || question.qtype === 'idiom' || question.qtype === 'homonym' || (question.qtype === 'spelling' && !showSentence)}
      <!-- For OWS/idiom/homonym/spelling (no-sentence): show the stem as the question -->
      {#if question.stem && question.stem !== question.sent}
        <div class="text-sm text-zinc-700 dark:text-zinc-300 italic leading-relaxed bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded-md border border-zinc-200 dark:border-zinc-700">
          &ldquo;{question.stem}&rdquo;
        </div>
      {/if}
    {:else if !showSentence}
      <!-- Syn/ant with main word: show the stem word -->
      {#if question.stem}
        <div class="text-base font-semibold tracking-tight">{question.stem}</div>
      {/if}
    {:else if showSentence && question.stem && question.qtype !== 'idiom' && question.qtype !== 'one-word' && question.qtype !== 'homonym'}
      <!-- For syn/ant with sentence: also show the underlined word (the stem) below the sentence -->
      <div class="text-sm text-zinc-500">
        <span class="font-medium">Underlined word:</span>
        <span class="ml-1 font-semibold text-zinc-900 dark:text-zinc-100">{question.stem}</span>
      </div>
    {/if}

    <!-- Options: clickable -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
      {#each question.options as opt, i}
        {@const letter = String.fromCharCode(65 + i)}
        {@const hi = isHighlighted(opt)}
        {@const isSelected = selectedIdx === i}
        {@const isCorrect = hasCorrectAnswer && i === question.correctIdx}
        {@const showResult = selectedIdx !== null}
        {@const thisIsCorrect = isCorrect}
        {@const thisIsWrong = showResult && isSelected && !isCorrect}
        {@const thisIsMissedCorrect = showResult && !isSelected && isCorrect}
        <button
          on:click={() => handleClick(i)}
          disabled={showResult}
          class="flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors text-left
          {thisIsCorrect
            ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
            : thisIsWrong
              ? 'bg-rose-100 border-rose-400 text-rose-900 dark:bg-rose-950/50 dark:text-rose-100 dark:border-rose-700'
              : thisIsMissedCorrect
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100 dark:border-emerald-700'
                : hi && !showResult
                  ? 'bg-amber-50 border-amber-300 text-amber-900 dark:bg-amber-950/30 dark:text-amber-100 dark:border-amber-700'
                  : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 hover:border-orange-400/40 enabled:hover:bg-zinc-50 dark:enabled:hover:bg-zinc-800/50'}">
          <span class="font-mono text-xs font-bold text-zinc-500 w-5">({letter})</span>
          <span class="font-medium capitalize">{opt}</span>
          {#if thisIsCorrect}
            <span class="ml-auto text-[10px] font-bold text-emerald-700 dark:text-emerald-300 uppercase tracking-wide">✓ Correct</span>
          {:else if thisIsWrong}
            <span class="ml-auto text-[10px] font-bold text-rose-700 dark:text-rose-300 uppercase tracking-wide">✗ Wrong</span>
          {/if}
        </button>
      {/each}
    </div>

    <!-- Result + explanation -->
    {#if selectedIdx !== null}
      {#if selectedIdx === question.correctIdx}
        <div class="bg-emerald-50 dark:bg-emerald-950/20 border-l-4 border-emerald-400 dark:border-emerald-700 p-3 rounded-md">
          <div class="text-[10px] uppercase font-semibold text-emerald-700 dark:text-emerald-400 mb-1">🎉 Correct! Well done.</div>
          {#if question.expl}
            <p class="text-xs leading-relaxed text-zinc-800 dark:text-zinc-200 mt-1">
              <span class="font-semibold">Why: </span>{question.expl}
            </p>
          {/if}
        </div>
      {:else}
        <div class="bg-rose-50 dark:bg-rose-950/20 border-l-4 border-rose-400 dark:border-rose-700 p-3 rounded-md">
          <div class="text-[10px] uppercase font-semibold text-rose-700 dark:text-rose-400 mb-1">❌ Wrong answer</div>
          <p class="text-xs leading-relaxed text-zinc-800 dark:text-zinc-200">
            The correct answer is: <span class="font-semibold text-emerald-700 dark:text-emerald-400">{question.options[question.correctIdx ?? 0]}</span>
          </p>
          {#if question.expl}
            <p class="text-xs leading-relaxed text-zinc-800 dark:text-zinc-200 mt-1">
              <span class="font-semibold">Why: </span>{question.expl}
            </p>
          {/if}
        </div>
      {/if}
      <button
        on:click={reset}
        class="text-xs h-7 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
      >
        Try again
      </button>
    {/if}
  </div>
</div>

