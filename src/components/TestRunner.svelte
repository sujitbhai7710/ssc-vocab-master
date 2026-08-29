<script lang="ts">
  // src/components/TestRunner.svelte
  // The actual test-taking UI:
  // - Fetches all question payloads for the test's question_refs
  // - Shows one question at a time (slider style, like exams)
  // - Prev/Next + jump-to-question grid
  // - Timer (counts down; auto-submits when 0)
  // - Flag for review
  // - Submit-all at the end -> POST /api/test/submit
  import { onMount, onDestroy } from 'svelte';
  import { loadWordQuestions, type QuestionEntry } from '../lib/vocab-data';
  import { loadQuestionsForRule, loadNarrationQuestions, loadVoiceQuestions, type GrammarQuestion } from '../lib/grammar-data';
  import { getTest, submitTest, type TestDetail, type QuestionRef } from '../lib/test-api';
  import TestCard from './TestCard.svelte';

  let { attemptId }: { attemptId: number } = $props();

  let test = $state<TestDetail | null>(null);
  let loading = $state(true);
  let error = $state('');
  let questions = $state<Array<{ ref: QuestionRef; data: QuestionEntry | GrammarQuestion | null }>>([]);
  let currentIdx = $state(0);
  let selectedAnswers = $state<(number | null)[]>([]);
  let flaggedArr = $state<boolean[]>([]);
  let timeRemaining = $state<number | null>(null); // seconds
  let timerInterval: any = null;
  let submitting = $state(false);
  let submitError = $state('');
  let startedAt = $state(0);

  // Fetch the test, then fetch all question payloads in parallel
  async function loadEverything() {
    loading = true;
    const r = await getTest(attemptId);
    if (!r.ok || !r.test) {
      error = r.error || 'Failed to load test';
      loading = false;
      return;
    }
    if (r.test.finished_at !== null) {
      // Already submitted — redirect to results
      window.location.href = `/test-results?id=${attemptId}`;
      return;
    }
    test = r.test;
    startedAt = r.test.started_at;
    selectedAnswers = new Array(r.test.question_refs.length).fill(null);
    flaggedArr = new Array(r.test.question_refs.length).fill(false);

    // Fetch all questions in parallel (grouped by type for efficiency)
    const refs = r.test.question_refs;
    questions = new Array(refs.length).fill(null).map((_, i) => ({ ref: refs[i], data: null }));

    // Group vocab refs by letter (so we load each wq/<letter>.json only once)
    const vocabByLetter: Record<string, Array<{ wordLower: string; positions: number[] }>> = {};
    const grammarRuleIds = new Set<string>();
    let needNarration = false;
    let needVoice = false;

    refs.forEach((ref, i) => {
      if (ref.type === 'vocab') {
        const letter = (ref.itemKey[0] || '_').toLowerCase();
        if (!vocabByLetter[letter]) vocabByLetter[letter] = [];
        const existing = vocabByLetter[letter].find(e => e.wordLower === ref.itemKey);
        if (existing) existing.positions.push(i);
        else vocabByLetter[letter].push({ wordLower: ref.itemKey, positions: [i] });
      } else if (ref.type === 'grammar') {
        grammarRuleIds.add(ref.itemKey);
      } else if (ref.type === 'narration') {
        needNarration = true;
      } else if (ref.type === 'voice') {
        needVoice = true;
      }
    });

    // Load vocab
    for (const [letter, entries] of Object.entries(vocabByLetter)) {
      try {
        // We need all questions for each word — loadWordQuestions gives us asStem + asOption
        for (const entry of entries) {
          const wq = await loadWordQuestions(entry.wordLower);
          const allQs = [...(wq.asStem || []), ...(wq.asOption || [])];
          for (const pos of entry.positions) {
            const ref = refs[pos];
            const q = allQs.find(q => String(q.id) === ref.id);
            if (q) questions[pos].data = q;
          }
        }
      } catch (e) {
        console.error(`Failed to load wq/${letter}.json:`, e);
      }
    }

    // Load grammar (per-rule)
    for (const ruleId of grammarRuleIds) {
      try {
        const qs = await loadQuestionsForRule(ruleId);
        for (let i = 0; i < refs.length; i++) {
          const ref = refs[i];
          if (ref.type === 'grammar' && ref.itemKey === ruleId) {
            const q = qs.find(q => q.id === ref.id);
            if (q) questions[i].data = q;
          }
        }
      } catch (e) {
        console.error(`Failed to load grammar qs for ${ruleId}:`, e);
      }
    }

    // Load narration (all at once — single file)
    if (needNarration) {
      try {
        const narrationQs = await loadNarrationQuestions();
        for (let i = 0; i < refs.length; i++) {
          const ref = refs[i];
          if (ref.type === 'narration') {
            const q = narrationQs[ref.id];
            if (q) questions[i].data = q;
          }
        }
      } catch (e) {
        console.error('Failed to load narration questions:', e);
      }
    }

    // Load voice (all at once)
    if (needVoice) {
      try {
        const voiceQs = await loadVoiceQuestions();
        for (let i = 0; i < refs.length; i++) {
          const ref = refs[i];
          if (ref.type === 'voice') {
            const q = voiceQs[ref.id];
            if (q) questions[i].data = q;
          }
        }
      } catch (e) {
        console.error('Failed to load voice questions:', e);
      }
    }

    // Start timer
    if (r.test.timer_minutes) {
      timeRemaining = r.test.timer_minutes * 60;
      const elapsed = Math.floor((Date.now() - startedAt) / 1000);
      timeRemaining = Math.max(0, timeRemaining - elapsed);
      timerInterval = setInterval(() => {
        timeRemaining = (timeRemaining || 0) - 1;
        if (timeRemaining <= 0) {
          clearInterval(timerInterval);
          handleSubmit(true);
        }
      }, 1000);
    }

    loading = false;
  }

  onMount(loadEverything);
  onDestroy(() => { if (timerInterval) clearInterval(timerInterval); });

  const answeredCount = $derived(selectedAnswers.filter(a => a !== null).length);
  const totalQuestions = $derived(questions.length);
  const progressPct = $derived(totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0);
  const currentQuestion = $derived(questions[currentIdx]);

  function gotoIdx(i: number) {
    if (i >= 0 && i < totalQuestions) currentIdx = i;
  }

  function formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  const isTimeLow = $derived(timeRemaining !== null && timeRemaining <= 60);

  async function handleSubmit(auto = false) {
    if (!test) return;
    if (submitting) return;
    if (!auto) {
      const unanswered = totalQuestions - answeredCount;
      if (unanswered > 0) {
        if (!confirm(`You have ${unanswered} unanswered question(s). Submit anyway?`)) return;
      }
    }
    submitting = true;
    submitError = '';
    if (timerInterval) clearInterval(timerInterval);

    const answers = selectedAnswers.map((selected_idx, question_idx) => ({
      question_idx,
      selected_idx,
    }));

    const r = await submitTest(test.id, answers);
    if (!r.ok || !r.result) {
      submitError = r.error || 'Failed to submit test';
      submitting = false;
      // restart timer if submission failed (test still in progress)
      if (test.timer_minutes && timeRemaining && timeRemaining > 0) {
        timerInterval = setInterval(() => {
          timeRemaining = (timeRemaining || 0) - 1;
          if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            handleSubmit(true);
          }
        }, 1000);
      }
      return;
    }
    // Redirect to results page
    window.location.href = `/test-results?id=${test.id}${auto ? '&auto=1' : ''}`;
  }

  function exitTest() {
    if (confirm('Exit test? Your progress will be saved and you can resume later from the Tests page.')) {
      window.location.href = '/tests';
    }
  }
