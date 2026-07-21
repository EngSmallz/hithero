<script lang="ts">
	import { page } from '$app/state';
	import Footer from '$lib/components/Footer.svelte';
	import Header from '$lib/components/Header.svelte';
	import '$lib/styles/app.css';
	import type { Snippet } from 'svelte';
	import type { LayoutData } from './$types';

	let { children, data } = $props<{
		children: Snippet;
		data: LayoutData;
	}>();
</script>

<svelte:head>
	<link rel="icon" href="/images/favicon.ico" />
</svelte:head>

<div
	data-app-shell
	class="flex min-h-screen flex-col bg-gray-800 font-sans text-slate-950"
>
	<a
		href="#main-content"
		class="sr-only z-50 rounded-md bg-white px-4 py-2 text-sm font-semibold text-green-900 shadow focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
	>
		Skip to content
	</a>
	<Header currentPath={page.url.pathname} initialProfile={data.profile} />
	<main id="main-content" class="flex-1">
		{@render children()}
	</main>
	<Footer />
</div>
