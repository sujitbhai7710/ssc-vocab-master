<script lang="ts">
  // src/components/CustomTestBuilder.svelte
  // Build a custom test configuration:
  // - Toggle each category on/off
  // - Set min/max questions per category (range inputs)
  // - Toggle "single MCQ per item"
  // - Toggle shuffle
  // - Auto-calc timer (sum of max × 0.48 min/question) with manual override
  // - Save config (named) or start test immediately
  import { onMount } from 'svelte';
  import { isLoggedIn, loadSession, onAuthChange } from '../lib/auth';
  import { generateTest, saveConfig, updateConfig, deleteConfig, calculateTimerMinutes, CATEGORIES, type TestConfig, type TestCategorySpec } from '../lib/test-api';
  import { listTests, type SavedConfig } from '../lib/test-api';

  let editId = $state<number | null>(null); // if editing an existing config
  let name = $state('My Custom Test');
  let enabledCats = $state<Record<string, boolean>>({});
  let minVals = $state<Record<string, number>>({});
  let maxVals = $state<Record<string, number>>({});
  let singlePerItem = $state(true);
  let shuffle = $state(true);
  let useTimer = $state(true);
  let timerOverride = $state<string>(''); // empty = auto-calc
  let source = $state<'auto' | 'problematic'>('auto');

  let loggedIn = $state(false);
  let loading = $state(true);
  let saving = $state(false);
  let starting = $state(false);
  let error = $state('');
  let msg = $state('');
  let unsub: (() => void) | null = null;

  // Initialize defaults
  function setDefaults() {
    for (const c of CATEGORIES) {
      enabledCats[c.type] = c.type === 'syn-ant'; // only syn-ant enabled by default
      minVals[c.type] = 5;
      maxVals[c.type] = 10;
    }
  }

  async function loadExisting(id: number) {
    const data = await listTests();
    if (!data) return;
    const cfg = data.configs.find(c => c.id === id);
    if (!cfg) {
      error = 'Config not found';
      return;
    }
    editId = id;
    name = cfg.name;
    for (const c of CATEGORIES) {
      const spec = cfg.config.categories.find(s => s.type === c.type);
      enabledCats[c.type] = !!spec;
      minVals[c.type] = spec?.min ?? 5;
      maxVals[c.type] = spec?.max ?? 10;
    }
    singlePerItem = cfg.config.single_per_item;
    shuffle = cfg.config.shuffle;
    useTimer = cfg.config.timer_minutes !== null;
    timerOverride = cfg.config.timer_minutes !== null ? String(cfg.config.timer_minutes) : '';
    source = cfg.config.source === 'problematic' ? 'problematic' : 'auto';
  }

  onMount(async () => {
    setDefaults();
    await loadSession();
    loggedIn = isLoggedIn();
    unsub = onAuthChange((u) => { loggedIn = !!u; });
    // Check for ?id= param (editing existing config)
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      const idParam = url.searchParams.get('id');
      if (idParam) {
        const id = parseInt(idParam, 10);
        if (Number.isFinite(id)) await loadExisting(id);
      }
    }
    loading = false;
  });

  // Calculate total expected questions (sum of max values for enabled cats)
  const totalMax = $derived(
    CATEGORIES.filter(c => enabledCats[c.type]).reduce((s, c) => s + (maxVals[c.type] || 0), 0)
  );
  const totalMin = $derived(
    CATEGORIES.filter(c => enabledCats[c.type]).reduce((s, c) => s + (minVals[c.type] || 0), 0)
  );
  const autoTimer = $derived(calculateTimerMinutes(totalMax));
  const effectiveTimer = $derived(
    useTimer ? (timerOverride.trim() ? Math.max(1, parseInt(timerOverride, 10) || autoTimer) : autoTimer) : null
  );

  function buildConfig(): TestConfig | null {
    const cats: TestCategorySpec[] = [];
    for (const c of CATEGORIES) {
      if (!enabledCats[c.type]) continue;
      const min = Math.max(0, Math.floor(minVals[c.type] || 0));
      const max = Math.max(min, Math.floor(maxVals[c.type] || 0));
      cats.push({ type: c.type, min, max });
    }
    if (cats.length === 0) {
      error = 'Enable at least one category';
      return null;
    }
    error = '';
    return {
      categories: cats,
      single_per_item: singlePerItem,
      timer_minutes: effectiveTimer,
      shuffle,
      source: source === 'problematic' ? 'problematic' : 'custom',
    };
  }

  async function handleSave() {
    const cfg = buildConfig();
    if (!cfg) return;
    if (!name.trim()) { error = 'Name is required'; return; }
    saving = true; msg = '';
    if (editId) {
      const r = await updateConfig(editId, { name: name.trim(), config: cfg });
      if (!r.ok) error = r.error || 'Failed to save';
      else msg = 'Config updated';
    } else {
      const r = await saveConfig(name.trim(), cfg);
      if (!r.ok) error = r.error || 'Failed to save';
      else { msg = 'Config saved'; if (r.id) editId = r.id; }
    }
    saving = false;
  }

  async function handleStart() {
    const cfg = buildConfig();
    if (!cfg) return;
    starting = true; error = '';
    const r = await generateTest(cfg);
    starting = false;
    if (!r.ok || !r.test) {
      error = r.error || 'Failed to start test';
      return;
    }
    window.location.href = `/test?id=${r.test.attempt_id}`;
  }

  async function handleDelete() {
    if (!editId) return;
    if (!confirm('Delete this saved config?')) return;
    const ok = await deleteConfig(editId);
    if (ok) window.location.href = '/tests';
  }
