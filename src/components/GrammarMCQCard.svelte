<script lang="ts">
  // src/components/GrammarMCQCard.svelte
  // Grammar MCQ: prompt + sentence + 4 clickable options (reveal-on-click) + explanation.
  import type { GrammarQuestion } from '../lib/grammar-data';
  import ProblematicButton from './ProblematicButton.svelte';

  let {
    question,
    index,
  }: { question: GrammarQuestion; index: number } = $props();

  let selectedIdx = $state<number | null>(null);

  const sourceLabels: Record<string, string> = {
    'rani': "Rani Ma'am",
    'error': 'Error PDF',
    'aman': 'Aman',
    'pyq-error': 'PYQ · Error',
    'pyq-improvement': 'PYQ · Improvement',
    'pyq-narration': 'PYQ · Narration',
    'pyq-voice': 'PYQ · Voice',
  };
  const sourceColors: Record<string, string> = {
    'rani': 'bg-rose-100 text-rose-900 border-rose-300 dark:bg-rose-950/40 dark:text-rose-200 dark:border-rose-800',
    'error': 'bg-orange-100 text-orange-900 border-orange-300 dark:bg-orange-950/40 dark:text-orange-200 dark:border-orange-800',
    'aman': 'bg-violet-100 text-violet-900 border-violet-300 dark:bg-violet-950/40 dark:text-violet-200 dark:border-violet-800',
    'pyq-error': 'bg-sky-100 text-sky-900 border-sky-300 dark:bg-sky-950/40 dark:text-sky-200 dark:border-sky-800',
    'pyq-improvement': 'bg-emerald-100 text-emerald-900 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-200 dark:border-emerald-800',
    'pyq-narration': 'bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800',
    'pyq-voice': 'bg-teal-100 text-teal-900 border-teal-300 dark:bg-teal-950/40 dark:text-teal-200 dark:border-teal-800',
  };

  const hasCorrect = $derived(question.correctIdx !== null && question.correctIdx >= 0 && question.correctIdx < question.options.length);

  function handleClick(i: number) {
    if (selectedIdx !== null) return;
    selectedIdx = i;
  }
  function reset() { selectedIdx = null; }

  $effect(() => {
    const qid = question.id;
    selectedIdx = null;
  });
</script>

<div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden">
  <div class="px-4 pt-3 pb-2 flex items-center justify-between gap-2 flex-wrap">
    <div class="text-sm font-semibold flex items-center gap-2 flex-wrap">
      <span class="text-xs font-mono text-zinc-500 tabular-nums">Q{index + 1}</span>
      <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 {sourceColors[question.source] ?? 'bg-zinc-100 text-zinc-700 border-zinc-300'}">
        {sourceLabels[question.source] ?? question.source}
      </span>
      {#if question.exam}
        <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 bg-zinc-100 text-zinc-700 dark:bg-zinc-800/50 dark:text-zinc-300 dark:border-zinc-700">
          {question.exam}{#if question.year} · {question.year}{/if}
        </span>
      {/if}
    </div>
    <ProblematicButton itemType="grammar-mcq" itemKey={question.id} subType={question.qtype} label="" />
  </div>
  <div class="px-4 pb-4 space-y-3">
    {#if question.prompt}
      <p class="text-xs text-zinc-500 leading-relaxed">{question.prompt}</p>
    {/if}
    {#if question.sentence}
      <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded-md border border-zinc-200 dark:border-zinc-700">
        &ldquo;{question.sentence}&rdquo;
      </div>
    {/if}

    <div class="grid grid-cols-1 gap-2">
      {#each question.options as opt, i}
        {@const letter = String.fromCharCode(65 + i)}
        {@const isSelected = selectedIdx === i}
        {@const isCorrect = hasCorrect && i === question.correctIdx}
        {@const answered = selectedIdx !== null}
        {@const clickedWrong = answered && isSelected && !isCorrect}
        {@const clickedCorrect = answered && isSelected && isCorrect}
        {@const missedCorrect = answered && !isSelected && isCorrect}
        <button
          onclick={() => handleClick(i)}
          disabled={answered || !hasCorrect}
          class="flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors text-left
          {clickedCorrect
            ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
            : clickedWrong
              ? 'bg-rose-100 border-rose-400 text-rose-900 dark:bg-rose-950/50 dark:text-rose-100 dark:border-rose-700'
              : missedCorrect
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100 dark:border-emerald-700'
                : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 hover:border-orange-400/40 enabled:hover:bg-zinc-50 dark:enabled:hover:bg-zinc-800/50'}">
          <span class="font-mono text-xs font-bold text-zinc-500 w-5">({letter})</span>
          <span class="font-medium">{opt}</span>
          {#if clickedCorrect}
            <span class="ml-auto text-[10px] font-bold text-emerald-700 dark:text-emerald-300 uppercase tracking-wide">✓ Correct</span>
          {:else if clickedWrong}
            <span class="ml-auto text-[10px] font-bold text-rose-700 dark:text-rose-300 uppercase tracking-wide">✗ Wrong</span>
          {:else if missedCorrect}
            <span class="ml-auto text-[10px] font-bold text-emerald-700 dark:text-emerald-300 uppercase tracking-wide">✓ Correct</span>
          {/if}
        </button>
      {/each}
    </div>

    {#if !hasCorrect}
      <div class="bg-zinc-50 dark:bg-zinc-800/40 border-l-4 border-zinc-300 dark:border-zinc-600 p-3 rounded-md">
        <div class="text-[10px] uppercase font-semibold text-zinc-500 mb-1">Answer key unavailable</div>
        {#if question.explanation}
          <p class="text-xs leading-relaxed text-zinc-800 dark:text-zinc-200">{question.explanation}</p>
        {/if}
      </div>
    {:else if selectedIdx !== null}
      {#if selectedIdx === question.correctIdx}
        <div class="bg-emerald-50 dark:bg-emerald-950/20 border-l-4 border-emerald-400 dark:border-emerald-700 p-3 rounded-md">
          <div class="text-[10px] uppercase font-semibold text-emerald-700 dark:text-emerald-400 mb-1">🎉 Correct! Well done.</div>
          {#if question.explanation}
            <p class="text-xs leading-relaxed text-zinc-800 dark:text-zinc-200 mt-1"><span class="font-semibold">Why: </span>{question.explanation}</p>
          {/if}
        </div>
      {:else}
        <div class="bg-rose-50 dark:bg-rose-950/20 border-l-4 border-rose-400 dark:border-rose-700 p-3 rounded-md">
          <div class="text-[10px] uppercase font-semibold text-rose-700 dark:text-rose-400 mb-1">❌ Wrong answer</div>
          <p class="text-xs leading-relaxed text-zinc-800 dark:text-zinc-200">The correct answer is: <span class="font-semibold text-emerald-700 dark:text-emerald-400">{question.options[question.correctIdx ?? 0]}</span></p>
          {#if question.explanation}
            <p class="text-xs leading-relaxed text-zinc-800 dark:text-zinc-200 mt-1"><span class="font-semibold">Why: </span>{question.explanation}</p>
          {/if}
        </div>
      {/if}
      <button onclick={reset} class="text-xs h-7 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors">Try again</button>
    {/if}
  </div>
</div>
