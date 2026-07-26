<script lang="ts">
	import type { Snippet } from 'svelte';

	type AlertVariant = 'info' | 'success' | 'warning' | 'error';

	let {
		variant = 'info',
		title,
		children
	} = $props<{
		variant?: AlertVariant;
		title?: string;
		children?: Snippet;
	}>();

	function getVariantClass(value: AlertVariant = 'info'): string {
		switch (value) {
			case 'success':
				return 'border-green-200 bg-green-50 text-green-950';
			case 'warning':
				return 'border-amber-200 bg-amber-50 text-amber-950';
			case 'error':
				return 'border-red-200 bg-red-50 text-red-950';
			case 'info':
			default:
				return 'border-blue-200 bg-blue-50 text-blue-950';
		}
	}

	let role = $derived(variant === 'error' ? 'alert' : 'status');
	let classes = $derived(`rounded-md border p-4 ${getVariantClass(variant)}`);
</script>

<div {role} class={classes}>
	{#if title}
		<p class="font-semibold">{title}</p>
	{/if}
	{#if children}
		<div class={title ? 'mt-1 text-sm leading-6' : 'text-sm leading-6'}>
			{@render children()}
		</div>
	{/if}
</div>
