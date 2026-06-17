<script lang="ts">
	import { page } from '$app/state';
	import Footer from '$lib/components/Footer.svelte';
	import Header from '$lib/components/Header.svelte';
	import '$lib/styles/app.css';
	import type { Snippet } from 'svelte';

	let { children } = $props<{
		children: Snippet;
	}>();
</script>

<svelte:head>
	<link rel="icon" href="/images/favicon.ico" />
</svelte:head>

<div class="flex min-h-screen flex-col bg-slate-50 font-sans text-slate-950">
	<a
		href="#main-content"
		class="sr-only z-50 rounded-md bg-white px-4 py-2 text-sm font-semibold text-green-900 shadow focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
	>
		Skip to content
	</a>
	<Header currentPath={page.url.pathname} />
	<main id="main-content" class="flex-1">
		{@render children()}
	</main>
	<Footer />
</div>
