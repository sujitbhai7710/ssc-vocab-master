<script lang="ts">
  // src/components/TestCard.svelte
  // Exam-style MCQ card for mock tests.
  // Unlike MCQCard (which reveals the answer immediately), this one:
  // - Records the user's selection but does NOT reveal correctness
  // - Lets the user change their answer (click another option to switch)
  // - Shows a "flag for review" toggle
  // - The actual correct/wrong feedback only appears in the results page
  import type { QuestionEntry } from '../lib/vocab-data';
  import type { GrammarQuestion } from '../lib/grammar-data';

  export type UnifiedQuestion = {
    type: 'vocab' | 'grammar' | 'narration' | 'voice';
    category: string;
    data: QuestionEntry | GrammarQuestion;
  };

  let {
    question,
    index,
    selectedIdx = $bindable<number | null>(null),
    flagged = $bindable<boolean>(false),
  }: {
    question: UnifiedQuestion;
    index: number;
    selectedIdx?: number | null;
    flagged?: boolean;
  } = $props();

  // Extract a unified shape from the question data
  const qData = $derived(question.data as any);
  const stem = $derived(qData.stem || qData.sentence || '');
  const prompt = $derived(qData.prompt || '');
  const options = $derived(qData.options || []);
  const sent = $derived(qData.sent || '');
  const qtype = $derived(question.type === 'vocab' ? qData.qtype : question.category);

  const categoryLabels: Record<string, string> = {
    'syn-ant': 'Syn/Ant',
    'ows': 'OWS',
    'idiom': 'Idiom',
    'homonym': 'Homonym',
    'spelling': 'Spelling',
    'grammar': 'Grammar',
    'narration': 'Narration',
    'voice': 'Voice',
  };

  const categoryColors: Record<string, string> = {
    'syn-ant': 'bg-sky-100 text-sky-900 border-sky-300 dark:bg-sky-950/40 dark:text-sky-200 dark:border-sky-800',
    'ows': 'bg-violet-100 text-violet-900 border-violet-300 dark:bg-violet-950/40 dark:text-violet-200 dark:border-violet-800',
    'idiom': 'bg-orange-100 text-orange-900 border-orange-300 dark:bg-orange-950/40 dark:text-orange-200 dark:border-orange-800',
    'homonym': 'bg-pink-100 text-pink-900 border-pink-300 dark:bg-pink-950/40 dark:text-pink-200 dark:border-pink-800',
    'spelling': 'bg-teal-100 text-teal-900 border-teal-300 dark:bg-teal-950/40 dark:text-teal-200 dark:border-teal-800',
    'grammar': 'bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800',
    'narration': 'bg-sky-100 text-sky-900 border-sky-300 dark:bg-sky-950/40 dark:text-sky-200 dark:border-sky-800',
    'voice': 'bg-teal-100 text-teal-900 border-teal-300 dark:bg-teal-950/40 dark:text-teal-200 dark:border-teal-800',
  };

  const showSentence = $derived(
    prompt.toLowerCase().includes('underlined word') ||
    prompt.toLowerCase().includes('italicised') ||
    prompt.toLowerCase().includes('italicized') ||
    question.type !== 'vocab'
  );

  function selectOption(i: number) {
    // Toggle: clicking the same option deselects it
    selectedIdx = selectedIdx === i ? null : i;
  }

  function toggleFlag() {
    flagged = !flagged;
  }
</script>

<div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden">
  <!-- Header: Q number + category + flag toggle -->
  <div class="px-4 pt-3 pb-2 flex items-center justify-between gap-2 flex-wrap border-b border-zinc-100 dark:border-zinc-800">
    <div class="text-sm font-semibold flex items-center gap-2 flex-wrap">
      <span class="text-xs font-mono text-zinc-500 tabular-nums">Q{index + 1}</span>
      <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 {categoryColors[question.category] || 'bg-zinc-100 text-zinc-700'}">
        {categoryLabels[question.category] || question.category}
      </span>
      {#if qData.exam}
        <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 bg-zinc-100 text-zinc-700 dark:bg-zinc-800/50 dark:text-zinc-300 dark:border-zinc-700">
          {qData.exam}{#if qData.year} · {qData.year}{/if}
        </span>
      {/if}
    </div>
    <button
      onclick={toggleFlag}
      class="text-xs h-7 px-2.5 rounded-md border flex items-center gap-1 transition-colors
        {flagged
          ? 'bg-amber-100 border-amber-400 text-amber-800 dark:bg-amber-950/50 dark:text-amber-200 dark:border-amber-700'
          : 'border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300'}"
      title="Flag for review"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill={flagged ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>
      <span class="text-[10px] font-medium uppercase tracking-wide">{flagged ? 'Flagged' : 'Flag'}</span>
    </button>
  </div>

  <div class="px-4 pb-4 space-y-3">
    <!-- Prompt (if any) -->
    {#if prompt}
      <div class="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">{prompt}</div>
    {/if}

    <!-- Sentence (for underlined-word or grammar questions) -->
    {#if showSentence && sent}
      <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded-md border border-zinc-200 dark:border-zinc-700">
        &ldquo;{sent}&rdquo;
      </div>
    {/if}

    <!-- Stem word (for vocab syn/ant without sentence) -->
    {#if !showSentence && stem}
      <div class="text-base font-semibold tracking-tight capitalize">{stem}</div>
    {/if}

    <!-- Options: clickable, allow re-selection (no reveal) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
      {#each options as opt, i}
        {@const letter = String.fromCharCode(65 + i)}
        {@const isSelected = selectedIdx === i}
        <button
          onclick={() => selectOption(i)}
          class="flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors text-left
          {isSelected
            ? 'bg-sky-100 border-sky-400 text-sky-900 dark:bg-sky-950/50 dark:text-sky-100 dark:border-sky-700'
            : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 hover:border-sky-400/40 hover:bg-zinc-50 dark:hover:bg-zinc-800/50'}">
          <span class="font-mono text-xs font-bold text-zinc-500 w-5">({letter})</span>
          <span class="font-medium capitalize">{opt}</span>
          {#if isSelected}
            <span class="ml-auto text-[10px] font-bold text-sky-700 dark:text-sky-300 uppercase tracking-wide">✓</span>
          {/if}
        </button>
      {/each}
    </div>

    <!-- Status row -->
    <div class="flex items-center justify-between text-[10px] text-zinc-500">
      <span>{selectedIdx === null ? 'Not answered' : 'Answer: ' + String.fromCharCode(65 + selectedIdx)}</span>
      <span>Click an option to select, click again to deselect</span>
    </div>
  </div>
</div>