</script>

{#if loading}
  <div class="flex items-center justify-center py-20">
    <div class="text-center space-y-3">
      <div class="h-8 w-8 rounded-full border-4 border-orange-500 border-t-transparent animate-spin mx-auto"></div>
      <p class="text-sm text-zinc-500">Loading your test…</p>
    </div>
  </div>
{:else if error}
  <div class="bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-lg p-6 text-center">
    <p class="text-sm text-rose-700 dark:text-rose-300 font-medium">{error}</p>
    <a href="/tests" class="inline-block mt-3 text-xs h-8 px-4 leading-8 rounded-md bg-rose-600 text-white font-medium hover:bg-rose-700">Back to Tests</a>
  </div>
{:else if test && currentQuestion}
  <!-- Test header: timer + progress + exit -->
  <div class="sticky top-0 z-10 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800 -mx-4 px-4 py-3 mb-4">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-3">
        <button onclick={exitTest} class="text-xs h-8 px-3 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          Exit
        </button>
        <div class="text-xs text-zinc-500">
          <span class="font-mono tabular-nums">Q{currentIdx + 1}</span> / <span class="font-mono tabular-nums">{totalQuestions}</span>
        </div>
      </div>
      <div class="flex items-center gap-3">
        {#if timeRemaining !== null}
          <div class="flex items-center gap-1.5 text-xs font-mono tabular-nums px-3 py-1.5 rounded-md border {isTimeLow ? 'bg-rose-100 border-rose-400 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-700 animate-pulse' : 'bg-zinc-100 border-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-300'}">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            {formatTime(timeRemaining)}
          </div>
        {/if}
        <button
          onclick={() => handleSubmit(false)}
          disabled={submitting}
          class="text-xs h-8 px-4 rounded-md bg-emerald-600 text-white font-medium hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1"
        >
          {#if submitting}<span class="h-3 w-3 rounded-full border-2 border-white border-t-transparent animate-spin"></span>{/if}
          Submit Test
        </button>
      </div>
    </div>
    <!-- Progress bar -->
    <div class="mt-2 h-1 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
      <div class="h-full bg-gradient-to-r from-emerald-500 to-sky-500 transition-all" style="width: {progressPct}%"></div>
    </div>
  </div>

  {#if submitError}
    <div class="bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-md p-3 mb-4 text-xs text-rose-700 dark:text-rose-300">
      {submitError}
    </div>
  {/if}

  <!-- Current question -->
  {#if currentQuestion.data}
    <TestCard
      question={{
        type: currentQuestion.ref.type,
        category: currentQuestion.ref.category,
        data: currentQuestion.data,
      }}
      index={currentIdx}
      bind:selectedIdx={selectedAnswers[currentIdx]}
      bind:flagged={flaggedArr[currentIdx]}
    />
  {:else}
    <div class="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-6 text-center">
      <p class="text-sm text-amber-700 dark:text-amber-300">This question could not be loaded (it may have been removed from the data files).</p>
      <button onclick={() => gotoIdx(currentIdx + 1 < totalQuestions ? currentIdx + 1 : currentIdx - 1)} class="mt-3 text-xs h-8 px-4 rounded-md bg-amber-600 text-white font-medium">Skip question</button>
    </div>
  {/if}

  <!-- Navigation: Prev / Next + question grid -->
  <div class="mt-6 space-y-4">
    <div class="flex items-center justify-between gap-3">
      <button
        onclick={() => gotoIdx(currentIdx - 1)}
        disabled={currentIdx === 0}
        class="text-xs h-9 px-4 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
        Previous
      </button>
      <div class="text-[10px] text-zinc-500">
        {answeredCount} answered · {flaggedArr.filter(Boolean).length} flagged
      </div>
      {#if currentIdx < totalQuestions - 1}
        <button
          onclick={() => gotoIdx(currentIdx + 1)}
          class="text-xs h-9 px-4 rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium hover:bg-zinc-800 dark:hover:bg-white flex items-center gap-1"
        >
          Next
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      {:else}
        <button
          onclick={() => handleSubmit(false)}
          disabled={submitting}
          class="text-xs h-9 px-4 rounded-md bg-emerald-600 text-white font-medium hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1"
        >
          {#if submitting}<span class="h-3 w-3 rounded-full border-2 border-white border-t-transparent animate-spin"></span>{/if}
          Finish & Submit
        </button>
      {/if}
    </div>

    <!-- Question grid (jump-to) -->
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-3">
      <div class="text-[10px] text-zinc-500 mb-2 uppercase font-semibold tracking-wide">Jump to question</div>
      <div class="grid grid-cols-8 sm:grid-cols-10 md:grid-cols-12 gap-1.5">
        {#each questions as _, i}
          {@const answered = selectedAnswers[i] !== null}
          {@const flagged = flaggedArr[i]}
          {@const isCurrent = i === currentIdx}
          <button
            onclick={() => gotoIdx(i)}
            class="h-7 w-7 rounded text-[10px] font-mono font-bold tabular-nums border transition-all
              {isCurrent
                ? 'ring-2 ring-orange-500 ring-offset-1 dark:ring-offset-zinc-900 '
                : ''}
              {flagged
                ? 'bg-amber-100 border-amber-400 text-amber-800 dark:bg-amber-950/50 dark:text-amber-200 dark:border-amber-700'
                : answered
                  ? 'bg-emerald-100 border-emerald-400 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200 dark:border-emerald-700'
                  : 'bg-zinc-50 border-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700'}"
            title={flagged ? `Q${i+1} (flagged)` : answered ? `Q${i+1} (answered)` : `Q${i+1}`}
          >
            {i + 1}
          </button>
        {/each}
      </div>
      <div class="flex items-center gap-3 mt-2 text-[10px] text-zinc-500">
        <span class="flex items-center gap-1"><span class="h-2.5 w-2.5 rounded-sm bg-emerald-400"></span>Answered</span>
        <span class="flex items-center gap-1"><span class="h-2.5 w-2.5 rounded-sm bg-amber-400"></span>Flagged</span>
        <span class="flex items-center gap-1"><span class="h-2.5 w-2.5 rounded-sm bg-zinc-300 dark:bg-zinc-700"></span>Unanswered</span>
      </div>
    </div>
  </div>
{/if}
