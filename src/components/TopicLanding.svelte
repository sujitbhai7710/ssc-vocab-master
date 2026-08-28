<script lang="ts">
  // src/components/TopicLanding.svelte
  // Landing page for /narration and /voice: lists all rule sections as cards.
  import type { TopicRule, GrammarQuestion } from '../lib/grammar-data';
  import { loadNarrationRules, loadNarrationQuestions, loadVoiceRules, loadVoiceQuestions } from '../lib/grammar-data';

  let { kind }: { kind: 'narration' | 'voice' } = $props();

  let sections = $state<TopicRule[]>([]);
  let qmap = $state<Record<string, GrammarQuestion>>({});
  let loading = $state(true);

  if (typeof window !== 'undefined') {
    (async () => {
      try {
        if (kind === 'narration') {
          [sections, qmap] = await Promise.all([loadNarrationRules(), loadNarrationQuestions()]);
        } else {
          [sections, qmap] = await Promise.all([loadVoiceRules(), loadVoiceQuestions()]);
        }
      } catch (e) { console.error(e); }
      finally { loading = false; }
    })();
  }

  function slug(s: TopicRule) {
    return `${s.no}-${s.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}`;
  }
  const base = $derived(kind === 'narration' ? '/narration' : '/voice');
  const title = $derived(kind === 'narration' ? 'Narration (Direct–Indirect Speech)' : 'Voice (Active–Passive)');
  const desc = $derived(
    kind === 'narration'
      ? 'Complete rule set for converting Direct to Indirect Speech and back, with every SSC PYQ mapped to its rule.'
      : 'Complete rule set for Active↔Passive Voice conversions across all tenses and sentence types, with every SSC PYQ mapped.'
  );
</script>

<div class="space-y-5">
  <div>
    <div class="text-[11px] uppercase font-semibold tracking-wide text-orange-600 dark:text-orange-400">Grammar Module</div>
    <h2 class="text-2xl font-bold tracking-tight mt-1">{title}</h2>
    <p class="text-sm text-zinc-600 dark:text-zinc-400 mt-2 leading-relaxed max-w-3xl">{desc}</p>
  </div>

  {#if loading}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">{#each Array(8) as _}<div class="h-24 rounded-xl bg-zinc-100 dark:bg-zinc-800 animate-pulse"></div>{/each}</div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      {#each sections as s (s.id)}
        {@const qcount = (s.questionIds || []).length}
        <a href={`${base}/${slug(s)}`} class="text-left bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4 hover:border-orange-400/40 hover:shadow-md transition-all group">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <div class="text-[11px] font-mono text-zinc-500">Section {s.no}</div>
              <h3 class="text-base font-semibold tracking-tight mt-0.5 group-hover:text-orange-600 dark:group-hover:text-orange-400">{s.title}</h3>
            </div>
            <div class="shrink-0 text-right">
              <div class="text-lg font-bold tabular-nums text-orange-600 dark:text-orange-400">{qcount}</div>
              <div class="text-[10px] text-zinc-500">PYQs</div>
            </div>
          </div>
          <p class="text-xs text-zinc-500 mt-2 leading-relaxed line-clamp-2">{s.concept}</p>
          <div class="text-[11px] text-zinc-500 mt-2">{s.rules?.length ?? 0} rule points</div>
        </a>
      {/each}
    </div>
  {/if}
</div>
