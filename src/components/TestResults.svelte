<script lang="ts">
  // src/components/TestResults.svelte
  // Shows the results of a submitted test:
  // - Score summary (correct/total, %, time taken, auto-problematic added count)
  // - Per-category breakdown
  // - Per-question review with the user's answer, correct answer, and explanation
  // - Filter: all / correct / wrong / skipped / flagged
  import { onMount } from 'svelte';
  import { loadWordQuestions, type QuestionEntry } from '../lib/vocab-data';
  import { loadQuestionsForRule, loadNarrationQuestions, loadVoiceQuestions, type GrammarQuestion } from '../lib/grammar-data';
  import { getTest, type TestDetail, type QuestionRef } from '../lib/test-api';

  let { attemptId }: { attemptId: number } = $props();

  let test = $state<TestDetail | null>(null);
  let loading = $state(true);
  let error = $state('');
  let questions = $state<Array<{ ref: QuestionRef; data: QuestionEntry | GrammarQuestion | null }>>([]);
  let filter = $state<'all' | 'correct' | 'wrong' | 'skipped'>('all');

  const autoSubmitted = $derived(typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('auto') === '1');

  async function loadResults() {
    loading = true;
    const r = await getTest(attemptId, true);
    if (!r.ok || !r.test) {
      error = r.error || 'Failed to load results';
      loading = false;
      return;
    }
    if (!r.test.results || r.test.finished_at === null) {
      // Not submitted yet — redirect to take the test
      window.location.href = `/test?id=${attemptId}`;
      return;
    }
    test = r.test;
    const refs = r.test.question_refs;
    questions = new Array(refs.length).fill(null).map((_, i) => ({ ref: refs[i], data: null }));

    // Fetch all question payloads (same logic as TestRunner, condensed)
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
      } else if (ref.type === 'narration') needNarration = true;
      else if (ref.type === 'voice') needVoice = true;
    });

    for (const [, entries] of Object.entries(vocabByLetter)) {
      for (const entry of entries) {
        try {
          const wq = await loadWordQuestions(entry.wordLower);
          const allQs = [...(wq.asStem || []), ...(wq.asOption || [])];
          for (const pos of entry.positions) {
            const ref = refs[pos];
            const q = allQs.find(q => String(q.id) === ref.id);
            if (q) questions[pos].data = q;
          }
        } catch (e) { /* skip */ }
      }
    }
    for (const ruleId of grammarRuleIds) {
      try {
        const qs = await loadQuestionsForRule(ruleId);
        for (let i = 0; i < refs.length; i++) {
          if (refs[i].type === 'grammar' && refs[i].itemKey === ruleId) {
            const q = qs.find(q => q.id === refs[i].id);
            if (q) questions[i].data = q;
          }
        }
      } catch (e) { /* skip */ }
    }
    if (needNarration) {
      try {
        const narrationQs = await loadNarrationQuestions();
        for (let i = 0; i < refs.length; i++) {
          if (refs[i].type === 'narration') {
            const q = narrationQs[refs[i].id];
            if (q) questions[i].data = q;
          }
        }
      } catch (e) { /* skip */ }
    }
    if (needVoice) {
      try {
        const voiceQs = await loadVoiceQuestions();
        for (let i = 0; i < refs.length; i++) {
          if (refs[i].type === 'voice') {
            const q = voiceQs[refs[i].id];
            if (q) questions[i].data = q;
          }
        }
      } catch (e) { /* skip */ }
    }
    loading = false;
  }

  onMount(loadResults);

  const results = $derived(test?.results || []);
  const score = $derived(test?.score ?? 0);
  const total = $derived(test?.total ?? 0);
  const pct = $derived(total > 0 ? Math.round((score / total) * 100) : 0);
  const correctCount = $derived(results.filter(r => r.is_correct).length);
  const wrongCount = $derived(results.filter(r => !r.is_correct && r.selected_idx !== null).length);
  const skippedCount = $derived(results.filter(r => r.selected_idx === null).length);
  const timeTakenMs = $derived(test?.finished_at && test?.started_at ? test.finished_at - test.started_at : 0);

  // Per-category breakdown
  const categoryBreakdown = $derived.by(() => {
    const map: Record<string, { correct: number; wrong: number; skipped: number; total: number }> = {};
    for (const r of results) {
      if (!map[r.category]) map[r.category] = { correct: 0, wrong: 0, skipped: 0, total: 0 };
      map[r.category].total++;
      if (r.is_correct) map[r.category].correct++;
      else if (r.selected_idx === null) map[r.category].skipped++;
      else map[r.category].wrong++;
    }
    return Object.entries(map).sort((a, b) => b[1].total - a[1].total);
  });

  const filteredResults = $derived.by(() => {
    if (filter === 'all') return results;
    if (filter === 'correct') return results.filter(r => r.is_correct);
    if (filter === 'wrong') return results.filter(r => !r.is_correct && r.selected_idx !== null);
    if (filter === 'skipped') return results.filter(r => r.selected_idx === null);
    return results;
  });

  function formatDuration(ms: number): string {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    const sec = s % 60;
    if (m >= 60) {
      const h = Math.floor(m / 60);
      const mm = m % 60;
      return `${h}h ${mm}m ${sec}s`;
    }
    return `${m}m ${sec}s`;
  }

  const categoryLabels: Record<string, string> = {
    'syn-ant': 'Syn/Ant', 'ows': 'OWS', 'idiom': 'Idiom', 'homonym': 'Homonym',
    'spelling': 'Spelling', 'grammar': 'Grammar', 'narration': 'Narration', 'voice': 'Voice',
  };