</script>

{#if loading}
  <div class="flex items-center justify-center py-20">
    <div class="h-8 w-8 rounded-full border-4 border-orange-500 border-t-transparent animate-spin"></div>
  </div>
{:else if !loggedIn}
  <div class="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-6 text-center">
    <p class="text-sm text-amber-700 dark:text-amber-300 font-medium">Please log in to build a custom test.</p>
    <a href="/login?next=/tests/custom" class="inline-block mt-3 text-xs h-8 px-4 leading-8 rounded-md bg-amber-600 text-white font-medium hover:bg-amber-700">Log in</a>
  </div>
{:else}
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div>
        <h2 class="text-xl font-bold tracking-tight">{editId ? 'Edit Custom Test' : 'Build Custom Test'}</h2>
        <p class="text-sm text-zinc-500 mt-1">Pick categories, set question counts, configure timer — then save or start.</p>
      </div>
      <a href="/tests" class="text-xs h-9 px-4 leading-9 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800">← Back to Tests</a>
    </div>

    {#if error}
      <div class="bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-md p-3 text-xs text-rose-700 dark:text-rose-300">{error}</div>
    {/if}
    {#if msg}
      <div class="bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-md p-3 text-xs text-emerald-700 dark:text-emerald-300">{msg}</div>
    {/if}

    <!-- Name + source -->
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg p-4 space-y-3">
      <div>
        <label class="text-xs font-medium text-zinc-500 uppercase tracking-wide">Test name</label>
        <input
          type="text"
          value={name}
          oninput={(e) => name = (e.target as HTMLInputElement).value}
          maxlength="100"
          class="mt-1 w-full h-9 px-3 text-sm border border-zinc-200 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-orange-400/40"
        />
      </div>
      <div>
        <label class="text-xs font-medium text-zinc-500 uppercase tracking-wide">Question source</label>
        <div class="mt-1 flex items-center gap-3">
          <label class="flex items-center gap-1.5 text-sm cursor-pointer">
            <input type="radio" name="source" checked={source === 'auto'} onchange={() => source = 'auto'} class="accent-orange-600" />
            <span>From my progress (auto)</span>
          </label>
          <label class="flex items-center gap-1.5 text-sm cursor-pointer">
            <input type="radio" name="source" checked={source === 'problematic'} onchange={() => source = 'problematic'} class="accent-orange-600" />
            <span>From my Problems list</span>
          </label>
        </div>
        <p class="text-[10px] text-zinc-500 mt-1">
          {#if source === 'auto'}Tests you on what you've marked as read (using the progress tracker).{:else}Tests you only on items you've marked as problematic.{/if}
        </p>
      </div>
    </div>

    <!-- Categories -->
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg p-4">
      <h3 class="text-sm font-semibold mb-3">Categories & question counts</h3>
      <div class="space-y-3">
        {#each CATEGORIES as c}
          <div class="border border-zinc-100 dark:border-zinc-800 rounded-lg p-3 {enabledCats[c.type] ? 'bg-orange-50/30 dark:bg-orange-950/10' : ''}">
            <div class="flex items-center justify-between gap-3 flex-wrap">
              <label class="flex items-center gap-2 cursor-pointer flex-1 min-w-0">
                <input
                  type="checkbox"
                  checked={enabledCats[c.type]}
                  onchange={(e) => enabledCats[c.type] = (e.target as HTMLInputElement).checked}
                  class="accent-orange-600 h-4 w-4"
                />
                <div class="min-w-0">
                  <div class="text-sm font-medium">{c.label}</div>
                  <div class="text-[10px] text-zinc-500">{c.desc}</div>
                </div>
              </label>
              {#if enabledCats[c.type]}
                <div class="flex items-center gap-2 text-xs">
                  <span class="text-zinc-500">Min</span>
                  <input
                    type="number" min="0" max="200" value={minVals[c.type]}
                    oninput={(e) => minVals[c.type] = parseInt((e.target as HTMLInputElement).value) || 0}
                    class="w-16 h-7 px-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-orange-400/40"
                  />
                  <span class="text-zinc-500">Max</span>
                  <input
                    type="number" min="0" max="200" value={maxVals[c.type]}
                    oninput={(e) => maxVals[c.type] = parseInt((e.target as HTMLInputElement).value) || 0}
                    class="w-16 h-7 px-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-orange-400/40"
                  />
                </div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Options -->
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg p-4 space-y-3">
      <h3 class="text-sm font-semibold">Options</h3>
      <label class="flex items-center justify-between gap-3 cursor-pointer">
        <div>
          <div class="text-sm font-medium">Single MCQ per item</div>
          <div class="text-[10px] text-zinc-500">If on, each vocab word / grammar rule appears at most once. Turn off for intensive revision.</div>
        </div>
        <input type="checkbox" checked={singlePerItem} onchange={(e) => singlePerItem = (e.target as HTMLInputElement).checked} class="accent-orange-600 h-4 w-4" />
      </label>
      <label class="flex items-center justify-between gap-3 cursor-pointer">
        <div>
          <div class="text-sm font-medium">Shuffle question order</div>
          <div class="text-[10px] text-zinc-500">Randomize the order of questions in the test.</div>
        </div>
        <input type="checkbox" checked={shuffle} onchange={(e) => shuffle = (e.target as HTMLInputElement).checked} class="accent-orange-600 h-4 w-4" />
      </label>
      <div class="border-t border-zinc-100 dark:border-zinc-800 pt-3">
        <label class="flex items-center justify-between gap-3 cursor-pointer">
          <div>
            <div class="text-sm font-medium">Use timer</div>
            <div class="text-[10px] text-zinc-500">SSC pattern: 12 min for 25 questions (0.48 min/Q). Auto-calculated from total.</div>
          </div>
          <input type="checkbox" checked={useTimer} onchange={(e) => useTimer = (e.target as HTMLInputElement).checked} class="accent-orange-600 h-4 w-4" />
        </label>
        {#if useTimer}
          <div class="mt-2 flex items-center gap-2 text-xs">
            <span class="text-zinc-500">Timer (minutes):</span>
            <input
              type="number" min="1" max="600"
              value={timerOverride}
              placeholder={String(autoTimer)}
              oninput={(e) => timerOverride = (e.target as HTMLInputElement).value}
              class="w-20 h-7 px-2 text-xs border border-zinc-200 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-orange-400/40"
            />
            <span class="text-[10px] text-zinc-500">Empty = auto ({autoTimer} min for {totalMax} max questions)</span>
          </div>
        {/if}
      </div>
    </div>

    <!-- Summary + actions -->
    <div class="bg-gradient-to-r from-emerald-50 to-sky-50 dark:from-emerald-950/30 dark:to-sky-950/30 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4">
      <div class="flex items-center justify-between gap-3 flex-wrap">
        <div class="text-sm">
          <div class="font-semibold">Summary</div>
          <div class="text-xs text-zinc-600 dark:text-zinc-400 mt-0.5">
            {CATEGORIES.filter(c => enabledCats[c.type]).length} categor{CATEGORIES.filter(c => enabledCats[c.type]).length === 1 ? 'y' : 'ies'} ·
            <span class="font-mono tabular-nums">{totalMin}-{totalMax}</span> questions ·
            {#if effectiveTimer !== null}<span class="font-mono tabular-nums">{effectiveTimer}m</span> timer{:else}no timer{/if}
          </div>
        </div>
        <div class="flex items-center gap-2">
          {#if editId}
            <button onclick={handleDelete} class="text-xs h-9 px-3 rounded-md border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30">Delete</button>
          {/if}
          <button onclick={handleSave} disabled={saving} class="text-xs h-9 px-4 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-50 flex items-center gap-1.5">
            {#if saving}<span class="h-3 w-3 rounded-full border-2 border-zinc-500 border-t-transparent animate-spin"></span>{/if}
            {editId ? 'Update' : 'Save'}
          </button>
          <button onclick={handleStart} disabled={starting} class="text-xs h-9 px-4 rounded-md bg-emerald-600 text-white font-medium hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1.5">
            {#if starting}<span class="h-3 w-3 rounded-full border-2 border-white border-t-transparent animate-spin"></span>{/if}
            Start Test
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
