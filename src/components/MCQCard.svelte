<script lang="ts">
  // src/components/MCQCard.svelte
  // MCQ display with click-to-reveal feedback:
  // - Before click: all options are neutral (no green shown)
  // - After click:
  //   - Clicked option is correct → that option turns GREEN (✓ Correct)
  //   - Clicked option is wrong → that option turns RED (✗ Wrong)
  //   - The actual correct answer (regardless of what user clicked) turns GREEN (✓ Correct)
  //
  // For homonym questions, shows a collapsible "Confused pair" heading above the question
  // (the set of similar-sounding words from the options), so users can see the pair being tested.
  import type { QuestionEntry } from '../lib/vocab-data';
  import { pronounceWord } from '../lib/vocab-data';
  import PronounceButton from './PronounceButton.svelte';
  import WordLinkButton from './WordLinkButton.svelte';

  let {
    question,
    highlightWord = '',
    index,
  }: {
    question: QuestionEntry;
    highlightWord?: string;
    index: number;
  } = $props();

  // Per-MCQ state: user's selected option index (null = not answered yet)
  let selectedIdx = $state<number | null>(null);

  // Homonym pair heading: collapsed by default (so user can test themselves without seeing the pair)
  let pairExpanded = $state(false);

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

  // OWS: the `sent` field holds the actual question text (the description to find a single word for).
  // The `stem` field holds the answer word — so we should NEVER show `stem` for OWS.
  // Detect OWS questions where sent is a real description (not just the word repeated).
  const owsHasDescription = $derived(
    question.qtype === 'one-word' &&
    !!question.sent &&
    question.sent.trim().length > 0 &&
    question.sent.trim().toLowerCase() !== question.stem.trim().toLowerCase()
  );

  // Idioms: the options are MEANINGS (not the idiom itself), so showing the idiom as the
  // question is SAFE — it doesn't reveal the answer.
  // - If `sent` is a real context sentence (different from `stem`): show `sent`
  // - If `sent` equals `stem` (both just the idiom phrase): show "What does '[idiom]' mean?"
  //   using the `stem` field — the idiom is NOT in the options (options are meanings).
  const idiomIsStemOnly = $derived(
    question.qtype === 'idiom' &&
    (!question.sent || question.sent.trim().toLowerCase() === question.stem.trim().toLowerCase())
  );
  const idiomHasContext = $derived(
    question.qtype === 'idiom' &&
    !!question.sent &&
    question.sent.trim().toLowerCase() !== question.stem.trim().toLowerCase()
  );

  // Homonyms: the `sent` field holds the fill-in-the-blank sentence in most cases.
  // But for some questions (e.g. "Select the nearest homonym of the given word"), `sent`
  // is just the word being asked about (short), and the full question text is in `prompt`.
  // In that case, show `prompt` + ": " + `sent` (e.g. "Select the nearest homonym of the given word: Accept").
  const homonymHasSentence = $derived(
    question.qtype === 'homonym' &&
    !!question.sent &&
    question.sent.trim().length >= 15 &&
    question.sent.trim().toLowerCase() !== question.stem.trim().toLowerCase()
  );
  const homonymNeedsPrompt = $derived(
    question.qtype === 'homonym' &&
    !!question.sent &&
    question.sent.trim().length < 15
  );

  // For homonyms: build the "confused pair" — the unique set of similar-sounding options.
  // E.g. options ['except', 'expect', 'accept', 'excerpt'] → "accept · except · excerpt · expect"
  // Sorted alphabetically and joined with a middle dot. Deduped case-insensitively.
  const homonymPair = $derived.by(() => {
    if (question.qtype !== 'homonym') return '';
    const seen = new Set<string>();
    const unique: string[] = [];
    for (const opt of question.options || []) {
      const lower = opt.trim().toLowerCase();
      if (lower && !seen.has(lower)) {
        seen.add(lower);
        unique.push(opt.trim());
      }
    }
    unique.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
    return unique.join('  ·  ');
  });

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

  // Reset when the question changes (e.g. slider navigation)
  $effect(() => {
    // Watch question.id and reset
    const qid = question.id;
    selectedIdx = null;
    pairExpanded = false;
  });
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
    <!-- Homonym pair heading (collapsible) -->
    {#if question.qtype === 'homonym' && homonymPair}
      <div class="bg-pink-50 dark:bg-pink-950/20 border border-pink-200 dark:border-pink-800 rounded-md">
        <button
          onclick={() => pairExpanded = !pairExpanded}
          class="w-full flex items-center justify-between gap-2 px-3 py-2 text-left"
        >
          <span class="text-[10px] uppercase font-semibold text-pink-700 dark:text-pink-400 tracking-wide">Confused pair (homophones)</span>
          <span class="text-[10px] text-pink-600 dark:text-pink-400 flex items-center gap-1">
            {pairExpanded ? 'Hide' : 'Show'}
            <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="transition-transform {pairExpanded ? 'rotate-180' : ''}"><path d="m6 9 6 6 6-6"/></svg>
          </span>
        </button>
        {#if pairExpanded}
          <div class="px-3 pb-2.5 pt-0">
            <div class="text-sm font-semibold text-pink-900 dark:text-pink-100 leading-relaxed break-words">
              {homonymPair}
            </div>
            <p class="text-[10px] text-pink-600 dark:text-pink-400 mt-1">These similar-sounding words are the options for this question. The correct one fits the blank in the sentence below.</p>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Question text — varies by question type -->

    {#if showSentence && question.sent && (question.qtype === 'synonym' || question.qtype === 'antonym')}
      <!-- Syn/ant with underlined word in sentence: show the sentence -->
      <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded-md border border-zinc-200 dark:border-zinc-700">
        &ldquo;{question.sent}&rdquo;
      </div>
      <div class="text-sm text-zinc-500">
        <span class="font-medium">Underlined word:</span>
        <span class="ml-1 font-semibold text-zinc-900 dark:text-zinc-100">{question.stem}</span>
      </div>
    {:else if owsHasDescription}
      <!-- OWS: show the description (sent) as the question — NEVER the answer word (stem) -->
      <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-amber-50 dark:bg-amber-950/20 p-2.5 rounded-md border border-amber-200 dark:border-amber-800">
        <div class="text-[10px] uppercase font-semibold text-amber-700 dark:text-amber-400 mb-1">Find the one-word substitute for:</div>
        &ldquo;{question.sent}&rdquo;
      </div>
    {:else if idiomHasContext}
      <!-- Idiom with context sentence: show the sentence with the idiom in it -->
      <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-orange-50 dark:bg-orange-950/20 p-2.5 rounded-md border border-orange-200 dark:border-orange-800">
        &ldquo;{question.sent}&rdquo;
      </div>
    {:else if idiomIsStemOnly}
      <!-- Idiom without context sentence: show the idiom itself as the question.
           Options are MEANINGS (not the idiom), so showing the idiom is SAFE. -->
      <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-orange-50 dark:bg-orange-950/20 p-2.5 rounded-md border border-orange-200 dark:border-orange-800">
        <div class="text-[10px] uppercase font-semibold text-orange-700 dark:text-orange-400 mb-1">Idiom — select the correct meaning</div>
        What does <span class="font-semibold text-orange-900 dark:text-orange-100">&ldquo;{question.stem}&rdquo;</span> mean?
      </div>
    {:else if homonymHasSentence}
      <!-- Homonym: show the fill-in-the-blank sentence. The "pair" heading is shown above. -->
      <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-pink-50 dark:bg-pink-950/20 p-2.5 rounded-md border border-pink-200 dark:border-pink-800">
        <div class="text-[10px] uppercase font-semibold text-pink-700 dark:text-pink-400 mb-1">Fill in the blank with the correct homonym:</div>
        &ldquo;{question.sent}&rdquo;
      </div>
    {:else if homonymNeedsPrompt}
      <!-- Homonym where sent is just the word (not a sentence): show prompt + sent.
           E.g. "Select the nearest homonym of the given word: Accept" -->
      <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-pink-50 dark:bg-pink-950/20 p-2.5 rounded-md border border-pink-200 dark:border-pink-800">
        <div class="text-[10px] uppercase font-semibold text-pink-700 dark:text-pink-400 mb-1">Homonym question:</div>
        {#if question.prompt}{question.prompt} {/if}<span class="font-semibold capitalize">&ldquo;{question.sent}&rdquo;</span>
      </div>
    {:else if question.qtype === 'spelling' && question.sent && question.sent.trim().toLowerCase() !== question.stem.trim().toLowerCase()}
      <!-- Spelling with sentence: show the sentence -->
      <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-teal-50 dark:bg-teal-950/20 p-2.5 rounded-md border border-teal-200 dark:border-teal-800">
        &ldquo;{question.sent}&rdquo;
      </div>
    {:else if question.qtype === 'spelling' || question.qtype === 'one-word' || question.qtype === 'idiom' || question.qtype === 'homonym'}
      <!-- Fallback for OWS/idiom/homonym/spelling without a usable sentence: show a generic prompt -->
      <div class="text-sm text-zinc-700 dark:text-zinc-300 italic leading-relaxed bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded-md border border-zinc-200 dark:border-zinc-700">
        Select the correct answer from the options below.
      </div>
    {:else if question.stem}
      <!-- Syn/ant with main word (no sentence): show the stem word with pronunciation -->
      <div class="flex items-center gap-2 flex-wrap">
        <div class="text-base font-semibold tracking-tight capitalize break-words">{question.stem}</div>
        {#if question.stem && question.stem.trim().length < 80}
          <PronounceButton word={question.stem} size="sm" />
          <WordLinkButton word={question.stem} size="sm" />
        {/if}
      </div>
    {/if}

    <!-- Options: clickable. NO answer is shown green/amber BEFORE clicking.
         Each option row has: the answer button + a pronunciation button + a word-link button.
         The small buttons use stopPropagation so they don't trigger the answer selection. -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
      {#each question.options as opt, i}
        {@const letter = String.fromCharCode(65 + i)}
        {@const isSelected = selectedIdx === i}
        {@const isCorrect = hasCorrectAnswer && i === question.correctIdx}
        {@const answered = selectedIdx !== null}
        {@const clickedWrong = answered && isSelected && !isCorrect}
        {@const clickedCorrect = answered && isSelected && isCorrect}
        {@const missedCorrect = answered && !isSelected && isCorrect}
        {@const optColor = clickedCorrect
          ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
          : clickedWrong
            ? 'bg-rose-100 border-rose-400 text-rose-900 dark:bg-rose-950/50 dark:text-rose-100 dark:border-rose-700'
            : missedCorrect
              ? 'bg-emerald-50 border-emerald-300 text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100 dark:border-emerald-700'
              : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 hover:border-orange-400/40 enabled:hover:bg-zinc-50 dark:enabled:hover:bg-zinc-800/50'}
        <div class="flex items-stretch gap-1.5">
          <button
            onclick={() => handleClick(i)}
            disabled={answered}
            class="flex-1 flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors text-left {optColor}">
            <span class="font-mono text-xs font-bold text-zinc-500 w-5">({letter})</span>
            <span class="font-medium capitalize break-words">{opt}</span>
            {#if clickedCorrect}
              <span class="ml-auto text-[10px] font-bold text-emerald-700 dark:text-emerald-300 uppercase tracking-wide shrink-0">✓ Correct</span>
            {:else if clickedWrong}
              <span class="ml-auto text-[10px] font-bold text-rose-700 dark:text-rose-300 uppercase tracking-wide shrink-0">✗ Wrong</span>
            {:else if missedCorrect}
              <span class="ml-auto text-[10px] font-bold text-emerald-700 dark:text-emerald-300 uppercase tracking-wide shrink-0">✓ Correct</span>
            {/if}
          </button>
          {#if opt && opt.trim().length > 0 && opt.trim().length < 80}
            <!-- Pronunciation button (only for single words / short phrases, not long sentences) -->
            <button
              onclick={(e) => { e.stopPropagation(); pronounceWord(opt); }}
              disabled={answered}
              class="shrink-0 w-9 flex items-center justify-center rounded-md border {optColor} hover:bg-orange-100 dark:hover:bg-orange-900 transition-colors disabled:opacity-50"
              title="Pronounce {opt}"
              aria-label="Pronounce {opt}"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.72a.99.99 0 0 1-.703.286H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.71a.99.99 0 0 1 .703.286l3.484 3.516A.705.705 0 0 0 11 19.298z"/><path d="M16 9a5 5 0 0 1 0 6"/><path d="M19.364 5.636a9 9 0 0 1 0 12.728"/></svg>
            </button>
            <!-- Word-link button (only for single words / short phrases) -->
            <a
              href={`/word/${encodeURIComponent(opt.toLowerCase().trim())}`}
              onclick={(e) => e.stopPropagation()}
              class="shrink-0 w-9 flex items-center justify-center rounded-md border {optColor} hover:bg-sky-100 dark:hover:bg-sky-900 transition-colors"
              title="Open {opt} detail page"
              aria-label="Open {opt} detail page"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>
            </a>
          {/if}
        </div>
      {/each}
    </div>

    <!-- Result + explanation (only after user clicks) -->
    {#if selectedIdx !== null && hasCorrectAnswer}
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
        onclick={reset}
        class="text-xs h-7 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
      >
        Try again
      </button>
    {/if}
  </div>
</div>
