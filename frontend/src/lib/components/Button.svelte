<script lang="ts">
	import { resolve } from '$app/paths';
	import type { Snippet } from 'svelte';

	type ButtonVariant = 'primary' | 'secondary' | 'ghost';
	type ButtonSize = 'sm' | 'md' | 'lg';

	let {
		href,
		type = 'button',
		variant = 'primary',
		size = 'md',
		disabled = false,
		ariaLabel,
		onclick,
		class: className = '',
		children
	} = $props<{
		href?: string;
		type?: 'button' | 'submit' | 'reset';
		variant?: ButtonVariant;
		size?: ButtonSize;
		disabled?: boolean;
		ariaLabel?: string;
		onclick?: (event: MouseEvent) => void;
		class?: string;
		children?: Snippet;
	}>();

	const baseClass =
		'inline-flex items-center justify-center rounded-md font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 disabled:pointer-events-none disabled:opacity-60';

	function getVariantClass(value: ButtonVariant = 'primary'): string {
		switch (value) {
			case 'secondary':
				return 'border border-green-700 bg-white text-green-800 hover:bg-green-50 focus-visible:outline-green-700';
			case 'ghost':
				return 'text-green-800 hover:bg-green-50 focus-visible:outline-green-700';
			case 'primary':
			default:
				return 'bg-green-700 text-white shadow-sm hover:bg-green-800 focus-visible:outline-green-700';
		}
	}

	function getSizeClass(value: ButtonSize = 'md'): string {
		switch (value) {
			case 'sm':
				return 'min-h-9 px-3 text-sm';
			case 'lg':
				return 'min-h-12 px-5 text-base';
			case 'md':
			default:
				return 'min-h-11 px-4 text-base';
		}
	}

	let classes = $derived(
		[baseClass, getVariantClass(variant), getSizeClass(size), className].filter(Boolean).join(' ')
	);
</script>

{#if href}
	<a href={resolve(href as '/')} class={classes} aria-label={ariaLabel}>
		{#if children}
			{@render children()}
		{/if}
	</a>
{:else}
	<button {type} class={classes} {disabled} aria-label={ariaLabel} {onclick}>
		{#if children}
			{@render children()}
		{/if}
	</button>
{/if}
