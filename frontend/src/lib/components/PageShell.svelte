<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		eyebrow,
		title,
		intro,
		narrow = false,
		children
	} = $props<{
		eyebrow?: string;
		title?: string;
		intro?: string;
		narrow?: boolean;
		children?: Snippet;
	}>();

	let wrapperClass = $derived(
		`mx-auto w-full px-4 py-10 sm:px-6 sm:py-14 lg:px-8 ${narrow ? 'max-w-4xl' : 'max-w-6xl'}`
	);
</script>

<div class={wrapperClass}>
	{#if eyebrow || title || intro}
		<header class="mb-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
			<div class="max-w-3xl">
				{#if eyebrow}
					<p class="text-sm font-semibold uppercase tracking-wide text-green-700">{eyebrow}</p>
				{/if}
				{#if title}
					<h1 class="mt-3 text-4xl font-bold tracking-normal text-slate-950 sm:text-5xl">
						{title}
					</h1>
				{/if}
				{#if intro}
					<p class="mt-4 text-lg leading-8 text-slate-700">{intro}</p>
				{/if}
			</div>
		</header>
	{/if}

	{#if children}
		{@render children()}
	{/if}
</div>