</script>

{#if loading}
  <div class="flex items-center justify-center py-20">
    <div class="text-center space-y-3">
      <div class="h-8 w-8 rounded-full border-4 border-orange-500 border-t-transparent animate-spin mx-auto"></div>
      <p class="text-sm text-zinc-500">Loading your results…</p>
    </div>
  </div>
{:else if error}
  <div class="bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-lg p-6 text-center">
    <p class="text-sm text-rose-700 dark:text-rose-300 font-medium">{error}</p>
    <a href="/tests" class="inline-block mt-3 text-xs h-8 px-4 leading-8 rounded-md bg-rose-600 text-white font-medium hover:bg-rose-700">Back to Tests</a>
  </div>
{:else if test}
  <!-- Score summary -->
  <div class="space-y-6">
    {#if autoSubmitted}
      <div class="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-3 text-xs text-amber-700 dark:text-amber-300">
        ⏱ Time's up! Your test was auto-submitted.
      </div>
    {/if}

    <div class="bg-gradient-to-br from-emerald-50 to-sky-50 dark:from-emerald-950/30 dark:to-sky-950/30 border border-emerald-200 dark:border-emerald-800 rounded-xl p-6">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <div class="text-xs uppercase font-semibold tracking-wide text-emerald-700 dark:text-emerald-400">Test Complete</div>
          <div class="mt-1 flex items-baseline gap-2">
            <span class="text-4xl font-bold tabular-nums tracking-tight">{score}</span>
            <span class="text-lg text-zinc-500">/ {total}</span>
            <span class="text-2xl font-bold tabular-nums text-emerald-600 dark:text-emerald-400">{pct}%</span>
          </div>
          <div class="mt-1 text-xs text-zinc-500">
            {test.config?.name || 'Untitled test'}
            {#if test.config?.source === 'problematic'} · Problematic revision{/if}
          </div>
        </div>
        <div class="grid grid-cols-3 gap-3 text-center">
          <div class="px-3 py-2 rounded-lg bg-white dark:bg-zinc-900 border border-emerald-200 dark:border-emerald-800">
            <div class="text-lg font-bold text-emerald-600 dark:text-emerald-400 tabular-nums">{correctCount}</div>
            <div class="text-[10px] uppercase text-zinc-500">Correct</div>
          </div>
          <div class="px-3 py-2 rounded-lg bg-white dark:bg-zinc-900 border border-rose-200 dark:border-rose-800">
            <div class="text-lg font-bold text-rose-600 dark:text-rose-400 tabular-nums">{wrongCount}</div>
            <div class="text-[10px] uppercase text-zinc-500">Wrong</div>
          </div>
          <div class="px-3 py-2 rounded-lg bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700">
            <div class="text-lg font-bold text-zinc-500 tabular-nums">{skippedCount}</div>
            <div class="text-[10px] uppercase text-zinc-500">Skipped</div>
          </div>
        </div>
      </div>
      <div class="mt-4 flex items-center justify-between gap-3 text-xs text-zinc-500 flex-wrap">
        <div class="flex items-center gap-3">
          {#if timeTakenMs > 0}
            <span>⏱ Time: <span class="font-mono tabular-nums">{formatDuration(timeTakenMs)}</span></span>
          {/if}
          {#if test.timer_minutes}
            <span>🎯 Allotted: <span class="font-mono tabular-nums">{test.timer_minutes}m</span></span>
          {/if}
        </div>
        <div class="flex items-center gap-3">
          <a href="/tests" class="text-xs h-8 px-4 leading-8 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800">Back to Tests</a>
          <a href="/test?id={attemptId}" class="text-xs h-8 px-4 leading-8 rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium hover:bg-zinc-800 dark:hover:bg-white">Retake Test</a>
        </div>
      </div>
    </div>

    <!-- Auto-problematic notice -->
    {#if wrongCount > 0}
      <div class="bg-sky-50 dark:bg-sky-950/30 border border-sky-200 dark:border-sky-800 rounded-lg p-3 text-xs text-sky-700 dark:text-sky-300">
        💡 The <strong>{wrongCount}</strong> question(s) you got wrong have been auto-added to your <a href="/problems" class="underline font-medium">Problematic Items</a> list for revision. You can remove them from there if you've mastered them.
      </div>
    {/if}

    <!-- Per-category breakdown -->
    {#if categoryBreakdown.length > 0}
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4">
        <h3 class="text-sm font-semibold mb-3">Per-category breakdown</h3>
        <div class="space-y-2">
          {#each categoryBreakdown as [cat, stats]}
            <div class="flex items-center gap-3">
              <div class="w-24 text-xs font-medium">{categoryLabels[cat] || cat}</div>
              <div class="flex-1 h-6 bg-zinc-100 dark:bg-zinc-800 rounded overflow-hidden flex">
                {#if stats.correct > 0}<div class="bg-emerald-500" style="width: {(stats.correct / stats.total) * 100}%" title="{stats.correct} correct"></div>{/if}
                {#if stats.wrong > 0}<div class="bg-rose-500" style="width: {(stats.wrong / stats.total) * 100}%" title="{stats.wrong} wrong"></div>{/if}
                {#if stats.skipped > 0}<div class="bg-zinc-300 dark:bg-zinc-600" style="width: {(stats.skipped / stats.total) * 100}%" title="{stats.skipped} skipped"></div>{/if}
              </div>
              <div class="w-24 text-[10px] text-zinc-500 text-right tabular-nums">
                {stats.correct}/{stats.total} · {Math.round((stats.correct / stats.total) * 100)}%
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Filter + question review -->
    <div class="space-y-3">
      <div class="flex items-center gap-1.5 flex-wrap">
        <span class="text-xs text-zinc-500 mr-2">Show:</span>
        {#each [['all', `All (${total})`], ['wrong', `Wrong (${wrongCount})`], ['correct', `Correct (${correctCount})`], ['skipped', `Skipped (${skippedCount})`]] as [f, label]}
          <button
            onclick={() => filter = f as any}
            class="text-xs h-7 px-3 rounded-md border transition-colors
              {filter === f
                ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 border-transparent font-medium'
                : 'border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300'}"
          >
            {label}
          </button>
        {/each}
      </div>

      {#each filteredResults as r}
        {@const q = questions[r.question_idx]}
        {@const qData = q?.data as any}
        {@const isCorrect = r.is_correct}
        {@const isSkipped = r.selected_idx === null}
        <div class="bg-white dark:bg-zinc-900 border rounded-lg overflow-hidden
          {isCorrect ? 'border-emerald-200 dark:border-emerald-800' : isSkipped ? 'border-zinc-200 dark:border-zinc-700' : 'border-rose-200 dark:border-rose-800'}">
          <div class="px-4 pt-3 pb-2 flex items-center justify-between gap-2 flex-wrap border-b border-zinc-100 dark:border-zinc-800">
            <div class="text-sm font-semibold flex items-center gap-2 flex-wrap">
              <span class="text-xs font-mono text-zinc-500 tabular-nums">Q{r.question_idx + 1}</span>
              <span class="text-[10px] font-medium border rounded-md px-2 py-0.5 bg-zinc-100 text-zinc-700 dark:bg-zinc-800/50 dark:text-zinc-300">
                {categoryLabels[r.category] || r.category}
              </span>
              {#if qData?.exam}
                <span class="text-[10px] text-zinc-500">{qData.exam}{#if qData.year} · {qData.year}{/if}</span>
              {/if}
            </div>
            <div class="text-[10px] font-bold uppercase tracking-wide
              {isCorrect ? 'text-emerald-700 dark:text-emerald-400' : isSkipped ? 'text-zinc-500' : 'text-rose-700 dark:text-rose-400'}">
              {#if isCorrect}✓ Correct{:else if isSkipped}— Skipped{:else}✗ Wrong{/if}
            </div>
          </div>
          {#if qData}
            <div class="px-4 pb-4 space-y-3">
              {#if qData.sent}
                <div class="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded-md border border-zinc-200 dark:border-zinc-700">
                  &ldquo;{qData.sent}&rdquo;
                </div>
              {/if}
              {#if qData.stem && !qData.sent}
                <div class="text-base font-semibold tracking-tight capitalize">{qData.stem}</div>
              {/if}

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {#each qData.options || [] as opt, i}
                  {@const letter = String.fromCharCode(65 + i)}
                  {@const isSelected = r.selected_idx === i}
                  {@const isCorrectOpt = r.correct_idx === i}
                  <div class="flex items-center gap-2 px-3 py-2 rounded-md border text-sm
                    {isCorrectOpt
                      ? 'bg-emerald-100 border-emerald-400 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100 dark:border-emerald-700'
                      : isSelected
                        ? 'bg-rose-100 border-rose-400 text-rose-900 dark:bg-rose-950/50 dark:text-rose-100 dark:border-rose-700'
                        : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300'}">
                    <span class="font-mono text-xs font-bold text-zinc-500 w-5">({letter})</span>
                    <span class="font-medium capitalize">{opt}</span>
                    {#if isCorrectOpt}
                      <span class="ml-auto text-[10px] font-bold text-emerald-700 dark:text-emerald-300 uppercase">✓ Correct</span>
                    {:else if isSelected}
                      <span class="ml-auto text-[10px] font-bold text-rose-700 dark:text-rose-300 uppercase">Your answer</span>
                    {/if}
                  </div>
                {/each}
              </div>

              {#if qData.expl || qData.explanation}
                <div class="bg-sky-50 dark:bg-sky-950/20 border-l-4 border-sky-400 dark:border-sky-700 p-3 rounded-md">
                  <div class="text-[10px] uppercase font-semibold text-sky-700 dark:text-sky-400 mb-1">Explanation</div>
                  <p class="text-xs leading-relaxed text-zinc-800 dark:text-zinc-200">{qData.expl || qData.explanation}</p>
                </div>
              {/if}
            </div>
          {:else}
            <div class="px-4 pb-4 text-xs text-zinc-500 italic">Question data unavailable.</div>
          {/if}
        </div>
      {/each}
    </div>
  </div>
{/if}
