<script lang="ts">
  // src/components/MCQCard.svelte
  import type { QuestionEntry } from '../lib/vocab-data';

  let {
    question,
    highlightWord,
    index,
  }: {
    question: QuestionEntry;
    highlightWord: string;
    index: number;
  } = $props();

  let revealed = $state(false);

  const qtypeLabels: Record<string, string> = {
    synonym: 'Synonym',
    antonym: 'Antonym',
    'one-word': 'One-word substitution',
  };

  const qtypeColors: Record<string, string> = {
    synonym: 'bg-sky-100 text-sky-900 border-sky-300 dark:bg-sky-950/40 dark:text-sky-200 dark:border-sky-800',
    antonym: 'bg-rose-100 text-rose-900 border-rose-300 dark:bg-rose-950/40 dark:text-rose-200 dark:border-rose-800',
    'one-word': 'bg-violet-100 text-violet-900 border-violet-300 dark:bg-violet-950/40 dark:text-violet-200 dark:border-violet-800',
  };

  const wordIsOption = $derived(question.options.some((o) => o.toLowerCase() === highlightWord.toLowerCase()));
  const wordIsStem = $derived(question.stem.toLowerCase().trim() === highlightWord.toLowerCase());

  function isHighlighted(opt: string): boolean {
    return opt.toLowerCase() === highlightWord.toLowerCase();
  }
</script>

<div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden">
  <div class="px-4 pt-3 pb-2 flex items-center justify-between gap-2 flex-wrap">
    <div class="text-sm font-semibold flex items-center gap-2 flex-wrap">
      <span class="text-xs font-mono text-zinc-500 tabular-nums">Q{index + 1}</span>
      <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 {qtypeColors[question.qtype]}">
        {qtypeLabels[question.qtype]}
      </span>
      <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 bg-zinc-100 text-zinc-700 dark:bg-zinc-800/50 dark:text-zinc-300 dark:border-zinc-700">
        {question.exam} · Q{question.qno}
      </span>
    </div>
  </div>
  <div class="px-4 pb-4 space-y-3">
    {#if question.qtype === 'one-word'}
      <div class="text-sm text-zinc-700 dark:text-zinc-300 italic leading-relaxed bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded-md border border-zinc-200 dark:border-zinc-700">
        &ldquo;{question.stem}&rdquo;
      </div>
    {:else}
      <div class="text-base font-semibold tracking-tight">
        {#if question.stem}
          {question.stem}
        {:else}
          <span class="text-zinc-500 italic text-sm">(stem not parsed)</span>
        {/if}
      </div>
    {/if}

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
      {#each question.options as opt, i}
        {@const letter = String.fromCharCode(65 + i)}
        {@const hi = isHighlighted(opt)}
        {@const isAnswer = revealed && hi && wordIsOption}
        <div
          class="flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors
          {isAnswer
            ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
            : hi
              ? 'bg-amber-50 border-amber-300 text-amber-900 dark:bg-amber-950/30 dark:text-amber-100 dark:border-amber-700'
              : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 hover:border-orange-400/40'}"
        >
          <span class="font-mono text-xs font-bold text-zinc-500 w-5">({letter})</span>
          <span class="font-medium capitalize">{opt}</span>
          {#if isAnswer}
            <span class="ml-auto text-[10px] font-bold text-emerald-700 dark:text-emerald-300 uppercase tracking-wide">Answer</span>
          {:else if !revealed && hi && wordIsOption}
            <span class="ml-auto text-[10px] font-bold text-amber-700 dark:text-amber-300 uppercase tracking-wide">This word</span>
          {/if}
        </div>
      {/each}
    </div>

    <div class="flex items-center justify-between gap-2 pt-1">
      <p class="text-[11px] text-zinc-500 leading-relaxed">
        {#if wordIsOption}
          This question tested the highlighted word as an option.
        {:else if wordIsStem}
          This question used the highlighted word as the main stem.
        {:else}
          This question relates to the highlighted word.
        {/if}
        Source PDFs do not include official answer keys; the highlighted option is the most likely answer based on SSC exam patterns.
      </p>
      <button
        on:click={() => (revealed = !revealed)}
        class="text-xs h-7 shrink-0 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
      >
        {revealed ? 'Hide answer' : 'Reveal answer'}
      </button>
    </div>
  </div>
</div>
