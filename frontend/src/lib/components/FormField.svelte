<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		id,
		label,
		help,
		error,
		required = false,
		children
	} = $props<{
		id: string;
		label: string;
		help?: string;
		error?: string;
		required?: boolean;
		children?: Snippet;
	}>();

	let helpId = $derived(help ? `${id}-help` : undefined);
	let errorId = $derived(error ? `${id}-error` : undefined);
</script>

<div class="space-y-2">
	<label for={id} class="block text-sm font-semibold text-slate-900">
		{label}
		{#if required}
			<span class="text-green-700">required</span>
		{/if}
	</label>

	{#if children}
		{@render children()}
	{/if}

	{#if help}
		<p id={helpId} class="text-sm text-slate-600">{help}</p>
	{/if}

	{#if error}
		<p id={errorId} class="text-sm font-medium text-red-700">{error}</p>
	{/if}
</div>
